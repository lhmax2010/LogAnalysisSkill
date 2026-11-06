// Discovery registrations are derived only from verified inert documents.
const ORIGIN = 'https://quickbuild.tizen.org';
const ARCHES = ['standard-aarch64', 'standard-armv7l', 'standard-x86_64'];
const ARCH_ORDER = [...ARCHES, 'emulator-x86_64', 'standard_gcov-armv7l'];
export const TEXT_LIMIT = 64 * 1024 * 1024;
export const DISCOVERY_PAGE_KINDS = ['parent_overview', 'parent_variables', 'child_overview',
  'child_variables', 'report_entry', 'report', 'log', 'configuration'];
export const DISCOVERY_CHECKS = ['identity_mismatch', 'child_link_count', 'variables_missing',
  'iframe_count', 'header_missing', 'header_duplicate', 'arch_unmapped', 'package_duplicate',
  'cell_multi_link', 'link_text', 'link_path', 'structure_invalid', 'table_count', 'cell_count',
  'package_name', 'row_limit', 'variable_duplicate', 'package_count'];
export const DISCOVERY_COUNT_KEYS = ['actual_count', 'expected_count', 'row_index', 'column_index'];
export class DiscoveryError extends Error {
  constructor(code, reason = null) { super(code); this.code = code; this.reason = reason; }
}
const need = (value, check = 'structure_invalid', counts = {}) => {
  if (!value) {
    const error = new DiscoveryError('DISCOVERY_REPORT_AMBIGUOUS', 'REPORT_STRUCTURE');
    error.first_failed_check = check; error.counts = counts;
    throw error;
  }
};
const one = (values, check = 'table_count') => {
  need(values.length === 1, check, { actual_count: values.length, expected_count: 1 }); return values[0];
};
const trim = value => String(value ?? '').trim();
const idOK = value => typeof value === 'string' && /^[1-9]\d*$/.test(value);
const packageOK = value => typeof value === 'string' && /^[A-Za-z0-9][A-Za-z0-9._+-]*$/.test(value);

export function discoveryFailure(error, pageKind) {
  if (!(error instanceof DiscoveryError) || !DISCOVERY_PAGE_KINDS.includes(pageKind)) return error;
  const check = error.first_failed_check ?? (error.reason === 'PATH_UNSUPPORTED' ? 'link_path' : 'structure_invalid');
  if (!DISCOVERY_CHECKS.includes(check)) return error;
  error.page_kind = pageKind; error.first_failed_check = check;
  error.counts = Object.fromEntries(Object.entries(error.counts ?? {}).filter(([key, value]) =>
    DISCOVERY_COUNT_KEYS.includes(key) && Number.isSafeInteger(value) && value >= 0));
  return error;
}

export function exactDiscoveryURL(href, base, build) {
  if (typeof href !== 'string' || !href || href !== href.trim() || /[\x00-\x1f\x7f\\?#]/.test(href)
    || /%(?:2f|5c|2e|25|0[0-9a-f]|1[0-9a-f]|7f)/i.test(href)
    || /(?:^|\/)\.{1,2}(?:\/|$)/.test(href)) throw new DiscoveryError('DISCOVERY_LOG_UNREADABLE', 'PATH_UNSUPPORTED');
  let url;
  try { url = new URL(href, base); } catch { throw new DiscoveryError('DISCOVERY_LOG_UNREADABLE', 'PATH_UNSUPPORTED'); }
  if (url.origin !== ORIGIN || url.username || url.password || url.search || url.hash
    || !url.pathname.startsWith(`/download/${build}/html/`)) throw new DiscoveryError('DISCOVERY_LOG_UNREADABLE', 'PATH_UNSUPPORTED');
  return url;
}

// This function is serialized into the isolated world. No Node closures are used.
export function discoveryDOM(document) {
  const text = node => node.nodeType === 3 ? node.textContent : node.nodeName === 'BR' ? '\n'
    : [...node.childNodes].map(text).join('');
  const table = node => ({
    headers: [...(node.querySelector('thead tr')?.cells ?? [])].map(e => text(e)),
    rows: [...node.querySelectorAll('tbody > tr')].map(row => [...row.cells].map(cell => ({
      text: text(cell), links: [...cell.querySelectorAll('a[href]')].map(a => ({
        text: a.textContent, href: a.getAttribute('href'), className: a.className,
      })),
    }))),
  });
  return {
    title: document.title,
    crumbs: [...document.querySelectorAll('#breadcrumb > span')].map(e => ({ text: e.textContent, linked: !!e.querySelector('a') })),
    copies: [...document.querySelectorAll('script')].flatMap(s => [...s.textContent.matchAll(
      /onCopyClipboardLinkDomReady\('[^']*',\s*'([^']*)'\)/g)].map(m => m[1])),
    iframes: [...document.querySelectorAll('iframe')].map(e => e.getAttribute('src')),
    tables: [...document.querySelectorAll('table')].map(table),
    details: [...document.querySelectorAll('h1,h2,h3,h4')].filter(e => e.textContent.trim() === 'Details')
      .map(e => e.nextElementSibling?.tagName === 'TABLE' ? table(e.nextElementSibling) : null),
    recent: [...document.querySelectorAll('.box-head')].filter(e => [...e.children].some(c =>
      c.classList.contains('flex-1') && c.textContent.trim() === 'Recent Builds'))
      .map(e => [...e.parentElement.querySelectorAll('table')].map(table)),
    welcome: [...document.querySelectorAll('span,div')].filter(e => [...e.childNodes].some(n =>
      n.nodeType === 3 && /^\s*Welcome!/.test(n.textContent))).map(e => e.textContent),
  };
}

export function detailsPackages(table) {
  need(table && table.headers.length >= 2, 'header_missing', { actual_count: table?.headers.length ?? 0 });
  const headers = table.headers.map(trim);
  need(headers[0] === 'name' && headers.every(Boolean), 'header_missing', { actual_count: headers.length });
  need(new Set(headers).size === headers.length, 'header_duplicate', { actual_count: headers.length - new Set(headers).size });
  const arches = headers.slice(1).map(h => /^standard [^\s]+$/.test(h) ? h.replace(' ', '-') : h);
  need(new Set(arches).size === arches.length, 'header_duplicate', { actual_count: arches.length - new Set(arches).size });
  const seen = new Set(); const packages = [];
  for (const [rowIndex, row] of table.rows.entries()) {
    need(row.length === headers.length, 'cell_count', { row_index: rowIndex, actual_count: row.length, expected_count: headers.length });
    const name = trim(row[0].text);
    // QB emits one explanatory row immediately after an unresolvable package.
    // It is not a package or a source of log registrations.
    if (name.endsWith(' - details')) {
      const previous = table.rows[rowIndex - 1];
      need(previous && packageOK(trim(previous[0].text)) && name === `${trim(previous[0].text)} - details`,
        'package_name', { row_index: rowIndex });
      need(previous.slice(1).every(c => trim(c.text) === 'unresolvable' && c.links.length === 0),
        'link_text', { row_index: rowIndex });
      for (const [columnIndex, cell] of row.entries()) need(cell.links.length === 0, 'cell_multi_link', {
        row_index: rowIndex, column_index: columnIndex, actual_count: cell.links.length, expected_count: 0,
      });
      continue;
    }
    need(packageOK(name), 'package_name', { row_index: rowIndex });
    need(!seen.has(name), 'package_duplicate', { row_index: rowIndex }); seen.add(name);
    for (const [columnIndex, cell] of row.entries()) need(cell.links.length <= 1, 'cell_multi_link', {
      row_index: rowIndex, column_index: columnIndex, actual_count: cell.links.length, expected_count: 1,
    });
    const failed = arches.filter((arch, i) => row[i + 1].links.length === 1 && trim(row[i + 1].links[0].text) === 'failed');
    if (!failed.length) continue;
    failed.sort((a, b) => {
      const rank = s => ARCH_ORDER.includes(s) ? ARCH_ORDER.indexOf(s) : ARCH_ORDER.length;
      if (rank(a) !== rank(b)) return rank(a) - rank(b);
      const aa = [...a].map(c => c.codePointAt(0)), bb = [...b].map(c => c.codePointAt(0));
      for (let i = 0; i < Math.min(aa.length, bb.length); i += 1) if (aa[i] !== bb[i]) return aa[i] - bb[i];
      return aa.length - bb.length;
    });
    const primary = failed.every(a => ARCHES.includes(a)) ? failed[0] : null;
    packages.push({ spec_name: name, failed_arches: failed, primary_arch: primary,
      href: primary === null ? null : row[arches.indexOf(primary) + 1].links[0].href });
  }
  return packages;
}

export class DiscoveryScope {
  constructor(project, build = null) {
    this.project = project; this.entries = new Map(); this.builds = new Map(); this.identities = new Set();
    this.usedLogs = new Set();
    if (build !== null) { need(idOK(build)); this.initial = `/build/${build}/overview`; this.entries.set(this.initial, { kind: 'overview', build }); }
    else { this.initial = `/overview/${project.overview_id}`; this.entries.set(this.initial, { kind: 'configuration' }); }
  }
  identity(facts, expected) {
    need(facts.title === `QuickBuild - ${expected}` || facts.title.startsWith(`QuickBuild - ${expected} - `), 'identity_mismatch');
    need(facts.crumbs.length && facts.crumbs.map(c => trim(c.text)).join('/') === expected && !facts.crumbs.at(-1).linked,
      'identity_mismatch', { actual_count: facts.crumbs.length });
    need(facts.copies.length === 1 && facts.copies[0] === expected, 'identity_mismatch', { actual_count: facts.copies.length, expected_count: 1 });
  }
  pageKind(path, facts = null) {
    const entry = this.entries.get(path);
    if (entry?.kind === 'configuration') return 'configuration';
    if (entry?.kind === 'report-entry') return 'report_entry';
    if (entry?.kind === 'report') return 'report';
    if (entry?.kind === 'text') return 'log';
    const child = entry?.child || this.builds.get(entry?.build)?.child
      || facts?.crumbs.map(c => trim(c.text)).join('/') === this.project.configuration_path.replace(/TRIGGER$/, 'build');
    return `${child ? 'child' : 'parent'}_${entry?.kind === 'variables' ? 'variables' : 'overview'}`;
  }
  consume(path, facts) {
    try { return this.consumeFacts(path, facts); }
    catch (error) { throw discoveryFailure(error, this.pageKind(path, facts)); }
  }
  consumeFacts(path, facts) {
    const entry = this.entries.get(path); need(entry);
    const additions = [];
    for (const text of facts.welcome) {
      const value = trim(text.replace(/^\s*Welcome!\s*/, ''));
      if (value && !['<USER>', '<REDACTED>'].includes(value)) {
        this.identities.add(value);
        const pair = /^(.+?)\s+\(([^()]+)\)$/.exec(value);
        if (pair) { this.identities.add(trim(pair[1])); this.identities.add(trim(pair[2])); }
      }
    }
    let result = { kind: entry.kind, paths: [] };
    if (entry.kind === 'configuration') {
      this.identity(facts, this.project.configuration_path);
      const table = one(one(facts.recent));
      need(table.headers.map(trim).join('|') === 'Id|Version|Master Node|Begin Date|Duration|Triggered By', 'header_missing', { actual_count: table.headers.length, expected_count: 6 });
      need(table.rows.length <= 50, 'row_limit', { actual_count: table.rows.length, expected_count: 50 });
      const seen = new Set(); const builds = [];
      for (const row of table.rows) {
        need(row.length === 6, 'cell_count', { actual_count: row.length, expected_count: 6 });
        const build = trim(row[0].text); need(idOK(build) && !seen.has(build), 'identity_mismatch'); seen.add(build);
        const links = row[1].links.filter(a => /^\/build\/[1-9]\d*$/.test(a.href));
        need(links.length === 1, 'child_link_count', { actual_count: links.length, expected_count: 1 });
        need(links[0].href === `/build/${build}`, 'link_path');
        additions.push([`/build/${build}/overview`, { kind: 'overview', build, parent: build }]);
        builds.push({ build_id: build, begin_date: trim(row[3].text) });
      }
      result.builds = builds;
    } else if (entry.kind === 'overview') {
      const parentPath = this.project.configuration_path;
      const childPath = parentPath.replace(/TRIGGER$/, 'build');
      const actual = facts.crumbs.map(c => trim(c.text)).join('/');
      need([parentPath, childPath].includes(actual), 'identity_mismatch');
      if (entry.child) need(actual === childPath, 'identity_mismatch');
      this.identity(facts, actual);
      const child = actual === childPath;
      const data = { child, parent: entry.parent ?? (child ? null : entry.build), variables: null, packages: null };
      additions.push([`/build/${entry.build}/variables`, { kind: 'variables', build: entry.build }]);
      if (child) additions.push([`/build/${entry.build}/html_report`, { kind: 'report-entry', build: entry.build }]);
      else {
        const tables = facts.tables.filter(t => t.headers.map(trim).join('|') === 'Repository-Architecture|QB Build URL|Build Result|Build Profiling');
        const table = one(tables, 'header_missing'); const seen = new Set();
        for (const row of table.rows) {
          need(row.length === 4, 'cell_count', { actual_count: row.length, expected_count: 4 });
          need(row[1].links.length === 1, 'child_link_count', { actual_count: row[1].links.length, expected_count: 1 });
          let url;
          try { url = new URL(row[1].links[0].href, ORIGIN + path); }
          catch { need(false, 'link_path'); }
          const match = /^\/build\/([1-9]\d*)$/.exec(url.pathname);
          need(url.origin === ORIGIN && !url.username && !url.password && !url.search && !url.hash && match, 'link_path');
          need(!seen.has(match[1]), 'child_link_count', { actual_count: 2, expected_count: 1 }); seen.add(match[1]);
          additions.push([`/build/${match[1]}/overview`, { kind: 'overview', build: match[1], child: true, parent: entry.build }]);
        }
      }
      this.builds.set(entry.build, data); result.child = child; result.build_id = entry.build;
    } else if (entry.kind === 'variables') {
      const table = one(facts.tables.filter(t => t.headers.map(trim).join('|') === 'Name|Display Name|Value'), 'variables_missing');
      const variables = new Map();
      for (const row of table.rows) {
        need(row.length === 3, 'cell_count', { actual_count: row.length, expected_count: 3 });
        need(!variables.has(trim(row[0].text)), 'variable_duplicate'); variables.set(trim(row[0].text), trim(row[2].text));
      }
      const data = this.builds.get(entry.build); need(data);
      if (data.child && data.parent !== null) need(variables.get('TRIGGER_ID') === data.parent, 'identity_mismatch');
      if (data.child && data.parent === null) { need(idOK(variables.get('TRIGGER_ID')), 'identity_mismatch'); data.parent = variables.get('TRIGGER_ID'); }
      data.variables = variables;
    } else if (entry.kind === 'report-entry') {
      const data = this.builds.get(entry.build); need(data?.child && data.variables);
      const url = exactDiscoveryURL(one(facts.iframes, 'iframe_count'), ORIGIN + path, entry.build);
      const match = new RegExp(`^/download/${entry.build}/html/([^/]+)/index\\.html$`).exec(url.pathname); need(match, 'link_path');
      data.report = url.pathname; data.reportDir = decodeURIComponent(match[1]);
      additions.push([url.pathname, { kind: 'report', build: entry.build }]);
    } else if (entry.kind === 'report') {
      const data = this.builds.get(entry.build); need(data?.report === path);
      data.packages = detailsPackages(one(facts.details));
      const source = (data.variables.get('BUILD_PKG_LIST') ?? '').split(/\r?\n/).filter(Boolean);
      result = { ...result, build_id: data.parent, child_build_id: entry.build, report_dir: data.reportDir,
        packages: data.packages.map(p => {
          const matches = source.map(line => /^([^\s@]+)@([0-9a-f]{40})$/.exec(line.trim())).filter(m => m && m[1].split('/').at(-1) === p.spec_name);
          const branch = data.variables.get('PROJECT_BRANCH') ?? this.builds.get(data.parent)?.variables?.get('PROJECT_BRANCH');
          const valid = matches.length === 1 && /^[A-Za-z0-9][A-Za-z0-9._/+-]*$/.test(matches[0][1]) && !matches[0][1].includes('..')
            && typeof branch === 'string' && /^[A-Za-z0-9][A-Za-z0-9._+-]*$/.test(branch);
          return { spec_name: p.spec_name, failed_arches: p.failed_arches, primary_arch: p.primary_arch,
            project: valid ? matches[0][1] : null, branch: valid ? branch : null, base_commit: valid ? matches[0][2] : null,
            log_path: null, log_sha256: null, status: !p.primary_arch ? 'ARCH_NOT_ALLOWED' : valid ? 'ok' : 'DISCOVERY_SOURCE_UNRESOLVED',
            reason: !p.primary_arch ? 'ARCH_NOT_ALLOWED' : valid ? null : 'SOURCE_VARIABLES' };
        }) };
    } else need(false);
    for (const [key, value] of additions) this.entries.set(key, value);
    result.paths = additions.map(([key]) => key);
    return result;
  }
  log(build, name) {
    try { return this.registerLog(build, name); }
    catch (error) { throw discoveryFailure(error, 'log'); }
  }
  registerLog(build, name) {
    const data = this.builds.get(build); need(data?.packages);
    const p = one(data.packages.filter(p => p.spec_name === name), 'package_count'); need(p.primary_arch, 'arch_unmapped');
    const key = `${build}/${name}`; need(!this.usedLogs.has(key)); this.usedLogs.add(key);
    const url = exactDiscoveryURL(p.href, ORIGIN + data.report, build);
    const expected = data.report.replace(/index\.html$/, `logfiles/standard/${p.primary_arch.slice(9)}/${name}.txt`);
    if (url.pathname !== expected) throw new DiscoveryError('DISCOVERY_LOG_UNREADABLE', 'PATH_UNSUPPORTED');
    this.entries.set(url.pathname, { kind: 'text', build });
    return { path: url.pathname, package: p };
  }
}

export function redactDiscoveryText(text, identities) {
  for (const value of [...identities].sort((a, b) => b.length - a.length)) {
    const escaped = value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    text = text.replace(new RegExp(`(?<![A-Za-z0-9_])${escaped}(?![A-Za-z0-9_])`, 'g'), '<USER>');
  }
  return text.replace(/^\s*(?:set-cookie|cookie|authorization)\s*:[^\r\n]*/gim, '<REDACTED>')
    .replace(/\b[\w-]*(?:token|csrf|xsrf|session|password|secret)[\w-]*\s*[:=]\s*(?:"[^"]*"|'[^']*'|[^\s;&]+)/gi, '<REDACTED>');
}
