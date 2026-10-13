// Local, synthetic DOM fixtures only. Invoked by the evidence entry's self-test.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import {
  AgentError, createRuntime, FIELDS, formDOM, normalizeFormDOM, ORIGIN, validateForm,
} from '../../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';
import { collectFormDiagnostic, FORM_ACTION, withFormFailureEvidence } from './p5q_c2b_form_diagnostics.mjs';

const PROJECT = 'Tizen-Base-Toolchain';
const TEXT_VALUE = 'SYNTHETIC_VALUE_MUST_NOT_BE_DIAGNOSTIC_OUTPUT';
const OPTION_VALUE = 'SYNTHETIC_OPTION_VALUE_MUST_NOT_BE_DIAGNOSTIC_OUTPUT';
const CALLBACK_TEXT = "wicketAjaxPost('https://quickbuild.tizen.org/wicket/page?20-1.IBehaviorListener.0-form-field', 0)";
const formURL = `${ORIGIN}/wicket/page?20`;
function row(label) {
  let controls;
  const name = `form:fields:${label}:input`;
  if (label === 'PROJECT_NAME') controls = `<div class="property-viewer">${PROJECT}</div>`;
  else if (['CHILD_CONFIGURATIONS', 'TARGET_IMAGE'].includes(label)) controls =
    `<input type="hidden" name="form:${label}:palette:recorder" value="" onchange="${CALLBACK_TEXT}">`
    + ['choices', 'selection'].map(role => `<select name="form:${label}:palette:${role}"></select>`).join('')
    + '<button class="palette-move">move</button>';
  else if (label === 'BUILD NOTES') controls = `<textarea name="${name}" onchange="${CALLBACK_TEXT}">${TEXT_VALUE}</textarea>`;
  else if (label === 'Build Package List') controls = `<input name="${name}" value="${TEXT_VALUE}" onchange="${CALLBACK_TEXT}">`;
  else controls = `<select name="${name}" onchange="${CALLBACK_TEXT}"><option value="${OPTION_VALUE}" selected>Full</option><option value="b">Partial</option></select>`;
  return `<tr><td class="form-label">${label}</td><td class="value">${controls}</td></tr>`;
}
function fixture({ extra = '', missing = null, transform = value => value,
  action = `${ORIGIN}/wicket/page?20-1.IFormSubmitListener-form` } = {}) {
  return `<base href="${formURL}"><h1>Specify Build Options</h1>`
    + `<form action="${action}"><table>${transform(['PROJECT_NAME', ...FIELDS].filter(label => label !== missing).map(row).join(''))}${extra}</table></form>`;
}

export async function formSelfTest(playwright, chromium, python, redactAddress) {
  const productionSource = await readFile(new URL('../../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs', import.meta.url), 'utf8');
  assert.ok(productionSource.includes(`const ACTION = ${FORM_ACTION};`));
  assert.ok(productionSource.includes("const PALETTES = new Set(['CHILD_CONFIGURATIONS', 'TARGET_IMAGE']);"));
  const runtime = await createRuntime(playwright, chromium);
  runtime.policy.allow = () => false;
  let networkRequests = 0;
  runtime.page.on('request', () => { networkRequests += 1; });
  const scratch = await mkdtemp(join(tmpdir(), 'p5q-form-evidence-'));
  let location = formURL;
  let files = 0;
  let evaluations = 0;
  let results = [];
  let tests = 0;
  const pass = name => { tests += 1; process.stdout.write(JSON.stringify({ test: name, result: 'PASS' }) + '\n'); };
  const verify = text => {
    const result = spawnSync(python, ['-c',
      'import sys; from ci_triage.qb_redact import PageRedactor; PageRedactor().check_bytes(sys.stdin.buffer.read())'],
    { input: text, encoding: 'utf8' });
    assert.equal(result.status, 0, 'redaction check must pass');
  };
  const context = {
    page: { url: () => location, evaluate: (...args) => { evaluations += 1; return runtime.page.evaluate(...args); } },
    projectName: PROJECT, redactAddress, documentStatus: () => 200,
    guard: () => { assert.equal(runtime.failure, null); },
    verify,
    archive: async html => {
      verify(html);
      const file = `form-${++files}.html`;
      await writeFile(join(scratch, file), html, { flag: 'wx' });
      verify(await readFile(join(scratch, file), 'utf8'));
      return { file, sha256: createHash('sha256').update(html).digest('hex') };
    },
    record: result => { results.push(result); },
  };
  const capture = async () => {
    const result = await collectFormDiagnostic(context);
    const json = JSON.stringify(result);
    for (const forbidden of [TEXT_VALUE, OPTION_VALUE, CALLBACK_TEXT]) assert.ok(!json.includes(forbidden));
    assert.equal(networkRequests, 0);
    assert.equal(runtime.policy.released, false);
    assert.equal(result.form_unverified, true);
    return result;
  };
  try {
    await runtime.page.setContent(fixture());
    const good = await capture();
    assert.equal(good.expected_labels.length, 13); // Includes PROJECT_NAME, per frozen explicit list.
    assert.deepEqual(good.extra_labels, []); assert.deepEqual(good.missing_labels, []);
    assert.equal(good.validation.production_passed, true);
    assert.equal(good.validation.first_failure, null);
    assert.equal(good.action_matches, true);
    const notes = good.rows.find(row => row.label === 'BUILD NOTES');
    assert.equal(notes.controls[0].value_length, TEXT_VALUE.length);
    const packages = good.rows.find(row => row.label === 'Build Package List');
    assert.equal(packages.controls[0].value_length, TEXT_VALUE.length);
    const buildType = good.rows.find(row => row.label === 'BUILD_TYPE');
    assert.deepEqual(buildType.controls[0].options, [{ text: 'Full', selected: true }, { text: 'Partial', selected: false }]);
    assert.deepEqual(buildType.controls[0].selected_texts, ['Full']);
    const palette = good.rows.find(row => row.label === 'CHILD_CONFIGURATIONS');
    assert.equal(palette.button_count, 1); assert.deepEqual(palette.button_classes, ['palette-move']);
    assert.deepEqual(good.rows[0].property_viewers, [PROJECT]);
    pass('valid-form-value-lengths-options-buttons-project-no-raw-values');
    await runtime.page.evaluate(() => {
      globalThis.originalTrim = String.prototype.trim;
      String.prototype.trim = function () { return this.replace(/^\s+|\s+$/, ''); };
      for (const node of document.querySelectorAll('.form-label,.property-viewer,option')) {
        node.textContent = ` \n${node.textContent}\t `;
      }
    });
    const brokenTrim = await capture();
    assert.equal(brokenTrim.validation.production_passed, true);
    assert.deepEqual(brokenTrim.rows, good.rows);
    await runtime.page.evaluate(() => { String.prototype.trim = globalThis.originalTrim; });
    pass('broken-page-trim-uses-node-normalization-same-diagnostic-rows');
    for (const [name, html, rule, assertion] of [
      ['extra-field', fixture({ extra: row('ADD_TO_IMG_LIST') }), 'label_set', result => {
        assert.deepEqual(result.extra_labels, ['ADD_TO_IMG_LIST']);
        assert.deepEqual(result.missing_labels, []);
      }],
      ['missing-field', fixture({ missing: 'BUILD_TYPE' }), 'label_set', result => {
        assert.deepEqual(result.missing_labels, ['BUILD_TYPE']);
        assert.deepEqual(result.extra_labels, []);
      }],
      ['rich-text-notes', fixture({ transform: html => html.replace('<textarea', '<input type="hidden" name="editor:extra" value="MASKED_TOKEN"><span class="cke_editor"></span><textarea style="display:none"') }), 'single_control', result => {
        const row = result.rows.find(row => row.label === 'BUILD NOTES');
        assert.equal(row.control_count, 2);
        assert.equal(result.ckeditor.cke_elements, 1);
        assert.equal(result.ckeditor.textareas[0].hidden, true);
        assert.equal(result.rows[result.validation.first_failure.row].label, 'BUILD NOTES');
      }],
      ['changed-onchange', fixture({ transform: html => html.replace(CALLBACK_TEXT, 'Wicket.Ajax.post({})') }), 'callback', result => {
        const control = result.rows.find(row => row.label === 'BUILD_TYPE').controls[0];
        assert.equal(control.onchange.present, true);
        assert.equal(control.onchange.exactly_one_wicket_ajax_post, false);
        assert.equal(control.onchange.failure_reason, 'WICKET_AJAX_POST_COUNT');
      }],
      ['invalid-action', fixture({ action: `${ORIGIN}/wicket/page?20-1.IFormSubmitListener-form-extra` }), 'action', result => {
        assert.equal(result.snapshot_null, false); assert.equal(result.action_matches, false);
      }],
    ]) {
      await runtime.page.setContent(html);
      const snapshot = normalizeFormDOM(await runtime.page.evaluate(formDOM));
      let failure;
      try { validateForm(snapshot, PROJECT); } catch (error) { failure = error; }
      assert.equal(failure?.code, 'QB_FORM_CHANGED');
      results = [];
      await assert.rejects(withFormFailureEvidence(async () => { throw failure; }, context), error => error === failure);
      assert.equal(results.length, 1);
      const result = results[0];
      assert.equal(result.reason, 'QB_FORM_CHANGED'); assert.equal(result.stage, 'open_form');
      assert.equal(result.validation.production_passed, false);
      assert.equal(result.validation.first_failure.rule, rule);
      assert.equal(result.validation.first_failure.reached, true);
      const first = result.validation.checks.findIndex(check => !check.ok);
      assert.ok(result.validation.checks.slice(first + 1).every(check => !check.reached));
      assert.ok(!JSON.stringify(result).includes(TEXT_VALUE));
      assert.equal(result.form_unverified, true);
      assert.ok((await readFile(join(scratch, result.file), 'utf8')).includes('Specify Build Options'));
      assertion(result);
      assert.equal(networkRequests, 0); assert.equal(runtime.policy.released, false);
      process.stdout.write(JSON.stringify({ fixture: name, extra: result.extra_labels,
        missing: result.missing_labels, first_failure: result.validation.first_failure,
        form_unverified: result.form_unverified, network_requests: networkRequests, released: false }) + '\n');
      pass(name);
    }
    await runtime.page.setContent(fixture({ action: `${ORIGIN}/wicket/page?token=SYNTHETIC_SECRET` })
      + '<form action="https://quickbuild.tizen.org/;jsessionid=SYNTHETIC_SECRET"></form>');
    const missingForm = await capture();
    assert.equal(missingForm.snapshot_null, true); assert.equal(missingForm.form_count, 2);
    for (const key of ['observed_labels', 'extra_labels', 'missing_labels', 'duplicate_labels']) {
      assert.equal(missingForm[key], null);
    }
    assert.equal(missingForm.validation.first_failure.rule, 'shape');
    assert.ok(!JSON.stringify(missingForm).includes('SYNTHETIC_SECRET'));
    pass('null-snapshot-fallback-all-forms-redacted-actions');

    for (const [name, html, rule] of [
      ['duplicate-label', fixture({ extra: row('BUILD_TYPE') }), 'unique_rows'],
      ['project-name', fixture({ transform: html => html.replace(PROJECT, 'WrongProject') }), 'project_name'],
      ['palette-roles', fixture({ transform: html => html.replace(':palette:recorder', ':palette:wrong') }), 'palette_controls'],
      ['callback-wrong-origin', fixture({ transform: html => html.replace(CALLBACK_TEXT, CALLBACK_TEXT.replace(ORIGIN, 'https://elsewhere.invalid')) }), 'callback'],
      ['callback-missing', fixture({ transform: html => html.replace(`onchange="${CALLBACK_TEXT}"`, '') }), 'callback'],
      ['callback-double', fixture({ transform: html => html.replace(CALLBACK_TEXT, `${CALLBACK_TEXT};${CALLBACK_TEXT}`) }), 'callback'],
    ]) {
      await runtime.page.setContent(html);
      const result = await capture();
      assert.equal(result.validation.first_failure.rule, rule);
      if (name === 'duplicate-label') assert.deepEqual(result.duplicate_labels, ['BUILD_TYPE']);
      if (name === 'callback-missing') assert.equal(result.rows[1].controls[0].onchange.failure_reason, 'MISSING_ONCHANGE');
      if (name === 'callback-double') assert.equal(result.rows[1].controls[0].onchange.wicket_ajax_post_count, 2);
      if (name === 'callback-wrong-origin') assert.equal(result.rows[1].controls[0].onchange.failure_reason, 'QB_FORM_CHANGED');
      pass(name);
    }
    await runtime.page.setContent(fixture());
    results = [];
    const fieldFailure = new AgentError('QB_FORM_VALUE_UNAVAILABLE');
    await assert.rejects(withFormFailureEvidence(async setStage => {
      setStage('BUILD_TYPE_Partial'); throw fieldFailure;
    }, context), error => error === fieldFailure);
    assert.equal(results[0].stage, 'BUILD_TYPE_Partial');
    assert.equal(results[0].validation.production_passed, true);
    assert.equal(results[0].validation.first_failure, null);
    pass('later-field-failure-captures-valid-form-and-preserves-original-reason');

    for (const reason of ['QB_BROWSER_UNAVAILABLE', 'LIVE_TARGET_FAIL_CLOSED', 'QB_READ_REDIRECTED',
      'QB_READ_HTTP_STATUS', 'QB_EVIDENCE_REDACTION_FAILED']) {
      const before = evaluations;
      const failure = new AgentError(reason);
      await assert.rejects(withFormFailureEvidence(async setStage => {
        setStage('BUILD_TYPE_Full'); throw failure;
      }, context), error => error === failure);
      assert.equal(evaluations, before);
      pass(`immediate-stop-no-diagnostic-${reason}`);
    }
    for (const url of [`${ORIGIN}/signin`, 'https://elsewhere.invalid/wicket/page?20']) {
      location = url;
      const before = evaluations;
      assert.equal(await collectFormDiagnostic(context), null);
      assert.equal(evaluations, before);
    }
    pass('wrong-main-frame-location-no-diagnostic');
    location = formURL;
    await assert.rejects(collectFormDiagnostic({ ...context,
      guard: () => { throw new AgentError('QB_BROWSER_UNAVAILABLE'); } }), { code: 'QB_BROWSER_UNAVAILABLE' });
    pass('runtime-failure-preempts-diagnostic');
    await assert.rejects(collectFormDiagnostic({ ...context,
      verify: () => { throw new AgentError('QB_EVIDENCE_REDACTION_FAILED'); } }), { code: 'QB_EVIDENCE_REDACTION_FAILED' });
    pass('diagnostic-redaction-failure-stops-before-archive');
    for (const status of [403, undefined]) {
      const before = evaluations;
      await assert.rejects(collectFormDiagnostic({ ...context, documentStatus: () => status }),
        { code: 'QB_READ_HTTP_STATUS' });
      assert.equal(evaluations, before);
    }
    pass('non200-or-missing-document-status-no-diagnostic');
    let guardCalls = 0;
    const beforeFiles = files;
    await assert.rejects(collectFormDiagnostic({ ...context, guard: () => {
      if (++guardCalls === 2) location = `${ORIGIN}/wicket/page?99`;
    } }), { code: 'QB_READ_REDIRECTED' });
    assert.equal(files, beforeFiles);
    pass('navigation-during-diagnostic-stops-without-archive');
    location = formURL;
    const beforeEvaluations = evaluations;
    const otherFailure = new AgentError('QB_LOGIN_TIMEOUT');
    await assert.rejects(withFormFailureEvidence(async () => { throw otherFailure; }, context), error => error === otherFailure);
    assert.equal(evaluations, beforeEvaluations);
    pass('open-form-other-error-no-diagnostic');
    await runtime.page.setContent(fixture({ transform: html => html.replace('</td><td class="value">', '<button class="outside-value">info</button></td><td class="value">') }));
    const buttons = await capture();
    assert.equal(buttons.rows[0].button_count, 1);
    assert.deepEqual(buttons.rows[0].button_classes, ['outside-value']);
    pass('whole-row-buttons-outside-value-cell');
    assert.equal(networkRequests, 0); assert.equal(runtime.policy.released, false);
    assert.equal(runtime.page.url(), 'about:blank');
    process.stdout.write(JSON.stringify({ self_tests: tests, passed: tests,
      network_requests: networkRequests, released: runtime.policy.released }) + '\n');
  } finally { await runtime.close(); await rm(scratch, { recursive: true, force: true }); }
}
