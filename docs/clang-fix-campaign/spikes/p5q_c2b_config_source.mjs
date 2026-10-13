// Evidence-only selectors for P5Q-C2B-04/07. No requests and no production imports.
export const CONFIGURATION_PATH = 'root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER';
export const BUILD_PREFIX = 'TIZEN_Tizen_Tizen-Base-Toolchain_RBS_TRIGGER_';

// Run on the exact redacted response being archived, not a later live DOM.
export function configurationDOM(html) {
  const doc = new DOMParser().parseFromString(html, 'text/html');
  const hrefs = selector => [...doc.querySelectorAll(selector)].map(a => a.getAttribute('href'));
  const breadcrumbs = [...doc.querySelectorAll('#breadcrumb')].map(root => {
    const labels = [...root.querySelectorAll(':scope > span')].map(span => span.firstElementChild);
    const last = labels.at(-1);
    return {
      segments: labels.map(label => label?.textContent ?? ''),
      current: Boolean(last && last.tagName !== 'A' && !last.querySelector('a')),
    };
  });
  return {
    overview_links: hrefs('li.tab-ConfigurationOverview a.nav-link'),
    pipeline_links: hrefs('li.tab-PipelinePage a.nav-link'),
    children_links: hrefs('li.tab-ChildrenPage a.nav-link'),
    breadcrumbs,
    scripts: [...doc.querySelectorAll('script')].map(node => node.textContent),
    copy_anchor_ids: [...doc.querySelectorAll('#breadcrumb a[id]')].map(node => node.id),
    build_names: [...doc.querySelectorAll('.build-header .text-2xl')].map(node => node.textContent),
  };
}

// Node-only; checks also accept already normalized evidence records.
export function normalizeConfigurationDOM(raw) {
  const { scripts, copy_anchor_ids, ...facts } = raw;
  const copyPaths = scripts === undefined ? facts.copy_paths : [];
  for (const script of scripts ?? []) {
    for (const match of script.matchAll(/\bonCopyClipboardLinkDomReady\(\s*(['"])([^'"\\]+)\1\s*,\s*(['"])([^'"\\]+)\3\s*\)/g)) {
      if (copy_anchor_ids.filter(id => id === match[2]).length === 1) copyPaths.push({ element_id: match[2], path: match[4] });
    }
  }
  return { ...facts, copy_paths: copyPaths,
    breadcrumbs: facts.breadcrumbs.map(row => ({ ...row, segments: row.segments.map(text => text.trim()) })),
    build_names: facts.build_names.map(text => text.trim()),
  };
}

function pathChecks(facts) {
  const breadcrumb = facts.breadcrumbs[0];
  return {
    breadcrumb: facts.breadcrumbs.length === 1
      && breadcrumb.segments.join('/') === CONFIGURATION_PATH
      && breadcrumb.segments.at(-1) === 'TRIGGER' && breadcrumb.current,
    copy_path: facts.copy_paths.length === 1 && facts.copy_paths[0].path === CONFIGURATION_PATH,
  };
}

export function parentConfigurationChecks(input, sourcePath) {
  const facts = normalizeConfigurationDOM(input);
  const linkId = (links, kind) => {
    if (links.length !== 1 || typeof links[0] !== 'string' || !links[0]
      || typeof sourcePath !== 'string' || !sourcePath.startsWith('/')) return null;
    try {
      // Use the archived request address, never the live DOM's base element.
      const url = new URL(links[0], `https://quickbuild.tizen.org${sourcePath}`);
      if (url.origin !== 'https://quickbuild.tizen.org' || url.href.includes('?')
        || url.href.includes('#')) return null;
      const match = new RegExp(`^/${kind}/(\\d+)$`).exec(url.pathname);
      return match && Number.isSafeInteger(Number(match[1])) && Number(match[1]) > 0 ? match[1] : null;
    } catch { return null; }
  };
  const id = linkId(facts.overview_links, 'overview');
  const checks = {
    overview_link: id !== null,
    sibling_tabs: id !== null && linkId(facts.pipeline_links, 'pipeline') === id
      && linkId(facts.children_links, 'children') === id,
    ...pathChecks(facts),
    build_name: facts.build_names.length === 1 && facts.build_names[0].startsWith(BUILD_PREFIX),
  };
  return { checks, passed: Object.values(checks).every(Boolean), overview_id: id };
}

export function configurationPageChecks(input) {
  const checks = pathChecks(normalizeConfigurationDOM(input));
  return { checks, passed: Object.values(checks).every(Boolean) };
}

export function parentRegistration(source) {
  if (!source || source.id_verified !== true || source.status !== 200 || !/^\/build\/\d+\/overview$/.test(source.path)
    || !/^[a-f0-9]{64}$/.test(source.sha256)) throw new Error('CONFIGURATION_SOURCE_MISMATCH');
  const result = parentConfigurationChecks(source.facts, source.path);
  if (!result.passed) throw new Error('CONFIGURATION_SOURCE_MISMATCH');
  return { overview_id: Number(result.overview_id), configuration_path: CONFIGURATION_PATH,
    project_name: 'Tizen-Base-Toolchain', source: {
      path: source.path, file: source.file, sha256: source.sha256, ...result,
    } };
}
