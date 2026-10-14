// Synthetic blueprint, not serialized live-12 HTML. No non-loopback listener.
import { execFileSync } from 'node:child_process';
import { createHash, X509Certificate } from 'node:crypto';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { createServer } from 'node:https';
import { createInterface } from 'node:readline';
import { pathToFileURL } from 'node:url';
import { FIELDS, ORIGIN } from '../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';

export const PROJECT = { overview_id: 1917,
  configuration_path: 'root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER',
  project_name: 'Tizen-Base-Toolchain' };
export const ARCH = 'standard-armv7l:aarch64:x86_64';
export const SNAPSHOT = 'tizen-base-toolchain_20260924.094908';
export const VALUES = { BUILD_TYPE: 'Full', REPO_TYPE: 'ALL', BUILD_REFERENCE: 'Ref. Snapshot',
  SNAPSHOT_NUM: SNAPSHOT, PROJECT_BRANCH: 'tizen_base', 'Immediate Stop With Error': true,
  CHILD_CONFIGURATIONS: [ARCH], TARGET_IMAGE: [], 'Add Package List': '',
  'Remove Package List': '', 'Build Package List': 'package@' + 'a'.repeat(40),
  'BUILD NOTES': 'clang-fix-campaign request=rehearsal-local' };
const escape = value => String(value).replace(/[&<>"']/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
})[char]);
const hex = value => Buffer.from(value).toString('hex');
const PALETTES = new Set(['CHILD_CONFIGURATIONS', 'TARGET_IMAGE']);
const scripts = `<script>String.prototype.trim=function(){return this.replace(/^\\s+|\\s+$/, '');};
  window.onCopyClipboardLinkDomReady=function(){};</script>`;
const page = (body, title = 'QuickBuild', extra = '') => `<!doctype html><html><head>
  <meta charset="utf-8"><title>${escape(title)}</title><link rel="icon" href="data:,"></head>
  <body><span>Welcome! LocalTester</span><a href="/signout">Sign Out</a>${body}${scripts}${extra}</body></html>`;
const breadcrumb = path => `<div id="breadcrumb">${path.split('/').map(part => `<span>${escape(part)}</span>`).join('')}</div>
  <script>onCopyClipboardLinkDomReady('copy', '${path}')</script>`;
const columns = values => '<tr>' + values.map(text => `<td>${escape(text).replaceAll('\n', '<br>')}</td>`).join('') + '</tr>';

export function overview(id, status = 'Running', mode = '') {
  const parent = id === '1193467';
  const path = parent ? PROJECT.configuration_path : PROJECT.configuration_path.replace(/TRIGGER$/, 'build');
  const config = parent ? 1917 : 1915;
  const nav = `<a class="nav-link">Build (id:${id})</a>`;
  return page(`${mode === 'insert-nav' ? '' : nav}${breadcrumb(path)}
    <ul>${[['ConfigurationOverview', 'overview'], ['PipelinePage', 'pipeline'], ['ChildrenPage', 'children']]
      .map(([cls, kind]) => `<li class="tab-${cls}"><a class="nav-link" href="../../${kind}/${config}">${kind}</a></li>`).join('')}</ul>
    <div class="build-header"><span>${path.replace('root/CI_TIZEN/', '').replaceAll('/', '_')}_20261014</span></div>
    <section class="build-summary"><div class="box-head">Summary</div><table><thead><tr>
    <th>Id</th><th>Status</th><th>Triggered By</th></tr></thead><tbody><tr><td>${id}</td>
    <td id="status">${status}</td><td>LocalTester</td></tr></tbody></table></section>
    ${status === 'Failed' ? '<div class="build-errors"><div class="box-head">Error Message</div><div class="box-body">synthetic build failure</div></div>' : ''}
    ${parent ? `<h3>Child Build</h3><table><thead><tr>${['Repository-Architecture', 'QB Build URL', 'Build Result', 'Build Profiling']
      .map(text => `<th>${text}</th>`).join('')}</tr></thead><tbody><tr><td>${ARCH}</td>
      <td><a href="${ORIGIN}/build/1193469">1193469</a></td><td>${status === 'Successful' ? 'SUCCESSFUL' : 'RUNNING'}</td><td></td></tr></tbody></table>` : ''}`,
  'QuickBuild', mode === 'insert-nav' ? `<script>document.body.insertAdjacentHTML('afterbegin', ${JSON.stringify(nav)})</script>`
    : mode === 'change-status' ? '<script>document.querySelector("#status").textContent="Successful"</script>' : '');
}

export function variables(id, submitted = VALUES) {
  const parent = id === '1193467';
  const values = parent ? [
    ['QB_TRIGGER_ID', '', id],
    ['BUILD_PKG_LIST_MODIFY', 'Build Package List', submitted['Build Package List']],
    ['BUILD_NOTES', 'BUILD NOTES', submitted['BUILD NOTES']],
    ['BUILD_TYPE', 'BUILD_TYPE', 'Full'], ['BUILD_REFERENCE', 'BUILD_REFERENCE', 'Ref. Snapshot'],
    ['SNAPSHOT_NUM', 'SNAPSHOT_NUM', SNAPSHOT], ['PROJECT_BRANCH', 'PROJECT_BRANCH', 'tizen_base'],
    ['FAIL_FAST', 'Immediate Stop With Error', 'yes'], ['CHILD_CONFIGURATIONS', '', ARCH],
  ] : [
    ['QB_TRIGGER_ID', '', id], ['TRIGGER_ID', '', '1193467'],
    ['BUILD_PKG_LIST', '', submitted['Build Package List'] + '\nother/package@' + 'b'.repeat(40)],
    ['FAIL_FAST', '', 'yes'], ['REPO_ARCH', '', ARCH], ['CHILD_CONFIGURATIONS', '', ARCH],
    ['EACH_GBS_BUILD_STATUS', '', ''], ['BUILD_REFERENCE', '', 'Ref. Snapshot'],
    ['SNAPSHOT_NUM_URL', '', `http://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/${SNAPSHOT}`],
  ];
  return page(`<a class="nav-link">Build (id:${id})</a><table><thead><tr><td>Name</td><td>Display Name</td><td>Value</td></tr></thead>
    <tbody>${values.map(columns).join('')}</tbody></table>`);
}

export function form(version, { extraField = false, refresh = true, noNavigation = false, callbackMismatch = false } = {}) {
  const rows = FIELDS.map((name, i) => {
    const base = `form:field:${i}`;
    const callback = escape(`wicketAjaxPost('page?${version}-1.IBehaviorListener.0-form-field-${i}', this)`);
    let control;
    if (PALETTES.has(name)) {
      const opts = VALUES[name].map(value => `<option value="${hex(value)}">${escape(value)}</option>`).join('');
      control = `<input type="hidden" name="${base}:palette:recorder" value="${VALUES[name].map(hex).join('')}" onchange="${callback}">
        <select name="${base}:choices" multiple></select><select name="${base}:selection" multiple>${opts}</select>`;
    } else if (i < 5) {
      const options = name === 'BUILD_TYPE' ? ['Full', 'Partial'] : [VALUES[name]];
      control = `<select name="${base}:input" onchange="${callback}">${options.map((value, j) =>
        `<option value="opaque-${i}-${j}">${escape(value)}</option>`).join('')}</select>`;
    } else if (name === 'Immediate Stop With Error') {
      control = `<input type="checkbox" name="${base}:input" checked onchange="${callback}">`;
    } else control = `<textarea name="${base}:input" onchange="${callback}"></textarea>`;
    return `<tr data-field="${escape(name)}"><td><span class="form-label">${escape(name)}</span></td><td class="value">${control}</td></tr>`;
  }).join('');
  return page(`<h1>Specify Build Options</h1><form method="POST" action="page?${version}-1.IFormSubmitListener-form">
    <table><tr><td><span class="form-label">PROJECT_NAME</span></td><td class="value"><div class="property-viewer"> \n${PROJECT.project_name}\t </div></td></tr>
    ${rows}${extraField ? '<tr><td><span class="form-label">EXTRA</span></td><td class="value"><input></td></tr>' : ''}
    </table><button type="submit">Ok</button></form>`, 'QuickBuild', `<script>
    window.wicketAjaxPost = function(url, element) {
      const row=element.closest('tr');
      ${callbackMismatch ? "url=url.replace('field-0','field-99');" : ''}
      fetch(url+'&random='+Math.random(), {method:'POST', body:new URLSearchParams({field:row.dataset.field,value:element.value})})
      .then(r=>r.json()).then(reply=>{
        document.querySelector('form').action='page?'+reply.version+'-1.IFormSubmitListener-form';
        document.querySelectorAll('tr[data-field]').forEach((row,i)=>row.querySelector('[onchange]').setAttribute('onchange',
          "wicketAjaxPost('page?"+reply.version+"-1.IBehaviorListener.0-form-field-"+i+"', this)"));
      });
    };
    ${refresh ? "setInterval(()=>fetch('page?41-1.IBehaviorListener.0-ajaxRefresh&random='+Math.random()).catch(()=>{}), 350);" : ''}
    ${noNavigation ? "document.querySelector('form').addEventListener('submit', event=>{event.preventDefault();const f=event.target;fetch(f.action,{method:'POST',body:new URLSearchParams(new FormData(f))});});" : ''}
    </script>`);
}

export async function fakeQuickBuild({ mode = 'build', compare = '', childStatus = 'Running' } = {}) {
  const directory = await mkdtemp('/dev/shm/p5q-c5a-server-');
  execFileSync('openssl', ['req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-keyout', `${directory}/key`,
    '-out', `${directory}/cert`, '-days', '1', '-subj', '/CN=quickbuild.tizen.org',
    '-addext', 'subjectAltName=DNS:quickbuild.tizen.org'], { stdio: 'ignore' });
  const cert = await readFile(`${directory}/cert`), key = await readFile(`${directory}/key`);
  const spki = createHash('sha256').update(new X509Certificate(cert).publicKey.export({ type: 'spki', format: 'der' })).digest('base64');
  const fixture = { received: [], submissions: [], version: 41, childStatus, mode, compare,
    submitted: { ...VALUES }, remembered: 'overview', builds: 0, errors: [] };
  const server = createServer({ cert, key }, (request, response) => {
    const row = { method: request.method, path: request.url, status: 200 };
    fixture.received.push(row);
    void (async () => {
      let body = '';
      for await (const part of request) body += part;
      // Synthetic fixtures only. Never reused for live requests or real credentials.
      row.body = body;
      response.setHeader('Cache-Control', 'no-store');
      response.setHeader('Content-Type', 'text/html; charset=utf-8');
      const redirect = path => { row.status = 302; response.writeHead(302, { Location: path }); response.end(); };
      const url = new URL(request.url, ORIGIN);
      if (row.method === 'GET' && url.pathname === '/signin') {
        if (fixture.loginCase === 'unregistered-landing') { redirect('/not-registered'); return; }
        if (fixture.loginCase === 'signin-with-signout') { response.end(page('<h1>Still signin</h1>')); return; }
        if (fixture.loginCase) { redirect('/dashboard'); return; }
        response.end('<!doctype html><link rel="icon" href="data:,"><form method="POST" action="/signin?0-1.IFormSubmitListener-content-form"><input name="user"><input type="password" name="password"><button>Login</button></form>');
      } else if (row.method === 'POST' && /IFormSubmitListener-content-form$/.test(url.search)) {
        row.body = '<SYNTHETIC_LOGIN_REDACTED>';
        redirect('/dashboard');
      } else if (url.pathname === '/dashboard') response.end(fixture.loginCase === 'no-signout'
        ? '<!doctype html><link rel="icon" href="data:,"><h1>Dashboard without signout</h1>'
        : page('<h1>Dashboard</h1>' + (fixture.loginCase === 'password-remains' ? '<input type="password">' : '')));
      else if (url.pathname === '/overview/1917') response.end(page(`${breadcrumb(PROJECT.configuration_path)}
        <button title="Run the configuration" onclick="var win = this.ownerDocument.defaultView || this.ownerDocument.parentWindow; if (win == window) { window.location.href='../wicket/page?41-1.ILinkListener-run'; } ;return false">Run</button>`, `QuickBuild - ${PROJECT.configuration_path}`));
      else if (row.method === 'GET' && /ILinkListener-run$/.test(url.search)) { fixture.version = 41; redirect('/wicket/page?41'); }
      else if (row.method === 'GET' && url.pathname === '/wicket/page' && /^\?\d+$/.test(url.search)) response.end(
        form(fixture.version, { noNavigation: fixture.mode === 'no-navigation', callbackMismatch: fixture.callbackMismatch }).replace('<h1>',
          url.search === '?99' ? '<div class="feedbackPanelERROR">Synthetic server error after request</div><h1>' : '<h1>'));
      else if (row.method === 'POST' && /IBehaviorListener/.test(url.search)) {
        response.setHeader('Content-Type', 'application/json');
        response.end(JSON.stringify({ version: ++fixture.version }));
      } else if (row.method === 'POST' && /IFormSubmitListener-form$/.test(url.search)) {
        const payload = Object.fromEntries(new URLSearchParams(body));
        fixture.submissions.push(payload);
        for (const name of ['Build Package List', 'BUILD NOTES']) fixture.submitted[name] = payload[`form:field:${FIELDS.indexOf(name)}:input`];
        if (fixture.mode !== 'error-no-build') fixture.builds++;
        fixture.remembered = 'variables';
        if (fixture.mode === 'build') redirect('/build/1193467');
        else if (fixture.mode === 'no-navigation') response.end(form(fixture.version));
        else redirect('/wicket/page?99');
      } else if (/^\/build\/\d+(?:\/(overview|variables|step_status))?$/.test(url.pathname)) {
        const [, , id, explicit] = url.pathname.split('/');
        if (fixture.redirectRead && id === '1193467') { redirect('/build/1193469/overview'); return; }
        if (explicit) fixture.remembered = explicit;
        const tab = explicit ?? fixture.remembered;
        if (tab === 'variables') response.end(variables(id, fixture.submitted));
        else if (tab === 'step_status') response.end(page(`<a class="nav-link">Build (id:${id})</a><div class="step failed"><div class="step-head"><span class="step-name">Build_GBS</span></div></div>`));
        else response.end(overview(id, fixture.childStatus, fixture.compare));
      } else { row.status = 404; fixture.errors.push(row); response.writeHead(404); response.end(); }
    })().catch(() => { fixture.errors.push({ category: 'FAKE_SERVER_ERROR' }); response.destroy(); });
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  fixture.overrides = { launchArgs: ['--no-proxy-server',
    `--host-resolver-rules=MAP quickbuild.tizen.org 127.0.0.1:${server.address().port}, EXCLUDE 127.0.0.1, MAP * ~NOTFOUND`,
    `--ignore-certificate-errors-spki-list=${spki}`] };
  fixture.close = async () => { server.closeAllConnections(); await new Promise(resolve => server.close(resolve)); await rm(directory, { recursive: true, force: true }); };
  return fixture;
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  const fixture = await fakeQuickBuild();
  const [config, evidence] = process.argv.slice(2);
  await writeFile(config, JSON.stringify(fixture.overrides));
  process.stdout.write('{"ready":true}\n');
  try {
    for await (const line of createInterface({ input: process.stdin })) {
      const command = JSON.parse(line);
      if (command.status) fixture.childStatus = command.status;
      if (command.mode) fixture.mode = command.mode;
      await writeFile(evidence, JSON.stringify({ received: fixture.received, submissions: fixture.submissions,
        builds: fixture.builds, errors: fixture.errors }, null, 2) + '\n');
      process.stdout.write('{"ok":true}\n');
      if (command.close) break;
    }
  } finally { await fixture.close(); }
}
