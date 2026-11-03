import assert from 'node:assert/strict';
import { createHash, X509Certificate } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { createServer } from 'node:https';
import { existsSync } from 'node:fs';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { createRuntime, ORIGIN } from '../../tizen-qb-verify/scripts/tizen_qb_verify/qb_browser_agent.mjs';

const [playwright, chromium, output] = process.argv.slice(2);
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const directory = await mkdtemp('/dev/shm/p5q-deny-gone-');
const received = [], attempts = [];
let runtime, server;
const facts = { network: 'loopback-only', received, attempts };
try {
  execFileSync('openssl', ['req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-keyout', directory + '/key.pem',
    '-out', directory + '/cert.pem', '-days', '1', '-subj', '/CN=quickbuild.tizen.org',
    '-addext', 'subjectAltName=DNS:quickbuild.tizen.org'], { stdio: 'ignore' });
  const cert = await readFile(directory + '/cert.pem'), key = await readFile(directory + '/key.pem');
  const spki = createHash('sha256').update(new X509Certificate(cert).publicKey.export({ type: 'spki', format: 'der' })).digest('base64');
  server = createServer({ cert, key }, (request, response) => {
    received.push({ method: request.method, path: request.url }); request.resume();
    if (['/build/307', '/build/308'].includes(request.url)) {
      response.writeHead(Number(request.url.slice(-3)), { Location: '/build/9' }); response.end();
    } else {
      response.setHeader('Content-Type', 'text/html; charset=utf-8');
      response.end('<!doctype html><link rel="icon" href="data:,"><title>LOCAL ONLY</title>');
    }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  runtime = await createRuntime(playwright, chromium, { launchArgs: ['--no-proxy-server',
    `--host-resolver-rules=MAP quickbuild.tizen.org 127.0.0.1:${server.address().port}, EXCLUDE 127.0.0.1, MAP * ~NOTFOUND`,
    `--ignore-certificate-errors-spki-list=${spki}`] });
  runtime.policy.phase = 'read';
  await runtime.page.goto(ORIGIN + '/build/1');
  const root = runtime.guards.root, send = root.send.bind(root);
  let cancelNext = false;
  root.send = async (method, params) => {
    if (method === 'Fetch.failRequest' && cancelNext) {
      cancelNext = false;
      // Cancel the real paused navigation before invoking the real CDP method.
      await runtime.guards.primary.send('Page.stopLoading');
      await wait(50);
      try { const result = await send(method, params); attempts.push({ operation: method, rejected: false }); return result; }
      catch (error) { attempts.push({ operation: method, rejected: true }); throw error; }
    }
    return send(method, params);
  };
  for (const path of ['/rest/gone-one', '/rest/gone-two']) {
    cancelNext = true;
    await runtime.page.goto(ORIGIN + path).catch(() => {});
    await wait(150);
    assert.equal(cancelNext, false);
    assert.equal(received.filter(row => row.path === path).length, 0);
    assert.equal(runtime.failure, null);
    await runtime.page.goto(ORIGIN + '/build/1');
  }
  assert.deepEqual(attempts, [{ operation: 'Fetch.failRequest', rejected: true }, { operation: 'Fetch.failRequest', rejected: true }]);
  assert.equal(runtime.trace.filter(row => row.action === 'DENY_TARGET_GONE').length, 2);
  assert.equal(runtime.trace.filter(row => row.action === 'OPERATION_FAILED').length, 0);
  const start = received.length;
  for (const path of ['/rest/after', '/wicket/page?1-1.ILinkListener-content-buildHead-promote']) {
    await runtime.page.goto(ORIGIN + path).catch(() => {});
    await wait(100);
  }
  assert.equal(received.length, start);
  const handler = root.listeners('Fetch.requestPaused')[0];
  root.removeListener('Fetch.requestPaused', handler);
  root.on('Fetch.requestPaused', event => handler(event.request.url === ORIGIN + '/build/9'
    ? { ...event, frameId: 'unknown-frame' } : event));
  await runtime.page.goto(ORIGIN + '/build/9').catch(() => {});
  await wait(100);
  assert.equal(received.length, start);
  for (const status of [307, 308]) {
    const before = received.length;
    await runtime.page.goto(ORIGIN + '/build/' + status).catch(() => {});
    await wait(100);
    assert.deepEqual(received.slice(before), [{ method: 'GET', path: '/build/' + status }]);
  }
  await runtime.page.goto(ORIGIN + '/build/1');
  assert.equal(runtime.failure, null);
  assert.ok(runtime.trace.filter(row => row.action === 'DENIED').length >= 7);
  assert.ok(!JSON.stringify(runtime.trace).includes('ILinkListener'));
  facts.ok = true;
} catch (error) {
  facts.ok = false; facts.failure = error instanceof assert.AssertionError ? 'ASSERTION_FAILED' : 'LOCAL_TEST_ERROR';
  process.exitCode = 1;
} finally {
  if (runtime) {
    facts.trace = runtime.trace;
    await runtime.close(); facts.profile_removed = !existsSync(runtime.profile);
  }
  if (server?.listening) { server.closeAllConnections(); await new Promise(resolve => server.close(resolve)); }
  await rm(directory, { recursive: true, force: true });
  facts.fixture_removed = !existsSync(directory);
  if (output) await writeFile(output, JSON.stringify(facts, null, 2) + '\n');
  console.log(JSON.stringify(facts));
}
