import { createHash } from 'node:crypto';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { createInterface } from 'node:readline';
import { pathToFileURL } from 'node:url';

export const ORIGIN = 'https://quickbuild.tizen.org';
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const STATIC = ['/styles/', '/jquery/', '/scripts/', '/datetimepicker/', '/codemirror/',
  '/wicket/resource/', '/images/', '/favicon.ico'];
const DESTRUCTIVE = /I(Link|Behavior|FormSubmit|Resource)Listener[.0-9-]*-[A-Za-z0-9:_-]*(promote|cancel|stop|rerun|delete|abort)/i;
export const destructiveListener = (query) => DESTRUCTIVE.test(query);
const CALLBACK = /^\d+-\d+\.IBehaviorListener\.\d+-[A-Za-z0-9:_-]+$/;
const ACTION = /^\d+-\d+\.IFormSubmitListener-form$/;
export const FIELDS = ['BUILD_TYPE', 'REPO_TYPE', 'BUILD_REFERENCE', 'SNAPSHOT_NUM',
  'PROJECT_BRANCH', 'Immediate Stop With Error', 'CHILD_CONFIGURATIONS', 'Build Package List',
  'Add Package List', 'Remove Package List', 'TARGET_IMAGE', 'BUILD NOTES'];
const PALETTES = new Set(['CHILD_CONFIGURATIONS', 'TARGET_IMAGE']);

export class AgentError extends Error {
  constructor(code, field, check) { super(code); this.code = code; this.field = field; this.check = check; }
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
    this.assertField();
    let parsed;
    try { parsed = new URL(url); } catch { throw new AgentError('QB_FORM_CHANGED'); }
    if (parsed.origin !== ORIGIN || parsed.pathname !== '/wicket/page'
      || !CALLBACK.test(parsed.search.slice(1))) throw new AgentError('QB_FORM_CHANGED');
    this.fieldUrl = url; this.fieldFinished = false; this.fieldRequest = null;
    this.fieldWindow = { allowed: 0, denied: 0 };
  }
  assertField() {
    if (this.fieldWindow?.denied) throw new AgentError('QB_FORM_CHANGED');
  }
  endField() { this.fieldUrl = null; this.fieldRequest = null; this.fieldWindow = null; }
  invalidate() { this.runUrl = null; this.submitUrl = null; this.endField(); }
  allow(m, requestId = '') {
    const url = `${m.protocol}//${m.host}${m.path}${m.query ? `?${m.query}` : ''}`;
    // Close both login channels even when the redirect itself is denied (307/308).
    if (this.loginPostRequests.has(requestId)
      && m.response_status >= 300 && m.response_status < 400) this.loginPostsClosed = true;
    if (m.protocol !== 'https:' || m.host !== 'quickbuild.tizen.org'
      || m.resource_type === 'WebSocket' || m.path.startsWith('/rest/')
      || destructiveListener(m.query) || /ILinkListener-form-cancel/i.test(m.query)
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
    if (['read', 'open_form', 'fill'].includes(this.phase)
      && m.method === 'GET' && this.readonly(m.path) && !m.query) return true;
    if (this.phase === 'open_form') {
      if (m.method === 'GET' && url === this.runUrl) { this.runUrl = null; return true; }
      return m.method === 'GET' && m.path === '/wicket/page' && /^\d+$/.test(m.query);
    }
    if (this.phase === 'fill') {
      const suffix = this.fieldUrl !== null && url.startsWith(this.fieldUrl)
        ? url.slice(this.fieldUrl.length) : null;
      if (m.method === 'POST' && (suffix === ''
        || suffix !== null && suffix.match(/^&random=0\.\d{1,20}$/)?.[0] === suffix)) {
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
      if (allowed) policy.lastActivity = Date.now();
      if (!response && policy.fieldWindow && m.method === 'POST' && /IBehaviorListener/.test(m.query)) {
        policy.fieldWindow[allowed ? 'allowed' : 'denied'] += 1;
      }
      if (!allowed) trace.push({ phase: policy.phase, path: pathShape(m.path), action: 'DENIED' });
      if (allowed && !response) policy.active.add(requestId);
      if (response || !allowed) policy.active.delete(requestId);
      const navigation = policy.readNavigation;
      const matchesRead = allowed && policy.phase === 'read' && navigation
        && frames.parents.get(frameId) === null && m.resource_type === 'Document' && m.method === 'GET'
        && m.redirect_source === null
        && `${m.protocol}//${m.host}${m.path}${m.query ? `?${m.query}` : ''}` === navigation.url;
      if (matchesRead && !response && navigation.requestId === null) {
        navigation.requestId = requestId; navigation.frameId = frameId;
      }
      guarded((async () => {
        // Capture the original bytes while this exact navigation is paused.
        // Playwright's response.body() may already have transcoded invalid text.
        if (matchesRead && response && navigation.requestId === requestId && navigation.frameId === frameId
          && !(m.response_status >= 300 && m.response_status < 400)) {
          try {
            const result = await root.send('Fetch.getResponseBody', { requestId });
            if (result.base64Encoded !== true || typeof result.body !== 'string') throw new Error('non-byte body');
            const body = Buffer.from(result.body, 'base64');
            if (body.toString('base64') !== result.body) throw new Error('invalid base64 body');
            if (policy.readNavigation === navigation && policy.phase === 'read') navigation.body = body;
            else navigation.failed = true;
          } catch { navigation.failed = true; }
        }
        await root.send(!allowed ? 'Fetch.failRequest' : response ? 'Fetch.continueResponse' : 'Fetch.continueRequest',
          !allowed ? { requestId, errorReason: 'BlockedByClient' } : { requestId });
        if (response && requestId === policy.fieldRequest && allowed) policy.fieldFinished = true;
      })());
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

// This function receives an inert document, never the live DOM.
export function redactDOM(document, facts = null, details = false) {
  const normalize = value => value.replace(/^[\s\u00a0]+|[\s\u00a0]+$/g, '');
  const root = document.documentElement;
  const identities = new Set();
  const identityNodes = new Map();
  const secrets = new Set();
  const remember = (set, value) => { if (value && !['<USER>', '<REDACTED>'].includes(value)) set.add(value); };
  for (const element of root.querySelectorAll('span, div')) {
    if ([...element.childNodes].some((node) => node.nodeType === 3 && /^\s*Welcome!/.test(node.textContent))) {
      const value = normalize(element.textContent.replace(/^\s*Welcome!\s*/, ''));
      remember(identities, value); element.textContent = 'Welcome! <USER>';
      identityNodes.set(element, 'Welcome! ');
    }
  }
  for (const table of root.querySelectorAll('table')) {
    let columns = [];
    for (const row of table.rows) {
      if (row.closest('table') !== table) continue;
      const cells = [...row.cells];
      if (cells.some(cell => cell.tagName === 'TH')) columns = cells.flatMap((cell, index) =>
        ['Triggered By', 'Requested By'].includes(normalize(cell.textContent)) ? [index] : []);
      const targets = columns.map(index => cells[index]).filter(cell => cell?.tagName === 'TD');
      const adjacent = cells.findIndex(cell => cell.tagName === 'TD' && normalize(cell.textContent) === 'Triggered By');
      if (adjacent >= 0 && cells[adjacent + 1]) targets.push(cells[adjacent + 1]);
      for (const cell of new Set(targets)) {
        remember(identities, normalize(cell.textContent)); cell.textContent = '<USER>';
        identityNodes.set(cell, '');
      }
    }
  }
  const sensitive = /password|passwd|secret|token|credential|authorization|cookie|session|csrf|xsrf/i;
  for (const element of root.querySelectorAll('*')) {
    const name = element.getAttribute('name') ?? '';
    const isInput = element.tagName === 'INPUT';
    const hidden = isInput && /^(hidden|password)$/i.test(element.getAttribute('type') ?? '');
    const recorder = /:palette:recorder$/.test(name);
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
  const scrub = text => {
    for (const value of [...secrets].sort((a, b) => b.length - a.length)) {
      for (const spelling of new Set([value, escaped(value), encodeURIComponent(value), JSON.stringify(value).slice(1, -1)])) {
        text = text.split(spelling).join('&lt;REDACTED&gt;');
      }
    }
    text = text.replace(/^\s*(?:set-cookie|cookie|authorization)\s*:[^\r\n]*/gim, '&lt;REDACTED&gt;')
      .replace(/JSESSIONID_8810\s*=/gi, 'redacted_session:');
    if ([...secrets].some(value => value && decode(text).includes(value))
      || /JSESSIONID_8810\s*=/i.test(text)) throw new Error('QB_EVIDENCE_REDACTION_FAILED');
    return text;
  };
  const walk = value => typeof value === 'string' ? scrub(value)
    : Array.isArray(value) ? value.map(walk)
      : value && typeof value === 'object' ? Object.fromEntries(Object.entries(value).map(([k, v]) => [scrub(k), walk(v)])) : value;
  html = scrub(html);
  // Exclude registered positions, including the masks we just generated, from
  // the outside count. This document is inert and html is already serialized.
  for (const [element, empty] of identityNodes) element.textContent = empty;
  const outsideHTML = decode(scrub(root.outerHTML));
  const outside = [...identities].reduce((count, value) => count + [...outsideHTML.matchAll(identityPattern(value))].length, 0);
  return details ? { html_redacted: html, facts: walk(facts), outside_identity_count: outside } : html;
}

// A fresh world is requested for every read, so a navigation can never leave a
// cached context id referring to the previous document.
export class TrustedPage {
  constructor(context, page) { this.context = context; this.page = page; }
  async run(fn, raw = null, args = []) {
    let session;
    try {
      session = await this.context.newCDPSession(this.page);
      const { frameTree } = await session.send('Page.getFrameTree');
      const { executionContextId } = await session.send('Page.createIsolatedWorld', {
        frameId: frameTree.frame.id, worldName: 'p5q-trusted',
      });
      const expression = `(() => { const document = ${raw === null ? 'globalThis.document'
        : `new DOMParser().parseFromString(${JSON.stringify(raw)}, "text/html")`};
        const buildDOM = ${buildDOM.toString()};
        const redactDOM = ${redactDOM.toString()};
        try { return { ok: true, value: (${fn.toString()})(document, ...${JSON.stringify(args)}) }; }
        catch (error) { return { ok: false, error: error.message === 'QB_EVIDENCE_REDACTION_FAILED'
          ? 'QB_EVIDENCE_REDACTION_FAILED' : 'QB_TRUSTED_CONTEXT_UNAVAILABLE' }; } })()`;
      const result = await session.send('Runtime.evaluate', { expression, contextId: executionContextId, returnByValue: true });
      if (result.exceptionDetails) throw new Error('trusted evaluation failed');
      if (!result.result.value?.ok) throw new AgentError(result.result.value?.error === 'QB_EVIDENCE_REDACTION_FAILED'
        ? 'QB_EVIDENCE_REDACTION_FAILED' : 'QB_TRUSTED_CONTEXT_UNAVAILABLE');
      return result.result.value.value;
    } catch (error) {
      if (error instanceof AgentError) throw error;
      throw new AgentError('QB_TRUSTED_CONTEXT_UNAVAILABLE');
    }
    finally { if (session) await session.detach().catch(() => {}); }
  }
}

export async function responseText(response, raw) {
  try {
    if (!response || !Buffer.isBuffer(raw)) throw new Error('missing response bytes');
    const contentType = await response.headerValue('content-type') ?? '';
    const charset = contentType.match(/(?:^|;)\s*charset\s*=\s*(?:"([^"]+)"|'([^']+)'|([^;\s]+))/i);
    if (/(?:^|;)\s*charset\s*=/i.test(contentType) && !charset) throw new Error('empty charset');
    return new TextDecoder(charset?.[1] ?? charset?.[2] ?? charset?.[3] ?? 'utf-8', { fatal: true }).decode(raw);
  } catch { throw new AgentError('QB_TRUSTED_CONTEXT_UNAVAILABLE'); }
}

export function checkRedacted(html) {
  if (typeof html !== 'string' || /JSESSIONID_8810\s*=|^\s*(set-cookie|cookie|authorization)\s*:/im.test(html)) {
    throw new AgentError('QB_EVIDENCE_REDACTION_FAILED');
  }
  return html;
}

export function formDOM(document = globalThis.document) {
  const forms = [...document.forms].filter((form) => /IFormSubmitListener-form/.test(form.action));
  if (forms.length !== 1) return null;
  const form = forms[0];
  const rows = [...form.querySelectorAll('.form-label')].map((label) => {
    const row = label.closest('tr');
    const box = row?.querySelector('td.value');
    if (!box) return null;
    const viewers = [...box.querySelectorAll('.property-viewer')];
    const controls = [...box.querySelectorAll('input, select, textarea')].map((element) => ({
      id: element.id, tag: element.tagName, type: element.type,
      name: element.name, callback: element.getAttribute('onchange'),
      value: element.value, checked: element.checked,
      options: element.tagName === 'SELECT' ? [...element.options].map((option) => ({
        text: option.textContent, value: option.value, selected: option.selected,
      })) : [],
    }));
    const buttons = [...box.querySelectorAll('button')].map((button) => ({
      className: button.className, code: button.getAttribute('onclick'),
    }));
    return { label: label.textContent, viewers: viewers.map((v) => v.textContent), controls, buttons };
  });
  return { title: document.title, body_text: document.body.textContent,
    action: form.action, rows, base: document.baseURI };
}

// Run only in Node, never serialized into the page's main world.
export function normalizeFormDOM(raw) {
  if (raw === null) return null;
  const { body_text, ...form } = raw;
  return { ...form, heading: body_text.includes('Specify Build Options'),
    rows: form.rows.map(row => row === null ? null : ({ ...row,
      label: row.label.trim(), viewers: row.viewers.map(value => value.trim()),
      controls: row.controls.map(({ name, ...control }) => ({ ...control, role: name?.split(':').at(-1),
        options: control.options.map(option => ({ ...option, text: option.text.trim() })),
      })),
    })),
  };
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
  if (!form?.heading) throw new AgentError('QB_FORM_CHANGED', undefined, 'heading');
  if (!Array.isArray(form.rows) || form.rows.some(row => !row)) throw new AgentError('QB_FORM_CHANGED', undefined, 'row');
  const labels = form.rows.map((row) => row.label);
  if (new Set(labels).size !== FIELDS.length + 1
    || labels.some((name) => ![...FIELDS, 'PROJECT_NAME'].includes(name))) throw new AgentError('QB_FORM_CHANGED', undefined, 'labels');
  const grouped = Object.fromEntries([...new Set(labels)].map((name) => [name, form.rows.filter((row) => row.label === name)]));
  if (Object.values(grouped).some((rows) => rows.length !== 1)) throw new AgentError('QB_FORM_CHANGED', undefined, 'labels');
  for (const row of form.rows) {
    if (row.label === 'PROJECT_NAME') {
      if (row.controls.length || row.viewers.length !== 1 || row.viewers[0] !== projectName) throw new AgentError('QB_FORM_CHANGED', undefined, 'project_name');
      continue;
    }
    if (PALETTES.has(row.label)) {
      if (row.controls.length !== 3 || canonical(row.controls.map((c) => c.role).sort())
        !== canonical(['choices', 'recorder', 'selection'])) throw new AgentError('QB_FORM_CHANGED', undefined, 'controls');
    } else if (row.controls.length !== 1) throw new AgentError('QB_FORM_CHANGED', undefined, 'controls');
    const callback = PALETTES.has(row.label) ? row.controls.find((c) => c.role === 'recorder') : row.controls[0];
    try { callbackURL(callback.callback, form.base); }
    catch { throw new AgentError('QB_FORM_CHANGED', undefined, 'callback'); }
  }
  let action;
  try { action = new URL(form.action); } catch { throw new AgentError('QB_FORM_CHANGED', undefined, 'action'); }
  if (action.origin !== ORIGIN || action.pathname !== '/wicket/page' || !ACTION.test(action.search.slice(1))) throw new AgentError('QB_FORM_CHANGED', undefined, 'action');
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
      if (selected.length > 1) throw new AgentError('QB_FORM_CHANGED');
      if (selected.length === 0 ? recorder !== ''
        : !/^(?:[\da-fA-F]{2})+$/.test(recorder)
          || decoded !== selected[0]) {
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

export function buildDOM(document) {
  return {
    labels: [...document.querySelectorAll('.nav-link')].map(label => label.textContent),
    summaries: [...document.querySelectorAll('.build-summary')].map(box => ({
      heading: box.querySelector('.box-head')?.textContent,
      tables: [...box.querySelectorAll('table')].map(table => ({
        columns: [...table.querySelectorAll('thead th')].map(cell => cell.textContent),
        cells: [...(table.tBodies[0]?.rows[0]?.cells ?? [])].map(cell => cell.textContent),
      })),
    })),
  };
}

export function verifiedBuildId(raw, path) {
  const labels = raw.labels.map(text => text.trim().match(/^Build \((?:id|Id|ID):(\d+)\)$/)).filter(Boolean);
  if (labels.length !== 1) return null;
  const id = labels[0][1];
  if (!/^\/build\/\d+\/overview$/.test(path)) return id;
  const summaries = raw.summaries.filter(box => box.heading?.trim() === 'Summary');
  if (summaries.length !== 1 || summaries[0].tables.length !== 1) return null;
  const table = summaries[0].tables[0];
  const indices = table.columns.flatMap((text, index) => text.trim() === 'Id' ? [index] : []);
  return indices.length === 1 && table.cells[indices[0]]?.trim() === id ? id : null;
}

export function formFacts(form, projectName) {
  const rows = form?.rows ?? [];
  const labels = rows.filter(Boolean).map(row => row.label);
  let first = !form?.heading ? 'heading' : rows.some(row => !row) ? 'row' : null;
  const missing = [...FIELDS, 'PROJECT_NAME'].filter(name => !labels.includes(name));
  const extra = labels.filter(name => ![...FIELDS, 'PROJECT_NAME'].includes(name));
  const duplicate = labels.filter((name, index) => labels.indexOf(name) !== index);
  if (!first && (missing.length || extra.length || duplicate.length)) first = 'labels';
  const facts = rows.filter(Boolean).map(row => {
    const controls = row.controls.map(control => {
      let valid = true;
      try { callbackURL(control.callback, form.base); } catch { valid = false; }
      return { tag: control.tag, type: control.type, role: control.role, callback_valid: valid,
        callback: control.callback };
    });
    if (!first && row.label === 'PROJECT_NAME'
      && (row.controls.length || row.viewers.length !== 1 || row.viewers[0] !== projectName)) first = 'project_name';
    if (!first && row.label !== 'PROJECT_NAME') {
      if (PALETTES.has(row.label)
        ? canonical(controls.map(c => c.role).sort()) !== canonical(['choices', 'recorder', 'selection'])
        : controls.length !== 1) first = 'controls';
      else if (!controls.find(c => !PALETTES.has(row.label) || c.role === 'recorder')?.callback_valid) first = 'callback';
    }
    return { label: row.label, control_count: controls.length, controls };
  });
  if (!first) {
    try { validateForm(form, projectName); } catch { first = 'action'; }
  }
  return { labels, missing, extra, duplicate, rows: facts, first_failed_check: first ?? 'field_window_or_readback' };
}

export class Agent {
  constructor(runtime) {
    this.runtime = runtime; this.page = runtime.page; this.policy = runtime.policy;
    this.trusted = new TrustedPage(runtime.context, runtime.page);
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
    this.rawRead = null;
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
      if (command === 'read' && response.error === 'QB_READ_ID_MISMATCH'
        || ['open_form', 'fill'].includes(command) && response.error === 'QB_FORM_CHANGED') {
        this.policy.invalidate();
        this.policy.phase = 'read';
        try { response.diagnostic = await this.diagnostic(command, error.check); }
        catch { response.diagnostic_failed = true; }
      }
      if (error instanceof AgentError && error.field) response.field = error.field;
      if (command === 'fill' && response.error === 'QB_FORM_VALUE_UNAVAILABLE' && error.field === 'SNAPSHOT_NUM') {
        response.snapshot_state = this.snapshotState;
        response.released = false;
      }
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
        const status = await this.trusted.run(document => ({
          password: document.querySelectorAll('input[type=password]').length,
          links: [...document.querySelectorAll('a')].map(link => link.textContent),
        }));
        if (new URL(this.page.url()).pathname !== '/signin' && status.password === 0
          && status.links.some(text => text.trim() === 'Sign Out')) return {};
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
  async buildId(path, raw = null) { return verifiedBuildId(await this.trusted.run(buildDOM, raw), path); }
  async passive(raw, facts = null) {
    const result = await this.trusted.run(redactDOM, raw, [facts, true]);
    checkRedacted(result.html_redacted);
    this.runtime.trace.push({ action: 'IDENTITY_OUTSIDE_REGISTERED', count: result.outside_identity_count });
    return result;
  }
  async diagnostic(command, check) {
    const raw = command === 'read' ? this.rawRead
      : await this.trusted.run(document => document.documentElement.outerHTML);
    if (typeof raw !== 'string') throw new AgentError('QB_TRUSTED_CONTEXT_UNAVAILABLE');
    let facts;
    if (command === 'read') {
      const info = await this.trusted.run(buildDOM, raw);
      facts = { labels: info.labels, summary_count: info.summaries.length, first_failed_check: 'build_id' };
    } else facts = formFacts(normalizeFormDOM(await this.trusted.run(formDOM, raw)), this.currentProject?.project_name);
    if (check) facts.first_failed_check = check;
    const redacted = await this.passive(raw, facts);
    return { html_redacted: redacted.html_redacted, facts: redacted.facts };
  }
  async read(path) {
    this.rawRead = null;
    if (typeof path !== 'string' || !this.policy.readonly(path)) throw new AgentError('AGENT_PHASE');
    const expected = ORIGIN + path;
    const navigation = { url: expected, requestId: null, frameId: null, body: null, failed: false };
    this.policy.readNavigation = navigation;
    let response;
    try {
      response = await this.page.goto(expected);
      if (this.page.url() !== expected || response?.request().redirectedFrom()) throw new AgentError('QB_READ_REDIRECTED');
      if (this.policy.readNavigation !== navigation || navigation.failed || !navigation.requestId
        || response?.url() !== expected) throw new AgentError('QB_TRUSTED_CONTEXT_UNAVAILABLE');
      this.rawRead = await responseText(response, navigation.body);
    } finally {
      navigation.body = null;
      if (this.policy.readNavigation === navigation) this.policy.readNavigation = null;
    }
    const result = await this.trusted.run(document => ({ build: buildDOM(document),
      redacted: redactDOM(document, null, true) }), this.rawRead);
    const id = path.match(/^\/build\/(\d+)/)?.[1];
    if (id && verifiedBuildId(result.build, path) !== id) throw new AgentError('QB_READ_ID_MISMATCH');
    const redacted = result.redacted;
    checkRedacted(redacted.html_redacted);
    this.runtime.trace.push({ action: 'IDENTITY_OUTSIDE_REGISTERED', count: redacted.outside_identity_count });
    return { status: response.status(), html_redacted: redacted.html_redacted };
  }
  async snapshot() { return normalizeFormDOM(await this.trusted.run(formDOM)); }
  async openForm(id) {
    const project = this.projects.get(id);
    if (!project) throw new AgentError('QB_FORM_CHANGED');
    this.currentProject = project;
    await this.page.goto(`${ORIGIN}/overview/${id}`);
    const expected = `QuickBuild - ${project.configuration_path}`;
    const config = await this.trusted.run(document => ({ title: document.title,
      runs: [...document.querySelectorAll('[title="Run the configuration"]')].map(element => ({
        tag: element.tagName, onclick: element.getAttribute('onclick'),
      })),
    }));
    const title = config.title;
    if (title !== expected && !title.startsWith(`${expected} - `)) throw new AgentError('QB_FORM_CHANGED', undefined, 'configuration_title');
    const run = this.page.locator('button[title="Run the configuration"]');
    if (config.runs.length !== 1 || config.runs[0].tag !== 'BUTTON') {
      throw new AgentError('QB_FORM_CHANGED', undefined, 'run_control');
    }
    const onclick = config.runs[0].onclick;
    const match = typeof onclick === 'string' && /^var win = this\.ownerDocument\.defaultView \|\| this\.ownerDocument\.parentWindow; if \(win == window\) \{ window\.location\.href='((?:\.\.\/)*wicket\/page\?\d+-\d+\.ILinkListener-run)'; \} ;return false$/.exec(onclick);
    if (!match || match[0] !== onclick) throw new AgentError('QB_FORM_CHANGED', undefined, 'run_onclick');
    const url = new URL(match[1], this.page.url());
    if (url.origin !== ORIGIN || url.pathname !== '/wicket/page'
      || !/^\d+-\d+\.ILinkListener-run$/.test(url.search.slice(1))) throw new AgentError('QB_FORM_CHANGED');
    this.policy.runUrl = url.href;
    await run.click({ timeout: 30000 });
    const deadline = Date.now() + 30000;
    while (!(await this.snapshot())?.heading) {
      if (Date.now() >= deadline || this.runtime.failure) throw new AgentError('QB_FORM_CHANGED');
      await sleep(50);
    }
    validateForm(await this.snapshot(), project.project_name);
    return { released: false };
  }
  fieldRow(name) {
    return this.page.locator('tr').filter({ has: this.page.locator('.form-label').filter({ hasText: new RegExp(`^${name}$`) }) }).filter({ has: this.page.locator('td.value') }).last();
  }
  async fill(fields) {
    this.snapshotState = null;
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
        const selectedText = control.options.filter(option => option.selected).map(option => option.text.trim());
        this.snapshotState = { selected: selectedText.every(text => text.length <= 200 && /^[A-Za-z0-9._:+-]+$/.test(text))
          ? selectedText : null, option_count: snapshotCount };
        if (value === '@freeze') {
          const selected = control.options.filter((option) => option.selected);
          if (!snapshotCount || selected.length !== 1 || !selected[0].text) throw new AgentError('QB_FORM_VALUE_UNAVAILABLE', name);
          value = selected[0].text;
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
            const choices = row.controls.find(c => c.role === 'choices').options.map(option => option.text);
            if (value.some((item) => !choices.includes(item))) throw new AgentError('QB_FORM_VALUE_UNAVAILABLE', name);
            await box.locator('select[name$=":choices"]').selectOption(value.map((label) => ({ label })));
            await box.locator('button.add').click();
          }
        } else await box.locator('input[name$=":recorder"]').dispatchEvent('change');
      } else {
        const element = box.locator('input, select, textarea');
        if (control.tag === 'SELECT') {
          const options = control.options.filter(option => option.text === value);
          if (options.length !== 1) throw new AgentError('QB_FORM_VALUE_UNAVAILABLE', name);
          if (options[0].selected) await element.dispatchEvent('change');
          else await element.selectOption({ value: options[0].value });
        } else if (control.type === 'checkbox') {
          if (typeof value !== 'boolean') throw new AgentError('QB_FORM_READBACK_MISMATCH', name);
          if (control.checked === value) await element.dispatchEvent('change');
          else if (value) await element.check();
          else await element.uncheck();
        } else {
          if (typeof value !== 'string') throw new AgentError('QB_FORM_READBACK_MISMATCH', name);
          if (control.value === value) await element.dispatchEvent('change');
          else { await element.fill(value); await element.blur(); }
        }
      }
      const deadline = Date.now() + 30000;
      while (!this.policy.fieldFinished || Date.now() - this.policy.lastActivity < 1000) {
        this.policy.assertField();
        if (Date.now() > deadline || this.runtime.failure) throw new AgentError('QB_FORM_CHANGED');
        await sleep(50);
      }
      this.policy.assertField();
      expected[`${name}/${PALETTES.has(name) ? 'selection' : 'value'}`] = value;
    }
    const actual = readback(await this.snapshot(), this.currentProject.project_name);
    this.policy.assertField();
    this.policy.endField();
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

export async function startupSelfTest(runtime, version, syntheticCount = 1) {
  try {
    await runtime.page.setContent(`<select id="select" onchange="this.dataset.changes=+(this.dataset.changes||0)+${syntheticCount}"><option>a</option><option>b</option></select>
      <input id="check" type="checkbox" onchange="this.dataset.changes=+(this.dataset.changes||0)+${syntheticCount}">
      <textarea id="text" onchange="this.dataset.changes=+(this.dataset.changes||0)+${syntheticCount}"></textarea>`);
    await runtime.page.locator('#select').selectOption({ label: 'b' });
    await runtime.page.locator('#check').check();
    await runtime.page.locator('#text').fill('changed');
    await runtime.page.locator('#text').blur();
    const counts = await new TrustedPage(runtime.context, runtime.page).run(document =>
      [...document.querySelectorAll('#select,#check,#text')].map(element => Number(element.dataset.changes ?? 0)));
    if (canonical(counts) !== '[1,1,1]' || runtime.failure) throw new Error('framework mismatch');
    runtime.trace.push({ action: 'FRAMEWORK_SELF_TEST', playwright_version: version, counts });
  } catch {
    await runtime.close();
    process.stderr.write('浏览器框架的设值行为与设计不符,升级 Playwright 后须重新验证\n');
    throw new AgentError('QB_BROWSER_UNAVAILABLE');
  }
}

export async function createRuntime(modulePath, chromiumPath, testOptions = {}) {
  // Use a disposable, fully guarded browser for the synthetic page. Closing it
  // avoids weakening the new-page guard when starting the working page.
  const probe = await launchRuntime(modulePath, chromiumPath, testOptions);
  try {
    const pkg = JSON.parse(await readFile(new URL('./package.json', pathToFileURL(modulePath)), 'utf8'));
    await startupSelfTest(probe, pkg.version);
  } catch {
    throw new AgentError('QB_BROWSER_UNAVAILABLE');
  } finally { await probe.close(); }
  const runtime = await launchRuntime(modulePath, chromiumPath, testOptions);
  runtime.trace.push(...probe.trace);
  return runtime;
}

async function launchRuntime(modulePath, chromiumPath, testOptions = {}) {
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
