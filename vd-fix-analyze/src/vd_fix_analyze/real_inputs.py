"""Register the inputs of an existing manually submitted failed build."""
import re
import time

from vd_cosmos_core.bm_reader import Reader
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.export import check_content
from vd_cosmos_core.files import json_bytes, load_json
from vd_cosmos_core.read_ops import make_reader, register_read
from vd_cosmos_core.receipts import logs_valid, report_digests
from vd_cosmos_core.registered_logs import failed_packages, package_identity, registrations, read_registration
from vd_cosmos_core.submit_model import requests
from vd_cosmos_core.task_package import checked_file
from vd_cosmos_core.versions import build_key

from .api import create_snapshot


def check_registration(store, build, hub):
    for request in requests(store.events()).values():
        bindings = [request.get('binding') or {}, *request.get('binding_history', [])]
        if (any(str(item.get('build_id')) == build for item in bindings)
                or hub and str(request.get('hub_id')) == hub):
            raise FlowError(4, 'prepare_inputs_tool_managed_build', build_id=build)


def check_terminal(observation):
    basis = observation.get('effective_terminal_basis') or {}
    if (observation.get('observation_failed') or observation.get('effective_execution_state') != '已结束'
            or basis.get('kind') != 'trusted_terminal'):
        raise FlowError(6, 'prepare_inputs_terminal_not_verified')


def check_failed(observation):
    if observation.get('report_state') != '完整' or observation.get('header_consistency') != '一致':
        raise FlowError(6, 'prepare_inputs_reports_not_complete')
    if observation.get('result_state') != '失败':
        raise FlowError(6, 'prepare_inputs_build_not_failed')
    if not failed_packages(observation):
        raise FlowError(6, 'prepare_inputs_no_failure_logs')


def cached_logs(config, store, key, observation):
    for event in registrations(store, key):
        try:
            original, receipt = read_registration(config, event)
        except FlowError:
            return None
        if receipt is None:
            continue
        items = receipt.get('logs', [])
        identities = [package_identity(item['key']) for item in items]
        if (len(identities) == len(set(identities)) and set(identities) == set(failed_packages(observation))
                and report_digests(original['reports']) == report_digests(observation['reports'])
                and logs_valid(config, receipt, observation)):
            for item in items:
                sidecar = config.output(item['path'] + '.json')
                if not sidecar.is_file():
                    return None
                try:
                    metadata = load_json(sidecar)
                except FlowError:
                    return None
                if any(metadata.get(field) != item[field] for field in ('sha256', 'key', 'binding', 'final')):
                    return None
            return receipt
        return None
    return None


def summarize_snapshot(config, item, result):
    manifest = result['artifact']
    snapshot = load_json(config.output(manifest['path']))
    sources = []
    for source in snapshot['files']:
        record = source.get('content')
        if record:
            checked_file(config, record)
            sources.append({field: record[field] for field in ('size', 'sha256')})
    return {'package': item['key'], 'log': {field: item[field] for field in ('size', 'sha256')},
            'snapshot': {field: manifest[field] for field in ('size', 'sha256')},
            'mode': snapshot['mode'], 'sources': sources,
            'unavailable_source_count': sum(bool(f.get('unavailable_reason') and not f.get('content'))
                                            for f in snapshot['files']),
            'snapshot_reused': bool(result.get('skipped')),
            'status': 'reused' if result.get('skipped') else 'registered'}


def prepare_real_inputs(config, build, hub_id=None, *, reader_factory=None, detail_reader=Reader, sleep=time.sleep):
    if not re.fullmatch(r'[1-9][0-9]*', build) or (hub_id and not re.fullmatch(r'[1-9][0-9]*', hub_id)):
        raise FlowError(2, 'invalid_prepare_inputs_build_id')
    if build == '19270877':
        raise FlowError(4, 'prepare_inputs_excluded_build')
    if reader_factory is None:
        reader_factory = lambda: make_reader(config, 'real', build_id=build)
    management = detail_reader(config)
    try:
        detail = management.detail(build)
    finally:
        management.close()
    if detail['identity'] != 'strong' or detail['build_id'] != build or detail['conflict']:
        raise FlowError(6, 'prepare_inputs_build_identity_unverified', build_id=build)
    hub = detail.get('hub_id')
    if hub_id and hub_id != hub:
        raise FlowError(4, 'prepare_inputs_hub_mismatch', build_id=build)
    if not detail['ended']:
        raise FlowError(6, 'prepare_inputs_terminal_not_verified')

    reader = reader_factory()
    key = build_key(reader)

    def manual_only(store):
        check_registration(store, build, hub)

    def observe_before_fetch(store):
        manual_only(store)
        observation = reader.observe(reader.build_ref)
        check_terminal(observation)
        return observation

    def fetch_precheck(store):
        observation = observe_before_fetch(store)
        if not all(report.get('settled') for report in observation['reports'].values()):
            raise FlowError(6, 'prepare_inputs_reports_not_settled',
                            retry_after_s=config.raw['poll']['interval_s'])
        check_failed(observation)

    def observe_cache(store):
        for event in registrations(store, key):
            if event['command'] != 'watch.observe':
                continue
            try:
                prior, _ = read_registration(config, event)
            except FlowError:
                return None
            fresh = reader.observe(reader.build_ref)
            if (prior.get('effective_terminal_basis') == fresh['effective_terminal_basis']
                    and report_digests(prior['reports']) == report_digests(fresh['reports'])
                    and all(report.get('settled') for report in prior['reports'].values())
                    and all(report.get('settled') for report in fresh['reports'].values())):
                return fresh
            return None
        return None

    _, observation = register_read(config, reader, 'watch', 'observe',
                                   precheck=observe_before_fetch, cached=observe_cache)
    if not all(report.get('settled') for report in observation['reports'].values()):
        sleep(config.raw['poll']['interval_s'])
        reader = reader_factory()
        _, observation = register_read(config, reader, 'watch', 'observe',
                                       precheck=observe_before_fetch, cached=observe_cache)
    fetch_result, receipt = register_read(config, reader, 'fetch', 'logs', precheck=fetch_precheck,
        cached=lambda store: cached_logs(config, store, key, observation), partial_logs=True)
    if receipt.get('exit_code', 0):
        raise FlowError(receipt['exit_code'], 'prepare_inputs_final_logs_required', build_id=build)
    expected = failed_packages(observation)
    downloaded = receipt.get('logs', [])
    items = {package_identity(item['key']): item for item in downloaded}
    failures = {package_identity(item['key']): item['reason'] for item in receipt.get('log_failures', [])}
    if (len(items) != len(downloaded) or items.keys() & failures.keys()
            or not (items.keys() | failures.keys()) <= expected.keys()):
        raise FlowError(6, 'prepare_inputs_log_identity_mismatch', build_id=build)
    # Validate against the observation used to authorize preparation, even if the
    # download produced a newer observation.
    usable = {identity: item for identity, item in items.items()
              if logs_valid(config, {'logs': [item]}, observation)}

    def use_verified_base_list(store):
        path = config.output(f'rounds/{key}/inputs/build-lists/manifest.json')
        if not path.is_file():
            return None
        prior = load_json(path)
        for artifact in prior['files'].values():
            checked_file(config, artifact)
        return prior if prior.get('source') == 'variables_page' else None

    if usable:
        register_read(config, reader, 'fetch', 'base-list', precheck=fetch_precheck,
                      cached=use_verified_base_list)
    rows = []
    for identity, expected_package in expected.items():
        package = expected_package['key']
        item = usable.get(identity)
        if not item:
            rows.append({'package': package, 'status': 'snapshot_failed',
                         'reason': failures.get(identity, 'prepare_inputs_final_log_required')})
            continue
        try:
            result = create_snapshot(config, reader, package['name'], package['arch'], item['path'], reuse=True)
            rows.append(summarize_snapshot(config, item, result))
        except FlowError as error:
            # A missing/expiring ticket is shared by every remaining package.
            if error.reason in {'p4_not_logged_in', 'p4_ticket_expiring'}:
                raise FlowError(error.code, error.reason, **error.details, package=package, completed=rows) from None
            rows.append({'package': package, 'status': 'snapshot_failed', 'reason': error.reason,
                         'details': error.details,
                         'log': {field: item[field] for field in ('size', 'sha256')}})
        except (OSError, KeyError, TypeError, ValueError):
            rows.append({'package': package, 'status': 'snapshot_failed', 'reason': 'snapshot_processing_failed'})
    summary = {'build_id': build, 'build_key': key, 'hub_id': hub, 'logs_reused': fetch_result is None,
               'packages': rows, 'exit_code': 5 if any(row['status'] == 'snapshot_failed' for row in rows) else 0}
    if not check_content(json_bytes(summary), config)['allowed']:
        raise FlowError(4, 'prepare_inputs_summary_credential_blocked')
    return summary
