import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import test from 'node:test';
import { Agent, createRuntime, pathShape } from '../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';
import { fakeQuickBuild, PROJECT } from './p5q_fake_quickbuild.mjs';

const [playwright, chromium] = process.argv.slice(2);
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
for (const scenario of ['signin', 'unregistered', 'no-signout', 'closed']) {
  test(`C6 login facts: ${scenario}`, { timeout: 45000 }, async () => {
    const fixture = await fakeQuickBuild();
    fixture.loginCookie = 'synthetic_private_session';
    const runtime = await createRuntime(playwright, chromium, fixture.overrides);
    const agent = new Agent(runtime);
    let result;
    try {
      if (scenario === 'unregistered') fixture.loginRedirect = '/not-registered?synthetic_query_value';
      if (scenario === 'no-signout') fixture.dashboardNoSignOut = true;
      const pending = agent.command({ command: 'login', projects: [PROJECT], login_timeout_seconds: 7 });
      await runtime.page.locator('input[type=password]').waitFor();
      // Wait for a real production poll before acting as the synthetic person.
      const deadline = Date.now() + 4000;
      while (!(agent.lastLoginCheck?.checks > 0) && Date.now() < deadline) await sleep(20);
      assert.ok(agent.lastLoginCheck.checks > 0);
      if (scenario === 'closed') await runtime.page.close();
      else if (scenario !== 'signin') {
        await runtime.page.locator('input[name=user]').fill('synthetic_private_account');
        await runtime.page.locator('input[type=password]').fill('synthetic_private_password');
        await runtime.page.getByRole('button', { name: 'Login', exact: true }).click().catch(() => {});
      }
      result = await pending;
      assert.equal(result.error, scenario === 'closed' ? 'QB_LOGIN_ABORTED' : 'QB_LOGIN_TIMEOUT');
      assert.equal(result.ok, false);
      const facts = result.login_facts;
      assert.deepEqual(Object.keys(facts).sort(), ['final_path_shape', 'on_signin', 'password_present',
        'sign_out_present', 'checks', 'login_posts_released', 'login_channel_closed', 'denied'].sort());
      assert.ok(Number.isInteger(facts.checks) && facts.checks > 0);
      assert.equal(facts.login_posts_released, ['signin', 'closed'].includes(scenario) ? 0 : 1);
      assert.equal(facts.login_channel_closed, !['signin', 'closed'].includes(scenario));
      assert.equal(facts.sign_out_present, false);
      assert.equal(facts.on_signin, ['signin', 'closed'].includes(scenario));
      assert.equal(facts.password_present, ['signin', 'closed'].includes(scenario));
      assert.equal(facts.final_path_shape, pathShape(new URL(runtime.page.url()).pathname));
      if (scenario === 'signin' || scenario === 'closed') assert.equal(facts.final_path_shape, '/signin');
      if (scenario === 'no-signout') assert.equal(facts.final_path_shape, '/dashboard');
      const denied = {};
      for (const row of runtime.trace) if (row.phase === 'login' && row.action === 'DENIED') denied[row.path] = (denied[row.path] ?? 0) + 1;
      assert.deepEqual(facts.denied, denied);
      if (scenario === 'unregistered') {
        assert.ok(facts.denied['<other>'] >= 1);
        assert.ok(!fixture.received.some(row => row.path.startsWith('/not-registered')));
      } else assert.deepEqual(facts.denied, {});
      assert.equal(fixture.submissions.length, 0);
      for (const secret of ['synthetic_private_account', 'synthetic_private_password', 'synthetic_private_session', 'synthetic_query_value']) {
        assert.ok(!JSON.stringify(result).includes(secret));
      }
      console.log(JSON.stringify({ scenario, result }));
    } finally {
      await runtime.close();
      if (process.env.P5Q_C6_FIX_EVIDENCE) {
        await mkdir(process.env.P5Q_C6_FIX_EVIDENCE, { recursive: true });
        await writeFile(`${process.env.P5Q_C6_FIX_EVIDENCE}/login-${scenario}.json`, JSON.stringify({
          result, trace: runtime.trace, received: fixture.received,
        }, null, 2));
      }
      await fixture.close();
    }
  });
}
