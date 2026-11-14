# recon23: 23rd read-only reconnaissance (HLD v0.9.18 §14 item 23).
# Part D: variable pages of 19206687 and 19270912 -> all variable names, digests, shapes, exact checks, cmp-v1.
# Part E: was there another build (start 2026-11-05 12:00:00 ~ 15:43:00 server time) with Hub Link 37432138?
# Read-only https, no login, no form submit, no p4. Anonymous session only in memory. Writes NO files
# (stdout is redirected by the caller). Plaintext is printed only for values in a fixed vocabulary.
import hashlib, html, html.parser, http.cookiejar, re, sys, time, urllib.error, urllib.parse, urllib.request
BM_HOST = 'vdcosmos-bm.sec.samsung.net'
BM = 'https://' + BM_HOST
CONFIG = '4362'
BUILDS = ['19206687', '19270912']
WIN_FROM, WIN_TO = '2026-11-05 12:00:00', '2026-11-05 15:43:00'   # server time
TARGET_HUB = '37432138'
KNOWN_START = '2026-11-05 15:42:50'
MAX_PAGES, MAX_DETAIL, MAX_SECONDS = 320, 400, 2400
VOCAB = {'', 'true', 'false', 'yes', 'no', 'on', 'off', 'full', 'partial', 'armv7l'}
CRED_NAME = re.compile(r'PASS|PWD|TOKEN|SECRET|KEY|CRED|AUTH|COOKIE|TICKET|SESSION|PRIVATE', re.I)
NO_DIGEST = {'SHELVE_LIST'}
EXACT_BUILD_CONF = '//SHARED/[TizenBuild_Prj]/[INT]/buildconf/tizen/TEST/migration/10.0/TV/TIZEN_KantSU2E_Clang_build.conf@14368686'
T0 = time.time()

def say(*a): print(*a, flush=True)
def h16(s): return hashlib.sha256(s.encode('utf-8', 'surrogateescape')).hexdigest()[:16]
def hfull(s): return hashlib.sha256(s.encode('utf-8', 'surrogateescape')).hexdigest()
def over_time(): return time.time() - T0 > MAX_SECONDS

class NoRedir(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None
JAR = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedir(), urllib.request.HTTPCookieProcessor(JAR))
PLAIN = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedir())
def get(url, op):
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
            if p.netloc != BM_HOST or not re.sub(r';jsessionid=[^/?#]*', '', p.path).startswith('/history/' + CONFIG):
                return st, '', url
            url = nu; continue
        return st, t, url
    return 'too_many_redirects', '', url

def plain(t): return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]*>', ' ', t)))
DT = re.compile(r'\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}:\d{2}')
def rows_of(t):
    out = []
    for r in re.findall(r'<tr[^>]*>(.*?)</tr>', t, re.S | re.I):
        m = re.search(r'/build/(\d{6,9})\b', r)
        if not m: continue
        d = DT.search(plain(r))
        out.append((m.group(1), d.group(0) if d else ''))
    return out
def next_href(t):
    for a in re.finditer(r'<a\b([^>]*)>(.*?)</a>', t, re.S | re.I):
        if plain(a.group(2)).strip() in ('>', '›', 'Next'):
            h = re.findall(r'href\s*=\s*["\']([^"\']*)', a.group(1), re.I)
            return html.unescape(h[0]) if h else ''
    return ''
HUBLINK = re.compile(r'Hub Link\s*:\s*(?:<[^a][^>]*>\s*)*<a\b[^>]*href\s*=\s*["\']https?://vdcosmos-hub[^"\']*?/build/(\d{6,9})', re.I)

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

# cmp-v1: newlines -> LF, strip trailing whitespace of each line, drop trailing empty lines.
# Keeps leading indentation, inner whitespace and empty lines in the middle (HLD §14 item 23).
def cmp1(v):
    lines = [l.rstrip() for l in v.replace('\r\n', '\n').replace('\r', '\n').split('\n')]
    while lines and lines[-1] == '': lines.pop()
    return '\n'.join(lines)
def shape(raw):
    ls = raw.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    lead = 0
    for l in ls:
        if l.strip(): break
        lead += 1
    trail = 0
    for l in reversed(ls):
        if l.strip(): break
        trail += 1
    if lead == len(ls): trail = 0
    ws_lines = sum(1 for l in ls if l.strip() and l[:1].isspace())
    first_ws = len(ls[0]) - len(ls[0].lstrip()) if ls else 0
    fnb = next((l for l in ls if l.strip()), '')
    return f'lead_blank={lead} trail_blank={trail} lines_with_leading_ws={ws_lines} first_line_leading_ws={first_ws} first_nonblank_leading_ws={len(fnb) - len(fnb.lstrip())} total_lines={len(ls)}'

def variables(bm):
    st, t, _ = get(f'{BM}/build/{bm}/variables', PLAIN)
    if not t: return st, None
    p = HP(); p.feed(t); del t
    got = {}
    for tr in (n for n in walk(p.root) if n['tag'] == 'tr'):
        cells = [k for k in tr['kids'] if isinstance(k, dict) and k['tag'] in ('td', 'th')]
        if len(cells) >= 2:
            name = text(cells[0]).strip()
            if name: got.setdefault(name, []).append((len(cells) - 1, ''.join(text(c) for c in cells[1:])))
    return st, got

say('== recon23 start', time.strftime('%F %T'), 'python', sys.version.split()[0])
say('== D variable pages')
res, order = {}, []
for bm in BUILDS:
    st, g = variables(bm)
    say(f'-- build {bm}: status {st}, variables found {len(g) if g else 0}')
    res[bm] = g or {}
    for k in (g or {}):
        if k not in order: order.append(k)
say('  all variable names (union, page order): ' + ', '.join(order))
summ = {}
for name in order:
    sensitive = bool(CRED_NAME.search(name))
    say(f'-- {name}' + ('  [credential-like name: only listed/line count]' if sensitive else ''))
    for bm in BUILDS:
        occ = res[bm].get(name)
        if not occ:
            say(f'   {bm}: listed=no'); summ[(bm, name)] = None; continue
        ncells, raw = occ[0]
        nonempty = sum(1 for l in raw.splitlines() if l.strip())
        dup = f' DUPLICATE x{len(occ)}' if len(occ) > 1 else ''
        if sensitive or name in NO_DIGEST:
            say(f'   {bm}: listed=yes{dup} nonempty_lines={nonempty}')
            summ[(bm, name)] = ('hidden', nonempty); continue
        c = cmp1(raw)
        shown = f' value={c!r}' if c.lower() in VOCAB else ''
        extra = ''
        if name == 'PACKAGE_LIST':
            extra = ' sorted_nonblank_lines_digest=' + h16('\n'.join(sorted(l.strip() for l in c.split('\n') if l.strip())))
        say(f'   {bm}: listed=yes{dup} cells_after_name={ncells} nonempty_lines={nonempty} raw_digest={h16(raw)} cmpv1_digest={h16(c)}{shown}{extra}')
        say(f'   {bm}: shape {shape(raw)}')
        summ[(bm, name)] = (hfull(raw), hfull(c))
    a, b = summ.get((BUILDS[0], name)), summ.get((BUILDS[1], name))
    if a and b and a[0] != 'hidden':
        say(f'   same_between_builds: raw={a[0] == b[0]} cmpv1={a[1] == b[1]}')
    elif a is None or b is None:
        say(f'   same_between_builds: n/a (listed in {BUILDS[0]}={a is not None}, {BUILDS[1]}={b is not None})')

say('== D2 exact checks (cmp-v1)')
def exact(bm, name, expected):
    occ = res[bm].get(name)
    if not occ: return 'not listed'
    return str(hfull(cmp1(occ[0][1])) == hfull(expected))
for bm in BUILDS:
    say(f'   {bm}: BUILD_TYPE==Full: {exact(bm, "BUILD_TYPE", "Full")}; ARCH==armv7l: {exact(bm, "ARCH", "armv7l")}; '
        f'EXTRA_BUILD_PARAMETER==--threads 32: {exact(bm, "EXTRA_BUILD_PARAMETER", "--threads 32")}')
say(f'   {BUILDS[0]}: BUILD_CONF==recon21 value: {exact(BUILDS[0], "BUILD_CONF", EXACT_BUILD_CONF)}')

say(f'== E history /history/{CONFIG}: page back until start < {WIN_FROM} (max {MAX_PAGES} pages)')
st, t, url = get_follow(f'{BM}/history/{CONFIG}')
say(f'  page 1: status {st}, {" ".join(re.findall(r"Showing[^<]{0,40}", t)[:1])!r}')
allrows, pages, stop = rows_of(t), 1, 'max_pages'
while pages < MAX_PAGES:
    if allrows and allrows[-1][1] and allrows[-1][1] < WIN_FROM: stop = 'reached_window_start'; break
    if over_time(): stop = 'time_limit'; break
    h = next_href(t)
    if not h: stop = 'no_next_link'; break
    st, t, url = get_follow(urllib.parse.urljoin(url, h))
    rs = rows_of(t)
    if not rs: stop = f'empty_page(status {st})'; break
    allrows += rs; pages += 1
    if pages % 25 == 0: say(f'  ... page {pages}, oldest start so far {allrows[-1][1]}')
    time.sleep(0.3)
seen, rows = set(), []
for r in allrows:
    if r[0] not in seen: seen.add(r[0]); rows.append(r)
oldest = rows[-1][1] if rows else ''
say(f'  stop reason {stop}; pages {pages}; unique builds {len(rows)} (dups {len(allrows) - len(rows)}); range {oldest} ~ {rows[0][1] if rows else ""}')
win = [r for r in rows if r[1] and WIN_FROM <= r[1] < WIN_TO]
say(f'  builds starting in window: {len(win)}')
found, near = [], []
for bid, begin in win[:MAX_DETAIL]:
    if over_time(): say('  time limit reached while reading detail pages'); break
    st, d, _ = get(f'{BM}/build/{bid}', PLAIN)
    hub = HUBLINK.findall(d)
    if TARGET_HUB in hub: found.append((bid, begin))
    if any(37432120 <= int(x) <= 37432160 for x in hub): near.append((bid, begin, hub[:2]))
    time.sleep(0.2)
say(f'  detail pages read: {min(len(win), MAX_DETAIL)}')
for n in near: say(f'   near-number build: {n[0]} start {n[1]} hub {n[2]}')
others = [f for f in found if f[1] != KNOWN_START]
if others:
    concl = 'FOUND another build with Hub Link 37432138 -> supports "rerun keeps the number"'
elif oldest and oldest < WIN_FROM and stop == 'reached_window_start':
    concl = 'window retained, no other build with 37432138 -> supports "submit-side queueing"'
else:
    concl = 'window not fully retained/reached -> "cleaned or not reached"; cannot distinguish'
say(f'  builds with Hub Link {TARGET_HUB}: {found}')
say(f'  CONCLUSION E: {concl}')
say('== recon23 end', time.strftime('%F %T'), f'elapsed {int(time.time() - T0)}s')
