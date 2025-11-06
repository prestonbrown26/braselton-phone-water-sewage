# Getting Started - Choose Your Path

Two ways to get started with the Braselton AI Phone Agent:

---

## 🚀 **Option 1: Build Prototype on Render (Recommended)**

**Best for:** Testing independently before involving Blake/Jennifer

- ✅ Deploy everything yourself
- ✅ No need to coordinate with Blake yet
- ✅ Working demo in 2-3 hours
- ✅ Show them a live phone number they can call
- ✅ Only ~$3-4 for testing
- ✅ Get approval before production setup

**👉 Follow:** [RENDER_DEPLOY.md](./RENDER_DEPLOY.md)

This is the **fastest way** to have a working phone agent to demo.

---

## 🏢 **Option 2: Production Setup (Azure with Blake)**

**Best for:** After demo approval, deploying to production

- Requires Blake's help for Azure
- Requires Jennifer's FAQ content
- More secure, town-managed infrastructure
- Full production deployment

**👉 Follow:** [SETUP_GUIDE.md](./SETUP_GUIDE.md)

Do this **after** Blake and Jennifer approve the prototype.

---

## 📋 **Recommended Flow**

### Week 1: Build Prototype
1. Follow `RENDER_DEPLOY.md`
2. Deploy to Render yourself
3. Set up Retell AI voice agent
4. Get working phone number
5. Test everything

### Week 2: Demo & Get Approval
1. Email Blake/Jennifer with test number
2. Demo in 30-minute meeting
3. Get feedback on voice, answers, tone
4. Get go-ahead for production

### Week 3: Production Deployment
1. Follow `SETUP_GUIDE.md` with Blake's help
2. Deploy to Azure
3. Configure production settings
4. Soft launch during business hours
5. Monitor and tune

### Week 4: Go Live
1. Full 24/7 launch
2. Monthly monitoring
3. Update FAQs as needed

---

## 🎯 **Start Here**

**Right now, go to:** [RENDER_DEPLOY.md](./RENDER_DEPLOY.md)

Follow it step-by-step to have a working prototype by end of day.

---

## 📚 **All Documentation**

- **RENDER_DEPLOY.md** ⭐ - Deploy prototype on Render (start here!)
- **SETUP_GUIDE.md** - Production setup with Blake (after approval)
- **README.md** - Full technical documentation
- **QUICKSTART.md** - 15-minute local testing
- **RETELL_SETUP.md** - Detailed Retell AI configuration
- **COST_ANALYSIS.md** - LiveKit vs Retell AI comparison
- **MIGRATION_SUMMARY.md** - What changed from LiveKit

---

## ❓ **Which Guide Should I Use?**

**"I want to test this myself first"**  
→ Use `RENDER_DEPLOY.md`

**"Blake/Jennifer already approved, let's go to production"**  
→ Use `SETUP_GUIDE.md`

**"I want to test locally on my laptop"**  
→ Use `QUICKSTART.md`

**"I need detailed Retell AI settings"**  
→ Use `RETELL_SETUP.md`

**"I need full technical details"**  
→ Use `README.md`

---

## 💡 **Quick Summary**

This is a phone agent for Braselton Utilities that:
- Answers common questions about water/sewer
- Sends payment links via email
- Transfers to staff when needed
- Stores all call transcripts (5-year retention)

**Tech Stack:**
- Retell AI (voice agent)
- Flask (webhook integration)
- PostgreSQL (call storage)
- SMTP2Go (email)

**Monthly Cost:** ~$240 (mostly Retell AI usage)

---

**Ready? Go to [RENDER_DEPLOY.md](./RENDER_DEPLOY.md) and start building!**

