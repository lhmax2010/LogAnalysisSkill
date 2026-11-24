"""Offline analysis acceptance using registered, already-downloaded artifacts."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import re
import sys
import tempfile

from .analysis_result import SCHEMA, accept_result
from .commands import command_context
from .config import load_config
from .diagnosis import version_source
from .errors import FlowError
from .files import atomic_write, digest, json_bytes
from .receipts import logs_valid
from .state import EventStore
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
        raise FlowError(6, 'analysis_verifier_source_database_required')
    if before != [read(path) for path in paths]:
        raise FlowError(6, 'analysis_verifier_source_database_busy')
    for path, raw in zip(paths, before):
        if raw is not None:
            atomic_write(scratch, 'state/' + path.name, raw)


def locate_logs(config, source, build_id):
    candidates, rejected = {}, set()
    for e in reversed(source.events(kinds=['observation_recorded', 'workflow_result'])):
        p = e['payload']
        if (p.get('step') != 'logs' and e['command'] != 'fetch.logs'
                or p.get('exit_code') or not p.get('artifact')):
            continue
        key = p.get('build')
        if key in candidates:
            continue
        try:
            data = json.loads(checked_file(config, p['artifact']))
        except (FlowError, ValueError, OSError, KeyError):
            rejected.add(key)
            continue
        identity = data.get('observation', {}).get('build_ref', {})
        if str(identity.get('run_id')) == build_id:
            if key in rejected:
                raise FlowError(4, 'analysis_verifier_latest_log_registration_invalid')
            if digest(json_bytes(identity)) != key:
                raise FlowError(4, 'analysis_verifier_build_identity_mismatch')
            candidates[key] = data
    if len(candidates) != 1:
        raise FlowError(6, 'analysis_verifier_unique_build_required')
    build, data = next(iter(candidates.items()))
    observed = data['observation']
    expected = {tuple(p['key'][k] for k in ('name', 'arch', 'path')): p['category']
                for report in observed['reports'].values() for p in report.get('packages', [])
                if p['category'] in {'build_error', 'export_error'}}
    supplied = [tuple(item['key'][k] for k in ('name', 'arch', 'path')) for item in data['logs']]
    if not supplied or len(supplied) != len(set(supplied)) or expected.keys() != set(supplied):
        raise FlowError(6, 'analysis_verifier_failure_log_coverage')
    if not logs_valid(config, data, observed):
        raise FlowError(6, 'analysis_verifier_final_logs_required')
    return build, data, expected


def stage_local_inputs(config, target, source, build, data, expected):
    local_logs, snapshots = [], []
    for index, item in enumerate(data['logs']):
        path = f'source/{index}'
        package = item['key']
        category = expected[tuple(package[k] for k in ('name', 'arch', 'path'))]
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


def verify(config, build_id, workspace):
    db_copy = workspace / 'source-db'
    db_copy.mkdir(mode=0o700)
    copy_database(config, db_copy)
    safe_analyzer = dict(config.raw['analyzer'], cline_extension={})
    target = replace(config, data_root=workspace, raw={**config.raw, 'analyzer': safe_analyzer})
    with EventStore(db_copy) as source:
        build, original, expected = locate_logs(config, source, build_id)
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
    args = parser.parse_args(argv)
    if not re.fullmatch(r'[0-9]+', args.build):
        print(json.dumps({'verdict': 'FAIL', 'exit_code': 2, 'error': 'invalid_build_number'}))
        return 2
    workspace = None
    try:
        config = load_config(args.config)
        parent = config.output('verification')
        parent.mkdir(parents=True, exist_ok=True)
        workspace = Path(tempfile.mkdtemp(prefix='b3a2-', dir=parent))
        result = verify(config, args.build, workspace)
    except FlowError as error:
        result = {'verdict': 'FAIL', 'exit_code': error.code, 'error': error.reason}
        if error.reason in {'lzma_unavailable', 'bz2_unavailable', 'zlib_unavailable', 'sqlite3_unavailable'}:
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
