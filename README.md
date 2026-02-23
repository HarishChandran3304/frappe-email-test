# frappe-email-test

A developer tool for testing Frappe **Email Templates** end-to-end without writing any test scripts.

Pick a template, let AI generate realistic variable values, and send a real email all from the Frappe Desk.

### Why this matters

Email clients render HTML very differently. What looks correct in Gmail may break in Outlook, Apple Mail, or a corporate webmail client and Frappe's template preview in the browser tells you nothing about how the email will actually render once delivered. The only reliable way to catch layout issues, broken variables, or missing conditional blocks before they reach users is to send a real email with real data and open it in the target client.

This app makes that loop fast: pick a template, generate plausible variable values, send to yourself (or a shared inbox your team monitors), and verify rendering across clients before the template goes anywhere near production traffic.

(I personally made this rookie mistake and sent out broken emails to all customers 💀)

---

## Features

- Directly integrate with **existing Email Templates** in desk
- **Auto-extract variables** from any Jinja2 Email Template (subject + body)
- **AI-powered fill** *(optional)* sends the full template to an OpenRouter model, which infers correct types (strings, numbers, dates) from context
- **Send real emails** via any configured Frappe Email Account
- **Resend** failed emails with one click
- Accessible to any `System Manager` from the **Email Tester** workspace

---

## Requirements

- Frappe Framework v15+
- A Gmail (or any SMTP) account for outgoing email

> **OpenRouter API key is not required.** Template Args can always be filled manually. The AI fill feature is optional and the app works fully without it.

---

## Installation

```bash
fm shell
bench get-app https://github.com/HarishChandran3304/frappe_email_test
bench install-app frappe_email_test
bench migrate
bench build --app frappe_email_test
bench restart
```

---

## Configuration

### 1) Outgoing Email Account

Go to **Desk → Email Account → New** and fill in:

| Field | Value |
|---|---|
| Email Account Name | Any label, e.g. `Test Sender` |
| Email ID | `your.email@gmail.com` |
| Password | 16-char Gmail App Password (see below) |
| Enable Outgoing | ✓ |
| SMTP Server | `smtp.gmail.com` |
| SMTP Port | `587` |
| Use TLS | ✓ |
| Enable Incoming | leave unchecked |

**Getting a Gmail App Password**

1. Enable 2-Step Verification on your Google account (required)
2. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Enter any app name (e.g. `Frappe Mail`) and click **Create**
4. Copy the 16-character password shown paste it **without spaces**

Any SMTP provider works (SendGrid, Mailgun, etc.) Gmail is just the quickest to set up.

### 2) Email Tester Settings

Go to **Desk → Email Tester Settings** and fill in:

| Field | Required | Value |
|---|---|---|
| Email Account | Yes | The account created above |
| Default Recipient | Yes | Email address where test emails should land |
| OpenRouter API Key | No | From [openrouter.ai/keys](https://openrouter.ai/keys) (only needed for AI auto-fill feature) |
| AI Model | No | `openai/gpt-4o-mini` (default; any OpenRouter model slug works) |

---

## Usage

1. **Desk → Email Tester → Email Test → New**
2. Select an **Email Template** the template's Jinja variables are extracted automatically into the **Template Args** JSON field
3. Fill in the JSON values either manually, or click **Tools → Fill with AI** if an OpenRouter key is configured
4. Click **Send Test Email** → confirm → email is delivered and status flips to **Sent**

If a send fails (status `Failed`), fix the issue and click **Resend**.

---
