// All browser tests resolve QuickBuild exclusively to a loopback HTTPS fixture.
import assert from 'node:assert/strict';
import test from 'node:test';
import { execFileSync } from 'node:child_process';
import { createHash, X509Certificate } from 'node:crypto';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { createServer } from 'node:https';
import { dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { ROOT, PATHS, LIMIT, exactLink, capturePolicy, capture, decodeText } from './capture.mjs';
const { Policy, createRuntime } = await import(pathToFileURL(`${ROOT}/tizen-qb-verify/scripts/tizen_qb_verify/qb_browser_agent.mjs`));
const { DEFAULTS, PROJECT } = await import(pathToFileURL(`${ROOT}/docs/clang-fix-campaign/spikes/p5q_c5_tools.mjs`));
const ORIGIN = 'https://quickbuild.tizen.org';
const REPORT = '/download/1204736/html/GBS%20Reports%40%5E%40standard-armv7l%3Aaarch64%3Ax86_64/index.html';
const LOG = REPORT.replace('index.html', 'logfiles/standard/armv7l/zlib.txt');
const HERE = dirname(fileURLToPath(import.meta.url));

test('exact URLs and UTF-8 are fail-closed', () => {
  assert.equal(exactLink(REPORT, ORIGIN), ORIGIN + REPORT);
  for (const value of ['https://else.invalid' + REPORT, REPORT + '?x=1', REPORT + '#x',
    REPORT.replace('1204736', '1204735'), '../x', REPORT + '/%2f', REPORT + '/%252e',
    'http://quickbuild.tizen.org' + REPORT, 'https://user@quickbuild.tizen.org' + REPORT]) {
    assert.throws(() => exactLink(value, ORIGIN), { code: 'CAPTURE_PATH_UNSUPPORTED' });
  }
  assert.equal(decodeText(Buffer.from('error: a<T>\n')), 'error: a<T>\n');
  assert.throws(() => decodeText(Buffer.from([0xff])), { code: 'QB_TEXT_ENCODING_UNSUPPORTED' });
  assert.throws(() => decodeText(Buffer.alloc(LIMIT + 1)), { code: 'QB_TEXT_TOO_LARGE' });
});

test('capture-only policy: one main-frame GET, no permanent-denial expansion', () => {
  const policy = new Policy([1917]);
  const scope = capturePolicy(policy, () => 'root', new Map([['r', 'root'], ['sub', 'child']]));
  policy.phase = 'read'; scope.current = ORIGIN + PATHS.at(-1);
  const m = { method: 'GET', protocol: 'https:', host: 'quickbuild.tizen.org',
    path: PATHS.at(-1), query: '', resource_type: 'Document', response_status: null };
  assert.equal(policy.allow(m, 'r'), true);
  for (const change of [{ method: 'POST' }, { protocol: 'http:' }, { query: '1' },
    { response_status: 307 }, { response_status: 308 }, { resource_type: 'Fetch' },
    { path: '/build/1204736/log' }, { path: '/build/1204736/artifacts' }, { path: '/rest/run' }]) {
    assert.equal(policy.allow({ ...m, ...change }, 'r'), false);
  }
  assert.equal(policy.allow(m, 'sub'), false);
  policy.active.add('r');
  assert.equal(policy.allow({ ...m, response_status: 200 }, 'r'), true);
  policy.phase = 'idle'; assert.equal(policy.allow(m, 'r'), false);
});

function body(path, mode) {
  const id = path.includes('1204735') ? '1204735' : '1204736';
  const config = id === '1204735' || path === '/overview/1917' ? PROJECT.configuration_path
    : PROJECT.configuration_path.replace(/TRIGGER$/, 'build');
  const nav = `<a class="nav-link">Build (id:${id})</a>`;
  const head = `<title>QuickBuild - ${config}</title><link rel="icon" href="data:,">`;
  const identity = '<span>Welcome! SyntheticIdentity</span><a>Sign Out</a>';
  let content = '';
  if (path.endsWith('/overview') || path === '/overview/1917') {
    content = `<script>function onCopyClipboardLinkDomReady(){};onCopyClipboardLinkDomReady('id','${config}')</script>
      <div class="build-summary"><div class="box-head">Summary</div><table><thead><tr><th>Id</th><th>Status</th></tr></thead>
      <tbody><tr><td>${id}</td><td>Failed</td></tr></tbody></table></div>`;
    if (id === '1204735') content += `<table><tr><th>Repository-Architecture</th><th>QB Build URL</th><th>Build Result</th><th>Build Profiling</th></tr>
      <tr><td>standard-armv7l:aarch64:x86_64</td><td><a href="/build/1204736">1204736</a></td><td>FAILED</td><td></td></tr></table>`;
  } else if (path.endsWith('/variables')) {
    content = `<table><tr><td>Name</td><td>Display Name</td><td>Value</td></tr><tr><td>TRIGGER_ID</td><td></td><td>1204735</td></tr>
      <tr><td>BUILD_PKG_LIST</td><td></td><td>platform/upstream/zlib@${'a'.repeat(40)}</td></tr></table>`;
  } else if (path.endsWith('/html_report')) {
    content = `<iframe src="${mode === 'foreign' ? 'https://outside.invalid' : ''}${REPORT}"></iframe>`;
  } else if (path === REPORT) {
    content = `<table><tr><th>Package Name</th><th>Package Path</th><th>Build Status</th></tr>
      <tr><td>zlib</td><td>zlib-1</td><td><a class="failed" href="logfiles/standard/armv7l/zlib.txt">failed</a></td></tr></table>`;
  }
  return `<!doctype html><html><head>${head}</head><body>${identity}${nav}${content}</body></html>`;
}

test('real guarded Chromium capture, foreign iframe, 307 and attachment stops', { timeout: 180000 }, async t => {
  const temp = await mkdtemp('/tmp/restore08-capture-');
  execFileSync('openssl', ['req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-keyout', `${temp}/key`,
    '-out', `${temp}/cert`, '-days', '1', '-subj', '/CN=quickbuild.tizen.org',
    '-addext', 'subjectAltName=DNS:quickbuild.tizen.org'], { stdio: 'ignore' });
  const cert = await readFile(`${temp}/cert`), key = await readFile(`${temp}/key`);
  const spki = createHash('sha256').update(new X509Certificate(cert).publicKey.export({ type: 'spki', format: 'der' })).digest('base64');
  let mode = '', received = [];
  const server = createServer({ cert, key }, (req, res) => {
    received.push({ method: req.method, path: req.url });
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    if (req.url === '/signin') {
      res.end('<form action="/signin?0-1.IFormSubmitListener-content-form" method="POST"><input type="password"><button>Login</button></form>');
    } else if (req.method === 'POST') {
      res.writeHead(302, { Location: '/' }); res.end();
    } else if (req.url === '/') res.end('<a>Sign Out</a>');
    else if (req.url === LOG) {
      res.setHeader('Content-Type', 'text/plain; charset=utf-8');
      if (mode === 'attachment') res.setHeader('Content-Disposition', 'attachment; filename="zlib.txt"');
      res.end('SyntheticIdentity error: vector<T>\ntoken="SYNTHETIC_SECRET"\n');
    } else if (mode === '307' && req.url === PATHS[1]) {
      res.writeHead(307, { Location: '/forbidden' }); res.end();
    } else res.end(body(req.url, mode));
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const args = ['--no-proxy-server', `--host-resolver-rules=MAP quickbuild.tizen.org 127.0.0.1:${server.address().port}`,
    `--ignore-certificate-errors-spki-list=${spki}`];
  try {
    for (const item of ['', 'foreign', '307', 'attachment']) await t.test(item || 'normal', async () => {
      mode = item; received = [];
      let rt;
      let resolveRuntime;
      const available = new Promise(resolve => { resolveRuntime = resolve; });
      const output = `${temp}/${item || 'normal'}`;
      const pending = capture(output, async () => {
        rt = await createRuntime(DEFAULTS.playwright, DEFAULTS.chromium, { launchArgs: args });
        resolveRuntime(); return rt;
      });
      await available;
      try {
        // Test fixture only; production capture never fills or clicks the login form.
        await rt.page.locator('input[type=password]').fill('synthetic-password');
        await rt.page.getByRole('button', { name: 'Login' }).click();
        const result = await pending;
        assert.equal(result.profile_removed, true);
        assert.equal(result.status, item ? 'STOPPED' : 'CAPTURED');
        assert.equal(result.failure, item === 'foreign' ? 'CAPTURE_PATH_UNSUPPORTED'
          : item === '307' ? 'CAPTURE_REDIRECT_UNSUPPORTED'
            : item === 'attachment' ? 'QB_DOWNLOAD_UNSUPPORTED' : null);
        assert.ok(!received.some(row => row.path === '/forbidden'));
        if (!item) {
          assert.equal(result.pages.length, 8);
          assert.equal(received.filter(row => row.path === REPORT).length, 1, 'iframe auto-load denied');
          assert.equal(received.filter(row => row.path === LOG).length, 1);
          const log = await readFile(`${output}/08.response.txt`, 'utf8');
          assert.ok(log.includes('vector<T>'));
          assert.ok(!log.includes('SyntheticIdentity') && !log.includes('SYNTHETIC_SECRET'));
        }
        const recorded = await readFile(`${output}/run.json`, 'utf8');
        assert.ok(!recorded.includes('SyntheticIdentity') && !recorded.includes('synthetic-password'));
      } finally { await rt.close(); await pending; }
    });
  } finally { await new Promise(resolve => server.close(resolve)); await rm(temp, { recursive: true, force: true }); }
});
