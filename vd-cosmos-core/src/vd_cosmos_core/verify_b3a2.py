"""Offline analysis acceptance using registered, already-downloaded artifacts."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import re
import shlex
import sys
import tempfile

from .analysis_result import SCHEMA, accept_result
from .commands import command_context
from .config import load_config
from .export import check_content
from .diagnosis import version_source
from .errors import FlowError
from .files import atomic_write, digest, json_bytes
from .receipts import logs_valid
from .state import EventStore
from .registered_logs import failed_packages, is_log_event, package_identity, registrations, read_registration
from .task_package import build_task, checked_file, checked_task, snapshot_registration, verify_text


def copy_database(config, scratch):
    """Take a stable local copy without opening the original DB (or its WAL) writable."""
    base = config.output('state/state.db')
    paths = [base, base.with_name('state.db-wal')]
    def read(path):
        try:
            return path.read_bytes()
        except FileNotFoundError:
            return None
    before = [read(path) for path in paths]
    if before[0] is None:
        raise FlowError(6, 'analysis_verifier_unique_build_required', candidate_count=0, packages=[])
    if before != [read(path) for path in paths]:
        raise FlowError(6, 'analysis_verifier_source_database_busy')
    for path, raw in zip(paths, before):
        if raw is not None:
            atomic_write(scratch, 'state/' + path.name, raw)


def locate_logs(config, source, build_id, selected=None):
    observations, logs, seen_log, rejected = {}, {}, set(), set()
    for event in registrations(source, selected):
        key = event['payload']['build']
        if key in observations and key in logs:
            continue
        latest_log = is_log_event(event) and key not in seen_log
        if latest_log:
            seen_log.add(key)
        try:
            observation, receipt = read_registration(config, event)
        except FlowError:
            if latest_log:
                rejected.add(key)
            continue
        identity = observation.get('build_ref', {})
        if str(identity.get('run_id')) != build_id:
            continue
        if digest(json_bytes(identity)) != key:
            raise FlowError(4, 'analysis_verifier_build_identity_mismatch')
        observations.setdefault(key, observation)
        if latest_log:
            logs[key] = receipt
    if len(observations) != 1:
        raise FlowError(6, 'analysis_verifier_unique_build_required',
                        candidate_count=len(observations), build_keys=sorted(observations), packages=[])
    build, observation = next(iter(observations.items()))
    expected = failed_packages(observation)
    receipt = logs.get(build)
    inputs, issues = audit_inputs(config, source, build, observation, receipt, expected)
    details = {'candidate_count': 1, 'build_key': build, 'packages': inputs}
    if build in rejected:
        raise FlowError(4, 'analysis_verifier_latest_log_registration_invalid', **details)
    if not expected or issues['logs']:
        raise FlowError(6, 'analysis_verifier_final_logs_required', **details)
    if issues['snapshots']:
        raise FlowError(6, 'analysis_verifier_snapshot_inputs_required', **details)
    return build, receipt, {key: package['category'] for key, package in expected.items()}


def audit_inputs(config, source, build, observation, receipt, expected):
    by_package = {}
    for item in (receipt or {}).get('logs', []):
        by_package.setdefault(package_identity(item['key']), []).append(item)
    issues = {'logs': set(by_package) != set(expected), 'snapshots': False}
    rows = []
    for identity, package in sorted(expected.items()):
        key = package['key']
        items = by_package.get(identity, [])
        issues['logs'] |= len(items) != 1
        valid = len(items) == 1 and logs_valid(config, {'logs': items}, observation)
        row = {'package': key, 'registered_final_log': 'available' if valid else 'missing_or_invalid',
               'snapshot': 'unchecked', 'sources': [], 'source_status': 'unchecked'}
        rows.append(row)
        issues['logs'] |= not valid
        has_snapshot = any(event['payload'].get('package') == key for event in
                           source.events(build, kinds=['snapshot_completed']))
        if not valid:
            row['snapshot'] = 'unchecked_without_final_log' if has_snapshot else 'registered_snapshot_required'
            row['source_status'] = 'unchecked_without_snapshot' if not has_snapshot else 'unchecked_without_final_log'
            continue
        try:
            _, snapshot = snapshot_registration(config, source, build, key, items[0]['sha256'])
        except (FlowError, ValueError, KeyError, OSError) as error:
            row['snapshot'] = error.reason if isinstance(error, FlowError) else 'invalid_snapshot'
            issues['snapshots'] = True
            continue
        row['snapshot'] = 'available'
        row['source_status'] = 'available' if any(f.get('content') for f in snapshot['files']) else 'diagnostic_only_no_sources'
        for entry in snapshot['files']:
            info = {'file': entry.get('depotFile')}
            if entry.get('content'):
                try:
                    if digest(checked_file(config, entry['content'])) != entry['sha256']:
                        raise FlowError(4, 'registered_input_digest_mismatch')
                    info['status'] = 'available'
                except (FlowError, KeyError, OSError, ValueError, TypeError) as error:
                    info['status'] = error.reason if isinstance(error, FlowError) else 'invalid_source'
                    issues['snapshots'] = True
                    row['source_status'] = 'missing_or_invalid'
            else:
                info['status'] = 'not_captured'
                info['reason'] = entry.get('unavailable_reason') or 'no_registered_content'
            row['sources'].append(info)
    return rows, issues


def remediation(config_path, commit, build_id, details):
    repo = Path(__file__).resolve().parents[3]
    config_path = str(Path(config_path).resolve())
    prep = shlex.join(['nice', '-n', '19', sys.executable, str(repo / 'vd-fix-analyze/scripts/run.py'),
                       'prepare-inputs', '--config', config_path, '--build', build_id])
    verifier = ['nice', '-n', '19', 'bash', str(repo / 'vd-cosmos-core/scripts/verify_b3a2_real.sh'),
                commit, '--config', config_path, '--build', build_id, '--build-key']
    keys = details.get('build_keys', [])
    if len(keys) > 1:
        return {'next_commands': {key: shlex.join([*verifier, key]) for key in keys}}
    return {'next_command': prep}


def stage_local_inputs(config, target, source, build, data, expected):
    local_logs, snapshots = [], []
    for index, item in enumerate(data['logs']):
        path = f'source/{index}'
        package = item['key']
        category = expected[package_identity(package)]
        raw = checked_file(config, item)
        verify_text(config, raw)
        artifact = atomic_write(target.data_root, path+'/build.log', raw)
        local_logs.append(dict(item, **artifact))
        registered, original = snapshot_registration(config, source, build, package, item['sha256'])
        verify_text(config, checked_file(config, registered))
        snapshot = dict(original, files=[], verifier_source_manifest_sha256=registered['sha256'])
        for offset, entry in enumerate(original['files']):
            copied = dict(entry)
            if entry.get('content'):
                content = checked_file(config, entry['content'])
                verify_text(config, content)
                copied['content'] = atomic_write(target.data_root, f'{path}/files/{offset}', content)
            snapshot['files'].append(copied)
        cloned = atomic_write(target.data_root, path+'/manifest.json', json_bytes(snapshot))
        snapshots.append((category, cloned, snapshot))
    return dict(data, logs=local_logs), snapshots


def example(task):
    """Hand-written diagnostic-only result. The fixture tag prevents live progression."""
    return {'schema_version': SCHEMA, 'task_id': task['task_id'], 'attempt': task['attempt'],
            'input_digest': task['task_input_digest'], 'facts': ['build-and-package'],
            'outcome': 'diagnostic_only',
            'proposals': {'root_cause': 'Fixture demonstrating the result contract.',
                          'responsible': None, 'bug_assessment': {'value': 'unknown', 'basis': 'Fixture.'},
                          'alternatives': [], 'owner_pending': '', 'knowledge_refs': []},
            'provenance': {'analyst_type': 'fixture', 'analyst_version': '1', 'model': 'none',
                           'task_sha256': task['inputs']['TASK.md']['sha256'],
                           'prompt_sha256': digest(b'no AI; hand-written verifier fixture')}}


def verify(config, build_id, workspace, *, selected=None):
    db_copy = workspace / 'source-db'
    db_copy.mkdir(mode=0o700)
    copy_database(config, db_copy)
    safe_analyzer = dict(config.raw['analyzer'], cline_extension={})
    target = replace(config, data_root=workspace, raw={**config.raw, 'analyzer': safe_analyzer})
    with EventStore(db_copy) as source:
        build, original, expected = locate_logs(config, source, build_id, selected)
        local, snapshots = stage_local_inputs(config, target, source, build, original, expected)
    receipt = atomic_write(workspace, 'registered-logs.json', json_bytes(local))
    release = version_source(config, build)
    tasks = []
    with EventStore(workspace) as journal:
        journal.append(command_context('fetch.logs'), 'observation_recorded',
                       {'build': build, 'artifact': receipt}, journal.head())
        for item, (category, record, body) in zip(local['logs'], snapshots):
            journal.append(command_context('analyze.snapshot'), 'snapshot_completed',
                           {'build': build, 'package': item['key'], 'artifact': record}, journal.head())
            prepared = build_task(target, journal, build, build_id, item, category, record, body,
                                  clang_release=release)
            _, refs = checked_task(target, prepared)
            tasks.append({'task_id': prepared['task_id'], 'attempt': prepared['attempt'],
                          'package': prepared['package'], 'mode': prepared['mode'],
                          'evidence_ids': len(refs),
                          'original_snapshot_sha256': body['verifier_source_manifest_sha256'],
                          'segment_manifest_sha256': prepared['inputs']['segments.json']['sha256']})
            if len(tasks) == 1:
                fixture_task = prepared
    raw_example = json_bytes(example(fixture_task))
    atomic_write(workspace, fixture_task['directory']+'/outputs/result.json', raw_example)
    accepted = accept_result(target, build, fixture_task['task_id'], fixture_task['attempt'])
    return {'build_id': build_id, 'build_key': build, 'tasks': tasks,
            'fixture_receiver': {'task_id': accepted['task_id'], 'outcome': accepted['outcome'], 'fixture': True},
            'exit_code': 0, 'verdict': 'PASS'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--build', default='19270912')
    parser.add_argument('--verified-commit', required=True)
    parser.add_argument('--build-key')
    args = parser.parse_args(argv)
    if not re.fullmatch(r'[1-9][0-9]*', args.build) or (args.build_key and
            not re.fullmatch(r'[0-9a-f]{64}', args.build_key)):
        print(json.dumps({'verdict': 'FAIL', 'exit_code': 2, 'error': 'invalid_build_number'}))
        return 2
    workspace = None
    try:
        config = load_config(args.config)
        parent = config.output('verification')
        parent.mkdir(parents=True, exist_ok=True)
        workspace = Path(tempfile.mkdtemp(prefix='b3a2-', dir=parent))
        result = verify(config, args.build, workspace, selected=args.build_key)
    except FlowError as error:
        result = {'verdict': 'FAIL', 'exit_code': error.code, 'error': error.reason}
        if error.reason in {'analysis_verifier_unique_build_required', 'analysis_verifier_final_logs_required',
                            'analysis_verifier_snapshot_inputs_required',
                            'analysis_verifier_latest_log_registration_invalid'}:
            details = {'build_id': args.build, **error.details,
                       **remediation(args.config, args.verified_commit, args.build, error.details)}
            try:
                allowed = check_content(json_bytes(details), config)['allowed']
            except FlowError:
                allowed = False
            result['details'] = details if allowed else {'candidate_count': error.details.get('candidate_count'),
                                                        'issue': 'verifier_details_credential_blocked'}
        if error.reason in {'lzma_unavailable', 'bz2_unavailable', 'zlib_unavailable', 'sqlite3_unavailable',
                            'log_analyzer_dependency_missing', 'log_analyzer_dependency_probe_failed',
                            'log_analyzer_failed', 'patch_context_failed', 'analysis_patch_format_failed'}:
            result['details'] = error.details
    except (OSError, KeyError, ValueError, TypeError):
        result = {'verdict': 'FAIL', 'exit_code': 5, 'error': 'analysis_verifier_processing_failed'}
    result['commit'] = args.verified_commit
    if workspace:
        try:
            artifact = atomic_write(workspace, 'result.json', json_bytes(result))
            result['artifact'] = artifact['path']
        except (OSError, FlowError):
            result.update(verdict='FAIL', exit_code=5, error='analysis_verifier_summary_failed')
    print(json.dumps(result, ensure_ascii=False))
    return result['exit_code']
