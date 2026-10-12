// Evidence-only selectors for P5Q-C2B-04. No requests and no production imports.
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
      segments: labels.map(label => label?.textContent.trim() ?? ''),
      current: Boolean(last && last.tagName !== 'A' && !last.querySelector('a')),
    };
  });
  const copyPaths = [];
  for (const script of doc.querySelectorAll('script')) {
    for (const match of script.textContent.matchAll(/\bonCopyClipboardLinkDomReady\(\s*(['"])([^'"\\]+)\1\s*,\s*(['"])([^'"\\]+)\3\s*\)/g)) {
      const anchors = [...doc.querySelectorAll('#breadcrumb a[id]')].filter(a => a.id === match[2]);
      if (anchors.length === 1) copyPaths.push({ element_id: match[2], path: match[4] });
    }
  }
  return {
    overview_links: hrefs('li.tab-ConfigurationOverview a.nav-link'),
    pipeline_links: hrefs('li.tab-PipelinePage a.nav-link'),
    children_links: hrefs('li.tab-ChildrenPage a.nav-link'),
    breadcrumbs,
    copy_paths: copyPaths,
    build_names: [...doc.querySelectorAll('.build-header .text-2xl')].map(node => node.textContent.trim()),
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

export function parentConfigurationChecks(facts) {
  const match = facts.overview_links.length === 1
    && /^(?:\.\.\/)+overview\/(\d+)$/.exec(facts.overview_links[0]);
  const id = match ? match[1] : null;
  const checks = {
    overview_link: id !== null && Number.isSafeInteger(Number(id)) && Number(id) > 0,
    sibling_tabs: id !== null && facts.pipeline_links.length === 1 && facts.children_links.length === 1
      && facts.pipeline_links[0] === `../pipeline/${id}` && facts.children_links[0] === `../children/${id}`,
    ...pathChecks(facts),
    build_name: facts.build_names.length === 1 && facts.build_names[0].startsWith(BUILD_PREFIX),
  };
  return { checks, passed: Object.values(checks).every(Boolean), overview_id: id };
}

export function configurationPageChecks(facts) {
  const checks = pathChecks(facts);
  return { checks, passed: Object.values(checks).every(Boolean) };
}

export function parentRegistration(source) {
  if (!source || source.status !== 200 || !/^\/build\/\d+$/.test(source.path)
    || !/^[a-f0-9]{64}$/.test(source.sha256)) throw new Error('CONFIGURATION_SOURCE_MISMATCH');
  const result = parentConfigurationChecks(source.facts);
  if (!result.passed) throw new Error('CONFIGURATION_SOURCE_MISMATCH');
  return { overview_id: Number(result.overview_id), configuration_path: CONFIGURATION_PATH,
    project_name: 'Tizen-Base-Toolchain', source: {
      path: source.path, file: source.file, sha256: source.sha256, ...result,
    } };
}
