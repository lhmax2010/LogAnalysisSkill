import assert from 'node:assert/strict';
import { createHash, X509Certificate } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { createServer } from 'node:https';
import { existsSync } from 'node:fs';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { Agent, createRuntime, ORIGIN } from '../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';

const [playwright, chromium] = process.argv.slice(2);
const directory = await mkdtemp('/dev/shm/p5q-login-retry-');
const received = [];
const results = [];
let scenario;
execFileSync('openssl', ['req', '-x509', '-newkey', 'rsa:2048', '-nodes',
  '-keyout', `${directory}/key.pem`, '-out', `${directory}/cert.pem`, '-days', '1',
  '-subj', '/CN=quickbuild.tizen.org', '-addext', 'subjectAltName=DNS:quickbuild.tizen.org'],
{ stdio: 'ignore' });
const cert = await readFile(`${directory}/cert.pem`);
const key = await readFile(`${directory}/key.pem`);
const spki = createHash('sha256').update(new X509Certificate(cert).publicKey
  .export({ type: 'spki', format: 'der' })).digest('base64');
const minimal = '<!doctype html><link rel="icon" href="data:,"><title>LOCAL login retry fixture</title>';
const postPath = attempt => `${attempt === 0 ? '/signin' : '/wicket/page'}?${attempt}-1.IFormSubmitListener-content-form`;
const loginForm = attempt => `${minimal}<form method="POST" action="${postPath(attempt)}">
  <input type="password" name="password"><button>Local Sign In</button></form>`;
const server = createServer({ cert, key }, (request, response) => {
  const row = { scenario, method: request.method, path: request.url, status: 200 };
  received.push(row);
  request.resume();
  response.setHeader('Content-Type', 'text/html; charset=utf-8');
  if (request.method === 'POST') {
    const count = received.filter(item => item.scenario === scenario && item.method === 'POST').length;
    if (scenario === 'retry-success' && count === 2) {
      row.status = 302;
      response.writeHead(302, { Location: '/' }); response.end();
    } else response.end(loginForm(count));
  } else if (request.url === '/') response.end(`${minimal}<a href="/unused">Sign Out</a>`);
  else response.end(loginForm(0));
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const options = { launchArgs: ['--no-proxy-server',
  `--host-resolver-rules=MAP quickbuild.tizen.org 127.0.0.1:${server.address().port}, EXCLUDE 127.0.0.1, MAP * ~NOTFOUND`,
  `--ignore-certificate-errors-spki-list=${spki}`] };

async function run(name) {
  scenario = name;
  const start = received.length;
  const runtime = await createRuntime(playwright, chromium, options);
  const agent = new Agent(runtime);
  let login;
  let result;
  try {
    login = agent.command({ command: 'login', login_timeout_seconds: 30, projects: [] });
    await runtime.page.locator('input[type=password]').waitFor();
    assert.equal(received.slice(start).filter(row => row.method === 'POST').length, 0,
      'agent sent POST before synthetic human click');
    const attempts = name === 'retry-success' ? 2 : 5;
    for (let i = 0; i < attempts; i++) {
      assert.equal(await runtime.page.locator('form').getAttribute('action'), postPath(i));
      const response = runtime.page.waitForResponse(item => item.request().method() === 'POST'
        && item.url() === ORIGIN + postPath(i));
      // Only the fixture simulates the human. Agent.login remains read-only.
      await runtime.page.locator('input[type=password]').fill('local-synthetic-value');
      await runtime.page.getByRole('button', { name: 'Local Sign In' }).click();
      assert.equal((await response).status(), name === 'retry-success' && i === 1 ? 302 : 200);
      assert.equal(runtime.policy.loginPostCount, i + 1);
      if (i === 0) assert.equal(agent.state, 'new', 'HTTP200 must not count as authentication');
    }
    if (name === 'retry-success') {
      assert.deepEqual(await login, { ok: true });
      assert.equal(new URL(runtime.page.url()).pathname, '/');
      assert.equal(await runtime.page.locator('input[type=password]').count(), 0);
      assert.equal(await runtime.page.getByRole('link', { name: 'Sign Out', exact: true }).count(), 1);
      const afterLogin = received.length;
      const outcome = await runtime.page.evaluate(async path => {
        try { await fetch(path, { method: 'POST' }); return 'unexpected-success'; }
        catch { return 'blocked'; }
      }, postPath(2));
      assert.equal(outcome, 'blocked');
      assert.equal(received.length, afterLogin, 'post-success login request reached server');
      result = { login: 'three-conditions-passed', postStatuses: [200, 302], afterSuccessReceived: 0 };
    } else {
      assert.equal(await runtime.page.locator('form').getAttribute('action'), postPath(5));
      const failed = runtime.page.waitForEvent('requestfailed', {
        predicate: request => request.method() === 'POST' && request.url() === ORIGIN + postPath(5),
      });
      await runtime.page.locator('input[type=password]').fill('local-synthetic-value');
      await runtime.page.getByRole('button', { name: 'Local Sign In' }).click({ noWaitAfter: true });
      assert.match((await failed).failure().errorText, /ERR_BLOCKED_BY_CLIENT/);
      assert.equal(received.slice(start).filter(row => row.method === 'POST').length, 5);
      result = { attempted: 6, serverReceived: 5, sixthDenied: true, postStatuses: [200, 200, 200, 200, 200] };
    }
    assert.equal(runtime.failure, null);
    assert.equal(runtime.policy.loginPostsClosed, true);
    assert.equal(runtime.policy.released, false);
    assert.equal(runtime.trace.some(row => ['WORKER_BLOCKED', 'NEW_PAGE'].includes(row.action)), false);
  } finally {
    await runtime.close();
    if (login) await login;
  }
  assert.equal(runtime.browser.isConnected(), false);
  assert.equal(existsSync(runtime.profile), false);
  const row = { scenario, ok: true, ...result, received: received.slice(start),
    trace: runtime.trace, browserClosed: true, temporaryDirectoryRemoved: true };
  results.push(row);
  console.log(JSON.stringify(row));
}

try {
  await run('retry-success');
  await run('five-failure-limit');
} finally {
  server.closeAllConnections(); await new Promise(resolve => server.close(resolve));
  await rm(directory, { recursive: true, force: true });
  console.log(JSON.stringify({ summary: results.length, passed: results.length, expected: 2,
    network: 'loopback-only', temporaryDirectoryRemoved: !existsSync(directory) }));
}
