## SMTP2Go Setup Guide

Braselton wants to “send as” `utilitybilling@braselton.net` (or another town-owned address) without letting the AI agent log into the actual 365 mailbox. SMTP2Go is perfect for that because it acts as a relay: the agent connects to SMTP2Go with API credentials, and SMTP2Go spoofs the `From` address after the domain is verified.

Below is a checklist you can hand to Blake (IT) so he can wire everything up in less than 30 minutes.

---

### 1. Create/Log In to SMTP2Go

1. Go to [https://app.smtp2go.com/signup](https://app.smtp2go.com/signup).
2. Choose the free tier (1,000 emails/month is more than enough right now).
3. Use a town-owned email for the account owner (e.g. `it@braselton.net`).

> **Tip:** Enable MFA on the account—this credential sends mail on behalf of the town.

---

### 2. Add the Braselton Domain

1. In the SMTP2Go dashboard, navigate to **Sending → Sender Domains**.
2. Click **Add Sender Domain** and enter `braselton.net`.
3. SMTP2Go will show three DNS records to add:

| Purpose | Type | Host | Value |
|---------|------|------|-------|
| SPF     | TXT  | `@` or `_spf` | `v=spf1 include:smtp2go.com ~all` |
| DKIM    | CNAME | something like `smtp2go._domainkey` | Target host provided by SMTP2Go |
| Tracking (optional) | CNAME | `smtp` or `track` | Provided target host |

4. Add those records in Braselton’s DNS provider (GoDaddy, Azure DNS, etc.).
5. Click **Verify** in SMTP2Go after DNS propagates (usually 5–15 minutes).

> **Result:** Once verified, SMTP2Go is authorized to spoof any `@braselton.net` email address.

---

### 3. Create SMTP Credentials

1. Go to **Settings → SMTP Users → Add SMTP User**.
2. Choose a name like `braselton-utilities-ai`.
3. Copy the auto-generated username and password (you’ll paste these into Render/Azure).

> **Security:** This user can be revoked at any time without affecting the rest of the town’s email.

---

### 4. Configure the Flask App

In Render/Azure (or local `.env`), set:

```
SMTP2GO_SMTP_HOST=smtp.smtp2go.com
SMTP2GO_SMTP_PORT=587
SMTP2GO_USERNAME=<smtp user from step 3>
SMTP2GO_PASSWORD=<smtp password from step 3>
EMAIL_FROM_ADDRESS=utilitybilling@braselton.net   # or whichever sender you prefer
EMAIL_STUB_MODE=false
```

> Leave `EMAIL_STUB_MODE=true` in staging so you can see the log output without actually sending email. Flip it to `false` in production once SMTP2Go is ready.

---

### 5. Test the Connection

1. In the Render dashboard, go to **Shell** and run:
   ```bash
   python - <<'PY'
   from app import app
   from app.email_utils import send_billing_email
   with app.app_context():
       send_billing_email(
           to_address="your.address+test@gmail.com",
           subject="SMTP2Go smoke test",
           body="If you received this, SMTP2Go is wired correctly."
       )
   PY
   ```
2. If the email is delivered, you’re done. If not, check:
   - SMTP2Go dashboard → **Reports → Activity** for errors.
   - Render logs for authentication/connection issues.

---

### 6. Handoff Notes for IT

- Any future sender (e.g. `water@braselton.net`, `sewer@braselton.net`) can be added without touching the Flask app—just add it under **Sender Emails** inside SMTP2Go and update `EMAIL_FROM_ADDRESS`.
- Rate limits: free tier allows 25 emails/hour, 1,000/month. If usage exceeds that, upgrade to the $10/month plan (still cheap).
- Compliance: SMTP2Go provides analytics/logs for open records requests. Downloadable via their web UI.

---

With those steps complete, Retell’s agent can safely “spoof” Braselton’s utility email without any direct access to Microsoft 365. Let me know if you want the app to surface SMTP2Go failures in the admin UI or send alerts when an email bounces.


