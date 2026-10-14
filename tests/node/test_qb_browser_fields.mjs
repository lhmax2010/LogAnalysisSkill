import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash, X509Certificate } from 'node:crypto';
import { existsSync } from 'node:fs';
import { mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { createServer } from 'node:https';
import test from 'node:test';
import { pathToFileURL } from 'node:url';
import {
  Agent, FIELDS, ORIGIN, adaptProtocol, createRuntime, fingerprint, startupSelfTest,
} from '../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';

// Run like the other browser tests: NODE this-file PLAYWRIGHT/index.mjs CHROMIUM.
// Only synthetic HTML and real loopback HTTPS are used, never archived responses.
const [playwright, chromium] = process.argv.slice(2);
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const PROJECT = { overview_id: 1917, configuration_path: 'root/LOCAL/FIELDS', project_name: 'LOCAL-FIELDS' };
const ARCH = 'standard-armv7l:aarch64:x86_64';
const PALETTES = new Set(['CHILD_CONFIGURATIONS', 'TARGET_IMAGE']);
const TEXTS = ['Build Package List', 'Add Package List', 'Remove Package List', 'BUILD NOTES'];
const SELECTS = FIELDS.slice(0, 5);
const EXPECTED = {
  BUILD_TYPE: 'Partial', REPO_TYPE: 'ALL', BUILD_REFERENCE: 'Ref. Snapshot',
  SNAPSHOT_NUM: 'snapshot-42', PROJECT_BRANCH: 'tizen_base',
  'Immediate Stop With Error': true, CHILD_CONFIGURATIONS: [ARCH],
  'Build Package List': 'synthetic-package@0123456789abcdef',
  'Add Package List': '', 'Remove Package List': '', TARGET_IMAGE: [],
  'BUILD NOTES': 'clang-fix-campaign request=offline-fields',
};
const SELF_TEST_ERROR = '\u6d4f\u89c8\u5668\u6846\u67b6\u7684\u8bbe\u503c\u884c\u4e3a\u4e0e\u8bbe\u8ba1\u4e0d\u7b26,\u5347\u7ea7 Playwright \u540e\u987b\u91cd\u65b0\u9a8c\u8bc1\n';
const escapeHTML = value => String(value).replace(/[&<>"']/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
})[char]);
const hex = value => Buffer.from(value).toString('hex');
const controlId = name => `field-${FIELDS.indexOf(name)}`;
const callbackPath = (version, index) => `/wicket/page?${version}-1.IBehaviorListener.0-form-field-${index}`;

function formHTML({ equal = false, freeze = false, checked = true, extra = null, duplicate = false } = {}) {
  const wanted = { ...EXPECTED, 'Immediate Stop With Error': checked };
  const rows = FIELDS.map((name, index) => {
    const id = controlId(name);
    const onchange = escapeHTML(`wicketAjaxPost('page?41-1.IBehaviorListener.0-form-field-${index}', this)`);
    let controls;
    if (PALETTES.has(name)) {
      const selected = equal ? wanted[name] : name === 'CHILD_CONFIGURATIONS' ? [] : ['synthetic-image'];
      const choices = name === 'CHILD_CONFIGURATIONS' && !equal ? [ARCH] : [];
      const options = values => values.map(text => `<option value="${hex(text)}">${escapeHTML(text)}</option>`).join('');
      controls = `<input id="${id}" name="fixture:${id}:recorder" type="hidden" value="${selected.map(hex).join('')}" onchange="${onchange}">
        <select name="fixture:${id}:choices" multiple>${options(choices)}</select>
        <select name="fixture:${id}:selection" multiple>${options(selected)}</select>
        ${equal ? '' : `<button class="add" type="button" onclick="move(this, 'choices', 'selection')">Add</button>
        <button class="remove" type="button" onclick="move(this, 'selection', 'choices')">Remove</button>`}`;
    } else if (SELECTS.includes(name)) {
      const other = name === 'SNAPSHOT_NUM' ? 'snapshot-41' : `other-${index}`;
      const targetSelected = equal || name === 'SNAPSHOT_NUM' && freeze;
      controls = `<select id="${id}" name="fixture:${id}:input" onchange="${onchange}">
        <option value="opaque-${index}-old" ${targetSelected ? '' : 'selected'}>${other}</option>
        <option value="opaque-${index}-wanted" ${targetSelected ? 'selected' : ''}> \n${escapeHTML(wanted[name])}\t </option>
        ${duplicate && name === 'BUILD_TYPE' ? `<option value="duplicate"> ${escapeHTML(wanted[name])} </option>` : ''}</select>`;
    } else if (name === 'Immediate Stop With Error') {
      controls = `<input id="${id}" name="fixture:${id}:input" type="checkbox" ${(equal ? checked : !checked) ? 'checked' : ''} onchange="${onchange}">`;
    } else {
      controls = `<textarea id="${id}" name="fixture:${id}:input" onchange="${onchange}">${escapeHTML(equal ? wanted[name] : `old-${index}`)}</textarea>`;
    }
    return `<tr data-field="${escapeHTML(name)}"><td><span class="form-label">${escapeHTML(name)}</span></td><td class="value">${controls}</td></tr>`;
  }).join('');
  return `<!doctype html><html><head><title>LOCAL synthetic fields</title><link rel="icon" href="data:,"></head>
    <body><h1>Specify Build Options</h1><form method="POST" action="page?41-1.IFormSubmitListener-form"><table>
      <tr><td><span class="form-label">PROJECT_NAME</span></td><td class="value"><div class="property-viewer"> \n${PROJECT.project_name}<span></span>\t </div></td></tr>
      ${rows}</table><button type="submit">Ok</button></form><script>
      window.fixture = { events: [], attempts: [], settled: [], pending: [], moves: [], submitClicks: 0 };
      document.querySelector('button[type=submit]').addEventListener('click', () => fixture.submitClicks++);
      for (const type of ['change', 'focus', 'blur']) document.addEventListener(type, event => {
        const row = event.target.closest('tr[data-field]');
        if (row) fixture.events.push({ type, field: row.dataset.field, id: event.target.id,
          role: event.target.name.split(':').pop(), trusted: event.isTrusted });
      }, true);
      window.wicketAjaxPost = function(url, element) {
        const field = element.closest('tr').dataset.field;
        fixture.attempts.push({ field, url });
        const pending = fetch(url, { method: 'POST', body: new URLSearchParams({ field, value: element.value }) })
          .then(response => response.json()).then(reply => {
            document.querySelector('form').setAttribute('action', 'page?' + reply.version + '-1.IFormSubmitListener-form');
            for (const [index, row] of [...document.querySelectorAll('tr[data-field]')].entries()) {
              const control = row.querySelector('[onchange]');
              control.setAttribute('onchange', "wicketAjaxPost('page?" + reply.version + "-1.IBehaviorListener.0-form-field-" + index + "', this)");
            }
            fixture.settled.push({ field, ok: true });
          }).catch(() => fixture.settled.push({ field, ok: false }));
        fixture.pending.push(pending);
        if (${JSON.stringify(extra)} === field && !fixture.extraSent) {
          fixture.extraSent = true;
          queueMicrotask(() => element.dispatchEvent(new Event('change', { bubbles: true })));
        }
      };
      window.move = function(button, from, to) {
        const box = button.closest('td');
        const source = box.querySelector('select[name$=":' + from + '"]');
        const destination = box.querySelector('select[name$=":' + to + '"]');
        for (const option of [...source.selectedOptions]) { option.selected = false; destination.append(option); }
        const recorder = box.querySelector('input[type=hidden]');
        recorder.value = [...box.querySelector('select[name$=":selection"]').options].map(option => option.value).join('');
        fixture.moves.push({ field: button.closest('tr').dataset.field, from, to, recorder: recorder.value });
        recorder.dispatchEvent(new Event('change', { bubbles: true }));
      };
      </script></body></html>`;
}

async function localServer() {
  const directory = await mkdtemp('/dev/shm/p5q-c2c-fields-');
  let server;
  try {
    execFileSync('openssl', ['req', '-x509', '-newkey', 'rsa:2048', '-nodes',
      '-keyout', `${directory}/key.pem`, '-out', `${directory}/cert.pem`, '-days', '1',
      '-subj', '/CN=quickbuild.tizen.org', '-addext', 'subjectAltName=DNS:quickbuild.tizen.org'], { stdio: 'ignore' });
    const cert = await readFile(`${directory}/cert.pem`);
    const key = await readFile(`${directory}/key.pem`);
    const spki = createHash('sha256').update(new X509Certificate(cert).publicKey.export({ type: 'spki', format: 'der' })).digest('base64');
    const fixture = { received: [], errors: [], options: {}, version: 41 };
    server = createServer({ cert, key }, (request, response) => {
      const row = { method: request.method, path: request.url, host: request.headers.host, at: Date.now() };
      fixture.received.push(row);
      void (async () => {
        let body = '';
        for await (const chunk of request) body += chunk;
        row.body = body;
        response.setHeader('Cache-Control', 'no-store');
        if (request.method === 'GET' && request.url === `/overview/${PROJECT.overview_id}`) {
          response.setHeader('Content-Type', 'text/html; charset=utf-8');
          response.end(`<!doctype html><title>QuickBuild - ${PROJECT.configuration_path}</title><link rel="icon" href="data:,">
            <button title="Run the configuration" onclick="var win = this.ownerDocument.defaultView || this.ownerDocument.parentWindow; if (win == window) { window.location.href='../wicket/page?41-1.ILinkListener-run'; } ;return false">Run</button>`);
        } else if (request.method === 'GET' && request.url === '/wicket/page?41-1.ILinkListener-run') {
          response.setHeader('Content-Type', 'text/html; charset=utf-8');
          response.end(formHTML(fixture.options));
        } else if (request.method === 'POST' && /^\/wicket\/page\?\d+-1\.IBehaviorListener\.0-form-field-\d+$/.test(request.url)) {
          await wait(75);
          response.setHeader('Content-Type', 'application/json');
          row.respondedAt = Date.now();
          response.end(JSON.stringify({ version: ++fixture.version }));
        } else {
          fixture.errors.push(`unexpected request: ${request.method} ${request.url}`);
          response.writeHead(404); response.end();
        }
      })().catch(error => { fixture.errors.push(error.message); response.destroy(); });
    });
    await new Promise((resolve, reject) => { server.once('error', reject); server.listen(0, '127.0.0.1', resolve); });
    return Object.assign(fixture, {
      overrides: { launchArgs: ['--no-proxy-server',
        `--host-resolver-rules=MAP quickbuild.tizen.org 127.0.0.1:${server.address().port}, EXCLUDE 127.0.0.1, MAP * ~NOTFOUND`,
        `--ignore-certificate-errors-spki-list=${spki}`] },
      async close() {
        server.closeAllConnections();
        await new Promise(resolve => server.close(resolve));
        await rm(directory, { recursive: true, force: true });
      },
    });
  } catch (error) {
    server?.close();
    await rm(directory, { recursive: true, force: true });
    throw error;
  }
}

function observe(runtime, agent, { legacyText = false } = {}) {
  const windows = [];
  const requests = [];
  const operations = [];
  const begin = runtime.policy.beginField.bind(runtime.policy);
  const end = runtime.policy.endField.bind(runtime.policy);
  runtime.policy.beginField = url => {
    begin(url);
    if (windows.length) windows.at(-1).endedAt = Date.now();
    windows.push({ name: FIELDS[windows.length], url, counts: runtime.policy.fieldWindow, beganAt: Date.now() });
  };
  runtime.policy.endField = () => {
    if (windows.length) windows.at(-1).endedAt ??= Date.now();
    return end();
  };
  let activity = runtime.policy.lastActivity;
  runtime.guards.root.on('Fetch.requestPaused', event => {
    const { metadata: m, requestId } = adaptProtocol(event);
    requests.push({ ...m, window: windows.length - 1, at: Date.now(),
      allowed: m.response_status === null ? runtime.policy.active.has(requestId) : null,
      previousActivity: activity, activity: runtime.policy.lastActivity });
    activity = runtime.policy.lastActivity;
  });
  const fieldRow = agent.fieldRow.bind(agent);
  const methods = new Set(['selectOption', 'check', 'uncheck', 'fill', 'blur', 'dispatchEvent', 'click']);
  const chain = new Set(['locator', 'filter', 'first', 'last', 'nth']);
  const wrap = (locator, name) => new Proxy(locator, {
    get(target, key) {
      const value = Reflect.get(target, key);
      if (typeof value !== 'function') return value;
      return (...args) => {
        if (chain.has(key)) return wrap(value.apply(target, args), name);
        if (methods.has(key)) operations.push({ name, method: key, args });
        // Reproduce the old text bug without changing policy, clocks, or callbacks.
        if (legacyText && name === 'Build Package List' && key === 'blur') return target.dispatchEvent('change');
        return value.apply(target, args);
      };
    },
  });
  agent.fieldRow = name => wrap(fieldRow(name), name);
  return { windows, requests, operations };
}

async function controls(page) {
  return page.evaluate(() => [...document.querySelectorAll('tr[data-field]')].map(row => ({
    field: row.dataset.field,
    controls: [...row.querySelectorAll('input,select,textarea')].map(element => ({
      name: element.name, value: element.value, checked: element.checked ?? null,
      options: element.tagName === 'SELECT' ? [...element.options].map(option => ({
        text: option.textContent, value: option.value, selected: option.selected,
      })) : [],
    })),
  })));
}

async function withForm(fixture, options, action) {
  fixture.options = options;
  fixture.version = 41;
  const offset = fixture.received.length;
  const runtime = await createRuntime(playwright, chromium, fixture.overrides);
  try {
    assert.equal(fixture.received.length, offset, 'startup must not contact the HTTPS server');
    const agent = new Agent(runtime);
    // Authentication is outside this suite; all navigation/fill/submit commands are real.
    agent.state = 'ready';
    agent.projects.set(PROJECT.overview_id, PROJECT);
    runtime.policy.overviewIds.add(String(PROJECT.overview_id));
    const observed = observe(runtime, agent, options);
    const pageErrors = [];
    runtime.page.on('pageerror', error => pageErrors.push(error.message));
    assert.deepEqual(await agent.command({ command: 'open_form', overview_id: PROJECT.overview_id }), { ok: true, released: false });
    assert.deepEqual(fixture.received.slice(offset).map(row => [row.method, row.path]), [
      ['GET', `/overview/${PROJECT.overview_id}`], ['GET', '/wicket/page?41-1.ILinkListener-run'],
    ]);
    const fields = { ...EXPECTED, 'Immediate Stop With Error': options.checked ?? true,
      SNAPSHOT_NUM: options.freeze ? '@freeze' : EXPECTED.SNAPSHOT_NUM };
    await action({ runtime, agent, fields, ...observed, received: () => fixture.received.slice(offset) });
    assert.deepEqual(pageErrors, [], 'synthetic form script must work');
    assert.equal(runtime.failure, null);
    assert.equal(runtime.policy.released, false);
    assert.equal(await runtime.page.evaluate(() => fixture.submitClicks), 0);
    assert.ok(fixture.received.slice(offset).every(row => row.host === 'quickbuild.tizen.org'));
    assert.equal(fixture.received.slice(offset).some(row => row.path.includes('IFormSubmitListener')), false);
    assert.deepEqual(fixture.errors, []);
  } finally {
    await runtime.close();
    assert.equal(runtime.browser.isConnected(), false);
    assert.equal(existsSync(runtime.profile), false);
  }
}

function assertFullFill(result, fields, observations) {
  assert.equal(result.ok, true, JSON.stringify({ error: result.error, field: result.field }));
  const expected = Object.fromEntries(FIELDS.map(name => [
    `${name}/${PALETTES.has(name) ? 'selection' : 'value'}`,
    fields[name] === '@freeze' ? EXPECTED.SNAPSHOT_NUM : fields[name],
  ]));
  assert.deepEqual(result.readback, expected);
  assert.equal(result.fingerprint, fingerprint(expected));
  assert.equal(result.snapshot_option_count, 2);
  assert.equal(result.released, false);
  assert.equal(observations.agent.state, 'filled');
  assert.equal(observations.runtime.policy.fieldWindow, null);
  assert.equal(observations.windows.length, 12);
  const posts = observations.received().filter(row => row.method === 'POST');
  assert.equal(posts.length, 12);
  for (const [index, window] of observations.windows.entries()) {
    assert.equal(window.name, FIELDS[index]);
    assert.deepEqual(window.counts, { allowed: 1, denied: 0 }, window.name);
    assert.equal(window.url, ORIGIN + callbackPath(41 + index, index), 'callback must be reread after the previous response');
    assert.equal(posts[index].path, callbackPath(41 + index, index));
    assert.equal(new URLSearchParams(posts[index].body).get('field'), window.name);
    assert.ok(window.endedAt - posts[index].respondedAt >= 1000, `${window.name}: must wait a full second after the response`);
    const callbacks = observations.requests.filter(row => row.window === index && row.method === 'POST' && row.response_status === null);
    assert.equal(callbacks.length, 1, window.name);
    assert.equal(callbacks[0].allowed, true, window.name);
  }
}

async function assertInvalid(observations, result) {
  const { agent, runtime, received } = observations;
  assert.equal(result.ok, false);
  assert.equal(result.error, 'QB_FORM_CHANGED');
  assert.equal(agent.state, 'invalid');
  assert.equal(runtime.policy.fieldUrl, null);
  assert.equal(runtime.policy.fieldWindow, null);
  assert.equal(runtime.policy.runUrl, null);
  assert.equal(runtime.policy.submitUrl, null);
  assert.equal(runtime.policy.released, false);
  const before = received().length;
  assert.deepEqual(await agent.command({ command: 'submit', fingerprint: '0'.repeat(64) }), { ok: false, error: 'AGENT_PHASE' });
  assert.equal(received().length, before, 'invalid forms must not issue a submit request');
  assert.equal(await runtime.page.evaluate(() => fixture.submitClicks), 0);
}

async function injectAtReadback(observations, field) {
  const { agent, runtime, windows } = observations;
  const snapshot = agent.snapshot.bind(agent);
  let injected = false;
  agent.snapshot = async () => {
    // The next snapshot is either the next field's pre-registration read or
    // the final readback. Hold that read while a real browser timer fires.
    if (!injected && windows.length === FIELDS.indexOf(field) + 1) {
      injected = true;
      await runtime.page.evaluate(async id => {
        await new Promise(resolve => setTimeout(resolve, 25));
        document.getElementById(id).dispatchEvent(new Event('change', { bubbles: true }));
        await Promise.all(fixture.pending);
      }, controlId(field));
    }
    return snapshot();
  };
  return () => assert.equal(injected, true, 'late event injection must execute');
}

test('C2c frozen v1.5 fields and startup self-test, loopback HTTPS only', { timeout: 240000 }, async t => {
  assert.ok(playwright && chromium, 'supply the same Playwright module and Chromium paths as the other browser tests');
  const version = JSON.parse(await readFile(new URL('./package.json', pathToFileURL(playwright)), 'utf8')).version;
  const fixture = await localServer();
  try {
    await t.test('startup self-test: real counts, version trace, disposable page and zero server requests', async () => {
      const offset = fixture.received.length;
      const runtime = await createRuntime(playwright, chromium, fixture.overrides);
      try {
        const expected = { action: 'FRAMEWORK_SELF_TEST', playwright_version: version, counts: [1, 1, 1] };
        assert.deepEqual(runtime.trace.filter(row => row.action === 'FRAMEWORK_SELF_TEST'), [expected]);
        assert.equal(runtime.page.url(), 'about:blank');
        assert.equal(runtime.context.pages().length, 1);
        assert.equal(await runtime.page.locator('#select,#check,#text').count(), 0, 'probe DOM must not survive into the real runtime');
        await startupSelfTest(runtime, version);
        assert.deepEqual(runtime.trace.filter(row => row.action === 'FRAMEWORK_SELF_TEST'), [expected, expected]);
        assert.deepEqual(await runtime.page.evaluate(() => [...document.querySelectorAll('#select,#check,#text')]
          .map(element => Number(element.dataset.changes))), [1, 1, 1]);
        assert.equal(runtime.failure, null);
        assert.equal(runtime.browser.isConnected(), true);
        assert.equal(fixture.received.length, offset);
      } finally { await runtime.close(); }
      assert.equal(existsSync(runtime.profile), false);
    });

    for (const count of [0, 2]) await t.test(`startup self-test: count ${count} closes browser with fixed stderr`, async () => {
      const offset = fixture.received.length;
      const runtime = await createRuntime(playwright, chromium, fixture.overrides);
      const write = process.stderr.write;
      const chunks = [];
      try {
        const before = runtime.trace.length;
        process.stderr.write = function (chunk, encoding, callback) {
          chunks.push(Buffer.isBuffer(chunk) ? chunk.toString('utf8') : String(chunk));
          const done = typeof encoding === 'function' ? encoding : callback;
          if (done) queueMicrotask(done);
          return true;
        };
        await assert.rejects(startupSelfTest(runtime, version, count), { code: 'QB_BROWSER_UNAVAILABLE' });
        assert.equal(chunks.join(''), SELF_TEST_ERROR);
        assert.equal(runtime.trace.slice(before).some(row => row.action === 'FRAMEWORK_SELF_TEST'), false);
        assert.equal(runtime.browser.isConnected(), false);
        assert.equal(runtime.page.isClosed(), true);
        assert.equal(existsSync(runtime.profile), false);
        assert.equal(fixture.received.length, offset);
      } finally { process.stderr.write = write; await runtime.close(); }
    });

    await t.test('open_form rejects duplicate option text with a real passive diagnostic', async () => {
      fixture.options = { duplicate: true };
      const offset = fixture.received.length;
      const runtime = await createRuntime(playwright, chromium, fixture.overrides);
      try {
        const agent = new Agent(runtime); agent.state = 'ready';
        agent.projects.set(PROJECT.overview_id, PROJECT);
        runtime.policy.overviewIds.add(String(PROJECT.overview_id));
        const reply = await agent.command({ command: 'open_form', overview_id: PROJECT.overview_id });
        assert.equal(reply.error, 'QB_FORM_CHANGED');
        assert.equal(reply.diagnostic.facts.first_failed_check, 'duplicate_option_text');
        assert.ok(reply.diagnostic.html_redacted.includes('value="duplicate"'));
        assert.equal('snapshot_state' in reply, false);
        assert.equal(runtime.policy.released, false);
        assert.equal(fixture.received.slice(offset).filter(row => row.method === 'POST').length, 0);
      } finally { await runtime.close(); }
    });

    for (const [label, wanted] of [['SNAPSHOT_NUM', '@freeze'], ['SNAPSHOT_NUM', 'snapshot-42'], ['BUILD_TYPE', 'Full']]) {
      await t.test(`duplicate ordinary options produce passive diagnostic: ${label}/${wanted}`, async () => {
        await withForm(fixture, { equal: true }, async observations => {
          const { runtime, agent, fields } = observations;
          await runtime.page.evaluate(name => {
            const row = [...document.querySelectorAll('tr[data-field]')].find(r => r.dataset.field === name);
            const select = row.querySelector('select');
            const option = select.selectedOptions[0].cloneNode(true);
            option.value = 'duplicate-value'; option.selected = false;
            option.textContent = '  ' + select.selectedOptions[0].textContent + '  ';
            select.append(option);
          }, label);
          const result = await agent.command({ command: 'fill', fields: { ...fields, [label]: wanted } });
          assert.equal(result.error, 'QB_FORM_CHANGED');
          assert.equal(result.diagnostic.facts.first_failed_check, 'duplicate_option_text');
          assert.ok(result.diagnostic.html_redacted.includes('duplicate-value'));
          assert.equal('snapshot_state' in result, false);
          assert.equal(agent.state, 'invalid'); assert.equal(runtime.policy.released, false);
          assert.equal(observations.received().filter(row => row.method === 'POST').length, 0);
          assert.equal((await agent.command({ command: 'submit' })).error, 'AGENT_PHASE');
        });
      });
    }

    await t.test('all 12 unequal fields: native changes, text blur, palette buttons and new callback versions', async () => {
      await withForm(fixture, {}, async observations => {
        const { agent, runtime, fields, operations } = observations;
        const result = await agent.command({ command: 'fill', fields });
        assertFullFill(result, fields, observations);
        assert.equal(operations.some(row => row.method === 'dispatchEvent'), false, 'unequal fields must not supplement change');
        for (const name of SELECTS) assert.deepEqual(operations.filter(row => row.name === name).map(row => row.method), ['selectOption']);
        assert.deepEqual(operations.filter(row => row.name === 'Immediate Stop With Error').map(row => row.method), ['check']);
        for (const name of TEXTS) assert.deepEqual(operations.filter(row => row.name === name).map(row => row.method), ['fill', 'blur']);
        const events = await runtime.page.evaluate(() => fixture.events);
        for (const name of TEXTS) {
          const changes = events.filter(row => row.type === 'change' && row.field === name);
          assert.equal(changes.length, 1, `${name}: only one native change, including across subsequent focus`);
          assert.equal(changes[0].trusted, true);
          assert.equal(events.filter(row => row.type === 'blur' && row.field === name).length, 1);
        }
        for (const [previous, next] of [['Build Package List', 'Add Package List'], ['Add Package List', 'Remove Package List']]) {
          assert.ok(events.findIndex(row => row.field === previous && row.type === 'blur')
            < events.findIndex(row => row.field === next && row.type === 'focus'));
        }
        assert.deepEqual(await runtime.page.evaluate(() => fixture.moves), [
          { field: 'CHILD_CONFIGURATIONS', from: 'choices', to: 'selection', recorder: hex(ARCH) },
          { field: 'TARGET_IMAGE', from: 'selection', to: 'choices', recorder: '' },
        ]);
      });
    });

    await t.test('all 12 equal fields including @freeze: unchanged bytes and one explicit change each', async () => {
      await withForm(fixture, { equal: true, freeze: true }, async observations => {
        const { agent, runtime, fields, operations } = observations;
        const before = await controls(runtime.page);
        const result = await agent.command({ command: 'fill', fields });
        assertFullFill(result, fields, observations);
        assert.deepEqual(await controls(runtime.page), before, 'value/checked/options/recorder must remain byte-for-byte unchanged');
        assert.deepEqual(operations, FIELDS.map(name => ({ name, method: 'dispatchEvent', args: ['change'] })));
        assert.deepEqual(await runtime.page.evaluate(() => fixture.events.filter(row => row.type === 'change').map(row => row.field)), FIELDS);
        assert.deepEqual(await runtime.page.evaluate(() => fixture.moves), []);
      });
    });

    await t.test('an extra change is denied and invalidates the current field despite only one server POST', async () => {
      await withForm(fixture, { extra: 'BUILD_TYPE' }, async observations => {
        const result = await observations.agent.command({ command: 'fill', fields: observations.fields });
        await assertInvalid(observations, result);
        assert.equal(observations.windows.length, 1);
        assert.deepEqual(observations.windows[0].counts, { allowed: 1, denied: 1 });
        assert.equal(observations.received().filter(row => row.method === 'POST').length, 1);
        assert.equal(observations.requests.filter(row => row.method === 'POST' && row.response_status === null && !row.allowed).length, 1);
      });
    });

    await t.test('text fill plus artificial change without blur: next field focus produces a denied late native callback', async () => {
      await withForm(fixture, { legacyText: true }, async observations => {
        const result = await observations.agent.command({ command: 'fill', fields: observations.fields });
        await assertInvalid(observations, result);
        const previous = observations.windows.find(row => row.name === 'Build Package List');
        const next = observations.windows.find(row => row.name === 'Add Package List');
        assert.deepEqual(previous.counts, { allowed: 1, denied: 0 });
        assert.ok(next, 'must reach the next field focus');
        assert.equal(next.counts.denied, 1);
        const events = await observations.runtime.page.evaluate(() => fixture.events.filter(row => row.field === 'Build Package List' && row.type === 'change'));
        assert.deepEqual(events.map(row => row.trusted), [false, true]);
        assert.equal(observations.received().filter(row => row.method === 'POST' && new URLSearchParams(row.body).get('field') === 'Build Package List').length, 1);
      });
    });

    for (const field of ['Build Package List', 'BUILD NOTES']) await t.test(`delayed change during ${field === 'BUILD NOTES' ? 'final readback' : 'next-field snapshot'} fails`, async () => {
      await withForm(fixture, {}, async observations => {
        const assertInjected = await injectAtReadback(observations, field);
        const result = await observations.agent.command({ command: 'fill', fields: observations.fields });
        assertInjected();
        await assertInvalid(observations, result);
        assert.equal(observations.windows.length, FIELDS.indexOf(field) + 1);
        assert.deepEqual(observations.windows.at(-1).counts, { allowed: 1, denied: 1 });
        assert.equal(observations.received().filter(row => row.method === 'POST').length, observations.windows.length);
      });
    });

    await t.test('swallowed equal-value change: actual 30-second timeout, invalid form and no submit', async () => {
      await withForm(fixture, { equal: true }, async observations => {
        await observations.runtime.page.evaluate(() => {
          const dispatch = EventTarget.prototype.dispatchEvent;
          EventTarget.prototype.dispatchEvent = function (event) {
            if (event.type === 'change') { fixture.swallowed = (fixture.swallowed ?? 0) + 1; return true; }
            return dispatch.call(this, event);
          };
        });
        const started = performance.now();
        const result = await observations.agent.command({ command: 'fill', fields: observations.fields });
        const elapsed = performance.now() - started;
        await assertInvalid(observations, result);
        assert.ok(elapsed >= 30000, `must use the real 30-second field timeout, got ${elapsed}ms`);
        assert.ok(elapsed < 38000, `field timeout did not finish promptly: ${elapsed}ms`);
        assert.equal(await observations.runtime.page.evaluate(() => fixture.swallowed), 1);
        assert.deepEqual(observations.windows.map(row => row.counts), [{ allowed: 0, denied: 0 }]);
        assert.equal(observations.received().filter(row => row.method === 'POST').length, 0);
        t.diagnostic(`swallowed change elapsed ${Math.round(elapsed)}ms; server POSTs=0`);
      });
    });

    await t.test('continuous denied refresh GETs do not extend quiet; uncheck and @freeze still complete', async () => {
      await withForm(fixture, { freeze: true, checked: false }, async observations => {
        const { agent, runtime, fields, operations, requests, windows } = observations;
        await runtime.page.evaluate(() => {
          fixture.refresh = setInterval(() => {
            fetch('page?41-1.IBehaviorListener.0-refresh&action=ajaxRefresh').catch(() => {});
          }, 50);
        });
        const started = performance.now();
        let result;
        try { result = await agent.command({ command: 'fill', fields }); }
        finally { await runtime.page.evaluate(() => clearInterval(fixture.refresh)); }
        const elapsed = performance.now() - started;
        assertFullFill(result, fields, observations);
        assert.ok(elapsed < 20000, `refresh stream extended quiet windows: ${elapsed}ms`);
        assert.deepEqual(operations.filter(row => row.name === 'Immediate Stop With Error').map(row => row.method), ['uncheck']);
        assert.deepEqual(operations.filter(row => row.name === 'SNAPSHOT_NUM').map(row => row.method), ['dispatchEvent']);
        for (const [index, window] of windows.entries()) {
          const refreshes = requests.filter(row => row.window === index && row.query.endsWith('&action=ajaxRefresh'));
          assert.ok(refreshes.length >= 2, `${window.name}: refresh stream must continue during quiet`);
          assert.ok(refreshes.every(row => !row.allowed && row.activity === row.previousActivity), 'denials must not update lastActivity');
          assert.ok(window.endedAt - window.beganAt < 3000, `${window.name}: denied refresh must not extend quiet`);
        }
        assert.equal(observations.received().some(row => row.path.includes('ajaxRefresh')), false);
        t.diagnostic(`refresh stream elapsed ${Math.round(elapsed)}ms; refresh server requests=0`);
      });
    });
  } finally {
    if (process.env.P5Q_C5A_EVIDENCE) {
      await mkdir(process.env.P5Q_C5A_EVIDENCE, { recursive: true });
      await writeFile(`${process.env.P5Q_C5A_EVIDENCE}/existing-fields-requests.json`, JSON.stringify(fixture.received, null, 2));
    }
    await fixture.close();
  }
});
