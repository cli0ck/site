# cli0ck contact Worker

The site is static (GitHub Pages), so it cannot talk to SMTP. This Worker is
the only piece with credentials; the browser never sees them.

## Deploy

```bash
npm i -g wrangler
cd worker
wrangler login

# rate-limit store
wrangler kv namespace create RL          # paste the id into wrangler.toml

# the sending key (resend.com — free tier, verify cli0ck.com as a domain)
wrangler secret put RESEND_KEY

# optional bot check (dash.cloudflare.com → Turnstile)
wrangler secret put TURNSTILE_SECRET

wrangler deploy
```

## Requires

- `cli0ck.com` added to Cloudflare (nameservers moved from Hostinger).
  Keep every existing MX / SPF / DKIM / DMARC record so Hostinger mail keeps working.
- `form.cli0ck.com` route, created automatically by the `[[routes]]` block.
- Resend: verify `cli0ck.com`, add the DKIM records it gives you **alongside**
  the Hostinger ones, and add `include:_spf.resend.com` to the existing SPF.

## Test

```bash
curl -X POST https://form.cli0ck.com \
  -H 'Content-Type: application/json' -H 'Origin: https://cli0ck.com' \
  -d '{"name":"Test","email":"you@example.com","message":"A message at least twenty characters long."}'
```
