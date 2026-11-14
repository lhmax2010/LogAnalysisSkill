"""Build-machine B1 verification: offline suite, anonymous doctor and two lookups."""
from copy import deepcopy
import json
from pathlib import Path
import re
import subprocess
import sys
import uuid
from .cli import Parser
from .config import load_config
from .errors import FlowError
from .files import atomic_write, json_bytes
from .verify_b3a11 import ROOTS, child_env, command, contracts, offline_tests, reject_secret_settings, safe_bytes


def execute(args, repo):
    head = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    if not re.fullmatch(r'[0-9a-f]{40}', args.verified_commit) or head != args.verified_commit:
        raise FlowError(6, 'expected_commit_mismatch')
    if subprocess.check_output(['git', '-C', str(repo), 'status', '--porcelain=v1', '--untracked-files=all', '--', *ROOTS]):
        raise FlowError(6, 'owned_source_tree_dirty')
    original = load_config(args.config)
    raw = {k: deepcopy(original.raw[k]) for k in ('cosmos', 'fetch', 'network', 'poll', 'loop', 'budget', 'prepush', 'export', 'submit') if k in original.raw}
    reject_secret_settings(raw)
    inspected = deepcopy(raw); inspected['prepush'].pop('credential_patterns', None)
    safe_bytes(original, json_bytes(inspected))
    for section, key in [('network', 'ca_file'), ('prepush', 'words_file')]:
        if raw.get(section, {}).get(key): raw[section][key] = str(original.source(raw[section][key]))
    directory = original.output('verification/b3a11b1-' + uuid.uuid4().hex)
    directory.mkdir(parents=True, exist_ok=False)
    raw['data_root'] = str(directory)
    config_path = directory / 'config.json'; atomic_write(original.data_root, config_path, json_bytes(raw))
    config = load_config(config_path)
    for name in ('tmp', 'cache'): (directory / name).mkdir()
    env = child_env(directory)
    result = {'commit': head, 'python': sys.version.split()[0], 'exit_code': 0, 'checks': [], 'data_root': str(directory)}
    try:
        result['contracts'] = contracts(config, repo, directory, env)
        result['offline_tests'] = offline_tests(config, repo, directory, env)
        base = ['--config', str(config_path), '--backend', 'real']
        result['doctor'] = command(config, repo, directory, env, 'vd-cosmos-submit', ['doctor', '--online', *base])
        for hub, expected in [('37491096', '19270912'), ('37491058', '19270877')]:
            value = command(config, repo, directory, env, 'vd-cosmos-submit', ['lookup', '--hub-id', hub, *base])
            passed = value['result'] == '唯一' and [x['build_id'] for x in value['candidates']] == [expected]
            result['checks'].append({'hub_id': hub, 'expected': expected, 'result': value['result'],
                                     'candidate_ids': [x['build_id'] for x in value['candidates']],
                                     'coverage': value['coverage'], 'read_only': True, 'pass': passed})
            if not passed: raise FlowError(6, 'lookup_acceptance_mismatch')
    except FlowError as error:
        result.update(error.as_dict())
    result['verdict'] = 'PASS' if result['exit_code'] == 0 else 'FAIL'
    path = atomic_write(original.data_root, directory / 'result.json', safe_bytes(config, json_bytes(result)))
    return {'commit': head, 'python': result['python'], 'exit_code': result['exit_code'], 'verdict': result['verdict'],
            'result_file': path, 'checks': result['checks']}


def main(argv=None):
    try:
        parser = Parser(description=__doc__)
        parser.add_argument('--verified-commit', required=True); parser.add_argument('--config', required=True)
        args = parser.parse_args(argv)
        result = execute(args, Path(__file__).resolve().parents[3])
    except FlowError as error: result = error.as_dict()
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        result = {'exit_code': 5, 'error': 'acceptance_processing_failed'}
    print(json.dumps(result, ensure_ascii=False))
    return result['exit_code']
