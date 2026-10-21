// Contract probe only: baseline source plus the one permitted read timeout edit.
// All CDP/navigation responses are synthetic; no browser or network is started.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { setTimeout as delay } from 'node:timers/promises';

const baseline = '48b0aa9dd2d793a103839ca6239fbec668fdb648';
const path = 'tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';
const source = execFileSync('git', ['show', `${baseline}:${path}`], { encoding: 'utf8' });
const anchor = 'response = await this.page.goto(expected);';
assert.equal(source.split(anchor).length, 2);
const permitted = source.replace(anchor, 'response = await this.page.goto(expected, { timeout: 30000 });');
const { Agent, Policy } = await import(`data:text/javascript;base64,${Buffer.from(permitted).toString('base64')}`);
const prefix = source.slice(0, source.indexOf('export class Agent {'));
const holds = ['newCDPSession', 'Page.getFrameTree', 'Page.createIsolatedWorld', 'Runtime.evaluate', 'detach'];
const states = [];
const started = performance.now();
for (const hold of holds) {
  let release;
  const gate = new Promise(resolve => { release = resolve; });
  const state = { hold, calls: [], settled: false, outcome: null, release };
  const wait = async name => {
    state.calls.push(name);
    if (name === hold) await gate;
  };
  const cdp = {
    async send(method) {
      await wait(method);
      if (method === 'Page.getFrameTree') return { frameTree: { frame: { id: 'working-frame' } } };
      if (method === 'Page.createIsolatedWorld') return { executionContextId: 1 };
      assert.equal(method, 'Runtime.evaluate');
      return { result: { value: { ok: true, value: {
        build: { labels: ['Build (id:1)'], summaries: [] },
        redacted: { html_redacted: '<html><body>synthetic</body></html>', outside_identity_count: 0 },
      } } } };
    },
    async detach() { await wait('detach'); },
  };
  const policy = new Policy();
  const url = 'https://quickbuild.tizen.org/build/1/variables';
  const page = {
    url: () => url,
    async goto(expected, options) {
      assert.equal(expected, url);
      assert.deepEqual(options, { timeout: 30000 });
      state.calls.push('goto(timeout=30000)');
      Object.assign(policy.readNavigation, { requestId: 'synthetic', body: Buffer.from('<html></html>') });
      return { url: () => url, status: () => 200, request: () => ({ redirectedFrom: () => null }),
        headerValue: async () => 'text/html; charset=utf-8' };
    },
  };
  const runtime = { page, policy, trace: [], context: {
    async newCDPSession() { await wait('newCDPSession'); return cdp; },
  } };
  const agent = new Agent(runtime);
  state.promise = agent.read('/build/1/variables').then(
    () => { state.settled = true; state.outcome = 'read_returned'; },
    () => { state.settled = true; state.outcome = 'read_rejected'; },
  );
  states.push(state);
}
await delay(31000);
const observedAtMs = Math.round(performance.now() - started);
const observations = states.map(state => ({ hold: state.hold, calls: [...state.calls],
  pending_after_30000ms: !state.settled, observed_at_ms: observedAtMs }));
for (const state of states) state.release();
await Promise.all(states.map(state => state.promise));
const result = {
  baseline, source_sha256: createHash('sha256').update(source).digest('hex'),
  protected_prefix_sha256: createHash('sha256').update(prefix).digest('hex'),
  navigation_timeout_applied: true, network_requests: 0, browser_started: false,
  observations, after_release: states.map(state => ({ hold: state.hold, outcome: state.outcome })),
  contract_met: observations.every(row => !row.pending_after_30000ms),
};
process.stdout.write(JSON.stringify(result, null, 2) + '\n');
process.exitCode = result.contract_met ? 0 : 1;
