"""Join live final logs with immutable task, snapshot, and result registrations."""
from .analysis_result import invalidated, processing_state
from .diagnosis import version_source
from .errors import FlowError
from .files import digest, json_bytes
from .task_package import build_task, checked_task, snapshot_registration


def active_tasks(config, store, build, logs):
    prepared = {}
    for e in store.events(build, kinds=['analysis_prepared']):
        row = e['payload']
        prepared[digest(json_bytes(row['package']))] = row
    accepted_events = [e['payload'] for e in store.events(build, kinds=['analysis_received'])
                       if not e['payload']['fixture']]
    accepted = {(e['task_id'], e['attempt']) for e in accepted_events}
    pending, received, missing, expired = [], [], [], []
    for log in logs['logs']:
        pkg = log['key']
        row = prepared.get(digest(json_bytes(pkg)))
        if row and row['final_log']['sha256'] != log['sha256']:
            expired.append({'task_id': row['task_id'], 'attempt': row['attempt'], 'state': '输入已过期'})
        if not row or not row.get('skill') or row['final_log']['sha256'] != log['sha256']:
            missing.append(log)
            continue
        if invalidated(store, row) or processing_state(config, store, row) != '有效':
            missing.append(log)
            continue
        try:
            checked_task(config, row)
        except FlowError:
            missing.append(log)
            continue
        ident = {'task_id': row['task_id'], 'attempt': row['attempt'], 'directory': row['directory']}
        (received if (row['task_id'], row['attempt']) in accepted else pending).append(ident)
    current = {(row['task_id'], row['attempt']) for row in received}
    linked = {(row['task_id'], row['attempt']) for row in (*pending, *received)}
    handoffs = []
    for e in accepted_events:
        target = e.get('handoff_target')
        if not target or (e['task_id'], e['attempt']) not in current:
            continue
        row = prepared.get(digest(json_bytes(target)))
        task = {'task_id': row['task_id'], 'attempt': row['attempt']} if row and (
            row['task_id'], row['attempt']) in linked else None
        handoffs.append({'from': e['task_id'], 'package': target, 'target': task})
    state = '任务包已生成' if pending else '分析结果已接收' if received and not missing else '等待任务包'
    return {'pending': pending, 'received': received, 'missing': missing, 'expired': expired,
            'handoffs': handoffs, 'state': state}


def next_candidate(config, store, build, state, view):
    for item in view['missing']:
        try:
            artifact, snapshot = snapshot_registration(config, store, build, item['key'], item['sha256'])
        except FlowError as error:
            if error.reason in {'registered_snapshot_required', 'snapshot_input_mismatch'}:
                continue
            raise
        report = state['observation']['reports'][item['key']['arch']]
        category = next((p['category'] for p in report['packages'] if p['key'] == item['key']), None)
        if category not in {'build_error', 'export_error'}:
            continue
        return item, category, artifact, snapshot
    return None


def prepare_candidate(config, store, build, build_id, state, candidate):
    item, category, artifact, snapshot = candidate
    latest = next((e['payload'] for e in reversed(store.events(build, kinds=['analysis_prepared']))
                   if e['payload']['package'] == item['key']), None)
    build_task(config, store, build, build_id, item, category, artifact, snapshot,
               clang_release=version_source(config, build),
               force_new=bool(latest and invalidated(store, latest)))
    return active_tasks(config, store, build, state['logs'])


def task_counts(view):
    return {field: len(view[field]) for field in ('pending', 'received', 'missing', 'expired')}
