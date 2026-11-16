# diag30b: capture REAL Cosmos pages (5 detail, overview, history p1+p2), ANONYMIZE them on this machine,
# check them with the tool's own credential check, and write ONE markdown file for transfer.
# Also lists config values that are still placeholders. Anonymous read-only GETs; no p4, no login, no browser.
# Writes only run/recon-b3/pages30.md.
import hashlib, html as htmlmod, re, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path
ROOT = Path('/home1/chengkai/vd-cosmos')
sys.path.insert(0, str(ROOT / 'run/src/vd-cosmos-core/src'))
from vd_cosmos_core.config import load_config
from vd_cosmos_core.export import check_content
OUTMD = ROOT / 'run/recon-b3/pages30.md'
KEEP_HOSTS = {'vdcosmos-bm.sec.samsung.net', 'vdcosmos-hub.sec.samsung.net'}
KEEP_USERS = {'hao.lin'}
lines_out = []
def say(*a):
    s = ' '.join(str(x) for x in a); print(s, flush=True); lines_out.append(s)
cfg = load_config(str(ROOT / 'config.json')); c = cfg.raw['cosmos']
say('== diag30b start', time.strftime('%F %T'), 'python', sys.version.split()[0])

say('== C config values that are still placeholders (key path = value)')
def scan(node, path):
    if isinstance(node, dict):
        for k, v in node.items(): scan(v, path + [str(k)])
    elif isinstance(node, list):
        for i, v in enumerate(node): scan(v, path + [str(i)])
    elif isinstance(node, str) and re.search(r'example\.invalid|configure-|placeholder|CHANGE_ME', node, re.I):
        say('   ' + '.'.join(path) + ' = ' + repr(node))
scan(cfg.raw, [])

class NoRedir(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None
OP = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedir(), urllib.request.HTTPCookieProcessor())
def get(path):
    try:
        with OP.open(urllib.request.Request('https://vdcosmos-bm.sec.samsung.net' + path, headers={'User-Agent': 'vd-cosmos-diag'}), timeout=120) as r:
            return r.status, r.read(30 * 1024 * 1024).decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, ''

users = {}
def user_alias(name):
    if name in KEEP_USERS: return name
    return users.setdefault(name, 'user%d' % (len(users) + 1))
HOST = re.compile(r'(?i)\b([a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:samsung\.net|samsung\.com|sec\.samsung\.net|svc|local|corp))\b')
IP = re.compile(r'\b\d{1,3}(?:\.\d{1,3}){3}\b')
EMAIL = re.compile(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)+')
USERINFO = re.compile(r'(?i)\b([a-z][a-z0-9+.-]*://)[^/\s"\'<>@]+@')
JSESS = re.compile(r'(?i);jsessionid=[^/?#\s"\'<>]*')
NAME = re.compile(r'(?<![\w./@-])([a-z][a-z0-9_-]*\.[a-z][a-z0-9_-]*)(?![\w./@-])')
BRACKET = re.compile(r'\[([a-z][a-z0-9_-]*\.[a-z0-9_.-]+)\]')
FILEEXT = re.compile(r'\.(html?|ks|conf|xml|json|txt|log|rpm|spec|tar|gz|py|sh|js|css|png|svg)$', re.I)
def host_sub(m):
    h = m.group(1).lower()
    return h if h in KEEP_HOSTS else 'internal.example'
def anonymize(t):
    stats = {}
    t = t.replace('\r\n', '\n').replace('\r', '\n')
    def count(k, n): stats[k] = stats.get(k, 0) + n
    t, n = re.subn(r'(?is)(<script\b[^>]*>).*?(</script>)', r'\1/* removed */\2', t); count('script', n)
    t, n = re.subn(r'(?is)(<style\b[^>]*>).*?(</style>)', r'\1/* removed */\2', t); count('style', n)
    t, n = USERINFO.subn(r'\1', t); count('userinfo_removed', n)
    t, n = JSESS.subn('', t); count('jsessionid_removed', n)
    t, n = re.subn(r'(?i)wicket\s*:\s*interface\s*=', 'wicket%3Ainterface=', t); count('wicket_interface_encoded', n)
    t, n = re.subn(r'(?is)<input\b(?=[^>]*\btype\s*=\s*["\']?hidden)[^>]*>', '<!-- hidden input removed -->', t); count('hidden_input_removed', n)
    t, n = re.subn(r'(?i)(set-)?cookie\s*:', 'cookie-header-removed', t); count('cookie_text', n)
    t, n = EMAIL.subn('user@example.com', t); count('email', n)
    for name in set(BRACKET.findall(t)): user_alias(name)
    t, n = BRACKET.subn(lambda m: '[' + user_alias(m.group(1)) + ']', t); count('bracket_user', n)
    t, n = HOST.subn(host_sub, t); count('host', n)
    t, n = IP.subn('10.0.0.1', t); count('ip', n)
    # bare user names in text nodes only (not inside tags/attributes), skipping file names
    parts = re.split(r'(<[^>]*>)', t); k = 0
    for i in range(0, len(parts), 2):
        def rep(m):
            nonlocal k
            w = m.group(1)
            if FILEEXT.search(w) or w in KEEP_HOSTS or w.endswith('.example') or w == 'user@example.com': return w
            if w in users or re.fullmatch(r'[a-z]+[0-9]*\.[a-z]+[0-9]*', w):
                k += 1; return user_alias(w)
            return w
        parts[i] = NAME.sub(rep, parts[i])
    count('bare_user', k)
    return ''.join(parts), stats

pages = []
def take(name, path):
    st, t = get(path)
    if not t:
        say(f'   {name}: status {st}; EMPTY, skipped'); return ''
    a, stats = anonymize(t)
    try:
        v = check_content(a.encode('utf-8'), cfg)
    except Exception as e:
        say(f'   {name}: status {st}; credential check could not run ({type(e).__name__}); skipped'); return t
    if not v['allowed']:
        say(f'   {name}: status {st}; BLOCKED by credential check {[(h["pattern_index"], h["line"]) for h in v["credential_hits"]][:10]}; skipped'); return t
    if '~~~~' in a:
        say(f'   {name}: contains a fence marker; skipped'); return t
    sha = hashlib.sha256(a.encode('utf-8')).hexdigest()
    pages.append((name, a, sha))
    say(f'   {name}: status {st}; original {len(t)} chars; anonymized {len(a)} chars; sha256 {sha}; replaced {stats}')
    return t

say('== P pages (anonymized)')
h1 = take('history_4362_p1.html', '/history/4362')
nxt = None
for m in re.finditer(r'<a\b([^>]*)>(.*?)</a>', h1, re.S | re.I):
    if htmlmod.unescape(re.sub(r'<[^>]*>', '', m.group(2))).strip() in ('>', '›', 'Next'):
        hr = re.findall(r'href\s*=\s*["\']([^"\']*)', m.group(1), re.I)
        if hr: nxt = htmlmod.unescape(hr[0]); break
if nxt:
    p = urllib.parse.urlsplit(urllib.parse.urljoin('https://vdcosmos-bm.sec.samsung.net/history/4362', nxt))
    take('history_4362_p2.html', p.path + ('?' + p.query if p.query else ''))
else:
    say('   history_4362_p2.html: no next link found')
take('overview_4362.html', '/overview/4362')
running = None
for m in re.finditer(r'/build/(\d{6,9})\b', h1):
    st, d = get('/build/' + m.group(1))
    if 'Build is running' in d: running = m.group(1); break
for b in ['19270912', '19206687', '19238877', '19091860'] + ([running] if running else []):
    take(f'detail_{b}.html', '/build/' + b); time.sleep(0.3)
say('   user aliases used:', len(users), '(names not listed)')
say('== diag30b end', time.strftime('%F %T'))

md = ['# pages30 — anonymized real Cosmos pages (diag30b)', '', '## Run log', '', '~~~~text'] + lines_out + ['~~~~', '']
for name, a, sha in pages:
    md += [f'## {name}', '', f'sha256 (of the anonymized page text, UTF-8): `{sha}`', '', '~~~~html', a, '~~~~', '']
OUTMD.write_text('\n'.join(md), encoding='utf-8')
print('written', OUTMD, OUTMD.stat().st_size, 'bytes', flush=True)
