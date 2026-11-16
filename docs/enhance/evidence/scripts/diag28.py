# diag28: (I) why build 19091860's report rows do not all appear in its PACKAGE_LIST (A: missing_base_package),
# (L) what `lookup --hub-id 37491096` actually returned in B1 (child_error was null).
# Uses the tool's own parsers from run/src. Read-only toward Cosmos (anonymous GET of one variable page; lookup is a
# read-only command). lookup writes only into the existing B1 verification folder. Prints paths/CLs, never credentials.
import json, os, re, subprocess, sys, time, urllib.error, urllib.request
from pathlib import Path
ROOT = Path('/home1/chengkai/vd-cosmos')
RUNSRC = ROOT / 'run/src'
sys.path.insert(0, str(RUNSRC / 'vd-cosmos-core/src'))
from vd_cosmos_core.config import load_config
from vd_cosmos_core.report import parse_report
from vd_cosmos_core.variable_pages import parse as parse_vars
from vd_cosmos_core.build_inputs import package_key
PAGES = ROOT / 'recon2/pages'
BUILD = '19091860'
B1DIR = ROOT / 'run/verification/b3a11b1-62f2e4cf30d24533ad6f7ef96508c202'
LISTS = ['PACKAGE_LIST', 'PACKAGE_LIST_armv7l', 'PACKAGE_LIST_x86_64', 'S_PACKAGE_LIST', 'PKGINFO_LIST_x86_64',
         'SHELVE_LIST', 'SHELVE_LIST_armv7l', 'SHELVE_LIST_x86_64', 'DELETE_PACKAGE_LIST_x86_64']
RED = re.compile(r'(;jsessionid=|ticket[=:]\s*|passw\w*[=:]\s*|token[=:]\s*)[^\s"&;]+', re.I)
def say(*a): print(*a, flush=True)
def red(s): return RED.sub(lambda m: m.group(1) + '<redacted>', s)

say('== diag28 start', time.strftime('%F %T'), 'python', sys.version.split()[0])
say('   run/src HEAD', subprocess.run(['git', '-C', str(RUNSRC), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip())
cfg = load_config(str(ROOT / 'config.json'))
cosmos = cfg.raw['cosmos']; markers = cosmos['branch_markers']
say('   branch_markers', markers)

say('== I1 report input rows (saved pages of', BUILD, ')')
rows = {}
for arch, name in (('armv7l', 'report_armv7l.html'), ('x86_64', 'report_x86_64.html')):
    html = (PAGES / name).read_text(encoding='utf-8', errors='replace')
    r = parse_report(html, arch, cosmos, stable=True)
    rows[arch] = r['input_rows']
    say(f'   {arch}: headers arch={r["headers"].get("arch")}; input rows {len(r["input_rows"])}; shelve rows {sum(1 for x in r["input_rows"] if x["shelve"])}')

say('== I2 variable page lists (Value column, tool parser)')
url = cosmos['variables_url_template'].format(build_id=BUILD)
say('   variable page', url)
op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
with op.open(urllib.request.Request(url, headers={'User-Agent': 'vd-cosmos-diag'}), timeout=120) as resp:
    data = resp.read(30 * 1024 * 1024)
vals = {k: v['value'] for k, v in parse_vars(data, set(LISTS)).items()}
LINE = re.compile(r'(//\S+?)@=?([0-9]+)$')
keys = {}
for name in LISTS:
    if name not in vals: say(f'   {name}: not listed'); continue
    lines = [l.strip() for l in vals[name].splitlines() if l.strip()]
    ks, unparsed = {}, 0
    for l in lines:
        m = LINE.fullmatch(l)
        try:
            k = package_key(m.group(1), markers) if m else package_key(l, markers)
            ks[k] = (m.group(1), m.group(2)) if m else (l, None)
        except Exception:
            unparsed += 1
    keys[name] = ks
    first = re.sub(r'[0-9]', '9', lines[0])[:110] if lines else ''
    say(f'   {name}: lines {len(lines)}; keyed {len(ks)}; unparsed {unparsed}; first line shape {first!r}')

say('== I3 report rows vs PACKAGE_LIST, per arch')
base = keys.get('PACKAGE_LIST', {})
for arch, rs in rows.items():
    miss = [x for x in rs if package_key(x['path'], markers) not in base]
    differ = [x for x in rs if not x['shelve'] and package_key(x['path'], markers) in base
              and (base[package_key(x['path'], markers)][0], base[package_key(x['path'], markers)][1]) != (x['path'], str(x['cl']))]
    say(f'   {arch}: rows {len(rs)}; missing from PACKAGE_LIST {len(miss)} (shelve {sum(1 for x in miss if x["shelve"])}); non-shelve path/CL differs {len(differ)}')
    for x in miss[:15]:
        k = package_key(x['path'], markers)
        where = [n for n in keys if n != 'PACKAGE_LIST' and k in keys[n]]
        same_tail = [kk for kk in base if kk.rsplit('/', 1)[-1] == k.rsplit('/', 1)[-1]][:2]
        say(f'      MISSING {x["path"]} @{x["cl"]} shelve={x["shelve"]} | in other lists: {where} | same last component in PACKAGE_LIST: {same_tail}')
    for x in differ[:5]:
        b = base[package_key(x['path'], markers)]
        say(f'      DIFFERS report {x["path"]}@{x["cl"]} vs list {b[0]}@{b[1]}')
allrep = {package_key(x['path'], markers) for rs in rows.values() for x in rs}
say(f'   PACKAGE_LIST keys not in any report: {len(set(base) - allrep)}')

say('== L lookup --hub-id 37491096 (same config and folder as the failed B1 run)')
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH='', TMPDIR=str(B1DIR / 'tmp'), XDG_CACHE_HOME=str(B1DIR / 'cache'),
           VD_COSMOS_TEST_TMPDIR=str(B1DIR / 'tmp'))
t0 = time.time()
try:
    pr = subprocess.run([sys.executable, '-B', str(RUNSRC / 'vd-cosmos-submit/scripts/run.py'), 'lookup', '--hub-id', '37491096',
                         '--config', str(B1DIR / 'config.json'), '--backend', 'real'], cwd=B1DIR, env=env, capture_output=True, timeout=2400)
    say(f'   exit {pr.returncode}; {int(time.time() - t0)}s; stdout {len(pr.stdout)} bytes; stderr {len(pr.stderr)} bytes')
    out = pr.stdout.decode('utf-8', 'replace')
    try:
        say('   stdout JSON:'); say(red(json.dumps(json.loads(out), ensure_ascii=False, indent=1))[:8000])
    except ValueError:
        say('   stdout (not JSON):', red(out[:3000]))
    err = pr.stderr.decode('utf-8', 'replace').splitlines()
    if err: say('   stderr (last 30 lines):'); [say('   | ' + red(l)[:300]) for l in err[-30:]]
except subprocess.TimeoutExpired:
    say('   TIMEOUT after 2400s')
say('== diag28 end', time.strftime('%F %T'))
