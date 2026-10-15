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

export class EvidenceError extends Error {
  constructor(code) { super(); this.code = /^[A-Z_]+$/.test(code) ? code : 'EVIDENCE_ERROR'; }
}

export function errorCode(error) {
  if ((error instanceof AgentError || error instanceof EvidenceError) && /^[A-Z_]+$/.test(error.code)) return error.code;
  const name = error?.constructor?.name;
  return typeof name === 'string' && /^[A-Za-z_]{1,64}$/.test(name) ? name : 'Error';
}

export function reportFailure(error, stderr = process.stderr) {
  if (error instanceof EvidenceError && error.code === 'EVIDENCE_WRITE_FAILED') stderr.write('EVIDENCE_WRITE_FAILED\n');
  else stderr.write(`EVIDENCE_STOPPED stage=${error instanceof EvidenceError ? error.stage ?? 'startup' : 'startup'} code=${error instanceof EvidenceError ? error.recordedCode ?? error.code : errorCode(error)}\n`);
}

export class EvidenceRun {
  constructor(output) {
    this.output = output; this.stage = 'startup'; this.agent = null; this.diagnostic = null;
    this.data = { stage: this.stage, status: 'RUNNING', failure: null, responses: [], callbacks: [],
      observer_errors: [], page_identity_counts: [], snapshots: [], trace: [] };
  }
  fail(error) {
    if (!this.data.failure) this.data.failure = { stage: this.stage, code: errorCode(error) };
    this.data.status = 'STOPPED';
  }
  incomplete(kind, error) {
    this.data.observer_errors.push({ stage: this.stage, kind, code: errorCode(error) });
  }
  response(reply, stage = this.stage) {
    const summary = { stage, has_diagnostic: Boolean(reply?.diagnostic) };
    for (const key of ['ok', 'error', 'field', 'released', 'snapshot_state']) {
      if (Object.hasOwn(reply, key)) summary[key] = reply[key];
    }
    this.data.responses.push(summary);
    if (reply.diagnostic) this.diagnostic = reply.diagnostic;
    return reply;
  }
  async command(input) {
    this.stage = input.command;
    const reply = this.response(await this.agent.command(input));
    if (!reply.ok) throw new AgentError(reply.error);
    return reply;
  }
  async finish() {
    this.data.trace = this.agent?.runtime.trace ?? [];
    this.data.stage = this.data.failure?.stage ?? this.stage;
    if (!this.data.failure) this.data.status = this.data.observer_errors.length ? 'EVIDENCE_INCOMPLETE' : 'PASSED';
    if (this.diagnostic) {
      try {
        await checkedWrite(`${this.output}/diagnostic.html`, this.diagnostic.html_redacted);
        await writeJSON(`${this.output}/diagnostic.json`, this.diagnostic.facts);
        this.data.diagnostic_files = ['diagnostic.html', 'diagnostic.json'];
      } catch (error) {
        this.stage = 'write'; this.fail(error); this.data.stage = 'write';
        this.data.diagnostic_write_error = errorCode(error);
      }
    }
    this.data.write_stage = 'write';
    this.stage = 'write';
    try { await writeJSON(`${this.output}/run.json`, this.data); }
    catch { const failure = new EvidenceError('EVIDENCE_WRITE_FAILED'); failure.stage = 'write'; throw failure; }
  }
}

// One final record even when login/open_form fails before any form facts exist.
export async function withEvidence(output, work) {
  const record = new EvidenceRun(output);
  let value;
  try { value = await work(record); }
  catch (error) { record.fail(error); }
  finally { await record.finish(); }
  if (record.data.failure || record.data.status === 'EVIDENCE_INCOMPLETE') {
    const failure = new EvidenceError(record.data.failure?.code ?? 'EVIDENCE_INCOMPLETE');
    // Exception class names are not tool error names; keep them only as the recorded code.
    failure.recordedCode = record.data.failure?.code ?? failure.code;
    failure.stage = record.data.failure?.stage ?? record.data.stage;
    throw failure;
  }
  return value;
}

export async function evidenceSession(output, makeAgent, work) {
  return withEvidence(output, async record => {
    const agent = await makeAgent(); record.agent = agent;
    try {
      await record.command({ command: 'login', projects: [PROJECT], login_timeout_seconds: 600 });
      return await work(agent, record);
    } finally {
      try { record.response(await agent.command({ command: 'close' }), 'close'); }
      catch (error) { record.stage = 'close'; record.fail(error); }
    }
  });
}

// Only adapted metadata. Never reads raw protocol request/response headers/body.
export function observeCallbacks(runtime) {
  const requests = [];
  const actions = [];
  const errors = [];
  const windows = new WeakMap();
  let nextWindow = 0;
  const listener = event => {
    let adapted;
    try { adapted = adaptProtocol(event); }
    catch { errors.push({ action: 'ADAPT_FAILED' }); return; }
    const { metadata: m, requestId } = adapted;
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
  return { requests, actions, errors, close: () => runtime.guards.root.off('Fetch.requestPaused', listener) };
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

export async function comparePage(agent, path, output, sequence, record = null) {
  if (record) record.stage = 'read';
  const reply = await agent.command({ command: 'read', path });
  record?.response(reply);
  assertRuntime(agent.runtime);
  if (!reply.ok && reply.error !== 'QB_READ_ID_MISMATCH') throw new AgentError(reply.error);
  if (typeof agent.rawRead !== 'string' || agent.page.url() !== ORIGIN + path) throw new AgentError('QB_TRUSTED_CONTEXT_UNAVAILABLE');
  const active = await agent.trusted.run(document => document.documentElement.outerHTML);
  const rawRedacted = await agent.passive(agent.rawRead);
  const activeRedacted = await agent.passive(active);
  const rawName = `${sequence}.raw-redacted.html`, activeName = `${sequence}.active-redacted.html`;
  if (record) record.stage = 'write';
  await checkedWrite(`${output}/${rawName}`, rawRedacted.html_redacted);
  await checkedWrite(`${output}/${activeName}`, activeRedacted.html_redacted);
  const rawFacts = await agent.trusted.run(pageFacts, rawRedacted.html_redacted);
  const activeFacts = await agent.trusted.run(pageFacts, activeRedacted.html_redacted);
  if (record) record.stage = 'assemble';
  const result = { path, navigation: reply.ok ? 'VERIFIED' : reply.error, raw_file: rawName, active_file: activeName,
    raw_outside_identity_count: rawRedacted.outside_identity_count,
    active_outside_identity_count: activeRedacted.outside_identity_count, comparison: compareFacts(rawFacts, activeFacts) };
  if (record) {
    record.data.snapshots.push({ path, raw: rawFacts, active: activeFacts });
    record.data.page_identity_counts.push({ page: path, raw: rawRedacted.outside_identity_count, active: activeRedacted.outside_identity_count });
    record.stage = 'write';
  }
  await writeJSON(`${output}/${sequence}.comparison.json`, result);
  return result;
}

export async function assertPersisted(path) { checkRedacted(await readFile(path, 'utf8')); }
