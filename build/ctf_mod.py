# ============================================================
#  CTF write-ups: one markdown file per event, many challenges
#  inside it. Drop a file in build/ctf/ and rebuild.
# ============================================================
import re, os, html as H

CTF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ctf')

CAT = {
  'web':     ('Web',                'cat-web'),
  'rev':     ('Reverse Engineering','cat-rev'),
  'reverse': ('Reverse Engineering','cat-rev'),
  'pwn':     ('Pwn',                'cat-pwn'),
  'binary':  ('Pwn',                'cat-pwn'),
  'mobile':  ('Mobile',             'cat-mob'),
  'crypto':  ('Crypto',             'cat-cry'),
  'forensics':('Forensics',         'cat-for'),
  'misc':    ('Misc',               'cat-misc'),
  'osint':   ('OSINT',              'cat-misc'),
}

def _slug(s):
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', s.lower())).strip('-')

def load_events():
    out = []
    if not os.path.isdir(CTF_DIR): return out
    for fn in sorted(os.listdir(CTF_DIR)):
        if not fn.endswith('.md') or fn.startswith('EXAMPLE'): continue
        raw = open(os.path.join(CTF_DIR, fn), encoding='utf-8').read()
        m = re.match(r'---\n(.*?)\n---\n(.*)', raw, re.S)
        if not m: continue
        meta = {}
        for line in m.group(1).split('\n'):
            if ':' in line:
                k, v = line.split(':', 1); meta[k.strip()] = v.strip()
        chals = []
        for blk in re.split(r'\n## challenge\n', m.group(2))[1:]:
            head, _, rest = blk.partition('\n---\n')
            c = {}
            for line in head.split('\n'):
                if ':' in line:
                    k, v = line.split(':', 1); c[k.strip()] = v.strip()
            c['body'] = rest.strip()
            c['slug'] = _slug(c.get('name', 'challenge'))
            chals.append(c)
        meta['slug'] = _slug(meta.get('event', fn[:-3]))
        meta['challenges'] = chals
        meta['file'] = fn
        out.append(meta)
    out.sort(key=lambda e: e.get('date', ''), reverse=True)
    return out

# ---------- a very small markdown renderer, calif classes only ----------
C_H3   = 'break-words font-semibold lg:text-2xl mb-4 mt-10 scroll-mt-24 text-white text-xl'
C_P    = 'break-words leading-relaxed mb-5 text-white/80'
C_PRE  = 'bg-black/40 border border-white/10 max-w-full mb-6 overflow-x-auto p-4 rounded-lg'
C_CODE = 'font-mono leading-relaxed text-sm text-white/90'
C_IC   = 'bg-white/10 break-all font-mono px-1.5 py-0.5 rounded text-[0.9em] text-accent'
C_A    = 'hover:underline text-accent'

def render(md):
    md = md.replace('\r\n', '\n')
    parts, out = re.split(r'```(\w*)\n(.*?)```', md, flags=re.S), []
    i = 0
    while i < len(parts):
        prose = parts[i]
        for para in re.split(r'\n\s*\n', prose):
            para = para.strip()
            if not para: continue
            if para.startswith('### '):
                t = H.escape(para[4:].strip())
                out.append(f'<h3 id="{_slug(t)}" class="{C_H3}">{t}</h3>')
                continue
            if re.match(r'^\s*[-*]\s+', para):
                items = [re.sub(r'^\s*[-*]\s+', '', l) for l in para.split('\n') if l.strip()]
                lis = ''.join(f'<li class="break-words leading-relaxed">{_inline(x)}</li>' for x in items)
                out.append(f'<ul class="list-disc marker:text-accent mb-6 pl-5 space-y-2 text-white/80">{lis}</ul>')
                continue
            if re.match(r'^\s*\d+\.\s+', para):
                items = [re.sub(r'^\s*\d+\.\s+', '', l) for l in para.split('\n') if l.strip()]
                lis = ''.join(f'<li class="break-words leading-relaxed pl-1">{_inline(x)}</li>' for x in items)
                out.append(f'<ol class="list-decimal marker:text-accent mb-6 pl-5 space-y-2 text-white/80">{lis}</ol>')
                continue
            out.append(f'<p class="{C_P}">{_inline(para)}</p>')
        if i + 2 < len(parts):
            code = H.escape(parts[i+2].rstrip())
            out.append(f'<pre class="{C_PRE}"><code class="{C_CODE}">{code}</code></pre>')
        i += 3
    return '\n        '.join(out)

def _inline(s):
    s = H.escape(s)
    s = re.sub(r'`([^`]+)`', lambda m: f'<code class="{C_IC}">{m.group(1)}</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong class="font-semibold text-white">\1</strong>', s)
    s = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',
               lambda m: f'<a class="{C_A}" href="{m.group(2)}" target="_blank" rel="noopener">{m.group(1)}</a>', s)
    return s.replace('\n', ' ')

def cat_of(c):
    return CAT.get((c.get('category') or 'misc').lower().strip(), ('Misc', 'cat-misc'))
