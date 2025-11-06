# Braselton AI Phone Agent - Retell AI Integration

Backend integration layer for the Town of Braselton AI Phone Agent. This Flask application receives webhooks from Retell AI to handle email sending, transcript storage, and monitoring alerts.

**Client:** Town of Braselton, GA  
**Department:** Water & Sewer Utilities  
**Contact:** Jennifer Scott (Town Manager), Blake Boyd (IT)

---

## 🏗️ Architecture

```
Phone Call → Retell AI → Webhooks → Flask (Azure) → PostgreSQL
                              ↓
                          SMTP2Go → Email to caller
                              ↓
                     Teams → Alerts to staff
```

### Components

| Component | Platform | Purpose |
|-----------|----------|---------|
| Voice Agent | Retell AI Cloud | Handles all calls, AI conversation, transfer routing |
| Phone Number | Retell AI | Built-in phone number (no Twilio needed) |
| Integration Layer | Azure Web App | Webhook handlers for email, logging, alerts |
| Database | Azure PostgreSQL | 5-year transcript retention (state law) |
| Email Service | SMTP2Go | Sends payment links and forms to callers |
| Monitoring | Microsoft Teams | Alerts for negative sentiment calls |

---

## 🚀 Quick Start

### Local Development

1. **Clone and setup:**
   ```bash
   cd braselton-phone-water-sewage
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp env.example .env
   # Edit .env with your credentials
   ```

3. **Initialize database:**
   ```bash
   python init_db.py
   ```

4. **Run development server:**
   ```bash
   flask --app app:app --debug run
   ```

5. **Access endpoints:**
   - Main: http://localhost:5000/
   - Health: http://localhost:5000/health
   - Admin: http://localhost:5000/admin/transcripts

### Docker Compose

```bash
docker compose up --build
```

Access at http://localhost:8000

---

## 🔧 Configuration

### Required Environment Variables

```bash
# Database (provided by Azure)
DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/dbname

# Retell AI (from Retell dashboard)
RETELL_API_KEY=your_retell_api_key

# SMTP2Go (coordinate with Blake for DNS)
SMTP2GO_USERNAME=your_smtp_username
SMTP2GO_PASSWORD=your_smtp_password
EMAIL_FROM_ADDRESS=utilitybilling@braselton.net

# Teams webhook (Blake will provide)
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/...

# Admin portal
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure_password_here

# Optional
TOWN_WEBSITE_URL=https://braselton.net
LOG_LEVEL=INFO
```

---

## 📡 Webhook Endpoints

### 1. Email Webhook (`POST /webhook/email`)

**Triggered by:** Retell AI agent when caller needs email

**Request:**
```json
{
  "call_id": "abc123",
  "caller_phone": "+17705551234",
  "email_type": "payment_link | adjustment_form | general_info",
  "user_email": "resident@example.com"
}
```

**Response:**
```json
{
  "status": "sent",
  "email_type": "payment_link"
}
```

**Email Templates:**
- `payment_link` - Online payment portal link
- `adjustment_form` - Billing adjustment form
- `general_info` - Contact information

---

### 2. Transcript Webhook (`POST /webhook/transcript`)

**Triggered by:** Retell AI when call ends

**Request:**
```json
{
  "call_id": "abc123",
  "caller_phone": "+17705551234",
  "duration_seconds": 127,
  "transcript": "Full conversation text here...",
  "timestamp": "2025-11-06T14:30:00Z",
  "transferred": false,
  "sentiment": "positive | neutral | negative"
}
```

**Response:**
```json
{
  "status": "stored",
  "id": 42
}
```

**Retention:** 5 years per Georgia state law LG 20-022

---

### 3. Alert Webhook (`POST /webhook/alert`)

**Triggered by:** Retell AI on negative sentiment or abandoned calls

**Request:**
```json
{
  "alert_type": "negative_sentiment | abandoned_call",
  "call_id": "abc123",
  "caller_phone": "+17705551234",
  "transcript": "Conversation snippet...",
  "details": "Caller expressed frustration with billing"
}
```

**Response:**
```json
{
  "status": "alerted"
}
```

**Action:** Sends Teams message to Blake's monitoring channel

---

## 👨‍💼 Admin Portal

### Transcript Search

**URL:** `/admin/transcripts`

**Authentication:** Basic Auth (ADMIN_USERNAME / ADMIN_PASSWORD)

**Features:**
- Search by call ID, phone number, or date
- View full transcripts
- See sentiment, duration, transfer status
- Export as CSV

Per Blake's requirement: *"just need to put in call ID and get the transcript"*

### CSV Export

**URL:** `/admin/export`

Downloads all call logs as CSV for compliance/archival.

---

## 🎯 Retell AI Setup

### 1. Access Account

Blake has invited you to: `brownpreston2490@gmail.com`

Login at: https://retellai.com

### 2. Create Voice Agent

**System Prompt:**
```
You are a helpful assistant for the Town of Braselton Utilities Department in Georgia.

You help residents with:
- Questions about water, sewer, and sanitation services
- Billing information and payment options
- Service hours and contact information

IMPORTANT RULES:
1. Be professional, friendly, and concise (2-3 sentences max)
2. If someone wants to speak to a person, transfer immediately
3. For billing payments, offer to send an email with payment link
4. Never make up information - if unsure, transfer to staff
5. If frustrated caller, transfer to human

TRANSFER SCENARIOS:
- User asks for a person/representative
- Complex questions requiring account access
- Frustrated or unhappy caller
- Emergency situations

GREETING:
"Hello! Thanks for calling Braselton Utilities. How can I help you today?"
```

### 3. Configure Webhooks

In Retell AI dashboard → Settings → Webhooks:

**Email webhook:**
- URL: `https://your-azure-app.azurewebsites.net/webhook/email`
- Trigger: Custom action when agent says "I'll send you an email"

**Transcript webhook:**
- URL: `https://your-azure-app.azurewebsites.net/webhook/transcript`
- Trigger: Call ended

**Alert webhook:**
- URL: `https://your-azure-app.azurewebsites.net/webhook/alert`
- Trigger: Negative sentiment OR call abandonment

### 4. Set Up Call Transfer

**Transfer numbers** (get from Jennifer):
- Billing questions: [BILLING_NUMBER]
- Emergencies: [EMERGENCY_NUMBER]
- General: [MAIN_OFFICE]

### 5. Upload Knowledge Base

Upload FAQ document covering:
- Payment methods and locations
- Service hours
- Utility rates
- Common troubleshooting
- Emergency procedures

---

## ☁️ Azure Deployment

### Prerequisites

- Azure account with subscription
- Azure CLI installed
- Resource group created

### 1. Create Resources

```bash
# Login
az login

# Create resource group (if not exists)
az group create --name braselton-rg --location eastus

# Create PostgreSQL database
az postgres flexible-server create \
  --name braselton-db \
  --resource-group braselton-rg \
  --location eastus \
  --admin-user dbadmin \
  --admin-password YourSecurePassword123! \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32

# Create database
az postgres flexible-server db create \
  --resource-group braselton-rg \
  --server-name braselton-db \
  --database-name braselton

# Create App Service plan
az appservice plan create \
  --name braselton-plan \
  --resource-group braselton-rg \
  --sku B1 \
  --is-linux

# Create web app
az webapp create \
  --name braselton-utilities-agent \
  --resource-group braselton-rg \
  --plan braselton-plan \
  --runtime "PYTHON:3.11"
```

### 2. Configure App Settings

```bash
az webapp config appsettings set \
  --name braselton-utilities-agent \
  --resource-group braselton-rg \
  --settings \
    DATABASE_URL="postgresql+psycopg2://dbadmin:YourPassword@braselton-db.postgres.database.azure.com:5432/braselton" \
    RETELL_API_KEY="your_retell_key" \
    SMTP2GO_USERNAME="your_smtp_user" \
    SMTP2GO_PASSWORD="your_smtp_pass" \
    EMAIL_FROM_ADDRESS="utilitybilling@braselton.net" \
    TEAMS_WEBHOOK_URL="your_teams_webhook" \
    ADMIN_USERNAME="admin" \
    ADMIN_PASSWORD="secure_password"
```

### 3. Deploy Code

```bash
# From project root
az webapp up \
  --name braselton-utilities-agent \
  --resource-group braselton-rg
```

### 4. Initialize Database

```bash
# SSH into app
az webapp ssh --name braselton-utilities-agent --resource-group braselton-rg

# Run migrations
python init_db.py
```

### 5. Verify Deployment

```
https://braselton-utilities-agent.azurewebsites.net/
https://braselton-utilities-agent.azurewebsites.net/health
https://braselton-utilities-agent.azurewebsites.net/admin/transcripts
```

---

## 📧 SMTP2Go Setup (Blake's Instructions)

### 1. Create SMTP2Go Account

Town pays directly: https://www.smtp2go.com

### 2. Configure Sending Address

- From address: `utilitybilling@braselton.net`
- Get SMTP credentials from dashboard

### 3. DNS Configuration (Blake)

**SPF Record:**
```
TXT @ v=spf1 include:smtp2go.com ~all
```

**DKIM Record:**
(SMTP2Go will provide)

### 4. Test Email Delivery

```bash
curl -X POST https://your-app.azurewebsites.net/webhook/email \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "test123",
    "email_type": "payment_link",
    "user_email": "your-test@email.com"
  }'
```

Check that email arrives and replies go to shared mailbox.

---

## 📊 Monitoring

### Call Volume Stats

From Blake's data:
- **3,083 calls/month** average
- **57 seconds** average call duration
- **3,200 minutes/month** total

### Cost Estimate

| Item | Monthly Cost |
|------|--------------|
| Retell AI | $224 (3,200 min @ $0.07/min) |
| Azure Web App (B1) | $13 |
| Azure PostgreSQL (Basic) | $10 |
| SMTP2Go | $0 (free tier) |
| **Total** | **~$247/month** |

### Teams Alerts

Alerts sent when:
- ⚠️ Negative sentiment detected
- 📞 Call abandoned without resolution
- 🔄 Multiple transfer requests

Blake's team gets notification with:
- Call ID
- Caller number
- Transcript preview
- Link to full transcript

---

## 🔒 Security & Compliance

### State Law Requirements (GA LG 20-022)

**Retention periods:**
- Utility account communication: **5 years**
- Dispute-related: **Until resolved + 5 years**
- Emergency-related: **5 years after resolution**

**Solution:** Store ALL transcripts for 5 years (simplest per Blake)

### Data Protection

- Admin portal requires authentication
- Database credentials in Azure Key Vault (recommended)
- HTTPS only in production
- Regular backups enabled

### Privacy

- Call recording disclosure (handled by Retell AI greeting)
- No PII exposed in webhooks
- Transcripts stored encrypted at rest (Azure)

---

## 🧪 Testing

### Test Webhooks Locally

```bash
# Start local server
flask --app app:app run

# Test email webhook
curl -X POST http://localhost:5000/webhook/email \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "test1",
    "email_type": "payment_link",
    "user_email": "test@example.com"
  }'

# Test transcript webhook
curl -X POST http://localhost:5000/webhook/transcript \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "test2",
    "caller_phone": "+17705551234",
    "transcript": "Test call transcript",
    "duration_seconds": 60,
    "sentiment": "positive"
  }'
```

### Admin Portal

1. Visit http://localhost:5000/admin/transcripts
2. Login with admin/changeme
3. Search for call_id "test2"
4. Verify transcript appears

---

## 📝 API Reference

### Health Check

```
GET /health
```

Response:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### Admin Endpoints

All require Basic Auth (ADMIN_USERNAME / ADMIN_PASSWORD)

```
GET  /admin/calls                    - View recent calls
GET  /admin/transcripts              - Search transcripts
GET  /admin/transcripts?call_id=abc  - Search by call ID
GET  /admin/transcripts?phone=770    - Search by phone
GET  /admin/transcripts?date=2025-11-06  - Search by date
GET  /admin/export                   - Export all as CSV
```

---

## 🐛 Troubleshooting

### Emails Not Sending

1. Check SMTP2Go credentials in environment
2. Verify SPF/DKIM records with Blake
3. Check SMTP2Go dashboard for errors
4. Test with curl to /webhook/email

### Transcripts Not Storing

1. Check DATABASE_URL is correct
2. Run `python init_db.py` to create tables
3. Check Flask logs for database errors
4. Verify PostgreSQL is accepting connections

### Teams Alerts Not Working

1. Verify TEAMS_WEBHOOK_URL is set
2. Test webhook URL in Teams channel
3. Check pymsteams is installed
4. Review Flask logs for send errors

### Retell Webhooks Failing

1. Verify Azure app is publicly accessible
2. Check Retell dashboard for webhook errors
3. Test webhooks with curl locally first
4. Review Retell webhook logs

---

## 📞 Support Contacts

**Town of Braselton:**
- Jennifer Scott (Town Manager): jennifer@braselton.net
- Blake Boyd (IT): blake@braselton.net

**Developer:**
- Preston Brown / Smartagen AI
- preston@smartagen.ai
- 407-701-0667

**Platforms:**
- Retell AI: https://docs.retellai.com
- Azure Support: https://portal.azure.com
- SMTP2Go: https://www.smtp2go.com/support

---

## 📄 License

Proprietary - Town of Braselton, GA

All accounts owned and paid directly by the Town of Braselton per project agreement.

---

## 🚀 Next Steps

- [ ] Accept Retell AI invite (brownpreston2490@gmail.com)
- [ ] Build voice agent in Retell with FAQs
- [ ] Deploy Flask app to Azure
- [ ] Coordinate SMTP2Go setup with Blake
- [ ] Get Teams webhook URL from Blake
- [ ] Get transfer phone numbers from Jennifer
- [ ] Test all webhooks end-to-end
- [ ] Internal testing with Blake/Jennifer
- [ ] Purchase/configure phone number
- [ ] Forward main line to Retell
- [ ] Monitor first 100 calls
- [ ] Go live! 🎉
