import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { Agent, AgentError, Policy, FrameOwnership, adaptProtocol, ORIGIN, FIELDS,
  canonical, fingerprint, callbackURL, readback, validateForm } from '../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';

function meta(path, method = 'GET', extra = {}) {
  return { ...adaptProtocol({ requestId: 'r', frameId: 'main', resourceType: 'Document',
    request: { url: ORIGIN + path, method } }).metadata, ...extra };
}
const callback = `${ORIGIN}/wicket/page?50-2.IBehaviorListener.0-form-field`;
const action = `${ORIGIN}/wicket/page?50-2.IFormSubmitListener-form`;
const run = `${ORIGIN}/overview/1921?50-2.ILinkListener-run`;
const policy = (phase) => Object.assign(new Policy([1921]), { phase });

for (const [name, path, extra] of [
  ['external download', '/file', { host: 'download.tizen.org' }],
  ['http', '/build/1', { protocol: 'http:' }],
  ['websocket', '/build/1', { resource_type: 'WebSocket' }],
  ['rest', '/rest/version', {}], ['log', '/build/1/log', {}],
  ['html report', '/build/1/html_report', {}], ['artifact', '/build/1/artifacts/x', {}],
  ...['promote', 'cancel', 'stop', 'rerun', 'delete', 'abort'].map((word) =>
    [word, `/wicket/page?50-2.ILinkListener-content-buildHead-${word}`, {}]),
  ['form cancel', '/wicket/page?50-2.ILinkListener-form-cancel', {}],
  ['307', '/build/1', { response_status: 307 }],
  ['308', '/build/1', { response_status: 308 }],
]) test(`permanent deny ${name}`, () => {
  const p = policy('read'); p.active.add('r');
  p.refresh.add(ORIGIN + path);
  assert.equal(p.allow(meta(path, 'GET', extra), 'r'), false);
});

for (const [phase, path, method] of [
  ['idle', '/styles/main.css?v=7', 'GET'], ['login', '/signin', 'GET'],
  ['login', '/signin?12-1.IFormSubmitListener-form', 'POST'],
  ['login', '/', 'GET'], ['login', '/overview/0', 'GET'],
  ['read', '/build/1', 'GET'], ['read', '/build/1/overview', 'GET'],
  ['read', '/build/1/variables', 'GET'], ['read', '/build/1/step_status', 'GET'],
  ['read', '/overview/1921', 'GET'], ['open_form', '/wicket/page?50', 'GET'],
  ['fill', '/wicket/page?50-3', 'GET'],
]) test(`allow ${phase} ${method} ${path}`, () => assert.equal(policy(phase).allow(meta(path, method)), true));

for (const path of ['/build/1?x=1', '/overview/1922', '/styles/x?Listener=x', '/styles/x?v=a',
  '/wicket/page?1-1.IBehaviorListener-dragDrop', '/wicket/page?1-1.IBehaviorListener-loadPopup',
  '/wicket/page?1-1.IBehaviorListener-unloadPopup', '/wicket/page?1-1.IBehaviorListener-quicksearch']) {
  test(`unregistered denied ${path}`, () => assert.equal(policy('read').allow(meta(path)), false));
}
test('stage-specific navigation never escapes phase', () => {
  assert.equal(policy('idle').allow(meta('/signin')), false);
  assert.equal(policy('read').allow(meta('/signin', 'POST')), false);
  assert.equal(policy('login').allow(meta('/build/1')), false);
  const p = policy('read'); p.submitUrl = action; p.beginField(callback);
  assert.equal(p.allow(meta(action.slice(ORIGIN.length), 'POST')), false);
  assert.equal(p.allow(meta(callback.slice(ORIGIN.length), 'POST')), false);
});
test('exact run and exact refresh registrations, no prefix acceptance', () => {
  const p = policy('open_form'); p.runUrl = run;
  assert.equal(p.allow(meta(run.slice(ORIGIN.length) + 'x')), false);
  assert.equal(p.allow(meta(run.slice(ORIGIN.length))), true);
  assert.equal(p.allow(meta(run.slice(ORIGIN.length))), false);
  const refresh = `${ORIGIN}/build/1?1-1.IBehaviorListener-refresh&action=ajaxRefresh`;
  p.refresh.add(refresh);
  assert.equal(p.allow(meta(refresh.slice(ORIGIN.length))), true);
  assert.equal(p.allow(meta(refresh.slice(ORIGIN.length) + '0')), false);
});
test('one callback per field, old version and other field denied', () => {
  const p = policy('fill'); p.beginField(callback);
  assert.equal(p.allow(meta(callback.slice(ORIGIN.length) + 'x', 'POST')), false);
  assert.equal(p.allow(meta(callback.slice(ORIGIN.length), 'POST'), 'field'), true);
  assert.equal(p.allow(meta(callback.slice(ORIGIN.length), 'POST')), false);
  p.endField(); p.beginField(callback.replace('50-2', '50-3'));
  assert.equal(p.allow(meta(callback.slice(ORIGIN.length), 'POST')), false);
  assert.equal(p.allow(meta(callback.replace('50-2', '50-3').slice(ORIGIN.length), 'POST')), true);
});
test('stop in value not listener component is allowed', () => {
  const p = policy('read');
  const url = `${ORIGIN}/build/1?1-1.IBehaviorListener-refresh&action=ajaxRefresh&value=stop`;
  p.refresh.add(url);
  assert.equal(p.allow(meta(url.slice(ORIGIN.length))), true);
});
test('callback shape fails closed', () => {
  assert.throws(() => policy('fill').beginField('invalid'), { code: 'QB_FORM_CHANGED' });
  for (const bad of ['page?1', 'https://example.invalid/wicket/page?1-1.IBehaviorListener.0-x']) {
    assert.throws(() => callbackURL(`wicketAjaxPost('${bad}', 0)`, ORIGIN + '/wicket/page?50'),
      { code: 'QB_FORM_CHANGED' });
  }
});
test('two form instances each have exactly one release, response does not consume it', () => {
  const p = policy('submit');
  for (let i = 0; i < 2; i++) {
    p.newForm(); p.submitUrl = action;
    assert.equal(p.released, false);
    assert.equal(p.allow(meta(action.slice(ORIGIN.length), 'POST'), 'r'), true);
    p.active.add('r');
    assert.equal(p.allow(meta(action.slice(ORIGIN.length), 'POST', { response_status: 302 }), 'r'), true);
    assert.equal(p.allow(meta(action.slice(ORIGIN.length), 'POST')), false);
    assert.equal(p.allow(meta('/build/2')), true);
    assert.equal(p.released, true);
  }
});
test('302 next hop is judged independently and 307/308 preserve released', () => {
  const p = policy('submit'); p.submitUrl = action;
  p.allow(meta(action.slice(ORIGIN.length), 'POST'), 'r'); p.active.add('r');
  for (const status of [307, 308]) assert.equal(p.allow(meta('/build/2', 'POST', { response_status: status }), 'r'), false);
  assert.equal(p.released, true);
  assert.equal(p.allow(meta('/rest/builds')), false);
  assert.equal(p.allow(meta('/build/2', 'GET', { response_status: 200 }), 'unknown'), false);
});
test('protocol adapter forwards only metadata even when request contains credentials', () => {
  const result = adaptProtocol({ requestId: 'r', frameId: 'm', resourceType: 'Document',
    request: { url: ORIGIN + '/signin', method: 'POST', headers: { Cookie: 'cookie-secret', Authorization: 'auth-secret' },
      postData: 'password=password-secret', postDataEntries: [{ bytes: 'secret' }] },
    responseHeaders: [{ name: 'Set-Cookie', value: 'secret' }] });
  assert.deepEqual(Object.keys(result.metadata).sort(), ['method', 'protocol', 'host', 'path', 'query',
    'resource_type', 'redirect_source', 'response_status'].sort());
  assert.doesNotMatch(JSON.stringify(result), /secret|password|Cookie|Authorization/);
  assert.throws(() => adaptProtocol({ request: { url: 'invalid secret' } }),
    { message: 'QB_BROWSER_UNAVAILABLE' });
});
test('frame ownership is closed and descendants revoked on detach/navigation', () => {
  const f = new FrameOwnership({ frame: { id: 'm' }, childFrames: [{ frame: { id: 'c' } }] });
  assert.equal(f.has('c'), true); assert.equal(f.has(null), false); assert.equal(f.has('popup'), false);
  f.attach('grandchild', 'c'); f.attach('foreign', 'popup'); assert.equal(f.has('foreign'), false);
  f.detach('c'); assert.equal(f.has('grandchild'), false);
  f.navigate({ id: 'n' }); assert.equal(f.has('m'), false); assert.equal(f.has('n'), true);
});

function form() {
  return { heading: true, base: ORIGIN + '/wicket/page?50', action,
    rows: [{ label: 'PROJECT_NAME', viewers: ['Tizen'], controls: [] }, ...FIELDS.map((label) => ({
      label, viewers: [], controls: ['CHILD_CONFIGURATIONS', 'TARGET_IMAGE'].includes(label)
        ? ['recorder', 'choices', 'selection'].map((role) => ({ role, value: '', options: [],
          callback: `wicketAjaxPost('${callback}', 0)` }))
        : [{ tag: 'INPUT', type: 'text', value: label, options: [], callback: `wicketAjaxPost('${callback}', 0)` }],
    }))] };
}
test('form exact label/role closure and project identity', () => {
  assert.equal(Object.keys(validateForm(form(), 'Tizen')).length, 13);
  for (const mutation of [f => f.rows.pop(), f => f.rows.push(f.rows[1]),
    f => f.rows[1].controls.push(f.rows[1].controls[0]), f => f.rows[0].viewers[0] = 'Other',
    f => f.rows[1].controls[0].callback = 'unknown()']) {
    const f = form(); mutation(f); assert.throws(() => validateForm(f, 'Tizen'), { code: 'QB_FORM_CHANGED' });
  }
});
test('readback records text/checkbox/select/palette and validates recorder', () => {
  const f = form(); const p = f.rows.find(r => r.label === 'CHILD_CONFIGURATIONS');
  p.controls[0].value = Buffer.from('standard-armv7l').toString('hex');
  p.controls[2].options = [{ text: 'standard-armv7l' }];
  f.rows[1].controls[0] = { ...f.rows[1].controls[0], tag: 'SELECT', options: [{ text: 'selected', selected: true }] };
  f.rows[2].controls[0] = { ...f.rows[2].controls[0], type: 'checkbox', checked: false };
  const values = readback(f, 'Tizen');
  assert.equal(values['BUILD_TYPE/value'], 'selected'); assert.equal(values['REPO_TYPE/value'], false);
  assert.deepEqual(values['CHILD_CONFIGURATIONS/selection'], ['standard-armv7l']);
  assert.match(fingerprint(values), /^[a-f0-9]{64}$/);
  assert.equal(fingerprint(values), fingerprint(Object.fromEntries(Object.entries(values).reverse())));
  p.controls[0].value = '00'; assert.throws(() => readback(f, 'Tizen'), { code: 'QB_FORM_READBACK_MISMATCH' });
  p.controls[0].value = 'ff'; assert.throws(() => readback(f, 'Tizen'), { code: 'QB_FORM_READBACK_MISMATCH' });
});
test('failed fill and fingerprint mismatch invalidate form until new open', async () => {
  const a = new Agent({ policy: new Policy(), page: {}, close: async () => {} });
  a.login = async () => ({}); a.openForm = async () => ({});
  a.fill = async () => { throw new AgentError('QB_FORM_VALUE_UNAVAILABLE', 'SNAPSHOT_NUM'); };
  assert.deepEqual(await a.command({ command: 'submit' }), { ok: false, error: 'AGENT_PHASE' });
  await a.command({ command: 'login', projects: [], login_timeout_seconds: 1 });
  await a.command({ command: 'open_form', overview_id: 1921 });
  assert.equal((await a.command({ command: 'fill' })).ok, false);
  assert.equal((await a.command({ command: 'submit' })).error, 'AGENT_PHASE');
  await a.command({ command: 'open_form' }); a.fill = async () => ({});
  await a.command({ command: 'fill' });
  a.snapshot = async () => form(); a.currentProject = { project_name: 'Tizen' };
  assert.equal((await a.command({ command: 'submit', fingerprint: 'wrong' })).error, 'QB_FORM_CHANGED');
  assert.equal(a.policy.released, false);
  assert.equal((await a.command({ command: 'submit' })).error, 'AGENT_PHASE');
  await a.command({ command: 'open_form' }); assert.equal(a.state, 'form');
});
test('read checks exact URL and build id and returns actual HTTP status', async () => {
  let redirect = null;
  const page = { goto: async () => ({ status: () => 503, request: () => ({ redirectedFrom: () => redirect }) }), url: () => ORIGIN + '/build/1',
    evaluate: async () => '<p>safe</p>' };
  const a = new Agent({ policy: new Policy(), page });
  a.buildId = async () => '1'; a.registerRefresh = async () => {};
  assert.equal((await a.read('/build/1')).status, 503);
  redirect = {}; await assert.rejects(a.read('/build/1'), { code: 'QB_READ_REDIRECTED' }); redirect = null;
  a.buildId = async () => '2'; await assert.rejects(a.read('/build/1'), { code: 'QB_READ_ID_MISMATCH' });
  page.url = () => ORIGIN + '/build/1/overview';
  await assert.rejects(a.read('/build/1'), { code: 'QB_READ_REDIRECTED' });
  await assert.rejects(a.read('/build/1?x=1'), { code: 'AGENT_PHASE' });
});
test('source guards: no HTTP client, credential extraction, debug switch, or login interactions', () => {
  const source = readFileSync(new URL('../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs', import.meta.url), 'utf8');
  assert.doesNotMatch(source, /page\.request|context\.request|request\.newContext|\.cookies\(|storageState|ignoreHTTPSErrors|DEBUG\s*=\s*['"]pw/);
  const login = source.split('  async login(timeout) {')[1].split('  async registerRefresh()')[0];
  assert.doesNotMatch(login, /\b(click|fill|press|type|evaluate)\(/);
  const outside = source.slice(source.indexOf('export class Policy'));
  assert.doesNotMatch(outside, /\b(headers|postData|postDataEntries)\b/);
  const main = source.split('async function main()')[1];
  assert.doesNotMatch(main, /diagnostic|useBrowserFetch|testOptions/);
  assert.match(source, /--block-new-web-contents/);
  assert.equal(canonical({ z: 1, a: 2 }), '{"a":2,"z":1}');
});

test('every command outside its permitted phase rejects before any method call', async () => {
  const allowed = { login: ['new'], read: ['ready', 'form', 'filled', 'invalid'], open_form: ['ready', 'form', 'filled', 'invalid'],
    fill: ['form'], submit: ['filled'] };
  for (const state of ['new', 'ready', 'form', 'filled', 'invalid', 'closed']) {
    for (const command of [...Object.keys(allowed), 'unknown']) {
      if (allowed[command]?.includes(state)) continue;
      const a = new Agent({ policy: new Policy(), page: {} }); a.state = state;
      for (const method of ['login', 'read', 'openForm', 'fill', 'submit']) a[method] = () => assert.fail('executed invalid command');
      assert.deepEqual(await a.command({ command }), { ok: false, error: 'AGENT_PHASE' });
    }
  }
});

test('read remains available after submit but navigation invalidates the old form', async () => {
  const a = new Agent({ policy: new Policy(), page: {} });
  a.read = async () => ({ status: 200, html_redacted: '<p>safe</p>' });
  for (const state of ['invalid', 'form', 'filled']) {
    a.state = state;
    assert.equal((await a.command({ command: 'read', path: '/build/12' })).status, 200);
    assert.equal((await a.command({ command: 'submit' })).error, 'AGENT_PHASE');
  }
});

test('fill reads current callbacks and freezes selected snapshot without setting it', async () => {
  const f = form();
  const requested = Object.fromEntries(FIELDS.map(name => [name, name]));
  Object.assign(requested, { SNAPSHOT_NUM: '@freeze', CHILD_CONFIGURATIONS: ['standard-armv7l:aarch64:x86_64'],
    TARGET_IMAGE: [], 'Immediate Stop With Error': true, 'Build Package List': 'pkg/name@abc',
    'BUILD NOTES': 'clang-fix-campaign request=synthetic', 'Add Package List': '', 'Remove Package List': '' });
  const calls = [];
  const p = new Policy();
  for (const row of f.rows.slice(1)) {
    if (row.label === 'SNAPSHOT_NUM') Object.assign(row.controls[0], { tag: 'SELECT',
      options: [{ text: 'older', selected: false }, { text: 'chosen', selected: true }] });
    if (row.label === 'Immediate Stop With Error') Object.assign(row.controls[0], { type: 'checkbox', checked: false });
    if (row.label === 'CHILD_CONFIGURATIONS') {
      row.controls[0].value = Buffer.from(requested[row.label][0]).toString('hex');
      row.controls[2].options = [{ text: requested[row.label][0] }];
    }
  }
  const a = new Agent({ policy: p, page: {}, failure: null }); a.currentProject = { project_name: 'Tizen' };
  a.snapshot = async () => f;
  a.fieldRow = name => ({ locator: () => ({ locator: () => ({
    fill: async value => { calls.push([name, 'fill']); f.rows.find(r => r.label === name).controls[0].value = value; },
    setChecked: async value => { calls.push([name, 'checked']); f.rows.find(r => r.label === name).controls[0].checked = value;
      p.fieldFinished = true; p.lastActivity = Date.now() - 1500; },
    selectOption: async () => assert.fail('frozen snapshot must not be set'),
    dispatchEvent: async () => { calls.push([name, 'change']); p.fieldFinished = true; p.lastActivity = Date.now() - 1500; },
  }) }) });
  const result = await a.fill(requested);
  assert.equal(result.readback['SNAPSHOT_NUM/value'], 'chosen');
  assert.equal(result.snapshot_option_count, 2);
  assert.equal(calls.some(([name]) => name === 'SNAPSHOT_NUM'), false);
  assert.equal(new Set(calls.map(([name]) => name)).size, 11);
  assert.equal(result.fingerprint, fingerprint(result.readback));
});
