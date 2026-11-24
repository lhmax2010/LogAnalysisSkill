"""Public read operations shared by skill APIs and their CLI adapters."""
import uuid
from .backends import FixtureReportReader, SavedReportReader
from .http_reader import HTTPReportReader
from .errors import FlowError
from .groups import group_expansion
from .commands import command_context
from .files import atomic_write, json_bytes
from .journal import write_todos, monitor_todos, monitoring_fields
from .locks import OperationLock
from .state import EventStore, append_retry
from .versions import build_key, evaluation


def make_reader(config, backend, *, build_id=None, manifest=None, expected_rows=None):
    if backend == 'real' and build_id is not None:
        return HTTPReportReader(config, build_id, expected_rows)
    if not manifest:
        raise FlowError(2, 'build_id_required' if backend == 'real' else 'manifest_required')
    return (FixtureReportReader if backend == 'fixture' else SavedReportReader)(config, manifest)


def observe(reader):
    return reader.observe(reader.build_ref)


def fetch_logs(reader, observed=None, *, partial=False):
    observed = observed if observed is not None else observe(reader)
    if observed['observation_failed']:
        return observed
    if observed.get('exit_code') == 3:
        return observed
    reader.require('fetch_log')
    packages = [p for r in observed['reports'].values() for p in r.get('packages', [])
                if p['category'] in {'build_error', 'export_error'}]
    if partial:
        # Only explicit input preparation registers successful downloads from a mixed outcome.
        logs, failures = [], []
        for package in packages:
            key = package['key']
            try:
                logs.append({'key': key, **reader.fetch_log(reader.build_ref, key['arch'], package)})
            except FlowError as error:
                failures.append({'key': key, 'reason': error.reason})
    elif hasattr(reader, 'fetch_logs'):
        logs = reader.fetch_logs(packages)
    else:
        logs = [{'key': p['key'], **reader.fetch_log(reader.build_ref, p['key']['arch'], p)} for p in packages]
    result = {'logs': logs, 'todos': observed['todos'], 'observation': observed,
              'exit_code': 0, 'evaluation': evaluation(reader, observed)}
    if partial:
        result['log_failures'] = failures
    return result


def read_action(skill, command, reader, arch=None, *, partial_logs=False):
    if skill == 'watch':
        return observe(reader)
    if command == 'base-list':
        from .build_inputs import fetch_build_inputs
        return fetch_build_inputs(reader)
    if command == 'inputs':
        return reader.read_inputs(reader.build_ref)
    if command == 'packages':
        if not arch:
            raise FlowError(2, 'architecture_required')
        observed = observe(reader)
        if observed['observation_failed']:
            return observed
        return {**reader.read_packages(reader.build_ref, arch), 'todos': observed['todos'], 'exit_code': 0}
    if command == 'logs':
        return fetch_logs(reader, partial=partial_logs)
    observed = observe(reader)
    if observed['observation_failed']:
        return observed
    packages = [p for r in observed['reports'].values() for p in r.get('packages', [])]
    return {**group_expansion(packages, reader.provides()), 'todos': observed['todos']}


def register_read(config, reader, skill, command, *, arch=None, expected_event=None,
                  precheck=None, cached=None, partial_logs=False):
    """Run and register the same read for scripted and individual CLI flows."""
    context = command_context(f'{skill}.{command}')
    key = build_key(reader)
    with OperationLock(config.data_root, 'round', key), EventStore(config.data_root) as store:
        if precheck:
            precheck(store)
        if cached:
            prior = cached(store)
            if prior is not None:
                return None, prior
        expected = store.head() if expected_event is None else expected_event

        def append(kind, payload, head):
            return append_retry(store, context, kind, payload, head, heartbeat_retry=expected_event is None)

        attempt = uuid.uuid4().hex
        current = append('observation_started', {'attempt': attempt, 'build': key}, expected)
        step = 'logs' if command == 'logs' else 'observe'
        try:
            data = read_action(skill, command, reader, arch, partial_logs=partial_logs)
        except FlowError as error:
            current = append('observation_failed', {'attempt': attempt, 'build': key,
                             'reason': error.reason, 'exit_code': error.code}, current)
            error_data = {'exit_code': error.code, 'todos': [error.details['todo']] if error.details.get('todo') else []}
            todos = monitor_todos(config, store, key, error_data, step=step)
            write_todos(store, context, current, key, todos, config, heartbeat_retry=expected_event is None)
            raise
        if skill == 'watch':
            data['evaluation'] = evaluation(reader, data)
        code = data.get('exit_code', 0)
        artifact = atomic_write(config.data_root, f'rounds/{key}/attempt-{attempt}/{skill}-{command}.json',
                                json_bytes(data))
        fields = ('execution_state', 'report_state', 'result_state', 'header_consistency', 'package_coverage')
        payload = {'build': key, 'attempt': attempt, 'artifact': artifact, 'exit_code': code,
                   **{field: data.get(field) for field in fields if field != 'execution_state'}}
        if skill == 'watch':
            payload.update(monitoring_fields(data))
        current = append('observation_failed' if code else 'observation_recorded', payload, current)
        todos = monitor_todos(config, store, key, data, step=step)
        current = write_todos(store, context, current, key, todos, config, heartbeat_retry=expected_event is None)
    return {'artifact': artifact, 'last_event_id': current, 'exit_code': code,
            **{field: data[field] for field in fields if field in data}}, data
