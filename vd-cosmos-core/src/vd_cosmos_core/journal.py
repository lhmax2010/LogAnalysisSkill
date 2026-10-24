"""Deduplicated, versioned read-side inbox and live monitoring."""
from datetime import datetime, timezone
import json
import os
from .backends import timestamp
from .files import atomic_write, digest, json_bytes
from .state import append_retry


def sorted_body(value):
    if isinstance(value, dict):
        return {k: sorted_body(v) for k, v in value.items()}
    if isinstance(value, list):
        return sorted((sorted_body(v) for v in value), key=lambda v: json.dumps(v, sort_keys=True, ensure_ascii=False))
    return value


def write_inbox(store, config):
    lines = ['# 待办', ''] + ['- ' + json.dumps(e['payload']['todo'], ensure_ascii=False)
        for e in store.events(kinds=['inbox_opened'])]
    return atomic_write(config.data_root, 'inbox.md', ('\n'.join(lines) + '\n').encode())


def write_todos(store, context, expected, build_key, todos, config, *, retry=False):
    seen = {e['payload'].get('todo_key') for e in store.events(build_key, kinds=['inbox_opened'])}
    for original in todos:
        todo = sorted_body(original)
        identity = {'build': build_key, 'arch': todo.get('arch'), 'reason': todo['reason'],
                    'basis_version': todo.get('basis_version', 'unversioned')}
        key = digest(json_bytes(identity))
        if key not in seen:
            expected = append_retry(store, context, 'inbox_opened', {'todo_key': key, 'todo': todo, 'build': build_key}, expected, retry=retry)
            seen.add(key)
    write_inbox(store, config)
    return expected


def fingerprint(observation):
    return digest(json_bytes({a: r.get('evidence', {}).get('sha256') for a, r in observation.get('reports', {}).items()}))


def monitoring_fields(data):
    execution = data.get('execution_evidence', {})
    return {'content_fingerprint': fingerprint(data), 'observed_at': data.get('observed_at'),
            'detail_failed': bool(execution.get('detail_attempted') and execution.get('state') == '未知')}


def failure_run(events, field):
    consecutive = []
    for event in reversed(events):
        if not field(event['payload']):
            break
        consecutive.append(event)
    return consecutive


def monitor_todos(config, store, build_key, data, *, step='observe'):
    todos = list(data.get('todos', []))
    outcomes = [e for e in store.events(build_key, kinds=['observation_recorded', 'observation_failed', 'workflow_result'])
                if e['payload'].get('step') == step or e['command'] == ('watch.observe' if step == 'observe' else 'fetch.logs')]
    failed = failure_run(outcomes, lambda p: p.get('exit_code') in {4, 5})
    if len(failed) >= 3:
        todos.append({'reason': 'three_consecutive_observation_failures' if step == 'observe' else 'log_download_unavailable',
                      'basis_version': failed[-1]['id']})
    if step == 'observe':
        detail = failure_run(outcomes, lambda p: p.get('detail_failed'))
        todos = [t for t in todos if t['reason'] != 'detail_page_unavailable']
        if len(detail) >= 3 or data.get('execution_evidence', {}).get('failure_count', 0) >= 3:
            todos.append({'reason': 'detail_page_unavailable', 'basis_version': detail[-1]['id'] if detail else store.head()})
        ordered = [e for e in outcomes if e['payload'].get('observed_at')]
        reports = data.get('reports', {})
        waiting = (data.get('report_state') == '部分' and reports and
                   all(r.get('report_state') != '未发布' for r in reports.values()) and
                   any(r.get('evidence') for r in reports.values()))
        if waiting:
            count = config.raw['poll'].get('stall_polls', 6)
            recent = ordered[-count:]
            if len(recent) == count and all(e['payload'].get('content_fingerprint') == fingerprint(data) for e in recent):
                if timestamp(recent[-1]['payload']['observed_at']) - timestamp(recent[0]['payload']['observed_at']) >= (count - 1) * config.raw['poll']['interval_s']:
                    todos.append({'reason': 'report_stalled', 'basis_version': fingerprint(data)})
        if ordered and data.get('observed_at') and timestamp(data['observed_at']) - timestamp(ordered[0]['payload']['observed_at']) > config.raw['poll'].get('expected_hours', 24) * 5400:
            todos.append({'reason': 'expected_observation_duration_exceeded', 'basis_version': ordered[0]['id']})
    stats = os.statvfs(config.data_root)
    available = stats.f_bavail * stats.f_frsize
    if available < config.raw.get('budget', {}).get('disk_warning_bytes', 0):
        todos.append({'reason': 'disk_low', 'free_bytes': available,
                      'basis_version': datetime.now(timezone.utc).date().isoformat()})
    return todos
