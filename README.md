# braselton_ai_agent

Backend scaffold for the Town of Braselton AI Phone Agent. This project provides a Flask-based service that processes LiveKit calls, runs AI dialogue with OpenAI GPT-4o Realtime, sends utility billing emails, and stores transcripts for compliance.

## Getting Started

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

4. Access the health endpoint at `http://localhost:5000/health` and the admin API at `http://localhost:5000/admin/calls`.

## Docker Compose

Start the full stack (web + PostgreSQL) with:

```bash
docker compose up --build
```

## Next Steps

- Integrate LiveKit's Python SDK within `app/routes.py:/ws`.
- Connect OpenAI Realtime STT/TTS in `app/ai_logic.py`.
- Harden authentication via Azure AD when moving to production.
- Add observability (metrics, structured logging, tracing).

## Cloud Deployment

- Provision Azure resources following `infra/azure/README.md`.
- Populate GitHub Action secrets (`AZURE_CREDENTIALS`, `ACR_NAME`, `ACR_LOGIN_SERVER`, `AZURE_RESOURCE_GROUP`, `APP_SERVICE_NAME`).
- Push to `main` to trigger `.github/workflows/deploy.yaml`, which builds the container, pushes to ACR, and restarts the Azure App Service.

