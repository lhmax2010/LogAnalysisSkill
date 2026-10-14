import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
const { createRuntime } = await import(pathToFileURL(resolve('tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs')).href);

const [modulePath, chromiumPath] = process.argv.slice(2);
const runtime = await createRuntime(modulePath, chromiumPath, {
  launchArgs: ['--no-proxy-server', '--host-resolver-rules=MAP * ~NOTFOUND'],
});
let requests = 0;
runtime.policy.allow = () => { requests++; return false; };
try {
  await runtime.page.setContent(`<select id="s" onchange="this.dataset.count=+(this.dataset.count||0)+1"><option>a</option><option>b</option></select>
    <input id="c" type="checkbox" onchange="this.dataset.count=+(this.dataset.count||0)+1">
    <textarea id="t" onchange="this.dataset.count=+(this.dataset.count||0)+1"></textarea>`);
  await runtime.page.locator('#s').selectOption({ label: 'b' });
  await runtime.page.locator('#c').check();
  await runtime.page.locator('#t').fill('changed');
  await runtime.page.locator('#t').blur();
  const session = await runtime.context.newCDPSession(runtime.page);
  const { frameTree } = await session.send('Page.getFrameTree');
  const { executionContextId } = await session.send('Page.createIsolatedWorld', {
    frameId: frameTree.frame.id, worldName: 'p5q-c2c-preflight',
  });
  const result = await session.send('Runtime.evaluate', {
    contextId: executionContextId,
    expression: `Array.from(document.querySelectorAll('#s,#c,#t'), e => Number(e.dataset.count))`,
    returnByValue: true,
  });
  assert.deepEqual(result.result.value, [1, 1, 1]);
  assert.equal(requests, 0);
  console.log(JSON.stringify({ isolated_world: true, change_counts: result.result.value,
    network_requests: requests, result: 'PASS' }));
} finally { await runtime.close(); }
