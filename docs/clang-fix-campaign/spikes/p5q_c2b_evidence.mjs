// Dedicated C2b evidence entry. No launch overrides and no build submission.
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';
import { spawn, spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { mkdir, mkdtemp, readFile, rm, unlink, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createInterface } from 'node:readline';
import { PassThrough } from 'node:stream';
import { fileURLToPath } from 'node:url';
import {
  Agent, AgentError, callbackURL, canonical, checkRedacted, createRuntime,
  ORIGIN, FIELDS, pathShape, redactDOM, validateForm,
} from '../../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';
import {
  configurationDOM, configurationPageChecks, parentConfigurationChecks, parentRegistration,
} from './p5q_c2b_config_source.mjs';
import { withFormFailureEvidence } from './p5q_c2b_form_diagnostics.mjs';

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
let operation = 'handshake';
let stopped = false;
let actionReleases = 0;
let sequence = 0;
let lastRequest = 0;
let postRedirect = false;
let deniedDocumentAfterRedirect = false;
const loginPostResponses = new Set();
let wrapperDenied = 0;
const parentPages = new Map();
const parentOverview = '/build/1193467/overview';
const buildReadPaths = new Set([parentOverview, '/build/1193467/variables',
  '/build/1193469/overview', '/build/1193469/variables', '/build/1193469/step_status']);
let readNavigation = null;
let channel;

function commandChannel(input, onEnd) {
  const lines = createInterface({ input, crlfDelay: Infinity, terminal: false });
  const iterator = lines[Symbol.asyncIterator]();
  let ended = false;
  let receivedClose = false;
  let disposed = false;
  // EOF can arrive while login is running or before a queued close is consumed.
  lines.on('line', line => {
    try { if (JSON.parse(line)?.command === 'close') receivedClose = true; }
    catch { /* The command loop rejects malformed input without logging it. */ }
  });
  const inputEnded = () => {
    if (ended) return;
    ended = true;
    if (!disposed && !receivedClose) onEnd('EVIDENCE_STDIN_CLOSED');
  };
  input.once('end', inputEnded);
  input.once('close', inputEnded);
  return {
    iterator,
    async handshake(reply) {
      const first = await iterator.next();
      if (first.done || ended) throw new AgentError('EVIDENCE_STDIN_CLOSED');
      let input;
      try { input = JSON.parse(first.value); }
      catch { throw new AgentError('EVIDENCE_COMMAND_INVALID'); }
      if (canonical(input) !== '{"command":"ping"}') throw new AgentError('EVIDENCE_COMMAND_INVALID');
      await reply({ pong: true });
      if (ended) throw new AgentError('EVIDENCE_STDIN_CLOSED');
    },
    dispose() {
      disposed = true;
      input.off('end', inputEnded); input.off('close', inputEnded);
      lines.close(); input.pause();
    },
  };
}

export function idStructureDOM() {
  const navigation = [...document.querySelectorAll('.nav-link')]
    .map(node => node.textContent.trim()).filter(text => text.startsWith('Build ('));
  const boxes = [...document.querySelectorAll('.build-summary')];
  return {
    ready_state: document.readyState,
    navigation_count: navigation.length,
    navigation_labels: navigation.slice(0, 10),
    build_summary_count: boxes.length,
    build_summaries: boxes.map(box => {
      const heads = [...box.querySelectorAll('.box-head')].map(node => node.textContent.trim());
      const result = { box_heads: heads };
      if (heads.includes('Summary')) {
        const tables = [...box.querySelectorAll('table')];
        result.table_count = tables.length;
        result.tables = tables.map(table => {
          const columns = [...table.querySelectorAll('thead th')].map(node => node.textContent.trim());
          const indices = columns.flatMap((text, index) => text === 'Id' ? [index] : []);
          const rows = [...table.querySelectorAll('tbody tr')];
          return { thead_th: columns, tbody_rows: rows.length,
            id_column_index: indices.length === 1 ? indices[0] : null,
            first_row_id: indices.length === 1 ? rows[0]?.cells[indices[0]]?.textContent.trim() ?? null : null };
        });
      }
      return result;
    }),
  };
}

function requireReadLocation(page, path, navigation) {
  if (!navigation || navigation.status !== 200) throw new AgentError('QB_READ_HTTP_STATUS');
  if (navigation.redirected || navigation.url !== ORIGIN + path || page.url() !== ORIGIN + path) {
    throw new AgentError('QB_READ_REDIRECTED');
  }
}

async function readWithDiagnostics(input, send, page, navigation, guard, saveSample) {
  const response = await send(input);
  guard();
  requireReadLocation(page, input.path, navigation());
  if (response.ok) {
    if (response.status !== 200) throw new AgentError('QB_READ_HTTP_STATUS');
    return { ...response, ...(/^\/build\/\d+\/(?:overview|variables|step_status)$/.test(input.path)
      ? { id_verified: true, verification: 'VERIFIED' } : {}) };
  }
  if (response.error !== 'QB_READ_ID_MISMATCH' || !/^\/build\/\d+\/(?:overview|variables)$/.test(input.path)) {
    throw new AgentError(response.error);
  }
  const samples = [];
  for (const index of [0, 1]) {
    if (index) {
      const deadline = Date.now() + 3000;
      while (Date.now() < deadline) {
        guard();
        requireReadLocation(page, input.path, navigation());
        await sleep(Math.min(50, Math.max(0, deadline - Date.now())));
      }
    }
    guard();
    requireReadLocation(page, input.path, navigation());
    const url = new URL(page.url());
    const sample = { sample: index + 1, relative_ms: elapsed(),
      main_frame: { protocol: url.protocol, host: url.host, ...redactAddress(url.pathname, url.search.slice(1)) },
      ...await page.evaluate(idStructureDOM) };
    guard();
    saveSample(sample);
    samples.push(sample);
  }
  let html;
  try { html = checkRedacted(await page.evaluate(redactDOM)); }
  catch { throw new AgentError('QB_EVIDENCE_REDACTION_FAILED'); }
  guard();
  requireReadLocation(page, input.path, navigation());
  return { status: 200, html_redacted: html, id_verified: false, verification: 'ID_UNVERIFIED', id_samples: samples };
}

function requireVerifiedSource(source) {
  if (!source || source.id_verified !== true) throw new AgentError('ID_UNVERIFIED_SOURCE');
  return source;
}

function requireVerifiedOverview(source) {
  requireVerifiedSource(source);
  if (!/^\/build\/\d+\/overview$/.test(source.path)) throw new AgentError('CONFIGURATION_SOURCE_MISMATCH');
  return source;
}

function requireReadSource(path, sources) {
  if (!buildReadPaths.has(path)) throw new AgentError('EVIDENCE_COMMAND_INVALID');
  if (path.startsWith('/build/1193469/')) {
    const parent = requireVerifiedOverview(sources.get(parentOverview));
    if (!parent.child_build_ids.includes('1193469')) throw new AgentError('EVIDENCE_COMMAND_INVALID');
  }
}

async function childIdsFromVerifiedSource(source, page) {
  requireVerifiedOverview(source);
  return page.evaluate(html => {
    const doc = new DOMParser().parseFromString(html, 'text/html');
    const ids = [];
    for (const heading of doc.querySelectorAll('h3')) {
      if (heading.textContent.replace(/^\s*◆\s*/, '').trim() !== 'Child Build') continue;
      const table = heading.nextElementSibling;
      if (table?.tagName !== 'TABLE') continue;
      for (const link of table.querySelectorAll('a[href]')) {
        const match = /^https:\/\/quickbuild\.tizen\.org\/build\/(\d+)$/.exec(link.getAttribute('href'));
        if (match && !ids.includes(match[1])) ids.push(match[1]);
      }
    }
    return ids;
  }, source.html_redacted);
}

async function collectRead(input) {
  const requestedId = /^\/build\/(\d+)/.exec(input.path)?.[1];
  if (requestedId) requireReadSource(input.path, parentPages);
  readNavigation = null;
  const diagnostic = { path: input.path, samples: [] };
  const response = await readWithDiagnostics(input, command => call(command, true), runtime.page,
    () => readNavigation, check, sample => {
      checkedReport(JSON.stringify(sample));
      if (!diagnostic.samples.length) (report.id_diagnostics ??= []).push(diagnostic);
      diagnostic.samples.push(sample);
    });
  const suffix = response.id_verified === false ? '.id-unverified.response.html' : '.response.html';
  const saved = await archive(response.html_redacted, `${String(++sequence).padStart(2, '0')}${suffix}`);
  const record = { path: input.path, status: response.status, ...saved,
    ...(response.id_verified !== undefined ? { id_verified: response.id_verified, verification: response.verification } : {}) };
  report.pages.push(record);
  if (response.id_verified === false) {
    parentPages.delete(input.path);
    diagnostic.file = saved.file;
    emit(record);
    if (/^\/build\/1193467\/(?:overview|variables)$/.test(input.path)) throw new AgentError('QB_READ_ID_MISMATCH');
    return;
  }
  if (/^\/build\/\d+\/overview$/.test(input.path)) {
    const facts = await runtime.page.evaluate(configurationDOM, response.html_redacted);
    const childIds = await childIdsFromVerifiedSource({ ...record, html_redacted: response.html_redacted }, runtime.page);
    const source = { ...record, facts, child_build_ids: childIds };
    parentPages.set(input.path, source);
    (report.configuration_sources ??= []).push({ ...source, ...parentConfigurationChecks(facts, source.path) });
    record.child_build_ids = childIds;
  }
  if (/^\/overview\/\d+$/.test(input.path)) {
    const facts = await runtime.page.evaluate(configurationDOM, response.html_redacted);
    report.configuration_page = { ...record, facts, ...configurationPageChecks(facts) };
    if (!report.configuration || input.path !== `/overview/${report.configuration.overview_id}`
      || !report.configuration_page.passed) throw new AgentError('CONFIGURATION_SOURCE_MISMATCH');
  }
  emit(record);
}

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
  const scratch = await mkdtemp(join(tmpdir(), 'p5q-evidence-channel-'));
  try {
    const result = spawnSync(process.execPath, [fileURLToPath(import.meta.url),
      'unused-playwright', 'unused-chromium', scratch, interpreter, 'full'],
    { input: '', encoding: 'utf8', timeout: 30000 });
    assert.equal(result.status, 1);
    assert.equal(result.stderr, '');
    const output = JSON.parse(result.stdout.trim());
    const saved = JSON.parse(await readFile(join(scratch, 'run.json'), 'utf8'));
    for (const row of [output, saved]) {
      assert.equal(row.status, 'STOPPED');
      assert.equal(row.stop.reason, 'EVIDENCE_STDIN_CLOSED');
      assert.equal(row.browser_closed, true);
      assert.equal(row.profile_removed, true);
    }
    assert.deepEqual(saved.commands, []);
    assert.deepEqual(saved.traffic, []);
    emit({ test: 'stdin-eof-before-close-stops', result: 'PASS' });
    const waiting = spawn(process.execPath, [fileURLToPath(import.meta.url),
      'unused-playwright', 'unused-chromium', join(scratch, 'waiting'), interpreter, 'full'],
    { stdio: ['pipe', 'pipe', 'pipe'], timeout: 30000 });
    let waitingOutput = '';
    let errors = '';
    waiting.stdout.on('data', chunk => { waitingOutput += chunk; });
    waiting.stderr.on('data', chunk => { errors += chunk; });
    const finished = new Promise((resolve, reject) => {
      waiting.once('close', resolve); waiting.once('error', reject);
    });
    try {
      await sleep(100);
      assert.equal(waitingOutput, '');
      assert.equal(errors, '');
      // A non-ping first command must be rejected before attempting browser setup.
      waiting.stdin.write('{"command":"read"}\n');
      assert.equal(await finished, 1);
      assert.equal(errors, '');
      const rejected = JSON.parse(waitingOutput.trim());
      assert.equal(rejected.status, 'STOPPED');
      assert.equal(rejected.stop.reason, 'EVIDENCE_COMMAND_INVALID');
      const record = JSON.parse(await readFile(join(scratch, 'waiting', 'run.json'), 'utf8'));
      assert.deepEqual(record.commands, []);
      assert.deepEqual(record.traffic, []);
    } finally {
      if (waiting.exitCode === null) { waiting.kill(); await finished; }
    }
  } finally { await rm(scratch, { recursive: true, force: true }); }
  const stream = new PassThrough();
  const ends = [];
  const replies = [];
  const testChannel = commandChannel(stream, reason => ends.push(reason));
  let browserStarts = 0;
  try {
    const startup = testChannel.handshake(row => replies.push(row)).then(() => {
      assert.deepEqual(replies, [{ pong: true }]);
      browserStarts += 1;
    });
    await sleep(50);
    assert.equal(browserStarts, 0);
    assert.deepEqual(replies, []);
    stream.write('{"command":"ping"}\n');
    await startup;
    assert.deepEqual(replies, [{ pong: true }]);
    assert.equal(browserStarts, 1);
    stream.end();
    await testChannel.iterator.next();
    assert.deepEqual(ends, ['EVIDENCE_STDIN_CLOSED']);
    const normal = new PassThrough();
    const cleanEnds = [];
    const clean = commandChannel(normal, reason => cleanEnds.push(reason));
    try {
      normal.end('{"command":"close"}\n');
      assert.equal((await clean.iterator.next()).value, '{"command":"close"}');
      assert.equal((await clean.iterator.next()).done, true);
      assert.deepEqual(cleanEnds, []);
    } finally { clean.dispose(); }
    const failing = new PassThrough();
    const failureEnds = [];
    const failureChannel = commandChannel(failing, reason => failureEnds.push(reason));
    try {
      failing.write('{"command":"read"}\n');
      await assert.rejects(async () => {
        for await (const line of failureChannel.iterator) {
          assert.equal(JSON.parse(line).command, 'read');
          throw new AgentError('QB_READ_REDIRECTED');
        }
      }, { code: 'QB_READ_REDIRECTED' });
      assert.deepEqual(failureEnds, []);
    } finally { failureChannel.dispose(); }
    emit({ test: 'no-ping-no-browser', result: 'PASS' });
  } finally { testChannel.dispose(); }
  emit({ self_tests: 22, passed: 22, network_requests: 0 });
}

async function idSelfTest(pw, chrome, interpreter) {
  const browserRuntime = await createRuntime(pw, chrome);
  browserRuntime.policy.allow = () => false;
  let networkRequests = 0;
  browserRuntime.page.on('request', () => { networkRequests += 1; });
  let path;
  let navigations = 0;
  let lateSummary = false;
  const summary = '<div class="build-summary"><div class="box-head">Summary</div><table>'
    + '<thead><tr><th>Status</th><th>Id</th><th>Triggered By</th></tr></thead>'
    + '<tbody><tr><td>NON_ID_CELL</td><td>1193469</td><td>Fixture User</td></tr></tbody></table></div>';
  const header = '<span>Welcome! Fixture User</span><a class="nav-link">Build (id:1193469)</a>';
  const page = {
    goto: async () => {
      navigations += 1;
      if (lateSummary) await browserRuntime.page.evaluate(html => {
        setTimeout(() => document.body.insertAdjacentHTML('beforeend', html), 1000);
      }, summary);
      return { status: () => 200, request: () => ({ redirectedFrom: () => null }) };
    },
    url: () => ORIGIN + path,
    evaluate: (...args) => browserRuntime.page.evaluate(...args),
  };
  const testAgent = new Agent({ ...browserRuntime, page });
  testAgent.state = 'ready';
  const navigation = () => ({ status: 200, url: ORIGIN + path, redirected: false });
  let tests = 0;
  const pass = name => { tests += 1; emit({ test: name, result: 'PASS' }); };
  try {
    for (const name of ['two-build-labels', 'no-summary', 'late-summary']) {
      path = name === 'two-build-labels' ? '/build/1193469/variables' : '/build/1193469/overview';
      lateSummary = name === 'late-summary';
      await browserRuntime.page.setContent(header + (name === 'two-build-labels'
        ? '<a class="nav-link">Build (Id:999)</a>' + summary : ''));
      const beforeRequests = networkRequests;
      const beforeNavigations = navigations;
      const samples = [];
      const result = await readWithDiagnostics({ command: 'read', path },
        input => testAgent.command(input), page, navigation, () => {
          assert.equal(browserRuntime.failure, null);
        }, sample => samples.push(sample));
      assert.equal(result.id_verified, false);
      assert.equal(result.verification, 'ID_UNVERIFIED');
      assert.equal(samples.length, 2);
      assert.ok(samples[1].relative_ms - samples[0].relative_ms >= 3000);
      assert.equal(samples[0].ready_state, 'complete');
      assert.equal(samples[0].main_frame.path, path);
      assert.equal(samples[0].navigation_count, name === 'two-build-labels' ? 2 : 1);
      assert.equal(samples[0].build_summary_count, name === 'two-build-labels' ? 1 : 0);
      assert.equal(samples[1].build_summary_count, name === 'no-summary' ? 0 : 1);
      if (samples[1].build_summary_count) {
        assert.deepEqual(samples[1].build_summaries, [{ box_heads: ['Summary'], table_count: 1, tables: [{
          thead_th: ['Status', 'Id', 'Triggered By'], tbody_rows: 1, id_column_index: 1, first_row_id: '1193469',
        }] }]);
      }
      assert.ok(!JSON.stringify(samples).includes('NON_ID_CELL'));
      assert.ok(!JSON.stringify(samples).includes('Fixture User'));
      assert.ok(!result.html_redacted.includes('Fixture User'));
      checkedReport(JSON.stringify(samples), interpreter, ['Fixture User']);
      checkedReport(JSON.stringify({ html: result.html_redacted }), interpreter, ['Fixture User']);
      assert.equal(navigations - beforeNavigations, 1); // Only the original production read, no retry.
      assert.equal(networkRequests, beforeRequests);
      assert.throws(() => parentRegistration(requireVerifiedSource(result)), { code: 'ID_UNVERIFIED_SOURCE' });
      await assert.rejects(childIdsFromVerifiedSource(result, page), { code: 'ID_UNVERIFIED_SOURCE' });
      emit({ fixture: name, id_verified: false, samples, diagnostic_requests: networkRequests - beforeRequests });
      lateSummary = false;
      await browserRuntime.page.setContent(header + summary);
      path = '/build/1193469/overview';
      const next = await readWithDiagnostics({ command: 'read', path }, input => testAgent.command(input),
        page, navigation, () => {}, () => assert.fail('verified next read must not diagnose'));
      assert.equal(next.id_verified, true);
      pass(name);
    }
    for (const [name, observation, response, code] of [
      ['non-200', { ...navigation(), status: 403 }, { ok: false, error: 'QB_READ_ID_MISMATCH' }, 'QB_READ_HTTP_STATUS'],
      ['redirect', { ...navigation(), redirected: true }, { ok: false, error: 'QB_READ_REDIRECTED' }, 'QB_READ_REDIRECTED'],
      ['browser-failure', navigation(), { ok: false, error: 'QB_BROWSER_UNAVAILABLE' }, 'QB_BROWSER_UNAVAILABLE'],
      ['redaction-failure', navigation(), { ok: false, error: 'QB_EVIDENCE_REDACTION_FAILED' }, 'QB_EVIDENCE_REDACTION_FAILED'],
    ]) {
      await assert.rejects(readWithDiagnostics({ command: 'read', path }, async () => response,
        page, () => observation, () => {}, () => assert.fail('must stop without diagnosis')), { code });
      pass(name);
    }
    let guards = 0;
    await assert.rejects(readWithDiagnostics({ command: 'read', path },
      async () => ({ ok: false, error: 'QB_READ_ID_MISMATCH' }), page, navigation, () => {
        if (++guards === 4) throw new AgentError('QB_BROWSER_UNAVAILABLE');
      }, () => {}), { code: 'QB_BROWSER_UNAVAILABLE' });
    pass('fail-closed-during-diagnostic-wait');
    await browserRuntime.page.setContent('<a class="nav-link">Build (id:1193469)</a>'.repeat(11)
      + summary.replace('<th>Status</th>', '<th>Id</th>'));
    const capped = await browserRuntime.page.evaluate(idStructureDOM);
    assert.equal(capped.navigation_count, 11);
    assert.equal(capped.navigation_labels.length, 10);
    assert.equal(capped.build_summaries[0].tables[0].id_column_index, null);
    assert.equal(capped.build_summaries[0].tables[0].first_row_id, null);
    pass('ten-label-cap-and-nonunique-id-no-cell-text');
    const childPage = '<h3>Child Build</h3><table><tr><td>'
      + '<a href="https://quickbuild.tizen.org/build/1193469">child</a></td></tr></table>';
    const parent = { id_verified: true, path: parentOverview, html_redacted: childPage };
    assert.deepEqual(await childIdsFromVerifiedSource(parent, page), ['1193469']);
    pass('verified-child-id-source');
    for (const invalidPath of ['/build/1193467', '/build/1193467/variables', '/build/1193467/step_status']) {
      await assert.rejects(childIdsFromVerifiedSource({ ...parent, path: invalidPath }, page),
        { code: 'CONFIGURATION_SOURCE_MISMATCH' });
    }
    pass('child-id-requires-overview-not-remembered-tab');
    const sources = new Map([[parentOverview, { ...parent, child_build_ids: ['1193469'] }]]);
    for (const allowed of buildReadPaths) assert.doesNotThrow(() => requireReadSource(allowed, sources));
    for (const denied of ['/build/1186372/overview', '/build/1186372/variables', '/build/1193469', '/build/1193469/log']) {
      assert.throws(() => requireReadSource(denied, sources), { code: 'EVIDENCE_COMMAND_INVALID' });
    }
    assert.throws(() => requireReadSource('/build/1193469/overview', new Map()), { code: 'ID_UNVERIFIED_SOURCE' });
    sources.set(parentOverview, { ...parent, child_build_ids: [] });
    assert.throws(() => requireReadSource('/build/1193469/overview', sources), { code: 'EVIDENCE_COMMAND_INVALID' });
    pass('live07-paths-and-child-relation-closed');
    await browserRuntime.page.setContent(header);
    path = '/build/1193469/step_status';
    const step = await readWithDiagnostics({ command: 'read', path }, input => testAgent.command(input),
      page, navigation, () => {}, () => assert.fail('verified step status must not diagnose'));
    assert.equal(step.id_verified, true);
    pass('step-status-navigation-verified');
    const form = { heading: true, base: `${ORIGIN}/wicket/page?50`,
      action: `${ORIGIN}/wicket/page?50-1.IFormSubmitListener-form`,
      rows: [{ label: 'PROJECT_NAME', viewers: ['Tizen'], controls: [] }, ...FIELDS.map(label => ({ label, viewers: [],
        controls: (['CHILD_CONFIGURATIONS', 'TARGET_IMAGE'].includes(label) ? ['recorder', 'choices', 'selection'] : ['input'])
          .map(role => ({ role, tag: 'SELECT', type: 'select-one',
            callback: `wicketAjaxPost('${ORIGIN}/wicket/page?50-1.IBehaviorListener.0-form-field', 0)`,
            options: [{ text: label === 'BUILD_REFERENCE' ? 'Ref. Snapshot' : 'snapshot-1', value: 'first', selected: true },
              { text: 'other', value: 'second', selected: false }] })),
      }))] };
    const facts = formFacts(form, 'Tizen', 'initial');
    assert.equal(facts.page_version, '50');
    assert.equal(facts.reference_fields.BUILD_REFERENCE[0].value, 'Ref. Snapshot');
    assert.equal(facts.reference_fields.SNAPSHOT_NUM[0].value, 'snapshot-1');
    assert.equal(facts.reference_fields.SNAPSHOT_NUM[0].options.length, 2);
    assert.equal(facts.callback_has_random, false);
    checkedReport(JSON.stringify(facts), interpreter, []);
    pass('form-reference-current-values-options-and-version');
    assert.equal(networkRequests, 0);
    assert.equal(browserRuntime.page.url(), 'about:blank');
    emit({ self_tests: tests, passed: tests, network_requests: networkRequests, fixture_navigation: 'stubbed original read only' });
  } finally { await browserRuntime.close(); }
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
async function call(input, allowIdMismatch = false) {
  check();
  report.commands.push({ command: input.command, ...(input.path ? { path: input.path } : {}) });
  const result = await agent.command(input);
  check();
  if (!result.ok && !(allowIdMismatch && input.command === 'read' && result.error === 'QB_READ_ID_MISMATCH')) {
    throw new AgentError(result.error);
  }
  return result;
}
async function formRecord(label) {
  check();
  const form = await agent.snapshot();
  const record = formFacts(form, agent.currentProject.project_name, label);
  const saved = await archive(await runtime.page.evaluate(redactDOM), `form-${label}.html`);
  report.pages.push({ path: '/wicket/page', ...saved });
  return record;
}

function formFacts(form, projectName, label) {
  const fields = validateForm(form, projectName);
  const callback = callbackURL(fields.BUILD_TYPE.controls[0].callback, form.base);
  return { label, base: form.base, action: form.action, callback,
    page_version: new URL(form.base).search.slice(1),
    callback_has_random: new URL(callback).searchParams.has('random'),
    reference_fields: Object.fromEntries(['BUILD_REFERENCE', 'SNAPSHOT_NUM'].map(name => [name,
      fields[name].controls.map(control => ({ tag: control.tag, type: control.type,
        value: control.tag === 'SELECT' ? control.options.filter(option => option.selected).map(option => option.text).join('\n') : control.value,
        options: control.options ?? [] }))])),
    options: Object.fromEntries(Object.entries(fields).map(([name, row]) =>
      [name, row.controls.filter(c => c.tag === 'SELECT').map(c => c.options)])) };
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
if (playwright === '--id-self-test') { await idSelfTest(chromium, directory, python); process.exit(0); }
if (playwright === '--form-self-test') {
  const { formSelfTest } = await import('./p5q_c2b_form_diagnostics_test.mjs');
  await formSelfTest(chromium, directory, python, redactAddress);
  process.exit(0);
}

await mkdir(directory, { recursive: true });
if (existsSync(`${directory}/run.json`)) {
  emit({ error: 'EVIDENCE_ALREADY_EXISTS' });
  process.exit(1);
}
try {
  if (!['full', 'diagnostic'].includes(mode)) throw new AgentError('EVIDENCE_COMMAND_INVALID');
  channel = commandChannel(process.stdin, stop);
  await channel.handshake(row => new Promise((resolve, reject) => {
    process.stdout.write(JSON.stringify(row) + '\n', error => {
      if (error) reject(new AgentError('EVIDENCE_STDIN_CLOSED'));
      else resolve();
    });
  }));
  if (stopped) throw new AgentError('EVIDENCE_STDIN_CLOSED');
  report.channel = { ping_received: true, pong_sent: true };
  operation = 'login';
  process.stderr.write(prompt);
  runtime = await createRuntime(playwright, chromium);
  check();
  agent = new Agent(runtime);
  runtime.page.on('response', response => {
    if (operation !== 'read') return;
    try {
      const request = response.request();
      if (!request.isNavigationRequest() || request.frame() !== runtime.page.mainFrame()) return;
      readNavigation = { status: response.status(), url: response.url(), redirected: request.redirectedFrom() !== null };
      if (readNavigation.redirected || readNavigation.status >= 300 && readNavigation.status < 400) stop('QB_READ_REDIRECTED');
      else if (readNavigation.status !== 200) stop('QB_READ_HTTP_STATUS');
    } catch { stop('QB_BROWSER_UNAVAILABLE'); }
  });
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
    if (operation === 'form_evidence' && ['Document', 'XHR', 'Fetch'].includes(metadata.resource_type)) {
      (report.form_network ??= []).push({ relative_ms: elapsed(), phase: runtime.policy.phase,
        method: metadata.method, protocol: metadata.protocol, host: metadata.host,
        ...redactAddress(metadata.path, metadata.query), has_random: new URLSearchParams(metadata.query).has('random'),
        resource_type: metadata.resource_type, response_status: metadata.response_status, allowed: permitted });
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
    for await (const line of channel.iterator) {
      const input = JSON.parse(line);
      check();
      if (input.command === 'close') { report.status = 'COLLECTED'; break; }
      if (input.command === 'stop') { stop('OBSERVATION_MISMATCH'); break; }
      operation = input.command;
      if (input.command === 'read') {
        if (!/^\/(?:build\/\d+\/(?:overview|variables|step_status)|overview\/\d+)$/.test(input.path)) throw new AgentError('EVIDENCE_COMMAND_INVALID');
        current = input.path;
        await collectRead(input);
      } else if (input.command === 'register_config') {
        // Only a freshly archived parent response can authorize registration.
        let project;
        try {
          if (input.source_path !== parentOverview) throw new AgentError('CONFIGURATION_SOURCE_MISMATCH');
          project = parentRegistration(requireVerifiedOverview(parentPages.get(input.source_path)));
        }
        catch { throw new AgentError('CONFIGURATION_SOURCE_MISMATCH'); }
        agent.projects.set(project.overview_id, project);
        agent.policy.overviewIds.add(String(project.overview_id));
        report.configuration = project;
        emit({ registered: project.overview_id, source: project.source });
      } else if (input.command === 'form_evidence') {
        if (!report.configuration || !report.configuration_page?.passed) throw new AgentError('EVIDENCE_COMMAND_INVALID');
        await withFormFailureEvidence(async setStage => {
          current = `/overview/${report.configuration.overview_id}`;
          await call({ command: 'open_form', overview_id: report.configuration.overview_id });
          setStage('initial_snapshot');
          current = '/wicket/page';
          report.form = [await formRecord('initial')];
          const initial = report.form[0].options.BUILD_TYPE[0].filter(option => option.selected);
          if (initial.length !== 1 || initial[0].text !== 'Full') throw new AgentError('QB_FORM_VALUE_UNAVAILABLE');
          for (const value of ['Partial', 'Full']) {
            setStage(`BUILD_TYPE_${value}`);
            const eventStart = report.events.length;
            const networkStart = report.form_network?.length ?? 0;
            const transition = { value, before: report.form.at(-1) };
            (report.form_transitions ??= []).push(transition);
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
            transition.after = report.form.at(-1);
            transition.main_frame_navigations = report.events.slice(eventStart).filter(event => event.event === 'main_frame_navigation');
            transition.document_gets = report.form_network.slice(networkStart).filter(event =>
              event.resource_type === 'Document' && event.method === 'GET' && event.response_status === null);
            transition.has_random = report.form_network.slice(networkStart).some(event => event.has_random);
            await persist();
          }
          if (runtime.policy.released || actionReleases !== 0) throw new AgentError('EVIDENCE_RELEASE_VIOLATION');
          emit({ form: report.form, action_releases: actionReleases, state: 'not_released', canonical: canonical(report.form).length });
        }, { page: runtime.page, projectName: report.configuration.project_name, guard: check,
          documentStatus: url => {
            const parsed = new URL(url);
            return report.form_network?.findLast(row => row.resource_type === 'Document'
              && row.response_status !== null && row.protocol === parsed.protocol && row.host === parsed.host
              && row.path === parsed.pathname && row.query === parsed.search.slice(1))?.response_status;
          },
          redactAddress, verify: checkedReport,
          archive: html => archive(html, 'form-unverified.response.html'),
          record: async diagnostic => {
            checkedReport(JSON.stringify(diagnostic));
            (report.form_diagnostics ??= []).push(diagnostic);
            report.pages.push({ path: '/wicket/page', file: diagnostic.file,
              sha256: diagnostic.sha256, form_unverified: true });
            await persist();
          } });
      } else throw new AgentError('EVIDENCE_COMMAND_INVALID');
      check();
      await persist();
    }
    if (report.status === 'RUNNING') stop('EVIDENCE_STDIN_CLOSED');
    }
  } finally { clearInterval(watchdog); clearInterval(nameWatch); }
} catch (error) {
  stop(error instanceof AgentError ? error.code : 'EVIDENCE_RUNTIME_ERROR');
} finally {
  channel?.dispose();
  if (runtime) await runtime.close();
  report.browser_closed = !runtime || !runtime.browser.isConnected();
  report.profile_removed = !runtime || !existsSync(runtime.profile);
  try { await persist(); }
  catch { report.status = 'STOPPED'; report.stop = { reason: 'QB_EVIDENCE_REDACTION_FAILED' }; }
  emit({ status: report.status, stop: report.stop, browser_closed: report.browser_closed,
    profile_removed: report.profile_removed, released: runtime?.policy.released ?? false });
  if (report.status === 'STOPPED') process.exitCode = 1;
}
