import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';

// Only immutable local Git input and synthetic metadata; no browser or network.
const path = 'tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';
const source = execFileSync('git', ['show', `b6bec94:${path}`], { encoding: 'utf8' });
const { Policy, callbackURL, ORIGIN } = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
const design = readFileSync('docs/clang-fix-campaign/p5q-qb-trigger-design-v1.5-FROZEN.md');
assert.equal(createHash('sha256').update(design).digest('hex'),
  'f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c');
const meta = (url, method) => {
  const parsed = new URL(url);
  return { method, protocol: parsed.protocol, host: parsed.host, path: parsed.pathname,
    query: parsed.search.slice(1), resource_type: 'XHR', response_status: null };
};
const base = `${ORIGIN}/wicket/page?1-1.IBehaviorListener.0-form-field`;
const good = new Policy(); good.phase = 'fill'; good.beginField(base);
assert.equal(good.allow(meta(base, 'POST'), 'positive'), true);
console.log('POSITIVE exact field callback: ALLOWED');

const withValue = `${base}&value=stop`;
assert.throws(() => callbackURL(`wicketAjaxPost('${withValue}', 0)`, ORIGIN), { code: 'QB_FORM_CHANGED' });
assert.throws(() => new Policy().beginField(withValue), { code: 'QB_FORM_CHANGED' });
console.log('QUERY_VALUE_STOP listener=form-field: callbackURL and beginField both QB_FORM_CHANGED (extra parameter outside closed grammar)');

const stopComponent = base.replace('form-field', 'form-stopper');
const bad = new Policy(); bad.phase = 'fill'; bad.beginField(stopComponent);
assert.equal(bad.allow(meta(stopComponent, 'POST'), 'negative'), false);
console.log('LISTENER_COMPONENT_STOP: grammar accepts, permanent destructive-listener rule DENIES');

const refresh = `${ORIGIN}/build/1?1-1.IBehaviorListener-refresh&action=ajaxRefresh&value=stop`;
const legacy = new Policy(); legacy.phase = 'read'; legacy.refresh.add(refresh);
assert.equal(legacy.allow(meta(refresh, 'GET')), true);
console.log('LEGACY test fixture: registered ajaxRefresh GET with value=stop ALLOWED at b6bec94');
console.log('v1.5:280 requires this refresh fixture DENIED; v1.5:306 disallows value=stop on field callbacks; v1.5:756 still requires a legal non-destructive callback with stop in query ALLOWED');
console.log('SPEC_GAP_CONFIRMED P5Q-C2C-02; network_requests=0; assertion_checks=5/5; exit=2');
process.exitCode = 2;
