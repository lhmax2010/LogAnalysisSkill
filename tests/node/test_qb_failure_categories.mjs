import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import test from 'node:test';
import { Agent, Policy, FAILURE_CATEGORIES, recordFailure, installGuards }
  from '../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';

for (const category of FAILURE_CATEGORIES) test(`fixed stop category ${category}`, async t => {
  const lines = [];
  t.mock.method(process.stderr, 'write', line => { lines.push(line); return true; });
  const runtime = { failure: 'QB_BROWSER_UNAVAILABLE', trace: [], policy: new Policy(), page: {} };
  recordFailure(runtime, category);
  const agent = new Agent(runtime); agent.state = 'ready';
  assert.deepEqual(await agent.command({ command: 'read', path: '/build/1' }), {
    ok: false, error: 'QB_BROWSER_UNAVAILABLE', failure_category: category,
  });
  assert.deepEqual(lines, [`QB_AGENT_STOPPED category=${category}\n`]);
  assert.deepEqual(runtime.trace, [{ action: 'AGENT_STOPPED', failure_category: category }]);
});

async function guards(mode) {
  const primary = new EventEmitter(), root = new EventEmitter(), related = new EventEmitter();
  primary.send = async method => method === 'Target.getTargetInfo' ? { targetInfo: { targetId: 'main' } }
    : method === 'Page.getFrameTree' ? { frameTree: { frame: { id: 'main-frame' } } } : {};
  const calls = [];
  root.send = async (method, args) => {
    calls.push({ method, args });
    if (method === 'Target.closeTarget') {
      if (mode === 'close-throw') throw new Error('synthetic private error');
      return { success: mode !== 'close-false' };
    }
    if (method === 'Fetch.continueRequest' && mode === 'continue-fail') throw new Error('synthetic private error');
    return {};
  };
  related.send = root.send;
  let count = 0;
  const policy = new Policy(); policy.phase = 'login';
  const stops = [];
  await installGuards({ newBrowserCDPSession: async () => count++ ? related : root },
    { newCDPSession: async () => primary }, {}, policy, category => stops.push(category), []);
  return { root, calls, stops };
}

for (const [mode, expected] of [
  ['new-page', 'NEW_PAGE'], ['not-paused', 'WORKER_NOT_PAUSED'],
  ['close-false', 'CLOSE_TARGET_FAILED'], ['close-throw', 'CLOSE_TARGET_FAILED'],
  ['bad-event', 'ADAPT_FAILED'], ['continue-fail', 'FETCH_CONTINUE_FAILED'],
]) test(`actual guard stop site ${mode}`, async () => {
  const { root, stops } = await guards(mode);
  if (mode === 'new-page') root.emit('Target.targetCreated', { targetInfo: { type: 'page', targetId: 'new' } });
  else if (mode === 'bad-event') root.emit('Fetch.requestPaused', { request: { url: 'invalid' } });
  else if (mode === 'continue-fail') root.emit('Fetch.requestPaused', {
    requestId: 'r', frameId: 'main-frame', resourceType: 'Document',
    request: { method: 'GET', url: 'https://quickbuild.tizen.org/signin' },
  });
  else root.emit('Target.attachedToTarget', { targetInfo: { type: 'worker', targetId: 'w' }, waitingForDebugger: mode !== 'not-paused' });
  await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(stops, [expected]);
});

test('successfully closed paused worker does not gain a new stop condition', async () => {
  const { root, stops, calls } = await guards('close-ok');
  root.emit('Target.attachedToTarget', { targetInfo: { type: 'worker', targetId: 'w' }, waitingForDebugger: true });
  await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(stops, []);
  assert.ok(calls.some(call => call.method === 'Target.closeTarget'));
});
