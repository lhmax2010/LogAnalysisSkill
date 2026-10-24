"""Read-only ticks with durable evaluation identities and bounded retries."""
import re
import shutil
import signal
import threading
import uuid
from vd_cosmos_core.commands import command_context
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.files import atomic_write, digest, json_bytes, load_json
from vd_cosmos_core.journal import fingerprint, monitoring_fields, monitor_todos, write_todos, write_inbox
from vd_cosmos_core.locks import OperationLock
from vd_cosmos_core.observation import stopped
from vd_cosmos_core.state import EventStore, append_retry
from vd_cosmos_core.versions import build_key, evaluation
from vd_cosmos_watch.api import observe
from vd_cosmos_fetch.api import fetch_logs


def load_artifact(config, artifact):
    path = config.output(artifact['path'])
    if digest(path.read_bytes()) != artifact['sha256']:
        raise FlowError(6, 'workflow_artifact_digest_mismatch')
    return load_json(path)


def projection(config, store, key):
    state = {'phase': '构建中', 'observation': None, 'logs': None, 'todos': [], 'completed_evaluation': None}
    latest = {}
    for event in store.events(key):
        payload = event['payload']
        if event['kind'] == 'workflow_result' and payload.get('phase') == '结果已拉取' and not payload.get('exit_code'):
            state['completed_evaluation'] = payload.get('evaluation')
            state['phase'] = '结果已拉取'
        if event['kind'] not in {'workflow_result', 'observation_recorded', 'observation_failed'}:
            continue
        if payload.get('step') == 'observe' or event['command'] == 'watch.observe':
            latest['observation'] = payload
        if (payload.get('step') == 'logs' or event['command'] == 'fetch.logs') and not payload.get('exit_code'):
            latest['logs'] = payload
    for field, payload in latest.items():
        try:
            state[field] = load_artifact(config, payload['artifact'])
        except (FlowError, OSError, KeyError, ValueError):
            state['phase'] = '构建中'
            state['todos'].append({'reason': 'artifact_unavailable', 'arch': field,
                                   'basis_version': payload.get('artifact', {}).get('sha256', payload.get('attempt'))})
    return state


def ready(observation):
    return (observation and not observation.get('observation_failed') and observation.get('report_state') == '完整'
            and observation.get('header_consistency') == '一致' and not stopped(observation))


def clean_unfinished(config, store, key):
    events = store.events(key, kinds=['workflow_intent', 'workflow_result'])
    completed = {e['operation_id'] for e in events if e['kind'] == 'workflow_result'}
    for event in events:
        attempt = event['payload'].get('attempt', '')
        if event['kind'] != 'workflow_intent' or event['operation_id'] in completed or not re.fullmatch('[0-9a-f]{32}', attempt):
            continue
        raw = config.data_root / f'rounds/{key}/attempt-{attempt}'
        if raw.is_symlink():
            continue
        path = config.output(raw)
        if path.is_dir():
            shutil.rmtree(path)


def tick(config, reader_factory, *, expected_event=None, after_intent=None, after_action=None, loop_driven=False):
    reader = reader_factory()
    key = build_key(reader)
    context = command_context('workflow.tick')
    retry = loop_driven and expected_event is None
    with OperationLock(config.data_root, 'round', key), EventStore(config.data_root) as store:
        expected = store.head() if expected_event is None else expected_event
        if expected != store.head():
            raise FlowError(6, 'stale_head')
        clean_unfinished(config, store, key)
        state = projection(config, store, key)
        previous = state['observation']
        if (state['phase'] == '结果已拉取' and previous and state['logs']
                and state['completed_evaluation'] == evaluation(reader, previous)):
            write_inbox(store, config)
            return {'phase': state['phase'], 'exit_code': 0, 'last_event_id': store.head(), 'action': 'none'}
        step = 'observe'
        if ready(previous) and not state['todos']:
            step = 'logs'
            if (state['logs'] and state['logs'].get('evaluation') == evaluation(reader, previous)):
                step = 'notify'
        # Changed baseline/config requires a fresh observation even with cached
        # complete pages. Projection cannot promote a stale evaluation.
        if previous and previous.get('evaluation') != evaluation(reader, previous):
            step = 'observe'
        attempt = uuid.uuid4().hex
        current = append_retry(store, context, 'workflow_intent', {'build': key, 'step': step, 'attempt': attempt},
                               expected, operation_id=attempt, retry=retry)
        if after_intent:
            after_intent()
        try:
            if step == 'observe':
                data = observe(reader)
            elif step == 'logs':
                fresh = observe(reader)
                if not ready(fresh) or fingerprint(fresh) != fingerprint(previous):
                    step, data = 'observe', fresh
                else:
                    data = fetch_logs(reader, fresh)
                    data['evaluation'] = evaluation(reader, fresh)
            else:
                count = len(state['logs']['logs'])
                data = {'exit_code': 0, 'failed_package_count': count,
                        'todos': [{'reason': 'analysis_pending', 'count': count,
                                   'basis_version': evaluation(reader, previous),
                                   'message': f'有 {count} 个失败包待分析（第 3 批接分析）'}]}
        except FlowError as error:
            data = {'exit_code': error.code, 'error': error.reason,
                    'todos': [error.details['todo']] if error.details.get('todo') else []}
            if error.details.get('request_evidence'):
                data['request_evidence'] = error.details['request_evidence']
        except (OSError, UnicodeError, ValueError, KeyError, TypeError):
            data = {'exit_code': 5, 'error': 'workflow_action_failed', 'todos': []}
        if step == 'observe':
            data['evaluation'] = evaluation(reader, data)
            if previous and stopped(previous) and fingerprint(previous) != fingerprint(data):
                data.setdefault('todos', []).append({'reason': 'report_basis_changed', 'basis_version': fingerprint(data),
                    'message': '此前待办所依据的报告已变化，已重新判定'})
        code = data.get('exit_code', 0)
        phase = ('结果已拉取' if step == 'notify' and not code else
                 '停止推进' if step == 'observe' and stopped(data) else
                 '报告已完整' if step in {'logs', 'notify'} or ready(data) else '构建中')
        artifact = atomic_write(config.data_root, f'rounds/{key}/attempt-{attempt}/workflow-{step}.json', json_bytes(data))
        payload = {'build': key, 'step': step, 'attempt': attempt, 'phase': phase,
                   'exit_code': code, 'artifact': artifact}
        if step == 'observe':
            payload.update(monitoring_fields(data))
        if step == 'notify':
            payload['evaluation'] = evaluation(reader, previous)
            if not code:
                current = write_todos(store, context, current, key, data['todos'], config, retry=retry)
        if after_action:
            after_action(step)
        current = append_retry(store, context, 'workflow_result', payload, current, operation_id=attempt, retry=retry)
        todos = monitor_todos(config, store, key, data, step=step) + state['todos']
        current = write_todos(store, context, current, key, todos, config, retry=retry)
        return {'phase': phase, 'action': step, 'exit_code': code, 'last_event_id': current, 'artifact': artifact}


def loop(config, reader_factory, *, max_ticks=None, on_sleep=None, expected_event=None):
    if max_ticks is not None and (type(max_ticks) is not int or max_ticks < 1):
        raise FlowError(2, 'invalid_max_ticks')
    stop = threading.Event()
    old_handlers = {}
    if threading.current_thread() is threading.main_thread():
        for sig in (signal.SIGINT, signal.SIGTERM):
            old_handlers[sig] = signal.signal(sig, lambda *_: stop.set())
    results, contention = [], 0
    try:
        with OperationLock(config.data_root, 'loop', 'singleton'):
            while not stop.is_set() and (max_ticks is None or len(results) < max_ticks):
                try:
                    result = tick(config, reader_factory, loop_driven=True, expected_event=expected_event)
                    if expected_event is not None:
                        expected_event = result['last_event_id']
                    contention = 0
                except FlowError as error:
                    if error.reason != 'operation_locked':
                        raise
                    contention += 1
                    result = {'phase': '构建中', 'exit_code': 6, 'action': 'skipped', 'skip_count': contention}
                    if contention == 3:
                        key = build_key(reader_factory())
                        with EventStore(config.data_root) as store:
                            write_todos(store, command_context('workflow.loop'), store.head(), key,
                                        [{'reason': 'loop_contention', 'basis_version': 'active_contention'}], config, retry=True)
                results.append(result)
                if result['phase'] == '结果已拉取' or contention == 3:
                    break
                if result['exit_code'] not in {0, 3, 5} and result['action'] != 'skipped':
                    break
                if max_ticks is not None and len(results) == max_ticks:
                    break
                if on_sleep:
                    on_sleep()
                interval = config.raw['poll']['stopped_interval_s'] if result['phase'] == '停止推进' else config.raw['poll']['interval_s']
                stop.wait(interval)
    finally:
        for sig, previous in old_handlers.items():
            signal.signal(sig, previous)
    final = results[-1] if results else {'exit_code': 0, 'phase': '构建中'}
    return {**final, 'ticks': len(results), 'interrupted': stop.is_set(), 'tick_results': results}


def status(config, reader=None):
    with EventStore(config.data_root) as store:
        if reader is None:
            return {'last_event_id': store.head()}
        state = projection(config, store, build_key(reader))
        if state['observation'] and state['completed_evaluation'] != evaluation(reader, state['observation']):
            state['phase'] = '构建中'
        return {'phase': state['phase'], 'last_event_id': store.head(), 'todos': state['todos']}


def inbox(config):
    with EventStore(config.data_root) as store:
        return {'artifact': write_inbox(store, config), 'last_event_id': store.head()}
