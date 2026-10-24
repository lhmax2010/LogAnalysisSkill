"""Read-side inbox projections and observation monitoring."""
import json
from .backends import timestamp
from .files import atomic_write, digest, json_bytes


def write_inbox(store, config):
    lines = ['# 待办', ''] + ['- ' + json.dumps(e['payload']['todo'], ensure_ascii=False)
        for e in store.events() if e['kind'] == 'inbox_opened']
    return atomic_write(config.data_root, 'inbox.md', ('\n'.join(lines) + '\n').encode())


def write_todos(store, context, expected, build_key, todos, config):
    seen = {e['payload'].get('todo_key') for e in store.events() if e['kind'] == 'inbox_opened'}
    for todo in todos:
        key = digest(json_bytes({'build': build_key, 'todo': todo}))
        if key not in seen:
            expected = store.append(context, 'inbox_opened', {'todo_key': key, 'todo': todo, 'build': build_key}, expected)
            seen.add(key)
    write_inbox(store, config)
    return expected


def fingerprint(observation):
    return digest(json_bytes({a: r.get('evidence', {}).get('sha256') for a, r in observation['reports'].items()}))


def monitor_todos(config, store, build_key, data):
    todos = list(data.get('todos', []))
    outcomes = [e['payload'] for e in store.events() if e['payload'].get('build') == build_key
                and (e['command'] == 'watch.observe' or e['payload'].get('step') == 'observe')
                and e['kind'] in {'observation_recorded', 'observation_failed', 'workflow_result'}]
    if data.get('exit_code') == 5:
        if len(outcomes) >= 3 and all(p.get('exit_code', 5) == 5 for p in outcomes[-3:]):
            todos.append({'reason': 'three_consecutive_observation_failures'})
    elif data.get('report_state') != '完整' and data.get('reports'):
        distinct = {p['observed_at']: p for p in outcomes if p.get('observed_at') and not p.get('exit_code')}
        ordered = [distinct[k] for k in sorted(distinct)]
        count = config.raw['poll'].get('stall_polls', 6)
        recent = ordered[-count:]
        if len(recent) == count and all(p.get('content_fingerprint') == fingerprint(data) for p in recent):
            if timestamp(recent[-1]['observed_at']) - timestamp(recent[0]['observed_at']) >= (count - 1) * config.raw['poll']['interval_s']:
                todos.append({'reason': 'report_stalled'})
        if ordered and data.get('observed_at') and timestamp(data['observed_at']) - timestamp(ordered[0]['observed_at']) > config.raw['poll'].get('expected_hours', 24) * 5400:
            todos.append({'reason': 'expected_observation_duration_exceeded'})
    if config.filesystem['free_bytes'] < config.raw.get('budget', {}).get('disk_warning_bytes', 0):
        todos.append({'reason': 'disk_low', 'free_bytes': config.filesystem['free_bytes']})
    return todos
