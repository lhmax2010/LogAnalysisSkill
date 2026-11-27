"""Register the browser contract from a verified real rehearsal at a human terminal."""
import json
from pathlib import Path
import re
import subprocess

from vd_cosmos_core.config_update import update_submit
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.files import digest, json_bytes, load_json
from vd_cosmos_core.submit_browser_contract import SEED
from vd_cosmos_core.submit_config import CALLBACK_FIELDS, valid_callback_pattern
from vd_cosmos_core.submit_model import ensure_safe
from vd_cosmos_core import submit_terminal


SHA1 = re.compile(r'[0-9a-f]{40}')
SHA256 = re.compile(r'[0-9a-f]{64}')
OPTION_TEXT = re.compile(r'[A-Za-z0-9_.()+ /:-]{0,120}')
REVIEW_VALUE = re.compile(r'[A-Za-z0-9_.()+ -]{0,120}')
CONTROL_FIELDS = {'index', 'label', 'kind', 'name', 'options', 'default'}
REPO = Path(__file__).resolve().parents[3]


def source_commit():
    try:
        revision = subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', '--verify', 'HEAD'],
                                           stderr=subprocess.DEVNULL, text=True, timeout=5).strip()
    except (OSError, subprocess.SubprocessError):
        raise FlowError(6, 'rehearsal_commit_unavailable') from None
    if not SHA1.fullmatch(revision):
        raise FlowError(6, 'rehearsal_commit_unavailable')
    return revision


def binding(config):
    submit = config.raw['submit']
    return {key: submit[key] for key in ('target_config', 'target_config_id', 'target_instance', 'account')}


def record(config, result, revision):
    if source_commit() != revision:
        raise FlowError(6, 'rehearsal_commit_changed')
    return dict(result, ok=True, contract_source={**binding(config), 'source_commit': revision, 'backend': 'real'})


def invalid(check, index=None, *, reason='unverified_rehearsal_result'):
    details = {'check': check}
    if index is not None:
        details['control_index'] = index
    return FlowError(4, reason, **details)


def encoding(control, seed, parts, ks_encoding):
    index, name, kind = seed['index'], control['name'], seed['kind']
    if (type(control['index']) is not int
            or any(control[key] != seed[key] for key in ('index', 'label', 'kind'))
            or not isinstance(name, str)
            or not re.fullmatch(rf'editor:content:basicProperties:{index}:property:editor:editor:[A-Za-z0-9:_-]+', name)):
        raise invalid('control_fields', index)
    if name not in parts:
        raise invalid('parts', index)
    if kind == 'select':
        options = control['options']
        if not isinstance(options, list) or not options:
            raise invalid('select_options', index)
        values = {}
        for option in options:
            if not isinstance(option, dict) or option.keys() != {'text', 'value'}:
                raise invalid('select_options', index)
            text, value = option['text'], option['value']
            if not isinstance(text, str) or not OPTION_TEXT.fullmatch(text) or text in values:
                raise invalid('select_option_text', index)
            if not isinstance(value, str) or not REVIEW_VALUE.fullmatch(value):
                raise invalid('select_option_value', index)
            values[text] = value
        if not isinstance(control['default'], str) or control['default'] not in values:
            raise invalid('select_default', index)
        return {'encoding': 'enum', 'option_values': values}

    if control['options'] != []:
        raise invalid('control_options', index)
    if type(control['default']) is not bool:
        raise invalid('control_default', index)
    if kind == 'checkbox':
        checked = control['checked_value']
        if (not isinstance(checked, str) or not REVIEW_VALUE.fullmatch(checked)
                or parts[name] != {'name': name, 'length': len(checked.encode()), 'sha256': digest(checked.encode())}):
            raise invalid('checkbox_value', index)
        return {'encoding': 'boolean', 'checked_value': checked}
    if kind == 'ks':
        return {'encoding': ks_encoding}
    return {'encoding': 'text'}


def proposal(config, result):
    if (not isinstance(result, dict) or result.get('ok') is not True or result.get('rehearsed') is not True
            or result.get('clicked') is not False or 'error' in result
            or type(result.get('exit_code')) is not int or result['exit_code'] != 0):
        raise invalid('result_flags')
    source, evidence, fingerprint, account_check, records = (
        result.get(key) for key in ('contract_source', 'evidence', 'fingerprint', 'account_check', 'gate_records'))
    if (not isinstance(source, dict) or source.get('backend') != 'real'
            or not isinstance(source.get('source_commit'), str) or not SHA1.fullmatch(source['source_commit'])):
        raise invalid('contract_source')
    if not isinstance(account_check, dict) or account_check.get('matched') is not True:
        raise invalid('account_check')
    if (not isinstance(evidence, dict) or evidence.get('verified') is not True
            or evidence.get('ks_encoding') not in ('ids', 'texts')):
        raise invalid('evidence')
    if not isinstance(fingerprint, dict):
        raise invalid('fingerprint')
    if (any(source.get(key) != value for key, value in binding(config).items())
            or fingerprint.get('target') != source['target_config']):
        raise invalid('target_or_account', reason='rehearsal_target_or_account_mismatch')

    parts = {}
    raw_parts = evidence.get('parts')
    if not isinstance(raw_parts, list):
        raise invalid('parts')
    for part in raw_parts:
        if (not isinstance(part, dict) or part.keys() != {'name', 'length', 'sha256'}
                or not isinstance(part['name'], str) or part['name'] in parts
                or type(part['length']) is not int or part['length'] < 0
                or not isinstance(part['sha256'], str) or not SHA256.fullmatch(part['sha256'])):
            raise invalid('parts')
        parts[part['name']] = part
    hidden = evidence.get('hidden_name')
    if (not isinstance(hidden, str) or not re.fullmatch(r'[A-Za-z0-9_-]+_hf_0', hidden)
            or parts.get(hidden) != {'name': hidden, 'length': 0, 'sha256': digest(b'')}):
        raise invalid('hidden')

    controls = fingerprint.get('controls')
    if not isinstance(controls, list) or len(controls) != len(SEED):
        raise invalid('controls_count')
    encodings = {}
    components = {}
    for control, seed in zip(controls, SEED):
        fields = CONTROL_FIELDS | {'checked_value'} if seed['kind'] == 'checkbox' else CONTROL_FIELDS
        if not isinstance(control, dict) or control.keys() != fields:
            raise invalid('control_fields', seed['index'])
        encodings[seed['label']] = encoding(control, seed, parts, evidence['ks_encoding'])
        components['form-' + control['name'].replace(':', '-')] = seed['index']
    if len(parts) != len(SEED) + 1:
        raise invalid('parts')

    if not isinstance(records, list):
        raise invalid('callbacks')
    callbacks = []
    for row in records:
        if not isinstance(row, dict):
            raise invalid('callbacks')
        if row.get('classification') not in ('callback_candidate', 'callback_sent'):
            continue
        pattern = {key: row[key] for key in sorted(CALLBACK_FIELDS) if key in row}
        component = pattern.get('component')
        index = components.get(component) if isinstance(component, str) else None
        if not valid_callback_pattern(pattern) or row.get('control') != component or index is None:
            raise invalid('callbacks', index, reason='unverified_rehearsal_callback')
        if pattern not in callbacks:
            callbacks.append(pattern)

    properties = config.raw['submit']['property_map']
    updates = {
        'property_map': {label: {**properties[label], **item} for label, item in encodings.items()},
        'gate_patterns': callbacks,
        'form_fingerprint': {'controls': controls, 'confirmed': True},
        'hidden_registered_value': '',
        'property_map_confirmed': True,
        'gate_patterns_confirmed': True,
    }
    review = {'source_commit': source['source_commit'], 'encodings': [
        {'property': control['label'], 'kind': control['kind'], **encodings[control['label']]} for control in controls],
        'gate_patterns': callbacks, 'fingerprint': {'controls': len(controls), 'sha256': digest(json_bytes(fingerprint))},
        'hidden_registered_value': ''}
    ensure_safe(config, review)
    ensure_safe(config, updates)
    return updates, review


def run(config_path, result_path):
    if not submit_terminal.available():
        raise FlowError(2, 'terminal_required')
    submit_terminal.ancestors_allowed()
    if not result_path or not Path(result_path).is_file():
        raise FlowError(2, 'rehearsal_result_required')
    result = load_json(result_path)

    def plan(config, current):
        updates, review = proposal(config, result)
        prompt = 'Review rehearsal contract\n' + json.dumps(review, ensure_ascii=True, indent=2)
        if submit_terminal.ask(prompt + '\nType confirm to register the contract: ') != 'confirm':
            raise FlowError(3, 'confirmation_required')
        changes = {key: value for key, value in updates.items() if key not in current or current[key] != value}
        return changes, {'changed': ['submit.' + key for key in sorted(changes)]}

    return update_submit(config_path, plan)
