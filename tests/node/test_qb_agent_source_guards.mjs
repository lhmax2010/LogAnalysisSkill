import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { inspectAgentSource, inspectDriverSource, assertAgentSourceGuards,
  assertDriverSourceGuards } from './qb_agent_source_guards.mjs';

// Never import, execute, or write production code. Every mutant starts afresh
// from these actual on-disk sources, not from a hand-written passing surrogate.
const agentURL = new URL('../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs', import.meta.url);
const driverURL = new URL('../../tizen-ci-triage/scripts/ci_triage/qb_browser.py', import.meta.url);
const agent = readFileSync(agentURL, 'utf8');
const driver = readFileSync(driverURL, 'utf8');
const baseline = inspectAgentSource(agent);
const LOGIN = '  async login(timeout) {';
const ADAPTER = 'export function adaptProtocol(event) {';
const MAIN = 'async function main() {';

function insertLine(source, line, after = null) {
  assert.equal(line.includes('\n'), false, 'A mutation inserts exactly one line');
  let offset = source.length;
  if (after !== null) {
    const start = source.indexOf(after);
    assert.notEqual(start, -1, `Production insertion anchor missing: ${after}`);
    assert.equal(source.indexOf(after, start + after.length), -1, `Ambiguous insertion anchor: ${after}`);
    offset = source.indexOf('\n', start) + 1;
    assert.notEqual(offset, 0, 'Anchor must have a following line');
  }
  assert.ok(offset === 0 || source[offset - 1] === '\n', 'Insertion must start on a line boundary');
  return { source: source.slice(0, offset) + line + '\n' + source.slice(offset),
    line: source.slice(0, offset).split('\n').length };
}

function negative(name, line, rule, after = null) {
  test(`C2c RED ${name}`, () => {
    const mutant = insertLine(agent, line, after);
    const found = inspectAgentSource(mutant.source);
    assert.equal(found.some((v) => v.rule === 'parse'), false, 'A syntax error is not a killed mutation');
    // An already-red production baseline must never make a missed mutation pass.
    assert.ok(found.some((v) => v.rule === rule && v.line === mutant.line),
      `${name}: missing ${rule} at inserted line ${mutant.line}\n${JSON.stringify(found)}`);
    assert.throws(() => assertAgentSourceGuards(mutant.source), { code: 'ERR_ASSERTION' });
  });
}

function positive(name, line, after = null) {
  test(`C2c ALLOW ${name}`, () => {
    const mutant = insertLine(agent, line, after);
    const shifted = baseline.map((v) => ({ ...v, line: v.line >= mutant.line ? v.line + 1 : v.line }));
    assert.deepEqual(inspectAgentSource(mutant.source), shifted);
  });
}

test('C2c production agent satisfies frozen v1.5 section 9.2 source guards', () => assertAgentSourceGuards(agent));
test('C2c production Python driver has no test launch switches', () => assertDriverSourceGuards(driver));

// Keep each frozen API name visible in TAP output, including receiver variants.
for (const receiver of ['page', 'frame', 'locator', 'handle', 'arbitraryAlias']) {
  negative(`${receiver}.evaluate`, `await ${receiver}.evaluate(() => 1);`, 'main-world');
}
for (const name of ['evaluateAll', 'evaluateHandle', '$eval', '$$eval', 'waitForFunction',
  'addScriptTag', 'exposeFunction', 'exposeBinding']) {
  negative(name, `await arbitraryAlias.${name}(() => 1);`, 'main-world');
}
negative('evaluate optional chain', 'await arbitraryAlias?.evaluate?.(() => 1);', 'main-world');
negative('evaluate computed property', "await arbitraryAlias['evaluate'](() => 1);", 'main-world');
negative('evaluate constant concatenation', "await arbitraryAlias['eval' + 'uate'](() => 1);", 'main-world');
negative('evaluate escaped identifier', 'await arbitraryAlias.eval\\u0075ate(() => 1);', 'main-world');
negative('evaluate extracted method alias', 'const runInPage = arbitraryAlias.evaluate;', 'main-world');
negative('evaluate destructured alias', 'const { evaluate: runInPage } = arbitraryAlias;', 'main-world');
negative('evaluate inside template interpolation', 'const mutation = `${arbitraryAlias.evaluate(() => 1)}`;', 'main-world');
negative('evaluate comment between tokens', 'await arbitraryAlias /* gap */ . /* gap */ evaluate(() => 1);', 'main-world');

negative('page.request', "await page.request.get('https://example.invalid');", 'http-client');
negative('context.request', "await context.request.post('https://example.invalid');", 'http-client');
negative('request.newContext', 'await request.newContext();', 'http-client');
negative('request.newContext aliased namespace', 'const httpAlias = request; await httpAlias.newContext();', 'http-client');
negative('playwright.request.newContext', 'await playwright.request.newContext();', 'http-client');
negative('context.request alias', 'const directHttp = runtime.context.request;', 'http-client');
negative('page.request computed property', "const directHttp = page['request'];", 'http-client');
negative('request destructuring', 'const { request: directHttp } = context;', 'http-client');
negative('page.request inside protocol adapter is still forbidden', '  void page.request;', 'http-client', ADAPTER);
negative('context.request inside protocol adapter is still forbidden', '  void context.request;', 'http-client', ADAPTER);
negative('request client destructuring inside protocol adapter', '  const { request: directHttp } = context;', 'http-client', ADAPTER);
negative('cookies', 'await context.cookies();', 'cookies');
negative('storageState', 'await context.storageState();', 'storageState');
negative('cookies computed alias', "const leak = context['cookies'];", 'cookies');
negative('storageState browser option', "await browser.newContext({ storageState: 'state.json' });", 'storageState');
negative('ignoreHTTPSErrors: true', 'await browser.newContext({ ignoreHTTPSErrors: true });', 'tls');
negative('ignoreHTTPSErrors computed true', "await browser.newContext({ ['ignoreHTTPSErrors']: true });", 'tls');
negative('ignoreHTTPSErrors dynamic value', 'await browser.newContext({ ignoreHTTPSErrors: externalFlag });', 'tls');
negative('DEBUG=pw:protocol', "process.env.DEBUG = 'pw:protocol';", 'protocol-debug');
negative('PWDEBUG=1', "process.env['PWDEBUG'] = '1';", 'protocol-debug');
negative('DEBUG launch environment', "const unsafeEnv = { DEBUG: 'pw:protocol' };", 'protocol-debug');
negative('DEBUG command switch', "const debugSwitch = 'DEBUG=pw:protocol';", 'protocol-debug');
negative('fetch', "await fetch('https://example.invalid');", 'http-client');
negative('XMLHttpRequest', 'new XMLHttpRequest();', 'http-client');
for (const name of ['node:http', 'node:https', 'node:http2', 'undici', 'axios', 'got', 'node-fetch', 'superagent']) {
  negative(`HTTP module ${name}`, `await import('${name}');`, 'http-client');
}
negative('HTTP static import', "import * as unsafeHttp from 'node:https';", 'http-client');
negative('HTTP require', "const unsafeHttp = require('node:http');", 'http-client');

for (const name of ['headers', 'postData', 'postDataEntries']) {
  negative(`${name} outside protocol adapter`, `void event.request.${name};`, 'protocol-fields');
  negative(`${name} before protocol adapter`, `void event.request.${name};`, 'protocol-fields', "import { pathToFileURL } from 'node:url';");
  negative(`${name} computed access`, `void event.request['${name}'];`, 'protocol-fields');
  negative(`${name} destructuring`, `const { ${name}: leaked } = event.request;`, 'protocol-fields');
  negative(`${name} fake adapter in comment`, `/* function adaptProtocol(event) { */ void event.request.${name}; /* } */`, 'protocol-fields');
  negative(`${name} nested namesake is not protocol adapter`, `function decoy() { function adaptProtocol(event) { void event.request.${name}; } }`, 'protocol-fields');
  positive(`${name} inside actual adaptProtocol`, `  void event.request.${name};`, ADAPTER);
}

for (const name of ['click', 'fill', 'press', 'type', 'dblclick', 'tap', 'check', 'uncheck',
  'setChecked', 'selectOption', 'pressSequentially', 'insertText', 'dispatchEvent', 'focus',
  'blur', 'hover', 'dragTo', 'dragAndDrop', 'setInputFiles', 'clear', 'selectText',
  'down', 'up', 'move', 'wheel', 'submit', 'requestSubmit']) {
  negative(`login ${name}`, `    await this.page.locator('input').${name}('mutation');`, 'login-interaction', LOGIN);
}
negative('login interaction after fake closing brace comment', "    /* } async harmless() { */ await this.page.click('button');", 'login-interaction', LOGIN);
negative('login interaction after fake closing brace string', "    const marker = '} async harmless() {'; await this.page.fill('input', 'mutation');", 'login-interaction', LOGIN);
negative('login nested callback', "    await Promise.resolve().then(() => this.page.click('button'));", 'login-interaction', LOGIN);
negative('login computed interaction', "    await this.page['click']('button');", 'login-interaction', LOGIN);
negative('login inline dispatch branch', "        await this.page.click('button');", 'login-interaction', "      if (command === 'login') {");
negative('login delegated helper', "    function touch() { return arbitraryAlias.click('button'); } await touch();", 'login-interaction', LOGIN);

negative('addInitScript exactly one: extra call', 'await context.addInitScript(() => null);', 'init-count');
negative('addInitScript outside window.open installation', 'await context.addInitScript(() => null);', 'init-location');
negative('addInitScript extracted alias', 'const initialize = context.addInitScript;', 'init-count');
negative('addInitScript comment cannot authorize a call', '/* window.open guard */ await context.addInitScript(() => document.title);', 'init-location');
negative('setContent outside startupSelfTest', "await page.setContent('<p>mutation</p>');", 'set-content');
negative('setContent in login', "    await this.page.setContent('<p>mutation</p>');", 'set-content', LOGIN);
negative('setContent fake selftest comment', "/* async function startupSelfTest() { */ await page.setContent(''); /* } */", 'set-content');
negative('setContent nested namesake is not startupSelfTest', "async function decoy() { async function startupSelfTest() { await page.setContent(''); } }", 'set-content');
negative('setContent computed call', "await page['setContent']('');", 'set-content');

test('C2c RED addInitScript zero calls cannot be rescued by comment or string', () => {
  assert.ok(agent.includes('.addInitScript('));
  const mutant = agent.replace('.addInitScript(', '.unusedInitScript(')
    + "\n// context.addInitScript(() => window.open);\nconst commentDecoy = 'context.addInitScript(';\n";
  assert.ok(inspectAgentSource(mutant).some((v) => v.rule === 'init-count' && v.message.includes('found 0')));
  assert.throws(() => assertAgentSourceGuards(mutant), { code: 'ERR_ASSERTION' });
});
test('C2c RED sole addInitScript guard cannot also read page data', () => {
  const mutant = insertLine(agent, '      get stolen() { return document.title; },',
    "await runtime.context.addInitScript(() => Object.defineProperty(window, 'open', {");
  const found = inspectAgentSource(mutant.source);
  assert.equal(found.some((v) => ['parse', 'init-count'].includes(v.rule)), false);
  assert.ok(found.some((v) => v.rule === 'init-location'));
  assert.throws(() => assertAgentSourceGuards(mutant.source), { code: 'ERR_ASSERTION' });
});
test('C2c RED sole addInitScript must precede navigation', () => {
  const before = '    await runtime.context.addInitScript(';
  const index = agent.indexOf(before);
  assert.notEqual(index, -1);
  const mutant = agent.slice(0, index) + "    await runtime.page.goto('about:blank');\n" + agent.slice(index);
  const found = inspectAgentSource(mutant);
  assert.equal(found.some((v) => ['parse', 'init-count'].includes(v.rule)), false);
  assert.ok(found.some((v) => v.rule === 'init-location'));
  assert.throws(() => assertAgentSourceGuards(mutant), { code: 'ERR_ASSERTION' });
});
for (const [name, before, after] of [
  ['wrong function', 'async function launchRuntime(', 'async function unrelatedRuntime('],
  ['wrong receiver', 'await runtime.context.addInitScript(', 'await runtime.page.addInitScript('],
  ['not awaited', 'await runtime.context.addInitScript(', 'runtime.context.addInitScript('],
]) test(`C2c RED sole addInitScript ${name}`, () => {
  assert.ok(agent.includes(before));
  const mutant = agent.replace(before, after);
  const found = inspectAgentSource(mutant);
  assert.equal(found.some((v) => ['parse', 'init-count'].includes(v.rule)), false);
  assert.ok(found.some((v) => v.rule === 'init-location'));
  assert.throws(() => assertAgentSourceGuards(mutant), { code: 'ERR_ASSERTION' });
});

for (const [name, line] of [
  ['refresh allowset', 'const refresh = new Set();'],
  ['refreshUrls allowset', 'const refreshUrls = new Set();'],
  ['refresh property allowset', 'policy.refresh = new Set();'],
  ['refresh allowset lookup', 'policy.refresh.has(url);'],
  ['registerRefresh', 'await agent.registerRefresh();'],
  ['extractRefresh', 'await agent.extractRefresh();'],
  ['ajaxRefresh DOM extraction', "document.querySelectorAll('[href*=ajaxRefresh]');"],
  ['ajaxRefresh script extraction', 'script.textContent.matchAll(/ajaxRefresh/g);'],
  ['ajaxRefresh registration', "policy.allowed.add('https://example.invalid/?action=ajaxRefresh');"],
]) negative(name, line, 'refresh');
negative('cloneNode active document', 'document.documentElement.cloneNode(true);', 'cloneNode');
negative('cloneNode arbitrary alias', 'nodeAlias.cloneNode(true);', 'cloneNode');

for (const name of ['testOptions', 'launchArgs', 'diagnostic', 'useBrowserFetch', 'syntheticCount']) {
  negative(`main test option ${name}`, `  await createRuntime('module', 'chromium', { ${name}: true });`, 'production-options', MAIN);
}
negative('main anonymous third runtime argument', "  await createRuntime('module', 'chromium', {});", 'production-options', MAIN);
negative('main spread runtime arguments', '  await createRuntime(...externalArguments);', 'production-options', MAIN);

positive('normal browser.newContext', 'await browser.newContext({ acceptDownloads: false });');
positive('aliased browser.newContext', 'const browserAlias = browser; await browserAlias.newContext();');
positive('normal runtime.browser.newContext', 'await runtime.browser.newContext({ serviceWorkers: "block" });');
positive('ignoreHTTPSErrors: false', 'await browser.newContext({ ignoreHTTPSErrors: false });');
positive('Response.request metadata', 'response?.request().redirectedFrom();');
positive('protocol event.request destructuring', '  const { request: payload } = event;', ADAPTER);
positive('Runtime.evaluate CDP string', "await session.send('Runtime.evaluate', { expression: '1', contextId: 1 });");
positive('forbidden names inside comment', '// page.evaluate(); context.cookies(); storageState; headers; postData; postDataEntries; cloneNode();');
positive('forbidden names inside string', "const documentation = 'page.evaluate() setContent() addInitScript() headers postData postDataEntries';");
positive('forbidden names inside regex', 'const pattern = /evaluate\\(headers\\)\\{cloneNode\\}/;');
positive('DEBUG deletion', 'delete process.env.DEBUG; delete process.env.PWDEBUG;');
positive('refresh denial matcher', 'const deniedTimer = /ajaxRefresh/.test(query);');
positive('non-login interaction', "async function unrelatedInteraction() { await page.click('button'); }");
positive('main sanitized diagnostic response data', '  const diagnostic = response.diagnostic;', MAIN);
positive('source is never executed', "throw new Error('Static guard must not execute this source');");
positive('startupSelfTest setContent', "    await runtime.page.setContent('<p>selftest</p>');", 'export async function startupSelfTest(');

function driverNegative(name, line, after = null, rule = 'driver-options') {
  test(`C2c RED Python driver ${name}`, () => {
    const mutant = insertLine(driver, line, after);
    const found = inspectDriverSource(mutant.source);
    assert.equal(found.some((v) => v.rule === 'parse'), false);
    assert.ok(found.some((v) => v.rule === rule && v.line === mutant.line),
      `${name}: missing ${rule}\n${JSON.stringify(found)}`);
    assert.throws(() => assertDriverSourceGuards(mutant.source), { code: 'ERR_ASSERTION' });
  });
}
for (const name of ['testOptions', 'test_options', 'launchArgs', 'launch_args',
  'useBrowserFetch', 'use_browser_fetch', 'syntheticCount', 'synthetic_count']) {
  driverNegative(name, `unsafe_options = {"${name}": True}`);
}
for (const flag of ['--test-options', '--diagnostic', '--launch-args', '--use-browser-fetch',
  '--synthetic-count', '--host-resolver-rules=MAP example.invalid 127.0.0.1', '--ignore-certificate-errors-spki-list=fixture']) {
  driverNegative(`argv ${flag}`, `                    "${flag}",`, '                    browser["chromium"],');
}
driverNegative('diagnostic launch keyword', '                diagnostic=True,', '                env=env,');
driverNegative('unknown fifth argv element', '                    "--unknown-test-switch",', '                    browser["chromium"],', 'driver-argv');
driverNegative('argv unpacking', '                    *extra_arguments,', '                    browser["chromium"],', 'driver-argv');
test('C2c ALLOW Python diagnostic and diagnostic_failed response fields', () => {
  const mutant = insertLine(driver, 'diagnostic = {"diagnostic": None, "diagnostic_failed": False}');
  assertDriverSourceGuards(mutant.source);
});
test('C2c ALLOW Python diagnostic QbBrowserError keyword', () => {
  const mutant = insertLine(driver, 'error = QbBrowserError("QB_FORM_CHANGED", diagnostic={}, diagnostic_failed=False)');
  assertDriverSourceGuards(mutant.source);
});
test('C2c ALLOW Python comments do not become launch flags', () => {
  const mutant = insertLine(driver, '# --diagnostic testOptions launchArgs useBrowserFetch');
  assertDriverSourceGuards(mutant.source);
});
test('C2c RED malformed JS fails closed', () => {
  assert.equal(inspectAgentSource(agent + '\nconst = ;')[0].rule, 'parse');
  assert.throws(() => assertAgentSourceGuards(agent + '\nconst = ;'), { code: 'ERR_ASSERTION' });
});
test('C2c RED malformed Python fails closed', () => {
  assert.equal(inspectDriverSource(driver + '\nif :')[0].rule, 'parse');
  assert.throws(() => assertDriverSourceGuards(driver + '\nif :'), { code: 'ERR_ASSERTION' });
});
