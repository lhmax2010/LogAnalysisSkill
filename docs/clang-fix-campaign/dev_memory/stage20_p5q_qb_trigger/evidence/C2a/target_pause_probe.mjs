import { existsSync } from 'node:fs';
import { mkdtemp, rm } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';

// Offline capability experiment, not the production agent or a login command.
const [modulePath, executablePath, mode = 'hold'] = process.argv.slice(2);
if (!['baseline', 'hold', 'close'].includes(mode)) throw new Error('INVALID_PROBE_MODE');
const { chromium } = await import(pathToFileURL(modulePath).href);
const profile = await mkdtemp('/dev/shm/p5q-target-probe-');
process.env.TMPDIR = profile;
delete process.env.DEBUG;
delete process.env.PWDEBUG;
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
let browser;
let phase = 'launch';
try {
  browser = await chromium.launch({
    executablePath, headless: false,
    args: ['--disable-background-networking', '--disable-component-update',
      '--disable-sync', '--disable-breakpad', '--disable-crash-reporter',
      '--no-proxy-server', '--host-resolver-rules=MAP * ~NOTFOUND'],
    env: { ...process.env, TMPDIR: profile },
  });
  phase = 'new_context';
  const context = await browser.newContext({ acceptDownloads: false, serviceWorkers: 'block' });
  phase = 'websocket_route';
  await context.routeWebSocket('**/*', (socket) => socket.close());
  const requestSchemes = {};
  context.on('request', (request) => {
    const scheme = new URL(request.url()).protocol;
    requestSchemes[scheme] = (requestSchemes[scheme] ?? 0) + 1;
  });
  console.log(JSON.stringify({ node: process.versions.node, chromium: browser.version(), mode }));
  const page = await context.newPage();
  phase = 'browser_cdp';
  const root = await browser.newBrowserCDPSession();
  const events = [];
  const closures = [];
  root.on('Target.attachedToTarget', ({ targetInfo, waitingForDebugger }) => {
    events.push({ channel: 'browser', type: targetInfo.type,
      isPopup: Boolean(targetInfo.openerId), waitingForDebugger });
    if (mode === 'close' && targetInfo.openerId) {
      // Attempt closure immediately, without any child-session resume.
      closures.push(root.send('Target.closeTarget', { targetId: targetInfo.targetId }));
    }
  });
  phase = 'set_auto_attach';
  if (mode !== 'baseline') await root.send('Target.setAutoAttach', {
    autoAttach: true, waitForDebuggerOnStart: true, flatten: true,
    filter: [{ type: 'browser', exclude: true }, { type: 'tab', exclude: true }, {}],
  });
  const pageSession = await context.newCDPSession(page);
  const { targetInfo } = await pageSession.send('Target.getTargetInfo');
  phase = 'related_auto_attach';
  const related = await browser.newBrowserCDPSession();
  related.on('Target.attachedToTarget', ({ targetInfo, waitingForDebugger }) => {
    events.push({ channel: 'related', type: targetInfo.type, waitingForDebugger });
  });
  if (mode !== 'baseline') await related.send('Target.autoAttachRelated', {
    targetId: targetInfo.targetId, waitForDebuggerOnStart: true,
    filter: [{ type: 'browser', exclude: true }, { type: 'tab', exclude: true }, {}],
  });
  // Only in-memory payloads; no network URLs, no fetches, no login code.
  phase = 'secondary';
  const fixture = page.evaluate(() => {
    globalThis.probeWorkerRan = false;
    globalThis.probePopupRan = false;
    const worker = new Worker(URL.createObjectURL(new Blob(['postMessage("ran")'])));
    worker.onmessage = () => { globalThis.probeWorkerRan = true; };
    globalThis.probeWorker = worker;
    const popup = window.open('about:blank');
    popup.document.write('<script>opener.probePopupRan = true;<\/script>');
  });
  await delay(1000);
  const observed = await Promise.race([page.evaluate(() => ({
    workerRan: globalThis.probeWorkerRan, popupRan: globalThis.probePopupRan,
  })), delay(5000).then(() => { throw new Error('EVALUATION_TIMEOUT'); })]);
  await fixture;
  const closed = await Promise.all(closures);
  console.log(JSON.stringify({ phase: 'secondary_held', mode, ...observed,
    requestSchemes, closeResults: closed, events }));
  const ok = mode === 'baseline' ? observed.workerRan && observed.popupRan
    : !observed.workerRan && !observed.popupRan;
  console.log(`EXPECTATION=${ok ? 'PASS' : 'FAIL'}`);
  process.exitCode = ok ? 0 : 1;
} catch (error) {
  // Only fixed categories, never the underlying error or protocol event.
  const categories = ['DISPLAY', 'X server', 'shared libraries', 'Protocol error', 'ECONNRESET', 'ENOENT',
    'Only flatten protocol is supported with browser level auto-attach', 'Invalid parameters'];
  console.log(JSON.stringify({ error: 'CAPABILITY_PROBE_FAILED', phase,
    categories: categories.filter((value) => String(error.message).includes(value)) }));
  process.exitCode = 2;
} finally {
  await browser?.close();
  await rm(profile, { recursive: true, force: true });
  console.log(`PROFILE_REMOVED=${!existsSync(profile)}`);
}
