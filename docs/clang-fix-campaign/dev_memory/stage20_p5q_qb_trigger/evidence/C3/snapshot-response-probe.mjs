// Zero network: exercise production fill and command with synthetic DOM snapshots.
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';

const { Agent, FIELDS, ORIGIN, Policy, formFacts } = await import(pathToFileURL(resolve(
  'tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs',
)));
const callback = `${ORIGIN}/wicket/page?50-2.IBehaviorListener.0-form-field`;
const duplicateFirstFreeze = process.argv.includes('--duplicate-first-freeze');
const requested = Object.fromEntries(FIELDS.map(name => [name, name]));
Object.assign(requested, {
  SNAPSHOT_NUM: duplicateFirstFreeze ? '@freeze' : 'frozen-snapshot',
  CHILD_CONFIGURATIONS: ['standard-armv7l:aarch64:x86_64'], TARGET_IMAGE: [],
  'Immediate Stop With Error': true, 'Build Package List': 'pkg/name@abc',
  'BUILD NOTES': 'clang-fix-campaign request=00000000000000000000000000000001',
  'Add Package List': '', 'Remove Package List': '',
});
const results = [];
for (const current of ['current-snapshot-A', 'current-snapshot-B']) {
  const form = {
    heading: true, base: `${ORIGIN}/wicket/page?50`,
    action: `${ORIGIN}/wicket/page?50-2.IFormSubmitListener-form`,
    rows: [{ label: 'PROJECT_NAME', viewers: ['Tizen'], controls: [] },
      ...FIELDS.map(label => ({ label, viewers: [], controls:
        ['CHILD_CONFIGURATIONS', 'TARGET_IMAGE'].includes(label)
          ? ['recorder', 'choices', 'selection'].map(role => ({ role, value: '', options: [],
            callback: `wicketAjaxPost('${callback}', 0)` }))
          : [{ tag: label === 'SNAPSHOT_NUM' ? 'SELECT' : 'INPUT', type: 'text',
            value: label, options: label === 'SNAPSHOT_NUM'
              ? [{ text: current, value: current, selected: true },
                ...(duplicateFirstFreeze ? [{ text: current, value: 'other', selected: false }] : [])] : [],
            callback: `wicketAjaxPost('${callback}', 0)` }],
      }))],
  };
  const policy = new Policy();
  const agent = new Agent({ policy, page: {}, failure: null });
  agent.state = 'form';
  agent.currentProject = { project_name: 'Tizen' };
  agent.snapshot = async () => form;
  agent.diagnostic = async () => ({ html_redacted: '<form></form>', facts: formFacts(form, 'Tizen') });
  // The first three fields already equal their requested values. Only complete
  // their synthetic callbacks; production fill checks SNAPSHOT_NUM itself.
  agent.fieldRow = () => ({ locator: () => ({ locator: () => ({
    dispatchEvent: async () => {
      policy.fieldFinished = true;
      policy.lastActivity = Date.now() - 1500;
    },
  }) }) });
  const response = await agent.command({ command: 'fill', fields: requested });
  if (duplicateFirstFreeze) {
    assert.equal(response.error, 'QB_FORM_CHANGED');
    assert.equal(response.diagnostic.facts.first_failed_check, 'duplicate_option_text');
    assert.equal('snapshot_state' in response, false);
  } else assert.deepEqual(response, {
    ok: false, error: 'QB_FORM_VALUE_UNAVAILABLE', field: 'SNAPSHOT_NUM',
    released: false, snapshot_state: { selected: [current], option_count: duplicateFirstFreeze ? 2 : 1 },
  });
  assert.equal(agent.state, 'invalid');
  assert.equal(policy.released, false);
  results.push({ frozen: requested.SNAPSHOT_NUM, current_in_snapshot: current, response,
    form_state: agent.state, released: policy.released });
}
if (!duplicateFirstFreeze) assert.notDeepEqual(results[0].response, results[1].response);
console.log(JSON.stringify({ network_requests: 0, cases: results,
  distinct_current_values_produce_distinct_response: !duplicateFirstFreeze }, null, 2));
