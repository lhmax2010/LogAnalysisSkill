// Rehearsal only. The only command sequence is login/open_form/fill/close.
import { randomUUID } from 'node:crypto';
import { parseArgs } from 'node:util';
import { pathToFileURL } from 'node:url';
import { Agent, createRuntime, FIELDS } from '../../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';
import { PROJECT, DEFAULTS, assertRuntime, newOutput, writeJSON, observeCallbacks } from './p5q_c5_tools.mjs';

export async function rehearse(agent, target, output) {
  if (!/^[^\s@]+@[0-9a-f]{40}$/.test(target)) throw new Error('INVALID_TARGET');
  const observed = observeCallbacks(agent.runtime);
  const snapshots = [];
  const identityCounts = [];
  const original = agent.snapshot.bind(agent);
  const originalGoto = agent.page.goto.bind(agent.page);
  const recordIdentity = async () => {
    const raw = await agent.trusted.run(document => document.documentElement.outerHTML);
    const redacted = await agent.passive(raw);
    identityCounts.push({ page: agent.page.url(), outside_identity_count: redacted.outside_identity_count });
  };
  agent.page.goto = async (...args) => {
    const response = await originalGoto(...args);
    await recordIdentity();
    return response;
  };
  agent.snapshot = async () => {
    const form = await original();
    snapshots.push(form);
    await recordIdentity();
    return form;
  };
  try {
    const opened = await agent.command({ command: 'open_form', overview_id: PROJECT.overview_id });
    if (!opened.ok) throw new Error(opened.error);
    const start = snapshots.length;
    const request = 'rehearsal-' + randomUUID().replaceAll('-', '');
    const fields = { BUILD_TYPE: 'Full', REPO_TYPE: 'ALL', BUILD_REFERENCE: 'Ref. Snapshot',
      SNAPSHOT_NUM: '@freeze', PROJECT_BRANCH: 'tizen_base', 'Immediate Stop With Error': true,
      CHILD_CONFIGURATIONS: ['standard-armv7l:aarch64:x86_64'], 'Build Package List': target,
      'Add Package List': '', 'Remove Package List': '', TARGET_IMAGE: [], 'BUILD NOTES': `clang-fix-campaign request=${request}` };
    const result = await agent.command({ command: 'fill', fields });
    assertRuntime(agent.runtime);
    const registrations = snapshots.slice(start, start + FIELDS.length).map((form, i) => {
      const row = form.rows.find(row => row.label === FIELDS[i]);
      const control = row.controls.find(c => c.role === 'recorder') ?? row.controls[0];
      const initial = control.tag === 'SELECT' ? control.options.filter(o => o.selected).map(o => o.text)
        : control.type === 'checkbox' ? control.checked : control.value;
      const requests = observed.requests.filter(item => item.window === i && item.method === 'POST');
      return { field: FIELDS[i], callback: control.callback, action: form.action, page: form.base,
        initial, expected: fields[FIELDS[i]],
        value_already_equal: fields[FIELDS[i]] === '@freeze' || (control.tag === 'SELECT'
          ? initial.length === 1 && initial[0] === fields[FIELDS[i]]
          : control.role === 'recorder' ? control.value === (FIELDS[i] === 'TARGET_IMAGE' ? '' : Buffer.from(fields[FIELDS[i]][0]).toString('hex'))
            : initial === fields[FIELDS[i]]),
        allowed: requests.filter(item => item.status === null && item.allowed).length,
        denied: requests.filter(item => item.status === null && item.allowed === false).length,
        response_status: requests.filter(item => item.status !== null).map(item => item.status),
        random: requests.filter(item => item.status === null).map(item => item.random) };
    });
    const releases = observed.actions.filter(row => row.allowed).length;
    if (agent.policy.released || releases) throw new Error('UNEXPECTED_RELEASE');
    const record = { request_id: request, registrations, callbacks: observed.requests, result,
      page_identity_counts: identityCounts,
      final_action: snapshots.at(-1)?.action, trace: agent.runtime.trace,
      release_state: 'not_released', form_action_releases: releases };
    await writeJSON(`${output}/run.json`, record);
    if (!result.ok) throw new Error(result.error);
    return record;
  } finally { observed.close(); agent.snapshot = original; agent.page.goto = originalGoto; }
}

async function main() {
  const { values } = parseArgs({ options: { target: { type: 'string' }, output: { type: 'string' } } });
  if (!values.output || !/^[^\s@]+@[0-9a-f]{40}$/.test(values.target ?? '')) throw new Error('INVALID_ARGS');
  await newOutput(values.output);
  const runtime = await createRuntime(DEFAULTS.playwright, DEFAULTS.chromium);
  const agent = new Agent(runtime);
  try {
    const login = await agent.command({ command: 'login', projects: [PROJECT], login_timeout_seconds: 600 });
    if (!login.ok) throw new Error(login.error);
    await rehearse(agent, values.target, values.output);
  } finally { await agent.command({ command: 'close' }); }
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch(() => { process.stderr.write('EVIDENCE_STOPPED\n'); process.exitCode = 1; });
}
