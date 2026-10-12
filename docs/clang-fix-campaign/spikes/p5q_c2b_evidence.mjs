// Dedicated C2b evidence entry. No launch overrides and no build submission.
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { mkdir, readFile, unlink, writeFile } from 'node:fs/promises';
import { createInterface } from 'node:readline';
import {
  Agent, AgentError, callbackURL, canonical, checkRedacted, createRuntime,
  ORIGIN, pathShape, redactDOM, validateForm,
} from '../../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';

const [playwright, chromium, directory, python, mode = 'full'] = process.argv.slice(2);
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const report = { status: 'RUNNING', mode, commands: [], pages: [], traffic: [], diagnostics: [], events: [], stop: null };
const started = performance.now();
const elapsed = () => Math.round(performance.now() - started);
const identities = new Set();
const prompt = '已打开 QuickBuild 登录窗口,请在窗口中登录;登录后页面若显示被拦截属预期,请不要关闭窗口,工具会自动关闭。\n';
const previousPrompt = '已打开 QuickBuild 登录窗口,请在窗口中登录;登录后工具会自动继续。\n';
let runtime;
let agent;
let current = '/signin';
let operation = 'login';
let stopped = false;
let actionReleases = 0;
let sequence = 0;
let lastRequest = 0;
let postRedirect = false;
let deniedDocumentAfterRedirect = false;
const loginPostResponses = new Set();
let wrapperDenied = 0;

export function diagnosticStopReason({ redirect, deniedDocument, lastRequest, now, loginResponseCount }) {
  if (!redirect && loginResponseCount >= 5) return 'LOGIN_POST_LIMIT_NO_REDIRECT';
  if (redirect && deniedDocument && now - lastRequest >= 5000) return 'POST_3XX_DENIED_DOCUMENT_QUIET_5S';
  return null;
}

// Only URL components supplied by the production metadata adapter enter here.
export function redactAddress(path, query) {
  const maskedPath = path.split('/').map(segment => {
    if (segment.length > 64 || /[a-fA-F0-9]{16,}/.test(segment)
      || /[A-Za-z0-9+_-]{16,}={0,2}/.test(segment)) return '<TOKEN>';
    return segment.replace(/;([^;=]+)=([^;]*)/g, ';$1=<REDACTED>');
  }).join('/');
  let maskedQuery = query;
  if (query && !/^\d+(-\d+)?$/.test(query)
    && !/^\d+(-\d+)?\.?I[A-Za-z]+Listener[.0-9-]*-?[A-Za-z0-9:_-]*$/.test(query)) {
    maskedQuery = query.split('&').map(part => {
      const equals = part.indexOf('=');
      const key = equals < 0 ? part : part.slice(0, equals);
      const value = equals < 0 ? '' : part.slice(equals + 1);
      if (key === 'v' && /^\d{1,16}$/.test(value)) return part;
      return `${/^[A-Za-z0-9_.:-]{1,64}$/.test(key) ? key : '<KEY>'}=<REDACTED len=${[...value].length}>`;
    }).join('&');
  }
  return { path: maskedPath, query: maskedQuery };
}

function checkedReport(raw, interpreter = python, knownIdentities = [...identities]) {
  const result = spawnSync(interpreter, ['-c',
    'import json,re,sys; from ci_triage.qb_redact import PageRedactor; d=json.load(sys.stdin); r=PageRedactor(); r.identities.update(d["identities"]); raw=d["raw"].encode("utf-8"); r.check_bytes(raw); assert not re.search(rb"jsessionid=(?!<REDACTED(?:>| len=\\d+>))",raw,re.I)'],
  { input: JSON.stringify({ raw, identities: knownIdentities }), encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] });
  if (result.status !== 0) throw new AgentError('QB_EVIDENCE_REDACTION_FAILED');
}

async function selfTest(interpreter) {
  const cases = [
    ['session-path', '/;jsessionid=abc', '', '/;jsessionid=<REDACTED>', ''],
    ['session-query', '/x', 'jsessionid=abc', '/x', 'jsessionid=<REDACTED len=3>'],
    ['page-number', '/', '1', '/', '1'],
    ['listener', '/', '0-1.ILinkListener-x', '/', '0-1.ILinkListener-x'],
    ['query-values', '/', 'token=abc&v=2', '/', 'token=<REDACTED len=3>&v=2'],
    ['numeric-version', '/', 'v=1701391813000', '/', 'v=1701391813000'],
    ['nonnumeric-version', '/', 'v=abc123', '/', 'v=<REDACTED len=6>'],
    ['long-segment', '/' + 'x'.repeat(65), '', '/<TOKEN>', ''],
    ['hex-segment', '/0123456789abcdef', '', '/<TOKEN>', ''],
    ['base64-segment', '/QWxhZGRpbjpvcGVuIHNlc2FtZQ==', '', '/<TOKEN>', ''],
    ['bad-key', '/', 'bad%20key=abc', '/', '<KEY>=<REDACTED len=3>'],
    ['page-range', '/', '1-2', '/', '1-2'],
  ];
  for (const [name, path, query, expectedPath, expectedQuery] of cases) {
    const value = redactAddress(path, query);
    assert.deepEqual(value, { path: expectedPath, query: expectedQuery });
    checkedReport(JSON.stringify(value), interpreter, []);
    emit({ test: name, result: 'PASS' });
  }
  for (const [name, raw, users] of [
    ['cookie-assignment-rejected', '{"path":"JSESSIONID_8810=synthetic"}', []],
    ['session-assignment-rejected', '{"path":"/;jsessionid=synthetic"}', []],
    ['display-name-rejected', '{"path":"/synthetic-user"}', ['synthetic-user']],
  ]) {
    assert.throws(() => checkedReport(raw, interpreter, users), { code: 'QB_EVIDENCE_REDACTION_FAILED' });
    emit({ test: name, result: 'PASS' });
  }
  for (const [name, changes, expected] of [
    ['no-post-keeps-login-timeout', { now: 600000 }, null],
    ['four-login-responses-keep-waiting', { loginResponseCount: 4 }, null],
    ['five-login-responses-no-redirect-stop', { loginResponseCount: 5 }, 'LOGIN_POST_LIMIT_NO_REDIRECT'],
    ['redirect-not-yet-quiet', { redirect: true, deniedDocument: true, loginResponseCount: 5, now: 4999 }, null],
    ['redirect-quiet-done', { redirect: true, deniedDocument: true, loginResponseCount: 5, now: 5000 }, 'POST_3XX_DENIED_DOCUMENT_QUIET_5S'],
  ]) {
    assert.equal(diagnosticStopReason({ redirect: false, deniedDocument: false,
      lastRequest: 0, now: 0, loginResponseCount: 0, ...changes }), expected);
    emit({ test: name, result: 'PASS' });
  }
  emit({ self_tests: 20, passed: 20, network_requests: 0 });
}

function emit(row) { process.stdout.write(JSON.stringify(row) + '\n'); }
async function persist() {
  const traceDenied = runtime?.trace.filter(row => row.action === 'DENIED').length ?? 0;
  const raw = JSON.stringify({ ...report,
    trace: runtime?.trace ?? [], runtime_failure: runtime?.failure ?? null,
    form_action_releases: actionReleases, released: runtime?.policy.released ?? false,
    trace_denied_count: traceDenied, wrapper_denied_count: wrapperDenied,
    frame_ownership_denied_count: traceDenied - wrapperDenied,
    login_redirect_seen: postRedirect, login_response_count: loginPostResponses.size,
    denied_count_note: 'trace DENIED minus allow-wrapper denials are frame-ownership denials',
  }, null, 2) + '\n';
  const path = `${directory}/run.json`;
  try {
    checkedReport(raw);
    await writeFile(path, raw);
    checkedReport(await readFile(path, 'utf8'));
  } catch {
    await unlink(path).catch(() => {});
    throw new AgentError('QB_EVIDENCE_REDACTION_FAILED');
  }
}
function stop(reason) {
  if (stopped) return;
  stopped = true;
  report.status = 'STOPPED';
  report.stop = { reason, operation, path_shape: pathShape(current) };
  if (runtime) void runtime.close();
}
function check() {
  if (runtime.failure) stop(runtime.failure);
  if (stopped) throw new AgentError('QB_BROWSER_UNAVAILABLE');
}
async function archive(html, name) {
  checkRedacted(html);
  const before = spawnSync(python, ['-c',
    'import sys; from ci_triage.qb_redact import PageRedactor; PageRedactor().check_bytes(sys.stdin.buffer.read())'],
  { input: html, encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] });
  if (before.status !== 0) throw new AgentError('QB_EVIDENCE_REDACTION_FAILED');
  const path = `${directory}/${name}`;
  await writeFile(path, html, { flag: 'wx' });
  const after = spawnSync(python, ['-c',
    'import sys; from pathlib import Path; from ci_triage.qb_redact import PageRedactor; PageRedactor().check_written(Path(sys.argv[1]))', path],
  { stdio: ['ignore', 'pipe', 'pipe'] });
  if (after.status !== 0) throw new AgentError('QB_EVIDENCE_REDACTION_FAILED');
  return { file: name, sha256: createHash('sha256').update(await readFile(path)).digest('hex') };
}
async function call(input) {
  check();
  report.commands.push({ command: input.command, ...(input.path ? { path: input.path } : {}) });
  const result = await agent.command(input);
  check();
  if (!result.ok) throw new AgentError(result.error);
  return result;
}
async function formRecord(label) {
  check();
  const form = await agent.snapshot();
  const fields = validateForm(form, agent.currentProject.project_name);
  const control = fields.BUILD_TYPE.controls[0];
  const record = { label, base: form.base, action: form.action,
    callback: callbackURL(control.callback, form.base),
    options: Object.fromEntries(Object.entries(fields).map(([name, row]) =>
      [name, row.controls.filter(c => c.tag === 'SELECT').map(c => c.options)])) };
  const saved = await archive(await runtime.page.evaluate(redactDOM), `form-${label}.html`);
  report.pages.push({ path: '/wicket/page', ...saved });
  return record;
}

function diagnosticDone(reason) {
  if (stopped || report.status === 'DIAGNOSTIC_DONE') return;
  report.status = 'DIAGNOSTIC_DONE';
  report.diagnostic_end = { reason, relative_ms: elapsed() };
  void runtime.close();
}

async function rememberLoginNames() {
  // Read-only locator observation; no page script, input or navigation.
  try {
    const labels = await runtime.page.getByText(/^Welcome!\s*/).allTextContents();
    for (const text of labels) {
      const name = text.replace(/^\s*Welcome!\s*/, '').trim();
      if (name && name !== '<USER>') identities.add(name);
    }
  } catch { /* A closing page has no remaining DOM to observe. */ }
}

if (playwright === '--self-test') { await selfTest(chromium); process.exit(0); }

await mkdir(directory, { recursive: true });
if (existsSync(`${directory}/run.json`)) {
  emit({ error: 'EVIDENCE_ALREADY_EXISTS' });
  process.exit(1);
}
try {
  if (!['full', 'diagnostic'].includes(mode)) throw new AgentError('EVIDENCE_COMMAND_INVALID');
  process.stderr.write(prompt);
  runtime = await createRuntime(playwright, chromium);
  agent = new Agent(runtime);
  runtime.page.on('framenavigated', frame => {
    if (frame !== runtime.page.mainFrame()) return;
    try {
      const url = new URL(frame.url());
      report.events.push({ event: 'main_frame_navigation', relative_ms: elapsed(),
        protocol: url.protocol, host: url.host, ...redactAddress(url.pathname, url.search.slice(1)) });
    } catch { stop('QB_EVIDENCE_REDACTION_FAILED'); }
  });
  runtime.page.on('close', () => report.events.push({ event: 'page_close', relative_ms: elapsed() }));
  runtime.browser.on('disconnected', () => report.events.push({ event: 'browser_disconnected', relative_ms: elapsed() }));
  const push = runtime.trace.push.bind(runtime.trace);
  runtime.trace.push = (...rows) => {
    const length = push(...rows);
    if (rows.some(row => row.action === 'DENIED')) lastRequest = elapsed();
    if (rows.some(row => ['WORKER_BLOCKED', 'NEW_PAGE'].includes(row.action))) stop('LIVE_TARGET_FAIL_CLOSED');
    return length;
  };
  // Observe only the production adapter's metadata, never raw protocol events.
  const allow = runtime.policy.allow.bind(runtime.policy);
  runtime.policy.allow = (metadata, requestId) => {
    const permitted = allow(metadata, requestId);
    if (metadata.response_status === null) lastRequest = elapsed();
    if (!permitted) wrapperDenied += 1;
    if (!permitted || (runtime.policy.phase === 'login' && metadata.resource_type === 'Document')) {
      report.diagnostics.push({ sequence: report.diagnostics.length + 1, relative_ms: elapsed(),
        phase: runtime.policy.phase, method: metadata.method, protocol: metadata.protocol,
        host: metadata.host, ...redactAddress(metadata.path, metadata.query),
        resource_type: metadata.resource_type, response_status: metadata.response_status,
        redirect_hop: metadata.redirect_source !== null, allowed: permitted });
    }
    if (runtime.policy.loginPostRequests.has(requestId) && metadata.response_status !== null) {
      loginPostResponses.add(requestId);
      if (metadata.response_status >= 300 && metadata.response_status < 400) postRedirect = true;
    }
    if (postRedirect && !permitted && metadata.resource_type === 'Document'
      && metadata.response_status === null) deniedDocumentAfterRedirect = true;
    const shape = pathShape(metadata.path);
    const staticPath = /^\/(?:styles|jquery|scripts|datetimepicker|codemirror|wicket\/resource|images)\/[A-Za-z0-9_./~-]+$/.test(metadata.path);
    report.traffic.push({ operation, phase: runtime.policy.phase, method: metadata.method,
      path: staticPath ? metadata.path : shape, resource_type: metadata.resource_type,
      response_status: metadata.response_status, allowed: permitted });
    if (permitted && metadata.method === 'POST' && metadata.response_status === null
      && /IFormSubmitListener-form$/.test(metadata.query)) actionReleases += 1;
    return permitted;
  };
  const watchdog = setInterval(() => {
    if (runtime.failure) stop(runtime.failure);
    if (mode === 'diagnostic' && !stopped) {
      const reason = diagnosticStopReason({ redirect: postRedirect, deniedDocument: deniedDocumentAfterRedirect,
        lastRequest, now: elapsed(), loginResponseCount: loginPostResponses.size });
      if (reason === 'LOGIN_POST_LIMIT_NO_REDIRECT') stop(reason);
      else if (reason) diagnosticDone(reason);
    }
  }, 25);
  const nameWatch = setInterval(() => { void rememberLoginNames(); }, 500);
  try {
    report.commands.push({ command: 'login', login_timeout_seconds: 600 });
    const stderrWrite = process.stderr.write;
    process.stderr.write = function (chunk, ...args) {
      if (chunk === previousPrompt) return true;
      return stderrWrite.call(this, chunk, ...args);
    };
    let result;
    try { result = await agent.command({ command: 'login', login_timeout_seconds: 600, projects: [] }); }
    finally { process.stderr.write = stderrWrite; }
    report.login_response = result;
    check();
    if (report.status !== 'DIAGNOSTIC_DONE') {
    if (!result.ok) throw new AgentError(result.error);
    await rememberLoginNames();
    const url = new URL(runtime.page.url());
    report.login = { ok: result.ok, ...redactAddress(url.pathname, url.search.slice(1)), empty_query: url.search === '',
      not_signin: url.pathname !== '/signin',
      password_inputs: await runtime.page.locator('input[type=password]').count(),
      sign_out_links: await runtime.page.getByRole('link', { name: 'Sign Out', exact: true }).count() };
    check();
    if (mode === 'diagnostic') diagnosticDone('LOGIN_THREE_CONDITIONS');
    else emit({ login: report.login });
    }
    await persist();
    if (mode === 'full') {
    const lines = createInterface({ input: process.stdin, crlfDelay: Infinity });
    for await (const line of lines) {
      const input = JSON.parse(line);
      check();
      if (input.command === 'close') { report.status = 'COLLECTED'; break; }
      if (input.command === 'stop') { stop('OBSERVATION_MISMATCH'); break; }
      operation = input.command;
      if (input.command === 'read') {
        if (!/^\/(?:build\/\d+(?:\/(?:variables|step_status))?|overview\/\d+)$/.test(input.path)) throw new AgentError('EVIDENCE_COMMAND_INVALID');
        current = input.path;
        const response = await call(input);
        const saved = await archive(response.html_redacted, `${String(++sequence).padStart(2, '0')}.response.html`);
        const record = { path: input.path, status: response.status, ...saved };
        report.pages.push(record);
        emit(record);
      } else if (input.command === 'register_config') {
        // Explicit evidence-only registration; the operator derives it from the
        // archived parent's breadcrumb and verifies the configuration title.
        if (!Number.isSafeInteger(input.overview_id) || input.overview_id <= 0
          || input.configuration_path !== 'root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER') throw new AgentError('EVIDENCE_COMMAND_INVALID');
        const project = { overview_id: input.overview_id, configuration_path: input.configuration_path, project_name: 'Tizen-Base-Toolchain' };
        agent.projects.set(input.overview_id, project);
        agent.policy.overviewIds.add(String(input.overview_id));
        report.configuration = project;
        emit({ registered: input.overview_id });
      } else if (input.command === 'form_evidence') {
        if (!report.configuration) throw new AgentError('EVIDENCE_COMMAND_INVALID');
        current = `/overview/${report.configuration.overview_id}`;
        await call({ command: 'open_form', overview_id: report.configuration.overview_id });
        current = '/wicket/page';
        report.form = [await formRecord('initial')];
        const initial = report.form[0].options.BUILD_TYPE[0].filter(option => option.selected);
        if (initial.length !== 1 || initial[0].text !== 'Full') throw new AgentError('QB_FORM_VALUE_UNAVAILABLE');
        for (const value of ['Partial', 'Full']) {
          const form = await agent.snapshot();
          const field = validateForm(form, agent.currentProject.project_name).BUILD_TYPE.controls[0];
          runtime.policy.phase = 'fill';
          runtime.policy.beginField(callbackURL(field.callback, form.base));
          if (!field.options.some(option => option.text === value)) throw new AgentError('QB_FORM_VALUE_UNAVAILABLE');
          await agent.fieldRow('BUILD_TYPE').locator('td.value select').selectOption({ label: value });
          const deadline = Date.now() + 30000;
          while (!runtime.policy.fieldFinished || Date.now() - runtime.policy.lastActivity < 1000) {
            check();
            if (Date.now() >= deadline) throw new AgentError('QB_FORM_CHANGED');
            await sleep(50);
          }
          runtime.policy.endField(); runtime.policy.phase = 'idle';
          report.form.push(await formRecord(value.toLowerCase()));
          await persist();
        }
        if (runtime.policy.released || actionReleases !== 0) throw new AgentError('EVIDENCE_RELEASE_VIOLATION');
        emit({ form: report.form, action_releases: actionReleases, state: 'not_released', canonical: canonical(report.form).length });
      } else throw new AgentError('EVIDENCE_COMMAND_INVALID');
      check();
      await persist();
    }
    }
  } finally { clearInterval(watchdog); clearInterval(nameWatch); }
} catch (error) {
  stop(error instanceof AgentError ? error.code : 'EVIDENCE_RUNTIME_ERROR');
} finally {
  if (runtime) await runtime.close();
  report.browser_closed = !runtime || !runtime.browser.isConnected();
  report.profile_removed = !runtime || !existsSync(runtime.profile);
  try { await persist(); }
  catch { report.status = 'STOPPED'; report.stop = { reason: 'QB_EVIDENCE_REDACTION_FAILED' }; }
  emit({ status: report.status, stop: report.stop, browser_closed: report.browser_closed,
    profile_removed: report.profile_removed, released: runtime?.policy.released ?? false });
  if (report.status === 'STOPPED') process.exitCode = 1;
}
