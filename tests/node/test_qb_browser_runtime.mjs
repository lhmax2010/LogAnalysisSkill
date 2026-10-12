import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { Agent, createRuntime, redactDOM, ORIGIN } from '../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';

const [playwright, chromium] = process.argv.slice(2);
const archive = new URL('../../docs/clang-fix-campaign/dev_memory/stage15_p1_ef_spike/evidence/web-cookie-02/', import.meta.url);

test('C2A-04 build identity from archived HTML, with all network denied', async t => {
  const runtime = await createRuntime(playwright, chromium, {
    launchArgs: ['--no-proxy-server', '--host-resolver-rules=MAP * ~NOTFOUND'],
  });
  runtime.policy.allow = () => false;
  let path;
  // Navigation is replaced only in this offline fixture; DOM evaluation is real Chromium.
  const page = {
    goto: async () => ({ status: () => 200, request: () => ({ redirectedFrom: () => null }) }),
    url: () => ORIGIN + path,
    evaluate: (...args) => runtime.page.evaluate(...args),
  };
  const agent = new Agent({ ...runtime, page });
  const load = async (file, requested) => {
    path = requested;
    await runtime.page.setContent(readFileSync(new URL(file, archive), 'utf8'));
  };
  try {
    for (const [file, requested] of [
      ['01.response.txt', '/build/1069540'],
      ['03.response.txt', '/build/1069540/variables'],
      ['04.response.txt', '/build/1069540/step_status'],
    ]) await t.test(`archive ${file} ${requested}`, async () => {
      await load(file, requested);
      assert.equal((await agent.read(path)).status, 200);
    });
    for (const spelling of ['Id', 'ID']) await t.test(`navigation spelling ${spelling}`, async () => {
      await load('03.response.txt', '/build/1069540/variables');
      await runtime.page.evaluate(value => {
        document.querySelector('.tab-BuildPage .nav-link span').textContent = `Build (${value}:1069540)`;
      }, spelling);
      assert.equal((await agent.read(path)).status, 200);
    });
    await t.test('Summary Id resolved by column, not fixed position', async () => {
      await load('01.response.txt', '/build/1069540');
      await runtime.page.evaluate(() => {
        const table = document.querySelector('.build-summary table');
        for (const row of [table.tHead.rows[0], table.tBodies[0].rows[0]]) row.append(row.cells[0]);
      });
      assert.equal((await agent.read(path)).status, 200);
    });
    for (const mutation of [
      'duplicate-nav', 'missing-nav', 'wrong-nav', 'missing-summary', 'duplicate-summary',
      'missing-id-column', 'duplicate-id-column', 'different-summary-id', 'missing-first-row',
    ]) await t.test(`reject ${mutation}`, async () => {
      await load('01.response.txt', '/build/1069540');
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
      await assert.rejects(agent.read(path), { code: 'QB_READ_ID_MISMATCH' });
    });
    await t.test('both homepage sources agree but differ from requested id', async () => {
      await load('01.response.txt', '/build/1069532');
      await assert.rejects(agent.read(path), { code: 'QB_READ_ID_MISMATCH' });
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
      await assert.rejects(agent.read(path), { code: 'QB_READ_ID_MISMATCH' });
    });
    assert.equal(runtime.page.url(), 'about:blank');
    console.log('C2A-04 archived pages: page.setContent only; browser request policy denies every request');
  } finally { await runtime.close(); }
});

test('real browser DOM redaction with identities, hidden values, URL and recorder', async () => {
  const runtime = await createRuntime(playwright, chromium, {
    launchArgs: ['--no-proxy-server', '--host-resolver-rules=MAP * ~NOTFOUND'],
  });
  try {
    await runtime.page.setContent(`<span>Welcome! Alice-PRIVATE</span>
      <table><tr><td>Triggered By</td><td>Bob-PRIVATE</td></tr></table>
      <input type="hidden" name="opaque" value="hidden-SECRET">
      <input type="hidden" name="x:palette:recorder" value="616263">
      <a href="/x;jsessionid=url-SECRET?csrf=csrf-SECRET">test</a>
      <script>const token="script-SECRET";</script>
      <p>JSESSIONID_8810=text-SECRET</p>`);
    const html = await runtime.page.evaluate(redactDOM);
    assert.doesNotMatch(html, /PRIVATE|SECRET|JSESSIONID_8810=/);
    assert.match(html, /616263/); assert.match(html, /&lt;USER&gt;/);
    assert.match(html, /&lt;REDACTED&gt;/);
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
