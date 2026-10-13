import { createHash } from 'node:crypto';
import { mkdtemp, rm } from 'node:fs/promises';
import { createInterface } from 'node:readline';
import { pathToFileURL } from 'node:url';

export const ORIGIN = 'https://quickbuild.tizen.org';
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const STATIC = ['/styles/', '/jquery/', '/scripts/', '/datetimepicker/', '/codemirror/',
  '/wicket/resource/', '/images/', '/favicon.ico'];
const DESTRUCTIVE = /I(Link|Behavior|FormSubmit|Resource)Listener[.0-9-]*-[A-Za-z0-9:_-]*(promote|cancel|stop|rerun|delete|abort)/i;
const CALLBACK = /^\d+-\d+\.IBehaviorListener\.\d+-[A-Za-z0-9:_-]+$/;
const ACTION = /^\d+-\d+\.IFormSubmitListener-form$/;
export const FIELDS = ['BUILD_TYPE', 'REPO_TYPE', 'BUILD_REFERENCE', 'SNAPSHOT_NUM',
  'PROJECT_BRANCH', 'Immediate Stop With Error', 'CHILD_CONFIGURATIONS', 'Build Package List',
  'Add Package List', 'Remove Package List', 'TARGET_IMAGE', 'BUILD NOTES'];
const PALETTES = new Set(['CHILD_CONFIGURATIONS', 'TARGET_IMAGE']);

export class AgentError extends Error {
  constructor(code, field) { super(code); this.code = code; this.field = field; }
}

export function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  if (value && typeof value === 'object') return `{${Object.keys(value).sort().map(
    (key) => `${JSON.stringify(key)}:${canonical(value[key])}`).join(',')}}`;
  return JSON.stringify(value);
}
export const fingerprint = (value) => createHash('sha256').update(canonical(value)).digest('hex');

// The only protocol adapter. Request headers, postData and postDataEntries are
// never copied, parsed or forwarded; policy sees only the approved metadata.
export function adaptProtocol(event) {
  try {
    const url = new URL(event.request.url);
    return { requestId: event.requestId, frameId: event.frameId ?? null,
      metadata: { method: event.request.method, protocol: url.protocol, host: url.host,
        path: url.pathname, query: url.search.slice(1), resource_type: event.resourceType,
        redirect_source: event.redirectedRequestId ?? null,
        response_status: event.responseStatusCode ?? null } };
  } catch { throw new AgentError('QB_BROWSER_UNAVAILABLE'); }
}

export class Policy {
  constructor(overviewIds = []) {
    this.overviewIds = new Set(overviewIds.map(String));
    this.phase = 'idle';
    this.refresh = new Set();
    this.runUrl = null;
    this.fieldUrl = null;
    this.submitUrl = null;
    this.released = false;
    this.lastActivity = Date.now();
    this.active = new Set();
    this.fieldFinished = false;
    this.loginPostCount = 0;
    this.loginPostsClosed = false;
    this.loginPostRequests = new Set();
  }
  get phase() { return this._phase; }
  set phase(value) {
    if (this._phase === 'login' && value !== 'login') this.loginPostsClosed = true;
    this._phase = value;
  }
  readonly(path) {
    return /^\/build\/\d+(?:\/(overview|variables|step_status))?$/.test(path)
      || /^\/overview\/\d+$/.test(path) && this.overviewIds.has(path.split('/').at(-1));
  }
  newForm() { this.released = false; this.submitUrl = null; this.endField(); }
  beginField(url) {
    let parsed;
    try { parsed = new URL(url); } catch { throw new AgentError('QB_FORM_CHANGED'); }
    if (parsed.origin !== ORIGIN || parsed.pathname !== '/wicket/page'
      || !CALLBACK.test(parsed.search.slice(1))) throw new AgentError('QB_FORM_CHANGED');
    this.fieldUrl = url; this.fieldFinished = false; this.fieldRequest = null;
  }
  endField() { this.fieldUrl = null; this.fieldRequest = null; }
  invalidate() { this.runUrl = null; this.submitUrl = null; this.endField(); }
  allow(m, requestId = '') {
    const url = `${m.protocol}//${m.host}${m.path}${m.query ? `?${m.query}` : ''}`;
    // Close both login channels even when the redirect itself is denied (307/308).
    if (this.loginPostRequests.has(requestId)
      && m.response_status >= 300 && m.response_status < 400) this.loginPostsClosed = true;
    if (m.protocol !== 'https:' || m.host !== 'quickbuild.tizen.org'
      || m.resource_type === 'WebSocket' || m.path.startsWith('/rest/')
      || DESTRUCTIVE.test(m.query) || /ILinkListener-form-cancel/i.test(m.query)
      || /^\/build\/\d+\/(log|html_report|artifacts)(?:\/|$)/.test(m.path)
      || [307, 308].includes(m.response_status)) return false;
    // Responses cannot consume one-shot registrations a second time.
    if (m.response_status !== null) return this.active.has(requestId);
    if (m.method === 'GET' && STATIC.some((path) => m.path.startsWith(path))
      && (!m.query || /^v=\d+$/.test(m.query)) && !/Listener/i.test(m.query)) return true;
    if (this.phase === 'login') {
      if (m.method === 'GET' && ['/signin', '/', '/overview/0'].includes(m.path) && !m.query) return true;
      // Observed in live-02c; C2B-02 permits numeric login landing page versions.
      if (m.method === 'GET' && m.resource_type === 'Document' && m.path === '/dashboard'
        && (!m.query || m.query.match(/^\d+$/)?.[0] === m.query)) return true;
      if (this.loginPostsClosed || m.method !== 'POST'
        || !['/signin', '/wicket/page'].includes(m.path)
        || m.query.match(/^\d+-\d+\.IFormSubmitListener-content-form$/)?.[0] !== m.query) return false;
      this.loginPostRequests.add(requestId);
      this.loginPostCount += 1;
      if (this.loginPostCount >= 5) this.loginPostsClosed = true;
      return true;
    }
    if (this.refresh.has(url) && m.method === 'GET') return true;
    if (['read', 'open_form', 'fill'].includes(this.phase)
      && m.method === 'GET' && this.readonly(m.path) && !m.query) return true;
    if (this.phase === 'open_form') {
      if (m.method === 'GET' && url === this.runUrl) { this.runUrl = null; return true; }
      return m.method === 'GET' && m.path === '/wicket/page' && /^\d+$/.test(m.query);
    }
    if (this.phase === 'fill') {
      if (m.method === 'POST' && url === this.fieldUrl) {
        this.fieldUrl = null; this.fieldRequest = requestId; return true;
      }
      return m.method === 'GET' && m.path === '/wicket/page' && /^\d+(-\d+)?$/.test(m.query);
    }
    if (this.phase === 'submit') {
      if (m.method === 'POST' && !this.released && url === this.submitUrl
        && m.path === '/wicket/page' && ACTION.test(m.query)) {
        this.submitUrl = null; this.released = true; return true;
      }
      return this.released && m.method === 'GET' && (
        /^\/build\/\d+$/.test(m.path) && !m.query
        || m.path === '/wicket/page' && /^\d+(-\d+)?$/.test(m.query));
    }
    return false;
  }
}

export class FrameOwnership {
  constructor(tree) {
    this.parents = new Map();
    const visit = (node, parent) => {
      this.parents.set(node.frame.id, parent);
      for (const child of node.childFrames ?? []) visit(child, node.frame.id);
    };
    visit(tree, null);
  }
  has(id) { return typeof id === 'string' && this.parents.has(id); }
  attach(id, parent) { if (this.has(parent)) this.parents.set(id, parent); }
  detach(id) {
    for (const [child, parent] of this.parents) if (parent === id) this.detach(child);
    this.parents.delete(id);
  }
  navigate(frame) {
    if (!frame.parentId) { this.parents.clear(); this.parents.set(frame.id, null); }
    else this.attach(frame.id, frame.parentId);
  }
}

export async function installGuards(browser, context, page, policy, onStop, trace,
  { diagnostic = false, useBrowserFetch = true } = {}) {
  const primary = await context.newCDPSession(page);
  const { targetInfo: main } = await primary.send('Target.getTargetInfo');
  await primary.send('Page.enable');
  const { frameTree } = await primary.send('Page.getFrameTree');
  const frames = new FrameOwnership(frameTree);
  primary.on('Page.frameAttached', ({ frameId, parentFrameId }) => frames.attach(frameId, parentFrameId));
  primary.on('Page.frameDetached', ({ frameId }) => frames.detach(frameId));
  primary.on('Page.frameNavigated', ({ frame }) => frames.navigate(frame));
  const root = await browser.newBrowserCDPSession();
  const pending = new Set();
  const guarded = (promise) => {
    pending.add(promise);
    promise.catch(onStop).finally(() => pending.delete(promise));
  };
  if (useBrowserFetch) {
    root.on('Fetch.requestPaused', (event) => {
      let adapted;
      try { adapted = adaptProtocol(event); } catch { onStop(); return; }
      const { metadata: m, requestId, frameId } = adapted;
      const allowed = frames.has(frameId) && policy.allow(m, requestId);
      const response = m.response_status !== null;
      const url = `${m.protocol}//${m.host}${m.path}${m.query ? `?${m.query}` : ''}`;
      if (!policy.refresh.has(url)) policy.lastActivity = Date.now();
      if (!allowed) trace.push({ phase: policy.phase, path: pathShape(m.path), action: 'DENIED' });
      if (allowed && !response) policy.active.add(requestId);
      if (response || !allowed) policy.active.delete(requestId);
      guarded(root.send(!allowed ? 'Fetch.failRequest' : response ? 'Fetch.continueResponse' : 'Fetch.continueRequest',
        !allowed ? { requestId, errorReason: 'BlockedByClient' } : { requestId }).then(() => {
        if (response && requestId === policy.fieldRequest && allowed) policy.fieldFinished = true;
      }));
    });
    await root.send('Fetch.enable', { patterns: [
      { urlPattern: '*', requestStage: 'Request' }, { urlPattern: '*', requestStage: 'Response' },
    ] });
  }
  root.on('Target.targetCreated', ({ targetInfo }) => {
    if (targetInfo.type === 'page' && targetInfo.targetId !== main.targetId) {
      trace.push({ action: 'NEW_PAGE' });
      if (!diagnostic) onStop();
    }
  });
  await root.send('Target.setDiscoverTargets', { discover: true });
  const seen = new Set();
  const blockWorker = (session, { targetInfo, waitingForDebugger }) => {
    if (seen.has(targetInfo.targetId)) return;
    seen.add(targetInfo.targetId);
    trace.push({ action: 'WORKER_BLOCKED', type: targetInfo.type, paused: waitingForDebugger });
    if (!waitingForDebugger) { onStop(); return; }
    guarded(session.send('Target.closeTarget', { targetId: targetInfo.targetId }).then((result) => {
      if (!result.success) onStop();
    }));
  };
  const filter = [{ type: 'worker' }, { type: 'shared_worker' }, { type: 'service_worker' }, { exclude: true }];
  root.on('Target.attachedToTarget', (event) => blockWorker(root, event));
  await root.send('Target.setAutoAttach', { autoAttach: true, waitForDebuggerOnStart: true, flatten: true, filter });
  const related = await browser.newBrowserCDPSession();
  related.on('Target.attachedToTarget', (event) => blockWorker(related, event));
  await related.send('Target.autoAttachRelated', { targetId: main.targetId, waitForDebuggerOnStart: true, filter });
  return { primary, root, frames };
}

export function pathShape(path) {
  if (/^\/build\/\d+(?:\/(overview|variables|step_status))?$/.test(path)) return path.replace(/\d+/, '<id>');
  if (/^\/overview\/\d+$/.test(path)) return '/overview/<id>';
  if (path === '/' || path === '/dashboard' || path === '/wicket/page' || path === '/signin') return path;
  return '<other>';
}

// Browser DOM redaction is followed by a Node-side string self-check and the
// independent qb_redact check in Python. Only the redacted DOM crosses IPC.
export function redactDOM() {
  const root = document.documentElement.cloneNode(true);
  const identities = new Set();
  const secrets = new Set();
  const remember = (set, value) => { if (value && !['<USER>', '<REDACTED>'].includes(value)) set.add(value); };
  for (const element of root.querySelectorAll('span, div')) {
    if ([...element.childNodes].some((node) => node.nodeType === 3 && /^\s*Welcome!/.test(node.textContent))) {
      const value = element.textContent.replace(/^\s*Welcome!\s*/, '').trim();
      remember(identities, value); element.textContent = 'Welcome! <USER>';
    }
  }
  for (const table of root.querySelectorAll('table')) {
    let column = null;
    for (const row of table.rows) {
      if (row.closest('table') !== table) continue;
      const cells = [...row.cells];
      const index = cells.findIndex((cell) => cell.textContent.trim() === 'Triggered By');
      let cell;
      if (index >= 0 && cells[index].tagName === 'TH') column = index;
      else if (index >= 0) cell = cells[index + 1];
      else if (column !== null && cells[column]?.tagName === 'TD') cell = cells[column];
      if (cell) { remember(identities, cell.textContent.trim()); cell.textContent = '<USER>'; }
    }
  }
  const sensitive = /password|passwd|secret|token|credential|authorization|cookie|session|csrf|xsrf/i;
  for (const element of root.querySelectorAll('*')) {
    const name = element.getAttribute('name') ?? '';
    const isInput = element.tagName === 'INPUT';
    const hidden = isInput && /^(hidden|password)$/i.test(element.getAttribute('type') ?? '');
    const recorder = name.endsWith(':palette:recorder');
    if (sensitive.test(name + (element.id ?? ''))) {
      remember(secrets, element.getAttribute(isInput ? 'value' : 'content'));
    }
    if (hidden && !recorder && element.hasAttribute('value')) {
      remember(secrets, element.getAttribute('value')); element.setAttribute('value', '<REDACTED>');
    }
    for (const attribute of [...element.attributes]) {
      if (!['name', 'id'].includes(attribute.name) && sensitive.test(attribute.name)) {
        remember(secrets, attribute.value); element.setAttribute(attribute.name, '<REDACTED>');
      }
    }
  }
  let html = root.outerHTML;
  const assignment = /[\w-]*(?:token|csrf|xsrf|session)[\w-]*["']?\s*[:=]\s*(?:"([^"]*)"|'([^']*)'|([^?&;\s<>"'`)\]}]+))/gi;
  const escaped = (value) => { const div = document.createElement('div'); div.textContent = value; return div.innerHTML; };
  const decode = (value) => { const box = document.createElement('textarea'); box.innerHTML = value; return box.value; };
  const identityPattern = (value) => new RegExp(`(?<![A-Za-z0-9_])${value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?![A-Za-z0-9_])`, 'g');
  for (const match of decode(html).matchAll(assignment)) remember(secrets, match[1] ?? match[2] ?? match[3]);
  for (const value of [...secrets].sort((a, b) => b.length - a.length)) {
    for (const spelling of new Set([value, escaped(value), encodeURIComponent(value), JSON.stringify(value).slice(1, -1)])) {
      html = html.split(spelling).join('&lt;REDACTED&gt;');
    }
  }
  for (const value of [...identities].sort((a, b) => b.length - a.length)) {
    for (const spelling of new Set([value, escaped(value)])) html = html.replace(identityPattern(spelling), '&lt;USER&gt;');
  }
  html = html.replace(/^\s*(?:set-cookie|cookie|authorization)\s*:[^\r\n]*/gim, '&lt;REDACTED&gt;')
    .replace(/JSESSIONID_8810\s*=/gi, 'redacted_session:');
  if ([...secrets].some((value) => value && decode(html).includes(value))
    || [...identities].some((value) => identityPattern(value).test(decode(html)))
    || /JSESSIONID_8810\s*=/i.test(html)) throw new Error('QB_EVIDENCE_REDACTION_FAILED');
  return html;
}

export function checkRedacted(html) {
  if (typeof html !== 'string' || /JSESSIONID_8810\s*=|^\s*(set-cookie|cookie|authorization)\s*:/im.test(html)) {
    throw new AgentError('QB_EVIDENCE_REDACTION_FAILED');
  }
  return html;
}

export function formDOM() {
  const forms = [...document.forms].filter((form) => form.action.includes('IFormSubmitListener-form'));
  if (forms.length !== 1) return null;
  const form = forms[0];
  const rows = [...form.querySelectorAll('.form-label')].map((label) => {
    const row = label.closest('tr');
    const box = row?.querySelector('td.value');
    if (!box) return null;
    const viewers = [...box.querySelectorAll('.property-viewer')];
    const controls = [...box.querySelectorAll('input, select, textarea')].map((element) => ({
      id: element.id, tag: element.tagName, type: element.type,
      role: element.name?.split(':').at(-1), callback: element.getAttribute('onchange'),
      value: element.value, checked: element.checked,
      options: element.tagName === 'SELECT' ? [...element.options].map((option) => ({
        text: option.textContent, value: option.value, selected: option.selected,
      })) : [],
    }));
    const buttons = [...box.querySelectorAll('button')].map((button) => ({
      className: button.className, code: button.getAttribute('onclick'),
    }));
    return { label: label.textContent.trim(), viewers: viewers.map((v) => v.textContent.trim()), controls, buttons };
  });
  return { title: document.title, heading: document.body.textContent.includes('Specify Build Options'),
    action: form.action, rows, base: document.baseURI };
}

export function callbackURL(code, base) {
  if (typeof code !== 'string') throw new AgentError('QB_FORM_CHANGED');
  const matches = [...code.matchAll(/wicketAjaxPost\(\s*(['"])(.*?)\1/g)];
  if (matches.length !== 1) throw new AgentError('QB_FORM_CHANGED');
  let url;
  try { url = new URL(matches[0][2], base); } catch { throw new AgentError('QB_FORM_CHANGED'); }
  if (url.origin !== ORIGIN || url.pathname !== '/wicket/page' || !CALLBACK.test(url.search.slice(1))) {
    throw new AgentError('QB_FORM_CHANGED');
  }
  return url.href;
}

export function validateForm(form, projectName) {
  if (!form?.heading || !Array.isArray(form.rows) || form.rows.some((row) => !row)) throw new AgentError('QB_FORM_CHANGED');
  const labels = form.rows.map((row) => row.label);
  if (new Set(labels).size !== FIELDS.length + 1
    || labels.some((name) => ![...FIELDS, 'PROJECT_NAME'].includes(name))) throw new AgentError('QB_FORM_CHANGED');
  const grouped = Object.fromEntries([...new Set(labels)].map((name) => [name, form.rows.filter((row) => row.label === name)]));
  if (Object.values(grouped).some((rows) => rows.length !== 1)) throw new AgentError('QB_FORM_CHANGED');
  for (const row of form.rows) {
    if (row.label === 'PROJECT_NAME') {
      if (row.controls.length || row.viewers.length !== 1 || row.viewers[0] !== projectName) throw new AgentError('QB_FORM_CHANGED');
      continue;
    }
    if (PALETTES.has(row.label)) {
      if (row.controls.length !== 3 || canonical(row.controls.map((c) => c.role).sort())
        !== canonical(['choices', 'recorder', 'selection'])) throw new AgentError('QB_FORM_CHANGED');
    } else if (row.controls.length !== 1) throw new AgentError('QB_FORM_CHANGED');
    const callback = PALETTES.has(row.label) ? row.controls.find((c) => c.role === 'recorder') : row.controls[0];
    callbackURL(callback.callback, form.base);
  }
  let action;
  try { action = new URL(form.action); } catch { throw new AgentError('QB_FORM_CHANGED'); }
  if (action.origin !== ORIGIN || action.pathname !== '/wicket/page' || !ACTION.test(action.search.slice(1))) throw new AgentError('QB_FORM_CHANGED');
  return Object.fromEntries(form.rows.map((row) => [row.label, row]));
}

export function readback(form, projectName) {
  const fields = validateForm(form, projectName);
  const values = {};
  for (const name of FIELDS) {
    const controls = fields[name].controls;
    if (PALETTES.has(name)) {
      const selected = controls.find((c) => c.role === 'selection').options.map((option) => option.text);
      const recorder = controls.find((c) => c.role === 'recorder').value;
      let decoded;
      try { decoded = new TextDecoder('utf-8', { fatal: true }).decode(Buffer.from(recorder, 'hex')); }
      catch { throw new AgentError('QB_FORM_READBACK_MISMATCH', name); }
      // The frozen configuration only permits zero or one item; a multi-value
      // delimiter was not observed and is deliberately not guessed.
      if (selected.length > 1 || (selected.length === 0 ? recorder !== ''
        : !/^(?:[\da-fA-F]{2})+$/.test(recorder)
          || decoded !== selected[0])) {
        throw new AgentError('QB_FORM_READBACK_MISMATCH', name);
      }
      values[`${name}/selection`] = selected;
    } else {
      const control = controls[0];
      if (control.tag === 'SELECT') {
        const selected = control.options.filter((option) => option.selected);
        if (selected.length !== 1) throw new AgentError('QB_FORM_VALUE_UNAVAILABLE', name);
        values[`${name}/value`] = selected[0].text;
      } else values[`${name}/value`] = control.type === 'checkbox' ? control.checked : control.value;
    }
  }
  return values;
}

export class Agent {
  constructor(runtime) {
    this.runtime = runtime; this.page = runtime.page; this.policy = runtime.policy;
    this.state = 'new'; this.projects = new Map(); this.currentProject = null;
  }
  async command(input) {
    const allowed = { login: ['new'], read: ['ready', 'form', 'filled', 'invalid'], open_form: ['ready', 'form', 'filled', 'invalid'],
      fill: ['form'], submit: ['filled'] };
    const command = input?.command;
    if (command === 'close') { await this.runtime.close(); this.state = 'closed'; return { ok: true }; }
    if (!allowed[command]?.includes(this.state)) return { ok: false, error: 'AGENT_PHASE' };
    if (this.runtime.failure) return { ok: false, error: this.runtime.failure };
    this.policy.phase = command;
    try {
      let result;
      if (command === 'login') {
        if (!Number.isSafeInteger(input.login_timeout_seconds) || input.login_timeout_seconds <= 0
          || !Array.isArray(input.projects)) throw new AgentError('AGENT_PHASE');
        for (const project of input.projects) {
          if (!Number.isSafeInteger(project.overview_id) || project.overview_id <= 0
            || typeof project.configuration_path !== 'string' || typeof project.project_name !== 'string') throw new AgentError('AGENT_PHASE');
          this.projects.set(project.overview_id, project);
          this.policy.overviewIds.add(String(project.overview_id));
        }
        result = await this.login(input.login_timeout_seconds); this.state = 'ready';
      } else if (command === 'read') {
        this.state = 'ready'; this.policy.invalidate(); result = await this.read(input.path);
      }
      else if (command === 'open_form') {
        this.policy.newForm(); this.state = 'invalid';
        result = await this.openForm(input.overview_id); this.state = 'form';
      } else if (command === 'fill') {
        this.state = 'invalid'; result = await this.fill(input.fields); this.state = 'filled';
      } else {
        this.state = 'invalid'; result = await this.submit(input.fingerprint);
      }
      return { ok: true, ...result };
    } catch (error) {
      if (command === 'fill' || command === 'open_form' || command === 'submit') {
        this.state = 'invalid'; this.policy.invalidate();
      }
      if (command === 'submit' && this.policy.released) return { ok: true, landed: 'unknown', released: true, observed: '<other>', messages: [] };
      const response = { ok: false, error: error instanceof AgentError ? error.code : 'QB_BROWSER_UNAVAILABLE' };
      if (error instanceof AgentError && error.field) response.field = error.field;
      if (command === 'submit') response.released = false;
      return response;
    } finally { this.policy.phase = 'idle'; }
  }
  async login(timeout) {
    process.stderr.write('已打开 QuickBuild 登录窗口,请在窗口中登录;登录后工具会自动继续。\n');
    const deadline = Date.now() + timeout * 1000;
    try {
      await this.page.goto(`${ORIGIN}/signin`, { timeout: timeout * 1000 });
      while (Date.now() < deadline) {
        if (this.page.isClosed()) throw new AgentError('QB_LOGIN_ABORTED');
        if (new URL(this.page.url()).pathname !== '/signin'
          && await this.page.locator('input[type=password]').count() === 0
          && await this.page.getByRole('link', { name: 'Sign Out', exact: true }).count() > 0) return {};
        await sleep(Math.min(2000, Math.max(0, deadline - Date.now())));
      }
    } catch (error) {
      const closed = this.page.isClosed();
      await this.runtime.close();
      if (error instanceof AgentError) throw error;
      throw new AgentError(this.runtime.failure ?? (closed ? 'QB_LOGIN_ABORTED' : 'QB_LOGIN_TIMEOUT'));
    }
    await this.runtime.close(); throw new AgentError('QB_LOGIN_TIMEOUT');
  }
  async registerRefresh() {
    const values = await this.page.evaluate(() => [...document.querySelectorAll('script, [onload], [onclick]')]
      .flatMap((element) => [element.textContent ?? '', element.getAttribute('onload') ?? '', element.getAttribute('onclick') ?? ''])
      .flatMap((code) => [...code.matchAll(/['"]([^'"\s]*IBehaviorListener[^'"\s]*action=ajaxRefresh[^'"\s]*)['"]/g)].map((m) => m[1])));
    this.policy.refresh = new Set(values.map((value) => new URL(value.replaceAll('&amp;', '&'), this.page.url()).href)
      .filter((value) => new URL(value).origin === ORIGIN));
  }
  async buildId(path) {
    return this.page.evaluate((overview) => {
      const labels = [...document.querySelectorAll('.nav-link')]
        .map((label) => label.textContent.trim().match(/^Build \((?:id|Id|ID):(\d+)\)$/))
        .filter(Boolean);
      if (labels.length !== 1) return null;
      const id = labels[0][1];
      if (!overview) return id;
      const summaries = [...document.querySelectorAll('.build-summary')]
        .filter((box) => box.querySelector('.box-head')?.textContent.trim() === 'Summary');
      if (summaries.length !== 1) return null;
      const tables = summaries[0].querySelectorAll('table');
      if (tables.length !== 1) return null;
      const columns = [...tables[0].querySelectorAll('thead th')];
      const indices = columns.flatMap((cell, index) => cell.textContent.trim() === 'Id' ? [index] : []);
      if (indices.length !== 1) return null;
      const cells = tables[0].tBodies[0]?.rows[0]?.cells;
      return cells?.[indices[0]]?.textContent.trim() === id ? id : null;
    }, /^\/build\/\d+\/overview$/.test(path));
  }
  async read(path) {
    if (typeof path !== 'string' || !this.policy.readonly(path)) throw new AgentError('AGENT_PHASE');
    this.policy.refresh.clear();
    const expected = ORIGIN + path;
    const response = await this.page.goto(expected);
    if (this.page.url() !== expected || response?.request().redirectedFrom()) throw new AgentError('QB_READ_REDIRECTED');
    const id = path.match(/^\/build\/(\d+)/)?.[1];
    if (id && await this.buildId(path) !== id) throw new AgentError('QB_READ_ID_MISMATCH');
    await this.registerRefresh();
    let html;
    try { html = await this.page.evaluate(redactDOM); } catch { throw new AgentError('QB_EVIDENCE_REDACTION_FAILED'); }
    return { status: response?.status() ?? 0, html_redacted: checkRedacted(html) };
  }
  async snapshot() { return this.page.evaluate(formDOM); }
  async openForm(id) {
    const project = this.projects.get(id);
    if (!project) throw new AgentError('QB_FORM_CHANGED');
    this.currentProject = project;
    this.policy.refresh.clear();
    await this.page.goto(`${ORIGIN}/overview/${id}`);
    const expected = `QuickBuild - ${project.configuration_path}`;
    const title = await this.page.title();
    if (title !== expected && !title.startsWith(`${expected} - `)) throw new AgentError('QB_FORM_CHANGED');
    const run = this.page.locator('button[title="Run the configuration"]');
    if (await run.count() !== 1 || await this.page.locator('[title="Run the configuration"]').count() !== 1) {
      throw new AgentError('QB_FORM_CHANGED');
    }
    const onclick = await run.getAttribute('onclick');
    const match = typeof onclick === 'string' && /^var win = this\.ownerDocument\.defaultView \|\| this\.ownerDocument\.parentWindow; if \(win == window\) \{ window\.location\.href='((?:\.\.\/)*wicket\/page\?\d+-\d+\.ILinkListener-run)'; \} ;return false$/.exec(onclick);
    if (!match || match[0] !== onclick) throw new AgentError('QB_FORM_CHANGED');
    const url = new URL(match[1], this.page.url());
    if (url.origin !== ORIGIN || url.pathname !== '/wicket/page'
      || !/^\d+-\d+\.ILinkListener-run$/.test(url.search.slice(1))) throw new AgentError('QB_FORM_CHANGED');
    this.policy.runUrl = url.href;
    await run.click({ timeout: 30000 });
    await this.page.getByText('Specify Build Options', { exact: true }).waitFor({ timeout: 30000 });
    validateForm(await this.snapshot(), project.project_name);
    await this.registerRefresh();
    return { released: false };
  }
  fieldRow(name) {
    return this.page.locator('tr').filter({ has: this.page.locator('.form-label').filter({ hasText: new RegExp(`^${name}$`) }) }).filter({ has: this.page.locator('td.value') }).last();
  }
  async fill(fields) {
    if (!fields || canonical(Object.keys(fields).sort()) !== canonical([...FIELDS].sort())) throw new AgentError('QB_FORM_CHANGED');
    if (typeof fields['Build Package List'] !== 'string'
      || !/^[^\s@]+@[^\s@]+$/.test(fields['Build Package List'])
      || typeof fields['BUILD NOTES'] !== 'string'
      || !/^clang-fix-campaign request=\S+$/.test(fields['BUILD NOTES'])
      || fields['Add Package List'] !== '' || fields['Remove Package List'] !== ''
      || canonical(fields.TARGET_IMAGE) !== '[]'
      || canonical(fields.CHILD_CONFIGURATIONS) !== '["standard-armv7l:aarch64:x86_64"]') {
      throw new AgentError('QB_FORM_READBACK_MISMATCH');
    }
    let snapshotCount = 0;
    const expected = {};
    for (const name of FIELDS) {
      const form = await this.snapshot();
      const row = validateForm(form, this.currentProject.project_name)[name];
      const control = PALETTES.has(name) ? row.controls.find((c) => c.role === 'recorder') : row.controls[0];
      this.policy.beginField(callbackURL(control.callback, form.base));
      const box = this.fieldRow(name).locator('td.value');
      let value = fields[name];
      if (name === 'SNAPSHOT_NUM') {
        snapshotCount = control.options.length;
        if (value === '@freeze') {
          const selected = control.options.filter((option) => option.selected);
          if (!snapshotCount || selected.length !== 1 || !selected[0].text) throw new AgentError('QB_FORM_VALUE_UNAVAILABLE', name);
          value = selected[0].text;
          this.policy.endField();
          expected[`${name}/value`] = value;
          continue;
        }
      }
      if (PALETTES.has(name)) {
        if (!Array.isArray(value)) throw new AgentError('QB_FORM_READBACK_MISMATCH', name);
        const selected = row.controls.find((c) => c.role === 'selection').options.map((option) => option.text);
        if (canonical(selected) !== canonical(value)) {
          if (selected.length) {
            await box.locator('select[name$=":selection"]').selectOption(selected.map((label) => ({ label })));
            await box.locator('button.remove').click();
          }
          if (value.length) {
            const choices = await box.locator('select[name$=":choices"] option').allTextContents();
            if (value.some((item) => !choices.includes(item))) throw new AgentError('QB_FORM_VALUE_UNAVAILABLE', name);
            await box.locator('select[name$=":choices"]').selectOption(value.map((label) => ({ label })));
            await box.locator('button.add').click();
          }
        } else await box.locator('input[name$=":recorder"]').dispatchEvent('change');
      } else {
        const element = box.locator('input, select, textarea');
        if (control.tag === 'SELECT') {
          if (!control.options.some((option) => option.text === value)) throw new AgentError('QB_FORM_VALUE_UNAVAILABLE', name);
          await element.selectOption({ label: value });
        } else if (control.type === 'checkbox') {
          if (typeof value !== 'boolean') throw new AgentError('QB_FORM_READBACK_MISMATCH', name);
          if (control.checked === value) await element.dispatchEvent('change');
          else await element.setChecked(value);
        } else {
          if (typeof value !== 'string') throw new AgentError('QB_FORM_READBACK_MISMATCH', name);
          await element.fill(value); await element.dispatchEvent('change');
        }
      }
      const deadline = Date.now() + 30000;
      while (!this.policy.fieldFinished || Date.now() - this.policy.lastActivity < 1000) {
        if (Date.now() > deadline || this.runtime.failure) throw new AgentError('QB_FORM_CHANGED');
        await sleep(50);
      }
      this.policy.endField();
      expected[`${name}/${PALETTES.has(name) ? 'selection' : 'value'}`] = value;
    }
    const actual = readback(await this.snapshot(), this.currentProject.project_name);
    if (canonical(actual) !== canonical(expected)) throw new AgentError('QB_FORM_READBACK_MISMATCH');
    this.expected = expected;
    return { readback: actual, fingerprint: fingerprint(actual), snapshot_option_count: snapshotCount, released: false };
  }
  async submit(expectedFingerprint) {
    const form = await this.snapshot();
    const actual = readback(form, this.currentProject.project_name);
    if (fingerprint(actual) !== expectedFingerprint) throw new AgentError('QB_FORM_CHANGED');
    this.policy.submitUrl = form.action;
    try {
      await this.page.getByRole('button', { name: 'Ok', exact: true }).click({ timeout: 60000, noWaitAfter: true });
      const deadline = Date.now() + 10000;
      while (!this.policy.released && Date.now() < deadline) {
        if (this.runtime.failure || this.page.isClosed()) throw new AgentError('QB_BROWSER_UNAVAILABLE');
        await sleep(Math.min(50, Math.max(0, deadline - Date.now())));
      }
      if (!this.policy.released) throw new AgentError('QB_FORM_CHANGED');
      // Fetch releases before Chromium starts navigating; the old form is already loaded.
      await this.page.waitForURL((url) => url.href !== form.base, { waitUntil: 'load', timeout: 60000 });
      const url = new URL(this.page.url());
      const id = url.pathname.match(/^\/build\/(\d+)$/)?.[1];
      if (url.origin === ORIGIN && id && await this.buildId(url.pathname) === id) return { landed: 'build', build_id: id, released: true };
    } catch (error) { if (!this.policy.released) throw error; }
    return { landed: 'unknown', observed: pathShape(new URL(this.page.url()).pathname), messages: [], released: this.policy.released };
  }
}

export async function createRuntime(modulePath, chromiumPath, testOptions = {}) {
  const profile = await mkdtemp('/dev/shm/p5q-browser-');
  process.env.TMPDIR = profile;
  const env = { ...process.env, TMPDIR: profile };
  for (const name of ['DEBUG', 'PWDEBUG', 'NODE_OPTIONS', 'QB_COOKIE', 'QB_PASSWORD']) delete env[name];
  const runtime = { profile, failure: null, trace: [], policy: new Policy() };
  let closing;
  let launching;
  const stopSignal = () => { void runtime.close().finally(() => process.exit(0)); };
  runtime.close = () => closing ??= (async () => {
    try {
      const browser = runtime.browser ?? (launching ? await launching.catch(() => null) : null);
      if (browser) await browser.close();
    } finally {
      await rm(profile, { recursive: true, force: true });
      for (const signal of ['SIGINT', 'SIGTERM']) process.removeListener(signal, stopSignal);
    }
  })();
  for (const signal of ['SIGINT', 'SIGTERM']) process.once(signal, stopSignal);
  try {
    const { chromium } = await import(pathToFileURL(modulePath).href);
    if (closing) throw new AgentError('QB_BROWSER_UNAVAILABLE');
    launching = chromium.launch({ executablePath: chromiumPath, headless: false, env,
      ignoreDefaultArgs: ['--disable-popup-blocking'],
      args: ['--block-new-web-contents', '--disable-background-networking', '--disable-component-update',
        '--disable-sync', '--disable-breakpad', '--disable-crash-reporter', ...(testOptions.launchArgs ?? [])],
    });
    runtime.browser = await launching;
    runtime.context = await runtime.browser.newContext({ acceptDownloads: false, serviceWorkers: 'block' });
    await runtime.context.routeWebSocket('**/*', (socket) => { runtime.trace.push({ action: 'WEBSOCKET_DENIED' }); socket.close(); });
    await runtime.context.addInitScript(() => Object.defineProperty(window, 'open', {
      value: () => null, configurable: false, writable: false,
    }));
    runtime.page = await runtime.context.newPage();
    runtime.guards = await installGuards(runtime.browser, runtime.context, runtime.page, runtime.policy, () => {
      runtime.failure = 'QB_BROWSER_UNAVAILABLE'; void runtime.close();
    }, runtime.trace);
    return runtime;
  } catch { await runtime.close(); throw new AgentError('QB_BROWSER_UNAVAILABLE'); }
}

export function installFailureHandlers(finish) {
  const fatal = () => {
    process.stdout.write('{"ok":false,"error":"QB_BROWSER_UNAVAILABLE"}\n');
    void finish().finally(() => process.exit(1));
  };
  process.once('uncaughtException', fatal);
  process.once('unhandledRejection', fatal);
}

async function main() {
  for (const name of ['DEBUG', 'PWDEBUG', 'NODE_OPTIONS']) delete process.env[name];
  let runtime;
  const finish = async () => { if (runtime) await runtime.close(); };
  installFailureHandlers(finish);
  try {
    if (process.argv.length !== 4) throw new AgentError('QB_BROWSER_UNAVAILABLE');
    runtime = await createRuntime(process.argv[2], process.argv[3]);
    const agent = new Agent(runtime);
    const lines = createInterface({ input: process.stdin, crlfDelay: Infinity });
    for await (const line of lines) {
      let input;
      try { input = JSON.parse(line); } catch { process.stdout.write('{"ok":false,"error":"AGENT_PHASE"}\n'); continue; }
      const response = await agent.command(input);
      process.stdout.write(`${JSON.stringify(response)}\n`);
      if (agent.state === 'closed' || runtime.failure || ['QB_LOGIN_TIMEOUT', 'QB_LOGIN_ABORTED'].includes(response.error)) break;
    }
  } catch { process.stdout.write('{"ok":false,"error":"QB_BROWSER_UNAVAILABLE"}\n'); }
  finally { await finish(); }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) await main();
