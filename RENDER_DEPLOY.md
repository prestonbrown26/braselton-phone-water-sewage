# Deploy to Render - Complete Prototype

Deploy the entire Braselton phone agent on Render yourself to create a working demo.

**Goal:** Have a fully working phone agent to show Blake and Jennifer before asking for their help.

---

## What You'll Build

- ✅ Web app hosted on Render
- ✅ PostgreSQL database on Render
- ✅ Email sending via SMTP2Go (free tier)
- ✅ Voice agent on Retell AI
- ✅ Working phone number you can call
- ✅ Admin portal to view calls

**Time:** 2-3 hours  
**Cost:** $0 for testing (all free tiers)

---

## Step 1: Deploy to Render (15 minutes)

### 1.1 Create Render Account

1. Go to: https://render.com
2. Sign up with GitHub (easiest)
3. Verify email

### 1.2 Push Code to GitHub

```bash
cd braselton-phone-water-sewage

# Initialize git if not already
git init
git add .
git commit -m "Initial commit - Braselton phone agent"

# Create repo on GitHub
# Go to github.com → New Repository
# Name: braselton-phone-agent
# Don't initialize with README (you already have code)

# Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/braselton-phone-agent.git
git push -u origin main
```

### 1.3 Create PostgreSQL Database

1. Login to Render dashboard
2. Click **"New +"** → **"PostgreSQL"**
3. Settings:
   - **Name:** `braselton-db`
   - **Database:** `braselton`
   - **User:** `braselton_user`
   - **Region:** Oregon (US West) or Ohio (US East)
   - **Plan:** **Free** (good for testing)
4. Click **"Create Database"**
5. Wait ~2 minutes for creation
6. **Copy the "Internal Database URL"** - you'll need this!

### 1.4 Create Web Service

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repo
3. If prompted, give Render access to your repos
4. Select: `braselton-phone-agent`
5. Settings:
   - **Name:** `braselton-phone-agent`
   - **Environment:** `Python 3`
   - **Region:** Same as database (Oregon or Ohio)
   - **Branch:** `main`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn -w 4 -b 0.0.0.0:$PORT app:app`
   - **Plan:** **Free** (for testing)

### 1.5 Add Environment Variables

Click **"Advanced"** → **"Add Environment Variable"**

Add these (one at a time):

```bash
# Database (paste the Internal URL from step 1.3)
DATABASE_URL=postgresql://braselton_user:...@...

# Admin portal (you choose the password)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=test123

# Basic config
SECRET_KEY=dev-secret-key-for-testing
TOWN_WEBSITE_URL=https://braselton.net
LOG_RETENTION_DAYS=1825

# Leave these empty for now (add in Step 2)
SMTP2GO_USERNAME=
SMTP2GO_PASSWORD=
EMAIL_FROM_ADDRESS=utilitybilling@braselton.net
RETELL_API_KEY=
```

6. Click **"Create Web Service"**
7. Wait 3-5 minutes for deployment
8. Render will show build logs

### 1.6 Initialize Database

After deployment finishes:

1. In Render dashboard, click your web service
2. Click **"Shell"** tab
3. Run:
   ```bash
   python init_db.py
   ```
4. Should see: "Database initialized successfully" or similar

### 1.7 Test It Works

Your app URL will be: `https://braselton-phone-agent.onrender.com`

Visit: `https://braselton-phone-agent.onrender.com/health`

Should see:
```json
{"status": "healthy", "database": "connected"}
```

✅ **Step 1 Complete!** Web app is live.

---

## Step 2: Set Up Email (20 minutes)

### 2.1 Create SMTP2Go Account

1. Go to: https://www.smtp2go.com
2. Click **"Sign Up"**
3. Use your personal email for now (can transfer to Braselton later)
4. Choose **Free Plan** (1,000 emails/month)
5. Verify email

### 2.2 Get SMTP Credentials

1. Login to SMTP2Go dashboard
2. Click **"Settings"** → **"Users"**
3. You'll see a default user already created
4. Click **"Show Password"** or **"Create New User"**
5. **Save the username and password**

### 2.3 Add to Render

1. Go back to Render dashboard
2. Click your web service
3. Click **"Environment"** tab
4. Edit these variables:
   ```bash
   SMTP2GO_USERNAME=your_smtp_username
   SMTP2GO_PASSWORD=your_smtp_password
   ```
5. Click **"Save Changes"**
6. App will auto-redeploy (~1 minute)

### 2.4 Test Email Sending

```bash
curl -X POST https://braselton-phone-agent.onrender.com/webhook/email \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "test_001",
    "email_type": "payment_link",
    "user_email": "YOUR_EMAIL@gmail.com"
  }'
```

**Important:** First time might fail because SMTP2Go needs to verify your sending.

If it says "sender not verified":
1. Go to SMTP2Go → **Settings** → **Sender Addresses**
2. Add your email address
3. Verify it (check email for verification link)
4. Try test again

Check your inbox - should get payment link email!

✅ **Step 2 Complete!** Emails working.

---

## Step 3: Set Up Retell AI (60 minutes)

### 3.1 Create Retell AI Account

**Note:** Blake already invited `brownpreston2490@gmail.com`. Use that OR create your own account for testing.

**Option A: Use Existing Invite (Recommended)**
1. Check email for Retell AI invite
2. Accept and create password
3. Login to: https://app.retellai.com

**Option B: Create New Account (For Independent Testing)**
1. Go to: https://retellai.com
2. Sign up with your email
3. Choose free trial or pay-as-you-go

### 3.2 Create Voice Agent

1. Click **"Agents"** → **"Create Agent"**
2. **Name:** Braselton Utilities Test
3. **Voice:** Click different voices to preview
   - Recommended: `Joanna`, `Matthew`, or `Samantha`
   - Pick one that sounds professional
4. Click **"Create"**

### 3.3 Add System Prompt

Click **"Agent Configuration"** and paste this in **System Instructions**:

```
You are a friendly customer service assistant for the Town of Braselton Utilities Department.

WHAT YOU DO:
- Answer questions about water, sewer, and sanitation services
- Help with billing and payment information
- Transfer to staff when needed

RULES:
1. Keep responses SHORT - 2 sentences maximum
2. Be friendly but professional
3. If caller asks for a person, transfer immediately
4. If you don't know the answer, offer to transfer

PAYMENT REQUESTS:
When caller wants to pay bill:
- Say: "I can send you a link to pay online. What's your email address?"
- After they give email, say: "Perfect! I'll send that to [email] right now."

GREETING:
"Hello! Thanks for calling Braselton Utilities. How can I help you today?"

TRANSFER PHRASES:
If caller says "speak to someone", "representative", "manager", or "person":
- Say: "Of course! Let me transfer you now."
- Transfer immediately
```

Click **"Save"**.

### 3.4 Add Knowledge Base

Click **"Knowledge Base"** tab → **"Add Knowledge"**

Add these Q&A pairs manually (click "Add Q&A"):

**Q:** What are your office hours?  
**A:** Monday through Friday, 8 AM to 5 PM. We're closed on weekends and holidays.

**Q:** Where can I pay my water bill?  
**A:** You can pay online at braselton.net/pay, or in person at Town Hall with cash, check, or money order.

**Q:** Can I pay by credit card over the phone?  
**A:** No, but I can send you a link to pay online with a credit card. What's your email address?

**Q:** What's your phone number?  
**A:** Our main number is 770-867-4488.

**Q:** Where are you located?  
**A:** We're at 6111 Winder Highway, Braselton, GA 30517.

**Q:** How do I report a water emergency?  
**A:** For water emergencies, please let me transfer you to our emergency line right away.

Add more as needed. Click **"Save"** after each.

### 3.5 Configure Call Transfer

Click **"Call Transfer"** tab → **"Add Transfer"**

**For testing, use your own number:**
1. **Name:** Emergency/Support
2. **Number:** Your cell phone (format: +17705551234)
3. **Trigger Phrases:**
   ```
   speak to someone
   talk to a person
   representative
   manager
   transfer me
   emergency
   ```

Click **"Save"**.

### 3.6 Set Up Webhooks

Click **"Webhooks"** tab:

**Webhook 1: Email**
- **Name:** Send Email
- **URL:** `https://braselton-phone-agent.onrender.com/webhook/email`
- **Method:** POST
- **Trigger:** Custom (when agent needs to send email)
- **Enabled:** ✅

**Webhook 2: Transcript**
- **Name:** Store Transcript  
- **URL:** `https://braselton-phone-agent.onrender.com/webhook/transcript`
- **Method:** POST
- **Trigger:** Call Ended
- **Enabled:** ✅

Click **"Save"** for each.

### 3.7 Get API Key

1. Click **"Settings"** → **"API Keys"**
2. Click **"Create New Key"**
3. **Name:** Render Integration
4. Click **"Create"**
5. **Copy the key** (you'll only see it once!)

### 3.8 Add API Key to Render

1. Go to Render dashboard
2. Click your web service
3. Click **"Environment"** tab
4. Edit:
   ```bash
   RETELL_API_KEY=your_api_key_here
   ```
5. Click **"Save Changes"**

✅ **Step 3 Complete!** Retell AI configured.

---

## Step 4: Get a Phone Number (5 minutes)

### 4.1 Purchase Number

1. In Retell dashboard: **"Phone Numbers"** → **"Purchase Number"**
2. **Country:** United States
3. **Area Code:** 770 (or 678, 470 for Atlanta/Braselton area)
4. Pick any available number
5. Click **"Purchase"** (~$1/month)

### 4.2 Assign to Agent

1. After purchase, click the number
2. **Assign to Agent:** Select "Braselton Utilities Test"
3. Click **"Save"**

### 4.3 Get Your Number

The number will show in format: `+1 (770) 555-1234`

**This is your test phone number!**

✅ **Step 4 Complete!** Phone number active.

---

## Step 5: Test Everything (30 minutes)

### 5.1 Make Test Call #1: FAQ

1. Call your Retell number from your phone
2. Should hear: "Hello! Thanks for calling Braselton Utilities..."
3. Ask: "What are your office hours?"
4. Should get accurate answer
5. Hang up

### 5.2 Make Test Call #2: Email Request

1. Call the number again
2. Say: "I need to pay my water bill"
3. Should ask for email
4. Give your email address
5. Should confirm sending
6. Hang up
7. **Check your email** - payment link should arrive

### 5.3 Make Test Call #3: Transfer

1. Call the number
2. Say: "Can I speak to someone?"
3. Should offer to transfer
4. Should ring your cell phone (the transfer number)
5. Hang up

### 5.4 Check Admin Portal

1. Go to: `https://braselton-phone-agent.onrender.com/admin/transcripts`
2. Login: `admin` / `test123`
3. Should see your 3 test calls
4. Click on each to view transcript

### 5.5 Check Retell Dashboard

1. Go to Retell dashboard → **"Calls"**
2. Should see your 3 test calls
3. Click each to see:
   - Full transcript
   - Call duration
   - Cost per call

### 5.6 Verify Webhooks Worked

In Render dashboard:
1. Click your web service
2. Click **"Logs"** tab
3. Search for "webhook"
4. Should see POST requests from Retell

✅ **Step 5 Complete!** Everything working end-to-end!

---

## Step 6: Polish for Demo (15 minutes)

### 6.1 Test Different Scenarios

Call and test:
- ✅ Various FAQ questions
- ✅ Payment request with real email
- ✅ Transfer request
- ✅ Unknown question (should offer transfer)
- ✅ Interrupting the agent

### 6.2 Tune the Agent

Based on your tests, adjust in Retell:

**If agent talks too much:**
- Update system prompt: "Keep ALL responses under 20 words"

**If voice is wrong:**
- Try different voices in Retell

**If answers are wrong:**
- Update Knowledge Base

**If transfers too quickly or slowly:**
- Adjust trigger phrases

### 6.3 Prepare Demo Script

Write down what you'll show Blake/Jennifer:

```
1. Call the number live in meeting
2. Show FAQ working
3. Show payment email request
4. Show transfer to human
5. Show admin portal with transcripts
6. Show Retell dashboard with analytics
```

✅ **Step 6 Complete!** Ready to demo!

---

## Step 7: Demo to Blake & Jennifer (30 minutes)

### Email Them:

```
Subject: AI Phone Agent Prototype Ready

Hi Blake and Jennifer,

I've built a working prototype of the AI phone agent we discussed. 
It's fully functional and ready to demonstrate.

Would you have 30 minutes this week for a quick demo?

What's working:
✅ Voice agent answers common questions
✅ Sends payment links via email
✅ Transfers to staff when needed
✅ Stores all call transcripts (5-year retention)
✅ Admin portal to search calls

Test it yourself:
📞 Call: [YOUR RETELL NUMBER]
🌐 View calls: https://braselton-phone-agent.onrender.com/admin/transcripts
   (Login: admin / test123)

Looking forward to showing you!

Preston
```

### During Demo:

1. **Live call demonstration** (5 min)
   - Call in meeting, test FAQ
   - Request payment email (check your inbox)
   - Request transfer (to your phone)

2. **Show admin portal** (5 min)
   - Search for calls
   - Show transcripts
   - Export to CSV

3. **Show Retell dashboard** (5 min)
   - Call analytics
   - Costs per call
   - Settings you can tune

4. **Answer questions** (15 min)
   - How it works
   - What info you need from them
   - Next steps for production

### Get Their Input:

- ✅ Voice approval (right tone?)
- ✅ Answer accuracy (FAQ correct?)
- ✅ Transfer numbers (what should they be?)
- ✅ Any FAQs to add?
- ✅ Go-ahead to proceed with production setup

✅ **Step 7 Complete!** Demo successful, ready for production.

---

## Production Setup (After Demo Approval)

Once Blake/Jennifer approve, transition to production:

### Move to Azure (Blake helps):
1. Blake deploys to Azure (more secure, town-managed)
2. Use official utilitybilling@braselton.net email
3. Blake adds DNS records for email
4. Configure official transfer numbers
5. Get proper phone number (keep or change)

### Or Stay on Render:
1. Upgrade to paid plan (~$7/month for web service)
2. Keep using your SMTP2Go account or switch to town's
3. Forward town's main number to Retell number
4. Monitor and optimize

---

## Costs for Prototype

### Free Tier (Testing):
- Render Web Service: **$0** (free tier)
- Render PostgreSQL: **$0** (free tier)
- SMTP2Go: **$0** (free 1,000 emails/month)
- Retell AI: Pay-as-you-go (~$0.07/min)
  - 10 test calls @ 2 min each = ~$1.40
- Phone number: **$1-2/month**

**Total for testing: ~$3-4**

### Production Estimate (3,200 min/month):
- Render Web Service: $7/month (starter)
- Render PostgreSQL: $7/month (starter)
- SMTP2Go: $0 (free tier)
- Retell AI: $224/month (3,200 min @ $0.07/min)
- Phone number: $1-2/month

**Total production: ~$239-240/month**

---

## Troubleshooting

### Render deployment fails:
- Check build logs in Render dashboard
- Verify `requirements.txt` has all dependencies
- Make sure `Procfile` has correct gunicorn command

### Database connection error:
- Verify `DATABASE_URL` is set in environment
- Run `python init_db.py` in Render Shell
- Check PostgreSQL is running in Render

### Emails not sending:
- Verify SMTP2Go credentials
- Check sender address is verified in SMTP2Go
- Look at Render logs for error messages

### Webhooks not working:
- Check URL is exactly: `https://braselton-phone-agent.onrender.com`
- Verify webhooks are enabled in Retell
- Check Render logs for incoming requests

### Retell calls not working:
- Verify phone number is assigned to agent
- Check agent is enabled
- Look at Retell call logs for errors

### Can't access admin portal:
- Verify URL: `/admin/transcripts` (not just `/admin`)
- Check username/password in Render environment
- Try incognito browser window

---

## Next Steps After Prototype

1. ✅ Demo to Blake & Jennifer
2. ✅ Get approval and feedback
3. ✅ Collect production info:
   - Transfer phone numbers from Jennifer
   - Full FAQ list from Jennifer
   - Azure credentials from Blake
   - Official email setup from Blake
4. ✅ Deploy production version
5. ✅ Test with staff
6. ✅ Soft launch (business hours only)
7. ✅ Full launch (24/7)

---

## Quick Commands Reference

**Test email webhook:**
```bash
curl -X POST https://braselton-phone-agent.onrender.com/webhook/email \
  -H "Content-Type: application/json" \
  -d '{"call_id":"test","email_type":"payment_link","user_email":"test@email.com"}'
```

**View logs:**
Render Dashboard → Your Service → Logs tab

**Access database:**
Render Dashboard → PostgreSQL → Connect tab

**View call transcripts:**
https://braselton-phone-agent.onrender.com/admin/transcripts

**Redeploy:**
Render Dashboard → Your Service → Manual Deploy → Deploy Latest Commit

---

You now have a complete, working phone agent prototype that you built entirely yourself!

Show Blake and Jennifer, get their approval, then move to production with their help.

