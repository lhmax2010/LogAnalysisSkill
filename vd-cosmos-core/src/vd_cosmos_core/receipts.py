"""Shared terminal/log/input predicates; no authorization is created here."""
from .files import digest, json_bytes
from .state import EventStore


def report_digests(reports):
    return {a: ('未发布' if r.get('report_state') == '未发布' else r.get('evidence', {}).get('sha256'))
            for a, r in reports.items()}


def manual_terminal(config, key, reports, invalidated):
    with EventStore(config.data_root) as store:
        events = store.events(key, kinds=['terminal_confirmed', 'terminal_withdrawn'])
    if not events or events[-1]['kind'] == 'terminal_withdrawn':
        return None
    event = events[-1]
    if event['id'] in invalidated:
        return None
    bound = event['payload'].get('report_digests')
    actual = report_digests(reports)
    # A failed observation is not evidence that a digest changed.
    if bound and any(actual.get(a) is not None and actual[a] != sha for a, sha in bound.items()):
        invalidated.append(event['id'])
        return None
    return {**event['payload'], 'event_id': event['id'], 'confirmed_at': event['created_at']} if bound and set(bound) == set(reports) else None


def terminal_basis(execution, manual=None):
    if manual:
        return {'kind': 'manual_terminal', 'event_id': manual['event_id'], 'epoch': manual['confirmed_at']}
    if execution.get('effective_state') == '已结束' and execution.get('terminal_epoch'):
        return {'kind': 'trusted_terminal', 'epoch': execution['terminal_epoch']}
    return None


def log_binding(observation, arch, limit, url):
    report = observation['reports'][arch]
    basis = observation.get('effective_terminal_basis')
    state = observation.get('effective_execution_state', '未知')
    final_stage = bool(report.get('settled') and (state not in {'运行', '排队'} or basis))
    return {'report_sha256': report.get('evidence', {}).get('sha256'), 'max_log_bytes': limit,
            'url_sha256': digest(url.encode()), 'settled_basis': report.get('settled_basis'),
            'execution_state': state, 'terminal_basis': basis, 'final_stage': final_stage}


def logs_valid(config, logs, observation):
    if not logs or not observation:
        return False
    try:
        for item in logs['logs']:
            path = config.output(item['path'])
            if not path.is_file() or path.stat().st_size != item['size'] or digest(path.read_bytes()) != item['sha256']:
                return False
            if not item.get('final', False):
                return False
            binding = item['binding']
            arch = item['key']['arch']
            report = observation['reports'][arch]
            if (not report.get('settled')
                    or (observation.get('effective_execution_state') in {'运行', '排队'} and not observation.get('effective_terminal_basis'))
                    or binding['report_sha256'] != report.get('evidence', {}).get('sha256')
                    or binding['max_log_bytes'] != config.raw['fetch']['max_log_bytes']
                    or binding['terminal_basis'] != observation.get('effective_terminal_basis')
                    or binding['settled_basis'] != observation['reports'][arch].get('settled_basis')):
                return False
        return True
    except (KeyError, OSError, ValueError):
        return False


def task_input_digest(final_log_sha256, snapshot_manifest_sha256, segment_manifest_sha256, rules_version):
    return digest(json_bytes({'final_log': final_log_sha256, 'snapshot_manifest': snapshot_manifest_sha256,
                              'segments': segment_manifest_sha256, 'rules': rules_version}))


def accepted_result_state(result, package, input_digest):
    if result.get('package') != package or not result.get('validated'):
        return '无可用结果'
    return '有效' if result.get('task_input_digest') == input_digest else '输入已过期'
