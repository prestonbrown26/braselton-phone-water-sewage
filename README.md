## Braselton Utilities Voice Agent

Flask app that receives Retell AI webhooks, logs calls to Postgres, and sends billing emails through SMTP2Go.

### Prerequisites
- Python 3.11+
- PostgreSQL URL (e.g., from Render/Azure)
- SMTP2Go credentials (host, port, username, password)

### Setup
1) Create a virtualenv and install deps:
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
2) Copy env template and fill values:
```
cp env.example .env
```
3) Initialize the database:
```
python init_db.py
```
4) Run locally:
```
flask --app app:app --debug run
```

### Key URLs
- Health: `/health`
- Admin dashboard: `/admin`
- Admin transcripts: `/admin/transcripts`
- Admin call logs: `/admin/calls`
- Admin email templates: `/admin/email-templates`

### Webhooks to configure in Retell AI
- Email: `POST /webhook/email`
- Transcript: `POST /webhook/transcript`
- Transfer: `POST /webhook/transfer`

### Deployment tips
- Set the same env vars in Render/Azure as in `.env`.
- Keep `EMAIL_STUB_MODE=true` in staging to log emails without sending.
- Flip `EMAIL_STUB_MODE=false` in production once SMTP2Go DNS and credentials are verified.


