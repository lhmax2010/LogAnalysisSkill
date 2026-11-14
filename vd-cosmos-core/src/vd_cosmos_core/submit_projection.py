"""Expose mapping cautions and input reconciliation to the existing read workflow."""
from .build_inputs import compare_lists
from .errors import FlowError
from .files import digest, json_bytes
from .http_reader import HTTPReportReader
from .submit_model import requests


def bound_request(config, store, key):
    for request in requests(store.events()).values():
        binding = request.get('binding')
        if not binding: continue
        ref = HTTPReportReader(config, binding['build_id']).build_ref
        if digest(json_bytes(ref.to_dict())) == key:
            return request
    return None


def apply(config, store, key, observation):
    r = bound_request(config, store, key)
    if not r or not observation: return observation
    observation['request_id'] = r['request_id']
    observation['result_caution'] = r.get('result_caution')
    observation['binding_input_check'] = '待报告完整'
    if observation.get('report_state') != '完整' or observation.get('observation_failed'):
        observation['terminal_prerequisite_met'] = False
        return observation
    try:
        compare_lists(r['form']['PACKAGE_LIST'], r['form']['SHELVE_LIST'], observation['reports'], config.raw['cosmos']['branch_markers'])
    except (FlowError, KeyError):
        observation.update(binding_input_check='绑定不一致', exit_code=3, terminal_prerequisite_met=False)
        observation.setdefault('todos', []).append({'reason': 'binding_inputs_mismatch', 'request_id': r['request_id'],
                                                    'basis_version': r['digest']})
    else:
        observation['binding_input_check'] = '一致'
    if r.get('result_caution'):
        observation['terminal_prerequisite_met'] = False
    return observation
