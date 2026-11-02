"""Journaled immutable snapshot attempts; task preparation is intentionally absent."""
import uuid
from pathlib import Path
from vd_cosmos_core.backends import FixtureReportReader
from vd_cosmos_core.commands import command_context
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.files import atomic_write, digest, json_bytes, load_json
from vd_cosmos_core.journal import write_todos
from vd_cosmos_core.locks import OperationLock
from vd_cosmos_core.p4 import P4Adapter
from vd_cosmos_core.receipts import logs_valid
from vd_cosmos_core.state import EventStore
from vd_cosmos_core.versions import build_key
from .snapshot import snapshot


def unclassified_count(events, package):
    count = 0
    for event in events:
        p = event['payload']
        if p.get('package') != package:
            continue
        if event['kind'] == 'inbox_closed' and p.get('todo_reason') == 'p4_unclassified':
            count = 0
        elif event['kind'] in {'snapshot_completed', 'snapshot_failed'}:
            count = count + 1 if p.get('error') == 'p4_unclassified' else 0
    return count


def write_round_report(config, store, key):
    latest = {}
    for event in store.events(key, kinds=['snapshot_completed']):
        latest[digest(json_bytes(event['payload']['package']))] = event['payload']
    lines = ['# 本轮源码快照', '', '| 包 | 架构 | 结论 | 来源依据与通知 |', '|---|---|---|---|']
    for payload in latest.values():
        artifact = payload['artifact']
        raw = config.output(artifact['path']).read_bytes()
        if digest(raw) != artifact['sha256']:
            raise FlowError(4, 'immutable_snapshot_digest_mismatch')
        data = load_json(artifact['path'])
        fields = sorted({f['snapshot_provenance'] for f in data.get('files', [])})
        fields += [n.get('message', n['reason']) for n in data.get('notices', [])]
        cell = '；'.join(fields).replace('|', '\\|').replace('\n', ' ')
        package = payload['package']
        lines.append(f"| {package['name']} | {package['arch']} | {data['mode']} | {cell} |")
    return atomic_write(config.data_root, f'rounds/{key}/reports/source-snapshots.md', ('\n'.join(lines)+'\n').encode())


def create_snapshot(config, reader, name, arch, log_path, *, expected_event=None, tickets_override=None):
    key, context = build_key(reader), command_context('analyze.snapshot')
    with OperationLock(config.data_root, 'round', key), EventStore(config.data_root) as store:
        expected = store.head() if expected_event is None else expected_event
        if expected != store.head():
            raise FlowError(6, 'stale_head')
        observed = reader.observe(reader.build_ref)
        packages = [p for p in observed['reports'].get(arch, {}).get('packages', []) if p['key']['name'] == name]
        if len(packages) != 1:
            raise FlowError(2, 'unique_package_required')
        package = packages[0]
        count = unclassified_count(store.events(key), package['key'])
        if count >= config.raw['p4']['unclassified_retry_limit']:
            raise FlowError(3, 'p4_unclassified_retry_exhausted')
        attempt = uuid.uuid4().hex
        folder = f'rounds/{key}/snapshots/{attempt}'
        current = store.append(context, 'snapshot_started', {'build': key, 'package': package['key'], 'attempt': attempt}, expected)
        try:
            path = config.output(log_path)
            metadata = load_json(str(path)+'.json') if config.output(str(path)+'.json').exists() else {}
            if not metadata:
                raise FlowError(6, 'final_log_required')
            if metadata.get('key') != package['key'] or not logs_valid(config, {'logs': [metadata]}, observed):
                raise FlowError(4, 'final_log_required')
            lists_path = config.output(f'rounds/{key}/inputs/build-lists/manifest.json')
            lists = load_json(lists_path) if lists_path.exists() else None
            if lists:
                for artifact in lists['files'].values():
                    if digest(config.output(artifact['path']).read_bytes()) != artifact['sha256']:
                        raise FlowError(4, 'immutable_input_digest_mismatch')
            confirmations = [e['payload']['shelve_digest'] for e in store.events(key, kinds=['input_confirmed']) if e['payload'].get('package')==package['key']]
            binding = digest(json_bytes({'log': digest(path.read_bytes()), 'lists': (lists or {}).get('digests'),
                'confirmations': confirmations, 'snapshot_code': digest((Path(__file__).parent / 'snapshot.py').read_bytes())}))
            prior = store.events(key, kinds=['snapshot_completed'])
            for event in reversed(prior):
                if event['payload'].get('package') != package['key']:
                    continue
                saved = event['payload'].get('artifact')
                if saved and digest(config.output(saved['path']).read_bytes()) == saved['sha256']:
                    old = load_json(saved['path'])
                    if old.get('historical_input_unrecoverable') and old.get('input_binding') == binding:
                        current = store.append(context, 'snapshot_completed', {'build': key, 'package': package['key'], 'attempt': attempt, 'artifact': saved, 'reused': True}, current)
                        return {'artifact': saved, 'mode': '仅诊断', 'skipped': True, 'last_event_id': current, 'exit_code': 0}
                break
            if isinstance(reader, FixtureReportReader) and reader.manifest.get('p4_fixture'):
                from vd_cosmos_core.files import confined
                atomic_write(config.data_root, 'fake-p4.json', confined(reader.base, reader.manifest['p4_fixture']).read_bytes())
            adapter = P4Adapter(config, tickets_override=tickets_override, fixture=isinstance(reader, FixtureReportReader))
            data = snapshot(config, adapter, package, observed['reports'][arch]['headers'], path.read_bytes(), folder,
                build_id=reader.build_ref.run_id, lists=lists, input_confirmations=confirmations,
                log_metadata={**metadata.get('response', {}), 'first_failure_observed_at': metadata.get('first_failure_observed_at'), 'known_sync_cls': metadata.get('known_sync_cls', [])},
                notice_seen=[e['payload']['todo'].get('basis_version') for e in store.events(key, kinds=['inbox_opened']) if e['payload']['todo']['reason']=='snapshot_notice'])
            data['input_binding'] = binding
            artifact = atomic_write(config.data_root, folder + '/manifest.json', json_bytes(data))
            current = store.append(context, 'snapshot_completed', {'build': key, 'package': package['key'],
                'attempt': attempt, 'artifact': artifact}, current)
            current = write_todos(store, context, current, key, data['notices'], config)
            report = write_round_report(config, store, key)
            return {'artifact': artifact, 'round_report': report, 'mode': data['mode'], 'last_event_id': current, 'exit_code': 0}
        except FlowError as error:
            current = store.append(context, 'snapshot_failed', {'build': key, 'package': package['key'],
                'attempt': attempt, 'error': error.reason}, current)
            todo = error.details.get('todo') or {'reason': error.reason}
            if error.reason == 'p4_unclassified':
                todo['structured_message'] = error.details.get('message', {})
            todo.update(package=package['key'], basis_version=digest(json_bytes(package['key'])), retry_count=count+1 if error.reason=='p4_unclassified' else 0)
            write_todos(store, context, current, key, [todo], config)
            raise
