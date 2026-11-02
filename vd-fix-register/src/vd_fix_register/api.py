"""TTY-only human decisions, scoped by round locks and expected event numbers."""
from vd_cosmos_core.build_inputs import freeze
from vd_cosmos_core.backends import FixtureReportReader
from vd_cosmos_core.commands import command_context
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.files import load_json
from vd_cosmos_core.journal import write_inbox
from vd_cosmos_core.locks import OperationLock
from vd_cosmos_core.p4 import P4Adapter
from vd_cosmos_core.receipts import report_digests
from vd_cosmos_core.state import EventStore
from vd_cosmos_core.versions import build_key


def decide(config, reader, command, *, expected_event=None, reason='', report_bindings=None,
           override_running=False, withdraw=False, package=None, shelve_digest=None,
           base_file=None, shelve_file=None, todo_key=None, context=None):
    context = context or command_context(command)
    if context.name != command or context.category.value != '人工裁决' or not context.terminal_confirmed:
        raise FlowError(2, 'terminal_required')
    if not reason.strip():
        raise FlowError(2, 'reason_required')
    key = build_key(reader)
    with OperationLock(config.data_root, 'round', key), EventStore(config.data_root) as store:
        expected = store.head() if expected_event is None else expected_event
        if expected != store.head():
            raise FlowError(6, 'stale_head')
        payload = {'build': key, 'reason': reason}
        if command == 'confirm-terminal':
            kind = 'terminal_withdrawn' if withdraw else 'terminal_confirmed'
            if withdraw:
                payload['after_click_intent'] = bool(store.events(key, kinds=['click_intent']))
            else:
                observed = reader.observe(reader.build_ref)
                actual = report_digests(observed['reports'])
                if not report_bindings or actual != report_bindings or any(v is None for v in actual.values()):
                    raise FlowError(4, 'terminal_report_digests_mismatch')
                running = observed.get('effective_execution_state') in {'运行', '排队'}
                if running and not override_running:
                    raise FlowError(4, 'override_running_required')
                if running:
                    import json
                    try:
                        with open('/dev/tty', 'r', encoding='utf-8') as tty, open('/dev/tty', 'w', encoding='utf-8') as display:
                            display.write(json.dumps({'build': reader.build_ref.run_id, 'reports': actual,
                                'execution': observed['execution_state'], 'observed_at': observed.get('observed_at')}, ensure_ascii=False)+'\n输入构建号确认：')
                            display.flush()
                            if tty.readline().strip() != reader.build_ref.run_id:
                                raise FlowError(3, 'build_confirmation_required')
                    except OSError:
                        raise FlowError(2, 'terminal_required') from None
                payload.update(report_digests=actual, override_running=override_running,
                               execution_evidence=observed.get('execution_evidence'))
        elif command == 'bind-base-list':
            if not base_file:
                raise FlowError(2, 'base_file_required')
            values = {'PACKAGE_LIST': config.source(base_file).read_text(),
                      'SHELVE_LIST': config.source(shelve_file).read_text() if shelve_file else None}
            inputs = freeze(config, key, values, reader.observe(reader.build_ref)['reports'], source='manual_binding')
            kind, payload['input_digests'] = 'base_list_bound', inputs['digests']
        elif command == 'confirm-input':
            observed = reader.observe(reader.build_ref)
            packages = [p for r in observed['reports'].values() for p in r.get('packages', []) if p['key'] == package]
            if len(packages) != 1 or not packages[0]['shelve']:
                raise FlowError(2, 'unique_shelve_package_required')
            adapter = P4Adapter(config, fixture=isinstance(reader, FixtureReportReader))
            adapter.info(); adapter.login_status()
            described = adapter.describe(packages[0]['cl'])
            if not shelve_digest or described.get('digest') != shelve_digest:
                raise FlowError(4, 'shelve_digest_mismatch')
            kind = 'input_confirmed'
            payload.update(package=package, shelve_digest=shelve_digest)
        elif command == 'inbox.done':
            found = [e for e in store.events(key, kinds=['inbox_opened']) if e['payload'].get('todo_key') == todo_key]
            if len(found) != 1:
                raise FlowError(2, 'todo_not_found')
            kind = 'inbox_closed'
            todo = found[0]['payload']['todo']
            payload.update(todo_key=todo_key, package=todo.get('package'), todo_reason=todo.get('reason'))
        else:
            raise FlowError(2, 'unregistered_command')
        current = store.append(context, kind, payload, expected)
        write_inbox(store, config)
        return {'last_event_id': current, 'kind': kind, 'exit_code': 0}
