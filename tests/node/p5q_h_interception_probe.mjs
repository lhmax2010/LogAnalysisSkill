import { createServer } from 'node:http';
import { createServer as createSecureServer } from 'node:https';
import { createHash, X509Certificate } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
import { installGuards, Policy } from '../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';

// Diagnostic switches live only in this synthetic, loopback-only test entrypoint.
const [modulePath, executablePath] = process.argv.slice(2);
const { chromium } = await import(pathToFileURL(modulePath).href);
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const directory = await mkdtemp('/dev/shm/p5q-h-probe-');
execFileSync('openssl', ['req', '-x509', '-newkey', 'rsa:2048', '-nodes',
  '-keyout', `${directory}/key.pem`, '-out', `${directory}/cert.pem`, '-days', '1',
  '-subj', '/CN=127.0.0.1', '-addext', 'subjectAltName=IP:127.0.0.1'], { stdio: 'ignore' });
const cert = await readFile(`${directory}/cert.pem`);
const key = await readFile(`${directory}/key.pem`);
const spki = createHash('sha256').update(new X509Certificate(cert).publicKey.export({
  type: 'spki', format: 'der',
})).digest('base64');
const requests = [];
const handshakes = [];
function reply(request, response) {
  requests.push({ method: request.method, path: request.url });
  request.resume();
  response.setHeader('Content-Type', 'text/html; charset=utf-8');
  response.end('<!doctype html><link rel="icon" href="data:,"><title>Synthetic P5Q h fixture</title><body>fixture</body>');
}
const server = createServer(reply);
const secure = createSecureServer({ cert, key }, reply);
for (const [instance, scheme] of [[server, 'ws'], [secure, 'wss']]) {
  instance.on('upgrade', (request, socket) => {
    handshakes.push({ scheme, path: request.url });
    socket.destroy();
  });
  await new Promise((resolve) => instance.listen(0, '127.0.0.1', resolve));
}
const origin = `http://127.0.0.1:${server.address().port}`;
const wsOrigin = origin.replace('http:', 'ws:');
const wssOrigin = `wss://127.0.0.1:${secure.address().port}`;
const rows = [];

async function run(mode) {
  const diagnostic = mode !== 'normal';
  const useBrowserFetch = mode !== 'control';
  const profile = await mkdtemp(`${directory}/profile-`);
  process.env.TMPDIR = profile;
  const env = { ...process.env, TMPDIR: profile };
  for (const name of ['DEBUG', 'PWDEBUG', 'QB_COOKIE', 'QB_PASSWORD']) delete env[name];
  const row = { mode, diagnostic, useBrowserFetch, ok: false };
  const transcript = [];
  const intercepted = [];
  const wsBlocks = [];
  const pageTargets = [];
  const workerTargets = [];
  const pending = [];
  let browser;
  let closing;
  let stopped = null;
  let phase = 'launch';
  const stop = () => {
    stopped = 'QB_BROWSER_UNAVAILABLE';
    closing ??= browser.close();
  };
  try {
    browser = await chromium.launch({ executablePath, headless: false, env,
      ignoreDefaultArgs: ['--disable-popup-blocking'],
      args: ['--disable-background-networking', '--disable-component-update', '--disable-sync',
        '--disable-breakpad', '--disable-crash-reporter', '--no-proxy-server',
        '--host-resolver-rules=EXCLUDE 127.0.0.1, MAP * ~NOTFOUND',
        `--ignore-certificate-errors-spki-list=${spki}`, '--block-new-web-contents'],
    });
    const context = await browser.newContext({ acceptDownloads: false, serviceWorkers: 'block' });
    await context.routeWebSocket('**/*', (socket) => {
      wsBlocks.push(new URL(socket.url()).pathname);
      socket.close();
    });
    await context.addInitScript(() => Object.defineProperty(window, 'open', {
      value: () => null, configurable: false, writable: false,
    }));
    const page = await context.newPage();
    const primary = await context.newCDPSession(page);
    primary.on('Runtime.consoleAPICalled', ({ args }) => {
      // This fixture emits only fixed-category, synthetic JSON. No real page logs.
      const value = args[0]?.value;
      if (typeof value !== 'string' || !value.startsWith('P5Q_H:')) return;
      const entry = JSON.parse(value.slice(6));
      transcript.push(entry);
      console.log(JSON.stringify({ event: 'Runtime.consoleAPICalled', mode, entry }));
    });
    await primary.send('Runtime.enable');
    const policy = new Policy();
    policy.phase = 'h_probe';
    // The fixture host is loopback; frame ownership and CDP mechanisms are the
    // production implementation, not a separately reimplemented security guard.
    policy.allow = (metadata) => `${metadata.protocol}//${metadata.host}` === origin
      && ![307, 308].includes(metadata.response_status);
    const trace = [];
    const { root } = await installGuards(browser, context, page, policy, stop, trace,
      { diagnostic, useBrowserFetch });
    root.on('Target.targetCreated', ({ targetInfo }) => {
      if (targetInfo.type === 'page') pageTargets.push(targetInfo.targetId);
    });
    root.on('Fetch.requestPaused', () => intercepted.push({ event: 'paused' }));
    root.on('Target.attachedToTarget', ({ targetInfo, waitingForDebugger }) => {
      workerTargets.push({ type: targetInfo.type, waitingForDebugger });
    });
    const { arguments: argv } = await root.send('Browser.getBrowserCommandLine');
    row.startup = { node: process.versions.node, chromium: browser.version(),
      blockNewWebContents: argv.includes('--block-new-web-contents'),
      disablePopupBlocking: argv.includes('--disable-popup-blocking') };
    phase = 'fixture_navigation';
    await page.goto(`${origin}/fixture/${mode}`, { timeout: 5000 });
    row.openDescriptor = await page.evaluate(() => {
      const { writable, configurable } = Object.getOwnPropertyDescriptor(window, 'open');
      return { writable, configurable, returnedNull: window.open('about:blank') === null };
    });
    const httpStart = requests.length;
    const wsStart = handshakes.length;
    phase = 'h1_h2';
    try {
      await page.evaluate(({ origin, wsOrigin, wssOrigin }) => {
        const log = (entry) => console.log(`P5Q_H:${JSON.stringify(entry)}`);
        const deadline = performance.now() + 10000;
        let round = 0;
        const refs = [];
        const blobs = [];
        addEventListener('message', (event) => {
          if (event.data?.tag !== 'p5q-h-ready') return;
          const ref = event.source;
          const obtained = Boolean(ref && ref !== window);
          const round = event.data.round;
          log({ kind: 'reference', round, obtained });
          if (!obtained || performance.now() >= deadline) return;
          refs.push(ref);
          const invoke = (operation, action) => {
            try {
              const result = action();
              log({ kind: 'attempt', round, operation, result: 'INVOKED' });
              if (result?.then) result.then(
                () => log({ kind: 'completion', round, operation, result: 'RESOLVED' }),
                () => log({ kind: 'completion', round, operation, result: 'REJECTED' }));
            } catch (error) {
              log({ kind: 'attempt', round, operation, result: 'THREW', error: error.name });
            }
          };
          const url = (kind) => `${origin}/attack/${round}/${kind}`;
          invoke('fetch', () => ref.fetch(url('fetch')));
          invoke('fetch-eval', () => ref.eval(`fetch(${JSON.stringify(url('fetch-eval'))})`));
          invoke('xhr', () => {
            const xhr = new ref.XMLHttpRequest();
            xhr.open('GET', url('xhr'));
            xhr.send();
          });
          invoke('ws', () => new ref.WebSocket(`${wsOrigin}/attack/${round}/ws`));
          invoke('wss', () => new ref.WebSocket(`${wssOrigin}/attack/${round}/wss`));
          invoke('form', () => {
            const form = Object.assign(ref.document.createElement('form'), { method: 'POST', action: url('form') });
            ref.document.body.append(form);
            form.submit();
          });
          invoke('location', () => { ref.location.href = url('location'); });
        });
        const launch = () => {
          if (performance.now() >= deadline) { log({ kind: 'window_complete', rounds: round }); return; }
          round += 1;
          const blob = URL.createObjectURL(new Blob([
            `<body><script>opener.postMessage({tag:'p5q-h-ready',round:${round}}, '*');<\/script>`,
          ], { type: 'text/html' }));
          blobs.push(blob);
          const link = Object.assign(document.createElement('a'), { href: blob, target: '_blank', rel: 'opener' });
          document.body.append(link);
          log({ kind: 'launch', round });
          link.click();
        };
        globalThis.probeReferences = refs;
        globalThis.probeBlobs = blobs;
        globalThis.launchProbeRound = launch;
        globalThis.finishProbeWindow = () => log({ kind: 'window_complete', rounds: round });
        launch();
      }, { origin, wsOrigin, wssOrigin });
    } catch { row.fixtureInterrupted = true; }
    if (diagnostic) {
      // Each evaluation supplies a fresh activation, avoiding popup-throttle
      // false greens while retaining the page's scripted _blank click.
      for (let index = 1; index < 20; index += 1) {
        await wait(450);
        await page.evaluate(() => globalThis.launchProbeRound());
      }
      await wait(1000);
      await page.evaluate(() => globalThis.finishProbeWindow());
    } else await wait(700);
    if (closing) await closing;
    await Promise.all(pending);
    row.http = requests.slice(httpStart).filter((request) => request.path.startsWith('/attack/'));
    row.otherHttp = requests.slice(httpStart).filter((request) => !request.path.startsWith('/attack/'));
    row.websockets = handshakes.slice(wsStart);
    row.newPageTargets = pageTargets.length;
    row.workerTargets = workerTargets;
    row.wsBlocks = wsBlocks;
    row.intercepted = intercepted;
    row.referenceRecords = transcript.filter((entry) => entry.kind === 'reference');
    row.attemptCounts = Object.fromEntries(['fetch', 'fetch-eval', 'xhr', 'form', 'location', 'ws', 'wss'].map(
      (operation) => [operation, transcript.filter((entry) => entry.kind === 'attempt' && entry.operation === operation).length]));
    row.transcriptRecords = transcript.length;
    row.browserClosed = !browser.isConnected();
    row.stopped = stopped;
    row.ok = mode === 'control' ? row.http.length > 0
      : row.http.length === 0 && row.otherHttp.length === 0 && row.websockets.length === 0;
    if (mode === 'normal') row.ok &&= row.browserClosed && stopped === 'QB_BROWSER_UNAVAILABLE';
    else row.ok &&= transcript.some((entry) => entry.kind === 'window_complete');
  } catch {
    row.error = 'LOCAL_PROBE_FAILED';
    row.phase = phase;
    row.stopped = stopped;
  } finally {
    if (browser) await browser.close();
    await rm(profile, { recursive: true, force: true });
    row.profileRemoved = !existsSync(profile);
    rows.push(row);
    console.log(JSON.stringify({ event: 'result', ...row }));
  }
}

try {
  for (const mode of ['diagnostic', 'normal', 'control']) await run(mode);
  console.log(JSON.stringify({ summary: rows.length, passed: rows.filter((row) => row.ok).length,
    failed: rows.filter((row) => !row.ok).length, networkScope: 'synthetic-loopback-only' }));
  process.exitCode = rows.every((row) => row.ok) ? 0 : 1;
} finally {
  for (const instance of [server, secure]) {
    instance.closeAllConnections();
    await new Promise((resolve) => instance.close(resolve));
  }
  await rm(directory, { recursive: true, force: true });
  console.log(JSON.stringify({ temporaryDirectoryRemoved: !existsSync(directory) }));
}
