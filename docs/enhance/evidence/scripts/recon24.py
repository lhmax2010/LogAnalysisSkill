# recon24: why did PACKAGE_LIST / SHELVE_LIST on variable pages change between recon22 (11-10) and recon23 (11-14)?
# Read-only https, anonymous, no login, no p4. Writes NO files. Never prints list contents: counts and digests only.
import hashlib, html, html.parser, re, sys, time, urllib.error, urllib.request
BM = 'https://vdcosmos-bm.sec.samsung.net'
CONFIG = '4362'
FIXED = ['19091860', '19206687', '19270877', '19270912', '19287341']
KNOWN = {  # recon21/22 digests (11-10), recon21-style normalization
    ('19206687', 'PACKAGE_LIST'): ('b4831e2ede7a38d9', 2245), ('19206687', 'SHELVE_LIST'): ('249832d7df09e0f2', 893),
    ('19270877', 'PACKAGE_LIST'): ('b4831e2ede7a38d9', 2245), ('19270877', 'SHELVE_LIST'): ('d522141f10d750a3', 903),
    ('19270912', 'PACKAGE_LIST'): ('b4831e2ede7a38d9', 2245), ('19270912', 'SHELVE_LIST'): ('e3b0c44298fc1c14', 0),
    ('19287341', 'PACKAGE_LIST'): ('8b1b19fed8d77859', 2245), ('19287341', 'SHELVE_LIST'): ('13b21f95bac54941', 907),
}
NAMES = ['PACKAGE_LIST', 'SHELVE_LIST', 'PACKAGE_LIST_armv7l', 'BUILD_TYPE']
CRED = re.compile(r'passw|pwd|token|secret|cookie|ticket|session', re.I)
def say(*a): print(*a, flush=True)
class NoRedir(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None
OP = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedir())
def get(url):
    try:
        with OP.open(urllib.request.Request(url, headers={'User-Agent': 'vd-cosmos-recon'}), timeout=120) as r:
            return r.status, r.read(30 * 1024 * 1024).decode('utf-8', 'replace'), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, '', dict(e.headers or {})
    except Exception as e:
        return type(e).__name__, '', {}
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
class HP(html.parser.HTMLParser):
    def __init__(s):
        super().__init__(convert_charrefs=True); s.root = {'tag': '#root', 'attrs': {}, 'kids': []}; s.cur = [s.root]
    def handle_starttag(s, tag, attrs):
        n = {'tag': tag, 'attrs': dict((k, v or '') for k, v in attrs), 'kids': []}
        s.cur[-1]['kids'].append(n)
        if tag == 'br': s.cur[-1]['kids'].append('\n')
        if tag not in VOID: s.cur.append(n)
    def handle_endtag(s, tag):
        for i in range(len(s.cur) - 1, 0, -1):
            if s.cur[i]['tag'] == tag: del s.cur[i:]; break
    def handle_data(s, d): s.cur[-1]['kids'].append(d)
def text(n):
    if isinstance(n, str): return n
    t = ''.join(text(k) for k in n['kids'])
    return t + '\n' if n['tag'] in ('tr', 'p', 'div', 'li', 'pre') else t
def walk(n):
    if isinstance(n, str): return
    yield n
    for k in n['kids']: yield from walk(k)
def norm(v): return '\n'.join(l.strip() for l in v.replace('\r\n', '\n').replace('\r', '\n').split('\n') if l.strip())
def dig(v): return hashlib.sha256(norm(v).encode()).hexdigest()[:16]
def short(s):
    s = re.sub(r'\s+', ' ', s).strip()
    return '<hidden>' if CRED.search(s) else (s if len(s) <= 40 else s[:40] + '…')

say('== recon24 start', time.strftime('%F %T'), 'python', sys.version.split()[0])
st, t, _ = get(f'{BM}/history/{CONFIG}')
ids = re.findall(r'/build/(\d{6,9})\b', t)
newest = ids[0] if ids else None
say(f'  history page 1 status {st}; newest build {newest}')
for bm in FIXED + ([newest] if newest else []):
    st, page, hd = get(f'{BM}/build/{bm}/variables')
    say(f'-- {bm}: status {st}; bytes {len(page)}; Last-Modified {hd.get("Last-Modified", "-")}; Date {hd.get("Date", "-")}')
    if not page: continue
    p = HP(); p.feed(page)
    tables = [n for n in walk(p.root) if n['tag'] == 'table']
    occ = ', '.join('%s=%d' % (n, len(re.findall(r'>\s*' + re.escape(n) + r'\s*<', page))) for n in NAMES)
    say(f'   tables {len(tables)}; raw occurrences: {occ}')
    heads = []
    for tb in tables:
        for tr in (n for n in walk(tb) if n['tag'] == 'tr'):
            hs = [short(text(k)) for k in tr['kids'] if isinstance(k, dict) and k['tag'] == 'th']
            if hs: heads.append(hs); break
    say(f'   table headers: {heads}')
    links = sorted({re.sub(r'\?.*$', '', a['attrs'].get('href', '')) for a in walk(p.root) if a['tag'] == 'a' and re.search(r'variab|param|prompt', a['attrs'].get('href', ''), re.I)})
    say(f'   variable-related link paths: {links[:10]}')
    for tr in (n for n in walk(p.root) if n['tag'] == 'tr'):
        cells = [k for k in tr['kids'] if isinstance(k, dict) and k['tag'] in ('td', 'th')]
        if len(cells) < 2: continue
        name = text(cells[0]).strip()
        if name not in NAMES: continue
        v = text(cells[1])
        extra = [short(text(c)) for c in cells[2:]] if name != 'SHELVE_LIST' else ['<not shown>']
        k = KNOWN.get((bm, name))
        cmp = f'; recon22: {k[1]} lines {k[0]} -> same={dig(v) == k[0]}' if k else ''
        say(f'   {name}: cells {len(cells)}; value nonempty_lines {len(norm(v).splitlines()) if norm(v) else 0}; digest {dig(v)}; other columns {extra}{cmp}')
    time.sleep(0.5)
say('== recon24 end', time.strftime('%F %T'))
