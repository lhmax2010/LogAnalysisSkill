import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash, X509Certificate } from 'node:crypto';
import { existsSync } from 'node:fs';
import { mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { createServer } from 'node:https';
import test from 'node:test';
import {
  Agent, createRuntime, FIELDS, ORIGIN, responseText, validateForm,
} from '../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';

// Run with the Playwright module and Chromium executable as positional arguments.
// All responses are synthetic; DNS and the test certificate point only to loopback.
const [playwright, chromium] = process.argv.slice(2);
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const project = {
  overview_id: 17, project_name: 'Synthetic Project',
  configuration_path: 'root/LOCAL/TrustedExample',
};
const runPath = '/wicket/page?17-1.ILinkListener-run';
const callback = `${ORIGIN}/wicket/page?20-1.IBehaviorListener.0-form-field`;
const submit = `${ORIGIN}/wicket/page?20-1.IFormSubmitListener-form`;
const secret = 'c2c-hidden-private-73';
const sessionSecret = 'c2c-url-private-91';
const imagePath = '/images/c2c-no-store.png';
const scriptTag = '<script src="/scripts/c2c-hostile.js"></script>';
const escapeHTML = text => text.replaceAll('&', '&amp;').replaceAll('"', '&quot;')
  .replaceAll('<', '&lt;').replaceAll('>', '&gt;');

function documentHTML(body, title = 'Synthetic C2c', script = true) {
  return `<!doctype html><html><head><meta charset="utf-8"><title>${escapeHTML(title)}</title>
    <link rel="icon" href="data:,"></head><body>${body}${script ? scriptTag : ''}</body></html>`;
}

function buildHTML(id, { extra = '', summary = true, nav = true, script = true } = {}) {
  return documentHTML(`${nav ? `<a class="nav-link"> \nBuild (id:${id})\t </a>` : ''}
    ${summary ? `<div class="build-summary"><div class="box-head"> \nSummary\t </div><table>
      <thead><tr><th> \nId\t </th><th>Status</th></tr></thead>
      <tbody><tr><td> \n${id}\t </td><td id="status">Failed</td></tr></tbody></table></div>` : ''}
    <span>Welcome! Synthetic Reader</span><input type="hidden" name="token" value="${secret}">
    <p>prefix-${secret}-suffix</p>${extra}`, 'Synthetic C2c', script);
}

function formHTML({ mismatch = false, image = false } = {}) {
  const row = (label, contents) => `<tr><td class="form-label"> \n${escapeHTML(label)}\t </td>
    <td class="value">${contents}</td></tr>`;
  const rows = [row('PROJECT_NAME', `<span class="property-viewer"> ${project.project_name} </span>`)];
  for (const [index, label] of FIELDS.entries()) {
    const onchange = escapeHTML(`wicketAjaxPost('${callback}${index}', 0)`);
    const name = `form:field${index}`;
    let controls;
    if (['CHILD_CONFIGURATIONS', 'TARGET_IMAGE'].includes(label)) {
      controls = `<input type="hidden" name="${name}:palette:recorder" value="" onchange="${onchange}">
        <select name="${name}:palette:choices"><option value="a"> Alpha </option></select>
        <select name="${name}:palette:selection"></select>`;
    } else if (label === 'BUILD_TYPE') {
      controls = `<select name="${name}:input" onchange="${onchange}">
        <option value="full"> \nFull\t </option><option value="partial"> Partial </option></select>`;
    } else {
      controls = `<input name="${name}:input" value="unchanged" onchange="${onchange}">`;
    }
    rows.push(row(label, controls));
  }
  if (mismatch) rows.push(row(`UNKNOWN-${secret}`, `<input name="extra:input" onchange="${escapeHTML(
    `wicketAjaxPost('/wicket/page;jsessionid=${sessionSecret}?20-1.IBehaviorListener.0-form-extra', 0)`,
  )}">`));
  return documentHTML(`<h1>Specify Build Options</h1><span>Welcome! Synthetic Reader</span>
    <form method="post" action="${submit}"><table>${rows.join('')}</table>
    <input type="hidden" name="token" value="${secret}"></form>
    ${image ? `<img src="${imagePath}" alt="local fixture">` : ''}`, 'Specify Build Options');
}

function configurationHTML() {
  const onclick = `var win = this.ownerDocument.defaultView || this.ownerDocument.parentWindow; if (win == window) { window.location.href='../wicket/page?17-1.ILinkListener-run'; } ;return false`;
  return documentHTML(`<button title="Run the configuration" onclick="${escapeHTML(onclick)}">Run</button>`,
    `QuickBuild - ${project.configuration_path}`);
}

// Runs as an actual server-delivered main-world script, never as an agent reader.
function hostileMain() {
  const outer = Object.getOwnPropertyDescriptor(Element.prototype, 'outerHTML');
  const text = Object.getOwnPropertyDescriptor(Node.prototype, 'textContent');
  const parse = DOMParser.prototype.parseFromString;
  String.prototype.trim = function () { return this.replace(/^\s+|\s+$/, ''); };
  Object.defineProperty(Element.prototype, 'outerHTML', { ...outer,
    get() { return outer.get.call(this).replaceAll('Failed', 'Successful'); } });
  Object.defineProperty(Node.prototype, 'textContent', { ...text,
    get() { return text.get.call(this)?.replaceAll('Failed', 'Successful'); } });
  DOMParser.prototype.parseFromString = function () {
    return parse.call(this, '<html><body>HOSTILE_PARSE</body></html>', 'text/html');
  };
  for (const prototype of [Document.prototype, Element.prototype]) {
    const query = prototype.querySelectorAll;
    prototype.querySelectorAll = function (selector) {
      return [...query.call(this, selector)].filter(element =>
        !element.matches('.nav-link, .build-summary, .form-label, input[type=hidden]'));
    };
  }
  Function.prototype.toString = function () { return 'function () { [native code] }'; };
  globalThis.c2cHostileInstalled = true;
}

async function fixtureServer(t) {
  const directory = await mkdtemp('/dev/shm/p5q-c2c-trusted-');
  t.after(() => rm(directory, { recursive: true, force: true }));
  execFileSync('openssl', ['req', '-x509', '-newkey', 'rsa:2048', '-nodes',
    '-keyout', `${directory}/key.pem`, '-out', `${directory}/cert.pem`, '-days', '1',
    '-subj', '/CN=quickbuild.tizen.org', '-addext', 'subjectAltName=DNS:quickbuild.tizen.org'],
  { stdio: 'ignore' });
  const cert = await readFile(`${directory}/cert.pem`);
  const key = await readFile(`${directory}/key.pem`);
  const spki = createHash('sha256').update(new X509Certificate(cert).publicKey.export({
    type: 'spki', format: 'der',
  })).digest('base64');
  const fixture = { routes: new Map(), received: [], script: '' };
  const server = createServer({ cert, key }, (request, response) => {
    fixture.received.push({ method: request.method, path: request.url,
      host: request.headers.host, remote: request.socket.remoteAddress });
    request.resume();
    response.setHeader('Cache-Control', 'no-store');
    if (request.url === '/scripts/c2c-hostile.js') {
      response.setHeader('Content-Type', 'application/javascript');
      response.end(fixture.script);
    } else if (request.url === imagePath) {
      response.setHeader('Content-Type', 'image/png');
      response.end(Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aP1sAAAAASUVORK5CYII=', 'base64'));
    } else {
      const route = fixture.routes.get(request.url);
      response.statusCode = route ? 200 : 404;
      response.setHeader('Content-Type', route?.contentType ?? 'text/html; charset=utf-8');
      response.end(route?.body ?? 'Unknown local fixture');
    }
  });
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  t.after(async () => {
    server.closeAllConnections();
    await new Promise(resolve => server.close(resolve));
  });
  fixture.overrides = { launchArgs: ['--no-proxy-server',
    `--host-resolver-rules=MAP quickbuild.tizen.org 127.0.0.1:${server.address().port}, EXCLUDE 127.0.0.1, MAP * ~NOTFOUND`,
    `--ignore-certificate-errors-spki-list=${spki}`] };
  fixture.set = (path, body, contentType) => fixture.routes.set(path, { body, contentType });
  fixture.forms = options => {
    fixture.set(`/overview/${project.overview_id}`, configurationHTML());
    fixture.set(runPath, formHTML(options));
  };
  return fixture;
}

// Observe only the agent's newly opened CDP sessions, not the interception guards.
function observeTrusted(runtime) {
  const original = runtime.context.newCDPSession;
  const tape = { sessions: [], worlds: [], evaluations: [], parseCounts: [],
    failWorld: false, staleId: null, countParses: false };
  runtime.context.newCDPSession = async function (...args) {
    const session = await original.apply(this, args);
    const send = session.send.bind(session);
    const detach = session.detach.bind(session);
    const lifetime = { detached: false };
    tape.sessions.push(lifetime);
    session.detach = async () => { try { return await detach(); } finally { lifetime.detached = true; } };
    session.send = async (method, params) => {
      if (method === 'Page.createIsolatedWorld') {
        if (tape.failWorld) throw new Error('synthetic createIsolatedWorld failure');
        const result = await send(method, params);
        tape.worlds.push({ id: result.executionContextId, url: runtime.page.url(), frameId: params.frameId });
        return result;
      }
      if (method !== 'Runtime.evaluate') return send(method, params);
      const evaluation = { contextId: tape.staleId ?? params.contextId, failed: false };
      tape.evaluations.push(evaluation);
      const actual = { ...params, contextId: evaluation.contextId };
      if (tape.countParses) {
        await send(method, { contextId: actual.contextId, expression: `
          globalThis.c2cParseOriginal = DOMParser.prototype.parseFromString;
          globalThis.c2cParseCount = 0;
          DOMParser.prototype.parseFromString = function (...args) {
            globalThis.c2cParseCount++;
            return Reflect.apply(globalThis.c2cParseOriginal, this, args);
          };` });
      }
      try {
        const result = await send(method, actual);
        evaluation.failed = Boolean(result.exceptionDetails);
        return result;
      } catch (error) { evaluation.failed = true; throw error; }
      finally {
        if (tape.countParses) {
          const result = await send(method, { contextId: actual.contextId, returnByValue: true,
            expression: `(() => {
              DOMParser.prototype.parseFromString = globalThis.c2cParseOriginal;
              const count = globalThis.c2cParseCount;
              delete globalThis.c2cParseOriginal; delete globalThis.c2cParseCount;
              return count;
            })()` });
          tape.parseCounts.push(result.result.value);
        }
      }
    };
    return session;
  };
  tape.restore = () => { runtime.context.newCDPSession = original; };
  return tape;
}

function observeCapture(runtime) {
  const root = runtime.guards.root;
  const original = root.send;
  const capture = { requests: new Map(), calls: [], order: [] };
  const paused = event => {
    capture.requests.set(event.requestId, { url: event.request.url, frameId: event.frameId,
      type: event.resourceType, status: event.responseStatusCode ?? null,
      main: runtime.guards.frames.parents.get(event.frameId) === null });
  };
  root.prependListener('Fetch.requestPaused', paused);
  root.send = async (method, params) => {
    if (method === 'Fetch.continueResponse') capture.order.push({ method, requestId: params.requestId });
    if (method !== 'Fetch.getResponseBody') return original.call(root, method, params);
    const call = { requestId: params.requestId, request: capture.requests.get(params.requestId),
      navigation: runtime.policy.readNavigation };
    capture.calls.push(call);
    const result = await original.call(root, method, params);
    call.base64 = result.base64Encoded;
    call.bytes = result.base64Encoded ? Buffer.from(result.body, 'base64') : null;
    capture.order.push({ method, requestId: params.requestId });
    return result;
  };
  capture.restore = () => { root.send = original; root.removeListener('Fetch.requestPaused', paused); };
  return capture;
}

async function withRuntime(fixture, action) {
  const start = fixture.received.length;
  const runtime = await createRuntime(playwright, chromium, fixture.overrides);
  const tape = observeTrusted(runtime);
  const capture = observeCapture(runtime);
  const originals = new Map();
  const main = runtime.page.evaluate.bind(runtime.page);
  const fallback = [];
  for (const name of ['evaluate', 'evaluateHandle', '$eval', '$$eval', 'content', 'waitForFunction']) {
    originals.set(name, runtime.page[name]);
    runtime.page[name] = () => { fallback.push(name); throw new Error('main-world fallback forbidden'); };
  }
  const goto = runtime.page.goto;
  originals.set('goto', goto);
  runtime.page.goto = async function (...args) {
    const response = await goto.apply(this, args);
    if (!response) return response;
    return new Proxy(response, { get(target, key) {
      if (key === 'body') return () => { fallback.push('response.body'); throw new Error('transcoded body forbidden'); };
      const value = Reflect.get(target, key);
      return typeof value === 'function' ? value.bind(target) : value;
    } });
  };
  const agent = new Agent(runtime);
  agent.state = 'ready';
  agent.projects.set(project.overview_id, project);
  runtime.policy.overviewIds.add(String(project.overview_id));
  try {
    await action({ runtime, agent, tape, capture, main, fallback });
    assert.deepEqual(fallback, [], 'agent attempted a main-world fallback');
    for (const call of capture.calls) {
      assert.equal(call.request.main, true, 'captured a subframe response');
      assert.equal(call.request.type, 'Document', 'captured a subresource response');
      assert.equal(call.request.url, call.navigation.url, 'captured a different URL');
      assert.equal(call.requestId, call.navigation.requestId, 'captured a different request');
      const captured = capture.order.findIndex(event => event.requestId === call.requestId
        && event.method === 'Fetch.getResponseBody');
      const continued = capture.order.findIndex(event => event.requestId === call.requestId
        && event.method === 'Fetch.continueResponse');
      assert.ok(captured >= 0 && continued > captured, 'response continued before its bytes were captured');
    }
    assert.ok(tape.sessions.every(session => session.detached), 'trusted CDP session leaked');
    assert.equal(runtime.failure, null, 'runtime guard failed');
  } finally {
    for (const [name, original] of originals) runtime.page[name] = original;
    tape.restore();
    capture.restore();
    await runtime.close();
    assert.equal(existsSync(runtime.profile), false, 'browser profile was not removed');
    for (const request of fixture.received.slice(start)) {
      assert.equal(request.remote, '127.0.0.1');
      assert.equal(request.host, 'quickbuild.tizen.org');
      assert.equal(request.method, 'GET', 'read/diagnosis unexpectedly submitted a request');
    }
  }
}

async function assertNative(trusted) {
  const functions = await trusted.run(() => {
    const getter = (prototype, name) => Object.getOwnPropertyDescriptor(prototype, name).get;
    return Object.fromEntries(Object.entries({
      outerHTML: getter(Element.prototype, 'outerHTML'),
      innerHTML: getter(Element.prototype, 'innerHTML'),
      textContent: getter(Node.prototype, 'textContent'),
      DOMParser, parseFromString: DOMParser.prototype.parseFromString,
      trim: String.prototype.trim, trimStart: String.prototype.trimStart, trimEnd: String.prototype.trimEnd,
      documentQuery: Document.prototype.querySelectorAll, elementQuery: Element.prototype.querySelectorAll,
      toString: Function.prototype.toString,
    }).map(([name, fn]) => [name, Function.prototype.toString.call(fn)]));
  });
  for (const [name, source] of Object.entries(functions)) {
    assert.match(source, /^function [\s\S]*\{\s*\[native code\]\s*\}$/, `${name} is not native in isolation`);
    assert.notEqual(source, 'function () { [native code] }', `${name} used the hostile toString`);
  }
  const facts = await trusted.run(document => ({
    inert: document.defaultView === null, trim: ' x '.trim(),
    text: document.getElementById('probe').textContent,
    html: document.getElementById('probe').outerHTML,
    count: document.querySelectorAll('.nav-link').length,
  }), '<p id="probe" class="nav-link">Failed</p>');
  assert.deepEqual(facts, { inert: true, trim: 'x', text: 'Failed',
    html: '<p id="probe" class="nav-link">Failed</p>', count: 1 });
}

function assertScrubbed(value) {
  const text = JSON.stringify(value);
  assert.ok(!text.includes(secret), 'hidden secret survived redaction');
  assert.ok(!text.includes(sessionSecret), 'URL session secret survived redaction');
  assert.doesNotMatch(text, /JSESSIONID_8810=/);
}

function seedRegistrations(policy) {
  policy.runUrl = ORIGIN + runPath;
  policy.beginField(callback);
  policy.submitUrl = submit;
}

function assertRevoked(policy) {
  assert.equal(policy.runUrl, null, 'run registration survived');
  assert.equal(policy.fieldUrl, null, 'field registration survived');
  assert.equal(policy.submitUrl, null, 'submit registration survived');
  assert.equal(policy.fieldWindow, null, 'field window survived');
}

// Seed after the failing snapshot is read, so command-entry invalidation alone
// cannot satisfy the requirement to revoke registrations before diagnosis.
function seedAtMismatch(agent, kind) {
  const run = agent.trusted.run.bind(agent.trusted);
  const seeded = { count: 0 };
  agent.trusted.run = async (...args) => {
    const value = await run(...args);
    if (!seeded.count && (kind === 'read' ? Boolean(value?.build) : Array.isArray(value?.rows))) {
      seedRegistrations(agent.policy);
      seeded.count++;
    }
    return value;
  };
  return seeded;
}

function diagnosticFixture(fixture, kind) {
  fixture.script = '';
  if (kind === 'read') {
    fixture.set('/build/707/overview', buildHTML(808, {
      extra: `<a class="nav-link">unrecognized-${secret}</a>
        <a href="/wicket/page;jsessionid=${sessionSecret}?20">local</a>
        <img src="${imagePath}" alt="local fixture">`,
    }));
    return { command: 'read', path: '/build/707/overview' };
  }
  fixture.forms({ mismatch: true, image: true });
  return { command: 'open_form', overview_id: project.overview_id };
}

test('C2c isolated/inert read and diagnosis (synthetic loopback HTTPS only)', { timeout: 180000 }, async t => {
  assert.ok(playwright && chromium, 'pass the Playwright module and Chromium executable paths');
  const fixture = await fixtureServer(t);

  await t.test('hostile main-world builtins leave read, identity, form and redaction unchanged', async () => {
    fixture.set('/build/101/overview', buildHTML(101));
    fixture.forms();
    await withRuntime(fixture, async ({ agent, tape, main }) => {
      fixture.script = '';
      tape.countParses = true;
      const baselineRead = await agent.command({ command: 'read', path: '/build/101/overview' });
      tape.countParses = false;
      assert.equal(baselineRead.ok, true);
      assert.equal(baselineRead.status, 200);
      assert.equal(Number.isInteger(baselineRead.outside_identity_count), true);
      assert.ok(baselineRead.outside_identity_count >= 0);
      assert.match(baselineRead.html_redacted, /<td id="status">Failed<\/td>/);
      assertScrubbed(baselineRead);
      assert.match(baselineRead.html_redacted, /Welcome! &lt;USER&gt;/);
      assert.deepEqual(tape.parseCounts, [1], 'raw read must parse exactly once');
      assert.deepEqual(await agent.command({ command: 'open_form', overview_id: 17 }), { ok: true, released: false });
      const baselineForm = await agent.snapshot();
      validateForm(baselineForm, project.project_name);

      fixture.script = `(${hostileMain.toString()})();`;
      const hostileRead = await agent.command({ command: 'read', path: '/build/101/overview' });
      assert.deepEqual(hostileRead, baselineRead);
      assert.deepEqual(await main(() => ({
        installed: globalThis.c2cHostileInstalled, trim: ' x '.trim(),
        text: document.getElementById('status').textContent,
        html: document.getElementById('status').outerHTML,
        parser: new DOMParser().parseFromString('<p>Failed</p>', 'text/html').body.innerText,
        documentQuery: document.querySelectorAll('.nav-link').length,
        elementQuery: document.body.querySelectorAll('.nav-link').length,
        spoof: Function.prototype.toString.call(String.prototype.trim),
      })), { installed: true, trim: 'x ', text: 'Successful', html: '<td id="status">Successful</td>',
        parser: 'HOSTILE_PARSE', documentQuery: 0, elementQuery: 0, spoof: 'function () { [native code] }' });
      await assertNative(agent.trusted);
      assert.equal(await agent.buildId('/build/101/overview'), '101');
      assert.deepEqual(await agent.command({ command: 'open_form', overview_id: 17 }), { ok: true, released: false });
      assert.equal(await main(() => globalThis.c2cHostileInstalled), true);
      const hostileForm = await agent.snapshot();
      assert.deepEqual(hostileForm, baselineForm);
      const fields = validateForm(hostileForm, project.project_name);
      assert.deepEqual(fields.BUILD_TYPE.controls[0].options.map(option => option.text), ['Full', 'Partial']);
      await assertNative(agent.trusted);
    });
  });

  await t.test('response remains Failed after the live DOM becomes Successful', async () => {
    fixture.script = "document.getElementById('status').textContent = 'Successful';";
    fixture.set('/build/102/overview', buildHTML(102));
    await withRuntime(fixture, async ({ agent, main }) => {
      const result = await agent.command({ command: 'read', path: '/build/102/overview' });
      assert.equal(result.ok, true);
      assert.equal(await main(() => document.getElementById('status').textContent), 'Successful');
      assert.equal(await agent.trusted.run(document => document.getElementById('status').textContent), 'Successful');
      assert.match(agent.rawRead, /<td id="status">Failed<\/td>/);
      assert.match(result.html_redacted, /<td id="status">Failed<\/td>/);
      assert.doesNotMatch(result.html_redacted, /Successful/);
    });
  });

  await t.test('script-inserted build identity cannot rescue missing response identity', async () => {
    fixture.script = "const a = document.createElement('a'); a.className = 'nav-link'; a.textContent = 'Build (id:103)'; document.body.append(a);";
    fixture.set('/build/103/overview', buildHTML(103, { nav: false }));
    await withRuntime(fixture, async ({ agent }) => {
      const result = await agent.command({ command: 'read', path: '/build/103/overview' });
      assert.equal(await agent.buildId('/build/103/overview'), '103');
      assert.equal(result.ok, false);
      assert.equal(result.error, 'QB_READ_ID_MISMATCH');
      assert.deepEqual(result.diagnostic.facts.labels, []);
      assert.doesNotMatch(result.diagnostic.html_redacted, /Build \(id:103\)/);
    });
  });

  await t.test('two reads and both openForm navigations recreate the isolated context', async () => {
    fixture.script = '';
    fixture.set('/build/201/overview', buildHTML(201));
    fixture.set('/build/202/variables', buildHTML(202, { summary: false }));
    fixture.forms();
    const paths = ['/build/201/overview', '/build/202/variables', '/overview/17', runPath];
    const start = fixture.received.length;
    await withRuntime(fixture, async ({ agent, tape }) => {
      for (const path of paths.slice(0, 2)) assert.equal((await agent.command({ command: 'read', path })).ok, true);
      assert.deepEqual(await agent.command({ command: 'open_form', overview_id: 17 }), { ok: true, released: false });
      const ids = paths.map(path => {
        const worlds = tape.worlds.filter(world => world.url === ORIGIN + path);
        assert.ok(worlds.length, `no isolated context observed after ${path}`);
        assert.ok(worlds.every(world => world.frameId && Number.isInteger(world.id)));
        return worlds[0].id;
      });
      assert.equal(new Set(ids).size, paths.length, 'a context was reused across navigation');
      assert.ok(tape.evaluations.every(evaluation => tape.worlds.some(world => world.id === evaluation.contextId)));
      assert.deepEqual(fixture.received.slice(start).filter(request => paths.includes(request.path))
        .map(request => request.path), paths);
    });
  });

  await t.test('capture is exclusive to this read main-frame navigation, never same-URL fetches or frames', async () => {
    const path = '/build/501/overview';
    fixture.set(path, buildHTML(501, { extra: '<p>FIRST_RESPONSE</p>' }));
    fixture.set('/build/502/variables', buildHTML(502, { summary: false, script: false }));
    fixture.script = `if (window === window.top) {
      const frame = document.createElement('iframe'); frame.src = '${path}'; document.body.append(frame);
      globalThis.c2cNoise = Promise.all([fetch('${path}'), fetch('/build/502/variables')])
        .then(responses => responses.map(response => response.status));
    }`;
    await withRuntime(fixture, async ({ runtime, agent, capture, main }) => {
      assert.equal((await agent.command({ command: 'read', path })).ok, true);
      assert.deepEqual(await main(() => globalThis.c2cNoise), [200, 200]);
      assert.equal(capture.calls.length, 1);
      const requests = [...capture.requests.values()];
      assert.ok(requests.some(request => request.url === ORIGIN + path && request.type === 'Document' && !request.main));
      assert.ok(requests.some(request => request.url === ORIGIN + path && request.type !== 'Document'));
      assert.ok(requests.some(request => request.url === ORIGIN + '/build/502/variables'));
      assert.equal(runtime.policy.readNavigation, null);
      const first = capture.calls[0];
      fixture.script = '';
      fixture.set(path, buildHTML(501, { extra: '<p>SECOND_RESPONSE</p>' }));
      const result = await agent.command({ command: 'read', path });
      assert.equal(result.ok, true);
      assert.match(result.html_redacted, /SECOND_RESPONSE/);
      assert.doesNotMatch(result.html_redacted, /FIRST_RESPONSE/);
      assert.equal(capture.calls.length, 2);
      const second = capture.calls[1];
      assert.notEqual(second.requestId, first.requestId);
      assert.notEqual(second.navigation, first.navigation);
      assert.equal(first.navigation.body, null);
      assert.equal(second.navigation.body, null);

      runtime.policy.phase = 'read';
      await runtime.page.goto(ORIGIN + path);
      runtime.policy.phase = 'idle';
      fixture.forms();
      assert.deepEqual(await agent.command({ command: 'open_form', overview_id: 17 }), { ok: true, released: false });
      assert.equal(capture.calls.length, 2, 'non-command read or openForm captured a response body');
    });
  });

  for (const mismatch of ['absent slot', 'wrong URL', 'wrong request id', 'wrong frame id']) {
    await t.test(`${mismatch} cannot reuse a preceding read's captured bytes`, async () => {
      fixture.script = '';
      const path = '/build/601/overview';
      fixture.set(path, buildHTML(601));
      await withRuntime(fixture, async ({ runtime, agent, capture, tape }) => {
        assert.equal((await agent.command({ command: 'read', path })).ok, true);
        const previous = capture.calls[0].navigation;
        const evaluations = tape.evaluations.length;
        const root = runtime.guards.root;
        const send = root.send;
        let injected = false;
        root.send = async (method, params) => {
          const navigation = runtime.policy.readNavigation;
          if (!injected && method === 'Fetch.continueRequest' && navigation?.requestId === params.requestId) {
            injected = true;
            if (mismatch === 'absent slot') runtime.policy.readNavigation = null;
            if (mismatch === 'wrong URL') navigation.url = ORIGIN + '/build/999/overview';
            if (mismatch === 'wrong request id') navigation.requestId = 'unmatched-request';
            if (mismatch === 'wrong frame id') navigation.frameId = 'unmatched-frame';
          }
          return send.call(root, method, params);
        };
        try {
          assert.deepEqual(await agent.command({ command: 'read', path }),
            { ok: false, error: 'QB_TRUSTED_CONTEXT_UNAVAILABLE' });
          assert.equal(injected, true);
          assert.equal(capture.calls.length, 1, 'unmatched response body was captured');
          assert.equal(tape.evaluations.length, evaluations, 'unmatched bytes reached the parser');
          assert.equal(agent.rawRead, null);
          assert.equal(previous.body, null);
          assert.equal(runtime.policy.readNavigation, null);
        } finally { root.send = send; }
        assert.equal((await agent.command({ command: 'read', path })).ok, true);
      });
    });
  }

  await t.test('in-flight capture rejects a replaced slot even when it contains old valid bytes', async () => {
    fixture.script = '';
    const path = '/build/602/overview';
    const firstBody = buildHTML(602, { extra: '<p>OLD_BYTES</p>' });
    fixture.set(path, firstBody);
    await withRuntime(fixture, async ({ runtime, agent, capture, tape }) => {
      assert.equal((await agent.command({ command: 'read', path })).ok, true);
      const stale = capture.calls[0].navigation;
      const evaluations = tape.evaluations.length;
      fixture.set(path, buildHTML(602, { extra: '<p>NEW_BYTES</p>' }));
      const root = runtime.guards.root;
      const send = root.send;
      let injected = false;
      root.send = async (method, params) => {
        const result = await send.call(root, method, params);
        if (method === 'Fetch.getResponseBody') {
          stale.body = Buffer.from(firstBody);
          runtime.policy.readNavigation = stale;
          injected = true;
        }
        return result;
      };
      try {
        assert.deepEqual(await agent.command({ command: 'read', path }),
          { ok: false, error: 'QB_TRUSTED_CONTEXT_UNAVAILABLE' });
        assert.equal(injected, true);
        assert.equal(agent.rawRead, null);
        assert.equal(tape.evaluations.length, evaluations);
        assert.equal(capture.calls.at(-1).navigation.failed, true);
        assert.equal(capture.calls.at(-1).navigation.body, null);
        assert.deepEqual(stale.body, Buffer.from(firstBody), 'late capture wrote into the replacement slot');
      } finally {
        root.send = send;
        stale.body = null;
        runtime.policy.readNavigation = null;
      }
      const recovered = await agent.command({ command: 'read', path });
      assert.equal(recovered.ok, true);
      assert.match(recovered.html_redacted, /NEW_BYTES/);
      assert.doesNotMatch(recovered.html_redacted, /OLD_BYTES/);
    });
  });

  for (const failure of ['stale context', 'createIsolatedWorld', 'Fetch.getResponseBody', 'non-base64 body', 'malformed base64']) {
    await t.test(`${failure} fails closed without a main-world fallback`, async () => {
      fixture.script = '';
      fixture.set('/build/301/overview', buildHTML(301));
      fixture.set('/build/302/overview', buildHTML(302));
      await withRuntime(fixture, async ({ runtime, agent, tape, fallback }) => {
        assert.equal((await agent.command({ command: 'read', path: '/build/301/overview' })).ok, true);
        const previousId = tape.worlds.at(-1).id;
        const before = tape.evaluations.length;
        let bodyCalls = 0;
        const root = runtime.guards.root;
        const send = root.send;
        if (failure === 'stale context') tape.staleId = previousId;
        if (failure === 'createIsolatedWorld') tape.failWorld = true;
        const bodyFailure = !['stale context', 'createIsolatedWorld'].includes(failure);
        if (bodyFailure) root.send = async (method, params) => {
          if (method !== 'Fetch.getResponseBody') return send.call(root, method, params);
          bodyCalls++;
          if (failure === 'Fetch.getResponseBody') throw new Error(`synthetic capture unavailable: ${secret}`);
          const result = await send.call(root, method, params);
          return failure === 'non-base64 body'
            ? { base64Encoded: false, body: Buffer.from(result.body, 'base64').toString('utf8') }
            : { base64Encoded: true, body: 'not-base64!' };
        };
        try {
          const result = await agent.command({ command: 'read', path: '/build/302/overview' });
          assert.deepEqual(result, { ok: false, error: 'QB_TRUSTED_CONTEXT_UNAVAILABLE' });
          assert.deepEqual(fallback, []);
          if (failure === 'stale context') {
            assert.notEqual(tape.worlds.at(-1).id, previousId);
            assert.equal(tape.evaluations.at(-1).contextId, previousId);
            assert.equal(tape.evaluations.at(-1).failed, true, 'stale CDP context unexpectedly remained usable');
          } else assert.equal(tape.evaluations.length, before, 'reader ran after prerequisite failed');
          if (bodyFailure) {
            assert.equal(bodyCalls, 1);
            assert.equal(agent.rawRead, null);
          }
          assert.equal(runtime.policy.readNavigation, null);
        } finally {
          root.send = send;
          tape.staleId = null;
          tape.failWorld = false;
        }
        assert.equal((await agent.command({ command: 'read', path: '/build/302/overview' })).ok, true);
      });
    });
  }

  await t.test('strict response charset decoding uses headers, default UTF-8 and fatal errors', async st => {
    fixture.script = '';
    await withRuntime(fixture, async ({ runtime, agent, tape, capture }) => {
      const cases = [
        ['latin1', 'text/html; charset=ISO-8859-1', Buffer.from('caf\u00e9', 'latin1'), 'caf\u00e9'],
        ['quoted charset', 'text/html; charset="ISO-8859-1"', Buffer.from('caf\u00e9', 'latin1'), 'caf\u00e9'],
        ['no charset', 'text/html', Buffer.from('UTF-8 \u96ea'), 'UTF-8 \u96ea'],
        ['literal replacement character', 'text/html; charset=UTF-8', Buffer.from('\ufffd'), '\ufffd'],
        ['invalid UTF-8', 'text/html; charset=UTF-8', Buffer.from([0xc3, 0x28]), null],
        ['invalid default UTF-8', 'text/html', Buffer.from([0xff]), null],
        ['unsupported charset', 'text/html; charset=c2c-unsupported', Buffer.from('ascii'), null],
      ];
      for (const [index, [name, contentType, bytes, expected]] of cases.entries()) {
        await st.test(`${name}: raw decoder`, async () => {
          const response = { headerValue: async () => contentType,
            body: async () => { assert.fail('raw decoder used Playwright body'); } };
          if (expected === null) await assert.rejects(responseText(response, bytes), { code: 'QB_TRUSTED_CONTEXT_UNAVAILABLE' });
          else assert.equal(await responseText(response, bytes), expected);
        });
        await st.test(`${name}: HTTPS navigation`, async () => {
          const id = 400 + index;
          const path = `/build/${id}/overview`;
          const html = buildHTML(id, { extra: '<p id="decoded">BYTE_MARKER</p>', script: false });
          const [prefix, suffix] = html.split('BYTE_MARKER');
          const raw = Buffer.concat([Buffer.from(prefix), bytes, Buffer.from(suffix)]);
          fixture.set(path, raw, contentType);
          const before = tape.evaluations.length;
          const captured = capture.calls.length;
          const result = await agent.command({ command: 'read', path });
          assert.equal(capture.calls.length, captured + 1);
          assert.equal(capture.calls.at(-1).base64, true);
          assert.deepEqual(capture.calls.at(-1).bytes, raw, 'Fetch body differs from exact server bytes');
          assert.equal(runtime.policy.readNavigation, null);
          assert.equal(capture.calls.at(-1).navigation.body, null, 'raw buffer remained in the navigation slot');
          if (expected === null) {
            assert.equal(result.ok, false, 'invalid encoding was accepted');
            assert.deepEqual(result, { ok: false, error: 'QB_TRUSTED_CONTEXT_UNAVAILABLE' });
            assert.equal(tape.evaluations.length, before, 'invalid bytes reached the DOM parser');
          } else {
            assert.equal(result.ok, true);
            assert.equal(result.html_redacted.match(/<p id="decoded">([^<]*)<\/p>/)?.[1], expected);
            assert.ok(agent.rawRead.includes(expected));
          }
        });
      }
    });
    await assert.rejects(responseText(null, Buffer.alloc(0)), { code: 'QB_TRUSTED_CONTEXT_UNAVAILABLE' });
    await assert.rejects(responseText({ headerValue: async () => 'text/html' }),
      { code: 'QB_TRUSTED_CONTEXT_UNAVAILABLE' });
    await assert.rejects(responseText({ headerValue: async () => { throw new Error('missing headers'); } }, Buffer.alloc(0)),
      { code: 'QB_TRUSTED_CONTEXT_UNAVAILABLE' });
  });

  for (const kind of ['read', 'form']) {
    await t.test(`${kind} mismatch: shared secret context, revoked registrations and inert no-store image`, async () => {
      const input = diagnosticFixture(fixture, kind);
      const imageStart = fixture.received.filter(request => request.path === imagePath).length;
      await withRuntime(fixture, async ({ runtime, agent }) => {
        const seeded = seedAtMismatch(agent, kind);
        const allow = runtime.policy.allow.bind(runtime.policy);
        const allowed = [];
        runtime.policy.allow = (metadata, requestId) => {
          const result = allow(metadata, requestId);
          if (result && metadata.response_status === null) allowed.push(metadata.path);
          return result;
        };
        const diagnostic = agent.diagnostic.bind(agent);
        let inspected = false;
        let inspectionError;
        agent.diagnostic = async (...args) => {
          try {
            assert.equal(seeded.count, 1, 'test did not seed registrations before failure');
            assertRevoked(runtime.policy);
            assert.equal(runtime.policy.phase, 'read');
            assert.equal(fixture.received.filter(request => request.path === imagePath).length, imageStart + 1,
              'no-store image was not loaded by the live document');
            const requests = fixture.received.length;
            const permitted = allowed.length;
            const trace = runtime.trace.length;
            const result = await diagnostic(...args);
            assert.deepEqual(await diagnostic(...args), result, 'repeated diagnostics changed evidence');
            await wait(150);
            assert.equal(fixture.received.length, requests, 'diagnostic caused a server request');
            assert.equal(allowed.length, permitted, 'diagnostic obtained a new request allowance');
            assert.ok(runtime.trace.slice(trace).every(row => row.action === 'IDENTITY_OUTSIDE_REGISTERED'),
              'diagnostic attempted browser activity');
            assertRevoked(runtime.policy);
            inspected = true;
            return result;
          } catch (error) { inspectionError = error; throw error; }
        };
        const result = await agent.command(input);
        if (inspectionError) throw inspectionError;
        assert.equal(inspected, true);
        assert.equal(result.ok, false);
        assert.equal(result.error, kind === 'read' ? 'QB_READ_ID_MISMATCH' : 'QB_FORM_CHANGED');
        assert.deepEqual(Object.keys(result).sort(), ['diagnostic', 'error', 'ok']);
        assert.deepEqual(Object.keys(result.diagnostic).sort(), ['facts', 'html_redacted']);
        assertScrubbed(result);
        assertScrubbed(runtime.trace);
        const { facts, html_redacted: html } = result.diagnostic;
        assert.match(html, /&lt;REDACTED&gt;/);
        assert.match(html, /c2c-no-store\.png/);
        assert.ok(JSON.stringify(facts).includes('&lt;REDACTED&gt;'), 'structured facts were not scrubbed');
        assert.equal(facts.first_failed_check, kind === 'read' ? 'build_id' : 'labels');
        if (kind === 'read') {
          assert.equal(facts.summary_count, 1);
          assert.ok(facts.labels.some(label => label.includes('Build (id:808)')));
        } else {
          assert.deepEqual(facts.extra, ['UNKNOWN-&lt;REDACTED&gt;']);
          assert.match(facts.rows.at(-1).controls[0].callback, /jsessionid=&lt;REDACTED&gt;/);
          assert.equal(facts.rows.at(-1).controls[0].callback_valid, false);
          assert.equal(agent.state, 'invalid');
        }
        assertRevoked(runtime.policy);
        assert.equal(runtime.policy.phase, 'idle');
      });
    });

    for (const stage of ['snapshot', 'after redaction']) {
      await t.test(`${kind} diagnostic failure ${stage} returns no partial evidence`, async () => {
        const input = diagnosticFixture(fixture, kind);
        await withRuntime(fixture, async ({ runtime, agent }) => {
          seedAtMismatch(agent, kind);
          const diagnostic = agent.diagnostic.bind(agent);
          let injected = false;
          agent.diagnostic = async (...args) => {
            assertRevoked(runtime.policy);
            const target = stage === 'snapshot' ? agent.trusted : agent;
            const key = stage === 'snapshot' ? 'run' : 'passive';
            const original = target[key];
            target[key] = async function (...args) {
              if (stage === 'after redaction') {
                const partial = await original.apply(this, args);
                assert.equal(typeof partial.html_redacted, 'string');
                assert.ok(partial.facts);
              }
              injected = true;
              throw new Error(`synthetic diagnostic failure: ${secret}`);
            };
            try { return await diagnostic(...args); } finally { target[key] = original; }
          };
          const result = await agent.command(input);
          assert.equal(injected, true);
          assert.deepEqual(result, { ok: false,
            error: kind === 'read' ? 'QB_READ_ID_MISMATCH' : 'QB_FORM_CHANGED', diagnostic_failed: true });
          assertScrubbed(result);
          assertRevoked(runtime.policy);
        });
      });
    }
  }

  t.diagnostic(`network=loopback-only; server requests=${fixture.received.length}; synthetic responses only`);
  if (process.env.P5Q_C5A_EVIDENCE) {
    assertScrubbed(fixture.received);
    await mkdir(process.env.P5Q_C5A_EVIDENCE, { recursive: true });
    await writeFile(`${process.env.P5Q_C5A_EVIDENCE}/existing-trusted-requests.json`, JSON.stringify(fixture.received, null, 2));
  }
});
