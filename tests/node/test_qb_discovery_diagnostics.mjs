import assert from 'node:assert/strict';
import test from 'node:test';
import { Agent, Policy } from '../../tizen-qb-verify/scripts/tizen_qb_verify/qb_browser_agent.mjs';
import { DiscoveryScope, DiscoveryError, discoveryFailure, DISCOVERY_PAGE_KINDS, DISCOVERY_CHECKS,
  DISCOVERY_COUNT_KEYS } from '../../tizen-qb-verify/scripts/tizen_qb_verify/qb_discovery_scope.mjs';

const project = { overview_id: 1917, configuration_path: 'root/Test/RBS/TRIGGER' };
const cell = (text, links = []) => ({ text, links });
const facts = (child = false) => {
  const path = project.configuration_path.replace('TRIGGER', child ? 'build' : 'TRIGGER');
  return { title: 'QuickBuild - ' + path, crumbs: path.split('/').map(text => ({ text, linked: false })),
    copies: [path], welcome: [], tables: [], recent: [], iframes: [], details: [] };
};
function fixture(kind = 'report') {
  const scope = new DiscoveryScope(project, '101');
  scope.entries.set('/target', { kind: { parent_overview: 'overview', child_overview: 'overview',
    parent_variables: 'variables', child_variables: 'variables', report_entry: 'report-entry' }[kind] ?? kind,
    build: '102', child: kind.startsWith('child') });
  scope.builds.set('102', { child: !kind.startsWith('parent'), parent: '101', variables: new Map(), report: '/target' });
  const value = facts(!kind.startsWith('parent'));
  value.details = [{ headers: ['name', 'standard armv7l', 'standard aarch64', 'standard x86_64'],
    rows: [[cell('zlib'), cell('failed', [{ text: 'failed', href: 'logfiles/standard/armv7l/zlib.txt' }]), cell('succeeded'), cell('succeeded')]] }];
  return { scope, value };
}
async function reply(scope, value) {
  const policy = new Policy(); policy.discoveryScope = scope;
  const agent = new Agent({ policy, trace: [], page: {} }); agent.state = 'ready';
  agent.discoveryRead = async () => scope.consume('/target', value);
  return agent.command({ command: 'discovery_read', path: '/target' });
}

const cases = [
  ['parent_overview', 'identity_mismatch', f => { f.title = 'private title ?cookie=secret'; }],
  ['parent_overview', 'child_link_count', f => { f.tables = [{ headers: ['Repository-Architecture', 'QB Build URL', 'Build Result', 'Build Profiling'], rows: [[cell(''), cell(''), cell(''), cell('')]] }]; }],
  ['parent_variables', 'variables_missing', () => {}],
  ['child_variables', 'variables_missing', () => {}],
  ['child_overview', 'identity_mismatch', f => { f.copies = []; }],
  ['report_entry', 'iframe_count', () => {}],
  ['report_entry', 'link_path', f => { f.iframes = ['https://evil.invalid/path?secret']; }],
  ['report', 'header_missing', f => { f.details[0].headers = []; }],
  ['report', 'header_duplicate', f => { f.details[0].headers[2] = f.details[0].headers[1]; }],
  ['report', 'package_duplicate', f => { f.details[0].rows.push(f.details[0].rows[0]); }],
  ['report', 'cell_multi_link', f => { f.details[0].rows[0][1].links.push({ text: 'failed', href: '?private' }); }],
  ['report', 'package_name', f => { f.details[0].rows[0][0].text = 'private invalid name'; }],
  ['report', 'cell_count', f => { f.details[0].rows[0].pop(); }],
  ['report', 'table_count', f => { f.details = []; }],
  ['report', 'link_text', f => { f.details[0].rows.push([cell('zlib - details'), cell(''), cell(''), cell('')]); }],
  ['configuration', 'identity_mismatch', f => { f.copies = []; }],
];
for (const [kind, check, change] of cases) test(`${kind}: first check ${check}`, async () => {
  const { scope, value } = fixture(kind); change(value);
  const before = [...scope.entries.keys()];
  const response = await reply(scope, value);
  assert.equal(response.ok, false);
  assert.equal(response.page_kind, kind);
  assert.equal(response.first_failed_check, check);
  assert.deepEqual([...scope.entries.keys()], before);
  assert.ok(Object.keys(response.counts).every(k => DISCOVERY_COUNT_KEYS.includes(k)));
  assert.ok(Object.values(response.counts).every(v => Number.isSafeInteger(v) && v >= 0));
  for (const privateValue of ['private', 'secret', 'evil.invalid', 'cookie', '?']) assert.ok(!JSON.stringify(response).includes(privateValue));
});
test('log arch gate stays closed and emits arch_unmapped', () => {
  const { scope } = fixture();
  scope.builds.get('102').packages = [{ spec_name: 'zlib', primary_arch: null }];
  assert.throws(() => scope.log('102', 'zlib'), e => e.page_kind === 'log' && e.first_failed_check === 'arch_unmapped');
  assert.equal(scope.usedLogs.size, 0);
});
test('build identity failure keeps its error code and returns fixed discovery facts', async () => {
  const { scope } = fixture('child_overview');
  scope.entries.set('/build/102/overview', { kind: 'overview', child: true, build: '102' });
  const policy = new Policy(); policy.discoveryScope = scope;
  const agent = new Agent({ policy, trace: [], page: {} }); agent.state = 'ready';
  agent.discoveryNavigate = async () => 'private page'; agent.buildId = async () => '999';
  const response = await agent.command({ command: 'discovery_read', path: '/build/102/overview' });
  assert.deepEqual(response, { ok: false, error: 'QB_READ_ID_MISMATCH', page_kind: 'child_overview',
    first_failed_check: 'identity_mismatch', counts: {} });
});
for (const check of DISCOVERY_CHECKS) test(`closed diagnostic response ${check}`, () => {
  const error = new DiscoveryError('DISCOVERY_REPORT_AMBIGUOUS', 'REPORT_STRUCTURE');
  error.first_failed_check = check; error.counts = { actual_count: 2, secret: 'private' };
  const result = discoveryFailure(error, 'report');
  assert.equal(result.first_failed_check, check); assert.deepEqual(result.counts, { actual_count: 2 });
});
test('diagnostic enums exported for driver parity', () => {
  console.log(JSON.stringify({ page_kinds: DISCOVERY_PAGE_KINDS, checks: DISCOVERY_CHECKS, count_keys: DISCOVERY_COUNT_KEYS }));
});
