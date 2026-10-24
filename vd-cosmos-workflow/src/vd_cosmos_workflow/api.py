"""One action per tick, durable attempts and fresh projections after every sleep."""
import signal
import threading
import uuid

from vd_cosmos_core.commands import command_context
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.files import atomic_write, digest, json_bytes, load_json
from vd_cosmos_core.journal import fingerprint, monitor_todos, write_todos, write_inbox
from vd_cosmos_core.locks import OperationLock
from vd_cosmos_core.state import EventStore
from vd_cosmos_watch.api import observe
from vd_cosmos_fetch.api import fetch_logs


def build_key(reader):
    return digest(json_bytes(reader.build_ref.to_dict()))


def load_artifact(config, artifact):
    path = config.output(artifact['path'])
    if digest(path.read_bytes()) != artifact['sha256']:
        raise FlowError(6, 'workflow_artifact_digest_mismatch')
    return load_json(path)


def projection(config, store, key):
    state = {'phase': '构建中', 'observation': None, 'logs': None}
    for event in store.events():
        payload = event['payload']
        if payload.get('build') != key:
            continue
        if event['kind'] == 'workflow_result' and payload.get('phase') == '结果已拉取' and not payload.get('exit_code'):
            state['phase'] = '结果已拉取'
        if event['kind'] not in {'workflow_result', 'observation_recorded', 'observation_failed'} or not payload.get('artifact'):
            continue
        if payload.get('step') == 'observe' or event['command'] == 'watch.observe':
            state['observation'] = load_artifact(config, payload['artifact'])
        if (payload.get('step') == 'logs' or event['command'] == 'fetch.logs') and not payload.get('exit_code'):
            state['logs'] = load_artifact(config, payload['artifact'])
    return state


def stopped(observation):
    return (observation.get('report_state') in {'对账失败', '结构未知'}
            or observation.get('header_consistency') == '不一致'
            or observation.get('package_coverage') == '不一致')


def ready(observation):
    return (observation and not observation.get('exit_code') and observation.get('report_state') == '完整'
            and observation.get('header_consistency') == '一致' and observation.get('package_coverage') != '不一致')


def tick(config, reader_factory, *, expected_event=None, after_intent=None):
    reader = reader_factory()
    key = build_key(reader)
    context = command_context('workflow.tick')
    with OperationLock(config.data_root, 'round', key), EventStore(config.data_root) as store:
        expected = store.head() if expected_event is None else expected_event
        if expected != store.head():
            raise FlowError(6, 'concurrent_event_conflict')
        state = projection(config, store, key)
        if state['phase'] == '结果已拉取':
            return {'phase': state['phase'], 'exit_code': 0, 'last_event_id': store.head(), 'action': 'none'}
        step = 'observe'
        previous = state['observation']
        if ready(previous):
            step = 'logs'
            if state['logs'] and fingerprint(state['logs']['observation']) == fingerprint(previous):
                step = 'notify'
        attempt = uuid.uuid4().hex
        current = store.append(context, 'workflow_intent', {'build': key, 'step': step, 'attempt': attempt},
                               expected, operation_id=attempt)
        if after_intent:
            after_intent()
        try:
            if step == 'observe':
                data = observe(reader)
            elif step == 'logs':
                data = fetch_logs(reader, previous)
            else:
                count = len(state['logs']['logs'])
                data = {'exit_code': 0, 'failed_package_count': count,
                        'todos': [{'reason': 'analysis_pending', 'count': count,
                                   'message': f'有 {count} 个失败包待分析（第 3 批接分析）'}]}
        except FlowError as error:
            data = {'exit_code': error.code, 'error': error.reason,
                    'todos': [error.details['todo']] if error.details.get('todo') else []}
        except (OSError, UnicodeError, ValueError, KeyError, TypeError):
            data = {'exit_code': 5, 'error': 'workflow_action_failed', 'todos': []}
        code = data.get('exit_code', 0)
        if step == 'observe' and not code and stopped(data):
            code = 3
        phase = ('结果已拉取' if step == 'notify' and not code else
                 '报告已完整' if step in {'logs', 'notify'} or ready(data) else '构建中')
        artifact = atomic_write(config.data_root, f'rounds/{key}/attempt-{attempt}/workflow-{step}.json', json_bytes(data))
        payload = {'build': key, 'step': step, 'attempt': attempt, 'phase': phase,
                   'exit_code': code, 'artifact': artifact}
        if step == 'observe' and data.get('reports'):
            payload.update(content_fingerprint=fingerprint(data), observed_at=data.get('observed_at'))
        # Notification is the action of this step. Commit its idempotent inbox
        # event before the result advances the phase, so a crash cannot leave a
        # finished round without its analysis todo.
        if step == 'notify' and not code:
            current = write_todos(store, context, current, key, data['todos'], config)
        current = store.append(context, 'workflow_result', payload, current, operation_id=attempt)
        todos = monitor_todos(config, store, key, data) if step == 'observe' else data.get('todos', [])
        current = write_todos(store, context, current, key, todos, config)
        return {'phase': phase, 'action': step, 'exit_code': code, 'last_event_id': current, 'artifact': artifact}


def loop(config, reader_factory, *, max_ticks=None, on_sleep=None):
    if max_ticks is not None and (type(max_ticks) is not int or max_ticks < 1):
        raise FlowError(2, 'invalid_max_ticks')
    stop = threading.Event()
    old_handlers = {}
    if threading.current_thread() is threading.main_thread():
        for sig in (signal.SIGINT, signal.SIGTERM):
            old_handlers[sig] = signal.signal(sig, lambda *_: stop.set())
    results = []
    try:
        with OperationLock(config.data_root, 'loop', 'singleton'):
            while not stop.is_set() and (max_ticks is None or len(results) < max_ticks):
                result = tick(config, reader_factory)
                results.append(result)
                if result['phase'] == '结果已拉取' or result['exit_code'] not in {0, 5}:
                    break
                if max_ticks is not None and len(results) == max_ticks:
                    break
                # Only the lifecycle instance lock remains held here. tick has
                # closed SQLite and released its round lock before returning.
                if on_sleep:
                    on_sleep()
                stop.wait(config.raw['poll']['interval_s'])
    finally:
        for sig, previous in old_handlers.items():
            signal.signal(sig, previous)
    final = results[-1] if results else {'exit_code': 0, 'phase': '构建中'}
    return {**final, 'ticks': len(results), 'interrupted': stop.is_set(), 'tick_results': results}


def status(config, reader=None):
    with EventStore(config.data_root) as store:
        if reader is None:
            return {'last_event_id': store.head(), 'events': len(store.events())}
        state = projection(config, store, build_key(reader))
        return {'phase': state['phase'], 'last_event_id': store.head()}


def inbox(config):
    with EventStore(config.data_root) as store:
        return {'artifact': write_inbox(store, config), 'last_event_id': store.head()}
