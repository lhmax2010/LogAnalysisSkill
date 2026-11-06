import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { TrustedPage } from '../../tizen-qb-verify/scripts/tizen_qb_verify/qb_browser_agent.mjs';
import { DiscoveryScope, discoveryDOM, detailsPackages } from '../../tizen-qb-verify/scripts/tizen_qb_verify/qb_discovery_scope.mjs';

const [playwright, executablePath] = process.argv.slice(2);
const { chromium } = await import(playwright);
const browser = await chromium.launch({ executablePath, headless: true });
const context = await browser.newContext({ serviceWorkers: 'block' });
let requests = 0;
await context.route('**/*', route => { requests++; return route.abort(); });
const page = await context.newPage();
const trusted = new TrustedPage(context, page);
const root = new URL('../../docs/clang-fix-campaign/dev_memory/stage21_campaign_skeleton/evidence/restore/discovery-capture/', import.meta.url);
const scope = new DiscoveryScope({ overview_id: 1917,
  configuration_path: 'root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER' }, '1204735');
try {
  const sequence = [
    ['/build/1204735/overview', 'live-02/02.response.html'],
    ['/build/1204735/variables', 'live-02/03.response.html'],
    ['/build/1204736/overview', 'live-02/04.response.html'],
    ['/build/1204736/variables', 'live-02/05.response.html'],
    ['/build/1204736/html_report', 'live-02/06.response.html'],
    ['/download/1204736/html/HTML%20REPORT/index.html', 'live-04/02.response.html'],
  ];
  let report;
  for (const [path, file] of sequence) {
    const raw = await readFile(new URL(file, root), 'utf8');
    const facts = await trusted.run(discoveryDOM, raw);
    if (file === 'live-02/02.response.html') assert.ok(raw.includes('</thea&lt;USER&gt;'));
    const result = scope.consume(path, facts);
    if (file === 'live-04/02.response.html') {
      report = facts.details[0];
      assert.equal(report.rows.length, 259);
      assert.equal(report.rows[238][0].text, 'toybox - details');
      assert.ok(!result.packages.some(p => p.spec_name.startsWith('toybox')));
      for (const name of ['zlib', 'libtirpc', 'elfutils']) assert.ok(result.packages.some(p => p.spec_name === name));
      assert.equal(scope.log('1204736', 'zlib').path, '/download/1204736/html/HTML%20REPORT/logfiles/standard/aarch64/zlib.txt');
    }
  }
  const original = JSON.stringify(report);
  assert.doesNotThrow(() => detailsPackages(report));
  assert.equal(JSON.stringify(report), original, 'never edit the archive facts');
  // Only the observed, link-free explanation of an immediately preceding
  // unresolvable package is ignored. Never hide links or duplicate packages.
  for (const mutation of ['orphan', 'other-name', 'has-link', 'failed-parent', 'duplicate-details', 'short-row']) {
    const value = structuredClone(report);
    if (mutation === 'orphan') value.rows = [value.rows[238]];
    if (mutation === 'other-name') value.rows[238][0].text = 'other - details';
    if (mutation === 'has-link') value.rows[238][1].links.push({ text: 'failed', href: 'logfiles/standard/armv7l/toybox.txt' });
    if (mutation === 'failed-parent') value.rows[237][1].text = 'failed';
    if (mutation === 'duplicate-details') value.rows.splice(239, 0, value.rows[238]);
    if (mutation === 'short-row') value.rows[238].pop();
    assert.throws(() => detailsPackages(value), { code: 'DISCOVERY_REPORT_AMBIGUOUS' }, mutation);
  }
  console.log(JSON.stringify({ pages: 6, passed: 6, explanation_rows: 1, rejected_mutations: 6, network_requests: requests }));
  assert.equal(requests, 0);
} finally { await context.close(); await browser.close(); }
