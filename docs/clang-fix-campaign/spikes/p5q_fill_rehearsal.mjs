// Rehearsal only. The only command sequence is login/open_form/fill/close.
import { randomUUID } from 'node:crypto';
import { parseArgs } from 'node:util';
import { pathToFileURL } from 'node:url';
import { Agent, createRuntime, FIELDS, formFacts } from '../../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';
import { PROJECT, DEFAULTS, assertRuntime, newOutput, observeCallbacks,
  EvidenceError, withEvidence, evidenceSession, reportFailure } from './p5q_c5_tools.mjs';

export async function rehearse(agent, target, output, record = null) {
  if (!record) return withEvidence(output, inner => rehearse(agent, target, output, inner));
  record.agent = agent;
  if (!/^[^\s@]+@[0-9a-f]{40}$/.test(target)) throw new EvidenceError('INVALID_TARGET');
  const observed = observeCallbacks(agent.runtime);
  record.data.callbacks = observed.requests;
  const snapshots = [];
  const original = agent.snapshot.bind(agent);
  const originalGoto = agent.page.goto.bind(agent.page);
  const recordIdentity = async (form = undefined) => {
    try {
      const facts = form === undefined ? null : { ...formFacts(form, PROJECT.project_name),
        base: form?.base ?? null, action: form?.action ?? null };
      const raw = await agent.trusted.run(document => document.documentElement.outerHTML);
      const redacted = await agent.passive(raw, facts);
      record.data.page_identity_counts.push({ page: agent.page.url(), outside_identity_count: redacted.outside_identity_count });
      if (form !== undefined) record.data.snapshots.push({ stage: record.stage, facts: redacted.facts });
    } catch (error) {
      record.incomplete('IDENTITY_COUNT_FAILED', error);
      // Counts alone remain safe even when the auxiliary redaction failed.
      if (form !== undefined) record.data.snapshots.push({ stage: record.stage,
        row_count: form?.rows?.length ?? 0, facts_unavailable: true });
    }
  };
  agent.page.goto = async (...args) => {
    const response = await originalGoto(...args);
    await recordIdentity();
    return response;
  };
  agent.snapshot = async () => {
    const form = await original();
    snapshots.push(form);
    await recordIdentity(form);
    return form;
  };
  let start = null;
  const fields = { BUILD_TYPE: 'Full', REPO_TYPE: 'ALL', BUILD_REFERENCE: 'Ref. Snapshot',
    SNAPSHOT_NUM: '@freeze', PROJECT_BRANCH: 'tizen_base', 'Immediate Stop With Error': true,
    CHILD_CONFIGURATIONS: ['standard-armv7l:aarch64:x86_64'], 'Build Package List': target,
    'Add Package List': '', 'Remove Package List': '', TARGET_IMAGE: [],
    'BUILD NOTES': `clang-fix-campaign request=rehearsal-${randomUUID().replaceAll('-', '')}` };
  record.data.request_id = fields['BUILD NOTES'].split('=')[1];
  try {
    await record.command({ command: 'open_form', overview_id: PROJECT.overview_id });
    start = snapshots.length;
    const result = await record.command({ command: 'fill', fields });
    record.data.result = { ok: result.ok, readback: result.readback, fingerprint: result.fingerprint,
      snapshot_option_count: result.snapshot_option_count, released: result.released };
    assertRuntime(agent.runtime);
  } catch (error) { record.fail(error); }
  finally {
    observed.close(); agent.snapshot = original; agent.page.goto = originalGoto;
    for (const error of observed.errors) record.incomplete('ADAPT_FAILED', new EvidenceError(error.action));
    record.stage = 'assemble';
    record.data.release_state = agent.policy.released ? 'released' : 'not_released';
    record.data.form_action_releases = observed.actions.filter(row => row.allowed).length;
    record.data.final_action = snapshots.at(-1)?.action;
    record.data.registrations = (start === null ? [] : snapshots.slice(start, start + FIELDS.length)).map((form, i) => {
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
    if (agent.policy.released || record.data.form_action_releases) throw new EvidenceError('UNEXPECTED_RELEASE');
  }
  return record.data;
}

async function main() {
  const { values } = parseArgs({ options: { target: { type: 'string' }, output: { type: 'string' } } });
  if (!values.output || !/^[^\s@]+@[0-9a-f]{40}$/.test(values.target ?? '')) throw new EvidenceError('INVALID_ARGS');
  await newOutput(values.output);
  await evidenceSession(values.output, async () => new Agent(await createRuntime(DEFAULTS.playwright, DEFAULTS.chromium)),
    (agent, record) => rehearse(agent, values.target, values.output, record));
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch(error => { reportFailure(error); process.exitCode = 1; });
}
