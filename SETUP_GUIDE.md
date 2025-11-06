# Setup Guide - Braselton AI Phone Agent

Simple step-by-step instructions to get your phone agent working.

---

## What You're Building

A phone number that residents can call to:
- Get answers to common utility questions
- Request payment links via email
- Be transferred to staff when needed

---

## Before You Start

You'll need to coordinate with:
- **Blake** (IT) - for Azure deployment and DNS
- **Jennifer** (Town Manager) - for FAQ content and transfer numbers

---

## Step 1: Deploy the Web App to Azure

### What Blake Needs to Do:

1. **Create Azure Resources:**
   ```bash
   # Create PostgreSQL database
   az postgres flexible-server create \
     --name braselton-db \
     --resource-group braselton-rg \
     --admin-user dbadmin \
     --admin-password [SECURE_PASSWORD] \
     --sku-name Standard_B1ms
   
   # Create database
   az postgres flexible-server db create \
     --server-name braselton-db \
     --database-name braselton
   
   # Create web app
   az webapp create \
     --name braselton-utilities-agent \
     --resource-group braselton-rg \
     --runtime "PYTHON:3.11"
   ```

2. **Deploy the Code:**
   - Give Blake the `braselton-phone-water-sewage` folder
   - Blake runs: `az webapp up --name braselton-utilities-agent`

3. **Set Environment Variables in Azure:**
   Blake adds these in Azure Portal → App Service → Configuration:
   ```
   DATABASE_URL=postgresql://dbadmin:[PASSWORD]@braselton-db.postgres.database.azure.com/braselton
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=[choose-secure-password]
   TOWN_WEBSITE_URL=https://braselton.net
   SECRET_KEY=[random-string]
   LOG_RETENTION_DAYS=1825
   ```

4. **Initialize Database:**
   ```bash
   # SSH into the app
   az webapp ssh --name braselton-utilities-agent
   
   # Run database setup
   python init_db.py
   ```

### Verify It Works:
Visit: `https://braselton-utilities-agent.azurewebsites.net/health`

Should see: `{"status": "healthy"}`

✅ **Step 1 Complete** - Web app is running!

---

## Step 2: Set Up Email (SMTP2Go)

### 2.1 Create SMTP2Go Account

1. Go to: https://www.smtp2go.com
2. Sign up (use Braselton email/credit card - Town pays)
3. Choose free plan (1,000 emails/month)

### 2.2 Get SMTP Credentials

1. Login to SMTP2Go dashboard
2. Go to **Settings** → **Users**  
3. Click **Add SMTP User**
4. Name: `braselton-phone-agent`
5. **Save the username and password** - you'll need these!

### 2.3 Configure Sending Domain

1. In SMTP2Go: **Settings** → **Sender Domains**
2. Click **Add Sender Domain**
3. Enter: `braselton.net`
4. SMTP2Go will show you DNS records needed

### 2.4 Blake Adds DNS Records

Send Blake these DNS records (from SMTP2Go):

**SPF Record:**
```
Type: TXT
Host: @
Value: v=spf1 include:smtp2go.com ~all
```

**DKIM Record:**
```
Type: TXT
Host: [SMTP2Go will provide]
Value: [SMTP2Go will provide]
```

Wait 30 minutes for DNS to update.

### 2.5 Add SMTP Credentials to Azure

Blake adds these to Azure App Service → Configuration:
```
SMTP2GO_USERNAME=[from step 2.2]
SMTP2GO_PASSWORD=[from step 2.2]
EMAIL_FROM_ADDRESS=utilitybilling@braselton.net
```

Then restarts the app.

### 2.6 Test Email

```bash
curl -X POST https://braselton-utilities-agent.azurewebsites.net/webhook/email \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "test123",
    "email_type": "payment_link",
    "user_email": "YOUR_EMAIL@gmail.com"
  }'
```

Check your inbox - you should get the payment link email!

✅ **Step 2 Complete** - Emails working!

---

## Step 3: Set Up Retell AI

### 3.1 Accept Invite

1. Check email for Retell AI invite (Blake sent to `brownpreston2490@gmail.com`)
2. Click invite link and create password
3. Login to: https://app.retellai.com

### 3.2 Create Voice Agent

1. Click **"Create Agent"**
2. **Name:** Braselton Utilities Assistant
3. **Voice:** Click "Try voices" and pick one
   - Recommended: `Joanna` (female) or `Matthew` (male)
   - Test a few and choose what sounds best
4. Click **Create**

### 3.3 Add System Prompt

Copy and paste this into the **System Instructions** box:

```
You are a professional customer service assistant for the Town of Braselton Utilities Department in Georgia.

YOUR ROLE:
You help residents calling about water, sewer, and sanitation services.

IMPORTANT RULES:

1. BE BRIEF - Keep responses to 2-3 sentences maximum

2. TRANSFER IMMEDIATELY IF:
   - Caller asks for a person/representative
   - Caller sounds frustrated
   - Question needs account access
   - You don't know the answer
   - Emergency situation

3. PAYMENT REQUESTS:
   - If caller wants to pay bill, say: "I can send you a link to pay online. What's your email address?"
   - After getting email, say: "I'll send that payment link to [email] right now."

4. NEVER:
   - Make up information
   - Access account details
   - Handle payments over the phone

5. GREETING:
"Hello! Thanks for calling Braselton Utilities. How can I help you today?"

If caller asks to speak to someone, say: "Of course! Let me transfer you right now."
```

Click **Save**.

### 3.4 Add Knowledge Base

1. Click **Knowledge Base** tab
2. Get FAQ list from Jennifer
3. Click **Add Knowledge**
4. Either upload FAQ document or manually add Q&A pairs

**Example FAQs:**
```
Q: What are your office hours?
A: Monday through Friday, 8 AM to 5 PM. Closed weekends and holidays.

Q: Where can I pay my water bill?
A: You can pay online at braselton.net/pay, or in person at Town Hall with cash, check, or money order.

Q: Can I pay by credit card over the phone?
A: No, but I can send you a link to pay online. What's your email address?
```

### 3.5 Set Up Call Transfers

1. Get transfer numbers from Jennifer:
   - Billing questions: `_______________`
   - Emergencies: `_______________`
   - General office: `_______________`

2. In Retell: Click **Call Transfer** tab
3. Add each number with a name (e.g., "Billing Department")
4. Add trigger phrases:
   ```
   "speak to someone"
   "talk to a person"
   "representative"
   "transfer"
   "manager"
   ```

### 3.6 Configure Webhooks

1. Click **Webhooks** tab
2. Add these webhooks:

**Email Webhook:**
```
Name: Send Email
URL: https://braselton-utilities-agent.azurewebsites.net/webhook/email
Method: POST
Trigger: On email request
```

**Transcript Webhook:**
```
Name: Store Transcript
URL: https://braselton-utilities-agent.azurewebsites.net/webhook/transcript
Method: POST
Trigger: Call ended
```

### 3.7 Get API Key

1. Click **Settings** → **API Keys**
2. Click **Create New Key**
3. Name: `Azure Integration`
4. **Copy the key** - you need this!

Send to Blake to add to Azure as:
```
RETELL_API_KEY=[the key you copied]
```

Blake restarts the app.

✅ **Step 3 Complete** - Retell AI configured!

---

## Step 4: Test the Voice Agent

### 4.1 Make Test Call

1. In Retell dashboard: Click **Testing**
2. Click **Make Test Call**
3. Retell will call your phone

### 4.2 Test These Scenarios

**Test 1: FAQ Question**
- Call and ask: "What are your office hours?"
- Should get: Brief, accurate answer

**Test 2: Payment Request**
- Ask: "I need to pay my water bill"
- Should ask for email
- Give your email
- Check inbox for payment link

**Test 3: Transfer Request**  
- Say: "Can I speak to someone?"
- Should say: "Let me transfer you"
- Should transfer to office number

**Test 4: Unknown Question**
- Ask something obscure
- Should offer to transfer

### 4.3 Review and Tune

Check the call in Retell dashboard:
- Was the voice clear?
- Were answers accurate?
- Was it too chatty or too brief?
- Did transfers work?

Adjust:
- Voice speed if too fast/slow
- System prompt if wrong behavior
- Knowledge base if wrong answers

✅ **Step 4 Complete** - Agent tested and tuned!

---

## Step 5: Get a Phone Number

### 5.1 Purchase Number in Retell

1. In Retell: Click **Phone Numbers**
2. Click **Purchase Number**
3. Select area code: **770** (Braselton local)
4. Choose an available number
5. Assign to: "Braselton Utilities Assistant"

**Cost:** ~$1-2/month

### 5.2 Test by Calling It

Call the new number from your phone.
- Should hear the greeting
- Test a few questions
- Verify everything works

✅ **Step 5 Complete** - Phone number active!

---

## Step 6: Internal Testing

### 6.1 Share with Blake & Jennifer

Email them:
```
Subject: Phone Agent Ready for Testing

The AI phone agent is ready to test!

Test Number: [YOUR RETELL NUMBER]

Please call and test:
1. Ask about office hours
2. Ask to pay bill (provide email to test)
3. Ask a complex question
4. Request to speak to someone

Let me know:
- Does the voice sound good?
- Are the answers accurate?
- Is the tone professional?
- Anything that needs adjustment?
```

### 6.2 Make Adjustments

Based on feedback, update:
- Voice selection
- System prompt (tone, verbosity)
- Knowledge base (better answers)
- Transfer timing

### 6.3 Test Again

Repeat until Blake and Jennifer are happy with it.

✅ **Step 6 Complete** - Everyone approves!

---

## Step 7: Go Live

### Option A: Soft Launch

Start with limited hours to monitor closely:

1. Blake forwards the main utilities number to your Retell number
   - Only during business hours (M-F 8am-5pm)
   - After hours goes to regular voicemail

2. Monitor for 1 week:
   - Check Retell dashboard daily
   - Review call transcripts in admin portal
   - Ask staff for feedback

3. If going well, enable 24/7

### Option B: Direct Launch

1. Give residents the new number directly
2. Keep old number for now as backup
3. Gradually transition over 1 month

### Monitor After Launch

**Daily (first week):**
- Check Retell dashboard for call volume
- Review transcripts: `/admin/transcripts`
- Watch for issues

**Weekly:**
- Review top questions asked
- Update FAQs if needed
- Check transfer rates

**Monthly:**
- Meet with Jennifer to review
- Update knowledge base
- Tune responses

✅ **Step 7 Complete** - You're live! 🎉

---

## Admin Portal

### View Call Transcripts

1. Go to: `https://braselton-utilities-agent.azurewebsites.net/admin/transcripts`
2. Login with: `admin` / `[password Blake set]`
3. Search by:
   - Call ID
   - Phone number
   - Date

### Export Call Logs

For compliance or records:
```
https://braselton-utilities-agent.azurewebsites.net/admin/export
```

Downloads CSV of all calls (5-year retention per state law).

---

## Monthly Costs

- Retell AI: ~$224/month (based on 3,200 min/month)
- Phone number: $1-2/month  
- Azure hosting: ~$23/month
- SMTP2Go: Free (under 1,000 emails/month)

**Total: ~$248/month**

---

## Troubleshooting

### Emails not sending
1. Check SMTP2Go credentials in Azure
2. Verify DNS records with Blake
3. Check SMTP2Go dashboard for errors

### Calls not storing in database
1. Check webhook URL in Retell
2. Verify Azure app is running
3. Check app logs in Azure Portal

### Agent not answering correctly
1. Update knowledge base in Retell
2. Revise system prompt
3. Add more FAQ examples

### Can't access admin portal
1. Verify URL is correct
2. Check username/password with Blake
3. Try incognito browser window

---

## Support

**Blake (IT):**
- Azure issues
- DNS records  
- Database problems

**Jennifer (Town Manager):**
- FAQ content
- Transfer numbers
- Policy questions

**Retell AI Support:**
- Voice agent issues
- Platform problems
- support@retellai.com

**Preston (Developer):**
- Technical setup help
- preston@smartagen.ai
- 407-701-0667

---

## Quick Reference Checklist

- [ ] Azure web app deployed (Blake)
- [ ] Database initialized
- [ ] SMTP2Go account created
- [ ] DNS records added (Blake)
- [ ] Email tested successfully
- [ ] Retell AI account accessed
- [ ] Voice agent created
- [ ] System prompt added
- [ ] Knowledge base uploaded
- [ ] Transfer numbers configured
- [ ] Webhooks configured
- [ ] API key added to Azure (Blake)
- [ ] Test calls completed
- [ ] Blake approved
- [ ] Jennifer approved
- [ ] Phone number purchased
- [ ] Soft launch started
- [ ] Monitoring in place

---

That's it! Follow these steps in order and you'll have a working phone agent.

