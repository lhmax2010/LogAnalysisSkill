// Evidence-only replay of validateForm. Never changes the production verdict.
import {
  AgentError, callbackURL, canonical, checkRedacted, FIELDS, formDOM, normalizeFormDOM,
  ORIGIN, redactDOM, validateForm,
} from '../../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';

// Private production constants; the offline test pins these copies to source.
export const FORM_ACTION = /^\d+-\d+\.IFormSubmitListener-form$/;
const PALETTES = new Set(['CHILD_CONFIGURATIONS', 'TARGET_IMAGE']);

export function formExtrasDOM() {
  const forms = [...document.forms];
  const selected = forms.filter(form => /IFormSubmitListener-form/.test(form.action));
  return {
    ready_state: document.readyState,
    forms: forms.map(form => ({ action: form.action })),
    row_buttons: selected.length === 1 ? [...selected[0].querySelectorAll('.form-label')].map(label => {
      const buttons = [...(label.closest('tr')?.querySelectorAll('button') ?? [])];
      return { count: buttons.length, classes: buttons.map(button => button.className) };
    }) : [],
    cke_elements: [...document.querySelectorAll('[class]')]
      .filter(node => /cke/.test(node.getAttribute('class'))).length,
    textareas: [...document.querySelectorAll('textarea')].map(node => {
      const style = getComputedStyle(node);
      return { name: node.name, hidden_attribute: node.hidden,
        hidden: node.hidden || style.display === 'none' || style.visibility === 'hidden'
          || node.getClientRects().length === 0 };
    }),
  };
}

function callbackFacts(code, base) {
  const count = typeof code === 'string' ? [...code.matchAll(/wicketAjaxPost\(\s*(['"])(.*?)\1/g)].length : 0;
  const calls = typeof code === 'string' ? [...code.matchAll(/\bwicketAjaxPost\s*\(/g)].length : 0;
  let valid = false;
  try { callbackURL(code, base); valid = true; } catch { /* No raw callback or exception text is evidence. */ }
  return { present: typeof code === 'string', exactly_one_wicket_ajax_post: calls === 1,
    wicket_ajax_post_count: calls, production_match_count: count, valid,
    failure_reason: valid ? null : typeof code !== 'string' ? 'MISSING_ONCHANGE'
      : count !== 1 ? 'WICKET_AJAX_POST_COUNT' : 'QB_FORM_CHANGED' };
}

function address(value, base, redactAddress) {
  try {
    const url = new URL(value, base);
    return { valid_url: true, protocol: url.protocol, host: url.host,
      ...redactAddress(url.pathname, url.search.slice(1)) };
  } catch { return { valid_url: false }; }
}

export function formDiagnosticFacts(form, extras, projectName, redactAddress) {
  const expected = [...FIELDS, 'PROJECT_NAME'];
  const rows = Array.isArray(form?.rows) ? form.rows : [];
  const labels = rows.filter(Boolean).map(row => row.label);
  const unique = [...new Set(labels)];
  const checks = [];
  let reached = true;
  const add = (rule, ok, row = null) => {
    checks.push({ rule, row, ok, reached });
    if (!ok) reached = false;
  };
  const shape = Boolean(form?.heading && Array.isArray(form.rows) && form.rows.every(Boolean));
  add('shape', shape);
  if (shape) {
    add('label_set', unique.length === FIELDS.length + 1 && labels.every(name => expected.includes(name)));
    add('unique_rows', unique.every(name => labels.filter(label => label === name).length === 1));
    for (const [index, row] of rows.entries()) {
      if (row.label === 'PROJECT_NAME') {
        add('project_name', row.controls.length === 0 && row.viewers.length === 1
          && row.viewers[0] === projectName, index);
        continue;
      }
      const palette = PALETTES.has(row.label);
      const controlsOK = palette ? row.controls.length === 3
        && canonical(row.controls.map(control => control.role).sort()) === canonical(['choices', 'recorder', 'selection'])
        : row.controls.length === 1;
      add(palette ? 'palette_controls' : 'single_control', controlsOK, index);
      const control = palette ? row.controls.find(control => control.role === 'recorder') : row.controls[0];
      add('callback', callbackFacts(control?.callback, form.base).valid, index);
    }
    let valid = false;
    try {
      const action = new URL(form.action);
      valid = action.origin === ORIGIN && action.pathname === '/wicket/page' && FORM_ACTION.test(action.search.slice(1));
    } catch { /* Invalid URL is a failed action check. */ }
    add('action', valid);
  }
  const firstFailure = checks.find(check => check.reached && !check.ok) ?? null;
  let productionPassed = false;
  let productionError = null;
  try { validateForm(form, projectName); productionPassed = true; }
  catch (error) { productionError = error instanceof AgentError ? error.code : 'EVIDENCE_VALIDATION_ERROR'; }
  if (productionPassed !== (firstFailure === null)) throw new AgentError('EVIDENCE_VALIDATION_REPLAY_MISMATCH');
  return {
    snapshot_null: form === null, ready_state: extras.ready_state,
    form_count: extras.forms.length,
    forms: extras.forms.map(item => ({ action: address(item.action, form?.base, redactAddress) })),
    expected_labels: expected, observed_labels: form === null ? null : unique,
    extra_labels: form === null ? null : unique.filter(label => !expected.includes(label)),
    missing_labels: form === null ? null : expected.filter(label => !unique.includes(label)),
    duplicate_labels: form === null ? null : unique.filter(label => labels.filter(item => item === label).length > 1),
    rows: rows.map((row, index) => row === null ? null : ({ label: row.label, control_count: row.controls.length,
      controls: row.controls.map(control => ({ tag: control.tag, type: control.type, role: control.role,
        onchange: callbackFacts(control.callback, form.base),
        ...(control.tag === 'SELECT' ? {
          options: control.options.map(option => ({ text: option.text, selected: option.selected })),
          selected_texts: control.options.filter(option => option.selected).map(option => option.text),
        } : ['INPUT', 'TEXTAREA'].includes(control.tag) ? { value_length: control.value.length } : {}),
      })),
      button_count: extras.row_buttons[index]?.count ?? row.buttons.length,
      button_classes: extras.row_buttons[index]?.classes ?? row.buttons.map(button => button.className),
      ...(row.label === 'PROJECT_NAME' ? { property_viewers: row.viewers } : {}),
    })),
    action: form ? address(form.action, undefined, redactAddress) : null,
    action_matches: checks.find(check => check.rule === 'action')?.ok ?? null,
    ckeditor: { cke_elements: extras.cke_elements, textareas: extras.textareas },
    validation: { production_passed: productionPassed, production_error: productionError,
      first_failure: firstFailure, checks },
  };
}

export async function collectFormDiagnostic({ page, projectName, guard, documentStatus, redactAddress, verify, archive }) {
  guard();
  const current = page.url();
  const url = new URL(current);
  if (url.origin !== ORIGIN || url.pathname !== '/wicket/page') return null;
  const stable = () => {
    guard();
    if (page.url() !== current) throw new AgentError('QB_READ_REDIRECTED');
    if (documentStatus(current) !== 200) throw new AgentError('QB_READ_HTTP_STATUS');
  };
  stable();
  const form = normalizeFormDOM(await page.evaluate(formDOM));
  stable();
  const extras = await page.evaluate(formExtrasDOM);
  extras.textareas = extras.textareas.map(({ name, ...item }) => ({ ...item, role: name.split(':').at(-1) }));
  stable();
  const facts = { main_frame: address(current, undefined, redactAddress),
    ...formDiagnosticFacts(form, extras, projectName, redactAddress) };
  // Check diagnostic strings before any persistence; form values/callbacks stay in memory.
  verify(JSON.stringify(facts));
  const html = checkRedacted(await page.evaluate(redactDOM));
  stable();
  const saved = await archive(html);
  stable();
  return { ...facts, ...saved, form_unverified: true };
}

export async function withFormFailureEvidence(run, context) {
  let stage = 'open_form';
  try { return await run(value => { stage = value; }); }
  catch (error) {
    context.guard();
    const reason = error instanceof AgentError ? error.code : 'EVIDENCE_RUNTIME_ERROR';
    const immediate = ['QB_BROWSER_UNAVAILABLE', 'LIVE_TARGET_FAIL_CLOSED', 'QB_READ_REDIRECTED',
      'QB_READ_HTTP_STATUS', 'QB_EVIDENCE_REDACTION_FAILED'];
    if (!immediate.includes(reason) && (stage !== 'open_form' || reason === 'QB_FORM_CHANGED')) {
      const diagnostic = await collectFormDiagnostic(context);
      if (diagnostic) await context.record({ reason, stage, ...diagnostic });
    }
    throw error;
  }
}
