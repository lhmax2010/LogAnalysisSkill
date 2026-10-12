import { createServer } from 'node:http';
import { createServer as createSecureServer } from 'node:https';
import { createHash, X509Certificate } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';

// Only synthetic loopback servers. No QuickBuild URL or credential is used.
const [modulePath, executablePath, caseName] = process.argv.slice(2);
const { chromium } = await import(pathToFileURL(modulePath).href);
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const certDir = await mkdtemp('/dev/shm/p5q-boundary-cert-');
execFileSync('openssl', ['req', '-x509', '-newkey', 'rsa:2048', '-nodes',
  '-keyout', `${certDir}/key.pem`, '-out', `${certDir}/cert.pem`, '-days', '1',
  '-subj', '/CN=127.0.0.1', '-addext', 'subjectAltName=IP:127.0.0.1'], { stdio: 'ignore' });
const cert = await readFile(`${certDir}/cert.pem`);
const key = await readFile(`${certDir}/key.pem`);
const spki = createHash('sha256').update(new X509Certificate(cert).publicKey.export({
  type: 'spki', format: 'der',
})).digest('base64');
const requests = [];
const handshakes = [];
function reply(request, response) {
  requests.push({ method: request.method, path: request.url });
  response.setHeader('Content-Type', 'text/html; charset=utf-8');
  const script = request.url === '/probe/h'
    ? '<script>window.name="p5q-named-popup";opener.postMessage("p5q-popup-ready", "*")</script>'
    : request.url.startsWith('/probe/')
      ? `<script>fetch(${JSON.stringify(`${request.url}-script`)})</script>` : '';
  response.end(`<!doctype html><title>Local P5Q fixture</title><body>fixture${script}</body>`);
}
const server = createServer(reply);
const secure = createSecureServer({ cert, key }, reply);
for (const [instance, scheme] of [[server, 'ws'], [secure, 'wss']]) {
  instance.on('upgrade', (request, socket) => {
    handshakes.push({ scheme, path: request.url });
    // Complete the synthetic handshake so the unprotected control is real.
    const accept = createHash('sha1').update(`${request.headers['sec-websocket-key']}258EAFA5-E914-47DA-95CA-C5AB0DC85B11`).digest('base64');
    socket.end(`HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: ${accept}\r\n\r\n`);
  });
  await new Promise((resolve) => instance.listen(0, '127.0.0.1', resolve));
}
const origin = `http://127.0.0.1:${server.address().port}`;
const wsOrigin = origin.replace('http:', 'ws:');
const wssOrigin = `wss://127.0.0.1:${secure.address().port}`;
const rows = [];
const activeBrowsers = new Set();

function protocolMetadata(event) {
  const url = new URL(event.request.url);
  return { requestId: event.requestId, frameId: event.frameId ?? null,
    method: event.request.method, origin: url.origin, path: url.pathname,
    resourceType: event.resourceType, responseStatus: event.responseStatusCode ?? null };
}

function frameIds(tree) {
  return [tree.frame.id, ...(tree.childFrames ?? []).flatMap(frameIds)];
}

async function runCase(name, protectedMode) {
  const profile = await mkdtemp('/dev/shm/p5q-boundary-profile-');
  process.env.TMPDIR = profile;
  const env = { ...process.env, TMPDIR: profile };
  for (const name of ['DEBUG', 'PWDEBUG', 'QB_COOKIE', 'QB_PASSWORD']) delete env[name];
  let browser;
  let closing;
  let stopped = null;
  let phase = 'launch';
  const targets = [];
  const workers = [];
  const intercepted = [];
  const socketBlocks = [];
  const referenceAttempts = [];
  const decisions = [];
  const row = { name, mode: protectedMode ? 'protected' : 'control', ok: false };
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
        `--ignore-certificate-errors-spki-list=${spki}`,
        ...(protectedMode ? ['--block-new-web-contents'] : [])],
    });
    activeBrowsers.add(browser);
    const context = await browser.newContext({ acceptDownloads: false, serviceWorkers: 'block' });
    if (protectedMode) {
      await context.routeWebSocket('**/*', (socket) => {
        socketBlocks.push(new URL(socket.url()).pathname);
        socket.close();
      });
      await context.addInitScript(() => Object.defineProperty(window, 'open', {
        value: () => null, configurable: false, writable: false,
      }));
    }
    const page = await context.newPage();
    // Only these fixed synthetic messages are observed, never arbitrary logs.
    page.on('console', (message) => {
      const value = message.text();
      if (value.startsWith('P5Q_REFERENCE:')) referenceAttempts.push(JSON.parse(value.slice(14)));
    });
    const primary = await context.newCDPSession(page);
    const { targetInfo: main } = await primary.send('Target.getTargetInfo');
    await primary.send('Page.enable');
    const { frameTree } = await primary.send('Page.getFrameTree');
    const ownedFrames = new Map(frameIds(frameTree).map((id) => [id, null]));
    primary.on('Page.frameAttached', ({ frameId, parentFrameId }) => {
      if (ownedFrames.has(parentFrameId)) ownedFrames.set(frameId, parentFrameId);
    });
    primary.on('Page.frameDetached', ({ frameId }) => {
      const remove = (id) => {
        for (const [child, parent] of ownedFrames) if (parent === id) remove(child);
        ownedFrames.delete(id);
      };
      remove(frameId);
    });
    primary.on('Page.frameNavigated', ({ frame }) => {
      if (!frame.parentId) {
        ownedFrames.clear();
        ownedFrames.set(frame.id, null);
      } else if (ownedFrames.has(frame.parentId)) ownedFrames.set(frame.id, frame.parentId);
    });
    row.initialFrameIds = [...ownedFrames.keys()];
    const root = await browser.newBrowserCDPSession();
    const { arguments: commandLine } = await root.send('Browser.getBrowserCommandLine');
    row.startup = { node: process.versions.node, chromium: browser.version(),
      blockNewWebContents: commandLine.includes('--block-new-web-contents'),
      disablePopupBlocking: commandLine.includes('--disable-popup-blocking') };
    const stopWorker = (session, { targetInfo, waitingForDebugger }) => {
      if (!['worker', 'shared_worker', 'service_worker'].includes(targetInfo.type)
        || workers.some((worker) => worker.targetId === targetInfo.targetId)) return;
      workers.push({ type: targetInfo.type, targetId: targetInfo.targetId, waitingForDebugger });
      session.send('Target.closeTarget', { targetId: targetInfo.targetId }).then((result) => {
        if (!result.success) stop();
      }, stop);
    };
    if (protectedMode) {
      root.on('Fetch.requestPaused', (event) => {
        // Only sanitized protocol metadata crosses into policy/ownership logic.
        const metadata = protocolMetadata(event);
        decisions.push((async () => {
          const owned = Boolean(metadata.frameId) && ownedFrames.has(metadata.frameId);
          const forbidden = !owned || metadata.origin !== origin
            || [307, 308].includes(metadata.responseStatus);
          intercepted.push({ ...metadata, owned, forbidden });
          try {
            await root.send(forbidden ? 'Fetch.failRequest'
              : metadata.responseStatus === null ? 'Fetch.continueRequest' : 'Fetch.continueResponse',
            forbidden ? { requestId: metadata.requestId, errorReason: 'BlockedByClient' }
              : { requestId: metadata.requestId });
          } catch { stop(); }
        })());
      });
      phase = 'browser_fetch';
      await root.send('Fetch.enable', { patterns: [
        { urlPattern: '*', requestStage: 'Request' },
        { urlPattern: '*', requestStage: 'Response' },
      ] });
    }
    root.on('Target.targetCreated', ({ targetInfo }) => {
      if (targetInfo.type !== 'page' || targetInfo.targetId === main.targetId) return;
      targets.push({ type: targetInfo.type });
      if (protectedMode) stop();
    });
    phase = 'discovery';
    await root.send('Target.setDiscoverTargets', { discover: true });
    if (protectedMode) {
      root.on('Target.attachedToTarget', (event) => stopWorker(root, event));
      await root.send('Target.setAutoAttach', {
        autoAttach: true, waitForDebuggerOnStart: true, flatten: true,
        filter: [{ type: 'browser', exclude: true }, { type: 'tab', exclude: true }, {}],
      });
      const related = await browser.newBrowserCDPSession();
      related.on('Target.attachedToTarget', (event) => stopWorker(related, event));
      await related.send('Target.autoAttachRelated', {
        targetId: main.targetId, waitForDebuggerOnStart: true,
        filter: [{ type: 'browser', exclude: true }, { type: 'tab', exclude: true }, {}],
      });
    }
    phase = 'fixture_navigation';
    const setupStart = requests.length;
    await page.goto(`${origin}/fixture/${name}`, { timeout: 5000 });
    row.setupRequests = requests.slice(setupStart);
    row.openDescriptor = await page.evaluate(() => {
      const { writable, configurable } = Object.getOwnPropertyDescriptor(window, 'open');
      return { writable, configurable };
    });
    const start = requests.length;
    const wsStart = handshakes.length;
    phase = 'fixture_execution';
    try {
      row.output = await page.evaluate(({ name, origin, wsOrigin, wssOrigin }) => {
        const url = `${origin}/probe/${name}`;
        if (name === 'a') return { returnedNull: window.open(url) === null };
        if (name === 'b') {
          const popup = window.open('about:blank');
          if (popup) popup.document.write(`<script>fetch(${JSON.stringify(url)})<\/script>`);
          return { returnedNull: popup === null };
        }
        if (name === 'd') {
          const form = Object.assign(document.createElement('form'), {
            action: url, method: 'GET', target: '_blank',
          });
          document.body.append(form);
          form.submit();
        } else if (name.startsWith('e-')) {
          const script = URL.createObjectURL(new Blob([`fetch(${JSON.stringify(url)})`], { type: 'text/javascript' }));
          globalThis.fixtureWorker = name === 'e-worker' ? new Worker(script) : new SharedWorker(script);
        } else {
          let href = url;
          if (name === 'g') {
            href = URL.createObjectURL(new Blob([`<script>
              fetch(${JSON.stringify(url)});
              new WebSocket(${JSON.stringify(`${wsOrigin}/probe/g-ws`)});
              new WebSocket(${JSON.stringify(`${wssOrigin}/probe/g-wss`)});
              <\/script>`], { type: 'text/html' }));
          }
          const popupName = 'p5q-named-popup';
          if (name === 'h') {
            addEventListener('message', (event) => {
              if (event.data !== 'p5q-popup-ready') return;
              const obtained = Boolean(event.source && event.source !== window);
              console.log(`P5Q_REFERENCE:${JSON.stringify({ route: 'message.source', obtained })}`);
              if (obtained) event.source.document.write(`<script>fetch(${JSON.stringify(url)})<\/script>`);
            });
          }
          const link = Object.assign(document.createElement('a'), { href, target: '_blank' });
          if (name === 'h') link.rel = 'opener';
          document.body.append(link);
          link.click();
          if (name === 'h') {
            const byOpen = window.open('', popupName);
            const byName = window[popupName];
            const byFrames = window.frames[popupName];
            const candidates = [['window.open', byOpen], ['window.name', byName], ['window.frames', byFrames]];
            for (const [route, ref] of candidates) {
              const obtained = Boolean(ref && ref !== window && ref.window === ref);
              console.log(`P5Q_REFERENCE:${JSON.stringify({ route, obtained })}`);
              if (obtained) ref.document.write(`<script>fetch(${JSON.stringify(url)})<\/script>`);
            }
            return { returnedNull: byOpen === null, namedReference: Boolean(byName), frameReference: Boolean(byFrames) };
          }
        }
        return { fixtureDispatched: true };
      }, { name, origin, wsOrigin, wssOrigin });
    } catch {
      row.fixtureError = 'FIXTURE_INTERRUPTED';
    }
    await wait(1000);
    if (closing) await closing;
    await Promise.all(decisions);
    row.actualRequests = requests.slice(start);
    row.received = row.actualRequests.filter((request) => request.path.startsWith('/probe/'));
    row.handshakes = handshakes.slice(wsStart);
    row.newPageTargets = targets.length;
    row.workers = workers;
    row.intercepted = intercepted;
    row.socketBlocks = socketBlocks;
    row.referenceAttempts = referenceAttempts;
    row.stopped = stopped;
    row.browserClosed = !browser.isConnected();
    const noNetwork = row.received.length === 0 && row.handshakes.length === 0;
    const closesOnPage = targets.length > 0 && row.browserClosed && stopped === 'QB_BROWSER_UNAVAILABLE';
    if (!protectedMode) {
      row.ok = row.received.length > 0 && targets.length > 0;
      if (name === 'g') row.ok &&= ['ws', 'wss'].every((scheme) => row.handshakes.some((h) => h.scheme === scheme));
    } else if (['c', 'd', 'g', 'h'].includes(name)) {
      row.ok = noNetwork && closesOnPage;
      if (name === 'h') row.ok &&= referenceAttempts.length >= 3 && referenceAttempts.every((entry) => !entry.obtained);
    } else {
      row.ok = noNetwork && targets.length === 0;
      if (name.startsWith('e-')) row.ok &&= workers.some((worker) => worker.waitingForDebugger);
      else row.ok &&= row.output?.returnedNull === true;
    }
  } catch {
    row.error = 'LOCAL_CASE_FAILED';
    row.phase = phase;
    row.intercepted = intercepted;
    row.stopped = stopped;
  } finally {
    if (browser) {
      await browser.close();
      activeBrowsers.delete(browser);
    }
    await rm(profile, { recursive: true, force: true });
    row.profileRemoved = !existsSync(profile);
    row.ok &&= row.profileRemoved;
    rows.push(row);
    console.log(JSON.stringify(row));
  }
}

try {
  // h is superseded by p5q_h_interception_probe.mjs (C2A-03).
  for (const name of caseName ? [caseName] : ['a', 'b', 'c', 'd', 'e-worker', 'e-shared', 'g']) await runCase(name, true);
  for (const name of caseName ? [caseName] : ['a', 'b', 'g']) await runCase(name, false);
  console.log(JSON.stringify({ summary: rows.length, passed: rows.filter((row) => row.ok).length,
    failed: rows.filter((row) => !row.ok).length, externalRequests: 0 }));
  process.exitCode = rows.every((row) => row.ok) ? 0 : 1;
} finally {
  for (const browser of activeBrowsers) await browser.close();
  for (const instance of [server, secure]) {
    instance.closeAllConnections();
    await new Promise((resolve) => instance.close(resolve));
  }
  await rm(certDir, { recursive: true, force: true });
  console.log(JSON.stringify({ certificateRemoved: !existsSync(certDir) }));
}
