// Additional offline acceptance vectors; archived HTML is parsed inertly, never navigated.
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
const load = path => import(pathToFileURL(resolve(path)).href);
const { DiscoveryScope, discoveryDOM } = await load('tizen-qb-verify/scripts/tizen_qb_verify/qb_discovery_scope.mjs');
const { Policy, TrustedPage, FrameOwnership } = await load('tizen-qb-verify/scripts/tizen_qb_verify/qb_browser_agent.mjs');
const { chromium } = await import(pathToFileURL(process.argv[2]).href);
const browser = await chromium.launch({ executablePath: process.argv[3], headless: true });
const checks = [];
const project = { overview_id: 1917, configuration_path: 'root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER' };
const network = [];
try {
  const context = await browser.newContext();
  await context.route('**/*', route => { network.push('blocked'); return route.abort(); });
  const page = await context.newPage();
  const raw = await readFile('docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C6b/raw-active-01/05.raw-redacted.html', 'utf8');
  const facts = await new TrustedPage(context, page).run(discoveryDOM, raw);
  const scope = new DiscoveryScope(project);
  const result = scope.consume('/overview/1917', facts);
  assert.ok(result.builds.length > 0 && result.builds.length <= 50);
  assert.ok(result.builds.every(b => scope.entries.has(`/build/${b.build_id}/overview`)));
  checks.push('archived Recent Builds six-column parse and exact registrations');
  for (const fault of ['identity', 'headers', 'duplicate-id', 'link-id', 'link-query', 'too-many']) {
    const value = structuredClone(facts), table = value.recent[0][0];
    if (fault === 'identity') value.copies = ['root/other/RBS/TRIGGER'];
    if (fault === 'headers') table.headers.pop();
    if (fault === 'duplicate-id') table.rows.push(table.rows[0]);
    if (fault === 'link-id') table.rows[0][1].links.find(a => a.href.startsWith('/build/')).href = '/build/999999';
    if (fault === 'link-query') table.rows[0][1].links.find(a => a.href.startsWith('/build/')).href += '?1';
    if (fault === 'too-many') table.rows = Array(51).fill(table.rows[0]);
    const candidate = new DiscoveryScope(project);
    assert.throws(() => candidate.consume('/overview/1917', value));
    assert.deepEqual([...candidate.entries.keys()], ['/overview/1917']);
    checks.push(`Recent Builds refuses ${fault} before registrations`);
  }
  const policy = new Policy(); policy.phase = 'read'; policy.discoveryScope = scope;
  scope.entries.set('/build/102/html_report', { kind: 'report-entry', build: '102' });
  const metadata = { protocol: 'https:', host: 'quickbuild.tizen.org', path: '/build/102/html_report',
    query: '', method: 'GET', resource_type: 'Document', response_status: null, redirect_source: null };
  for (const patch of [{ method: 'HEAD' }, { path: '/build/102/html_report/x' },
    { path: '/build/102/html_reporu' }, { query: '0-1.ILinkListener-form-stop' },
    { resource_type: 'WebSocket' }, { path: '/wicket/page', query: '1-1.IFormSubmitListener-form' }]) {
    assert.equal(policy.allow({ ...metadata, ...patch }), false);
    checks.push(`exact report refusal ${JSON.stringify(patch)}`);
  }
  for (const phase of ['login', 'idle', 'open_form', 'fill', 'submit']) {
    policy.phase = phase; assert.equal(policy.allow(metadata), false);
    checks.push(`report denied in ${phase}`);
  }
  const frames = new FrameOwnership({ frame: { id: 'main' } });
  assert.equal(frames.has('unknown'), false); checks.push('unknown frame rejected');
  const childPath = project.configuration_path.replace(/TRIGGER$/, 'build');
  const child = { ...facts, title: 'QuickBuild - ' + childPath, copies: [childPath],
    crumbs: childPath.split('/').map(text => ({ text, linked: false })), welcome: [], tables: [] };
  const cell = text => ({ text, links: [] });
  for (const iframes of [[], ['/download/102/html/HTML REPORT/index.html', '/download/102/html/HTML REPORT/index.html']]) {
    const candidate = new DiscoveryScope(project, '102');
    candidate.consume('/build/102/overview', child);
    candidate.consume('/build/102/variables', { ...child, tables: [{ headers: ['Name', 'Display Name', 'Value'], rows: [
      [cell('TRIGGER_ID'), cell(''), cell('101')],
    ] }] });
    assert.throws(() => candidate.consume('/build/102/html_report', { ...child, iframes }));
    assert.ok(![...candidate.entries.keys()].some(path => path.startsWith('/download/')));
    checks.push(`iframe cardinality ${iframes.length} denied before download registrations`);
  }
  assert.deepEqual(network, []);
  console.log(JSON.stringify({ passed: checks.length, failed: 0, checks, network_requests: 0, source: 'archived C6b HTML, inert isolated document' }, null, 2));
} finally { await browser.close(); }
