#!/usr/bin/env python3
"""Build the cli0ck site: home, research index, and one page per writeup."""
import re, os, html as H, json

# Source writeups (exported from azoz.my) and the output root.
# Override with CLI0CK_SRC / CLI0CK_OUT if your checkout lives elsewhere.
_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.environ.get('CLI0CK_SRC', os.path.join(_HERE, 'build', 'src'))
OUT = os.environ.get('CLI0CK_OUT', _HERE)

EMAIL  = 'info@cli0ck.com'
GITHUB = 'https://github.com/defineid'
LI_AZ  = 'https://www.linkedin.com/in/abdulaziz-alasaiqah-b74071334'
LI_AH  = ''          # TODO: Ahmed's LinkedIn

WRITEUPS = [
  dict(src='rasterimage-uaf',      slug='cve-2026-74943-rasterimage-use-after-free'),
  dict(src='font-cmap-leak',       slug='cve-2026-74945-font-heap-disclosure'),
  dict(src='cometchat-xss',        slug='cve-2026-39154-cometchat-stored-xss'),
  dict(src='webrender-pipelineid', slug='cve-2026-74970-webrender-fission-bypass'),
  dict(src='ff-autofill',          slug='cve-2026-6765-formautofill-handlers'),
]

# ---------------------------------------------------------------- extraction
def strip_i18n(s):
    return re.sub(r'\s+data-i18n(?:-[a-z]+)?="[^"]*"', '', s)

def fix_assets(s):
    s = re.sub(r'(src|href|poster)="assets/([^"?]+)(\?[^"]*)?"', r'\1="assets/\2"', s)
    return s

def text_of(frag):
    return H.unescape(re.sub(r'<[^>]+>', '', frag)).strip()

def el(body, cls, tags='span|a|div|h3|dd|dt'):
    """Inner HTML of the first element carrying `cls`, whatever tag it uses."""
    m = re.search(r'<(%s)\b[^>]*class="[^"]*\b%s\b[^"]*"[^>]*>(.*?)</\1>'
                  % (tags, re.escape(cls)), body, re.S)
    return m.group(2) if m else ''

def parse(src):
    raw = open(f'{SRC}/{src}.html', encoding='utf-8', errors='replace').read()
    m = re.search(r'<article([^>]*)>(.*?)</article>', raw, re.S)
    attrs, body = m.group(1), m.group(2)

    body = strip_i18n(body)
    body = fix_assets(body)

    d = {}
    d['cls']    = re.search(r'class="([^"]+)"', attrs).group(1).strip()
    d['sev']    = (re.search(r'wu__sev--(\w+)', body) or [None, 'mod'])[1]
    d['sevtx']  = text_of(el(body, 'wu__sev'))
    d['cve']    = text_of(el(body, 'wu__cve')) or (re.search(r'CVE-\d{4}-\d+', body) or [''])[0]
    d['status'] = text_of(el(body, 'wu__status'))
    d['title']  = text_of(el(body, 'wu__title'))
    d['vendor'] = text_of(el(body, 'name'))
    d['tag']    = text_of(el(body, 'tag'))

    meta = {}
    for dt, dd in re.findall(r'<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>', body, re.S):
        meta[text_of(dt)] = text_of(dd)
    d['meta'] = meta

    sums = re.search(r'<h3[^>]*>\s*Summary\s*</h3>\s*<p[^>]*>(.*?)</p>', body, re.S)
    d['summary'] = text_of(sums.group(1)) if sums else ''

    d['banner'] = re.search(r'(<div[^>]*class="wu__banner".*?</div>)', body, re.S).group(1)
    inner = re.search(r'<div[^>]*class="wu__in"[^>]*>(.*)$', body, re.S).group(1).rstrip()
    if inner.endswith('</div>'):
        inner = inner[: inner.rfind('</div>')].rstrip()
    d['inner'] = inner
    return d

for w in WRITEUPS:
    w.update(parse(w['src']))

# short deck for cards: first sentence of the summary, capped
def deck(w):
    s = w['summary']
    cut = s.find('. ')
    s = s[:cut+1] if 0 < cut < 260 else (s[:250].rsplit(' ', 1)[0] + '…' if len(s) > 250 else s)
    return H.escape(s)

SEVCLASS = {'crit':'critical', 'high':'high', 'mod':'moderate'}

# ============================================================
#  Pages built on calif.io's compiled stylesheet, using its own
#  class names and section structure verbatim. assets/site.css
#  is byte-identical to https://calif.io/website.64c5da79.css.
#  Only the content is ours.
# ============================================================
SEVN   = {'crit':0, 'high':1, 'mod':2}
SEVLBL = {'crit':'Critical', 'high':'High', 'mod':'Moderate'}
ordered = sorted(WRITEUPS, key=lambda w: SEVN.get(w['sev'], 9))

RETINT = {
  '#d4a24c':'#d97706', '#e6b76a':'#f59e0b', '#e9cda0':'#fcd9a0',
  '#e78d6f':'#f0836a', '#e06a4a':'#dc2626',
  '#d6d3cc':'#e7e5e4', '#8f8778':'#a8a29e',
  '#17110b':'#1c1917', '#0d0a07':'#171412', '#7fb8e6':'#a3a380',
  'rgba(233,205,160':'rgba(231,229,228', 'rgba(212,162,76':'rgba(217,119,6',
  'rgba(224,106,74':'rgba(220,38,38',
}
def retint(s):
    for a, b in RETINT.items(): s = s.replace(a, b).replace(a.upper(), b)
    return s

# ---- calif.io's own article classes -------------------------------------
C_H2   = 'break-words font-semibold lg:text-3xl mb-4 mt-12 scroll-mt-24 text-2xl text-white'
C_P    = 'break-words leading-relaxed mb-5 text-white/80'
C_PRE  = 'bg-black/40 border border-white/10 max-w-full mb-6 overflow-x-auto p-4 rounded-lg'
C_CODE = 'font-mono leading-relaxed text-sm text-white/90'
C_IMG  = 'block h-auto max-h-[480px] max-w-full mx-auto my-8 rounded-lg w-auto'
C_CAP  = 'mb-8 text-center text-white/40 text-xs tracking-[0.15em] uppercase'
C_A    = 'hover:underline text-accent'
C_PILL = 'border border-white/15 hover:border-accent/40 hover:text-accent px-3 py-1 rounded-full text-white/60 text-xs transition-colors'
C_LBL  = 'text-white/40 text-xs tracking-[0.2em] uppercase'
C_QUOTE= 'border-accent border-l-2 break-words italic mb-5 pl-4 py-1 text-white/70'


DIV_RE = re.compile(r'<div\b[^>]*>|</div>', re.I)
def unwrap_divs(s, needle):
    """Drop <div ...needle...> wrappers and their matching </div>, keeping the contents."""
    while True:
        m = re.search(r'<div\b[^>]*class="[^"]*' + needle + r'[^"]*"[^>]*>', s, re.I)
        if not m:
            return s
        depth = 1
        for t in DIV_RE.finditer(s, m.end()):
            if t.group(0).startswith('</'):
                depth -= 1
                if depth == 0:
                    s = s[:m.start()] + s[m.end():t.start()] + s[t.end():]
                    break
            else:
                depth += 1
        else:
            return s[:m.start()] + s[m.end():]

def to_calif(html):
    """Rewrite the ported writeup markup into calif.io's article classes."""
    s = retint(html)

    # the ported body repeats its own badge row, title and meta table;
    # this page renders those itself, so drop everything before the first section
    k = s.find('<div class="wu__sec">')
    if k > 0: s = s[k:]

    # section wrappers dissolve; their h3 becomes calif's h2
    s = unwrap_divs(s, 'wu__sec')
    s = re.sub(r'<h3[^>]*>(.*?)</h3>', lambda m: f'<h2 class="{C_H2}">{m.group(1).strip()}</h2>', s, flags=re.S)

    # code blocks
    s = re.sub(r'<pre class="wu__code">(.*?)</pre>',
               lambda m: f'<pre class="{C_PRE}"><code class="{C_CODE}">{m.group(1)}</code></pre>', s, flags=re.S)
    s = s.replace('<span class="cm">', '<span class="text-white/40">')

    # figures: image / video + caption
    s = re.sub(r'<figure([^>]*?)\s*class="[^"]*wu__fig[^"]*"([^>]*)>', r'<figure\1\2>', s)
    s = re.sub(r'<img((?![^>]*class=)[^>]*)>', lambda m: f'<img{m.group(1)} class="{C_IMG}">', s)
    s = re.sub(r'<video((?![^>]*class=)[^>]*)>', lambda m: f'<video{m.group(1)} class="{C_IMG}">', s)
    s = re.sub(r'<figcaption>', f'<figcaption class="{C_CAP}">', s)

    # numbered steps
    s = s.replace('<ul class="wu__steps">', '<ol class="list-decimal marker:text-accent mb-6 pl-5 space-y-2 text-white/80">')
    s = re.sub(r'(<ol class="list-decimal[^"]*">)(.*?)</ul>', r'\1\2</ol>', s, flags=re.S)
    s = re.sub(r'<li>', '<li class="break-words leading-relaxed">', s)

    # the verify / advisory link becomes a calif pill
    def _pill(m):
        attrs = re.sub(r'\s*class="[^"]*"', '', m.group(1))
        return '<a' + attrs + ' class="' + C_PILL + ' inline-flex items-center gap-2 mt-2">'
    s = re.sub(r'<a\b([^>]*wu__verify[^>]*)>', _pill, s)

    # the note line
    s = re.sub(r'<p class="wu__note-line">', f'<p class="italic mb-5 text-sm text-white/40">', s)

    # remaining unclassed paragraphs get calif's body class
    # \b is essential here: without it this matched the start of <path> inside
    # every inline SVG and rewrote it to <p class="..."ath ...>, destroying the icon.
    s = re.sub(r'<p\b(?![^>]*class=)([^>]*)>', lambda m: f'<p class="{C_P}"{m.group(1)}>', s)

    # links inside prose
    s = re.sub(r'<a (?![^>]*class=)((?:href|target|rel)=)', f'<a class="{C_A}" \\1', s)

    # tables + diagrams keep their hooks (calif has no equivalent)
    s = re.sub(r'<(div|figure)([^>]*?)\s*class="[^"]*wu__table-wrap[^"]*"([^>]*)>',
               r'<\1\2\3 class="wu-table max-w-full mb-6 overflow-x-auto rounded-lg">', s)
    s = re.sub(r'<table([^>]*?)\s*class="[^"]*wu__table[^"]*"([^>]*)>', r'<table\1\2>', s)

    # give every <td> a data-label from its column's <th>, so the mobile
    # stylesheet can card-stack the table instead of side-scrolling it
    def label_cells(tm):
        tbl = tm.group(0)
        heads = [H.unescape(re.sub(r'<[^>]+>', '', t)).strip()
                 for t in re.findall(r'<th\b[^>]*>(.*?)</th>', tbl, re.S)]
        if not heads:
            return tbl
        def label_row(rm):
            i = [0]
            def cell(cm):
                lbl = heads[i[0]] if i[0] < len(heads) else ''
                i[0] += 1
                return '<td data-label="%s"%s' % (H.escape(lbl, quote=True), cm.group(1))
            return re.sub(r'<td((?![^>]*data-label)[^>]*)', cell, rm.group(0))
        return re.sub(r'<tr\b.*?</tr>', label_row, tbl, flags=re.S)
    s = re.sub(r'<table\b.*?</table>', label_cells, s, flags=re.S)
    s = s.replace('<div class="wu__diagram">', '<div class="wu-diagram mb-6 overflow-x-auto rounded-lg">')
    return s

def meta_grid(w):
    order = ['Vendor','Component','Product','Class','CWE','CVSS','Endpoint','Fixed in','Interaction','Bounty','Reporter']
    cells = []
    for k in order:
        v = w['meta'].get(k)
        if not v: continue
        cells.append(f'''          <div>
            <p class="{C_LBL}">{H.escape(k)}</p>
            <p class="mt-1 text-white">{H.escape(v)}</p>
          </div>''')
    return ('<div class="border border-white/10 gap-6 grid grid-cols-2 lg:grid-cols-4 md:grid-cols-3 mt-10 p-6 rounded-lg">\n'
            + '\n'.join(cells) + '\n        </div>')

def deck(w, n=200):
    s = w['summary']; cut = s.find('. ')
    return H.escape(s[:cut+1] if 0 < cut < n else (s[:n].rsplit(' ',1)[0] + '…' if len(s) > n else s))

def head(title, desc, p, extra=''):
    return f'''<!doctype html>
<html lang="en" class="bg-primary">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{H.escape(desc, quote=True)}">
<meta name="theme-color" content="#1c1917">
<title>{title}</title>
<link href="{p}assets/site.css" rel="stylesheet">{extra}
</head>
<body>'''

def hdr(p):
    def li(href, label):
        return f'            <li><a href="{href}" class="block pl-3 pr-4 py-2 text-white">{label}</a></li>'
    return f'''<header id="header" class="bg-secondary fixed transition-colors w-full z-50">
  <nav class="border-b border-gray-300 lg:px-6 px-4 py-2.5">
    <div class="flex flex-wrap items-center justify-between max-w-screen-xl mx-auto">
      <a href="{p}index.html" class="flex items-center">
        <span class="font-semibold mr-3 text-2xl text-white">cli<span class="text-accent">0</span>ck</span>
      </a>
      <div class="flex items-center lg:order-2">
        <button type="button" id="menu-btn" class="inline-flex items-center lg:hidden ml-1 p-2 text-white">
          <span class="sr-only">Open main menu</span>
          <svg fill="currentColor" class="h-6 w-6" viewBox="0 0 20 20" aria-hidden="true"><path fill-rule="evenodd" d="M3 5h14a1 1 0 100-2H3a1 1 0 000 2zm0 6h14a1 1 0 100-2H3a1 1 0 000 2zm0 6h14a1 1 0 100-2H3a1 1 0 000 2z" clip-rule="evenodd"/></svg>
        </button>
      </div>
      <div class="hidden items-center justify-between lg:flex lg:order-1 lg:w-auto w-full" id="menu">
        <ul class="flex flex-col font-medium lg:flex-row lg:mt-0 lg:space-x-8 mt-4 text-xl">
{li(p+'index.html','Home')}
{li(p+'research.html','Research')}
{li(p+'index.html#crew','The Crew')}
{li(p+'index.html#record','Record')}
{li('mailto:'+EMAIL,'Contact')}
        </ul>
      </div>
    </div>
  </nav>
</header>'''

ICON_LI = '<svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor" class="text-white" aria-hidden="true"><path d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5ZM3 9h4v12H3V9Zm7 0h3.8v1.7h.05c.53-1 1.83-2.05 3.77-2.05 4.03 0 4.78 2.65 4.78 6.1V21h-4v-5.5c0-1.31-.02-3-1.83-3-1.83 0-2.11 1.43-2.11 2.9V21h-4V9Z"/></svg>'
ICON_GH = '<svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor" class="text-white" aria-hidden="true"><path d="M12 .5a12 12 0 0 0-3.79 23.4c.6.11.82-.26.82-.58v-2.03c-3.34.73-4.04-1.61-4.04-1.61-.55-1.39-1.34-1.76-1.34-1.76-1.09-.75.08-.73.08-.73 1.2.08 1.84 1.24 1.84 1.24 1.07 1.83 2.8 1.3 3.49.99.11-.78.42-1.3.76-1.6-2.67-.3-5.47-1.33-5.47-5.93 0-1.31.47-2.38 1.24-3.22-.12-.3-.54-1.52.12-3.18 0 0 1.01-.32 3.3 1.23a11.5 11.5 0 0 1 6 0c2.29-1.55 3.3-1.23 3.3-1.23.66 1.66.24 2.88.12 3.18.77.84 1.24 1.91 1.24 3.22 0 4.61-2.8 5.62-5.48 5.92.43.37.81 1.1.81 2.22v3.29c0 .32.21.7.82.58A12 12 0 0 0 12 .5Z"/></svg>'
ICON_MAIL = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.7" class="text-white" aria-hidden="true"><rect x="2.5" y="4.5" width="19" height="15" rx="2"/><path d="m3 6 9 7 9-7"/></svg>'

def foot(p):
    socials = f'''<div class="flex gap-6 justify-center">
          <a href="{LI_AZ}" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn">{ICON_LI}</a>
          <a href="{GITHUB}" target="_blank" rel="noopener noreferrer" aria-label="GitHub">{ICON_GH}</a>
          <a href="mailto:{EMAIL}" aria-label="Email">{ICON_MAIL}</a>
        </div>'''
    return f'''<footer class="bg-secondary">
  <div class="border-accent/30 border-y divide-accent/30 divide-y">
    <div class="divide-accent/30 divide-x flex">
      <div class="flex flex-1 items-center">
        <span class="font-semibold m-auto p-6 text-2xl text-white">cli<span class="text-accent">0</span>ck</span>
      </div>
      <div class="flex-1 hidden lg:block p-6 text-center">
        <p class="mb-3 text-white">Connect With Us</p>
        {socials}
      </div>
      <div class="flex-1 lg:text-center p-6">
        <ul class="flex flex-col">
          <li><a href="{p}index.html" class="text-white">Home</a></li>
          <li><a href="{p}research.html" class="text-white">Research</a></li>
          <li><a href="{p}index.html#crew" class="text-white">The Crew</a></li>
          <li><a href="{p}index.html#record" class="text-white">Record</a></li>
          <li><a href="mailto:{EMAIL}" class="text-white">Contact</a></li>
        </ul>
      </div>
    </div>
    <div class="lg:hidden px-16 py-6 text-center">
      <p class="mb-3 text-white">Connect with us</p>
      {socials}
    </div>
  </div>
  <p class="py-6 text-center text-white text-xs">&copy; 2026 cli0ck. All Rights Reserved. &middot; Riyadh, Kingdom of Saudi Arabia</p>
</footer>'''

MENU_JS = '''<script>
(function(){
  var b = document.getElementById('menu-btn'), m = document.getElementById('menu');
  if (b && m) b.addEventListener('click', function(){ m.classList.toggle('hidden'); });
})();
</script>'''

def cta(label, href):
    return f'''<div class="inline-block">
          <a href="{href}" class="bg-gradient-to-r border border-accent flex from-accent items-center rounded-full to-accent-dark transition-all">
            <div class="bg-white/20 flex h-[44px] items-center justify-center rounded-full w-[44px]">
              <span class="text-white text-xl">&rarr;</span>
            </div>
            <div class="font-medium px-9 text-lg text-white">{label}</div>
          </a>
        </div>'''

def press_row(w, p=''):
    return f'''      <a href="{p}research/{w['slug']}.html" class="block group lg:py-10 py-8">
        <div class="flex gap-6 items-baseline justify-between mb-3">
          <span class="lg:text-sm text-white/50 text-xs tracking-[0.2em] uppercase">{H.escape(w['vendor'])} &middot; {H.escape(w['tag'])}</span>
          <span class="c-meta whitespace-nowrap">{w['cve']} &middot; {SEVLBL.get(w['sev'],'')}</span>
        </div>
        <p class="font-medium group-hover:text-accent leading-snug lg:text-3xl text-white text-xl transition-colors">{H.escape(w['title'])}<span class="group-hover:opacity-100 inline-block ml-3 opacity-0 transition-opacity">&rarr;</span></p>
      </a>'''


POSTER = {
  'Mozilla Firefox': ('assets/posters/firefox.svg',   'Mozilla Firefox'),
  'CometChat':       ('assets/posters/cometchat.svg', 'CometChat'),
}
def poster_for(w, assets=''):
    src, alt = POSTER.get(w['vendor'], ('assets/posters/firefox.svg', w['vendor']))
    return assets + src, alt

# calif's research card, with the vendor's logo in the poster tile
def research_card(w, p='', href=None, assets=None):
    assets = p if assets is None else assets
    href = f"{p}research/{w['slug']}.html" if href is None else href
    src, alt = poster_for(w, assets)
    return f'''        <a href="{href}" class="block group rx-card">
          <div class="aspect-[2/3] bg-secondary mb-4 overflow-hidden rounded-lg">
            <img src="{src}" alt="{alt}" loading="lazy" class="duration-300 group-hover:scale-[1.03] h-full object-contain p-6 transition-transform w-full">
          </div>
          <p class="c-meta mb-2">{w['cve']} &middot; {SEVLBL.get(w['sev'],'')}</p>
          <h2 class="font-semibold group-hover:text-accent leading-snug mb-2 text-lg text-white transition-colors">{H.escape(w['title'])}</h2>
          <p class="leading-snug text-sm text-white/60">{deck(w, 130)}</p>
        </a>'''

# ============================================================ HOME
SERVICES = [
 ('Vulnerability research', [
  ('Browser and memory safety',
   'We read the code paths everyone else skips: use-after-free, uninitialised heap disclosure, and process-isolation bypasses. Four CVEs in Mozilla Firefox, including a content-process use-after-free rated CVSS 9.8 and reachable from an ordinary web page.'),
  ('Application security',
   'Stored XSS, broken access control, and authentication flaws across web platforms and SDKs. We test the product you actually shipped, in the environment it actually runs in, and write the report so triage takes an afternoon rather than a fortnight.'),
  ('Responsible disclosure',
   'Private report first, always. A minimised reproducer, a root cause written for the engineer who has to land the patch, and no publication until the fix has reached users. Five disclosures, five vendor fixes, zero leaks.'),
 ]),
 ('Offensive operations', [
  ('Red teaming',
   'Full-chain adversary simulation: initial access, Windows internals and process-level tradecraft, lateral movement, objective. Run by an operator who does this for a living at HABOOB, against the organisation rather than a single application.'),
  ('Penetration testing',
   'Web, mobile, and infrastructure assessments that are original research rather than a checklist run. You get the attack path, the proof it works, and what to change &mdash; not a scanner export with the logo swapped.'),
  ('After the report',
   'A finding is not a fix. We stay available while your team lands the patch, re-test what we broke, and tell you plainly when a control still does not hold.'),
 ]),
]
services = ''
for label, items in SERVICES:
    cards = '\n'.join(f'''          <div>
            <h3 class="font-semibold lg:text-2xl mb-3 text-white text-xl">{t}</h3>
            <p class="leading-relaxed text-white/60">{b}</p>
          </div>''' for t, b in items)
    services += f'''      <div class="lg:mb-16 mb-12">
        <p class="mb-8 text-accent text-xs tracking-[0.2em] uppercase">{label}</p>
        <div class="gap-8 grid grid-cols-1 lg:gap-12 md:grid-cols-3">
{cards}
        </div>
      </div>
'''

def proof_card(src, num, body):
    n = f'<p class="c-proof-num">{num}</p>' if num else ''
    return f'''          <div class="break-inside-avoid c-proof max-w-3xl mx-auto w-full">
            <p class="c-proof-src">{src}</p>
            {n}
            <p class="c-proof-body">{body}</p>
          </div>'''

PROOF = [
 ('Mozilla &middot; Firefox security team', '4 CVEs',
  'Credited across ImageLib, Text, WebRender and Form Autofill &mdash; including a <span class="c-fact">CVSS 9.8</span> use-after-free reachable from an ordinary web page. Bounty awarded.'),
 ('BugBounty.sa &middot; Saudi national platform', '1,060+',
  'Points on the national bug bounty platform, plus third place in the BugBounty Joiner competition.'),
 ('Black Hat MEA 2025 &middot; Bug bounty junior', '3rd',
  'Third against the region&rsquo;s bug bounty field, at the largest security event in the Middle East.'),
 ('Tuwaiq Academy &middot; Mobile CTF', '1st',
  'First across the line in a national mobile application exploitation competition.'),
 ('Tuwaiq Cyber Challenge &middot; Reverse engineering', '3rd',
  'Third overall, and first blood on the reverse engineering track &mdash; first competitor to solve it.'),
 ('Defensathon &middot; Project SATE&rsquo;', '2nd',
  'Second place for an AI-guided counter-UAS laser defence system &mdash; detection, tracking and low-cost interception.'),
 ('CometChat &middot; messaging platform', '',
  'Stored XSS in group messages, reported privately and fixed by the vendor before anything was published here. <span class="c-fact">CVE-2026-39154</span>'),
 ('HABOOB &middot; Red Team Specialist', '',
  'Ahmed runs full-scope red team engagements at one of the Kingdom&rsquo;s leading offensive security firms.'),
 ('Certifications &middot; both operators', '',
  'CRTO &middot; OSCP+ &middot; OSCP &middot; eCDFP &middot; CCNA &middot; eCPPTv3 &middot; eJPTv2. Earned, not collected.'),
]
white_cards = '\n'.join(proof_card(*c) for c in PROOF)

CREW = [
 ('AA','Abdulaziz Alasaiqah','Vulnerability research &middot; web &amp; browser security',
  'Five published CVEs across Mozilla Firefox and CometChat &mdash; a content-process use-after-free in ImageLib, an uninitialised heap leak through a crafted web font, a WebRender Fission bypass, test-only autofill handlers shipped to production, and a stored XSS in group messaging. eCPPTv3, eJPTv2. 1,060+ points on BugBounty.sa.', LI_AZ),
 ('AB','Ahmed Albalawi','Red team &middot; adversary simulation',
  'Red Team Specialist at HABOOB. Focused on offensive security and adversary simulation &mdash; not just finding vulnerabilities, but understanding why they exist and how an attacker actually reaches them. Windows internals, malware tradecraft, and full-chain operations. CRTO, OSCP+, OSCP, eCDFP, CCNA.', None),
]
crew = '\n'.join(f'''          <div>
            <div class="flex items-center mb-4 space-x-3">
              <div class="bg-white/20 flex flex-shrink-0 h-12 items-center justify-center overflow-hidden rounded-full w-12">
                <span class="font-semibold text-white">{i}</span>
              </div>
              <div class="flex-1 min-w-0">
                <h3 class="font-semibold lg:text-2xl text-white text-xl">{n}</h3>
                <p class="text-accent text-xs tracking-[0.2em] uppercase">{r}</p>
              </div>
            </div>
            <p class="leading-relaxed text-white/60">{b}</p>
            {f'<a href="{u}" class="hover:underline inline-block mt-4 text-accent">LinkedIn &rarr;</a>' if u else ''}
          </div>''' for i, n, r, b, u in CREW)

home = head('cli0ck | Vulnerability research',
  'cli0ck is a two-person vulnerability research team in Riyadh. Five CVEs published and fixed in Mozilla Firefox and CometChat, application security, and adversary simulation.', '',
  '\n<link href="assets/writeup.css" rel="stylesheet">') + f'''

{hdr('')}
<main>
  <section class="bg-center bg-cover bg-home lg:pt-[320px] lg:px-10 pt-[170px] px-3 relative">
    <div class="absolute bg-gradient-to-t bottom-0 from-primary h-48 left-0 to-transparent via-primary/70 w-full"></div>
    <div class="relative z-10">
      <div class="max-w-screen-xl mb-20 mx-auto">
        <p class="c-eyebrow mb-5">Vulnerability research &middot; Riyadh</p>
        <h1 class="font-semibold lg:text-6xl mb-5 text-3xl text-white">Five CVEs. Every one fixed before you read this.</h1>
        <p class="font-light lg:mb-10 lg:text-2xl mb-8 text-lg text-white/80">Two researchers out of Riyadh. We break browsers and the software around them, then hand the vendor the root cause and the patch.</p>
        {cta('Put us on your target', 'mailto:' + EMAIL)}
      </div>
    </div>
  </section>

  <section id="customers" class="lg:pb-16 lg:pt-14 lg:px-6 pb-12 pt-8 px-3">
    <div class="lg:pb-14 pb-10 px-3 text-center">
      <p class="text-white/40 text-xs tracking-[0.2em] uppercase">Reported to &middot; competed in &middot; certified by</p>
    </div>
    <div class="logo-container" style="--num-logos:14">
      <div class="logo-slide">
        <img src="assets/logos/mozilla.svg" alt="Mozilla" loading="lazy">
        <img src="assets/logos/firefox.svg" alt="Mozilla Firefox" loading="lazy">
        <img src="assets/logos/cometchat.svg" alt="CometChat" loading="lazy">
        <img src="assets/logos/haboob.svg" alt="HABOOB" loading="lazy">
        <img src="assets/logos/tuwaiq.png" alt="Tuwaiq Academy" loading="lazy">
        <img src="assets/logos/bugbountysa.svg" alt="BugBounty.sa" loading="lazy">
        <img src="assets/logos/ine.svg" alt="INE" loading="lazy">
        <img src="assets/logos/mozilla.svg" alt="Mozilla" loading="lazy">
        <img src="assets/logos/firefox.svg" alt="Mozilla Firefox" loading="lazy">
        <img src="assets/logos/cometchat.svg" alt="CometChat" loading="lazy">
        <img src="assets/logos/haboob.svg" alt="HABOOB" loading="lazy">
        <img src="assets/logos/tuwaiq.png" alt="Tuwaiq Academy" loading="lazy">
        <img src="assets/logos/bugbountysa.svg" alt="BugBounty.sa" loading="lazy">
        <img src="assets/logos/ine.svg" alt="INE" loading="lazy">
      </div>
      <div class="logo-slide">
        <img src="assets/logos/mozilla.svg" alt="Mozilla" loading="lazy">
        <img src="assets/logos/firefox.svg" alt="Mozilla Firefox" loading="lazy">
        <img src="assets/logos/cometchat.svg" alt="CometChat" loading="lazy">
        <img src="assets/logos/haboob.svg" alt="HABOOB" loading="lazy">
        <img src="assets/logos/tuwaiq.png" alt="Tuwaiq Academy" loading="lazy">
        <img src="assets/logos/bugbountysa.svg" alt="BugBounty.sa" loading="lazy">
        <img src="assets/logos/ine.svg" alt="INE" loading="lazy">
        <img src="assets/logos/mozilla.svg" alt="Mozilla" loading="lazy">
        <img src="assets/logos/firefox.svg" alt="Mozilla Firefox" loading="lazy">
        <img src="assets/logos/cometchat.svg" alt="CometChat" loading="lazy">
        <img src="assets/logos/haboob.svg" alt="HABOOB" loading="lazy">
        <img src="assets/logos/tuwaiq.png" alt="Tuwaiq Academy" loading="lazy">
        <img src="assets/logos/bugbountysa.svg" alt="BugBounty.sa" loading="lazy">
        <img src="assets/logos/ine.svg" alt="INE" loading="lazy">
      </div>
    </div>
  </section>

  <section id="services" class="bg-secondary lg:px-6 lg:py-20 px-3 py-12">
    <div class="max-w-screen-xl mx-auto">
      <div class="lg:mb-16 max-w-3xl mb-12">
        <h2 class="font-semibold leading-tight lg:text-5xl mb-6 text-3xl text-white">What we offer</h2>
        <p class="leading-relaxed lg:text-xl text-lg text-white/60">A two-person team that publishes what it finds. Half the work is original vulnerability research on software everyone runs. The other half is the offensive engineering our clients need, done by people whose findings you can go and read.</p>
      </div>
{services}      <p class="lg:mt-16 lg:text-lg mt-12 text-base text-white/40">None of this is a claim you have to take on trust. <a href="research.html" class="hover:underline text-accent">Read the research &rarr;</a></p>
    </div>
  </section>

  <section id="research" class="lg:px-6 lg:py-24 px-3 py-16">
    <div class="max-w-screen-xl mx-auto">
      <p class="font-mono mb-4 text-accent text-sm">$ cat cves.txt</p>
      <h2 class="font-semibold leading-tight lg:mb-16 lg:text-5xl max-w-4xl mb-12 text-3xl text-white">The work, as the vendors recorded it</h2>
      <div class="gap-x-6 gap-y-12 grid grid-cols-2 lg:grid-cols-4 md:grid-cols-3">
{chr(10).join(research_card(w) for w in ordered[:4])}
      </div>
      <p class="lg:mt-16 lg:text-lg mt-12 text-base text-white/40"><a href="research.html" class="hover:underline text-accent">All 5 write-ups &rarr;</a></p>
    </div>
  </section>


  <section id="reach" class="lg:px-6 lg:py-24 px-3 py-16">
    <div class="max-w-screen-xl mx-auto">
      <p class="c-eyebrow mb-5">Reach</p>
      <h2 class="font-semibold leading-tight lg:mb-10 lg:text-5xl mb-4 max-w-3xl text-3xl text-white">Five bugs found in Riyadh. Patched on every continent.</h2>
      <p class="leading-relaxed lg:text-xl max-w-3xl text-lg text-white/60">Every vulnerability below was reported privately from here, fixed by the vendor, and shipped in a release that reached the whole install base. The scores and statuses below are pulled live from NIST&rsquo;s National Vulnerability Database every time this page loads &mdash; our disclosure record, read straight from the source. Not telemetry, and not a threat feed.</p>
      <div class="c-map-wrap lg:mt-16 mt-10">
        <canvas class="c-map" id="reachmap" aria-label="World map showing disclosures reported from Riyadh and the releases that carried the fixes worldwide"></canvas>
        <div class="c-map-cap">
          <div class="c-live-head">
            <span class="c-live-dot is-cached" id="mapdot"></span>
            <span class="c-live-src">National Vulnerability Database</span>
            <span class="c-live-sync" id="mapsync">syncing&hellip;</span>
          </div>
          <div class="c-live-row">
            <span class="c-map-cve" id="mapcve">CVE-2026-74943</span>
            <span class="c-live-score sev-critical" id="mapscore">9.8 CRITICAL</span>
            <span class="c-live-status" id="mapstatus">Modified &middot; published 2026-08-18</span>
          </div>
          <span class="c-map-what" id="mapwhat">Use-after-free in RasterImage surface discard &middot; Mozilla Firefox</span>
        </div>
      </div>
      <div class="c-map-legend">
        <b><i class="o"></i>Reported from Riyadh</b>
        <b><i class="p"></i>Carried by the vendor release</b>
        <b><span id="maptotal">384,715</span>&nbsp;CVEs in NVD &mdash; five are ours</b>
      </div>
    </div>
  </section>

  <section id="crew" class="bg-secondary lg:px-6 lg:py-24 px-3 py-16">
    <div class="max-w-screen-xl mx-auto">
      <div class="lg:mb-16 max-w-3xl mb-12">
        <p class="mb-4 text-white/40 text-xs tracking-[0.2em] uppercase">The crew</p>
        <h2 class="font-semibold leading-tight lg:text-5xl mb-6 text-3xl text-white">Two people, two halves of the same problem</h2>
      </div>
      <div class="gap-8 grid grid-cols-1 lg:gap-12 md:grid-cols-2">
{crew}
      </div>
    </div>
  </section>

  <section id="record" class="bg-white">
    <div class="lg:py-24 py-16">
      <div class="lg:pb-16 max-w-screen-xl mx-auto pb-12 px-3">
        <p class="c-eyebrow c-eyebrow--light mb-5">Third-party record</p>
        <h2 class="font-semibold lg:text-5xl max-w-3xl text-3xl">Don&rsquo;t take our word for it.</h2>
      </div>
      <div class="px-3">
        <div class="columns-1 gap-3 lg:columns-3 max-w-screen-xl md:columns-2 mx-auto">
{white_cards}
        </div>
      </div>
    </div>
  </section>

  <section class="bg-primary lg:px-10 lg:py-20 px-3 py-16">
    <div class="max-w-screen-xl mx-auto text-center">
      <h2 class="font-semibold lg:text-5xl mb-4 text-3xl text-white">Let&rsquo;s talk</h2>
      <p class="font-light lg:mb-10 lg:text-2xl mb-8 text-lg text-white/80">Tell us what you&rsquo;re building, and what keeps you up at night.</p>
      {cta('Put us on your target', 'mailto:' + EMAIL)}
    </div>
  </section>
</main>
{foot('')}
{MENU_JS}
<script src="assets/map.js" defer></script>
</body>
</html>'''
open(f'{OUT}/index.html','w',encoding='utf-8').write(home)
print(f'  index.html  {len(home)}')

# ============================================================ RESEARCH INDEX
research = head('Research | cli0ck',
  'Root-cause analysis and a working proof of concept for every vulnerability cli0ck has disclosed.', '',
  '\n<link href="assets/writeup.css" rel="stylesheet">') + f'''

{hdr('')}
<main>
  <section class="lg:pb-24 lg:pt-40 lg:px-6 pb-16 pt-32 px-3">
    <div class="max-w-screen-xl mx-auto">
      <p class="font-mono mb-4 text-accent text-sm">$ cat cves.txt</p>
      <h1 class="font-semibold leading-tight lg:text-6xl max-w-4xl mb-6 text-4xl text-white">Root cause, proof of concept, and the patch that followed.</h1>
      <p class="leading-relaxed lg:mb-16 lg:text-xl max-w-2xl mb-12 text-lg text-white/60">Every vulnerability below was reported privately, reproduced, root-caused, and fixed by the vendor before it was published here. Nothing on this page is a claim you have to take on trust.</p>

      <div class="gap-x-6 gap-y-12 grid grid-cols-2 lg:grid-cols-4 md:grid-cols-3">
{chr(10).join(research_card(w) for w in ordered)}
      </div>

      <div class="border-t border-white/15 gap-6 grid grid-cols-2 lg:grid-cols-4 mt-16 pt-12">
        <div>
          <p class="font-semibold lg:text-5xl text-3xl text-white">5</p>
          <p class="mt-2 text-white/40 text-xs tracking-[0.2em] uppercase">CVEs published</p>
        </div>
        <div>
          <p class="font-semibold lg:text-5xl text-3xl text-white">9.8</p>
          <p class="mt-2 text-white/40 text-xs tracking-[0.2em] uppercase">Highest CVSS</p>
        </div>
        <div>
          <p class="font-semibold lg:text-5xl text-3xl text-white">2</p>
          <p class="mt-2 text-white/40 text-xs tracking-[0.2em] uppercase">Vendors credited</p>
        </div>
        <div>
          <p class="font-semibold lg:text-5xl text-3xl text-white">100%</p>
          <p class="mt-2 text-white/40 text-xs tracking-[0.2em] uppercase">Fixed before publication</p>
        </div>
      </div>
    </div>
  </section>

  <section class="bg-secondary lg:px-10 lg:py-20 px-3 py-16">
    <div class="max-w-screen-xl mx-auto text-center">
      <h2 class="font-semibold lg:text-5xl mb-4 text-3xl text-white">Let&rsquo;s talk</h2>
      <p class="font-light lg:mb-10 lg:text-2xl mb-8 text-lg text-white/80">Tell us what you&rsquo;re building, and what keeps you up at night.</p>
      {cta('Put us on your target', 'mailto:' + EMAIL)}
    </div>
  </section>
</main>
{foot('')}
{MENU_JS}
</body>
</html>
'''
open(f'{OUT}/research.html','w',encoding='utf-8').write(research)
print(f'  research.html  {len(research)}')

# ============================================================ ARTICLES
for i, w in enumerate(WRITEUPS):
    prev, nxt = (WRITEUPS[i-1] if i else None), (WRITEUPS[i+1] if i < len(WRITEUPS)-1 else None)
    body = to_calif(w['inner'])
    pills = ''.join(f'<span class="{C_PILL}">{H.escape(t)}</span>'
                    for t in [w['vendor'], w['tag'], w['meta'].get('Class',''), SEVLBL.get(w['sev'],'')] if t)
    nxt_html = ''
    cards = [x for x in (prev, nxt) if x]
    if cards:
        nxt_html = f'''
      <div class="border-t border-white/15 mt-16 pt-10">
        <p class="mb-6 text-white/40 text-xs tracking-[0.2em] uppercase">More research</p>
        <div class="gap-x-6 gap-y-12 grid grid-cols-2">
{chr(10).join(research_card(x, href=f"{x['slug']}.html", assets='../') for x in cards)}
        </div>
      </div>'''

    page = head(f"{w['cve']} &mdash; {H.escape(w['title'])} | cli0ck", w['summary'][:180], '../',
                '\n<link href="../assets/writeup.css" rel="stylesheet">') + f'''

{hdr('../')}
<main>
  <article class="lg:pb-24 lg:pt-40 lg:px-6 pb-16 pt-32 px-3">
    <div class="max-w-3xl mx-auto">
      <a href="../research.html" class="hover:text-accent text-white/40 text-xs tracking-[0.2em] transition-colors uppercase">&larr; Research</a>
      <h1 class="font-semibold leading-tight lg:text-5xl mb-4 mt-6 text-3xl text-white">{H.escape(w['title'])}</h1>
      <p class="font-light lg:text-xl mb-4 text-lg text-white/80">{deck(w, 300)}</p>
      <div class="border-b border-white/15 pb-10">
        <p class="font-medium text-sm text-white tracking-[0.15em] uppercase">Abdulaziz Alasaiqah</p>
        <p class="mt-2 text-white/40 text-xs tracking-[0.15em] uppercase">{w['cve']} &middot; {H.escape(w['status'])}</p>
        <div class="flex flex-wrap gap-2 mt-6">{pills}</div>
      </div>

      {meta_grid(w)}

      <div class="pt-10">
{body}
      </div>
{nxt_html}
    </div>
  </article>

  <section class="bg-secondary lg:px-10 lg:py-20 px-3 py-16">
    <div class="max-w-screen-xl mx-auto text-center">
      <h2 class="font-semibold lg:text-5xl mb-4 text-3xl text-white">Let&rsquo;s talk</h2>
      <p class="font-light lg:mb-10 lg:text-2xl mb-8 text-lg text-white/80">Tell us what you&rsquo;re building, and what keeps you up at night.</p>
      {cta('Put us on your target', 'mailto:' + EMAIL)}
    </div>
  </section>
</main>
{foot('../')}
{MENU_JS}
</body>
</html>
'''
    open(f"{OUT}/research/{w['slug']}.html", 'w', encoding='utf-8').write(page)
    print(f"  research/{w['slug']}.html  {len(page)}")
