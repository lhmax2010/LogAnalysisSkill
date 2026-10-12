import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import test from 'node:test';
import { createRuntime, redactDOM, ORIGIN } from '../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';

const [playwright, chromium] = process.argv.slice(2);
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
