import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, rm } from 'node:fs/promises';
import { Agent, createRuntime } from '../../tizen-qb-verify/scripts/tizen_qb_verify/qb_browser_agent.mjs';
import { discoveryServer } from './p5q_discovery_fixture.mjs';
import { PROJECT } from './p5q_fake_quickbuild.mjs';
const [playwright, chromium, mode = 'ok'] = process.argv.slice(2);
const server = await discoveryServer(mode), output = await mkdtemp('/dev/shm/p5q-discovery-output-');
const runtime = await createRuntime(playwright, chromium, server.overrides);
const agent = new Agent(runtime), commands = [];
async function command(input) {
  const result = await agent.command(input); commands.push({ command: input.command, ok: result.ok, error: result.error, reason: result.reason });
  return result;
}
try {
  const login = command({ command: 'login', login_timeout_seconds: 10, projects: [PROJECT] });
  await runtime.page.locator('input[name=user]').fill('synthetic');
  await runtime.page.locator('input[type=password]').fill('synthetic-password');
  await runtime.page.getByRole('button', { name: 'Login', exact: true }).click();
  assert.equal((await login).ok, true);
  assert.equal((await command({ command: 'discovery_start', overview_id: 1917, build_id: '1193467', output_dir: output })).ok, true);
  for (const path of ['/build/1193467/overview', '/build/1193469/overview', '/build/1193469/variables',
    '/build/1193469/html_report', '/download/1193469/html/HTML%20REPORT/index.html']) {
    const result = await command({ command: 'discovery_read', path });
    if (mode === 'ambiguous' && path.endsWith('index.html')) {
      assert.equal(result.error, 'DISCOVERY_REPORT_AMBIGUOUS');
    } else assert.equal(result.ok, true, JSON.stringify(result));
  }
  if (mode !== 'ambiguous') {
    await mkdir(`${output}/discovery/1193467/test-run`, { recursive: true });
    const result = await command({ command: 'read_text', build_id: '1193469', spec_name: 'zlib', run_dir: 'test-run' });
    if (mode === 'ok') {
      assert.equal(result.ok, true, JSON.stringify(result));
      assert.equal(await readFile(result.path, 'utf8'), '<USER>\nerror: compiler failure\n');
      assert.equal(result.sha256.length, 64);
      assert.ok(!('text' in result));
    } else {
      assert.equal(result.ok, false);
      assert.equal(result.reason, { status: 'HTTP_STATUS', redirect: 'REDIRECT', encoding: 'ENCODING',
        attachment: 'DOWNLOAD', binary: 'CONTENT_TYPE', large: 'TOO_LARGE' }[mode], JSON.stringify(result));
    }
  }
  const requests = server.received.map(({ method, path }) => ({ method, path }));
  const report = requests.filter(r => r.path === '/download/1193469/html/HTML%20REPORT/index.html');
  assert.equal(report.length, 1, 'iframe must not read the child frame');
  assert.ok(!requests.some(r => r.path === '/not-registered'));
  assert.ok(requests.filter(r => r.method === 'POST').every(r => r.path.startsWith('/signin?')));
  assert.equal(runtime.policy.released, false);
  assert.equal(server.submissions.length, 0);
  for (const row of runtime.trace) if (['OPERATION_FAILED', 'DENY_TARGET_GONE', 'CONTINUE_TARGET_GONE',
    'AGENT_STOPPED', 'PAGE_CLOSED', 'BROWSER_DISCONNECTED'].includes(row.action)) {
    assert.ok(Number.isInteger(row.elapsed_ms) && row.elapsed_ms >= 0);
  }
  console.log(JSON.stringify({ mode, commands, requests, trace: runtime.trace }));
} finally {
  await runtime.close(); await server.close(); await rm(output, { recursive: true, force: true });
}
