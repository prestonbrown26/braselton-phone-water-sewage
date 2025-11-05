# braselton_ai_agent

Backend scaffold for the Town of Braselton AI Phone Agent. This project provides a Flask-based service that processes LiveKit calls, runs AI dialogue with OpenAI GPT-4o Realtime, sends utility billing emails, and stores transcripts for compliance.

## Getting Started

### Local Development

1. Create a virtual environment and install dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Copy `env.example` to `.env` and populate the required secrets.

3. Run the development server:

   ```bash
   flask --app app:create_app --debug run
   ```

4. In a separate terminal, run the LiveKit agent worker:

   ```bash
   python livekit_worker.py start
   ```

5. Access the health endpoint at `http://localhost:5000/health` and the admin API at `http://localhost:5000/admin/calls`.

### Docker Compose

Start the full stack (web + PostgreSQL) with:

```bash
docker compose up --build
```

## Cloud Deployment

### Render

The app is currently deployed on Render with:
- **Web service**: Flask API backend
- **PostgreSQL**: Call logs database
- **Worker service** (optional): LiveKit agent for voice processing

To deploy updates:
1. Push to `main` branch
2. Render auto-deploys the web service
3. For the worker, create a **Background Worker** service in Render pointing to the same repo with start command: `python livekit_worker.py start`

Environment variables needed:
- `DATABASE_URL` - PostgreSQL connection string (auto-populated by Render)
- `OPENAI_API_KEY` - OpenAI API key for GPT-4o Realtime
- `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` - LiveKit credentials
- `BACKEND_URL` - URL of the Flask web service (e.g., `https://braselton-phone-water-sewage.onrender.com`)
- `ADMIN_USERNAME`, `ADMIN_PASSWORD` - Admin portal credentials
- `EMAIL_FROM_ADDRESS` - Verified sender email (optional, for testing)

### Azure (Future)

- Provision Azure resources following `infra/azure/README.md`.
- Populate GitHub Action secrets (`AZURE_CREDENTIALS`, `ACR_NAME`, `ACR_LOGIN_SERVER`, `AZURE_RESOURCE_GROUP`, `APP_SERVICE_NAME`).
- Push to `main` to trigger `.github/workflows/deploy.yaml`, which builds the container, pushes to ACR, and restarts the Azure App Service.

## Architecture

```
Phone Call (SIP) → LiveKit Cloud → LiveKit Worker (livekit_worker.py)
                                         ↓
                                   OpenAI Realtime API
                                   (STT → GPT-4o → TTS)
                                         ↓
                                   Flask Backend (/v1/intents)
                                         ↓
                                   PostgreSQL (call_logs table)
```

## API Endpoints

- `GET /health` - Health check
- `GET /` - Service info
- `POST /v1/intents` - Process user text and detect intent
- `POST /v1/process-audio` - Process audio chunks (legacy, replaced by LiveKit worker)
- `GET /admin/calls` - View call logs (requires basic auth)
- `GET /admin/export` - Download call logs as CSV

## Next Steps

- ✅ Flask backend with database
- ✅ LiveKit agent worker with OpenAI Realtime
- ✅ Intent detection and logging
- ⏸️ Email integration (waiting for domain access)
- 🔲 Phone number provisioning via SIP trunk
- 🔲 Call transfer to human agents
- 🔲 Production Azure deployment
- 🔲 Azure AD authentication for admin portal
