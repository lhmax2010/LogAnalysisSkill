import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import test from 'node:test';
import { Agent, Policy, installGuards } from '../../tizen-qb-verify/scripts/tizen_qb_verify/qb_browser_agent.mjs';

const flush = () => new Promise(resolve => setImmediate(resolve));
const privateText = 'cookie=private-cookie Authorization: private-header ?token=private-query';
async function fixture(send = async () => ({})) {
  const primary = new EventEmitter(), root = new EventEmitter(), related = new EventEmitter();
  primary.send = async method => method === 'Target.getTargetInfo' ? { targetInfo: { targetId: 'main' } }
    : method === 'Page.getFrameTree' ? { frameTree: { frame: { id: 'frame' } } } : {};
  root.send = send; related.send = async () => ({});
  const policy = new Policy(), trace = [], stops = [];
  let calls = 0;
  await installGuards({ newBrowserCDPSession: async () => calls++ ? related : root },
    { newCDPSession: async () => primary }, {}, policy, value => stops.push(value), trace);
  return { primary, root, policy, trace, stops };
}
function paused(root, url, status) {
  root.emit('Fetch.requestPaused', { requestId: 'request-private', frameId: 'frame',
    resourceType: 'Document', responseStatusCode: status,
    request: { url: `https://quickbuild.tizen.org${url}`, method: 'GET',
      headers: { Cookie: 'private-cookie', Authorization: 'private-header' },
      postData: 'private-body' } });
}
const diagnostics = trace => trace.filter(row => row.action === 'OPERATION_FAILED');

for (const method of ['Fetch.failRequest', 'Fetch.continueRequest', 'Fetch.continueResponse']) {
  test(`rejected ${method} still stops and records fixed metadata`, async () => {
    const { root, policy, trace, stops, primary } = await fixture(async name => {
      if (name === method) throw new Error(`Invalid InterceptionId ${privateText}`);
      return {};
    });
    policy.phase = 'login';
    primary.emit('Page.frameNavigated', { frame: { id: 'frame' } });
    if (method === 'Fetch.continueResponse') {
      paused(root, '/signin'); await flush(); paused(root, '/signin', 200);
    } else paused(root, method === 'Fetch.failRequest' ? '/private?token=private-query' : '/signin');
    await flush();
    assert.deepEqual(stops, method === 'Fetch.failRequest' ? [] : ['FETCH_CONTINUE_FAILED']);
    assert.deepEqual(trace.filter(row => row.action === 'DENY_TARGET_GONE'),
      method === 'Fetch.failRequest' ? [{ action: 'DENY_TARGET_GONE', phase: 'login',
        stage: 'request', path: '<other>', generation: 1 }] : []);
    assert.deepEqual(diagnostics(trace), method === 'Fetch.failRequest' ? [] : [{ action: 'OPERATION_FAILED', operation: method,
      phase: 'login', stage: method === 'Fetch.continueResponse' ? 'response' : 'request',
      path: method === 'Fetch.failRequest' ? '<other>' : '/signin', generation: 1,
      category: 'REQUEST_ID_INVALID' }]);
    for (const secret of ['private-', 'cookie', 'Authorization', 'headers', 'Invalid InterceptionId', 'token=']) {
      assert.ok(!JSON.stringify(trace).includes(secret));
    }
  });
}

test('capture scheduling phase and generation, keep first rejection only', async () => {
  let reject;
  const { root, primary, policy, trace, stops } = await fixture(method => method === 'Fetch.failRequest'
    ? new Promise((_, no) => { reject = no; }) : Promise.resolve({}));
  policy.phase = 'submit'; primary.emit('Page.frameNavigated', { frame: { id: 'frame' } });
  paused(root, '/wicket/page?secret');
  policy.phase = 'read'; primary.emit('Page.frameNavigated', { frame: { id: 'frame' } });
  reject(new Error('Session closed ' + privateText)); await flush();
  paused(root, '/private'); reject(new Error('Invalid requestId ' + privateText)); await flush();
  assert.deepEqual(stops, ['FETCH_CONTINUE_FAILED']);
  assert.deepEqual(trace.filter(row => row.action === 'DENY_TARGET_GONE'),
    [{ action: 'DENY_TARGET_GONE', phase: 'read', stage: 'request', path: '<other>', generation: 2 }]);
  assert.equal(diagnostics(trace).length, 1);
  assert.equal(diagnostics(trace)[0].phase, 'submit');
  assert.equal(diagnostics(trace)[0].generation, 1);
  assert.equal(diagnostics(trace)[0].category, 'TARGET_OR_SESSION_CLOSED');
});

const categories = [
  ['Invalid requestId', 'REQUEST_ID_INVALID'], ['Target page, context or browser has been closed', 'TARGET_OR_SESSION_CLOSED'],
  ['Navigation interrupted by another navigation', 'NAVIGATION_INTERRUPTED'],
  ['net::ERR_BLOCKED_BY_CLIENT', 'BLOCKED_BY_CLIENT'], ['net::ERR_CONNECTION_RESET', 'CONNECTION_FAILED'],
  ['Timeout 30000ms exceeded', 'TIMEOUT'], ['unregistered failure', 'OTHER'],
];
for (const [message, category] of categories) test(`read navigation diagnostic ${category}`, async () => {
  const { policy, trace } = await fixture();
  const error = new Error(message + ' ' + privateText);
  const runtime = { policy, trace, page: { goto: async () => { throw error; } } };
  const agent = new Agent(runtime); agent.state = 'ready';
  const response = await agent.command({ command: 'read', path: '/build/12/overview' });
  assert.deepEqual(response, { ok: false, error: 'QB_BROWSER_UNAVAILABLE', failure_category: 'UNKNOWN' });
  assert.deepEqual(diagnostics(trace), [{ action: 'OPERATION_FAILED', operation: 'page.goto', phase: 'read',
    stage: 'navigation', path: '/build/<id>/overview', generation: 0, category }]);
  assert.ok(!JSON.stringify(trace).includes('private'));
  assert.equal(policy.readNavigation, null);
});

test('read navigation cancellation after a gone deny records navigation as first failure', async () => {
  const { root, policy, trace, stops } = await fixture(async method => {
    if (method === 'Fetch.failRequest') throw new Error('Invalid InterceptionId');
    return {};
  });
  const agent = new Agent({ policy, trace, page: { goto: async () => {
    paused(root, '/private'); await flush(); throw new Error('net::ERR_ABORTED');
  } } }); agent.state = 'ready';
  const response = await agent.command({ command: 'read', path: '/build/1' });
  assert.equal(response.error, 'QB_BROWSER_UNAVAILABLE');
  assert.deepEqual(stops, []);
  assert.deepEqual(trace.filter(row => row.action === 'DENY_TARGET_GONE'),
    [{ action: 'DENY_TARGET_GONE', phase: 'read', stage: 'request', path: '<other>', generation: 0 }]);
  assert.equal(diagnostics(trace).length, 1);
  assert.equal(diagnostics(trace)[0].operation, 'page.goto');
  assert.equal(diagnostics(trace)[0].category, 'NAVIGATION_INTERRUPTED');
});

for (const command of ['read', 'submit']) test(`command catch observes ${command} without changing response`, async () => {
  const { policy, trace } = await fixture();
  const agent = new Agent({ policy, trace, page: { url: () => 'https://quickbuild.tizen.org/wicket/page?private-query' } });
  agent.state = command === 'read' ? 'ready' : 'filled';
  agent[command] = async () => { throw new Error('private-error'); };
  const response = await agent.command({ command, path: '/build/1' });
  assert.deepEqual(response, { ok: false, error: 'QB_BROWSER_UNAVAILABLE', failure_category: 'UNKNOWN',
    ...(command === 'submit' ? { released: false } : {}) });
  assert.equal(diagnostics(trace)[0].operation, 'Agent.command');
  assert.equal(diagnostics(trace)[0].category, 'OTHER');
  assert.ok(!JSON.stringify(trace).includes('private'));
});

test('released submit response is unchanged even when diagnostics cannot be written', async () => {
  const { policy, trace } = await fixture();
  const agent = new Agent({ policy, trace, page: {} }); agent.state = 'filled';
  agent.submit = async () => { policy.released = true; throw new Error(privateText); };
  assert.deepEqual(await agent.command({ command: 'submit' }), {
    ok: true, landed: 'unknown', released: true, observed: '<other>', messages: [],
  });
});

test('diagnostic sink and exception getters cannot change a guard stop', async () => {
  const { root, trace, stops } = await fixture(async method => {
    if (method === 'Fetch.failRequest') throw { get message() { throw new Error(privateText); } };
    return {};
  });
  const push = trace.push.bind(trace);
  trace.push = row => { if (row.action === 'OPERATION_FAILED') throw new Error(privateText); return push(row); };
  paused(root, '/private'); await flush(); paused(root, '/private'); await flush();
  assert.deepEqual(stops, ['FETCH_CONTINUE_FAILED', 'FETCH_CONTINUE_FAILED']);
  assert.deepEqual(diagnostics(trace), []);
});

test('diagnostic sink failure preserves the original navigation rejection', async () => {
  const { policy, trace } = await fixture();
  policy.observeFailure = () => { throw new Error('diagnostic failure'); };
  const original = new Error('original failure');
  const agent = new Agent({ policy, trace, page: { goto: async () => { throw original; } } });
  await assert.rejects(agent.read('/build/1'), error => error === original);
});
