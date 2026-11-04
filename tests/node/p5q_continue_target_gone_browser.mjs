// Real Chromium cancellation evidence. No manufactured CDP error or response.
import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { writeFile } from 'node:fs/promises';
import { performance } from 'node:perf_hooks';
import { Agent, createRuntime } from '../../tizen-qb-verify/scripts/tizen_qb_verify/qb_browser_agent.mjs';
import { fakeQuickBuild, PROJECT } from './p5q_fake_quickbuild.mjs';

const [playwright, chromium, output, mode = 'before'] = process.argv.slice(2);
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
async function until(condition, limit = 10000) {
  const deadline = Date.now() + limit;
  while (!condition()) { if (Date.now() > deadline) throw new Error('PROBE_DEADLINE'); await wait(10); }
}
function category(error) {
  if (/Invalid (?:InterceptionId|interceptionId|requestId)|No resource with given identifier/i.test(error?.message ?? '')) return 'REQUEST_ID_INVALID';
  if (/Target.*closed|Session closed|browser has been closed/i.test(error?.message ?? '')) return 'TARGET_OR_SESSION_CLOSED';
  return error?.name === 'TimeoutError' ? 'TIMEOUT' : 'OTHER';
}
const data = { mode, network: 'loopback-only', samples: [] };
for (let index = 1; index <= 3; index++) {
  const sample = { index, events: [], operations: [], received: [], cancelled: [], trace: [] };
  data.samples.push(sample);
  const start = performance.now();
  const now = () => Math.round(performance.now() - start);
  const fixture = await fakeQuickBuild();
  let runtime;
  const held = new Map(), networks = new Map();
  let release;
  const barrier = new Promise(resolve => { release = resolve; });
  const paths = ['/styles/cancel.css', '/scripts/cancel.js', '/images/cancel.png'];
  fixture.dashboardResources = '<link rel="stylesheet" href="/styles/cancel.css">'
    + '<script async src="/scripts/cancel.js"></script><img src="/images/cancel.png">'
    + '<img src="/images/delayed.png">';
  fixture.staticResources = new Map([
    [paths[0], { contentType: 'text/css', body: 'body{}' }],
    [paths[1], { contentType: 'application/javascript', body: 'void 0;' }],
    [paths[2], { contentType: 'image/png', body: Buffer.from([]) }],
    ['/images/delayed.png', { contentType: 'image/png', body: Buffer.from([]), delayMs: 3000 }],
  ]);
  try {
    runtime = await createRuntime(playwright, chromium, fixture.overrides);
    const agent = new Agent(runtime);
    const root = runtime.guards.root, primary = runtime.guards.primary;
    await primary.send('Network.enable');
    primary.on('Network.loadingFailed', event => {
      const seq = networks.get(event.requestId);
      if (seq !== undefined) {
        sample.events.push({ action: 'NETWORK_LOADING_FAILED', seq, cancelled: event.canceled === true,
          generation: runtime.policy.diagnosticGeneration, ms: now() });
        if (event.canceled === true) sample.cancelled.push(seq);
      }
    });
    root.prependListener('Fetch.requestPaused', event => {
      if (event.responseStatusCode !== undefined) return;
      const path = new URL(event.request.url).pathname;
      if (!paths.includes(path)) return;
      const seq = paths.indexOf(path) + 1;
      held.set(event.requestId, { seq, type: event.resourceType });
      networks.set(event.networkId, seq);
      sample.events.push({ action: 'PAUSED', seq, type: event.resourceType,
        generation: runtime.policy.diagnosticGeneration, ms: now() });
    });
    const send = root.send.bind(root);
    root.send = async (method, params) => {
      const metadata = held.get(params?.requestId);
      if (method !== 'Fetch.continueRequest' || !metadata) return send(method, params);
      await barrier;
      const op = { operation: method, ...metadata, cancelled_before_call: sample.cancelled.includes(metadata.seq),
        generation: runtime.policy.diagnosticGeneration, ms: now() };
      sample.operations.push(op);
      try { const result = await send(method, params); op.category = 'OK'; return result; }
      catch (error) { op.category = category(error); throw error; }
    };
    const login = agent.command({ command: 'login', projects: [PROJECT], login_timeout_seconds: 20 });
    await runtime.page.locator('input[name=user]').fill('synthetic');
    await runtime.page.locator('input[type=password]').fill('synthetic-password');
    await runtime.page.getByRole('button', { name: 'Login' }).click({ noWaitAfter: true });
    assert.deepEqual(await login, { ok: true });
    await until(() => held.size === 3 && fixture.received.some(row => row.path === '/images/delayed.png'));
    sample.events.push({ action: 'READ_STARTED', generation: runtime.policy.diagnosticGeneration, ms: now() });
    const reading = agent.command({ command: 'read', path: '/overview/1917' });
    await until(() => new Set(sample.cancelled).size === 3);
    sample.events.push({ action: 'CANCELS_CONFIRMED', generation: runtime.policy.diagnosticGeneration, ms: now() });
    release();
    const response = await reading;
    sample.read = { ok: response.ok, error: response.error ?? null, has_body: typeof response.html_redacted === 'string' };
    await until(() => sample.operations.length === 3 && sample.operations.every(op => op.category));
    assert.ok(sample.operations.every(op => op.cancelled_before_call && op.category === 'REQUEST_ID_INVALID'));
    for (const path of paths) assert.equal(fixture.received.filter(row => row.path === path).length, 0);
    if (mode === 'before') {
      await until(() => runtime.failure !== null);
      assert.equal(runtime.failure, 'QB_BROWSER_UNAVAILABLE');
      assert.ok(runtime.trace.some(row => row.action === 'OPERATION_FAILED'
        && row.operation === 'Fetch.continueRequest' && row.category === 'REQUEST_ID_INVALID'));
    } else {
      assert.equal(runtime.failure, null);
      assert.equal(response.ok, true);
      assert.equal(runtime.trace.filter(row => row.action === 'CONTINUE_TARGET_GONE').length, 3);
      assert.equal(runtime.trace.filter(row => row.action === 'OPERATION_FAILED').length, 0);
      const next = await agent.command({ command: 'read', path: '/build/1193467/overview' });
      assert.equal(next.ok, true);
      sample.next_read_ok = next.ok;
    }
    sample.ok = true;
  } catch (error) {
    sample.ok = false;
    sample.failure = error instanceof assert.AssertionError ? 'ASSERTION_FAILED' : category(error);
    process.exitCode = 1;
  } finally {
    release();
    if (runtime) {
      await runtime.close(); sample.profile_removed = !existsSync(runtime.profile); sample.trace = runtime.trace;
    }
    sample.received = fixture.received.map(row => ({ method: row.method,
      kind: row.path.includes('Listener') ? 'login' : row.path === '/images/delayed.png' ? 'delayed-image'
        : paths.includes(row.path) ? 'held-resource' : 'document', status: row.status }));
    await fixture.close();
    if (!sample.profile_removed) process.exitCode = 1;
  }
  if (!sample.ok) break;
}
if (mode === 'after' && data.samples.every(row => row.ok)) {
  const fixture = await fakeQuickBuild();
  const sample = { operations: [], events: [] };
  data.main_document = sample;
  let runtime;
  try {
    runtime = await createRuntime(playwright, chromium, fixture.overrides);
    const agent = new Agent(runtime); agent.state = 'ready';
    const root = runtime.guards.root, primary = runtime.guards.primary;
    await primary.send('Network.enable');
    let networkId, requestId, cancelled = false;
    primary.on('Network.loadingFailed', event => {
      if (event.requestId === networkId && event.canceled === true) {
        cancelled = true; sample.events.push({ action: 'MAIN_DOCUMENT_CANCELLED' });
      }
    });
    root.prependListener('Fetch.requestPaused', event => {
      if (event.resourceType === 'Document' && event.responseStatusCode === undefined) {
        requestId = event.requestId; networkId = event.networkId;
      }
    });
    const send = root.send.bind(root);
    root.send = async (method, params) => {
      if (method !== 'Fetch.continueRequest' || params?.requestId !== requestId) return send(method, params);
      await primary.send('Page.stopLoading');
      await until(() => cancelled);
      const operation = { operation: method, cancelled_before_call: cancelled, category: null };
      sample.operations.push(operation);
      try { const result = await send(method, params); operation.category = 'OK'; return result; }
      catch (error) { operation.category = category(error); throw error; }
    };
    const response = await agent.command({ command: 'read', path: '/build/1193467/overview' });
    await until(() => sample.operations.length === 1 && sample.operations[0].category !== null);
    assert.equal(response.ok, false);
    assert.equal(response.error, 'QB_BROWSER_UNAVAILABLE');
    assert.ok(!Object.hasOwn(response, 'html_redacted'));
    assert.equal(sample.operations[0].category, 'REQUEST_ID_INVALID');
    assert.equal(runtime.trace.filter(row => row.action === 'CONTINUE_TARGET_GONE').length, 1);
    assert.equal(runtime.trace.filter(row => row.action === 'OPERATION_FAILED' && row.operation === 'Fetch.continueRequest').length, 0);
    assert.equal(fixture.received.length, 0);
    sample.read = { ok: response.ok, error: response.error, has_body: false };
    sample.ok = true;
  } catch (error) {
    sample.ok = false; sample.failure = error instanceof assert.AssertionError ? 'ASSERTION_FAILED' : category(error);
    process.exitCode = 1;
  } finally {
    if (runtime) { await runtime.close(); sample.profile_removed = !existsSync(runtime.profile); sample.trace = runtime.trace; }
    await fixture.close();
    if (!sample.profile_removed) process.exitCode = 1;
  }
}
data.ok = data.samples.length === 3 && data.samples.every(row => row.ok && row.profile_removed)
  && (mode === 'before' || data.main_document?.ok === true && data.main_document.profile_removed);
await writeFile(output, JSON.stringify(data, null, 2) + '\n');
console.log(JSON.stringify({ ok: data.ok, samples: data.samples.length }));
