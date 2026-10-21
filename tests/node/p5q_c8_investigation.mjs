// Offline observations only. Never imports a live config or changes production guards.
import assert from 'node:assert/strict';
import { mkdir, writeFile, access } from 'node:fs/promises';
import { performance } from 'node:perf_hooks';
import { Agent, AgentError, createRuntime, adaptProtocol, pathShape } from '../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';
import { fakeQuickBuild, PROJECT, VALUES } from './p5q_fake_quickbuild.mjs';

const [playwright, chromium, output] = process.argv.slice(2);
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const classify = error => ({ class_name: error.constructor.name,
  agent_code: error instanceof AgentError ? error.code : null,
  category: /ERR_ABORTED|interrupted by another navigation/.test(error.message) ? 'NAVIGATION_INTERRUPTED'
    : /ERR_BLOCKED_BY_CLIENT/.test(error.message) ? 'BLOCKED_BY_CLIENT'
      : /ERR_EMPTY_RESPONSE|ERR_CONNECTION|ERR_HTTP2|ERR_SOCKET/.test(error.message) ? 'NETWORK_RESPONSE_FAILED'
        : error.name === 'TimeoutError' ? 'TIMEOUT' : 'OTHER_FRAMEWORK_ERROR' });

async function login(agent) {
  const pending = agent.command({ command: 'login', projects: [PROJECT], login_timeout_seconds: 20 });
  await agent.page.locator('input[name=user]').fill('synthetic');
  await agent.page.locator('input[type=password]').fill('synthetic-password');
  await agent.page.getByRole('button', { name: 'Login', exact: true }).click();
  assert.equal((await pending).ok, true);
}

async function scenario(name) {
  const fixture = await fakeQuickBuild({ mode: 'unknown' });
  const runtime = await createRuntime(playwright, chromium, fixture.overrides);
  const agent = new Agent(runtime);
  const facts = { case: name, observations: [], frame_events: [], reads: [], trace: [], server_requests: [] };
  let phase = 'setup';
  runtime.guards.primary.on('Page.frameNavigated', ({ frame }) => facts.frame_events.push({
    phase, action: 'navigated', frame_id: frame.id, parent_id: frame.parentId ?? null,
  }));
  runtime.guards.primary.on('Page.frameDetached', ({ frameId, reason }) => facts.frame_events.push({
    phase, action: 'detached', frame_id: frameId, reason,
  }));
  runtime.guards.root.on('Fetch.requestPaused', event => {
    try {
      const { frameId, metadata } = adaptProtocol(event);
      facts.observations.push({ phase, policy_phase: runtime.policy.phase, frame_id: frameId,
        frame_owned: runtime.guards.frames.has(frameId), method: metadata.method,
        path: pathShape(metadata.path), response_status: metadata.response_status });
    } catch { facts.observations.push({ phase, category: 'ADAPT_FAILED' }); }
  });
  const original = agent.read.bind(agent);
  agent.read = async path => {
    const row = { path, error: null }, start = performance.now();
    facts.reads.push(row);
    try { return await original(path); }
    catch (error) { row.error = classify(error); throw error; }
    finally { row.elapsed_ms = Math.round(performance.now() - start); }
  };
  try {
    phase = 'login'; await login(agent);
    phase = 'open_form'; assert.equal((await agent.command({ command: 'open_form', overview_id: 1917 })).ok, true);
    phase = 'fill'; const fill = await agent.command({ command: 'fill', fields: VALUES });
    assert.equal(fill.ok, true);
    const auto = name === 'idle-script-navigation' || name === 'racing-script-navigation';
    if (auto) fixture.landingScript = `<script>setTimeout(()=>location.href='/build/1193467',350)</script>`;
    if (name === 'racing-meta-refresh') fixture.landingScript = '<meta http-equiv="refresh" content="1;url=/build/1193467">';
    if (name === 'racing-wicket-navigation') fixture.landingScript = `<script>setTimeout(()=>location.href='/wicket/page?100',350)</script>`;
    if (name.startsWith('racing-')) fixture.configurationDelayMs = 1800;
    if (name === 'delay-only-control' || name === 'injected-competing-navigation') fixture.configurationDelayMs = 1800;
    if (name === 'configuration-connection-abort') fixture.configurationAbort = true;
    if (name === 'configuration-redirect-signin') fixture.configurationRedirect = { status: 302, path: '/signin' };
    if (name === 'configuration-redirect-307') fixture.configurationRedirect = { status: 307, path: '/overview/1917' };
    facts.root_before = (await runtime.guards.primary.send('Page.getFrameTree')).frameTree.frame.id;
    phase = 'submit'; facts.submit = await agent.command({ command: 'submit', fingerprint: fill.fingerprint });
    assert.equal(facts.submit.ok, true); assert.equal(facts.submit.landed, 'unknown');
    assert.equal(fixture.submissions.length, 1);
    phase = 'idle';
    if (name === 'idle-script-navigation') await sleep(650);
    facts.root_after_submit = (await runtime.guards.primary.send('Page.getFrameTree')).frameTree.frame.id;
    if (name === 'injected-missing-root-membership') {
      // Fault injection only: model a missed ownership event, not a production rule change.
      runtime.guards.frames.detach(facts.root_after_submit);
      facts.injected_fault = 'ROOT_MEMBERSHIP_REMOVED';
    }
    phase = 'read';
    let competing;
    if (name === 'injected-competing-navigation') {
      // Test-controlled second navigation; unlike the timer cases, force overlap.
      facts.injected_fault = 'CONCURRENT_CDP_NAVIGATION';
      competing = sleep(250).then(() => runtime.guards.primary.send('Page.navigate', { url: 'https://quickbuild.tizen.org/build/1193467' }))
        .then(() => { facts.competing_navigation = 'DISPATCHED'; }, error => { facts.competing_error = classify(error); });
    }
    const result = await agent.command({ command: 'read', path: '/overview/1917' });
    if (competing) await competing;
    facts.response = { ok: result.ok, error: result.error ?? null,
      failure_category: result.failure_category ?? null, status: result.status ?? null };
    facts.runtime_failure = runtime.failure;
    facts.browser_connected_after_reply = runtime.browser.isConnected();
    facts.root_after_read = (await runtime.guards.primary.send('Page.getFrameTree')).frameTree.frame.id;
    facts.signature = !result.ok && result.error === 'QB_BROWSER_UNAVAILABLE'
      && result.failure_category === 'UNKNOWN' && runtime.browser.isConnected()
      && facts.reads.at(-1).elapsed_ms < 3000;
    if (name === 'control') assert.equal(result.ok, true);
  } catch (error) { facts.harness_failure = classify(error); }
  finally {
    facts.trace = runtime.trace;
    facts.server_requests = fixture.received.map(({ method, path, status }) => ({ method, path, status }));
    facts.synthetic_submissions = fixture.submissions.length;
    phase = 'close';
    await agent.command({ command: 'close' });
    await fixture.close();
    facts.profile_removed = await access(runtime.profile).then(() => false, () => true);
    await writeFile(`${output}/${name}.json`, JSON.stringify(facts, null, 2) + '\n');
  }
  assert.equal(facts.harness_failure, undefined, `CASE_FAILED_${name}`);
  assert.equal(facts.profile_removed, true);
  assert.ok(facts.server_requests.every(row => !/promote|cancel|stop|rerun|\/rest\//i.test(row.path)));
  return { case: name, signature: facts.signature, response: facts.response, reads: facts.reads,
    same_root: facts.root_before === facts.root_after_submit && facts.root_after_submit === facts.root_after_read };
}

async function main() {
  assert.equal(process.env.P5Q_TEST_DISPLAY, 'virtual');
  await mkdir(output, { recursive: true });
  const cases = [];
  const names = process.env.P5Q_C8_CASES?.split(',') ?? ['control', 'idle-script-navigation', 'racing-script-navigation',
    'racing-meta-refresh', 'racing-wicket-navigation', 'injected-missing-root-membership',
    'configuration-connection-abort', 'configuration-redirect-signin', 'configuration-redirect-307',
    'delay-only-control', 'injected-competing-navigation'];
  for (const name of names) {
    cases.push(await scenario(name));
    console.log(`CASE_COMPLETE ${name}`);
  }
  await writeFile(`${output}/summary.json`, JSON.stringify(cases, null, 2) + '\n');
}
await main().catch(error => { console.error(`INVESTIGATION_STOPPED ${error.constructor.name}`); process.exitCode = 1; });
