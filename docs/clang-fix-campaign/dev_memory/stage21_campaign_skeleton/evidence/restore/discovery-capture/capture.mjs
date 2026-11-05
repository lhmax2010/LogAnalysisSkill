// RESTORE-08 evidence only. Production agent and guards remain unmodified.
import { spawn } from 'node:child_process';
import { access, mkdir } from 'node:fs/promises';
import { createInterface } from 'node:readline';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, resolve } from 'node:path';
import { performance } from 'node:perf_hooks';

const HERE = dirname(fileURLToPath(import.meta.url));
export const ROOT = resolve(HERE, '../../../../../../..');
const agentModule = await import(pathToFileURL(`${ROOT}/tizen-qb-verify/scripts/tizen_qb_verify/qb_browser_agent.mjs`));
const { Agent, AgentError, ORIGIN, createRuntime, responseText, destructiveListener } = agentModule;
const { DEFAULTS, PROJECT } = await import(pathToFileURL(`${ROOT}/docs/clang-fix-campaign/spikes/p5q_c5_tools.mjs`));
export const PATHS = Object.freeze(['/overview/1917', '/build/1204735/overview',
  '/build/1204735/variables', '/build/1204736/overview', '/build/1204736/variables',
  '/build/1204736/html_report']);
export const LIMIT = 64 * 1024 * 1024;
const fail = code => { throw new AgentError(code); };
export const fixedError = error => error instanceof AgentError ? error.code
  : ['TimeoutError', 'TargetClosedError'].includes(error?.name) ? error.name : 'CAPTURE_ERROR';

export function exactLink(href, base) {
  if (typeof href !== 'string' || !href || href !== href.trim() || /[\x00-\x1f\x7f\\]/.test(href)
    || /%(?:2f|5c|2e|25)/i.test(href) || /(?:^|\/)\.\.(?:\/|$)/.test(href)) fail('CAPTURE_PATH_UNSUPPORTED');
  let url;
  try { url = new URL(href, base); } catch { fail('CAPTURE_PATH_UNSUPPORTED'); }
  if (url.origin !== ORIGIN || url.username || url.password || url.search || url.hash
    || !url.pathname.startsWith('/download/1204736/html/')) fail('CAPTURE_PATH_UNSUPPORTED');
  return url.href;
}

// Installed before the first navigation. Only the current main-document request is widened.
export function capturePolicy(policy, rootFrame, requestFrames) {
  const original = policy.allow.bind(policy);
  const scope = { current: null };
  policy.allow = (m, requestId) => {
    if (policy.phase === 'login') return original(m, requestId);
    if (m.resource_type === 'Document') {
      const url = `${m.protocol}//${m.host}${m.path}${m.query ? `?${m.query}` : ''}`;
      return policy.phase === 'read' && m.method === 'GET' && !m.query
        && (PATHS.includes(m.path) || m.path.startsWith('/download/1204736/html/'))
        && url === scope.current && m.protocol === 'https:' && m.host === 'quickbuild.tizen.org'
        && requestFrames.get(requestId) === rootFrame()
        && !destructiveListener(m.query) && ![307, 308].includes(m.response_status)
        && (m.response_status === null || policy.active.has(requestId));
    }
    // No iframe reading or XHR/fetch path extension. Existing static resource rules only.
    if (/^\/build\/|^\/overview\/|^\/download\//.test(m.path)) return false;
    return original(m, requestId);
  };
  return scope;
}

export class Writer {
  constructor(output) {
    this.output = output;
    this.child = spawn(`${ROOT}/.venv/bin/python`, [`${HERE}/redact_capture.py`],
      { cwd: ROOT, stdio: ['pipe', 'pipe', 'ignore'] });
    this.lines = createInterface({ input: this.child.stdout });
    this.iterator = this.lines[Symbol.asyncIterator]();
    this.exit = new Promise(resolveExit => this.child.on('close', resolveExit));
    this.child.on('error', () => {});
  }
  async write(name, text, mode = 'json') {
    this.child.stdin.write(JSON.stringify({ path: `${this.output}/${name}`, text, mode }) + '\n');
    const reply = await this.iterator.next();
    if (reply.done) fail('QB_EVIDENCE_REDACTION_FAILED');
    let value;
    try { value = JSON.parse(reply.value); } catch { fail('QB_EVIDENCE_REDACTION_FAILED'); }
    if (!value.ok) fail('QB_EVIDENCE_REDACTION_FAILED');
    return { file: name, ...value };
  }
  async close() { this.child.stdin.end(); await this.exit; }
}

// Executed only in the production TrustedPage isolated world, on inert response HTML.
export function facts(document) {
  return {
    title: document.title,
    links: [...document.querySelectorAll('a[href]')].map(a => ({ href: a.getAttribute('href'), text: a.textContent })),
    copy_paths: [...document.querySelectorAll('script')].flatMap(s =>
      [...s.textContent.matchAll(/onCopyClipboardLinkDomReady\('[^']*',\s*'([^']+)'\)/g)].map(m => m[1])),
    iframes: [...document.querySelectorAll('iframe')].map(e => e.getAttribute('src')),
    tables: [...document.querySelectorAll('table')].map(table => [...table.rows].map(row => ({
      cells: [...row.cells].map(cell => cell.textContent),
      links: [...row.querySelectorAll('a[href]')].map(a => ({ href: a.getAttribute('href'),
        text: a.textContent, class_name: a.className })),
    }))),
  };
}

export function verifyPage(path, value) {
  const parent = PROJECT.configuration_path;
  const expected = path.includes('/1204736/') ? parent.replace(/TRIGGER$/, 'build') : parent;
  if (path.endsWith('/overview') || path === '/overview/1917') {
    if (value.copy_paths.length !== 1 || value.copy_paths[0] !== expected
      || !value.title.startsWith(`QuickBuild - ${expected}`)) fail('CAPTURE_CONFIGURATION_MISMATCH');
  }
  if (path === '/build/1204735/overview') {
    const tables = value.tables.filter(rows => rows[0]?.cells.map(s => s.trim()).join('|')
      === 'Repository-Architecture|QB Build URL|Build Result|Build Profiling');
    if (tables.length !== 1 || !tables[0].slice(1).some(row => row.links.some(a => {
      try { return new URL(a.href, ORIGIN + path).href === ORIGIN + '/build/1204736'; } catch { return false; }
    }))) fail('CAPTURE_CHILD_MISMATCH');
  }
  if (path === '/build/1204736/variables') {
    const rows = value.tables.flat();
    const trigger = rows.filter(row => row.cells[0]?.trim() === 'TRIGGER_ID');
    if (trigger.length !== 1 || trigger[0].cells.at(-1)?.trim() !== '1204735') fail('CAPTURE_CHILD_MISMATCH');
    const packages = rows.filter(row => row.cells[0]?.trim() === 'BUILD_PKG_LIST');
    if (packages.length !== 1 || !/platform\/upstream\/zlib@[0-9a-f]{40}/.test(packages[0].cells.at(-1))) fail('CAPTURE_PACKAGE_MISMATCH');
  }
}

export function logLink(value, base) {
  const matches = value.tables.flat().filter(row => row.cells[0]?.trim() === 'zlib')
    .flatMap(row => row.links.filter(a => /(?:^|\s)failed(?:\s|$)/.test(a.class_name)))
    .map(link => exactLink(link.href, base))
    .filter(url => /\/logfiles\/standard\/armv7l\/zlib\.txt$/.test(new URL(url).pathname));
  if (matches.length !== 1) fail('CAPTURE_LOG_LINK_MISMATCH');
  return matches[0];
}

export function decodeText(bytes) {
  if (!Buffer.isBuffer(bytes)) fail('QB_TRUSTED_CONTEXT_UNAVAILABLE');
  if (bytes.length > LIMIT) fail('QB_TEXT_TOO_LARGE');
  try { return new TextDecoder('utf-8', { fatal: true }).decode(bytes); }
  catch { fail('QB_TEXT_ENCODING_UNSUPPORTED'); }
}

export async function capture(output, runtimeFactory = () => createRuntime(DEFAULTS.playwright, DEFAULTS.chromium),
  paths = PATHS) {
  if (paths !== PATHS && !(paths.length === 1 && paths[0] === PATHS.at(-1))) fail('CAPTURE_PATH_UNSUPPORTED');
  await mkdir(output, { recursive: false });
  const writer = new Writer(output);
  const record = { started_utc: new Date().toISOString(), status: 'RUNNING', stage: 'startup',
    pages: [], requests: [], downloads: [], events: [], login: null, failure: null };
  const started = performance.now();
  const elapsed = () => Math.round(performance.now() - started);
  let runtime, agent, scope;
  let fatal = null;
  const frames = new Map();
  const check = () => {
    if (fatal) fail(fatal);
    if (runtime.failure || runtime.trace.some(row => ['WORKER_BLOCKED', 'NEW_PAGE'].includes(row.action))) fail('QB_BROWSER_UNAVAILABLE');
    if (record.downloads.length) fail('QB_DOWNLOAD_UNSUPPORTED');
  };
  try {
    runtime = await runtimeFactory(); agent = new Agent(runtime);
    const rootFrame = () => [...runtime.guards.frames.parents].find(([, parent]) => parent === null)?.[0];
    scope = capturePolicy(runtime.policy, rootFrame, frames);
    // Observe before the existing interceptor, without copying request fields other than URL/method/frame.
    runtime.guards.root.prependListener('Fetch.requestPaused', event => {
      try {
        frames.set(event.requestId, event.frameId);
        if (runtime.policy.phase !== 'read' || event.resourceType !== 'Document') return;
        const url = event.request.url;
        const same = url === scope.current;
        const row = { elapsed_ms: elapsed(), url: same ? url : '<UNREGISTERED>',
          method: event.request.method, frame: event.frameId === rootFrame() ? 'main' : 'other',
          response_status: event.responseStatusCode ?? null,
          redirect: Boolean(event.redirectedRequestId), registered: same };
        if (same && event.responseStatusCode !== undefined) {
          // Only the two explicitly authorized response fields; never copy the container.
          for (const header of event.responseHeaders ?? []) {
            const name = header.name.toLowerCase();
            if (name === 'content-type') row.content_type = header.value;
            if (name === 'content-disposition') row.content_disposition = header.value;
          }
          if (/attachment/i.test(row.content_disposition ?? '')) fatal = 'QB_DOWNLOAD_UNSUPPORTED';
        }
        record.requests.push(row);
        if (same && event.frameId === rootFrame() && event.responseStatusCode >= 300
          && event.responseStatusCode < 400) fatal = 'CAPTURE_REDIRECT_UNSUPPORTED';
      } catch { fatal = 'CAPTURE_METADATA_FAILED'; }
    });
    runtime.page.on('download', download => {
      record.downloads.push({ elapsed_ms: elapsed(), url: download.url() === scope.current ? download.url() : '<UNREGISTERED>' });
      fatal = 'QB_DOWNLOAD_UNSUPPORTED';
    });
    runtime.page.on('close', () => record.events.push({ action: 'PAGE_CLOSED', elapsed_ms: elapsed() }));
    runtime.browser.on('disconnected', () => record.events.push({ action: 'BROWSER_DISCONNECTED', elapsed_ms: elapsed() }));
    record.stage = 'login';
    record.login = await agent.command({ command: 'login', projects: [PROJECT], login_timeout_seconds: 600 });
    if (!record.login.ok) fail(record.login.error);
    check();

    const read = async (url, text = false) => {
      record.stage = url;
      scope.current = url; runtime.policy.phase = 'read'; runtime.policy.invalidate();
      const navigation = { url, requestId: null, frameId: null, body: null, failed: false };
      runtime.policy.readNavigation = navigation;
      const page = { requested_url: url, started_ms: elapsed(), status: null, content_type: null,
        content_disposition: null, redirect_chain: [], download: false, frame: 'main' };
      record.pages.push(page);
      try {
        const response = await runtime.page.goto(url, { timeout: 30000, waitUntil: 'domcontentloaded' });
        if (!response) fail('CAPTURE_NO_RESPONSE');
        page.status = response.status();
        page.content_type = await response.headerValue('content-type');
        page.content_disposition = await response.headerValue('content-disposition');
        for (let request = response.request(); request; request = request.redirectedFrom()) {
          page.redirect_chain.unshift(request.url() === url ? request.url() : '<UNREGISTERED>');
        }
        page.download = record.downloads.length > 0;
        if (/attachment/i.test(page.content_disposition ?? '')) fail('QB_DOWNLOAD_UNSUPPORTED');
        check();
        if (response.url() !== url || runtime.page.url() !== url || page.redirect_chain.length !== 1) fail('CAPTURE_REDIRECT_UNSUPPORTED');
        if (page.status !== 200) fail('CAPTURE_HTTP_NOT_OK');
        if (navigation.failed || !navigation.requestId || !Buffer.isBuffer(navigation.body)) fail('QB_TRUSTED_CONTEXT_UNAVAILABLE');
        if (navigation.body.length > LIMIT) fail('QB_TEXT_TOO_LARGE');
        const name = String(record.pages.length).padStart(2, '0');
        if (text) {
          if (!/^text\/plain(?:\s*;|$)/i.test(page.content_type ?? '')) fail('CAPTURE_LOG_NOT_TEXT');
          page.body = await writer.write(`${name}.response.txt`, decodeText(navigation.body), 'text');
          return null;
        }
        const raw = await responseText(response, navigation.body);
        page.body = await writer.write(`${name}.response.html`, raw, 'html');
        const path = new URL(url).pathname;
        if (/^\/build\/\d+\/(overview|variables)$/.test(path)) await agent.buildId(path, raw);
        const value = await agent.trusted.run(facts, raw);
        verifyPage(path, value);
        page.identity_verified = true;
        return value;
      } finally {
        page.finished_ms = elapsed(); page.download = record.downloads.length > 0;
        const observed = record.requests.findLast(row => row.url === url && row.response_status !== null);
        if (observed) {
          page.status ??= observed.response_status;
          page.content_type ??= observed.content_type ?? null;
          page.content_disposition ??= observed.content_disposition ?? null;
        }
        navigation.body = null; runtime.policy.readNavigation = null; scope.current = null;
        runtime.policy.phase = 'idle';
      }
    };
    let report;
    for (const path of paths) report = await read(ORIGIN + path);
    if (report.iframes.length !== 1) fail('CAPTURE_IFRAME_COUNT');
    const iframe = exactLink(report.iframes[0], ORIGIN + PATHS.at(-1));
    const table = await read(iframe);
    const log = logLink(table, iframe);
    await read(log, true);
    check();
    record.status = 'CAPTURED';
  } catch (error) {
    record.status = 'STOPPED'; record.failure = fatal ?? fixedError(error);
    process.stderr.write(`CAPTURE_STOPPED code=${record.failure}\n`);
  } finally {
    if (runtime) {
      try { await runtime.close(); } catch { record.status = 'STOPPED'; record.failure ??= 'CAPTURE_CLOSE_FAILED'; }
      record.trace = runtime.trace;
      try { await access(runtime.profile); record.profile_removed = false; }
      catch (error) { record.profile_removed = error.code === 'ENOENT'; }
      if (!record.profile_removed) { record.status = 'STOPPED'; record.failure ??= 'CAPTURE_PROFILE_REMAINS'; }
    }
    record.finished_utc = new Date().toISOString();
    try { await writer.write('run.json', JSON.stringify(record, null, 2) + '\n'); }
    finally { await writer.close(); }
  }
  return record;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  if (process.argv.length !== 3 || process.argv[2] !== '--live') {
    process.stderr.write('CAPTURE_USAGE\n'); process.exitCode = 2;
  } else {
    try {
      const record = await capture(`${HERE}/live-01`);
      process.stdout.write(JSON.stringify({ status: record.status, failure: record.failure,
        pages: record.pages.length, profile_removed: record.profile_removed }) + '\n');
      process.exitCode = record.status === 'CAPTURED' ? 0 : 4;
    } catch (error) { process.stderr.write(`CAPTURE_STOPPED code=${fixedError(error)}\n`); process.exitCode = 4; }
  }
}
