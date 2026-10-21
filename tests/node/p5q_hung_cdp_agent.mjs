// Synthetic CDP adapter; executes the production trusted-read path without a browser.
import readline from 'node:readline';
import fs from 'node:fs';
import { Agent, Policy } from '../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';

const hold = process.argv[2];
const scenario = process.argv[3] ? JSON.parse(fs.readFileSync(process.argv[3], 'utf8')) : { replies: [] };
const keepAlive = setInterval(() => {}, 1000);
const wait = async name => { if (name === hold) await new Promise(() => {}); };
const cdp = {
  async send(method) {
    await wait(method);
    if (method === 'Page.getFrameTree') return { frameTree: { frame: { id: 'working-frame' } } };
    if (method === 'Page.createIsolatedWorld') return { executionContextId: 1 };
    return { result: { value: { ok: true, value: {
      build: { labels: [`Build (id:${new URL(url).pathname.split('/')[2]})`], summaries: [] },
      redacted: { html_redacted: '<html><body>synthetic</body></html>', outside_identity_count: 0 },
    } } } };
  },
  async detach() { await wait('detach'); },
};
const policy = new Policy();
let url = 'https://quickbuild.tizen.org/build/1/variables';
const page = {
  url: () => url,
  async goto(expected) {
    url = expected;
    Object.assign(policy.readNavigation, { requestId: 'synthetic', body: Buffer.from('<html></html>') });
    return { url: () => url, status: () => 200, request: () => ({ redirectedFrom: () => null }),
      headerValue: async () => 'text/html; charset=utf-8' };
  },
};
const agent = new Agent({ page, policy, trace: [], context: {
  async newCDPSession() { await wait('newCDPSession'); return cdp; },
} });
for await (const line of readline.createInterface({ input: process.stdin })) {
  const request = JSON.parse(line);
  if (scenario.log) fs.appendFileSync(scenario.log, JSON.stringify(request) + '\n');
  if (request.command === 'close') break;
  if (request.command === 'login') { process.stdout.write('{"ok":true}\n'); continue; }
  if (scenario.replies.length) {
    process.stdout.write(JSON.stringify(scenario.replies.shift()) + '\n'); continue;
  }
  // Both operations begin by entering the unmodified TrustedPage.run implementation.
  const result = request.command === 'submit'
    ? await agent.submit('a'.repeat(64)) : await agent.read(request.path);
  process.stdout.write(JSON.stringify({ ok: true, ...result }) + '\n');
}
clearInterval(keepAlive);
process.stdin.destroy();
