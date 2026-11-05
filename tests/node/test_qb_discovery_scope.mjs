import assert from 'node:assert/strict';
import test from 'node:test';
import { DiscoveryScope, exactDiscoveryURL, detailsPackages, redactDiscoveryText }
  from '../../tizen-qb-verify/scripts/tizen_qb_verify/qb_discovery_scope.mjs';
import { Policy } from '../../tizen-qb-verify/scripts/tizen_qb_verify/qb_browser_agent.mjs';

const base = 'https://quickbuild.tizen.org/download/102/html/HTML%20REPORT/index.html';
const cell = (text, href) => ({ text, links: href ? [{ text, href }] : [] });
const table = () => ({ headers: ['name', 'standard armv7l', 'standard aarch64', 'standard x86_64'],
  rows: [[cell('zlib'), cell('failed', 'logfiles/standard/armv7l/zlib.txt'), cell('succeeded'), cell('succeeded')]] });
const project = { overview_id: 1917, configuration_path: 'root/Test/RBS/TRIGGER', project_name: 'Test' };
const facts = (child = false) => {
  const path = project.configuration_path.replace('TRIGGER', child ? 'build' : 'TRIGGER');
  return { title: 'QuickBuild - ' + path, crumbs: path.split('/').map(text => ({ text, linked: false })),
    copies: [path], tables: [{ headers: ['Repository-Architecture', 'QB Build URL', 'Build Result', 'Build Profiling'],
      rows: [[cell('standard'), cell('102', '/build/102'), cell('FAILED'), cell('')]] }],
    welcome: ['Welcome! tester (Test Person)'], iframes: [], details: [], recent: [] };
};

for (const href of ['/download/102/html/HTML REPORT/index.html', '/download/102/html/HTML%20REPORT/index.html']) {
  test(`one canonical registration: ${href}`, () => assert.equal(exactDiscoveryURL(href, base, '102').href, base));
}
for (const href of ['../zlib.txt', 'logfiles/../zlib.txt', '/download/103/html/HTML REPORT/index.html',
  'https://other.invalid/download/102/html/x', 'http://quickbuild.tizen.org/download/102/html/x',
  'https://user@quickbuild.tizen.org/download/102/html/x', '/download/102/html/a%2fb',
  '/download/102/html/a%5cb', '/download/102/html/%2e%2e/x', '/download/102/html/%252e/x',
  ' logfiles/x', 'logfiles/x ', 'logfiles/x?1', 'logfiles/x#x', 'logfiles\\x', 'logfiles/\nx']) {
  test(`reject path ${JSON.stringify(href)}`, () => assert.throws(() => exactDiscoveryURL(href, base, '102')));
}
test('four columns, plain failed anchors and primary ordering', () => {
  const t = table(); t.rows[0][2] = cell('failed', 'logfiles/standard/aarch64/zlib.txt');
  assert.deepEqual(detailsPackages(t), [{ spec_name: 'zlib', failed_arches: ['standard-aarch64', 'standard-armv7l'],
    primary_arch: 'standard-aarch64', href: 'logfiles/standard/aarch64/zlib.txt' }]);
});
for (const change of ['headers', 'duplicate-header', 'duplicate-name', 'two-links', 'short-row']) {
  test(`ambiguous ${change}`, () => {
    const t = table();
    if (change === 'headers') t.headers = [];
    if (change === 'duplicate-header') t.headers[2] = t.headers[1];
    if (change === 'duplicate-name') t.rows.push(t.rows[0]);
    if (change === 'two-links') t.rows[0][1].links.push(t.rows[0][1].links[0]);
    if (change === 'short-row') t.rows[0].pop();
    assert.throws(() => detailsPackages(t), { code: 'DISCOVERY_REPORT_AMBIGUOUS' });
  });
}
test('unknown arch goes to arch gate without a log', () => {
  const t = table(); t.headers[1] = 'standard mips';
  assert.equal(detailsPackages(t)[0].primary_arch, null);
});
test('only verified document chain can register a primary log, once', () => {
  const scope = new DiscoveryScope(project, '101');
  assert.throws(() => scope.log('102', 'zlib'));
  scope.consume('/build/101/overview', facts());
  scope.consume('/build/102/overview', facts(true));
  const v = facts(true); v.tables = [{ headers: ['Name', 'Display Name', 'Value'], rows: [
    [cell('TRIGGER_ID'), cell(''), cell('101')],
    [cell('BUILD_PKG_LIST'), cell(''), cell('platform/upstream/zlib@' + 'a'.repeat(40))],
    [cell('PROJECT_BRANCH'), cell(''), cell('tizen_base')],
  ] }];
  scope.consume('/build/102/variables', v);
  const report = facts(true); report.iframes = ['/download/102/html/HTML REPORT/index.html'];
  scope.consume('/build/102/html_report', report);
  report.details = [table()];
  const result = scope.consume(new URL(base).pathname, report);
  assert.equal(result.packages[0].status, 'ok');
  assert.equal(result.packages[0].base_commit, 'a'.repeat(40));
  assert.equal(scope.log('102', 'zlib').path, '/download/102/html/HTML%20REPORT/logfiles/standard/armv7l/zlib.txt');
  assert.throws(() => scope.log('102', 'zlib'));
});
test('identity mismatch registers no downstream addresses', () => {
  const scope = new DiscoveryScope(project, '101'), value = facts(); value.copies = ['root/other'];
  assert.throws(() => scope.consume('/build/101/overview', value));
  assert.deepEqual([...scope.entries.keys()], ['/build/101/overview']);
});
test('scope-only html_report exception and exact closed GET grammar', () => {
  const p = new Policy(); p.phase = 'read';
  const m = { protocol: 'https:', host: 'quickbuild.tizen.org', path: '/build/102/html_report', query: '',
    method: 'GET', resource_type: 'Document', response_status: null, redirect_source: null };
  assert.equal(p.allow(m, '0'), false);
  p.discoveryScope = new DiscoveryScope(project, '101');
  p.discoveryScope.entries.set(m.path, { kind: 'report-entry', build: '102' });
  assert.equal(p.allow(m, '1'), true);
  for (const patch of [{ method: 'POST' }, { query: '1' }, { protocol: 'http:' }, { host: 'evil.invalid' },
    { path: '/build/102/log' }, { path: '/build/102/artifacts' }, { path: '/rest/builds' },
    { path: '/build/999/html_report' }, { redirect_source: 'other' }, { response_status: 307 }, { response_status: 308 }]) {
    assert.equal(p.allow({ ...m, ...patch }, 'reject'), false, JSON.stringify(patch));
  }
  p.phase = 'idle'; assert.equal(p.allow(m, 'idle'), false);
});
test('text identity and secret replacement leaves compiler diagnostics intact', () => {
  const text = 'Test Person tester testercode\nCookie: synthetic-cookie\nerror: undeclared variable';
  const redacted = redactDiscoveryText(text, new Set(['tester', 'Test Person']));
  assert.equal(redacted, '<USER> <USER> testercode\n<REDACTED>\nerror: undeclared variable');
});
