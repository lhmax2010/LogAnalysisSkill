"""Checkpoint A acceptance. Never logs in, writes P4, or starts a browser."""
from copy import deepcopy
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace
import uuid

from .cli import Parser
from .config import load_config
from .errors import FlowError
from .export import check_content
from .files import atomic_write, digest, json_bytes, load_json
from .p4 import P4Adapter
from . import verify_b2

ROOTS = ['vd-cosmos-core', 'vd-cosmos-watch', 'vd-cosmos-fetch', 'vd-cosmos-workflow',
         'vd-fix-analyze', 'vd-fix-register', 'vd-cosmos-submit']


def safe_bytes(config, data):
    if not check_content(data, config)['allowed']:
        raise FlowError(4, 'acceptance_credential_blocked')
    return data


def reject_secret_settings(value):
    """Reject named secrets even when a deployment's regex list is incomplete."""
    if isinstance(value, dict):
        for key, child in value.items():
            if key == 'credential_patterns':
                continue
            if re.search(r'(?:^|_)(?:password|passwd|secret|token|cookies?|samlrequest|samlresponse|relaystate)(?:$|_)', key, re.I):  # credential-test-sample
                raise FlowError(4, 'acceptance_secret_setting_forbidden')
            reject_secret_settings(child)
    elif isinstance(value, list):
        for child in value:
            reject_secret_settings(child)


def child_env(directory):
    env = dict(os.environ)
    env.update(PYTHONDONTWRITEBYTECODE='1', VD_COSMOS_TEST_TMPDIR=str(directory / 'tmp'),
               TMPDIR=str(directory / 'tmp'), XDG_CACHE_HOME=str(directory / 'cache'),
               PYTHONPATH='')
    env['PATH'] = str(Path(sys.executable).parent) + os.pathsep + env.get('PATH', '')
    return env


def process(argv, directory, env, timeout=1800):
    try:
        return subprocess.run(argv, cwd=directory, env=env, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise FlowError(5, 'acceptance_process_timeout') from None
    except OSError:
        raise FlowError(5, 'acceptance_process_start_failed') from None


def command(config, repo, directory, env, skill, args):
    run = process([sys.executable, '-B', str(repo / skill / 'scripts/run.py'), *args], directory, env)
    safe_bytes(config, run.stdout)
    safe_bytes(config, run.stderr)
    try:
        value = json.loads(run.stdout)
        if not isinstance(value, dict):
            raise ValueError()
    except (ValueError, UnicodeError):
        raise FlowError(5, 'acceptance_cli_contract_failed') from None
    if run.returncode or value.get('exit_code', 0):
        code = run.returncode if run.returncode in {2, 3, 4, 5, 6} else 5
        raise FlowError(code, 'acceptance_skill_failed', skill=skill,
                        child_error=value.get('error'), todo=value.get('details', {}).get('todo'))
    return value


def contracts(config, repo, directory, env):
    result = []
    for skill in sorted(p.parent.parent.name for p in repo.glob('vd-*/scripts/run.py')):
        value = command(config, repo, directory, env, skill, ['--help'])
        if not value.get('commands'):
            raise FlowError(5, 'acceptance_cli_contract_failed')
        result.append({'skill': skill, 'commands': value['commands'], 'verdict': 'PASS'})
    return result


def offline_tests(config, repo, directory, env):
    run = process(['bash', str(repo / 'vd-cosmos-core/scripts/run_tests.sh')], directory, env, timeout=3600)
    # Do not write raw failed-command output until it has passed the same gate.
    output = safe_bytes(config, run.stdout + run.stderr)
    artifact = atomic_write(config.data_root, directory / 'offline-tests.txt', output)
    if run.returncode:
        raise FlowError(6, 'offline_suite_failed', test_output=artifact)
    return artifact


def read_side(args, config, directory, repo, config_path):
    options = SimpleNamespace(**vars(args), build_id='19091860', mode='real', fixture_counts=None)
    verify_b2.check_source(options, config, repo)
    result = {'mode': 'real'}
    target = directory / 'read-side'
    target.mkdir()
    verify_b2.run(options, config, target, result, repo, config_path)
    atomic_write(config.data_root, target / 'result.json', safe_bytes(config, json_bytes(result)))
    if result.get('exit_code'):
        raise FlowError(result['exit_code'], 'read_side_acceptance_failed')
    return result


def snapshots(config, repo, directory, env, config_path, logs):
    if len(logs) != 7 or len({json.dumps(x['key'], sort_keys=True) for x in logs}) != 7:
        raise FlowError(6, 'expected_seven_failed_packages')
    # Check authentication before reading variables or attempting package work.
    adapter = P4Adapter(config)
    adapter.login_status()
    adapter.info()
    common = ['--config', str(config_path), '--backend', 'real', '--build-id', '19091860']
    command(config, repo, directory, env, 'vd-cosmos-fetch', ['base-list', *common])
    rows = []
    for log in logs:
        key = log['key']
        try:
            value = command(config, repo, directory, env, 'vd-fix-analyze',
                ['snapshot', *common, '--package', key['name'], '--arch', key['arch'], '--log', log['path']])
        except FlowError as error:
            if error.code == 3 and (error.details.get('todo') or {}).get('reason') == 'p4_login_required':
                pending = [{'package': item['key'], 'source_line_check': ['未核对'], 'path_class': [],
                    'shelve_handling': [], 'status': '未执行', 'error': error.reason, 'exit_code': error.code}
                    for item in logs[len(rows):]]
                raise FlowError(error.code, error.reason, **error.details, summary_rows=rows + pending) from None
            rows.append({'package': key, 'source_line_check': ['未核对'], 'path_class': [],
                         'shelve_handling': [], 'status': '快照失败', 'error': error.reason, 'exit_code': error.code})
            continue
        artifact = value['artifact']
        raw = config.output(artifact['path']).read_bytes()
        if digest(raw) != artifact['sha256']:
            raise FlowError(4, 'immutable_snapshot_digest_mismatch')
        data = json.loads(safe_bytes(config, raw))
        rows.append({'package': key,
            'source_line_check': sorted({f['diagnostic_line_match'] for f in data.get('files', [])}) or ['未核对'],
            'path_class': sorted({p['classification']['kind'] for p in data.get('locations', [])}),
            'shelve_handling': sorted({f['snapshot_provenance'] for f in data.get('files', [])}),
            'status': data['mode'], 'exit_code': 0, 'artifact': artifact})
    return rows


def execute(args, repo):
    head = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    if not re.fullmatch(r'[0-9a-f]{40}', args.verified_commit) or args.verified_commit != head:
        raise FlowError(6, 'expected_commit_mismatch')
    dirty = subprocess.check_output(['git', '-C', str(repo), 'status', '--porcelain=v1', '--untracked-files=all', '--', *ROOTS])
    if dirty:
        raise FlowError(6, 'owned_source_tree_dirty')
    original = load_config(args.config)
    # Only sections used by the read-side runtime are retained. No browser or
    # submission settings enter this acceptance root.
    sections = ('cosmos', 'fetch', 'network', 'poll', 'loop', 'budget', 'prepush', 'export', 'p4', 'snapshot', 'analyzer')
    raw = {key: deepcopy(original.raw[key]) for key in sections if key in original.raw}
    # Pattern definitions are code, not values; check all remaining values
    # before persisting the runtime configuration.
    reject_secret_settings(raw)
    inspected = deepcopy(raw)
    inspected.get('prepush', {}).pop('credential_patterns', None)
    safe_bytes(original, json_bytes(inspected))
    for section, key in [('network', 'ca_file'), ('prepush', 'words_file')]:
        if raw.get(section, {}).get(key):
            raw[section][key] = str(original.source(raw[section][key]))
    for name in ['saved_dir', 'rows', 'links']:
        setattr(args, name, str(original.source(getattr(args, name))))
    directory = original.output('verification/b3a11-' + uuid.uuid4().hex)
    directory.mkdir(parents=True, exist_ok=False)
    raw['data_root'] = str(directory)
    config_path = directory / 'config.json'
    atomic_write(original.data_root, config_path, json_bytes(raw))
    config = load_config(config_path)
    for name in ('tmp', 'cache'):
        (directory / name).mkdir()
    env = child_env(directory)
    result = {'commit': head, 'python': sys.version.split()[0], 'data_root': str(directory),
              'exit_code': 0, 'verdict': 'PASS', 'summary': []}
    try:
        result['contracts'] = contracts(config, repo, directory, env)
        result['offline_tests'] = offline_tests(config, repo, directory, env)
        result['read_side'] = read_side(args, config, directory, repo, config_path)
        result['summary'] = snapshots(config, repo, directory, env, config_path, result['read_side']['B']['logs'])
        failed = [r['exit_code'] for r in result['summary'] if r['exit_code']]
        if failed:
            result.update(exit_code=failed[0], verdict='FAIL')
    except FlowError as error:
        result.update(error.as_dict(), verdict='FAIL')
        result['summary'] = result['details'].pop('summary_rows', result['summary'])
        if not result['summary']:
            result['summary'] = [{'package': log['key'], 'source_line_check': ['未核对'],
                'path_class': [], 'shelve_handling': [], 'status': '未执行',
                'error': error.reason, 'exit_code': error.code}
                for log in result.get('read_side', {}).get('B', {}).get('logs', [])]
    # Any notices or login command must pass before reaching either terminal or disk.
    output = safe_bytes(config, json_bytes(result))
    artifact = atomic_write(original.data_root, directory / 'result.json', output)
    lines = ['| Package | Source line | Path class | Shelve handling | Status |', '|---|---|---|---|---|']
    for row in result['summary']:
        fields = [row['package']['arch'] + '/' + row['package']['name'], ', '.join(row['source_line_check']),
                  ', '.join(row['path_class']), ', '.join(row['shelve_handling']), row['status']]
        lines.append('| ' + ' | '.join(f.replace('|', r'\|').replace('\n', ' ') for f in fields) + ' |')
    table = safe_bytes(config, ('\n'.join(lines)+'\n').encode())
    atomic_write(original.data_root, directory / 'summary.md', table)
    print(table.decode(), file=sys.stderr, end='')
    todo = result.get('details', {}).get('todo') or {}
    if todo.get('command'):
        print(todo['command'], file=sys.stderr)
    return {'commit': head, 'python': result['python'], 'exit_code': result['exit_code'],
            'verdict': result['verdict'], 'summary': result['summary'], 'result_file': artifact,
            **({'todo': todo} if todo else {})}


def main(argv=None):
    parser = Parser(description=__doc__)
    for name in ('verified-commit', 'config', 'saved-dir', 'rows', 'links'):
        parser.add_argument('--'+name, required=True)
    parser.add_argument('--live-build-id')
    parser.add_argument('--budget-s', type=float)
    try:
        args = parser.parse_args(argv)
        # No arbitrary exception messages or captured stderr are echoed.
        result = execute(args, Path(__file__).resolve().parents[3])
    except FlowError as error:
        result = error.as_dict()
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError):
        result = {'exit_code': 5, 'error': 'acceptance_processing_failed'}
    print(json.dumps(result, ensure_ascii=False))
    return result['exit_code']
