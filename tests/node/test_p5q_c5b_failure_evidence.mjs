import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { mkdir, mkdtemp, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import test from 'node:test';
import { Agent, AgentError, createRuntime } from '../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';
import { rehearse } from '../../docs/clang-fix-campaign/spikes/p5q_fill_rehearsal.mjs';
import { comparePages } from '../../docs/clang-fix-campaign/spikes/p5q_compare_raw_active.mjs';
import { evidenceSession, errorCode, EvidenceError, reportFailure, ROOT }
  from '../../docs/clang-fix-campaign/spikes/p5q_c5_tools.mjs';
import { fakeQuickBuild } from './p5q_fake_quickbuild.mjs';

const [playwright, chromium] = process.argv.slice(2);
const privateText = 'DO_NOT_ARCHIVE_raw_exception_password_86753';
const target = 'local/fixture@' + 'c'.repeat(40);

async function verifyFiles(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = `${directory}/${entry.name}`;
    if (entry.isDirectory()) { await verifyFiles(path); continue; }
    const contents = await readFile(path, 'utf8');
    for (const banned of [privateText, 'synthetic-password', 'JSESSIONID_8810=', 'LocalTester']) {
      assert.ok(!contents.includes(banned), `${entry.name}: prohibited content`);
    }
    execFileSync(`${ROOT}.venv/bin/python`, ['-c',
      'from pathlib import Path; import sys; from ci_triage.qb_redact import PageRedactor; PageRedactor().check_written(Path(sys.argv[1]))', path],
    { cwd: ROOT });
  }
}

test('C5b finally evidence and noninterfering observers on local HTTPS', { timeout: 170000 }, async t => {
  const root = process.env.P5Q_C5B_EVIDENCE ?? await mkdtemp('/tmp/p5q-c5b-failures-');
  await mkdir(root, { recursive: true });
  const outcomes = [];
  try {
    for (const mode of ['login_timeout', 'open_form', 'third_field', 'identity_goto', 'identity_snapshot',
      'adapter', 'write_failure', 'normal', 'assembly', 'compare_read_failure']) {
      await t.test(mode, async () => {
        const output = `${root}/${mode}`; await mkdir(output);
        if (mode === 'write_failure') await mkdir(`${output}/run.json`);
        const fixture = await fakeQuickBuild();
        fixture.extraField = mode === 'open_form';
        fixture.callbackMismatchAt = mode === 'third_field' ? 2 : null;
        let agent, runtime, caught;
        const stderr = [];
        try {
          await evidenceSession(output, async () => {
            runtime = await createRuntime(playwright, chromium, fixture.overrides);
            agent = new Agent(runtime);
            const command = agent.command.bind(agent);
            // Only the test simulates the human login. The production method is unchanged.
            agent.command = async input => {
              if (input.command !== 'login') return command(input);
              const pending = command({ ...input, login_timeout_seconds: mode === 'login_timeout' ? 1 : 20 });
              if (mode !== 'login_timeout') {
                await agent.page.locator('input[name=user]').fill('synthetic');
                await agent.page.locator('input[type=password]').fill('synthetic-password');
                await agent.page.getByRole('button', { name: 'Login', exact: true }).click();
              }
              return pending;
            };
            return agent;
          }, async (active, record) => {
            const passive = active.passive.bind(active);
            if (mode.startsWith('identity_')) {
              active.passive = async (...args) => {
                if ((mode === 'identity_goto' && args[1] === null)
                  || (mode === 'identity_snapshot' && args[1] !== null)) throw new TypeError(privateText);
                return passive(...args);
              };
            }
            if (mode === 'adapter') {
              const snapshot = active.snapshot.bind(active);
              let injected = false;
              active.snapshot = async () => {
                if (!injected) {
                  injected = true;
                  // Deliver only to the observer, not the real guard's CDP event handler.
                  const listener = runtime.guards.root.listeners('Fetch.requestPaused').at(-1);
                  assert.doesNotThrow(() => listener({ request: { url: 'not-a-url ' + privateText } }));
                }
                return snapshot();
              };
            }
            if (mode === 'assembly') {
              const snapshot = active.snapshot.bind(active);
              active.snapshot = async () => {
                const value = await snapshot();
                if (record.stage === 'fill') value.rows = new Proxy(value.rows, { get(rows, key) {
                  if (key === 'find') throw new TypeError(privateText);
                  return Reflect.get(rows, key);
                } });
                return value;
              };
            }
            if (mode === 'compare_read_failure') {
              fixture.redirectRead = true;
              return comparePages(active, ['/build/1193467/overview'], output, record);
            }
            return rehearse(active, target, output, record);
          });
        } catch (error) { caught = error; reportFailure(error, { write: value => stderr.push(value) }); }
        finally { await fixture.close(); }
        assert.equal(runtime.browser.isConnected(), false);
        assert.equal(existsSync(runtime.profile), false);
        assert.equal(fixture.submissions.length, 0);
        assert.equal(fixture.builds, 0);
        assert.ok(!stderr.join('').includes(privateText));
        let record;
        if (mode === 'write_failure') {
          assert.equal(caught.code, 'EVIDENCE_WRITE_FAILED');
          assert.deepEqual(stderr, ['EVIDENCE_WRITE_FAILED\n']);
          assert.equal((await readdir(`${output}/run.json`)).length, 0);
        } else {
          record = JSON.parse(await readFile(`${output}/run.json`, 'utf8'));
          if (mode === 'normal') {
            assert.equal(caught, undefined);
            assert.equal(record.status, 'PASSED');
          } else if (['identity_goto', 'identity_snapshot', 'adapter'].includes(mode)) {
            assert.equal(caught.code, 'EVIDENCE_INCOMPLETE');
            assert.equal(record.status, 'EVIDENCE_INCOMPLETE');
            assert.equal(record.result.ok, true, 'production fill must complete');
            const wanted = mode === 'adapter' ? 'ADAPT_FAILED' : 'IDENTITY_COUNT_FAILED';
            assert.ok(record.observer_errors.some(row => row.kind === wanted));
            assert.ok(record.observer_errors.every(row => row.code === (mode === 'adapter' ? 'ADAPT_FAILED' : 'TypeError')));
          } else {
            const [stage, code] = { login_timeout: ['login', 'QB_LOGIN_TIMEOUT'], open_form: ['open_form', 'QB_FORM_CHANGED'],
              third_field: ['fill', 'QB_FORM_CHANGED'], assembly: ['assemble', 'TypeError'],
              compare_read_failure: ['read', 'QB_READ_REDIRECTED'] }[mode];
            assert.deepEqual(record.failure, { stage, code });
            assert.equal(record.stage, stage);
            assert.equal(record.status, 'STOPPED');
            assert.deepEqual(stderr, [`EVIDENCE_STOPPED stage=${stage} code=${code}\n`]);
          }
          if (record.result?.ok && mode !== 'assembly') {
            assert.equal(record.registrations.length, 12);
            assert.ok(record.registrations.every(row => row.allowed === 1 && row.denied === 0 && row.response_status.length === 1 && row.response_status[0] === 200));
            assert.equal(record.form_action_releases, 0);
            assert.equal(record.release_state, 'not_released');
          }
          if (mode === 'assembly') {
            assert.equal(record.result.ok, true);
            assert.ok(record.snapshots.length >= 12);
            assert.equal(record.callbacks.filter(row => row.method === 'POST' && row.status === null && row.allowed).length, 12);
          }
          if (['open_form', 'third_field'].includes(mode)) {
            assert.ok(record.responses.some(row => row.error === 'QB_FORM_CHANGED' && row.has_diagnostic));
            assert.deepEqual(record.diagnostic_files, ['diagnostic.html', 'diagnostic.json']);
            assert.ok(existsSync(`${output}/diagnostic.html`));
            assert.ok(existsSync(`${output}/diagnostic.json`));
            assert.ok(record.snapshots.length > 0);
          }
          if (mode === 'third_field') {
            assert.equal(record.registrations.length, 3);
            assert.equal(record.registrations[2].field, 'BUILD_REFERENCE');
            assert.equal(record.registrations[2].denied, 1);
            assert.equal(fixture.received.filter(row => row.method === 'POST' && row.path.includes('IBehaviorListener')).length, 2);
          }
        }
        await writeFile(`${output}/server-requests.json`, JSON.stringify(fixture.received, null, 2) + '\n');
        await writeFile(`${output}/terminal.txt`, stderr.join(''));
        await verifyFiles(output);
        outcomes.push({ mode, stage: record?.stage ?? 'write', code: record?.failure?.code ?? caught?.code ?? null,
          status: record?.status ?? 'EVIDENCE_WRITE_FAILED', received: fixture.received.length,
          form_action_releases: record?.form_action_releases ?? null });
      });
    }
    await writeFile(`${root}/outcomes.json`, JSON.stringify(outcomes, null, 2) + '\n');
  } finally { if (!process.env.P5Q_C5B_EVIDENCE) await rm(root, { recursive: true, force: true }); }
});

test('exception codes never come from arbitrary exception text', () => {
  assert.equal(errorCode(new Error('LOOKS_FIXED_BUT_UNTRUSTED')), 'Error');
  assert.equal(errorCode(new TypeError(privateText)), 'TypeError');
  assert.equal(errorCode(new EvidenceError('FIXED_TOOL_ERROR')), 'FIXED_TOOL_ERROR');
  assert.equal(errorCode(new AgentError('QB_FORM_CHANGED')), 'QB_FORM_CHANGED');
  assert.equal(errorCode(new AgentError(privateText)), 'AgentError');
});
