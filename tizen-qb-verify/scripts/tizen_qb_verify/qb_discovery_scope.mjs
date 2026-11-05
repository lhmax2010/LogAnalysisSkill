// Discovery registrations are derived only from verified inert documents.
const ORIGIN = 'https://quickbuild.tizen.org';
const ARCHES = ['standard-aarch64', 'standard-armv7l', 'standard-x86_64'];
const ARCH_ORDER = [...ARCHES, 'emulator-x86_64', 'standard_gcov-armv7l'];
export const TEXT_LIMIT = 64 * 1024 * 1024;
export class DiscoveryError extends Error {
  constructor(code, reason = null) { super(code); this.code = code; this.reason = reason; }
}
const need = (value, reason = 'REPORT_STRUCTURE') => {
  if (!value) throw new DiscoveryError('DISCOVERY_REPORT_AMBIGUOUS', reason);
};
const one = values => { need(values.length === 1); return values[0]; };
const trim = value => String(value ?? '').trim();
const idOK = value => typeof value === 'string' && /^[1-9]\d*$/.test(value);
const packageOK = value => typeof value === 'string' && /^[A-Za-z0-9][A-Za-z0-9._+-]*$/.test(value);

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
  need(table && table.headers.length >= 2);
  const headers = table.headers.map(trim);
  need(headers[0] === 'name' && headers.every(Boolean) && new Set(headers).size === headers.length);
  const arches = headers.slice(1).map(h => /^standard [^\s]+$/.test(h) ? h.replace(' ', '-') : h);
  need(new Set(arches).size === arches.length);
  const seen = new Set(); const packages = [];
  for (const row of table.rows) {
    need(row.length === headers.length);
    const name = trim(row[0].text);
    need(packageOK(name) && !seen.has(name)); seen.add(name);
    need(row.every(cell => cell.links.length <= 1));
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
    need(facts.title === `QuickBuild - ${expected}` || facts.title.startsWith(`QuickBuild - ${expected} - `));
    need(facts.crumbs.length && facts.crumbs.map(c => trim(c.text)).join('/') === expected && !facts.crumbs.at(-1).linked);
    need(facts.copies.length === 1 && facts.copies[0] === expected);
  }
  consume(path, facts) {
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
      need(table.headers.map(trim).join('|') === 'Id|Version|Master Node|Begin Date|Duration|Triggered By' && table.rows.length <= 50);
      const seen = new Set(); const builds = [];
      for (const row of table.rows) {
        need(row.length === 6); const build = trim(row[0].text); need(idOK(build) && !seen.has(build)); seen.add(build);
        const links = row[1].links.filter(a => /^\/build\/[1-9]\d*$/.test(a.href));
        need(links.length === 1 && links[0].href === `/build/${build}`);
        additions.push([`/build/${build}/overview`, { kind: 'overview', build, parent: build }]);
        builds.push({ build_id: build, begin_date: trim(row[3].text) });
      }
      result.builds = builds;
    } else if (entry.kind === 'overview') {
      const parentPath = this.project.configuration_path;
      const childPath = parentPath.replace(/TRIGGER$/, 'build');
      const actual = facts.crumbs.map(c => trim(c.text)).join('/');
      need([parentPath, childPath].includes(actual));
      if (entry.child) need(actual === childPath);
      this.identity(facts, actual);
      const child = actual === childPath;
      const data = { child, parent: entry.parent ?? (child ? null : entry.build), variables: null, packages: null };
      additions.push([`/build/${entry.build}/variables`, { kind: 'variables', build: entry.build }]);
      if (child) additions.push([`/build/${entry.build}/html_report`, { kind: 'report-entry', build: entry.build }]);
      else {
        const tables = facts.tables.filter(t => t.headers.map(trim).join('|') === 'Repository-Architecture|QB Build URL|Build Result|Build Profiling');
        const table = one(tables); const seen = new Set();
        for (const row of table.rows) {
          need(row.length === 4 && row[1].links.length === 1);
          const url = new URL(row[1].links[0].href, ORIGIN + path);
          const match = /^\/build\/([1-9]\d*)$/.exec(url.pathname);
          need(url.origin === ORIGIN && !url.username && !url.password && !url.search && !url.hash && match);
          need(!seen.has(match[1])); seen.add(match[1]);
          additions.push([`/build/${match[1]}/overview`, { kind: 'overview', build: match[1], child: true, parent: entry.build }]);
        }
      }
      this.builds.set(entry.build, data); result.child = child; result.build_id = entry.build;
    } else if (entry.kind === 'variables') {
      const table = one(facts.tables.filter(t => t.headers.map(trim).join('|') === 'Name|Display Name|Value'));
      const variables = new Map();
      for (const row of table.rows) { need(row.length === 3 && !variables.has(trim(row[0].text))); variables.set(trim(row[0].text), trim(row[2].text)); }
      const data = this.builds.get(entry.build); need(data);
      if (data.child && data.parent !== null) need(variables.get('TRIGGER_ID') === data.parent);
      if (data.child && data.parent === null) { need(idOK(variables.get('TRIGGER_ID'))); data.parent = variables.get('TRIGGER_ID'); }
      data.variables = variables;
    } else if (entry.kind === 'report-entry') {
      const data = this.builds.get(entry.build); need(data?.child && data.variables);
      const url = exactDiscoveryURL(one(facts.iframes), ORIGIN + path, entry.build);
      const match = new RegExp(`^/download/${entry.build}/html/([^/]+)/index\\.html$`).exec(url.pathname); need(match);
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
    const data = this.builds.get(build); need(data?.packages);
    const p = one(data.packages.filter(p => p.spec_name === name)); need(p.primary_arch);
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
