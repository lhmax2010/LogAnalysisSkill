// Dedicated C2b evidence entry. No launch overrides and no build submission.
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { createInterface } from 'node:readline';
import {
  Agent, AgentError, callbackURL, canonical, checkRedacted, createRuntime,
  ORIGIN, pathShape, redactDOM, validateForm,
} from '../../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';

const [playwright, chromium, directory, python] = process.argv.slice(2);
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const report = { status: 'RUNNING', commands: [], pages: [], traffic: [], stop: null };
let runtime;
let agent;
let current = '/signin';
let operation = 'login';
let stopped = false;
let actionReleases = 0;
let sequence = 0;

function emit(row) { process.stdout.write(JSON.stringify(row) + '\n'); }
async function persist() {
  await writeFile(`${directory}/run.json`, JSON.stringify({ ...report,
    trace: runtime?.trace ?? [], runtime_failure: runtime?.failure ?? null,
    form_action_releases: actionReleases, released: runtime?.policy.released ?? false,
  }, null, 2) + '\n');
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

await mkdir(directory, { recursive: true });
if (existsSync(`${directory}/run.json`)) {
  emit({ error: 'EVIDENCE_ALREADY_EXISTS' });
  process.exit(1);
}
try {
  runtime = await createRuntime(playwright, chromium);
  agent = new Agent(runtime);
  const push = runtime.trace.push.bind(runtime.trace);
  runtime.trace.push = (...rows) => {
    const length = push(...rows);
    if (rows.some(row => ['WORKER_BLOCKED', 'NEW_PAGE'].includes(row.action))) stop('LIVE_TARGET_FAIL_CLOSED');
    return length;
  };
  // Observe only the production adapter's metadata, never raw protocol events.
  const allow = runtime.policy.allow.bind(runtime.policy);
  runtime.policy.allow = (metadata, requestId) => {
    const permitted = allow(metadata, requestId);
    const shape = pathShape(metadata.path);
    const staticPath = /^\/(?:styles|jquery|scripts|datetimepicker|codemirror|wicket\/resource|images)\/[A-Za-z0-9_./~-]+$/.test(metadata.path);
    report.traffic.push({ operation, phase: runtime.policy.phase, method: metadata.method,
      path: staticPath ? metadata.path : shape, resource_type: metadata.resource_type,
      response_status: metadata.response_status, allowed: permitted });
    if (permitted && metadata.method === 'POST' && metadata.response_status === null
      && /IFormSubmitListener-form$/.test(metadata.query)) actionReleases += 1;
    return permitted;
  };
  const watchdog = setInterval(() => { if (runtime.failure) stop(runtime.failure); }, 25);
  try {
    const result = await call({ command: 'login', login_timeout_seconds: 600, projects: [] });
    const url = new URL(runtime.page.url());
    report.login = { ok: result.ok, path: url.pathname, empty_query: url.search === '',
      not_signin: url.pathname !== '/signin',
      password_inputs: await runtime.page.locator('input[type=password]').count(),
      sign_out_links: await runtime.page.getByRole('link', { name: 'Sign Out', exact: true }).count() };
    check();
    emit({ login: report.login });
    await persist();
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
  } finally { clearInterval(watchdog); }
} catch (error) {
  stop(error instanceof AgentError ? error.code : 'EVIDENCE_RUNTIME_ERROR');
} finally {
  if (runtime) await runtime.close();
  report.browser_closed = !runtime || !runtime.browser.isConnected();
  report.profile_removed = !runtime || !existsSync(runtime.profile);
  await persist();
  emit({ status: report.status, stop: report.stop, browser_closed: report.browser_closed,
    profile_removed: report.profile_removed, released: runtime?.policy.released ?? false });
  if (report.status === 'STOPPED') process.exitCode = 1;
}
