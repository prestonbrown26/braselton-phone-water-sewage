# Prototype Deployment Checklist

Print this and check off as you go!

---

## ☐ Step 1: Deploy to Render (15 min)

- [ ] Create Render account at render.com
- [ ] Push code to GitHub
- [ ] Create PostgreSQL database on Render
- [ ] Copy database URL
- [ ] Create web service on Render
- [ ] Add environment variables
- [ ] Wait for deployment
- [ ] Run `python init_db.py` in Shell
- [ ] Test: Visit `/health` endpoint
- [ ] **Success:** See "healthy" status ✅

---

## ☐ Step 2: Set Up Email (20 min)

- [ ] Create SMTP2Go account (free tier)
- [ ] Get SMTP username from dashboard
- [ ] Get SMTP password from dashboard
- [ ] Add to Render environment variables
- [ ] Save and wait for redeploy
- [ ] Verify your email in SMTP2Go
- [ ] Test email webhook with curl
- [ ] **Success:** Receive payment link email ✅

---

## ☐ Step 3: Configure Retell AI (60 min)

- [ ] Login to Retell AI (use existing invite or create account)
- [ ] Create new agent
- [ ] Choose voice (test a few)
- [ ] Paste system prompt
- [ ] Add knowledge base Q&As (at least 6)
- [ ] Configure call transfer (use your phone for testing)
- [ ] Set up email webhook
- [ ] Set up transcript webhook
- [ ] Get API key from settings
- [ ] Add API key to Render
- [ ] **Success:** Agent created and configured ✅

---

## ☐ Step 4: Get Phone Number (5 min)

- [ ] Purchase number in Retell (area code 770)
- [ ] Assign to your agent
- [ ] Write down the number: _____________________
- [ ] **Success:** Phone number active ✅

---

## ☐ Step 5: Test Everything (30 min)

**Test Call 1: FAQ**
- [ ] Call the number
- [ ] Hear greeting
- [ ] Ask "What are your office hours?"
- [ ] Get correct answer
- [ ] Hang up

**Test Call 2: Email Request**
- [ ] Call the number
- [ ] Say "I need to pay my water bill"
- [ ] Agent asks for email
- [ ] Give your email
- [ ] Agent confirms sending
- [ ] Hang up
- [ ] Check email - payment link received

**Test Call 3: Transfer**
- [ ] Call the number
- [ ] Say "Can I speak to someone?"
- [ ] Agent offers to transfer
- [ ] Your phone rings
- [ ] Hang up

**Admin Portal**
- [ ] Visit `/admin/transcripts`
- [ ] Login with admin credentials
- [ ] See all 3 test calls
- [ ] View each transcript

**Retell Dashboard**
- [ ] Check Retell calls page
- [ ] See all 3 calls logged
- [ ] Review call details

- [ ] **Success:** All tests passed ✅

---

## ☐ Step 6: Polish (15 min)

- [ ] Call and test 5+ different scenarios
- [ ] Tune agent if too chatty/brief
- [ ] Adjust voice speed if needed
- [ ] Update knowledge base if answers wrong
- [ ] Write demo script
- [ ] **Success:** Agent polished and ready ✅

---

## ☐ Step 7: Demo Prep (10 min)

- [ ] Draft email to Blake/Jennifer
- [ ] Include test phone number
- [ ] Include admin portal link
- [ ] List what's working
- [ ] Request 30-minute meeting
- [ ] Send email
- [ ] **Success:** Meeting scheduled ✅

---

## During Demo Meeting

- [ ] Call agent live (FAQ test)
- [ ] Show email functionality
- [ ] Show transfer feature
- [ ] Show admin portal
- [ ] Show Retell dashboard
- [ ] Answer questions
- [ ] Get feedback on voice/tone
- [ ] Get approval to proceed
- [ ] **Success:** Approved for production ✅

---

## After Demo (Production Setup)

- [ ] Get transfer numbers from Jennifer
- [ ] Get FAQ content from Jennifer
- [ ] Coordinate with Blake for Azure
- [ ] OR upgrade Render to paid tier
- [ ] Switch to production settings
- [ ] Soft launch (business hours)
- [ ] Monitor for 1 week
- [ ] Full 24/7 launch
- [ ] **Success:** In production ✅

---

## Key URLs to Save

**Your Render App:**
https://braselton-phone-agent.onrender.com

**Admin Portal:**
https://braselton-phone-agent.onrender.com/admin/transcripts
- Username: admin
- Password: test123

**Retell Dashboard:**
https://app.retellai.com

**SMTP2Go Dashboard:**
https://app.smtp2go.com

**Your Phone Number:**
+1 (___) ___-____

---

## Costs Tracker

**Setup/Testing:**
- Render: $0 (free tier)
- PostgreSQL: $0 (free tier)
- SMTP2Go: $0 (free tier)
- Retell AI: ~$1-2 (test calls)
- Phone number: $1-2/month
- **Total: ~$3-4**

**Production (estimate):**
- Render: $7/month (or Azure ~$23/month)
- PostgreSQL: $7/month (or Azure ~$10/month)
- SMTP2Go: $0 (free tier)
- Retell AI: ~$224/month (3,200 min)
- Phone number: $1-2/month
- **Total: ~$239-265/month**

---

## Timeline

- [ ] **Day 1:** Deploy to Render (Steps 1-4)
- [ ] **Day 2:** Test and polish (Steps 5-6)
- [ ] **Week 1:** Demo to Blake/Jennifer (Step 7)
- [ ] **Week 2:** Production setup
- [ ] **Week 3:** Soft launch
- [ ] **Week 4:** Full launch

---

## Emergency Contacts

**Render Support:** https://render.com/support

**Retell AI Support:** support@retellai.com

**SMTP2Go Support:** https://www.smtp2go.com/support

**Your Info:**
- Email: ____________________
- Phone: ____________________

---

## Notes / Issues

(Use this space to jot down problems or things to remember)

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

---

**Good luck! 🚀**

