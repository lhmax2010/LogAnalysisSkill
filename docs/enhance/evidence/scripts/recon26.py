# recon26: recon25 part E only, with the next-page link text HTML-unescaped (recon25 stopped after page 1).
# Read-only https, anonymous, no login, no p4. Writes NO files. List contents are never printed (counts/digests only).
import hashlib, html, html.parser, http.cookiejar, re, sys, time, urllib.error, urllib.parse, urllib.request
BM_HOST = 'vdcosmos-bm.sec.samsung.net'
BM = 'https://' + BM_HOST
CONFIG = '4362'
BUILDS = ['19206687', '19270912']
EXTRA = ['19091860', '19287341']   # recon22 reference digests exist for 19287341; 19091860 is used by checkpoint A
KNOWN = {('19206687', 'PACKAGE_LIST'): 'b4831e2ede7a38d9', ('19206687', 'SHELVE_LIST'): '249832d7df09e0f2',
         ('19270912', 'PACKAGE_LIST'): 'b4831e2ede7a38d9', ('19270912', 'SHELVE_LIST'): 'e3b0c44298fc1c14',
         ('19287341', 'PACKAGE_LIST'): '8b1b19fed8d77859', ('19287341', 'SHELVE_LIST'): '13b21f95bac54941'}
WIN_FROM, WIN_TO = '2026-11-05 12:00:00', '2026-11-05 15:43:00'
TARGET_HUB, MAX_PAGES, MAX_DETAIL = '37432138', 320, 400
VOCAB = {'', 'true', 'false', 'yes', 'no', 'on', 'off', 'full', 'partial', 'armv7l'}
CRED = re.compile(r'PASS|PWD|TOKEN|SECRET|KEY|CRED|AUTH|COOKIE|TICKET|SESSION|PRIVATE', re.I)
NO_DIGEST = {'SHELVE_LIST'}
EXACT_BUILD_CONF = '//SHARED/[TizenBuild_Prj]/[INT]/buildconf/tizen/TEST/migration/10.0/TV/TIZEN_KantSU2E_Clang_build.conf@14368686'
def say(*a): print(*a, flush=True)
def h16(s): return hashlib.sha256(s.encode('utf-8', 'surrogateescape')).hexdigest()[:16]
class NoRedir(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedir(), urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
PLAIN = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedir())
def get(url, op=PLAIN):
    try:
        with op.open(urllib.request.Request(url, headers={'User-Agent': 'vd-cosmos-recon'}), timeout=120) as r:
            return r.status, r.read(30 * 1024 * 1024).decode('utf-8', 'replace'), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, '', dict(e.headers or {})
    except Exception as e:
        return type(e).__name__, '', {}
def get_follow(url):
    for _ in range(4):
        st, t, hd = get(url, OPENER)
        loc = hd.get('Location') or hd.get('location') or ''
        if str(st).startswith('3') and loc:
            nu = urllib.parse.urljoin(url, loc); p = urllib.parse.urlsplit(nu)
            if p.netloc != BM_HOST or not re.sub(r';jsessionid=[^/?#]*', '', p.path).startswith('/history/' + CONFIG): return st, '', url
            url = nu; continue
        return st, t, url
    return 'too_many_redirects', '', url
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
def cmp1(v):
    lines = [l.rstrip() for l in v.replace('\r\n', '\n').replace('\r', '\n').split('\n')]
    while lines and lines[-1] == '': lines.pop()
    return '\n'.join(lines)
def norm21(v): return '\n'.join(l.strip() for l in v.replace('\r\n', '\n').replace('\r', '\n').split('\n') if l.strip())
def shape(raw):
    ls = raw.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    lead = next((i for i, l in enumerate(ls) if l.strip()), len(ls))
    trail = 0 if lead == len(ls) else next(i for i, l in enumerate(reversed(ls)) if l.strip())
    ws = sum(1 for l in ls if l.strip() and l[:1].isspace())
    return f'L{lead}T{trail}W{ws}'
def variables(bm):
    st, t, _ = get(f'{BM}/build/{bm}/variables')
    if not t: return st, None, None
    p = HP(); p.feed(t); del t
    hdr, got = None, {}
    for tr in (n for n in walk(p.root) if n['tag'] == 'tr'):
        cells = [k for k in tr['kids'] if isinstance(k, dict) and k['tag'] in ('td', 'th')]
        heads = [text(c).strip() for c in cells]
        if hdr is None and 'Name' in heads and 'Value' in heads:
            hdr = heads; continue
        if hdr is None or len(cells) != len(hdr): continue
        row = dict(zip(hdr, cells))
        name = text(row['Name']).strip()
        if name: got.setdefault(name, []).append((text(row.get('Display Name', {'tag': 'x', 'kids': []})).strip(), text(row['Value']), ''.join(text(c) for c in cells[1:])))
    return st, hdr, got

say('== recon26 start', time.strftime('%F %T'), 'python', sys.version.split()[0])
say('== E 37432138 rerun check')
st, t, url = get_follow(f'{BM}/history/{CONFIG}')
DT = re.compile(r'\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}:\d{2}')
def rows_of(t):
    out = []
    for r in re.findall(r'<tr[^>]*>(.*?)</tr>', t, re.S | re.I):
        m = re.search(r'/build/(\d{6,9})\b', r)
        if m:
            d = DT.search(html.unescape(re.sub(r'<[^>]*>', ' ', r)))
            out.append((m.group(1), d.group(0) if d else ''))
    return out
def next_href(t):
    for a in re.finditer(r'<a\b([^>]*)>(.*?)</a>', t, re.S | re.I):
        if html.unescape(re.sub(r'<[^>]*>', '', a.group(2))).strip() in ('>', '›', 'Next'):
            h = re.findall(r'href\s*=\s*["\']([^"\']*)', a.group(1), re.I)
            return html.unescape(h[0]) if h else ''
    return ''
rows, pages, stop = rows_of(t), 1, 'max_pages'
while pages < MAX_PAGES:
    if rows and rows[-1][1] and rows[-1][1] < WIN_FROM: stop = 'reached_window_start'; break
    h = next_href(t)
    if not h: stop = 'no_next_link'; break
    st, t, url = get_follow(urllib.parse.urljoin(url, h))
    rs = rows_of(t)
    if not rs: stop = f'empty_page({st})'; break
    rows += rs; pages += 1; time.sleep(0.3)
seen, uniq = set(), []
for r in rows:
    if r[0] not in seen: seen.add(r[0]); uniq.append(r)
win = [r for r in uniq if r[1] and WIN_FROM <= r[1] < WIN_TO]
say(f'   stop {stop}; pages {pages}; builds {len(uniq)}; oldest {uniq[-1][1] if uniq else ""}; in window {len(win)}')
HUB = re.compile(r'Hub Link\s*:\s*(?:<[^a][^>]*>\s*)*<a\b[^>]*href\s*=\s*["\']https?://vdcosmos-hub[^"\']*?/build/(\d{6,9})', re.I)
found = []
for bid, begin in win[:MAX_DETAIL]:
    st, d, _ = get(f'{BM}/build/{bid}')
    hub = HUB.findall(d)
    if TARGET_HUB in hub: found.append((bid, begin, hub))
    time.sleep(0.2)
say(f'   builds whose Hub Link list contains {TARGET_HUB}: {found}')
say('== recon26 end', time.strftime('%F %T'))
