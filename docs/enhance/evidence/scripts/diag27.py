# diag27: why did checkpoint A get p4_incomplete_output and B1 get bm_table_unrecognized on the build machine?
# Read-only. p4: only `info` and `login -s` (login -s only reports status; it never logs in). Cosmos: anonymous GET of
# /overview/4362 and /history/4362. Writes NO files. Prints field NAMES and structure, not secret values.
import html, html.parser, json, marshal, io, os, re, subprocess, sys, time, urllib.error, urllib.request
CONFIG = '/home1/chengkai/vd-cosmos/config.json'
BM = 'https://vdcosmos-bm.sec.samsung.net'
CRED = re.compile(r'passw|pwd|token|secret|cookie|ticket|session|saml|relaystate', re.I)
def say(*a): print(*a, flush=True)
def safe(s, n=200):
    s = re.sub(r'\s+', ' ', str(s)).strip()
    s = re.sub(r'(;jsessionid=)[^/?#\s]*', r'\1<x>', s, flags=re.I)
    return (s[:n] + '…') if len(s) > n else s

say('== diag27 start', time.strftime('%F %T'), 'python', sys.version.split()[0])
raw = json.load(open(CONFIG))
p4 = raw.get('p4', {})
say('== P1 p4 config (keys present, non-secret values)')
say('   keys:', sorted(p4))
for k in ('port', 'user', 'expected_server_address', 'no_client_name', 'unknown_client_marker', 'tickets_file', 'executable', 'version', 'output_protocol', 'read_config_name'):
    v = p4.get(k, '<default>')
    say(f'   {k}: {v!r}')
say('   code0_table versions:', sorted((p4.get('code0_table') or {}).keys()) or '<default table>')
d = raw.get('data_root', '.')
data_root = os.path.normpath(os.path.join(os.path.dirname(CONFIG), d))
say('   data_root:', data_root)

say('== P2 p4 commands with the adapter environment (P4CONFIG=<nonexistent>, P4ENVIRO=/dev/null, P4TICKETS=<path>, no HOME)')
exe = p4.get('executable', 'p4')
tickets = os.path.expanduser(p4.get('tickets_file', '~/.p4tickets'))
base_env = {k: os.environ[k] for k in ('PATH', 'LANG', 'LC_ALL', 'TZ') if k in os.environ}
base_env.update(P4CONFIG='.vd-cosmos-noconfig-diag27', P4ENVIRO='/dev/null', P4TICKETS=tickets)
def run(args, env, label):
    argv = [exe, '-G', '-p', p4.get('port', ''), '-u', p4.get('user', ''), '-c', p4.get('no_client_name', 'vd-cosmos-noclient'), *args]
    try:
        pr = subprocess.run(argv, env=env, cwd=data_root, capture_output=True, timeout=60)
    except Exception as e:
        say(f'   [{label}] {args}: start failed {type(e).__name__}'); return
    say(f'   [{label}] {args}: exit {pr.returncode}; stdout {len(pr.stdout)} bytes; stderr {len(pr.stderr)} bytes')
    if pr.stderr: say(f'      stderr: {safe(pr.stderr.decode("utf-8", "replace"))}')
    st, recs = io.BytesIO(pr.stdout), []
    try:
        while st.tell() < len(pr.stdout): recs.append(marshal.load(st))
        say(f'      marshal records: {len(recs)} (parsed fully)')
    except Exception as e:
        say(f'      marshal records: {len(recs)} then {type(e).__name__}; stdout starts with {pr.stdout[:12]!r}')
    for r in recs:
        if not isinstance(r, dict): say(f'      non-dict record {type(r).__name__}'); continue
        r = {(k.decode() if isinstance(k, bytes) else k): (v.decode('utf-8', 'replace') if isinstance(v, bytes) else v) for k, v in r.items()}
        say(f'      keys: {sorted(r)}')
        for k in ('code', 'severity', 'generic', 'code0', 'fmt0'):
            if k in r: say(f'      {k}: {safe(r[k], 160)}')
        for k in ('userName', 'clientName', 'serverAddress', 'serverVersion', 'TicketExpiration', 'User', 'AuthedBy'):
            if k in r: say(f'      {k}: {safe(r[k], 120)}')
        if 'clientRoot' in r: say('      clientRoot: <present>')
for args in (['info'], ['login', '-s']):
    run(args, base_env, 'adapter env')
with_home = dict(base_env, HOME=os.environ.get('HOME', ''))
for args in (['info'], ['login', '-s']):
    run(args, with_home, 'adapter env + HOME')

say('== T table structure of /overview/4362 and /history/4362 (anonymous, page 1)')
class NoRedir(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None
OP = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedir())
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
class HP(html.parser.HTMLParser):
    def __init__(s):
        super().__init__(convert_charrefs=True); s.root = {'tag': '#root', 'attrs': {}, 'kids': [], 'parent': None}; s.cur = [s.root]
    def handle_starttag(s, tag, attrs):
        n = {'tag': tag, 'attrs': dict((k, v or '') for k, v in attrs), 'kids': [], 'parent': s.cur[-1]}
        s.cur[-1]['kids'].append(n)
        if tag not in VOID: s.cur.append(n)
    def handle_endtag(s, tag):
        for i in range(len(s.cur) - 1, 0, -1):
            if s.cur[i]['tag'] == tag: del s.cur[i:]; break
    def handle_data(s, d): s.cur[-1]['kids'].append(d)
def text(n): return n if isinstance(n, str) else ''.join(text(k) for k in n['kids'])
def walk(n):
    if isinstance(n, str): return
    yield n
    for k in n['kids']: yield from walk(k)
def owner_table(n):
    p = n['parent']
    while p and p['tag'] != 'table': p = p['parent']
    return p
def depth(n):
    k, p = 0, n['parent']
    while p:
        if p['tag'] == 'table': k += 1
        p = p['parent']
    return k
for path in ('/overview/4362', '/history/4362'):
    try:
        with OP.open(urllib.request.Request(BM + path, headers={'User-Agent': 'vd-cosmos-recon'}), timeout=120) as r:
            st, page = r.status, r.read(30 * 1024 * 1024).decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        st, page = e.code, ''
    say(f'-- {path}: status {st}; bytes {len(page)}')
    if not page: continue
    p = HP(); p.feed(page)
    tables = [n for n in walk(p.root) if n['tag'] == 'table']
    shows = len(re.findall(r'Showing\s+\d+\s+to\s+\d+\s+of\s+\d+', html.unescape(re.sub(r'<[^>]*>', ' ', page))))
    say(f'   tables {len(tables)}; "Showing x to y of N" matches {shows}')
    for i, t in enumerate(tables):
        rows = [n for n in walk(t) if n['tag'] == 'tr' and owner_table(n) is t]
        hdr = None
        for r in rows:
            cs = [c for c in r['kids'] if isinstance(c, dict) and c['tag'] in ('td', 'th')]
            names = [safe(html.unescape(text(c)), 30) for c in cs]
            if any(x in names for x in ('Hub ID', 'Version', 'Begin Date', 'Requester', 'Id')):
                hdr = (names, [c['tag'] for c in cs]); break
        if hdr or i < 6:
            say(f'   table {i}: depth {depth(t)}; own rows {len(rows)}; class {safe(t["attrs"].get("class", ""), 40)!r}')
            if hdr: say(f'      header cells ({len(hdr[0])}): {hdr[0]}'); say(f'      header tags: {hdr[1]}')
say('== diag27 end', time.strftime('%F %T'))
