# diag29: run the tool's own detail-page parser (bm_pages.detail) on known builds and show, for each failure,
# which check failed plus the page structure around it. Anonymous read-only GETs; writes no files; no p4.
import re, sys, time, urllib.error, urllib.request
from pathlib import Path
ROOT = Path('/home1/chengkai/vd-cosmos')
sys.path.insert(0, str(ROOT / 'run/src/vd-cosmos-core/src'))
from vd_cosmos_core.config import load_config
from vd_cosmos_core import bm_pages
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.report import Node, normalize
KNOWN = ['19270912', '19270877', '19241462', '19238877', '19206687', '19091860']
def say(*a): print(*a, flush=True)
def short(s, n=90):
    s = re.sub(r'\s+', ' ', s).strip(); s = re.sub(r'(;jsessionid=)[^/?#\s]*', r'\1<x>', s, flags=re.I)
    return s if len(s) <= n else s[:n] + '…'
cfg = load_config(str(ROOT / 'config.json')); c = cfg.raw['cosmos']
op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
def get(path):
    try:
        with op.open(urllib.request.Request('https://' + c['bm_host'] + path, headers={'User-Agent': 'vd-cosmos-diag'}), timeout=120) as r:
            return r.status, r.read(30 * 1024 * 1024)
    except urllib.error.HTTPError as e:
        return e.code, b''
say('== diag29 start', time.strftime('%F %T'), 'python', sys.version.split()[0])
say('   bm_host', c['bm_host'], '| hub_host', c.get('hub_host'), '| bm_config_id', c.get('bm_config_id'), '| bm_display_tz', c.get('bm_display_tz'))
st, page = get('/history/' + str(c.get('bm_config_id', '4362')))
recent = []
for m in re.findall(rb'/build/(\d{6,9})\b', page):
    b = m.decode()
    if b not in recent and b not in KNOWN: recent.append(b)
builds = KNOWN + recent[:8]
say('   history status', st, '; testing builds', builds)
for b in builds:
    st, data = get('/build/' + b)
    try:
        d = bm_pages.detail(data, cfg, b)
        say(f'-- {b}: OK hub={d.get("hub_id")} state={d.get("state")} config={d.get("config_id")} ended={d.get("ended")} conflict={d.get("conflict")}')
        continue
    except FlowError as e:
        say(f'-- {b}: status {st}; bytes {len(data)}; FAIL {e.reason}')
    except Exception as e:
        say(f'-- {b}: status {st}; bytes {len(data)}; CRASH {type(e).__name__}'); continue
    try:
        doc = bm_pages.document(data)
    except Exception as e:
        say(f'   document() failed: {type(e).__name__}'); continue
    heads = [n for n in doc.nodes if 'build-header' in n.attrs.get('class', '').split()]
    say(f'   build-header nodes: {len(heads)} (tags {[h.tag for h in heads][:4]})')
    for h in heads[:1]:
        titles = [normalize(n.attrs.get('title', '')) for n in h.descendants({'a', 'span', 'div', 'i', 'img', 'b'}) if n.attrs.get('title')]
        say(f'   titles in header: {[short(t, 50) for t in titles][:10]}')
        toks = []
        def walk(n):
            if n.tag == 'a':
                href = n.attrs.get('href', ''); toks.append('A[' + short(re.sub(r'^https?://', '', href).split('?')[0], 60) + '|' + short(n.text(), 25) + ']'); return
            for ch in n.children:
                if isinstance(ch, Node): walk(ch)
                elif ch.strip(): toks.append('T[' + short(ch, 40) + ']')
            if n.tag in {'br', 'div', 'p', 'li'}: toks.append('NL')
        walk(h)
        idx = [i for i, t in enumerate(toks) if 'Hub' in t]
        say(f'   header tokens: {len(toks)}; tokens with "Hub": {len(idx)}')
        for i in idx[:3]: say('   around Hub:', toks[max(0, i - 2):i + 4])
        if not idx: say('   first tokens:', toks[:14])
    tabs = [t for t in doc.nodes if t.tag == 'table']
    say(f'   tables: {len(tabs)}')
    for t in tabs[:6]:
        rows = [n for n in t.descendants({'tr'})]
        first = None
        for r in rows[:3]:
            cs = [x for x in r.children if isinstance(x, Node) and x.tag in ('th', 'td')]
            names = [short(normalize(x.text()), 20) for x in cs]
            if any(names): first = names; break
        say(f'     table class {short(t.attrs.get("class", ""), 40)!r}: rows {len(rows)}; first row {first}')
    time.sleep(0.3)
say('== diag29 end', time.strftime('%F %T'))
