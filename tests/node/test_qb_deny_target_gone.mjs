import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import test from 'node:test';
import { withoutElapsed } from './elapsed_trace.mjs';
import { installGuards, Policy } from '../../tizen-qb-verify/scripts/tizen_qb_verify/qb_browser_agent.mjs';

const flush = () => new Promise(resolve => setImmediate(resolve));
const secret = 'private-cookie Authorization: private-header ?token=private-query';
async function fixture(reject) {
  const primary = new EventEmitter(), root = new EventEmitter(), related = new EventEmitter();
  primary.send = async method => method === 'Target.getTargetInfo' ? { targetInfo: { targetId: 'main' } }
    : method === 'Page.getFrameTree' ? { frameTree: { frame: { id: 'main-frame' } } } : {};
  root.send = async method => { if (reject(method)) throw new Error(reject(method) + ' ' + secret); return {}; };
  related.send = async () => ({});
  const trace = [], stops = [], policy = new Policy();
  let calls = 0;
  await installGuards({ newBrowserCDPSession: async () => calls++ ? related : root },
    { newCDPSession: async () => primary }, {}, policy, category => stops.push(category), trace);
  policy.phase = 'login';
  const pause = (path, status) => root.emit('Fetch.requestPaused', { requestId: 'private-request', frameId: 'main-frame',
    resourceType: 'Document', responseStatusCode: status,
    request: { url: 'https://quickbuild.tizen.org' + path, method: 'GET',
      headers: { Cookie: secret }, postData: secret } });
  return { pause, trace, stops };
}

const categories = [
  ['Invalid InterceptionId', 'REQUEST_ID_INVALID'], ['Session closed', 'TARGET_OR_SESSION_CLOSED'],
  ['net::ERR_ABORTED', 'NAVIGATION_INTERRUPTED'], ['net::ERR_BLOCKED_BY_CLIENT', 'BLOCKED_BY_CLIENT'],
  ['net::ERR_CONNECTION_RESET', 'CONNECTION_FAILED'], ['Timeout exceeded', 'TIMEOUT'], ['unclassified', 'OTHER'],
];
for (const method of ['Fetch.failRequest', 'Fetch.continueRequest', 'Fetch.continueResponse']) {
  for (const [message, category] of categories) test(`${method} ${category} exact stop matrix`, async () => {
    const { pause, trace, stops } = await fixture(name => name === method ? message : null);
    if (method === 'Fetch.continueResponse') { pause('/signin'); await flush(); pause('/signin', 200); }
    else pause(method === 'Fetch.failRequest' ? '/rest/blocked?token=private-query' : '/signin');
    await flush();
    const gone = ['Fetch.failRequest', 'Fetch.continueRequest'].includes(method) && category === 'REQUEST_ID_INVALID';
    assert.deepEqual(stops, gone ? [] : ['FETCH_CONTINUE_FAILED']);
    assert.equal(trace.filter(row => row.action === 'DENY_TARGET_GONE').length, gone && method === 'Fetch.failRequest' ? 1 : 0);
    assert.equal(trace.filter(row => row.action === 'CONTINUE_TARGET_GONE').length, gone && method === 'Fetch.continueRequest' ? 1 : 0);
    const failures = trace.filter(row => row.action === 'OPERATION_FAILED');
    assert.equal(failures.length, gone ? 0 : 1);
    if (!gone) assert.equal(failures[0].category, category);
    for (const value of ['private-', 'Authorization', 'headers', 'postData', message]) {
      assert.ok(!JSON.stringify(trace).includes(value));
    }
  });
}

test('every gone deny is recorded without consuming the first failure', async () => {
  let message = 'Invalid requestId';
  const { pause, trace, stops } = await fixture(method => method === 'Fetch.failRequest' ? message : null);
  pause('/rest/one'); await flush(); pause('/rest/two'); await flush();
  assert.deepEqual(stops, []);
  assert.equal(trace.filter(row => row.action === 'OPERATION_FAILED').length, 0);
  assert.equal(trace.filter(row => row.action === 'DENY_TARGET_GONE').length, 2);
  message = 'Session closed'; pause('/rest/three'); await flush();
  assert.deepEqual(stops, ['FETCH_CONTINUE_FAILED']);
  assert.equal(trace.filter(row => row.action === 'OPERATION_FAILED')[0].category, 'TARGET_OR_SESSION_CLOSED');
  message = 'Invalid requestId'; pause('/rest/four'); await flush();
  assert.equal(trace.filter(row => row.action === 'DENY_TARGET_GONE').length, 3);
  assert.equal(trace.filter(row => row.action === 'OPERATION_FAILED').length, 1);
});

test('gone trace sink failure does not change the narrowly allowed outcome', async () => {
  const { pause, trace, stops } = await fixture(method => method === 'Fetch.failRequest' ? 'Invalid requestId' : null);
  const push = trace.push.bind(trace);
  trace.push = row => { if (row.action === 'DENY_TARGET_GONE') throw new Error(secret); return push(row); };
  pause('/rest/one'); await flush(); pause('/rest/two'); await flush();
  assert.deepEqual(stops, []);
  assert.ok(!JSON.stringify(trace).includes('private-'));
});

test('every gone continue is recorded without consuming the first failure', async () => {
  let message = 'Invalid requestId';
  const { pause, trace, stops } = await fixture(method => method === 'Fetch.continueRequest' ? message : null);
  pause('/signin'); await flush(); pause('/signin'); await flush();
  assert.deepEqual(stops, []);
  assert.equal(trace.filter(row => row.action === 'OPERATION_FAILED').length, 0);
  assert.deepEqual(withoutElapsed(trace.filter(row => row.action === 'CONTINUE_TARGET_GONE')), [0, 1].map(() => ({
    action: 'CONTINUE_TARGET_GONE', phase: 'login', stage: 'request', path: '/signin', generation: 0,
  })));
  message = 'Session closed'; pause('/signin'); await flush();
  assert.deepEqual(stops, ['FETCH_CONTINUE_FAILED']);
  assert.equal(trace.filter(row => row.action === 'OPERATION_FAILED')[0].category, 'TARGET_OR_SESSION_CLOSED');
  message = 'Invalid requestId'; pause('/signin'); await flush();
  assert.equal(trace.filter(row => row.action === 'CONTINUE_TARGET_GONE').length, 3);
  assert.equal(trace.filter(row => row.action === 'OPERATION_FAILED').length, 1);
  assert.ok(!JSON.stringify(trace).includes('private-'));
});

test('gone continue trace sink failure cannot turn an expired ID into a stop', async () => {
  const { pause, trace, stops } = await fixture(method => method === 'Fetch.continueRequest' ? 'Invalid requestId' : null);
  const push = trace.push.bind(trace);
  trace.push = row => { if (row.action === 'CONTINUE_TARGET_GONE') throw new Error(secret); return push(row); };
  pause('/signin'); await flush(); pause('/signin'); await flush();
  assert.deepEqual(stops, []);
  assert.equal(trace.filter(row => row.action === 'OPERATION_FAILED').length, 0);
});
