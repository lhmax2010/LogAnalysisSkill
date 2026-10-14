import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { Agent, AgentError, Policy, FrameOwnership, adaptProtocol, ORIGIN, FIELDS,
  canonical, fingerprint, callbackURL, readback, validateForm, pathShape,
  destructiveListener } from '../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';

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
  assert.equal(p.allow(meta(path, 'GET', extra), 'r'), false);
});

for (const [phase, path, method] of [
  ['idle', '/styles/main.css?v=7', 'GET'], ['login', '/signin', 'GET'],
  ['login', '/signin?12-1.IFormSubmitListener-content-form', 'POST'],
  ['login', '/', 'GET'], ['login', '/overview/0', 'GET'],
  ['read', '/build/1', 'GET'], ['read', '/build/1/overview', 'GET'],
  ['read', '/build/1/variables', 'GET'], ['read', '/build/1/step_status', 'GET'],
  ['read', '/overview/1921', 'GET'], ['open_form', '/wicket/page?50', 'GET'],
  ['fill', '/wicket/page?50-3', 'GET'],
]) test(`allow ${phase} ${method} ${path}`, () => assert.equal(policy(phase).allow(meta(path, method)), true));

for (const query of ['', '0', '123']) {
  test(`registered login landing accepts query ${JSON.stringify(query)}`, () => {
    const p = policy('login');
    assert.equal(p.allow(meta('/dashboard', 'GET', { query }), 'landing'), true);
    p.active.add('landing');
    assert.equal(p.allow(meta('/dashboard', 'GET', { query, response_status: 200 }), 'landing'), true);
  });
}
for (const query of ['v=1', '1-2', '1&x=2', 'x=1', '1\n', '1.IBehaviorListener-x']) {
  test(`registered login landing rejects query ${JSON.stringify(query)}`, () => {
    assert.equal(policy('login').allow(meta('/dashboard', 'GET', { query })), false);
  });
}
for (const [name, path, method, extra] of [
  ['post', '/dashboard', 'POST', {}],
  ['session path', '/dashboard;jsessionid=fixture', 'GET', {}],
  ['suffix', '/dashboard/extra', 'GET', {}],
  ['unregistered', '/unregistered-landing', 'GET', {}],
  ['http', '/dashboard', 'GET', { protocol: 'http:' }],
  ['foreign', '/dashboard', 'GET', { host: 'example.invalid' }],
  ['script', '/dashboard', 'GET', { resource_type: 'Script' }],
  ['ckeditor remains denied', '/ckeditor/ckeditor.js?v=1701391813000', 'GET', { resource_type: 'Script' }],
  ['font remains denied', '/images/fonts/bootstrap-icons.woff2?8d200481aa7f02a2d63a331fc782cfaf', 'GET', { resource_type: 'Font' }],
]) test(`registered login landing boundary ${name}`, () => {
  assert.equal(policy('login').allow(meta(path, method, extra)), false);
});
for (const phase of ['read', 'open_form', 'fill', 'submit', 'idle']) {
  test(`registered landing unavailable outside login: ${phase}`, () => {
    for (const query of ['', '1']) assert.equal(policy(phase).allow(meta('/dashboard', 'GET', { query })), false);
  });
}
test('registered landing after login redirect does not reopen the POST channels', () => {
  const p = policy('login');
  const post = meta('/signin?0-1.IFormSubmitListener-content-form', 'POST');
  assert.equal(p.allow(post, 'login'), true); p.active.add('login');
  assert.equal(p.allow({ ...post, response_status: 302 }, 'login'), true);
  assert.equal(p.allow(meta('/dashboard')), true);
  assert.equal(p.allow(meta('/wicket/page?1-1.IFormSubmitListener-content-form', 'POST')), false);
  assert.equal(pathShape('/dashboard'), '/dashboard');
});

for (const path of ['/signin', '/wicket/page']) {
  test(`login channel exact positive ${path}`, () => {
    assert.equal(policy('login').allow(meta(`${path}?0-1.IFormSubmitListener-content-form`, 'POST'), 'login'), true);
  });
  for (const query of ['0-1.IFormSubmitListener-form', '0-1.IFormSubmitListener-content-formx',
    '0-1.IFormSubmitListener-content-form&x=1', '0-.IFormSubmitListener-content-form',
    '0-1IFormSubmitListener-content-form', '0-1.IFormSubmitListener-content-form\n']) {
    test(`login channel query rejected ${path} ${JSON.stringify(query)}`, () => {
      // Pass the metadata query directly so URL parsing cannot strip the newline.
      assert.equal(policy('login').allow(meta(path, 'POST', { query }), 'login'), false);
    });
  }
  test(`login submission GET rejected ${path}`, () => {
    assert.equal(policy('login').allow(meta(`${path}?0-1.IFormSubmitListener-content-form`)), false);
  });
  for (const phase of ['read', 'open_form', 'fill', 'submit', 'idle']) {
    test(`login submission rejected in ${phase} ${path}`, () => {
      assert.equal(policy(phase).allow(meta(`${path}?0-1.IFormSubmitListener-content-form`, 'POST')), false);
    });
  }
}
test('other login submission paths rejected', () => {
  for (const path of ['/', '/signin/extra', '/wicket/page/extra', '/build/1']) {
    assert.equal(policy('login').allow(meta(`${path}?0-1.IFormSubmitListener-content-form`, 'POST')), false);
  }
});
for (const status of [300, 301, 302, 303, 304, 307, 308, 399]) {
  test(`login ${status} closes both channels, preserving redirect GET rules`, () => {
    const p = policy('login');
    const post = meta('/signin?0-1.IFormSubmitListener-content-form', 'POST');
    assert.equal(p.allow(post, 'login'), true); p.active.add('login');
    assert.equal(p.allow({ ...post, response_status: status }, 'login'), ![307, 308].includes(status));
    assert.equal(p.loginPostsClosed, true);
    for (const path of ['/signin', '/wicket/page']) {
      assert.equal(p.allow(meta(`${path}?1-1.IFormSubmitListener-content-form`, 'POST'), 'retry'), false);
    }
    assert.equal(p.allow(meta('/')), true);
    assert.equal(p.allow(meta('/unregistered-landing')), false);
    assert.equal(p.allow(meta('/?1')), false);
    p.phase = 'idle'; p.phase = 'login';
    assert.equal(p.allow(post, 'again'), false);
  });
}
test('five request-stage login releases close permanently; responses do not count', () => {
  const p = policy('login');
  for (let attempt = 1; attempt <= 5; attempt++) {
    const id = `login-${attempt}`;
    const post = meta(`${attempt % 2 ? '/signin' : '/wicket/page'}?${attempt}-1.IFormSubmitListener-content-form`, 'POST');
    assert.equal(p.allow(post, id), true); p.active.add(id);
    assert.equal(p.loginPostCount, attempt);
    assert.equal(p.allow({ ...post, response_status: 200 }, id), true);
    p.active.delete(id);
    assert.equal(p.loginPostCount, attempt);
    assert.equal(p.loginPostsClosed, attempt === 5);
  }
  for (const path of ['/signin', '/wicket/page']) {
    assert.equal(p.allow(meta(`${path}?6-1.IFormSubmitListener-content-form`, 'POST'), 'six'), false);
  }
  p.phase = 'idle'; p.phase = 'login';
  assert.equal(p.allow(meta('/signin?7-1.IFormSubmitListener-content-form', 'POST')), false);
  assert.equal(p.loginPostCount, 5);
});
test('leaving login permanently closes channels even after HTTP200', () => {
  const p = policy('login');
  const post = meta('/signin?0-1.IFormSubmitListener-content-form', 'POST');
  assert.equal(p.allow(post, 'login'), true); p.active.add('login');
  assert.equal(p.allow({ ...post, response_status: 200 }, 'login'), true);
  assert.equal(p.loginPostsClosed, false);
  p.phase = 'idle'; p.phase = 'login';
  assert.equal(p.allow(post, 'retry'), false);
});
test('rejected requests and unrelated responses do not consume the login allowance', () => {
  const p = policy('login');
  for (let i = 0; i < 6; i++) assert.equal(p.allow(meta('/signin?1-1.IFormSubmitListener-form', 'POST')), false);
  assert.equal(p.allow(meta('/overview/0', 'GET', { response_status: 302 }), 'other'), false);
  assert.equal(p.loginPostCount, 0); assert.equal(p.loginPostsClosed, false);
});
test('root path shape and static restrictions remain explicit', () => {
  assert.equal(pathShape('/'), '/');
  for (const path of ['/ckeditor/ckeditor.js?v=1701391813000',
    '/images/fonts/bootstrap-icons.woff2?8d200481aa7f02a2d63a331fc782cfaf',
    '/images/fonts/bootstrap-icons.woff?8d200481aa7f02a2d63a331fc782cfaf']) {
    assert.equal(policy('login').allow(meta(path)), false);
  }
});

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
test('exact run registration, no prefix acceptance', () => {
  const p = policy('open_form'); p.runUrl = run;
  assert.equal(p.allow(meta(run.slice(ORIGIN.length) + 'x')), false);
  assert.equal(p.allow(meta(run.slice(ORIGIN.length))), true);
  assert.equal(p.allow(meta(run.slice(ORIGIN.length))), false);
});
for (const phase of ['idle', 'login', 'read', 'open_form', 'fill', 'submit']) {
  test(`refresh denied in ${phase}, including C2C-03 value=stop regression`, () => {
    const p = policy(phase);
    for (const suffix of ['', '0', '&value=stop', '&random=0.1']) {
      const path = '/build/1?1-1.IBehaviorListener-refresh&action=ajaxRefresh' + suffix;
      for (const method of ['GET', 'POST']) assert.equal(p.allow(meta(path, method)), false);
    }
  });
}
test('one callback per field, old version and other field denied', () => {
  const p = policy('fill'); p.beginField(callback);
  assert.equal(p.allow(meta(callback.slice(ORIGIN.length) + 'x', 'POST')), false);
  assert.equal(p.allow(meta(callback.slice(ORIGIN.length), 'POST'), 'field'), true);
  assert.equal(p.allow(meta(callback.slice(ORIGIN.length), 'POST')), false);
  p.endField(); p.beginField(callback.replace('50-2', '50-3'));
  assert.equal(p.allow(meta(callback.slice(ORIGIN.length), 'POST')), false);
  assert.equal(p.allow(meta(callback.replace('50-2', '50-3').slice(ORIGIN.length), 'POST')), true);
});
test('C2C-03 permanent deny distinguishes stop query values from listener components', () => {
  assert.equal(destructiveListener(new URL(callback).search.slice(1) + '&value=stop'), false);
  assert.equal(destructiveListener('q=stop'), false);
  for (const component of ['stopper', 'nonstop']) {
    assert.equal(destructiveListener(`50-2.IBehaviorListener.0-form-${component}`), true);
  }
});
test('C2C-03 stop outside listener still fails the callback and read query grammar', () => {
  const p = policy('fill'); p.beginField(callback);
  assert.equal(p.allow(meta(callback.slice(ORIGIN.length) + '&value=stop', 'POST')), false);
  assert.equal(p.fieldUrl, callback);
  assert.equal(p.allow(meta(callback.slice(ORIGIN.length), 'POST')), true);
  assert.equal(policy('read').allow(meta('/build/1?q=stop')), false);
});
for (const suffix of ['', '&random=0.1234567890123456', '&random=0.0', '&random=0.' + '1'.repeat(20)]) {
  test(`C2B-10 callback one-shot accepts ${JSON.stringify(suffix)}`, () => {
    const p = policy('fill'); p.beginField(callback);
    const request = meta(callback.slice(ORIGIN.length) + suffix, 'POST');
    assert.equal(p.allow(request, 'field'), true);
    assert.equal(p.fieldRequest, 'field');
    assert.equal(p.fieldUrl, null);
    p.active.add('field');
    assert.equal(p.allow({ ...request, response_status: 200 }, 'field'), true);
    assert.equal(p.allow(request, 'again'), false);
    assert.equal(p.allow(meta(callback.slice(ORIGIN.length), 'POST'), 'bare-again'), false);
    assert.equal(p.released, false);
  });
}
for (const suffix of [
  '&random=0.1&random=0.2', '&random=0.1&extra=1', '&extra=1&random=0.1',
  '&random=', '&random=-0.1', '&random=5e-7', '&random=0.1e-7', '&random=abc',
  '&random=0.1a', '&random=1.1', '&random=0.', '&random=.1', '&random=0.' + '1'.repeat(21),
  '&random=0.1\n', '&random=0%2E1', '&Random=0.1',
]) test(`C2B-10 callback rejects ${JSON.stringify(suffix)} without consuming registration`, () => {
  const p = policy('fill'); p.beginField(callback);
  const request = meta(callback.slice(ORIGIN.length), 'POST');
  assert.equal(p.allow({ ...request, query: request.query + suffix }, 'bad'), false);
  assert.equal(p.fieldUrl, callback);
  assert.equal(p.allow(request, 'good'), true);
});
test('C2B-10 random permission cannot escape the current field POST', () => {
  const p = policy('fill'); p.beginField(callback);
  assert.equal(p.allow(meta(callback.slice(ORIGIN.length) + '&random=0.1')), false);
  assert.equal(p.allow(meta(callback.replace('form-field', 'form-other').slice(ORIGIN.length) + '&random=0.1', 'POST')), false);
  p.endField();
  assert.equal(p.allow(meta(callback.slice(ORIGIN.length) + '&random=0.1', 'POST')), false);
  for (const phase of ['idle', 'login', 'read', 'open_form', 'submit']) {
    p.phase = phase; p.beginField(callback);
    assert.equal(p.allow(meta(callback.slice(ORIGIN.length) + '&random=0.1', 'POST')), false);
  }
});
test('C2B-10 submit action and refresh never accept appended random', () => {
  const p = policy('submit'); p.newForm(); p.submitUrl = action;
  assert.equal(p.allow(meta(action.slice(ORIGIN.length) + '&random=0.1', 'POST')), false);
  assert.equal(p.released, false);
  assert.equal(p.allow(meta(action.slice(ORIGIN.length), 'POST')), true);
  const refresh = '/build/1?1-1.IBehaviorListener-refresh&action=ajaxRefresh';
  p.phase = 'fill';
  assert.equal(p.allow(meta(refresh + '&random=0.1')), false);
  assert.equal(p.allow(meta(refresh + '&random=0.1', 'POST')), false);
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
  p.controls[0].value = Buffer.from('standard-armv7l').toString('hex');
  p.controls[2].options.push({ text: 'aarch64' });
  assert.throws(() => readback(f, 'Tizen'), { code: 'QB_FORM_CHANGED' });
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

function submission() {
  const p = new Policy();
  const f = form();
  let location = f.base;
  const page = {
    isClosed: () => false, url: () => location,
    getByRole: () => ({ click: async () => {} }),
    waitForLoadState: () => assert.fail('old form load state cannot prove submission navigation'),
    waitForURL: async (predicate, options) => {
      assert.equal(p.released, true, 'must wait for actual request release first');
      assert.deepEqual(options, { waitUntil: 'load', timeout: 60000 });
      assert.equal(predicate(new URL(f.base)), false);
      location = ORIGIN + '/build/12';
      assert.equal(predicate(new URL(location)), true);
    },
  };
  const a = new Agent({ policy: p, page }); a.state = 'filled';
  a.currentProject = { project_name: 'Tizen' }; a.snapshot = async () => f;
  a.buildId = async path => { assert.equal(path, '/build/12'); return '12'; };
  return { a, p, page, input: { command: 'submit', fingerprint: fingerprint(readback(f, 'Tizen')) } };
}
test('delayed submit request is awaited before navigation, never false not_released', async () => {
  const { a, p, page, input } = submission();
  let pending;
  page.getByRole = (_role, name) => ({ click: async options => {
    assert.deepEqual(name, { name: 'Ok', exact: true });
    assert.equal(options.noWaitAfter, true);
    pending = setTimeout(() => {
      assert.equal(p.allow(meta(action.slice(ORIGIN.length), 'POST')), true);
    }, 150);
  } });
  try {
    const started = Date.now();
    assert.deepEqual(await a.command(input), { ok: true, landed: 'build', build_id: '12', released: true });
    assert.ok(Date.now() - started >= 150);
  } finally { clearTimeout(pending); }
});
test('no request release by ten-second deadline rejects and never waits for navigation', async () => {
  const { a, page, input } = submission();
  page.waitForURL = () => assert.fail('not released');
  const started = Date.now();
  assert.deepEqual(await a.command(input), { ok: false, error: 'QB_FORM_CHANGED', released: false });
  assert.ok(Date.now() - started >= 10000);
  assert.equal(a.policy.submitUrl, null);
});
test('released submit navigation timeout is unknown, not definite failure', async () => {
  const { a, p, page, input } = submission();
  page.getByRole = () => ({ click: async () => { p.allow(meta(action.slice(ORIGIN.length), 'POST')); } });
  page.waitForURL = async (_predicate, options) => {
    assert.equal(p.released, true); assert.equal(options.timeout, 60000);
    throw new Error('synthetic navigation timeout');
  };
  const reply = await a.command(input);
  assert.equal(reply.ok, true); assert.equal(reply.released, true); assert.equal(reply.landed, 'unknown');
});
test('read checks exact URL and build id and returns actual HTTP status', async () => {
  let redirect = null;
  let id = '1';
  const raw = '<a class="nav-link">Build (id:1)</a><p>safe</p>';
  const rawbytes = Buffer.from(raw, 'utf8');
  const p = new Policy();
  const page = { goto: async url => {
    assert.equal(p.readNavigation.url, url);
    Object.assign(p.readNavigation, { requestId: 'navigation', frameId: 'main', body: rawbytes });
    return { status: () => 503, url: () => url,
    request: () => ({ redirectedFrom: () => redirect }),
    headerValue: async name => { assert.equal(name, 'content-type'); return 'text/html; charset=utf-8'; },
    body: async () => assert.fail('Playwright transcoded body must not be used'),
  }; }, url: () => ORIGIN + '/build/1' };
  const a = new Agent({ policy: p, page, trace: [] });
  a.trusted = { run: async (_fn, input) => {
    assert.equal(input, raw);
    return { build: { labels: [`Build (id:${id})`], summaries: [] },
      redacted: { html_redacted: '<p>safe</p>', outside_identity_count: 0 } };
  } };
  assert.equal((await a.read('/build/1')).status, 503);
  assert.equal(a.rawRead, raw);
  assert.equal(p.readNavigation, null);
  redirect = {}; await assert.rejects(a.read('/build/1'), { code: 'QB_READ_REDIRECTED' }); redirect = null;
  id = '2'; await assert.rejects(a.read('/build/1'), { code: 'QB_READ_ID_MISMATCH' });
  page.url = () => ORIGIN + '/build/1/overview';
  await assert.rejects(a.read('/build/1'), { code: 'QB_READ_REDIRECTED' });
  await assert.rejects(a.read('/build/1?x=1'), { code: 'AGENT_PHASE' });
});
test('source guards: no HTTP client, credential extraction, debug switch, or login interactions', () => {
  const source = readFileSync(new URL('../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs', import.meta.url), 'utf8');
  assert.doesNotMatch(source, /page\.request|context\.request|request\.newContext|\.cookies\(|storageState|ignoreHTTPSErrors|DEBUG\s*=\s*['"]pw/);
  const login = source.split('  async login(timeout) {')[1].split('  async buildId(')[0];
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

for (const [checked, wanted] of [[false, true], [true, false], [true, true], [false, false]])
test(`fill uses current callbacks and frozen selection; checkbox ${checked} -> ${wanted}`, async () => {
  const f = form();
  const requested = Object.fromEntries(FIELDS.map(name => [name, name]));
  Object.assign(requested, { SNAPSHOT_NUM: '@freeze', CHILD_CONFIGURATIONS: ['standard-armv7l:aarch64:x86_64'],
    TARGET_IMAGE: [], 'Immediate Stop With Error': wanted, 'Build Package List': 'pkg/name@abc',
    'BUILD NOTES': 'clang-fix-campaign request=synthetic', 'Add Package List': '', 'Remove Package List': '' });
  const calls = [];
  const p = new Policy();
  for (const row of f.rows.slice(1)) {
    if (row.label === 'SNAPSHOT_NUM') Object.assign(row.controls[0], { tag: 'SELECT',
      options: [{ text: 'older', selected: false }, { text: 'chosen', selected: true }] });
    if (row.label === 'Immediate Stop With Error') Object.assign(row.controls[0], { type: 'checkbox', checked });
    if (row.label === 'CHILD_CONFIGURATIONS') {
      row.controls[0].value = Buffer.from(requested[row.label][0]).toString('hex');
      row.controls[2].options = [{ text: requested[row.label][0] }];
    }
  }
  const a = new Agent({ policy: p, page: {}, failure: null }); a.currentProject = { project_name: 'Tizen' };
  let snapshots = 0;
  let previousWindow;
  a.snapshot = async () => {
    if (snapshots++) assert.equal(p.fieldWindow, previousWindow, 'keep the window through the next snapshot');
    for (const row of f.rows.slice(1)) for (const control of row.controls) {
      control.callback = `wicketAjaxPost('${callback.replace('50-2', `50-${snapshots + 2}`)}', 0)`;
    }
    return f;
  };
  const finish = (name, event) => {
    calls.push([name, event]);
    assert.equal(p.fieldUrl, callback.replace('50-2', `50-${snapshots + 2}`));
    assert.ok(p.fieldWindow);
    assert.notEqual(p.fieldWindow, previousWindow, 'each registration opens a new window');
    previousWindow = p.fieldWindow;
    p.fieldFinished = true; p.lastActivity = Date.now() - 1500;
  };
  a.fieldRow = name => ({ locator: () => ({ locator: () => ({
    fill: async value => { calls.push([name, 'fill']); f.rows.find(r => r.label === name).controls[0].value = value; },
    blur: async () => finish(name, 'blur'),
    check: async () => { f.rows.find(r => r.label === name).controls[0].checked = true; finish(name, 'check'); },
    uncheck: async () => { f.rows.find(r => r.label === name).controls[0].checked = false; finish(name, 'uncheck'); },
    selectOption: async () => assert.fail('frozen snapshot must not be set'),
    dispatchEvent: async event => { assert.equal(event, 'change'); finish(name, event); },
  }) }) });
  const result = await a.fill(requested);
  assert.equal(result.readback['SNAPSHOT_NUM/value'], 'chosen');
  assert.equal(result.snapshot_option_count, 2);
  const events = name => calls.filter(([field]) => field === name).map(([, event]) => event);
  assert.deepEqual(events('SNAPSHOT_NUM'), ['change']);
  assert.deepEqual(events('BUILD_TYPE'), ['change']);
  assert.deepEqual(events('BUILD NOTES'), ['fill', 'blur']);
  assert.deepEqual(events('CHILD_CONFIGURATIONS'), ['change']);
  assert.deepEqual(events('TARGET_IMAGE'), ['change']);
  assert.deepEqual(events('Immediate Stop With Error'), [checked === wanted ? 'change' : wanted ? 'check' : 'uncheck']);
  assert.equal(result.readback['Immediate Stop With Error/value'], wanted);
  assert.equal(new Set(calls.map(([name]) => name)).size, FIELDS.length);
  assert.equal(snapshots, FIELDS.length + 1);
  assert.equal(p.fieldWindow, null);
  assert.equal(result.fingerprint, fingerprint(result.readback));
});

for (const [name, requested, options, selected] of [
  ['missing frozen', 'frozen', [{ text: ' current-A ', selected: true }], ['current-A']],
  ['no selected', '@freeze', [{ text: 'current-A', selected: false }], []],
  ['multiple selected', '@freeze', [{ text: 'a', selected: true }, { text: 'b', selected: true }], ['a', 'b']],
  ['first freeze duplicate text', '@freeze', [{ text: 'a', selected: true }, { text: 'a', selected: false }], ['a']],
  ['empty dropdown', '@freeze', [], []],
  ['long selected', 'frozen', [{ text: 'x'.repeat(201), selected: true }], null],
  ['invalid selected', 'frozen', [{ text: 'bad value', selected: true }], null],
]) test(`snapshot unavailable carries safe field-start state: ${name}`, async () => {
  const f = form(); const p = new Policy();
  Object.assign(f.rows.find(r => r.label === 'SNAPSHOT_NUM').controls[0], { tag: 'SELECT', options });
  const a = new Agent({ policy: p, page: {}, failure: null });
  a.state = 'form'; a.currentProject = { project_name: 'Tizen' };
  a.snapshot = async () => f;
  a.fieldRow = () => ({ locator: () => ({ locator: () => ({ dispatchEvent: async () => {
    p.fieldFinished = true; p.lastActivity = Date.now() - 1500;
  } }) }) });
  const fields = Object.fromEntries(FIELDS.map(label => [label, label]));
  Object.assign(fields, { CHILD_CONFIGURATIONS: ['standard-armv7l:aarch64:x86_64'], TARGET_IMAGE: [],
    'Build Package List': 'pkg/name@abc', 'BUILD NOTES': 'clang-fix-campaign request=synthetic',
    'Add Package List': '', 'Remove Package List': '' });
  fields.SNAPSHOT_NUM = requested;
  const response = await a.command({ command: 'fill', fields });
  assert.deepEqual(response, { ok: false, error: 'QB_FORM_VALUE_UNAVAILABLE', field: 'SNAPSHOT_NUM',
    released: false, snapshot_state: { selected, option_count: options.length } });
  assert.equal(a.state, 'invalid'); assert.equal(p.released, false);
  assert.equal((await a.command({ command: 'submit' })).error, 'AGENT_PHASE');
});

test('field registration rejects a late denial before replacing the previous window', () => {
  const p = policy('fill'); p.beginField(callback);
  const window = p.fieldWindow;
  p.fieldFinished = true;
  window.denied++;
  assert.throws(() => p.beginField(callback.replace('50-2', '50-3')), { code: 'QB_FORM_CHANGED' });
  assert.equal(p.fieldWindow, window);
  assert.equal(p.fieldUrl, callback);
});
