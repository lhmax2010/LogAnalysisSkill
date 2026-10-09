// Isolated manual login; secrets travel only over a private child stdin pipe.
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createInterface } from 'node:readline';
import { pathToFileURL } from 'node:url';
import assert from 'node:assert/strict';

const [playwrightPath, chromiumPath, pythonPath, receiverPath, outputPath] = process.argv.slice(2);
const base = 'https://quickbuild.tizen.org';
function loginRequestAllowed(method, target) {
  const url = new URL(target);
  if (url.origin !== base) return false;
  const login = /^\/signin\/?$/.test(url.pathname);
  const document = ['/','/overview/0','/build/1069532','/favicon.ico',
    '/build/1069540', '/build/1069540/overview', '/build/1069540/variables',
    '/build/1069532/step_status', '/build/1069540/step_status'].includes(url.pathname)
    && !url.search && !url.hash;
  return (method === 'POST' && login) || (method === 'GET'
    && (login || document || url.pathname.startsWith('/wicket/resource/')));
}
if (process.argv.includes('--policy-self-test')) {
  const cases = [
    ['GET', '/signin', true], ['POST', '/signin?0-form', true],
    ['GET', '/build/1069532', true], ['GET', '/wicket/resource/site.css', true],
    ['POST', '/build/1069532', false], ['GET', '/build/1069532?0-run', false],
    ['GET', '/rest/trigger', false], ['GET', '/wicket/page?0-run', false],
    ['GET', '/build/1069532/cancel', false], ['GET', '/build/1069540', true],
    ['GET', '/build/1069540/overview', true], ['GET', '/build/1069540/variables', true],
    ['GET', '/build/1069532/step_status', true], ['GET', '/build/1069540/step_status', true],
    ['GET', '/build/1069540?0-run', false], ['POST', '/build/1069540', false],
    ['GET', '/build/1069540/log', false], ['GET', '/build/1069540/cancel', false],
    ['DELETE', '/signin', false], ['GET', 'https://other.invalid/', false],
  ];
  for (const [method, path, expected] of cases) {
    assert.equal(loginRequestAllowed(method, new URL(path, base).href), expected);
  }
  console.log(`Browser login allowlist: ${cases.length} controls PASS; build actions rejected.`);
  process.exit(0);
}
let browser;
let profile;
let terminal;
let deadline;
try {
  console.log('先在浏览器里登录，登录后回到本终端按回车。');
  console.log('等待上限 10 分钟；不要在终端粘贴 Cookie 或密码。仅采集白名单只读页面。');
  const { chromium } = await import(pathToFileURL(playwrightPath).href);
  if (tmpdir() !== '/dev/shm') throw new Error('RAM-only temporary directory required');
  profile = await mkdtemp('/dev/shm/ef5-browser-');
  browser = await chromium.launch({
    executablePath: chromiumPath,
    headless: false,
    args: ['--disable-breakpad', '--disable-crash-reporter', '--disable-sync'],
    env: { ...process.env, TMPDIR: profile },
  });
  const context = await browser.newContext({ acceptDownloads: false, serviceWorkers: 'block' });
  await context.route('**/*', async route => {
    const request = route.request();
    // The human alone submits the sign-in form. Build operations are never allowed.
    if (loginRequestAllowed(request.method(), request.url())) {
      await route.continue();
    } else {
      await route.abort();
    }
  });
  const page = await context.newPage();
  console.log('QuickBuild: log in manually in the browser. No build actions are permitted.');
  console.log('After login, return here and press Enter. Do NOT paste any cookie or password here.');
  console.log('Waiting up to 10 minutes; session is non-persistent, with temporary files in RAM.');
  await page.goto(base + '/signin', { waitUntil: 'domcontentloaded', timeout: 60000 });
  terminal = createInterface({ input: process.stdin, output: process.stdout });
  const confirmed = await Promise.race([
    new Promise(resolve => terminal.once('line', () => resolve(true))),
    new Promise(resolve => { deadline = setTimeout(() => resolve(false), 600000); }),
  ]);
  clearTimeout(deadline);
  terminal.close();
  if (!confirmed) throw new Error('Manual login deadline reached');
  const cookies = await context.cookies(base + '/build/1069532');
  if (!cookies.length) throw new Error('No scoped cookie available');
  // Freeze all browser traffic before exporting this isolated session in memory.
  await context.unrouteAll({ behavior: 'wait' });
  await context.route('**/*', route => route.abort());
  const child = Bun.spawn([pythonPath, receiverPath, '--output', outputPath], {
    stdin: 'pipe', stdout: 'inherit', stderr: 'inherit',
  });
  child.stdin.write(JSON.stringify(cookies));
  child.stdin.end();
  const code = await child.exited;
  console.log(`Read-only probe exit=${code}; browser credentials are now discarded.`);
  process.exitCode = code;
} catch {
  console.log('Browser handoff stopped. No credential or raw browser error was printed.');
  process.exitCode = 2;
} finally {
  clearTimeout(deadline);
  terminal?.close();
  await browser?.close().catch(() => {});
  if (profile) await rm(profile, { recursive: true, force: true });
}
