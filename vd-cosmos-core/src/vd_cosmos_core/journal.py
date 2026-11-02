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
    closed = {e['payload'].get('todo_key') for e in store.events(kinds=['inbox_closed'])}
    lines = ['# 待办', ''] + ['- ' + json.dumps(e['payload']['todo'], ensure_ascii=False)
        for e in store.events(kinds=['inbox_opened']) if e['payload'].get('todo_key') not in closed]
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
        execution = data.get('execution_evidence', {})
        todos = [t for t in todos if t['reason'] != 'detail_page_unavailable']
        if execution.get('failure_count', 0) >= 3:
            todos.append({'reason': 'detail_page_unavailable', 'basis_version': execution['failure_started_at']})
        reports = data.get('reports', {})
        ordered = [e for e in outcomes if e['payload'].get('observed_at')]
        if ordered and data.get('observed_at'):
            age = timestamp(data['observed_at']) - timestamp(ordered[0]['payload']['observed_at'])
            limit = config.raw['poll'].get('expected_hours', 24) * 5400
            for arch, report in reports.items():
                since = report.get('unpublished_since')
                if since and any(r.get('settled') for r in reports.values()) and timestamp(data['observed_at']) - timestamp(since) >= config.raw['poll']['arch_lag_s']:
                    todos.append({'reason': 'architecture_lag', 'arch': arch, 'basis_version': since})
                since = report.get('unsettled_since')
                continuous = report.get('continuous', {})
                recent_change = continuous.get('first_seen_at')
                if (since and report.get('change_count', 0) >= 2 and recent_change
                        and timestamp(data['observed_at']) - timestamp(since) > limit
                        and timestamp(data['observed_at']) - timestamp(recent_change) < config.raw['poll']['settle_s']):
                    todos.append({'reason': 'report_continuously_changing', 'arch': arch, 'basis_version': since})
            if age > limit and all(r.get('report_state') == '未发布' for r in reports.values()):
                todos.append({'reason': 'expected_observation_duration_exceeded', 'basis_version': ordered[0]['id']})
        published = [r for r in reports.values() if r.get('continuous')]
        if (published and data.get('effective_execution_state') in {'运行', '排队'}
                and all(timestamp(r['continuous']['last_seen_at']) - timestamp(r['continuous']['first_seen_at']) >= config.raw['poll']['settle_s'] for r in published)):
            from datetime import timedelta
            for report in published:
                try:
                    start = datetime.fromisoformat(report['headers']['start_time'])
                    if start.tzinfo is None:
                        start = start.replace(tzinfo=timezone(timedelta(hours=9)))
                    if timestamp(data['observed_at']) - start.timestamp() > config.raw['poll'].get('expected_hours', 24) * 5400:
                        todos.append({'reason': 'running_but_stable', 'basis_version': fingerprint(data),
                                      'message': '可信来源仍为运行/排队；核实后可 confirm-terminal --override-running 或放弃本轮'})
                        break
                except (KeyError, ValueError):
                    pass
    stats = os.statvfs(config.data_root)
    available = stats.f_bavail * stats.f_frsize
    if available < config.raw.get('budget', {}).get('disk_warning_bytes', 0):
        todos.append({'reason': 'disk_low', 'free_bytes': available,
                      'basis_version': datetime.now(timezone.utc).date().isoformat()})
    return todos
