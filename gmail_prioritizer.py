import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
CONFIG_FILE = "config.json"
DEFAULT_CONFIG_FILE = "config.example.json"


def load_config() -> Dict:
    config_path = Path(CONFIG_FILE)

    if not config_path.exists():
        print("config.json not found. Using config.example.json.")
        config_path = Path(DEFAULT_CONFIG_FILE)

    with open(config_path, "r", encoding="utf-8") as file:
        return json.load(file)


def authenticate_gmail():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                raise FileNotFoundError(
                    "credentials.json not found. Download OAuth Desktop credentials from Google Cloud."
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token.json", "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def get_or_create_label(service, label_name: str) -> str:
    labels = service.users().labels().list(userId="me").execute().get("labels", [])

    for label in labels:
        if label["name"] == label_name:
            return label["id"]

    label_body = {
        "name": label_name,
        "labelListVisibility": "labelShow",
        "messageListVisibility": "show"
    }

    created = service.users().labels().create(
        userId="me",
        body=label_body
    ).execute()

    return created["id"]


def get_header(headers: List[Dict], name: str) -> str:
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")
    return ""


def search_messages(service, query: str, max_results: int) -> List[Dict]:
    result = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=max_results
    ).execute()

    return result.get("messages", [])


def read_message_summary(service, message_id: str) -> Dict:
    message = service.users().messages().get(
        userId="me",
        id=message_id,
        format="metadata",
        metadataHeaders=["From", "Subject", "Date"]
    ).execute()

    headers = message.get("payload", {}).get("headers", [])

    return {
        "id": message_id,
        "thread_id": message.get("threadId"),
        "from": get_header(headers, "From"),
        "subject": get_header(headers, "Subject"),
        "date": get_header(headers, "Date"),
        "snippet": message.get("snippet", "")
    }


def classify_with_rules(email: Dict) -> str:
    text = f"{email.get('from', '')} {email.get('subject', '')} {email.get('snippet', '')}".lower()

    urgent_words = [
        "urgent", "asap", "immediate", "today", "deadline", "overdue",
        "action required", "critical", "please respond"
    ]

    action_words = [
        "please review", "can you", "could you", "need your input",
        "approval", "approve", "respond", "follow up", "request"
    ]

    newsletter_words = [
        "unsubscribe", "newsletter", "weekly digest", "promotion",
        "sale", "webinar", "marketing"
    ]

    receipt_words = [
        "receipt", "invoice", "payment", "order confirmation",
        "transaction", "billing"
    ]

    if any(word in text for word in urgent_words):
        return "urgent"

    if any(word in text for word in action_words):
        return "action_needed"

    if any(word in text for word in receipt_words):
        return "receipt"

    if any(word in text for word in newsletter_words):
        return "newsletter"

    return "fyi"


def classify_with_openai(email: Dict) -> Optional[str]:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key or OpenAI is None:
        return None

    client = OpenAI(api_key=api_key)

    prompt = f"""
Classify this email into exactly one category:

urgent
action_needed
fyi
newsletter
receipt

Return only the category name.

From: {email.get("from", "")}
Subject: {email.get("subject", "")}
Snippet: {email.get("snippet", "")}
"""

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt
        )

        category = response.output_text.strip().lower()

        valid = {"urgent", "action_needed", "fyi", "newsletter", "receipt"}
        if category in valid:
            return category

    except Exception as error:
        print(f"OpenAI classification failed. Falling back to rules. Error: {error}")

    return None


def classify_email(email: Dict) -> str:
    ai_category = classify_with_openai(email)
    if ai_category:
        return ai_category

    return classify_with_rules(email)


def apply_label(service, message_id: str, label_id: str):
    service.users().messages().modify(
        userId="me",
        id=message_id,
        body={
            "addLabelIds": [label_id]
        }
    ).execute()


def main():
    parser = argparse.ArgumentParser(description="Gmail AI Prioritizer Agent")
    parser.add_argument("--dry-run", action="store_true", help="Preview classifications without labeling emails")
    args = parser.parse_args()

    config = load_config()
    service = authenticate_gmail()

    labels = config["labels"]
    label_ids = {
        category: get_or_create_label(service, label_name)
        for category, label_name in labels.items()
    }

    messages = search_messages(
        service=service,
        query=config.get("query", "in:inbox newer_than:14d"),
        max_results=config.get("max_results", 25)
    )

    print(f"Found {len(messages)} messages to classify.")

    processed = 0

    for msg in messages:
        email = read_message_summary(service, msg["id"])
        category = classify_email(email)
        label_name = labels[category]

        print("-" * 70)
        print(f"From: {email['from']}")
        print(f"Subject: {email['subject']}")
        print(f"Category: {category}")
        print(f"Label: {label_name}")

        if not args.dry_run:
            apply_label(service, email["id"], label_ids[category])
            print("Status: labeled")
        else:
            print("Status: dry run only")

        processed += 1

    print(f"Done. Processed {processed} messages.")


if __name__ == "__main__":
    main()
