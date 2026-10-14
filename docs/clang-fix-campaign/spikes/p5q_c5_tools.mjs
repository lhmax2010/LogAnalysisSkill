// Shared offline/live evidence primitives. Never changes guards or their policy.
import { spawnSync } from 'node:child_process';
import { mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { AgentError, ORIGIN, adaptProtocol, checkRedacted, canonical }
  from '../../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';

export const PROJECT = { overview_id: 1917,
  configuration_path: 'root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER',
  project_name: 'Tizen-Base-Toolchain' };
export const ROOT = fileURLToPath(new URL('../../../', import.meta.url));
export const DEFAULTS = {
  playwright: '/home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs',
  chromium: '/home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome',
};

export async function checkedWrite(path, html) {
  const python = `${ROOT}.venv/bin/python`;
  const code = 'import sys; from pathlib import Path; from ci_triage.qb_redact import PageRedactor; '
    + 'r=PageRedactor(); r.check_bytes(sys.stdin.buffer.read()) if len(sys.argv)==1 else r.check_written(Path(sys.argv[1]))';
  checkRedacted(html);
  if (spawnSync(python, ['-c', code], { input: Buffer.from(html), cwd: ROOT }).status !== 0) {
    throw new AgentError('QB_EVIDENCE_REDACTION_FAILED');
  }
  await writeFile(path, html, { flag: 'wx' });
  if (spawnSync(python, ['-c', code, path], { cwd: ROOT }).status !== 0) {
    await rm(path, { force: true }); throw new AgentError('QB_EVIDENCE_REDACTION_FAILED');
  }
}

export async function newOutput(path) { await mkdir(path, { recursive: false }); }
export async function writeJSON(path, data) { await checkedWrite(path, JSON.stringify(data, null, 2) + '\n'); }

// Only adapted metadata. Never reads raw protocol request/response headers/body.
export function observeCallbacks(runtime) {
  const requests = [];
  const actions = [];
  const windows = new WeakMap();
  let nextWindow = 0;
  const listener = event => {
    const { metadata: m, requestId } = adaptProtocol(event);
    if (m.method === 'POST' && m.response_status === null && /IFormSubmitListener-form$/.test(m.query)) {
      actions.push({ allowed: runtime.policy.active.has(requestId) });
    }
    if (m.path !== '/wicket/page' || !/IBehaviorListener/.test(m.query)) return;
    const window = runtime.policy.fieldWindow;
    if (window && !windows.has(window)) windows.set(window, nextWindow++);
    const match = /^(\d+-\d+\.IBehaviorListener\.\d+-[A-Za-z0-9:_-]+)(?:&random=(\d(?:\.\d+)?(?:e-\d+)?))?$/.exec(m.query);
    const allowed = m.response_status === null ? runtime.policy.active.has(requestId) : null;
    requests.push({ request_id: requestId, method: m.method, path: m.path,
      query: match ? m.query : '<UNREGISTERED_SHAPE>', random: match?.[2] ?? null,
      status: m.response_status, allowed, window: window ? windows.get(window) : null });
  };
  runtime.guards.root.on('Fetch.requestPaused', listener);
  return { requests, actions, close: () => runtime.guards.root.off('Fetch.requestPaused', listener) };
}

export function assertRuntime(runtime) {
  if (runtime.failure || runtime.trace.some(row => ['WORKER_BLOCKED', 'NEW_PAGE'].includes(row.action))) {
    throw new AgentError('QB_BROWSER_UNAVAILABLE');
  }
}

export function pageFacts(document) {
  const value = node => !node ? '' : node.nodeType === 3 ? node.textContent
    : node.nodeName === 'BR' ? '\n' : [...node.childNodes].map(value).join('');
  const text = element => value(element).replace(/^[\s\u00a0]+|[\s\u00a0]+$/g, '');
  const table = node => ({ columns: [...node.querySelectorAll('thead th,thead td')].map(text),
    rows: [...node.querySelectorAll('tbody tr')].map(row => [...row.cells].map(text)) });
  const summary = [...document.querySelectorAll('.build-summary')].map(box => ({
    heading: text(box.querySelector('.box-head')), tables: [...box.querySelectorAll('table')].map(table),
  }));
  const children = [...document.querySelectorAll('h1,h2,h3,h4')].filter(node => text(node).replace(/^◆\s*/, '') === 'Child Build')
    .map(node => node.nextElementSibling?.tagName === 'TABLE' ? table(node.nextElementSibling) : null);
  const variables = [...document.querySelectorAll('table')].filter(node =>
    [...node.querySelectorAll('thead th,thead td')].map(text).join('|') === 'Name|Display Name|Value').map(table);
  return {
    navigation: [...document.querySelectorAll('.nav-link')].map(text).filter(value => /^Build \(/.test(value)),
    summary, child_build: children, variables,
    configuration_tabs: ['ConfigurationOverview', 'PipelinePage', 'ChildrenPage'].map(cls =>
      [...document.querySelectorAll(`li.tab-${cls} a.nav-link`)].map(node => node.getAttribute('href'))),
    breadcrumb: [...(document.querySelector('#breadcrumb')?.children ?? [])].map(text),
    copy_path: [...document.scripts].flatMap(node => [...node.textContent.matchAll(/onCopyClipboardLinkDomReady\('[^']*',\s*'([^']*)'\)/g)].map(match => match[1])),
    build_name: [...document.querySelectorAll('.build-header span')].filter(node => node.children.length === 0).map(text),
    failed_steps: [...document.querySelectorAll('.step.failed')].map(node => {
      const path = []; let current = node;
      while (current) { if (current.classList.contains('step')) path.unshift(text(current.querySelector(':scope > .step-head .step-name'))); current = current.parentElement; }
      return path;
    }),
    error_message: [...document.querySelectorAll('.build-errors .box-body')].map(text),
  };
}

export function compareFacts(raw, active) {
  return Object.keys(raw).map(field => ({ field, result: canonical(raw[field]) === canonical(active[field])
    ? '一致' : raw[field].length === 0 && active[field].length > 0 ? '只在活动文档中' : '值不同',
  raw: raw[field], active: active[field] }));
}

export function validatePaths(policy, paths) {
  if (!paths.length || paths.some(path => typeof path !== 'string' || !policy.readonly(path)
    || new URL(path, ORIGIN).href !== ORIGIN + path)) throw new AgentError('AGENT_PHASE');
}

export async function comparePage(agent, path, output, sequence) {
  const reply = await agent.command({ command: 'read', path });
  assertRuntime(agent.runtime);
  if (!reply.ok && reply.error !== 'QB_READ_ID_MISMATCH') throw new AgentError(reply.error);
  if (typeof agent.rawRead !== 'string' || agent.page.url() !== ORIGIN + path) throw new AgentError('QB_TRUSTED_CONTEXT_UNAVAILABLE');
  const active = await agent.trusted.run(document => document.documentElement.outerHTML);
  const rawRedacted = await agent.passive(agent.rawRead);
  const activeRedacted = await agent.passive(active);
  const rawName = `${sequence}.raw-redacted.html`, activeName = `${sequence}.active-redacted.html`;
  await checkedWrite(`${output}/${rawName}`, rawRedacted.html_redacted);
  await checkedWrite(`${output}/${activeName}`, activeRedacted.html_redacted);
  const rawFacts = await agent.trusted.run(pageFacts, rawRedacted.html_redacted);
  const activeFacts = await agent.trusted.run(pageFacts, activeRedacted.html_redacted);
  const result = { path, navigation: reply.ok ? 'VERIFIED' : reply.error, raw_file: rawName, active_file: activeName,
    raw_outside_identity_count: rawRedacted.outside_identity_count,
    active_outside_identity_count: activeRedacted.outside_identity_count, comparison: compareFacts(rawFacts, activeFacts) };
  await writeJSON(`${output}/${sequence}.comparison.json`, result);
  return result;
}

export async function assertPersisted(path) { checkRedacted(await readFile(path, 'utf8')); }
