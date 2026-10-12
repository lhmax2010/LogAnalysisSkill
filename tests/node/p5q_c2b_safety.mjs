import assert from 'node:assert/strict';
import { createHash, X509Certificate } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { createServer } from 'node:https';
import { createServer as createPlainServer } from 'node:http';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { Agent, createRuntime, ORIGIN } from '../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';

// Synthetic HTTPS only. Production launchers never receive these overrides.
const [playwright, chromium] = process.argv.slice(2);
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const directory = await mkdtemp('/dev/shm/p5q-c2b-safety-');
const received = [];
const upgrades = [];
const results = [];
const synthetic = { cookie: 'c2b-cookie-private', auth: 'c2b-auth-private', password: 'c2b-password-private', user: 'c2b-user-private' };
let credentialFacts = { cookie: false, authorization: false, password: false };
let group = 'setup';
execFileSync('openssl', ['req', '-x509', '-newkey', 'rsa:2048', '-nodes',
  '-keyout', `${directory}/key.pem`, '-out', `${directory}/cert.pem`, '-days', '1',
  '-subj', '/CN=quickbuild.tizen.org', '-addext', 'subjectAltName=DNS:quickbuild.tizen.org,DNS:download.tizen.org'], { stdio: 'ignore' });
const cert = await readFile(`${directory}/cert.pem`);
const key = await readFile(`${directory}/key.pem`);
const spki = createHash('sha256').update(new X509Certificate(cert).publicKey.export({ type: 'spki', format: 'der' })).digest('base64');
const redirectMap = new Map([
  ['/build/307', [307, '/build/999']], ['/build/308', [308, '/build/999']],
  ['/build/302', [302, '/build/999']], ['/build/301', [302, '/rest/trigger']],
  ['/build/303', [302, '/wicket/page?1-1.ILinkListener-content-buildHead-promote']],
  ['/build/304', [302, 'https://download.tizen.org/build/999']],
  ['/signin?7-1.IFormSubmitListener-first', [307, '/signin?7-1.IFormSubmitListener-second']],
]);
const minimal = '<!doctype html><link rel="icon" href="data:,"><title>LOCAL C2b safety fixture</title>';
const reply = async (request, response) => {
  const url = request.url;
  received.push({ group, method: request.method, path: url, host: request.headers.host });
  credentialFacts.cookie ||= (request.headers.cookie ?? '').includes(synthetic.cookie);
  credentialFacts.authorization ||= (request.headers.authorization ?? '').includes(synthetic.auth);
  let body = '';
  for await (const data of request) body += data;
  credentialFacts.password ||= body.includes(synthetic.password);
  if (redirectMap.has(url)) {
    const [status, location] = redirectMap.get(url);
    response.writeHead(status, { Location: location }); response.end(); return;
  }
  response.setHeader('Content-Type', 'text/html; charset=utf-8');
  if (url === '/signin' && request.method === 'GET') {
    response.setHeader('Set-Cookie', `JSESSIONID_8810=${synthetic.cookie}; Path=/; Secure; HttpOnly`);
    response.end(`${minimal}<form method="POST" action="/signin?1-1.IFormSubmitListener-form">
      <input name="password" type="password"><button>Local Sign In</button></form>`);
  } else if (url === '/signin?1-1.IFormSubmitListener-form') {
    response.writeHead(302, { Location: '/overview/0' }); response.end();
  } else if (url === '/overview/0') {
    response.end(`${minimal}<a href="/unused">Sign Out</a>`);
  } else {
    response.end(`${minimal}<a class="nav-link">Build (id:1)</a>
      <span>Welcome! ${synthetic.user}</span>
      <input type="hidden" name="token" value="${synthetic.cookie}">
      <div class="build-summary"><div class="box-head">Summary</div><table>
      <thead><tr><th>Id</th><th>Triggered By</th></tr></thead>
      <tbody><tr><td>1</td><td>${synthetic.user}</td></tr></tbody></table></div>`);
  }
};
const server = createServer({ cert, key }, (request, response) => { void reply(request, response); });
const plain = createPlainServer((request, response) => {
  received.push({ group, method: request.method, path: request.url }); request.resume(); response.end();
});
for (const [instance, scheme] of [[server, 'wss'], [plain, 'ws']]) {
  instance.on('upgrade', (request, socket) => {
    upgrades.push({ group, scheme, path: request.url }); socket.destroy();
  });
  await new Promise(resolve => instance.listen(0, '127.0.0.1', resolve));
}
const overrides = {
  launchArgs: ['--no-proxy-server',
    `--host-resolver-rules=MAP quickbuild.tizen.org 127.0.0.1:${server.address().port}, MAP download.tizen.org 127.0.0.1:${server.address().port}, EXCLUDE 127.0.0.1, MAP * ~NOTFOUND`,
    `--ignore-certificate-errors-spki-list=${spki}`],
};

async function run(name, action) {
  group = name;
  const start = received.length;
  const wsStart = upgrades.length;
  const runtime = await createRuntime(playwright, chromium, overrides);
  let details;
  let ok = false;
  try { details = await action(runtime); ok = true; }
  catch (error) {
    details = { error: 'LOCAL_SAFETY_ASSERTION_FAILED', assertion: error instanceof assert.AssertionError ? error.message.split('\n')[0] : 'runtime failure' };
  } finally {
    await runtime.close();
    const row = { group: name, ok, requests: received.slice(start), handshakes: upgrades.slice(wsStart), trace: runtime.trace, details };
    results.push(row);
    const output = JSON.stringify(row);
    if (Object.values(synthetic).some(value => output.includes(value))) throw new Error('SYNTHETIC_CREDENTIAL_LEAK');
    console.log(output);
  }
  return ok;
}

try {
  const worker = await run('worker-websocket', async runtime => {
    runtime.policy.phase = 'read';
    await runtime.page.goto(ORIGIN + '/build/1');
    const start = received.length;
    await runtime.page.evaluate(({ plainPort }) => {
      globalThis.localWorkers = [];
      for (const type of ['Worker', 'SharedWorker']) {
        const script = URL.createObjectURL(new Blob([
          `fetch('/rest/trigger'); fetch('/build/999');`,
        ], { type: 'text/javascript' }));
        globalThis.localWorkers.push(new window[type](script));
      }
      globalThis.localSockets = [new WebSocket('wss://quickbuild.tizen.org/socket'), new WebSocket(`ws://127.0.0.1:${plainPort}/socket`)];
    }, { plainPort: plain.address().port });
    await wait(1000);
    assert.equal(received.length, start, 'worker attack request reached server');
    assert.equal(upgrades.length, 0, 'WebSocket handshake reached server');
    const workers = runtime.trace.filter(row => row.action === 'WORKER_BLOCKED');
    assert.ok(workers.some(row => row.type === 'worker' && row.paused), 'Worker not paused');
    assert.ok(workers.some(row => row.type === 'shared_worker' && row.paused), 'SharedWorker not paused');
    assert.ok(runtime.trace.filter(row => row.action === 'WEBSOCKET_DENIED').length >= 2, 'both WebSocket attempts must reach the context guard');
    assert.equal(runtime.failure, null);
    return { attackHTTP: 0, websocketHandshakes: 0, workers };
  });
  if (!worker) process.exitCode = 1;
  if (worker) {
    const redirects = await run('307-308', async runtime => {
      runtime.policy.phase = 'read';
      for (const code of [307, 308]) {
        const start = received.length;
        await runtime.page.goto(`${ORIGIN}/build/${code}`).catch(() => {});
        await wait(200);
        assert.deepEqual(received.slice(start).map(row => row.path), [`/build/${code}`], 'redirect replay reached legal destination');
      }
      const start = received.length;
      await runtime.page.goto(ORIGIN + '/build/302');
      assert.deepEqual(received.slice(start).map(row => row.path), ['/build/302', '/build/999']);
      return { blocked: [307, 308], allowed: 302 };
    });
    if (!redirects) process.exitCode = 1;
    if (redirects) {
      const hops = await run('per-hop', async runtime => {
        runtime.policy.phase = 'read';
        for (const id of [301, 303, 304]) {
          const start = received.length;
          await runtime.page.goto(`${ORIGIN}/build/${id}`).catch(() => {});
          await wait(200);
          assert.deepEqual(received.slice(start).map(row => row.path), [`/build/${id}`], 'forbidden redirect hop reached server');
        }
        runtime.policy.phase = 'login';
        await runtime.page.goto(ORIGIN + '/signin');
        const start = received.length;
        await runtime.page.evaluate(() => fetch('/signin?7-1.IFormSubmitListener-first', { method: 'POST', body: 'synthetic' }).catch(() => {}));
        assert.deepEqual(received.slice(start).map(row => [row.method, row.path]), [['POST', '/signin?7-1.IFormSubmitListener-first']], '307 replay POST reached server');
        return { forbiddenSecondHops: 0, postReplay: 0 };
      });
      if (!hops) process.exitCode = 1;
      if (hops) {
        const credentials = await run('credential-isolation', async runtime => {
          credentialFacts = { cookie: false, authorization: false, password: false };
          const agent = new Agent(runtime);
          const login = agent.command({ command: 'login', login_timeout_seconds: 20, projects: [] });
          await runtime.page.locator('input[type=password]').waitFor();
          assert.equal(received.filter(row => row.group === group && row.method === 'POST').length, 0, 'login submitted before simulated user action');
          // Local synthetic user only. Production Agent.login never interacts.
          await runtime.page.locator('input[type=password]').fill(synthetic.password);
          await runtime.page.getByRole('button', { name: 'Local Sign In' }).click();
          assert.equal((await login).ok, true, 'synthetic login failed');
          runtime.policy.phase = 'read';
          await runtime.page.evaluate(async auth => {
            await fetch('/build/1', { headers: { Authorization: auth } });
          }, synthetic.auth);
          assert.deepEqual(credentialFacts, { cookie: true, authorization: true, password: true }, 'synthetic credential did not reach fixture');
          const protocol = await agent.command({ command: 'read', path: '/build/1' });
          assert.equal(protocol.ok, true, 'credential page read failed');
          assert.equal(Object.values(synthetic).some(value => JSON.stringify(protocol).includes(value)), false, 'protocol exposed synthetic credential');
          // Deliver an actual credential-bearing event to the real adapter with
          // a malformed URL. The adapter's exception must only produce a fixed category.
          const root = runtime.guards.root;
          const handlers = root.listeners('Fetch.requestPaused');
          assert.equal(handlers.length, 1);
          root.removeListener('Fetch.requestPaused', handlers[0]);
          root.on('Fetch.requestPaused', event => handlers[0]({ ...event, request: { ...event.request, url: 'invalid-url' } }));
          runtime.policy.phase = 'read';
          await runtime.page.evaluate(auth => fetch('/build/1', { headers: { Authorization: auth } }).catch(() => {}), synthetic.auth).catch(() => {});
          await wait(200);
          assert.equal(runtime.failure, 'QB_BROWSER_UNAVAILABLE', 'adapter exception did not fail closed');
          return { credentialFacts, protocol, exception: { ok: false, error: runtime.failure } };
        });
        if (!credentials) process.exitCode = 1;
      }
    }
  }
} finally {
  for (const instance of [server, plain]) {
    instance.closeAllConnections(); await new Promise(resolve => instance.close(resolve));
  }
  await rm(directory, { recursive: true, force: true });
  console.log(JSON.stringify({ summary: results.length, passed: results.filter(row => row.ok).length,
    failed: results.filter(row => !row.ok).length, network: 'loopback-only', temporaryDirectoryRemoved: true }));
}
