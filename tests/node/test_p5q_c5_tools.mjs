import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtemp, mkdir, rm, writeFile, readFile } from 'node:fs/promises';
import test from 'node:test';
import { Agent, createRuntime } from '../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';
import { comparePages } from '../../docs/clang-fix-campaign/spikes/p5q_compare_raw_active.mjs';
import { rehearse } from '../../docs/clang-fix-campaign/spikes/p5q_fill_rehearsal.mjs';
import { validatePaths, PROJECT, ROOT } from '../../docs/clang-fix-campaign/spikes/p5q_c5_tools.mjs';
import { fakeQuickBuild, VALUES } from './p5q_fake_quickbuild.mjs';

const [playwright, chromium] = process.argv.slice(2);
async function login(agent) {
  const pending = agent.command({ command: 'login', projects: [PROJECT], login_timeout_seconds: 20 });
  await agent.page.locator('input[name=user]').fill('synthetic');
  await agent.page.locator('input[type=password]').fill('synthetic-password');
  await agent.page.getByRole('button', { name: 'Login', exact: true }).click();
  assert.deepEqual(await pending, { ok: true });
}

test('C5a offline evidence tools use real guards and isolated worlds', { timeout: 120000 }, async t => {
  const root = process.env.P5Q_C5A_EVIDENCE
    ? `${process.env.P5Q_C5A_EVIDENCE}/tools` : await mkdtemp('/tmp/p5q-c5a-tools-');
  await mkdir(root, { recursive: true });
  const fixture = await fakeQuickBuild();
  try {
    for (const [mode, wanted] of [['', '一致'], ['insert-nav', '只在活动文档中'], ['change-status', '值不同']]) {
      await t.test(`raw/live comparison: ${mode || 'equal'}`, async () => {
        fixture.compare = mode;
        fixture.childStatus = 'Failed';
        const runtime = await createRuntime(playwright, chromium, fixture.overrides);
        const agent = new Agent(runtime);
        const output = `${root}/${mode || 'equal'}`;
        await mkdir(output);
        try {
          await login(agent);
          const before = fixture.received.length;
          const paths = ['/build/1193469/overview'];
          if (!mode) paths.push('/build/1193467/overview', '/build/1193467/variables', '/build/1193469/variables', '/build/1193469/step_status', '/overview/1917');
          let results;
          if (mode) {
            await assert.rejects(comparePages(agent, paths, output), { code: 'EVIDENCE_PREMISE_MISMATCH' });
            results = JSON.parse(await readFile(`${output}/run.json`, 'utf8')).pages;
          } else results = await comparePages(agent, paths, output);
          const [result] = results;
          assert.equal(fixture.received.length - before, paths.length, 'one navigation per comparison');
          assert.equal(result.comparison.find(row => row.field === (mode === 'insert-nav' ? 'navigation' : 'summary')).result, wanted);
          assert.equal(result.navigation, mode === 'insert-nav' ? 'QB_READ_ID_MISMATCH' : 'VERIFIED');
          if (!mode) {
            assert.equal(results.length, paths.length);
            assert.ok(results.every(item => item.comparison.every(row => row.result === '一致')));
            assert.equal(results[2].comparison.find(row => row.field === 'variables').raw[0].rows.length, 9);
            assert.equal(results[3].comparison.find(row => row.field === 'variables').raw[0].rows
              .find(row => row[0] === 'BUILD_PKG_LIST')[2].split('\n').length, 2);
            assert.equal(results[1].comparison.find(row => row.field === 'child_build').raw.length, 1);
            assert.equal(results[4].comparison.find(row => row.field === 'failed_steps').raw[0][0], 'Build_GBS');
            assert.equal(results[5].comparison.find(row => row.field === 'copy_path').raw[0], PROJECT.configuration_path);
            assert.equal(result.comparison.find(row => row.field === 'error_message').raw[0], 'synthetic build failure');
          }
          for (const file of [result.raw_file, result.active_file]) {
            const html = await readFile(`${output}/${file}`, 'utf8');
            assert.ok(!html.includes('LocalTester'));
          }
          for (const bad of ['/rest/trigger', '/wicket/page?1', '/build/1/log', '/build/1?x', '//outside.invalid/build/1']) {
            assert.throws(() => validatePaths(runtime.policy, [bad]));
          }
        } finally { await agent.command({ command: 'close' }); }
      });
    }
    await t.test('twelve-field rehearsal: random/version/unchanged values/no action release', async () => {
      const runtime = await createRuntime(playwright, chromium, fixture.overrides);
      const agent = new Agent(runtime);
      const output = `${root}/rehearsal`;
      await mkdir(output);
      try {
        await login(agent);
        const before = fixture.received.length;
        const result = await rehearse(agent, 'local/package@' + 'c'.repeat(40), output);
        assert.equal(result.release_state, 'not_released');
        assert.equal(result.form_action_releases, 0);
        assert.ok(result.page_identity_counts.some(row => row.page.endsWith('/overview/1917')));
        assert.ok(result.page_identity_counts.some(row => row.page.includes('/wicket/page?')));
        assert.ok(result.page_identity_counts.every(row => row.outside_identity_count === 0));
        assert.equal(result.registrations.length, 12);
        assert.ok(result.registrations.every(row => row.allowed === 1 && row.denied === 0 && row.response_status[0] === 200));
        assert.ok(result.registrations.some(row => row.value_already_equal));
        assert.equal(new Set(result.registrations.map(row => row.action)).size, 12);
        const posts = result.callbacks.filter(row => row.status === null && row.method === 'POST' && row.allowed);
        assert.equal(posts.length, 12);
        assert.ok(posts.every(row => /^0\.\d{1,20}$/.test(row.random)));
        assert.equal(result.callbacks.filter(row => row.status === 200).length, 12);
        assert.ok(result.callbacks.some(row => row.allowed === false && row.method === 'GET'));
        assert.equal(fixture.submissions.length, 0);
        assert.equal(fixture.received.slice(before).filter(row => row.method === 'POST').length, 12);
      } finally { await agent.command({ command: 'close' }); }
    });
    for (const loginCase of ['signin-with-signout', 'password-remains', 'no-signout', 'unregistered-landing']) {
      await t.test(`login false positive: ${loginCase}`, async () => {
        fixture.loginCase = loginCase;
        const before = fixture.received.length;
        const runtime = await createRuntime(playwright, chromium, fixture.overrides);
        const agent = new Agent(runtime);
        try {
          const result = await agent.command({ command: 'login', projects: [PROJECT], login_timeout_seconds: 1 });
          assert.equal(result.error, 'QB_LOGIN_TIMEOUT');
          assert.ok(fixture.received.slice(before).every(row => row.method === 'GET'));
          if (loginCase === 'unregistered-landing') {
            assert.deepEqual(fixture.received.slice(before).map(row => row.path), ['/signin']);
          }
        } finally { await agent.command({ command: 'close' }); fixture.loginCase = null; }
      });
    }
    await t.test('read redirected to different Successful build stays a read failure', async () => {
      const runtime = await createRuntime(playwright, chromium, fixture.overrides);
      const agent = new Agent(runtime);
      try {
        await login(agent);
        fixture.redirectRead = true;
        fixture.childStatus = 'Successful';
        const result = await agent.command({ command: 'read', path: '/build/1193467/overview' });
        assert.equal(result.error, 'QB_READ_REDIRECTED');
        const mapped = execFileSync(`${ROOT}.venv/bin/python`, ['-c',
          'import sys; from ci_triage.qb_browser import decode_response,QbBrowserError\ntry: decode_response(sys.stdin.read(),command="read",submit_sent=False)\nexcept QbBrowserError as e: print(e.code)'],
          { input: JSON.stringify(result), encoding: 'utf8', cwd: ROOT });
        assert.equal(mapped.trim(), 'QB_FETCH_FAILED');
        await writeFile(`${root}/redirect-response.json`, JSON.stringify(result));
      } finally { await agent.command({ command: 'close' }); fixture.redirectRead = false; }
    });
    await t.test('window.open disabled and foreign iframe denied before request', async () => {
      const runtime = await createRuntime(playwright, chromium, fixture.overrides);
      const agent = new Agent(runtime);
      try {
        await login(agent);
        const before = fixture.received.length;
        const blocked = await runtime.page.evaluate(() => {
          const child = window.open('https://outside.invalid/');
          const frame = document.createElement('iframe');
          frame.src = 'https://outside.invalid/build/999'; document.body.append(frame);
          return child === null;
        });
        assert.ok(blocked);
        await new Promise(resolve => setTimeout(resolve, 500));
        assert.equal(fixture.received.length, before);
        assert.ok(runtime.trace.some(row => row.action === 'DENIED'));
        await writeFile(`${root}/window-frame-trace.json`, JSON.stringify(runtime.trace, null, 2));
      } finally { await agent.command({ command: 'close' }); }
    });
    await t.test('server callback code inconsistent with DOM is denied without a server POST', async () => {
      const runtime = await createRuntime(playwright, chromium, fixture.overrides);
      const agent = new Agent(runtime);
      fixture.callbackMismatch = true;
      try {
        await login(agent);
        assert.equal((await agent.command({ command: 'open_form', overview_id: 1917 })).ok, true);
        const before = fixture.received.length;
        const result = await agent.command({ command: 'fill', fields: VALUES });
        assert.equal(result.error, 'QB_FORM_CHANGED');
        assert.equal(agent.policy.released, false);
        assert.ok(result.diagnostic);
        assert.equal(fixture.received.length, before);
        await writeFile(`${root}/inconsistent-callback.json`, JSON.stringify({ result, trace: runtime.trace }, null, 2));
      } finally { await agent.command({ command: 'close' }); fixture.callbackMismatch = false; }
    });
    await writeFile(`${root}/server-requests.json`, JSON.stringify(fixture.received, null, 2));
    assert.deepEqual(fixture.errors, []);
  } finally {
    await fixture.close();
    if (!process.env.P5Q_C5A_EVIDENCE) await rm(root, { recursive: true, force: true });
  }
});
