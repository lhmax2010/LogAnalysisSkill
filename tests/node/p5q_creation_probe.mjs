import { createServer } from 'node:http';
import { existsSync } from 'node:fs';
import { mkdtemp, rm } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';

// Synthetic loopback fixtures only. This is never a production agent entrypoint.
const [modulePath, executablePath] = process.argv.slice(2);
const { chromium } = await import(pathToFileURL(modulePath).href);
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const requests = [];
const server = createServer((request, response) => {
  requests.push({ method: request.method, path: request.url });
  response.setHeader('Content-Type', 'text/html; charset=utf-8');
  response.end('<!doctype html><title>Local P5Q fixture</title><body>fixture</body>');
});
await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const rows = [];
const activeBrowsers = new Set();

async function launch(protectedMode) {
  const profile = await mkdtemp('/dev/shm/p5q-creation-probe-');
  process.env.TMPDIR = profile;
  const env = { ...process.env, TMPDIR: profile };
  for (const name of ['DEBUG', 'PWDEBUG', 'QB_COOKIE', 'QB_PASSWORD']) delete env[name];
  try {
    const browser = await chromium.launch({ executablePath, headless: false, env,
      ignoreDefaultArgs: ['--disable-popup-blocking'],
      args: ['--disable-background-networking', '--disable-component-update',
        '--disable-sync', '--disable-breakpad', '--disable-crash-reporter',
        '--no-proxy-server', '--host-resolver-rules=EXCLUDE 127.0.0.1, MAP * ~NOTFOUND',
        ...(protectedMode ? ['--block-new-web-contents'] : [])],
    });
    activeBrowsers.add(browser);
    const context = await browser.newContext({ acceptDownloads: false, serviceWorkers: 'block' });
    await context.routeWebSocket('**/*', (socket) => socket.close());
    if (protectedMode) await context.addInitScript(() => {
      Object.defineProperty(window, 'open', {
        value: () => null, configurable: false, writable: false,
      });
    });
    const page = await context.newPage();
    return { browser, context, page, profile };
  } catch {
    await rm(profile, { recursive: true, force: true });
    throw new Error('LOCAL_BROWSER_UNAVAILABLE');
  }
}

async function runCase(name, protectedMode) {
  const state = await launch(protectedMode);
  const { browser, context, page, profile } = state;
  const pageTargets = [];
  const workerTargets = [];
  const actions = [];
  const seenWorkers = new Set();
  const browserIntercepts = [];
  let closePromise;
  let fixtureError = null;
  let output = null;
  let startup = null;
  let openDescriptor = null;
  let phase = 'browser_cdp';
  try {
    const root = await browser.newBrowserCDPSession();
    const { arguments: commandLine } = await root.send('Browser.getBrowserCommandLine');
    startup = { node: process.versions.node, chromium: browser.version(),
      blockNewWebContents: commandLine.includes('--block-new-web-contents'),
      disablePopupBlocking: commandLine.includes('--disable-popup-blocking') };
    if (protectedMode) {
      // The companion capability probe demonstrated browser-level coverage.
      // Add that layer too; it is not a substitute for zero page creation.
      root.on('Fetch.requestPaused', (event) => {
        const metadata = { requestId: event.requestId,
          path: new URL(event.request.url).pathname, resourceType: event.resourceType };
        const forbidden = metadata.path.startsWith('/probe/');
        browserIntercepts.push({ path: metadata.path, resourceType: metadata.resourceType, forbidden });
        root.send(forbidden ? 'Fetch.failRequest' : 'Fetch.continueRequest',
          forbidden ? { requestId: metadata.requestId, errorReason: 'BlockedByClient' }
            : { requestId: metadata.requestId }).catch(() => {
          actions.push('FETCH_COMMAND_FAILED_CLOSE_BROWSER');
          closePromise ??= browser.close();
        });
      });
      await root.send('Fetch.enable', { patterns: [{ urlPattern: '*', requestStage: 'Request' }] });
    }
    const primary = await context.newCDPSession(page);
    const { targetInfo: initial } = await primary.send('Target.getTargetInfo');
    const blockWorker = (session, { targetInfo, waitingForDebugger }) => {
      if (!['worker', 'shared_worker', 'service_worker'].includes(targetInfo.type)
        || seenWorkers.has(targetInfo.targetId)) return;
      seenWorkers.add(targetInfo.targetId);
      workerTargets.push({ type: targetInfo.type, waitingForDebugger });
      actions.push('PAUSED_WORKER_CLOSE');
      session.send('Target.closeTarget', { targetId: targetInfo.targetId }).then((result) => {
        if (!result.success) closePromise ??= browser.close();
      }).catch(() => { closePromise ??= browser.close(); });
    };
    // Discovery is also used in the unprotected positive controls, but does not
    // enforce a deny there: their purpose is to prove requests reach the server.
    root.on('Target.targetCreated', ({ targetInfo }) => {
      if (targetInfo.type === 'page' && targetInfo.targetId !== initial.targetId) {
        pageTargets.push({ type: targetInfo.type });
        if (protectedMode) {
          actions.push('UNEXPECTED_PAGE_CLOSE_BROWSER');
          closePromise ??= browser.close();
        }
      }
    });
    phase = 'discovery';
    await root.send('Target.setDiscoverTargets', { discover: true });
    if (protectedMode) {
      phase = 'auto_attach';
      root.on('Target.attachedToTarget', (event) => blockWorker(root, event));
      await root.send('Target.setAutoAttach', {
        autoAttach: true, waitForDebuggerOnStart: true, flatten: true,
        filter: [{ type: 'browser', exclude: true }, { type: 'tab', exclude: true }, {}],
      });
      const related = await browser.newBrowserCDPSession();
      // Browser auto-attach covers shared workers; the separate related-target
      // session covers dedicated workers. Neither is ever resumed here.
      related.on('Target.attachedToTarget', (event) => blockWorker(related, event));
      phase = 'related_attach';
      await related.send('Target.autoAttachRelated', {
        targetId: initial.targetId, waitForDebuggerOnStart: true,
        filter: [{ type: 'browser', exclude: true }, { type: 'tab', exclude: true }, {}],
      });
    }
    phase = 'fixture_navigation';
    const setupStart = requests.length;
    await page.goto(`${origin}/fixture/${name}`);
    const setupRequests = requests.slice(setupStart);
    openDescriptor = await page.evaluate(() => {
      const descriptor = Object.getOwnPropertyDescriptor(window, 'open');
      return { writable: descriptor.writable, configurable: descriptor.configurable };
    });
    const start = requests.length;
    phase = 'fixture_execution';
    try {
      output = await page.evaluate(({ name, origin }) => {
        const url = `${origin}/probe/${name}`;
        if (name === 'a') {
          return { returnedNull: window.open(url) === null };
        }
        if (name === 'b') {
          const popup = window.open('about:blank');
          if (popup) popup.document.write(`<script>fetch(${JSON.stringify(url)})<\/script>`);
          return { returnedNull: popup === null };
        }
        if (name === 'c') {
          const link = document.createElement('a');
          link.href = url;
          link.target = '_blank';
          document.body.append(link);
          link.click();
        } else if (name === 'd') {
          const form = document.createElement('form');
          form.action = url;
          form.method = 'GET';
          form.target = '_blank';
          document.body.append(form);
          form.submit();
        } else if (name === 'e-worker') {
          globalThis.fixtureWorker = new Worker(URL.createObjectURL(new Blob([
            `fetch(${JSON.stringify(url)})`,
          ], { type: 'text/javascript' })));
        } else if (name === 'e-shared') {
          globalThis.fixtureWorker = new SharedWorker(URL.createObjectURL(new Blob([
            `fetch(${JSON.stringify(url)})`,
          ], { type: 'text/javascript' })));
        }
        const descriptor = Object.getOwnPropertyDescriptor(window, 'open');
        return { openWritable: descriptor.writable, openConfigurable: descriptor.configurable };
      }, { name, origin });
    } catch {
      fixtureError = 'FIXTURE_INTERRUPTED';
    }
    await wait(700);
    if (closePromise) await closePromise;
    const actualRequests = requests.slice(start);
    const received = actualRequests.filter((request) => request.path.startsWith('/probe/'));
    const workerObserved = !name.startsWith('e-') || workerTargets.some((target) => target.waitingForDebugger);
    const ok = protectedMode ? received.length === 0 && pageTargets.length === 0 && workerObserved
      : received.length > 0 && pageTargets.length > 0;
    const row = { name, mode: protectedMode ? 'protected' : 'control', startup, openDescriptor, received,
      setupRequests, actualRequests, newPageTargets: pageTargets.length,
      workerTargets, browserIntercepts, actions, output, fixtureError, ok };
    rows.push(row);
    console.log(JSON.stringify(row));
  } catch (error) {
    const labels = ['Invalid parameters', 'Target closed', 'closed', 'Protocol error', 'Timeout'];
    console.log(JSON.stringify({ name, phase, error: 'CASE_SETUP_FAILED', pageTargets, actions,
      networkCode: String(error.message).match(/net::ERR_[A-Z_]+/)?.[0] ?? null,
      categories: labels.filter((label) => String(error.message).includes(label)) }));
    throw new Error('LOCAL_CASE_FAILED');
  } finally {
    await browser.close();
    activeBrowsers.delete(browser);
    await rm(profile, { recursive: true, force: true });
    console.log(JSON.stringify({ name, profileRemoved: !existsSync(profile) }));
  }
}

async function browserFetchProbe() {
  const { browser, page, profile } = await launch(false);
  try {
    const session = await browser.newBrowserCDPSession();
    const intercepted = [];
    const decisions = [];
    // Adapter for synthetic local events: only request ID/path/type survive.
    session.on('Fetch.requestPaused', (event) => {
      const metadata = { requestId: event.requestId,
        path: new URL(event.request.url).pathname, resourceType: event.resourceType };
      const forbidden = metadata.path.startsWith('/probe/');
      intercepted.push({ path: metadata.path, resourceType: metadata.resourceType, forbidden });
      decisions.push(session.send(forbidden ? 'Fetch.failRequest' : 'Fetch.continueRequest',
        forbidden ? { requestId: metadata.requestId, errorReason: 'BlockedByClient' }
          : { requestId: metadata.requestId }).then(() => true, () => false));
    });
    let available = false;
    try {
      await session.send('Fetch.enable', { patterns: [{ urlPattern: '*', requestStage: 'Request' }] });
      available = true;
    } catch {
      console.log(JSON.stringify({ probe: 'browser-Fetch', available: false,
        error: 'BROWSER_FETCH_UNAVAILABLE', coverage: 'NOT_AVAILABLE' }));
    }
    if (available) {
      await page.goto(`${origin}/fixture/browser-fetch`);
      const start = requests.length;
      await page.evaluate((origin) => {
        window.open(`${origin}/probe/browser-popup`);
        globalThis.fetchProbeWorker = new Worker(URL.createObjectURL(new Blob([
          `fetch(${JSON.stringify(`${origin}/probe/browser-worker`)})`,
        ], { type: 'text/javascript' })));
        globalThis.fetchProbeShared = new SharedWorker(URL.createObjectURL(new Blob([
          `fetch(${JSON.stringify(`${origin}/probe/browser-shared`)})`,
        ], { type: 'text/javascript' })));
      }, origin);
      await wait(1000);
      const succeeded = await Promise.all(decisions);
      const received = requests.slice(start);
      const coverage = ['browser-popup', 'browser-worker', 'browser-shared'].map((name) => ({
        name,
        intercepted: intercepted.some((event) => event.path === `/probe/${name}` && event.forbidden),
        serverReceived: received.some((request) => request.path === `/probe/${name}`),
      }));
      await session.send('Fetch.disable');
      console.log(JSON.stringify({ probe: 'browser-Fetch', available: true, coverage,
        intercepted, actualRequests: received, commandsSucceeded: succeeded.every(Boolean) }));
    }
  } finally {
    await browser.close();
    activeBrowsers.delete(browser);
    await rm(profile, { recursive: true, force: true });
  }
}

try {
  await browserFetchProbe();
  for (const name of ['a', 'b', 'c', 'd', 'e-worker', 'e-shared']) await runCase(name, true);
  for (const name of ['a', 'b']) await runCase(name, false);
  console.log(JSON.stringify({ summary: rows.length, passed: rows.filter((row) => row.ok).length,
    failed: rows.filter((row) => !row.ok).length }));
  process.exitCode = rows.every((row) => row.ok) ? 0 : 1;
} catch {
  console.log(JSON.stringify({ error: 'LOCAL_PROBE_FAILED' }));
  process.exitCode = 2;
} finally {
  for (const browser of activeBrowsers) await browser.close();
  server.closeAllConnections();
  await new Promise((resolve) => server.close(resolve));
}
