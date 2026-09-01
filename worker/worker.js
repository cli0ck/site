/* cli0ck contact endpoint — Cloudflare Worker at form.cli0ck.com
 *
 * The static site posts here; this Worker validates, rate-limits, and sends
 * the enquiry on to info@cli0ck.com. No credentials ever reach the browser.
 *
 * Secrets (wrangler secret put NAME):
 *   RESEND_KEY   — API key from resend.com, sending as info@cli0ck.com
 *   TURNSTILE_SECRET — optional; set to enable bot checking
 * Vars in wrangler.toml: TO_EMAIL, FROM_EMAIL, ALLOWED_ORIGIN
 */

const MAX = { name: 120, email: 200, company: 160, budget: 60, message: 6000 };
const SERVICES = ['pentest', 'redteam', 'vulnresearch', 'mobile', 'advisory', 'other'];

const cors = (env, extra = {}) => ({
  'Access-Control-Allow-Origin': env.ALLOWED_ORIGIN || 'https://cli0ck.com',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Access-Control-Max-Age': '86400',
  ...extra,
});

const json = (env, obj, status = 200) =>
  new Response(JSON.stringify(obj), {
    status,
    headers: cors(env, { 'Content-Type': 'application/json' }),
  });

const esc = (s) =>
  String(s).replace(/[&<>"']/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

export default {
  async fetch(request, env, ctx) {
    if (request.method === 'OPTIONS') return new Response(null, { headers: cors(env) });
    if (request.method !== 'POST') return json(env, { error: 'method_not_allowed' }, 405);

    // only our own origin may post here
    const origin = request.headers.get('Origin') || '';
    const allowed = [env.ALLOWED_ORIGIN || 'https://cli0ck.com', 'https://www.cli0ck.com'];
    if (origin && !allowed.includes(origin)) return json(env, { error: 'forbidden' }, 403);

    let body;
    try { body = await request.json(); } catch { return json(env, { error: 'bad_json' }, 400); }

    // honeypot: real people never fill a hidden field
    if (body.website) return json(env, { ok: true });

    // per-IP rate limit, 3 per hour, via KV
    const ip = request.headers.get('CF-Connecting-IP') || '0';
    if (env.RL) {
      const key = `rl:${ip}`;
      const n = parseInt((await env.RL.get(key)) || '0', 10);
      if (n >= 3) return json(env, { error: 'rate_limited' }, 429);
      ctx.waitUntil(env.RL.put(key, String(n + 1), { expirationTtl: 3600 }));
    }

    // optional Turnstile
    if (env.TURNSTILE_SECRET) {
      const v = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ secret: env.TURNSTILE_SECRET, response: body.token, remoteip: ip }),
      }).then((r) => r.json()).catch(() => ({ success: false }));
      if (!v.success) return json(env, { error: 'challenge_failed' }, 403);
    }

    const f = {};
    for (const k of Object.keys(MAX)) f[k] = String(body[k] || '').trim().slice(0, MAX[k]);
    const services = (Array.isArray(body.services) ? body.services : [])
      .filter((s) => SERVICES.includes(s)).slice(0, 6);

    if (!f.name || !f.message) return json(env, { error: 'missing_fields' }, 400);
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(f.email)) return json(env, { error: 'bad_email' }, 400);
    if (f.message.length < 20) return json(env, { error: 'message_too_short' }, 400);

    const ref = 'CLK-' + Date.now().toString(36).toUpperCase().slice(-6);
    const meta = {
      country: request.headers.get('CF-IPCountry') || '—',
      when: new Date().toISOString().replace('T', ' ').slice(0, 16) + ' UTC',
    };

    const rows = [
      ['Reference', ref],
      ['Name', f.name],
      ['Email', f.email],
      ['Company', f.company || '—'],
      ['Services', services.length ? services.join(', ') : '—'],
      ['Budget', f.budget || '—'],
      ['Country', meta.country],
      ['Received', meta.when],
    ];

    const html = `<!doctype html><html><body style="margin:0;background:#1c1917;padding:24px;font-family:ui-sans-serif,system-ui,sans-serif">
<div style="max-width:640px;margin:0 auto;background:#292524;border:1px solid rgba(255,255,255,.12);border-radius:12px;overflow:hidden">
<div style="padding:20px 24px;border-bottom:1px solid rgba(255,255,255,.12)">
<div style="font:600 13px ui-monospace,monospace;letter-spacing:.18em;text-transform:uppercase;color:#f59e0b">New enquiry &middot; ${esc(ref)}</div>
<div style="margin-top:6px;font:600 20px system-ui;color:#fff">${esc(f.name)}${f.company ? ' &middot; ' + esc(f.company) : ''}</div>
</div>
<table style="width:100%;border-collapse:collapse">
${rows.map(([k, v]) => `<tr>
<td style="padding:10px 24px;font:600 11px ui-monospace,monospace;letter-spacing:.14em;text-transform:uppercase;color:rgba(255,255,255,.4);white-space:nowrap;vertical-align:top">${esc(k)}</td>
<td style="padding:10px 24px 10px 0;font:14px system-ui;color:#fff">${esc(v)}</td></tr>`).join('')}
</table>
<div style="padding:20px 24px;border-top:1px solid rgba(255,255,255,.12)">
<div style="font:600 11px ui-monospace,monospace;letter-spacing:.14em;text-transform:uppercase;color:rgba(255,255,255,.4);margin-bottom:10px">Message</div>
<div style="font:15px/1.65 system-ui;color:rgba(255,255,255,.85);white-space:pre-wrap">${esc(f.message)}</div>
</div>
<div style="padding:16px 24px;border-top:1px solid rgba(255,255,255,.12);font:12px ui-monospace,monospace;color:rgba(255,255,255,.35)">
Reply directly to this email to reach ${esc(f.email)}
</div></div></body></html>`;

    const text = rows.map(([k, v]) => `${k}: ${v}`).join('\n') + `\n\n---\n${f.message}\n`;

    const r = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { Authorization: `Bearer ${env.RESEND_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        from: `cli0ck enquiries <${env.FROM_EMAIL}>`,
        to: [env.TO_EMAIL],
        reply_to: f.email,
        subject: `[${ref}] ${f.name}${f.company ? ' — ' + f.company : ''}${services.length ? ' — ' + services[0] : ''}`,
        html, text,
      }),
    });

    if (!r.ok) {
      console.log('send failed', r.status, await r.text());
      return json(env, { error: 'send_failed' }, 502);
    }
    return json(env, { ok: true, ref });
  },
};
