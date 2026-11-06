import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const root = process.cwd();
const moduleRoot = path.join(root, 'tizen-qb-verify/scripts/tizen_qb_verify');
const { TrustedPage } = await import(pathToFileURL(path.join(moduleRoot, 'qb_browser_agent.mjs')));
const { DiscoveryScope, discoveryDOM } = await import(pathToFileURL(path.join(moduleRoot, 'qb_discovery_scope.mjs')));
const { chromium } = await import('/home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs');
const archives = 'docs/clang-fix-campaign/dev_memory/stage21_campaign_skeleton/evidence/restore/discovery-capture';
const inputs = [
  ['parent_overview', '/build/1204735/overview', 'live-02/02.response.html'],
  ['parent_variables', '/build/1204735/variables', 'live-02/03.response.html'],
  ['child_overview', '/build/1204736/overview', 'live-02/04.response.html'],
  ['child_variables', '/build/1204736/variables', 'live-02/05.response.html'],
  ['report_entry', '/build/1204736/html_report', 'live-02/06.response.html'],
  ['report', '/download/1204736/html/HTML%20REPORT/index.html', 'live-04/02.response.html'],
];
const project = { overview_id: '1917', configuration_path: 'root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER' };
const browser = await chromium.launch({ executablePath: '/home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome', headless: true });
const context = await browser.newContext({ serviceWorkers: 'block' });
let requests = 0;
await context.route('**/*', route => { requests += 1; return route.abort(); });
const page = await context.newPage();
const trusted = new TrustedPage(context, page);
const scope = new DiscoveryScope(project, '1204735');
try {
  for (const [kind, requestPath, file] of inputs) {
    const raw = await fs.readFile(path.join(archives, file), 'utf8');
    const facts = await trusted.run(discoveryDOM, raw);
    const expected = kind.startsWith('child') ? project.configuration_path.replace(/TRIGGER$/, 'build') : project.configuration_path;
    const childTables = facts.tables.filter(t => t.headers.map(s => s.trim()).join('|') === 'Repository-Architecture|QB Build URL|Build Result|Build Profiling');
    const checks = { title_matches: facts.title.startsWith(`QuickBuild - ${expected}`),
      crumbs_match: facts.crumbs.map(c => c.text.trim()).join('/') === expected,
      last_crumb_unlinked: facts.crumbs.length > 0 && !facts.crumbs.at(-1).linked,
      copy_count: facts.copies.length, copy_matches: facts.copies.length === 1 && facts.copies[0] === expected,
      child_table_count: childTables.length,
      child_rows: childTables.map(t => t.rows.map(r => ({ cells: r.length, link_count: r[1]?.links.length }))),
      variables_table_count: facts.tables.filter(t => t.headers.map(s => s.trim()).join('|') === 'Name|Display Name|Value').length,
      iframe_count: facts.iframes.length, details_count: facts.details.length,
      details_shapes: facts.details.map(t => t && ({ headers: t.headers.length, rows: t.rows.length,
        invalid_name_rows: t.rows.flatMap((r, i) => /^[A-Za-z0-9][A-Za-z0-9._+-]*$/.test(r[0].text.trim()) ? [] : [{
          row_index: i, cells: r.length, link_counts: r.map(c => c.links.length),
          previous_package_details: i > 0 && r[0].text.trim() === t.rows[i - 1][0].text.trim() + ' - details',
          previous_all_unresolvable: i > 0 && t.rows[i - 1].slice(1).every(c => c.text.trim() === 'unresolvable' && !c.links.length),
        }]),
      })),
      known_damaged_tag: raw.includes('</thea&lt;USER&gt;') };
    try {
      const result = scope.consume(requestPath, facts);
      console.log(JSON.stringify({ file, page_kind: kind, ok: true, checks, packages: result.packages?.map(p => ({ spec_name: p.spec_name, status: p.status })) }));
    } catch (error) {
      console.log(JSON.stringify({ file, page_kind: kind, ok: false, code: error.code, reason: error.reason,
        first_failed_check: error.first_failed_check ?? null, checks }));
      process.exitCode = 4;
      break;
    }
  }
} finally {
  await context.close(); await browser.close();
  console.log(JSON.stringify({ network_requests: requests, browser_closed: true }));
}
