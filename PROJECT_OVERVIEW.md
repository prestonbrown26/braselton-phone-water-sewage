# Braselton AI Phone Agent - Project Overview

AI-powered phone agent for the Town of Braselton Utilities Department.

---

## 📁 Project Structure

```
braselton-phone-water-sewage/
├── app/                          # Flask application
│   ├── __init__.py              # App factory & config
│   ├── admin.py                 # Admin portal routes
│   ├── email_utils.py           # SMTP2Go email integration
│   ├── health.py                # Health check endpoint
│   ├── models.py                # Database models (CallLog)
│   ├── routes.py                # Retell AI webhook handlers
│   └── templates/
│       ├── admin_calls.html     # Call log listing
│       └── admin_transcripts.html  # Transcript search UI
│
├── infra/                       # Infrastructure configs
│   └── azure/
│       └── README.md            # Azure deployment guide
│
├── app.py                       # Gunicorn entry point
├── init_db.py                   # Database initialization script
├── requirements.txt             # Python dependencies
├── Procfile                     # Render/Heroku deployment config
├── Dockerfile                   # Docker container config
├── docker-compose.yml           # Local Docker setup
├── env.example                  # Environment variables template
│
├── GETTING_STARTED.md           # ⭐ START HERE - Choose your path
├── RENDER_DEPLOY.md             # ⭐ Prototype deployment guide
├── SETUP_GUIDE.md               # Production setup with Blake
├── CHECKLIST.md                 # Printable deployment checklist
└── README.md                    # Technical documentation
```

---

## 🎯 What It Does

**For Residents:**
- Call a phone number
- Get answers to common utility questions
- Receive payment links via email
- Transfer to staff when needed

**For Staff:**
- View all call transcripts (5-year retention)
- Search calls by ID, phone, or date
- Monitor call volume and patterns
- Export call logs for compliance

---

## 🏗️ Architecture

```
Resident → Phone Call → Retell AI → Webhooks → Flask App → Database
                                            ↓
                                     Email (SMTP2Go)
```

**Components:**
- **Retell AI**: Handles voice, AI, call routing (cloud service)
- **Flask App**: Webhook integration, email, transcript storage (Render/Azure)
- **PostgreSQL**: 5-year call log retention (Render/Azure)
- **SMTP2Go**: Email delivery (free tier)

---

## 📚 Documentation Guide

### Getting Started
- **`GETTING_STARTED.md`** - Start here! Tells you which guide to use

### Deployment Guides
- **`RENDER_DEPLOY.md`** - Deploy prototype on Render (2-3 hours, independent)
- **`SETUP_GUIDE.md`** - Production deployment with Blake (after approval)
- **`CHECKLIST.md`** - Printable step-by-step checklist

### Technical Reference
- **`README.md`** - Complete technical documentation
- **`infra/azure/README.md`** - Azure-specific deployment steps

---

## 🚀 Quick Start Paths

### Path 1: Build Prototype (Recommended)
1. Open `RENDER_DEPLOY.md`
2. Deploy to Render yourself (all free tiers)
3. Configure Retell AI voice agent
4. Get working phone number
5. Demo to Blake/Jennifer
6. Get approval

**Time:** 2-3 hours  
**Cost:** ~$3-4

### Path 2: Production Deployment
1. Get approval from Blake/Jennifer
2. Open `SETUP_GUIDE.md`
3. Coordinate with Blake for Azure
4. Deploy to production
5. Go live

**Time:** 1-2 weeks  
**Cost:** ~$240/month

---

## 🛠️ Technology Stack

**Backend:**
- Python 3.11
- Flask 3.0
- PostgreSQL 15
- Gunicorn

**Voice Agent:**
- Retell AI (cloud platform)
- GPT-4 powered conversations
- Built-in STT/TTS

**Email:**
- SMTP2Go (free tier)

**Hosting:**
- Prototype: Render (free tier)
- Production: Azure or Render paid

---

## 🔑 Key Features

- ✅ Natural conversation AI
- ✅ FAQ knowledge base
- ✅ Email payment links
- ✅ Call transfer to staff
- ✅ 5-year transcript retention (GA law LG 20-022)
- ✅ Admin search portal
- ✅ CSV export for compliance

---

## 💰 Costs

### Prototype (Testing)
- Render: $0 (free tier)
- Database: $0 (free tier)
- SMTP2Go: $0 (free tier)
- Retell AI: ~$1-2 (test calls)
- **Total: ~$3-4**

### Production (3,200 min/month)
- Retell AI: $224/month
- Hosting: $7-23/month
- Database: $7-10/month
- SMTP2Go: $0 (free)
- **Total: ~$238-257/month**

---

## 👥 Team

**Town of Braselton:**
- Jennifer Scott (Town Manager)
- Blake Boyd (IT)

**Developer:**
- Preston Brown / Smartagen AI
- preston@smartagen.ai
- 407-701-0667

---

## 📋 Current Status

- ✅ Codebase complete (Retell AI architecture)
- ✅ Documentation complete
- ✅ Ready for prototype deployment
- ⏳ Awaiting prototype testing
- ⏳ Awaiting Blake/Jennifer approval
- ⏳ Production deployment pending

---

## 🎯 Next Steps

1. **You:** Deploy prototype using `RENDER_DEPLOY.md`
2. **You:** Test thoroughly
3. **You:** Demo to Blake/Jennifer
4. **Blake/Jennifer:** Approve and provide production info
5. **You + Blake:** Deploy to production using `SETUP_GUIDE.md`
6. **All:** Monitor and optimize

---

## 📞 Support

**Questions about:**
- Deployment: See `RENDER_DEPLOY.md` or `SETUP_GUIDE.md`
- Technical details: See `README.md`
- Retell AI: https://docs.retellai.com
- Preston: preston@smartagen.ai

---

**Ready to start?** → Open `GETTING_STARTED.md`

