import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { existsSync, readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import { Agent, TrustedPage, createRuntime, redactDOM, checkRedacted, validateForm,
  buildDOM, verifiedBuildId, callbackURL, ORIGIN, FIELDS } from '../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';

const [playwright, chromium] = process.argv.slice(2);
const archive = new URL('../../docs/clang-fix-campaign/dev_memory/stage15_p1_ef_spike/evidence/web-cookie-02/', import.meta.url);

test('C2B-09 page trim overrides cannot change Node decisions or identity redaction', async t => {
  const runtime = await createRuntime(playwright, chromium, {
    launchArgs: ['--no-proxy-server', '--host-resolver-rules=MAP * ~NOTFOUND'],
  });
  runtime.policy.allow = () => false;
  const agent = new Agent({ ...runtime, page: {
    url: () => `${ORIGIN}/wicket/page?10`,
    evaluate: () => assert.fail('agent reads must use the isolated world'),
  } });
  agent.trusted = new TrustedPage(runtime.context, runtime.page);
  const fixture = readFileSync(new URL('../../docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C2b/live-10/form-unverified.response.html', import.meta.url), 'utf8');
  const nativeTrim = await runtime.page.evaluate(() => {
    globalThis.savedTrim = String.prototype.trim;
    return ' x '.trim();
  });
  assert.equal(nativeTrim, 'x');
  const baseline = {};
  try {
    for (const broken of [false, true]) {
      await runtime.page.evaluate(bad => {
        String.prototype.trim = bad ? function () { return this.replace(/^\s+|\s+$/, ''); } : globalThis.savedTrim;
      }, broken);
      await t.test(`form and options, broken=${broken}`, async () => {
        await runtime.page.evaluate(html => {
          const parsed = new DOMParser().parseFromString(html, 'text/html');
          const form = parsed.querySelector('form[action*="IFormSubmitListener-form"]');
          const base = document.createElement('base'); base.href = 'https://quickbuild.tizen.org/wicket/page?10';
          document.head.replaceChildren(base);
          const heading = document.createElement('h1'); heading.textContent = 'Specify Build Options';
          document.body.replaceChildren(heading, document.importNode(form, true));
          for (const option of document.querySelectorAll('option')) option.textContent = ` \n${option.textContent}\t `;
        }, fixture);
        assert.equal(await runtime.page.evaluate(() => ' x '.trim()), broken ? 'x ' : 'x');
        const form = await agent.snapshot();
        const fields = validateForm(form, 'Tizen-Base-Toolchain');
        assert.equal(form.rows[0].viewers[0], 'Tizen-Base-Toolchain');
        assert.deepEqual(fields.BUILD_TYPE.controls[0].options.map(o => o.text), ['Full', 'Partial']);
        if (broken) assert.deepEqual(form, baseline.form); else baseline.form = form;
      });
      await t.test(`build identity, broken=${broken}`, async () => {
        await runtime.page.setContent(`<a class="nav-link"> \nBuild (id:1193469)\t </a>
          <div class="build-summary"><div class="box-head"> \nSummary\t </div><table>
          <thead><tr><th> \nId\t </th></tr></thead><tbody><tr><td> \n1193469\t </td></tr></tbody></table></div>`);
        assert.equal(await agent.buildId('/build/1193469/overview'), '1193469');
        assert.equal(await agent.buildId('/build/1193469/variables'), '1193469');
      });
      await t.test(`redaction pre/post check, broken=${broken}`, async () => {
        const raw = `<span> \nWelcome! Lin Hao\t </span>
          <table><tr><td> \nTriggered By\t </td><td> \nOther Person\t </td></tr></table>
          <p>Lin Hao; Other Person; Linux-PAM; ILinkListener</p>
          <input type="hidden" name="token" value="synthetic-C2B09-secret"><p>prefix-synthetic-C2B09-secret-suffix</p>`;
        const result = await agent.passive(raw);
        const html = checkRedacted(result.html_redacted);
        assert.doesNotMatch(html, /synthetic-C2B09-secret/);
        assert.match(html, /<p>Lin Hao; Other Person; Linux-PAM; ILinkListener<\/p>/);
        assert.match(html, /Welcome! &lt;USER&gt;/);
        assert.match(html, /<td>&lt;USER&gt;<\/td>/);
        assert.equal(result.outside_identity_count, 2);
        assert.match(html, /&lt;USER&gt;/); assert.match(html, /Linux-PAM; ILinkListener/);
        const root = fileURLToPath(new URL('../../', import.meta.url));
        const venv = `${root}.venv/bin/python`;
        const checked = spawnSync(existsSync(venv) ? venv : 'python3', ['-c',
          'import sys,tempfile; from pathlib import Path; sys.path.insert(0,sys.argv[1]); from ci_triage.qb_redact import PageRedactor; r=PageRedactor(); r.identities.update({"Lin Hao","Other Person"}); raw=sys.stdin.buffer.read(); r.check_bytes(raw); assert r.identity_outside_registered_count == 2;\nwith tempfile.TemporaryDirectory() as d:\n p=Path(d)/"page.html"; p.write_bytes(raw); r.check_written(p)',
          `${root}tizen-ci-triage/scripts`], { input: html, encoding: 'utf8' });
        assert.equal(checked.status, 0, checked.stderr);
        if (broken) assert.equal(html, baseline.redacted); else baseline.redacted = html;
      });
    }
    assert.equal(runtime.page.url(), 'about:blank');
  } finally { await runtime.close(); }
});

test('C2A-04 archived build DOM identity regression only, with all network denied', async t => {
  const runtime = await createRuntime(playwright, chromium, {
    launchArgs: ['--no-proxy-server', '--host-resolver-rules=MAP * ~NOTFOUND'],
  });
  runtime.policy.allow = () => false;
  let path;
  // Archived HTML and DOM mutations test extraction, not original response bytes.
  const trusted = new TrustedPage(runtime.context, runtime.page);
  const identify = async () => verifiedBuildId(await trusted.run(buildDOM), path);
  const load = async (file, requested) => {
    path = requested;
    await runtime.page.setContent(readFileSync(new URL(file, archive), 'utf8'));
  };
  try {
    for (const [file, requested] of [
      ['01.response.txt', '/build/1069540/overview'],
      ['03.response.txt', '/build/1069540/variables'],
      ['04.response.txt', '/build/1069540/step_status'],
    ]) await t.test(`archive ${file} ${requested}`, async () => {
      await load(file, requested);
      assert.equal(await identify(), '1069540');
    });
    for (const spelling of ['Id', 'ID']) await t.test(`navigation spelling ${spelling}`, async () => {
      await load('03.response.txt', '/build/1069540/variables');
      await runtime.page.evaluate(value => {
        document.querySelector('.tab-BuildPage .nav-link span').textContent = `Build (${value}:1069540)`;
      }, spelling);
      assert.equal(await identify(), '1069540');
    });
    await t.test('Summary Id resolved by column, not fixed position', async () => {
      await load('01.response.txt', '/build/1069540/overview');
      await runtime.page.evaluate(() => {
        const table = document.querySelector('.build-summary table');
        for (const row of [table.tHead.rows[0], table.tBodies[0].rows[0]]) row.append(row.cells[0]);
      });
      assert.equal(await identify(), '1069540');
    });
    for (const mutation of [
      'duplicate-nav', 'missing-nav', 'wrong-nav', 'missing-summary', 'duplicate-summary',
      'missing-id-column', 'duplicate-id-column', 'different-summary-id', 'missing-first-row',
    ]) await t.test(`reject ${mutation}`, async () => {
      await load('01.response.txt', '/build/1069540/overview');
      await runtime.page.evaluate(kind => {
        const nav = document.querySelector('.tab-BuildPage .nav-link');
        const summary = document.querySelector('.build-summary');
        const id = summary.querySelector('thead th');
        if (kind === 'duplicate-nav') nav.after(nav.cloneNode(true));
        if (kind === 'missing-nav') nav.remove();
        if (kind === 'wrong-nav') nav.textContent = 'Build (id:1069532)';
        if (kind === 'missing-summary') summary.remove();
        if (kind === 'duplicate-summary') summary.after(summary.cloneNode(true));
        if (kind === 'missing-id-column') id.textContent = 'Other';
        if (kind === 'duplicate-id-column') id.after(id.cloneNode(true));
        if (kind === 'different-summary-id') summary.querySelector('tbody td').textContent = '1069532';
        if (kind === 'missing-first-row') summary.querySelector('tbody tr').remove();
        document.title = 'Build #1069540'; // A matching title cannot rescue invalid sources.
      }, mutation);
      assert.equal(await identify(), null);
    });
    await t.test('both overview sources agree but differ from requested id', async () => {
      await load('01.response.txt', '/build/1069532/overview');
      assert.equal(await identify(), '1069540');
    });
    for (const mutation of ['missing', 'duplicate', 'wrong']) await t.test(`subpage ${mutation} navigation`, async () => {
      await load('03.response.txt', '/build/1069540/variables');
      await runtime.page.evaluate(kind => {
        const nav = document.querySelector('.tab-BuildPage .nav-link');
        if (kind === 'missing') nav.remove();
        if (kind === 'duplicate') nav.after(nav.cloneNode(true));
        if (kind === 'wrong') nav.textContent = 'Build (id:1069532)';
        document.title = 'Build #1069540';
      }, mutation);
      assert.equal(await identify(), mutation === 'wrong' ? '1069532' : null);
    });
    const live06 = new URL('../../docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C2b/live-06/', import.meta.url);
    for (const [file, id] of [['03.id-unverified.response.html', '1193469'], ['05.id-unverified.response.html', '1186372']]) {
      await t.test(`C2B-06 remembered Variables at bare build ${id}`, async () => {
        await runtime.page.setContent(readFileSync(new URL(file, live06), 'utf8'));
        assert.equal(await runtime.page.locator('.build-summary').count(), 0);
        path = `/build/${id}`;
        assert.equal(await identify(), id);
        path = `/build/${id}/overview`;
        assert.equal(await identify(), null);
      });
    }
    assert.equal(runtime.page.url(), 'about:blank');
    console.log('C2A-04 archived pages: page.setContent only; browser request policy denies every request');
  } finally { await runtime.close(); }
});

test('C2B-06 exact Run button grammar from live-06, with no navigation or click requests', async t => {
  const runtime = await createRuntime(playwright, chromium, {
    launchArgs: ['--no-proxy-server', '--host-resolver-rules=MAP * ~NOTFOUND'],
  });
  runtime.policy.allow = () => false;
  const html = readFileSync(new URL('../../docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C2b/live-06/07.response.html', import.meta.url), 'utf8');
  let clicks = 0;
  const page = {
    goto: async url => assert.equal(url, `${ORIGIN}/overview/1917`),
    url: () => `${ORIGIN}/overview/1917`,
    title: () => runtime.page.title(),
    locator: selector => {
      const locator = runtime.page.locator(selector);
      return { count: () => locator.count(), getAttribute: name => locator.getAttribute(name),
        click: async () => { clicks++; } };
    },
    getByText: () => ({ waitFor: async () => {} }),
  };
  const agent = new Agent({ ...runtime, page });
  agent.trusted = new TrustedPage(runtime.context, runtime.page);
  agent.projects.set(1917, { configuration_path: 'root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER', project_name: 'Tizen' });
  agent.snapshot = async () => ({ heading: true, base: `${ORIGIN}/wicket/page?50`,
    action: `${ORIGIN}/wicket/page?50-2.IFormSubmitListener-form`,
    rows: [{ label: 'PROJECT_NAME', viewers: ['Tizen'], controls: [] }, ...FIELDS.map(label => ({
      label, viewers: [], controls: (['CHILD_CONFIGURATIONS', 'TARGET_IMAGE'].includes(label)
        ? ['recorder', 'choices', 'selection'] : ['input']).map(role => ({ role,
        callback: `wicketAjaxPost('${ORIGIN}/wicket/page?50-2.IBehaviorListener.0-form-field', 0)` })),
    }))] });
  try {
    for (const mutation of ['none', 'anchor', 'duplicate', 'extra-statement', 'promote', 'run2', 'external', 'missing-onclick', 'trailing-newline']) {
      await t.test(mutation, async () => {
        clicks = 0; runtime.policy.runUrl = null;
        await runtime.page.setContent(html);
        await runtime.page.evaluate(kind => {
          const button = document.querySelector('button[title="Run the configuration"]');
          const code = button.getAttribute('onclick');
          if (kind === 'anchor') {
            const anchor = document.createElement('a'); anchor.title = button.title;
            anchor.href = '../wicket/page?9-1.ILinkListener-run'; button.replaceWith(anchor);
          }
          if (kind === 'duplicate') button.after(button.cloneNode(true));
          if (kind === 'extra-statement') button.setAttribute('onclick', code + ';alert(1)');
          if (kind === 'promote') button.setAttribute('onclick', code.replace('Listener-run', 'Listener-promote'));
          if (kind === 'run2') button.setAttribute('onclick', code.replace('Listener-run', 'Listener-run2'));
          if (kind === 'external') button.setAttribute('onclick', code.replace('../wicket/', 'https://outside.invalid/wicket/'));
          if (kind === 'missing-onclick') button.removeAttribute('onclick');
          if (kind === 'trailing-newline') button.setAttribute('onclick', code + '\n');
        }, mutation);
        if (mutation === 'none') {
          assert.deepEqual(await agent.openForm(1917), { released: false });
          assert.equal(runtime.policy.runUrl, `${ORIGIN}/wicket/page?9-1.ILinkListener-run`);
          assert.equal(clicks, 1);
        } else {
          await assert.rejects(agent.openForm(1917), { code: 'QB_FORM_CHANGED' });
          assert.equal(clicks, 0); assert.equal(runtime.policy.runUrl, null);
        }
      });
    }
    assert.equal(runtime.page.url(), 'about:blank');
  } finally { await runtime.close(); }
});

test('real browser DOM redaction with identities, hidden values, URL and recorder', async () => {
  const runtime = await createRuntime(playwright, chromium, {
    launchArgs: ['--no-proxy-server', '--host-resolver-rules=MAP * ~NOTFOUND'],
  });
  runtime.policy.allow = () => false;
  const agent = new Agent(runtime);
  try {
    const raw = `<span>Welcome! Alice-PRIVATE</span>
      <table><tr><td>Triggered By</td><td>Bob-PRIVATE</td></tr></table>
      <input type="hidden" name="opaque" value="hidden-SECRET">
      <input type="hidden" name="x:palette:recorder" value="616263">
      <a href="/x;jsessionid=url-SECRET?csrf=csrf-SECRET">test</a>
      <script>const token="script-SECRET";</script>
      <p>JSESSIONID_8810=text-SECRET</p>`;
    const html = await agent.trusted.run(redactDOM, raw);
    assert.doesNotMatch(html, /PRIVATE|SECRET|JSESSIONID_8810=/);
    assert.match(html, /616263/); assert.match(html, /&lt;USER&gt;/);
    assert.match(html, /&lt;REDACTED&gt;/);
    assert.equal(runtime.page.url(), 'about:blank');
  } finally { await runtime.close(); }
});

test('C2B-04 shared identity boundary and credential vectors', async t => {
  const vectors = JSON.parse(readFileSync(new URL('../fixtures/qb_redaction_vectors.json', import.meta.url), 'utf8'));
  const runtime = await createRuntime(playwright, chromium, {
    launchArgs: ['--no-proxy-server', '--host-resolver-rules=MAP * ~NOTFOUND'],
  });
  runtime.policy.allow = () => false;
  const agent = new Agent(runtime);
  try {
    for (const vector of vectors) await t.test(vector.name, async () => {
      const result = await agent.passive(vector.html);
      const html = result.html_redacted;
      const decoded = await runtime.page.evaluate(value => {
        const box = document.createElement('textarea'); box.innerHTML = value; return box.value;
      }, html);
      for (const value of [...vector.preserved, ...vector.masked]) assert.ok(decoded.includes(value), value);
      for (const value of vector.secrets) assert.ok(!decoded.includes(value), value);
      assert.equal(decoded.split('<USER>').length - 1, vector.user_mask_count);
      assert.equal(result.outside_identity_count, vector.identity_outside_registered_count);
      assert.deepEqual(runtime.trace.at(-1), {
        action: 'IDENTITY_OUTSIDE_REGISTERED', count: vector.identity_outside_registered_count,
      });
    });
    assert.equal(runtime.page.url(), 'about:blank');
  } finally { await runtime.close(); }
});

test('browser Fetch response 307/308 denied, 302 next-hop judged before server receives', async () => {
  const received = [];
  const server = createServer((request, response) => {
    received.push(request.url); request.resume();
    const status = request.url.match(/^\/build\/(302|307|308)$/)?.[1];
    if (status) { response.writeHead(Number(status), { Location: '/build/999' }); response.end(); }
    else if (request.url === '/build/301') { response.writeHead(302, { Location: '/rest/forbidden' }); response.end(); }
    else { response.end('<title>Local</title>'); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const host = `127.0.0.1:${server.address().port}`;
  const runtime = await createRuntime(playwright, chromium, {
    launchArgs: ['--no-proxy-server', '--host-resolver-rules=EXCLUDE 127.0.0.1, MAP * ~NOTFOUND'],
  });
  const original = runtime.policy.allow.bind(runtime.policy);
  runtime.policy.allow = (m, id) => m.host === host && original({ ...m, protocol: 'https:', host: new URL(ORIGIN).host }, id);
  runtime.policy.phase = 'read';
  try {
    for (const status of [307, 308]) {
      const start = received.length;
      await runtime.page.goto(`http://${host}/build/${status}`).catch(() => {});
      // Chromium commits its error document asynchronously after blocked redirects.
      await runtime.page.waitForTimeout(200);
      assert.equal(received.slice(start).includes('/build/999'), false);
      assert.equal(received.slice(start).includes(`/build/${status}`), true);
    }
    await runtime.page.goto(`http://${host}/build/302`);
    assert.equal(received.includes('/build/999'), true);
    await runtime.page.goto(`http://${host}/build/301`).catch(() => {});
    assert.equal(received.includes('/rest/forbidden'), false);
    assert.equal(runtime.failure, null);
    console.log(JSON.stringify({ received, forbiddenReceived: 0 }));
  } finally { await runtime.close(); await new Promise(resolve => server.close(resolve)); }
});

test('C2B-10 local form switches Full -> Partial -> Full with Math.random callbacks', async () => {
  const received = [];
  const callbackPath = '/wicket/page?50-2.IBehaviorListener.0-form-build-type';
  const server = createServer(async (request, response) => {
    let body = '';
    for await (const part of request) body += part;
    received.push({ method: request.method, path: request.url, body });
    if (request.method === 'POST') { response.end(body); return; }
    response.setHeader('Content-Type', 'text/html');
    response.end(`<!doctype html><link rel="icon" href="data:,"><h1>Specify Build Options</h1>
      <form action="/wicket/page?50-2.IFormSubmitListener-form"><table><tr>
      <td class="form-label">BUILD_TYPE</td><td class="value"><select name="build:editor"
      onchange="wicketAjaxPost('${callbackPath}', this.value)">
      <option>Full</option><option>Partial</option></select></td></tr></table></form><output id="ack">Full</output>
      <script>function wicketAjaxPost(url, value) {
        fetch(url + '&random=' + Math.random(), {method: 'POST', body: value})
          .then(response => response.text()).then(value => document.querySelector('#ack').textContent = value);
      }</script>`);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const host = `127.0.0.1:${server.address().port}`;
  let runtime;
  try {
    runtime = await createRuntime(playwright, chromium, {
      launchArgs: ['--no-proxy-server', '--host-resolver-rules=EXCLUDE 127.0.0.1, MAP * ~NOTFOUND'],
    });
    const original = runtime.policy.allow.bind(runtime.policy);
    runtime.policy.allow = (m, id) => m.host === host
      && original({ ...m, protocol: 'https:', host: new URL(ORIGIN).host }, id);
    runtime.policy.phase = 'fill';
    await runtime.page.goto(`http://${host}/wicket/page?50`);
    const agent = new Agent(runtime);
    const select = agent.fieldRow('BUILD_TYPE').locator('td.value select');
    assert.equal(await select.inputValue(), 'Full');
    for (const value of ['Partial', 'Full']) {
      const code = await select.getAttribute('onchange');
      runtime.policy.beginField(callbackURL(code, `${ORIGIN}/wicket/page?50`));
      await select.selectOption({ label: value });
      await runtime.page.waitForFunction(expected => document.querySelector('#ack').textContent === expected, value);
      assert.equal(await select.inputValue(), value);
      assert.equal(runtime.policy.fieldFinished, true);
      assert.equal(runtime.policy.fieldUrl, null);
      runtime.policy.endField();
    }
    const posts = received.filter(row => row.method === 'POST');
    assert.equal(posts.length, 2);
    assert.deepEqual(posts.map(row => row.body), ['Partial', 'Full']);
    for (const post of posts) {
      assert.ok(post.path.startsWith(callbackPath));
      assert.match(post.path.slice(callbackPath.length), /^&random=0\.\d{1,20}$/);
    }
    assert.equal(received.some(row => row.path.includes('IFormSubmitListener')), false);
    assert.equal(runtime.policy.released, false);
    assert.equal(runtime.failure, null);
    console.log(JSON.stringify({ c2b10: 'local-field-callbacks', received, form_action_releases: 0 }));
  } finally {
    if (runtime) await runtime.close();
    await new Promise(resolve => server.close(resolve));
  }
});
