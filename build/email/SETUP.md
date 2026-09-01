# The branded notification email

Web3Forms (what the form uses today) prints your fields as plain text and has
no template feature on the free tier — I verified this against their docs and
their API. To get the cli0ck-designed email in `template.html`, the form needs
EmailJS instead. Ten minutes, free for 200 emails a month.

## 1. Account

emailjs.com → sign up as **info@cli0ck.com**.

## 2. Connect the mailbox

**Email Services → Add New Service → Other (SMTP)**

| | |
|---|---|
| Host | `smtp.hostinger.com` |
| Port | `465` (SSL) |
| User | `info@cli0ck.com` |
| Password | the mailbox password |
| From name | `cli0ck.com` |

The password stays inside EmailJS. It never reaches the browser.
Copy the **Service ID**.

## 3. The template

**Email Templates → Create New Template → Content → `<>` Edit as HTML**

Paste all of `template.html`, then set:

- **Subject:** `cli0ck enquiry — {{topic}} — {{name}}`
- **To:** `info@cli0ck.com`
- **Reply-To:** `{{reply_to}}`

Copy the **Template ID**.

## 4. Public key

**Account → General → Public Key.** Safe in the page: it only sends through
the templates on your own account.

## 5. Wire it up

In `assets/contact.js`, top of the file:

```js
var EJS = {
  service:  'service_xxxxxxx',
  template: 'template_xxxxxxx',
  key:      'xxxxxxxxxxxxxxx'
};
```

Then:

```bash
git add -A && git commit -m "Send through EmailJS" && git push
```

Until those are filled in the form keeps using Web3Forms, so it never stops
working while you set this up.

## Placeholders the template uses

`{{name}}` `{{email}}` `{{company}}` `{{topic}}` `{{message}}` `{{sent_at}}` `{{reply_to}}`
