# Gmail Prioritizer Agent

A Python-based AI agent that scans Gmail inbox messages, classifies them by priority, and applies Gmail labels automatically.

## What it does

The agent reviews recent inbox emails and labels them as:

- `AI/Urgent`
- `AI/Action Needed`
- `AI/FYI`
- `AI/Newsletter`
- `AI/Receipts`

It supports:

- Dry-run mode
- Gmail API authentication
- OpenAI-based classification
- Rule-based fallback classification
- Configurable max email count
- Safe operation: it labels emails but does not delete anything

## Project structure

```text
gmail-prioritizer-agent/
├── gmail_prioritizer.py
├── config.example.json
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

## Setup

### 1. Clone the repo

```powershell
git clone https://github.com/YOUR-USERNAME/gmail-prioritizer-agent.git
cd gmail-prioritizer-agent
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Add Gmail OAuth credentials

Download your Google OAuth Desktop App credentials and save them as:

```text
credentials.json
```

Do not upload this file to GitHub.

### 5. Create your config file

```powershell
copy config.example.json config.json
```

Edit `config.json` and add your Gmail address.

### 6. Optional: Add OpenAI API key

```powershell
setx OPENAI_API_KEY "your_api_key_here"
```

Restart PowerShell after setting it.

If no OpenAI key is available, the agent uses rule-based classification.

### 7. Run dry-run mode first

```powershell
python gmail_prioritizer.py --dry-run
```

### 8. Run live mode

```powershell
python gmail_prioritizer.py
```

## Gmail API permissions

This project uses:

```text
https://www.googleapis.com/auth/gmail.modify
```

That scope allows the script to read and label Gmail messages.

## Safety notes

The agent does not delete emails. It only applies Gmail labels.

Files that must never be committed:

```text
credentials.json
token.json
config.json
.env
```

## Portfolio talking points

This project demonstrates:

- Gmail API integration
- OAuth authentication
- AI-assisted text classification
- Rule-based fallback logic
- Safe automation design
- Config-driven Python development

## Future improvements

- Add Streamlit dashboard
- Add weekly email analytics report
- Add calendar-aware urgency detection
- Add attachment summarization
- Add confidence score thresholding
