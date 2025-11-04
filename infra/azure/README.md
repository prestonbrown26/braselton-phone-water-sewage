# Azure Deployment Guide

This guide walks through provisioning Azure resources and configuring the CI/CD pipeline for the Braselton AI Agent backend.

## 1. Prerequisites

- Azure subscription with permissions to create resource groups, App Service, Azure Database for PostgreSQL, and Azure Container Registry (ACR)
- Azure CLI `az` (v2.55 or later)
- Access to GitHub repository settings for configuring secrets

Set reusable parameters:

```bash
LOCATION=eastus
RESOURCE_GROUP=rg-braselton-ai
ACR_NAME=braseltonacr
APP_SERVICE_PLAN=asp-braselton-ai
APP_SERVICE_NAME=app-braselton-ai
POSTGRES_SERVER=pg-braselton-ai
POSTGRES_DB=braselton
POSTGRES_USER=braselton_admin
```

## 2. Provision Azure Resources

Create the resource group:

```bash
az group create --name $RESOURCE_GROUP --location $LOCATION
```

### 2.1 Azure Container Registry

```bash
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Standard \
  --admin-enabled false
```

### 2.2 App Service Plan + Web App (Linux Container)

```bash
az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --is-linux \
  --sku P1v3

az webapp create \
  --name $APP_SERVICE_NAME \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --deployment-container-image-name mcr.microsoft.com/azuredocs/containerapps-helloworld:latest
```

Grant the App Service access to pull from ACR:

```bash
ACR_ID=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query "id" -o tsv)
az webapp config container set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_SERVICE_NAME \
  --docker-custom-image-name $ACR_NAME.azurecr.io/placeholder:latest \
  --docker-registry-server-url https://$ACR_NAME.azurecr.io

az webapp identity assign --name $APP_SERVICE_NAME --resource-group $RESOURCE_GROUP
PRINCIPAL_ID=$(az webapp identity show --name $APP_SERVICE_NAME --resource-group $RESOURCE_GROUP --query principalId -o tsv)
az role assignment create --assignee-object-id $PRINCIPAL_ID --assignee-principal-type ServicePrincipal --scope $ACR_ID --role "AcrPull"
```

### 2.3 Azure Database for PostgreSQL Flexible Server

```bash
az postgres flexible-server create \
  --name $POSTGRES_SERVER \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku-name Standard_D2s_v3 \
  --storage-size 128 \
  --version 15 \
  --database-name $POSTGRES_DB \
  --administrator-user $POSTGRES_USER

# Configure firewall for App Service outbound IPs (replace placeholders)
az postgres flexible-server firewall-rule create \
  --resource-group $RESOURCE_GROUP \
  --name $POSTGRES_SERVER \
  --rule-name allow-app-service \
  --start-ip-address <APP_SERVICE_OUTBOUND_IP> \
  --end-ip-address <APP_SERVICE_OUTBOUND_IP>
```

> ⚠️ Replace `<APP_SERVICE_OUTBOUND_IP>` with the outbound IPs listed via `az webapp show --resource-group $RESOURCE_GROUP --name $APP_SERVICE_NAME --query outboundIpAddresses -o tsv`.

## 3. Configure App Settings

Set required environment variables on the web app:

```bash
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_SERVICE_NAME \
  --settings \
    FLASK_ENV=production \
    DATABASE_URL="postgresql+psycopg2://$POSTGRES_USER:<PASSWORD>@${POSTGRES_SERVER}.postgres.database.azure.com:5432/$POSTGRES_DB" \
    LIVEKIT_URL=<LIVEKIT_URL> \
    LIVEKIT_API_KEY=<LIVEKIT_API_KEY> \
    LIVEKIT_API_SECRET=<LIVEKIT_API_SECRET> \
    OPENAI_API_KEY=<OPENAI_API_KEY> \
    SMTP2GO_SMTP_HOST=smtp.smtp2go.com \
    SMTP2GO_SMTP_PORT=587 \
    SMTP2GO_USERNAME=<SMTP2GO_USERNAME> \
    SMTP2GO_PASSWORD=<SMTP2GO_PASSWORD> \
    TEAMS_WEBHOOK_URL=<TEAMS_WEBHOOK_URL> \
    ADMIN_USERNAME=<ADMIN_USERNAME> \
    ADMIN_PASSWORD=<ADMIN_PASSWORD> \
    LOG_LEVEL=INFO
```

Consider storing secrets in Azure Key Vault and referencing them in App Service once the vault is provisioned.

## 4. GitHub Secrets

Add the following secrets to the repository (Settings → Secrets and variables → Actions):

| Secret | Description |
| --- | --- |
| `AZURE_CREDENTIALS` | Output of `az ad sp create-for-rbac --name braselton-gha --role contributor --scopes /subscriptions/<SUB_ID>/resourceGroups/$RESOURCE_GROUP --sdk-auth` |
| `AZURE_RESOURCE_GROUP` | Name of the resource group (`$RESOURCE_GROUP`) |
| `ACR_NAME` | Azure Container Registry name |
| `ACR_LOGIN_SERVER` | Usually `<acr_name>.azurecr.io` |
| `APP_SERVICE_NAME` | Web app name |

> The generated service principal should be stored securely. Rotate its secret per policy.

## 5. First Deployment

1. Commit the code and push to `main` (or trigger the workflow manually via **Run workflow**).
2. The GitHub Action builds the Docker image, pushes to ACR, and updates the running App Service.
3. Monitor App Service logs with `az webapp log tail --name $APP_SERVICE_NAME --resource-group $RESOURCE_GROUP`.
4. Visit `https://<APP_SERVICE_NAME>.azurewebsites.net/health` to verify the deployment.

## 6. Database Migrations

Add Alembic (or Flask-Migrate) before production rollout:

```bash
pip install alembic
alembic init migrations
```

Check migrations into source control and run `alembic upgrade head` against the Azure PostgreSQL instance during deployment.

## 7. Additional Hardening

- Restrict `/admin` to Braselton IP ranges using App Service access restrictions.
- Swap basic auth to Azure AD via App Service Authentication (Easy Auth) when ready.
- Configure Application Insights and connect logs to Log Analytics for long-term retention.
- Set up backup/snapshot policy for the PostgreSQL Flexible Server.

