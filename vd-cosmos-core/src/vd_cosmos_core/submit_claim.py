"""Candidate observations and explicit human mapping, never automatic submission."""
import copy
import time

from . import bm_pages
from .commands import Category, CommandContext
from .errors import FlowError
from .files import digest, json_bytes
from .http_reader import HTTPReportReader
from .state import EventStore
from .submit_model import mutate, read, requests, ensure_safe, lock


def pre_click_evidence(reader):
    """B2 seam: caller records this sample with its intent; failures never invent H_pre."""
    try:
        rows = reader.overview()['rows']
        return {'H_pre': max((int(r['hub_id']) for r in rows if r.get('hub_id')), default=None),
                'click_clock': copy.deepcopy(reader.samples[-1])}
    except FlowError:
        return {'H_pre': None, 'click_clock': {}}


def margin(config, sample):
    return max(config.raw['poll']['claim_margin_s'], abs(sample.get('offset_s', 0)) + sample.get('error_s', 0) + 300)


def lower_bound(config, r):
    sample = r.get('click_clock') or {}
    if r.get('click_time') is not None and sample.get('valid'):
        return r['click_time'] + sample['offset_s'] - margin(config, sample)
    start = (r.get('observation') or {}).get('supplementary_start')
    if start is None: start = r.get('click_time', r['created_at']) or r['created_at']
    bound = r.get('binding') or {}
    return min(start, bound.get('start_time', start)) - margin(config, sample)


def variable_names(config):
    return {'PACKAGE_LIST', 'SHELVE_LIST'} | {e['variable'] for e in config.raw['submit']['property_map'].values()
        if e['affects_build'] and e['variable'] not in (None, 'not_listed')}


def collect(config, r, reader):
    locate = r.get('hub_id') if not r.get('binding') else None
    scan = reader.scan(hub_id=locate, since=None if locate else lower_bound(config, r),
                       previous_anchor=r.get('anchor'), account_only=not r.get('binding') and not locate,
                       rerun=bool(r.get('binding')))
    for b in r.get('pending', []):
        if b not in scan['details']:
            try:
                scan['details'][b] = reader.detail(b, fresh=True)
            except FlowError as error:
                if error.code == 4: raise
                scan['coverage'] = False; scan['issues'].append('pending_detail_unreadable')
    matches = []; account_rows = []
    for b, row in scan['rows'].items():
        if not row['version'].startswith('[' + config.raw['submit']['account'] + ']'): continue
        d = scan['details'].get(b)
        if not d or d['config_id'] != config.raw['cosmos']['bm_config_id']:
            continue
        if d['start_time'] is not None and d['start_time'] < lower_bound(config, r): continue
        info = dict(d, comparison={'matches': False, 'fields': {}, 'unverified': ['变量页']})
        try:
            # Comparison always re-reads the page, regardless of relationship cache.
            values = reader.variables(b, variable_names(config))
            info['comparison'] = bm_pages.compare(r, values, config)
        except FlowError as e:
            if e.code == 4: raise
            scan['coverage'] = False; scan['issues'].append(e.reason)
            if e.details.get('todo'): scan.setdefault('todos', []).append(e.details['todo'])
        account_rows.append(info)
        if (info['comparison']['matches'] and d['hub_id'] and not d['conflict']
                and (not r.get('hub_id') or d['hub_id'] == r['hub_id'])):
            if (config.raw['submit']['hub_id_monotonic_confirmed'] and r.get('H_pre') is not None
                    and int(d['hub_id']) <= r['H_pre']): continue
            matches.append(info)
    scan['candidates'] = matches; scan['account_rows'] = account_rows
    if not (r.get('click_clock') or {}).get('valid') or r.get('click_time') is None:
        scan['issues'].append('click_clock_unverified')
    scan['claim_coverage'] = bool(scan['coverage'] and (r.get('click_clock') or {}).get('valid') and r.get('click_time') is not None)
    groups = {}
    for d in matches: groups.setdefault(d['hub_id'], []).append(d)
    scan['rerun_chains'] = [{'hub_id': h, 'builds': [
        {'build_id': d['build_id'], 'start_time': d['start_time'], 'status': d['state']} for d in group]}
        for h, group in groups.items() if len(group) > 1]
    scan['result'] = ('冲突' if scan['conflicts'] else '重跑链' if len(matches) > 1 and len(groups) == 1
                      else '多个候选' if len(matches) > 1 else '唯一' if matches else '未定位')
    scan['reason'] = None if matches else '当前保留记录中尚未出现' if scan['coverage'] else '扫描覆盖不足'
    return scan


def merge_scan(config, r, scan, context, *, now=None):
    now = time.time() if now is None else now
    pending = set(r.get('pending', [])) | set(scan['pending'])
    for b, d in scan['details'].items():
        if d.get('hub_id'): pending.discard(b)
    seen = dict(r.get('seen', {})); seen.update(scan['rows'])
    todos = list(r.get('todos', [])); caution = r.get('result_caution')
    def todo(reason):
        if reason not in todos: todos.append(reason)
    binding = r.get('binding')
    if not scan['coverage'] or pending or len(pending) > config.raw['cosmos']['bm_pending_max']:
        todo('重跑观察覆盖不足' if binding else '扫描覆盖不足')
    for issue in scan.get('todos', []): todo(issue['message'] if 'message' in issue else issue['reason'])
    if scan['conflicts']: todo('证据冲突')
    elif len(scan['candidates']) > 1: todo('重跑链待人工选择' if scan.get('rerun_chains') else '多个候选待人工确认')
    deadline = None; complete = False
    if binding:
        b, h = binding['build_id'], binding['hub_id']
        same_h = [d for d in scan['details'].values() if d.get('hub_id') == h and d['build_id'] != b]
        same_content = [d for d in scan.get('account_rows', []) if d['build_id'] != b and d['comparison']['matches']]
        if same_h: todo('发现重跑'); caution = '可能不是最终构建'
        if same_content: todo('疑似同内容的另一轮'); caution = '可能不是最终构建'
        current = scan['details'].get(b) or r.get('cache', {}).get(b)
        start = r.get('click_time')
        if start is None: start = r['observation']['supplementary_start']
        elif (r.get('click_clock') or {}).get('valid'): start += r['click_clock']['offset_s']
        if current and current.get('end_time') is not None:
            deadline = max(start + config.raw['poll']['expected_hours'] * 3600,
                           current['end_time'] + config.raw['poll']['rerun_watch_s'])
            if current['state'] not in {'successful', 'succeeded', 'success'} and now < deadline:
                caution = '可能有重跑、尚未确定最终构建'
            complete = now >= deadline and scan['coverage'] and not pending
        else: todo('构建结束时间未知，观察未完成')
    elif now > (r['observation'].get('supplementary_start') or r.get('click_time') or r['created_at']) + config.raw['poll']['expected_hours'] * 3600:
        todo('可能未生成构建，请核对提交端历史')
    changes = {'scan': scan, 'candidates': scan['candidates'], 'pending': sorted(pending), 'seen': seen,
               'cache': scan['cache'], 'anchor': scan['anchor'], 'next_scan_at': now + config.raw['poll']['watch_interval_s'],
               'todos': todos, 'result_caution': caution, 'deadline': deadline, 'observation_complete': complete,
               'lower_bound': lower_bound(config, r)}
    return mutate(config, r['request_id'], r['version'], context, changes, kind='submit_observation')


def hard_checks(config, r, d, all_requests):
    if d['build_id'] in {'19270877', '19206687'}:
        raise FlowError(4, 'verification_source_or_erroneous_build_not_bindable')
    if d['identity'] != 'strong' or not d['hub_id'] or d['conflict']:
        raise FlowError(4, 'candidate_identity_invalid')
    if d['config_id'] != config.raw['cosmos']['bm_config_id']:
        raise FlowError(4, 'candidate_wrong_config')
    if r.get('hub_id') and r['hub_id'] != d['hub_id']:
        raise FlowError(4, 'candidate_wrong_hub')
    if r.get('binding') and r['binding']['build_id'] != d['build_id']:
        raise FlowError(4, 'binding_conflict')
    for other in all_requests.values():
        if other['request_id'] == r['request_id']: continue
        if (other.get('binding') or {}).get('build_id') == d['build_id'] or other.get('hub_id') == d['hub_id']:
            raise FlowError(4, 'candidate_owned_by_other_request')
    sample = r.get('click_clock') or {}
    if r.get('click_time') is not None and sample.get('valid') and d['start_time'] < lower_bound(config, r):
        raise FlowError(4, 'candidate_before_click')
    if config.raw['submit']['hub_id_monotonic_confirmed'] and r.get('H_pre') is not None and int(d['hub_id']) <= r['H_pre']:
        raise FlowError(4, 'candidate_not_after_H_pre')


def fingerprint(r, scan, d):
    hpre = r.get('H_pre')
    return {'members': sorted(x['build_id'] for x in scan.get('candidates', [])),
            'coverage': bool(scan.get('claim_coverage', scan.get('coverage'))), 'H_pre': hpre,
            'H_gt_pre': int(d['hub_id']) > hpre if hpre is not None else None,
            'binding': r.get('binding'), 'status': r['status'],
            'other_newer': sorted(x['build_id'] for x in scan.get('account_rows', [])
                if x['build_id'] != d['build_id'] and x.get('hub_id') and hpre is not None and int(x['hub_id']) > hpre)}


def confirmation(config, r, scan, d):
    f = fingerprint(r, scan, d); words = []
    if d['build_id'] not in f['members']: words.append('claim-outside-candidates')
    if (f['H_gt_pre'] is not True or not (r.get('click_clock') or {}).get('valid')
            or r.get('click_time') is None or not f['coverage'] or f['other_newer']):
        words.append('claim-unverified')
    return {'fingerprint': f, 'required_words': words, 'build_id': d['build_id'], 'H_pre': r.get('H_pre'),
            'candidate': d, 'scan': scan, 'start_time_check': '未核验' if r.get('click_time') is None else '按点击时刻核对',
            'message': '确认前请在提交端核对本次提交的编号；无法核对时，这次确认按未核实的人工判断记录。'}


def prepare_attest(config, request_id, build_id, reader):
    r = read(config, request_id)
    if r['status'] not in {'accepted', 'submitted_manual', 'submitted_resolved'}:
        raise FlowError(6, 'request_not_submitted')
    d = reader.detail(str(build_id), fresh=True)
    with EventStore(config.data_root) as store: all_requests = requests(store.events())
    hard_checks(config, r, d, all_requests)
    scan = collect(config, r, reader)
    # Persist the fresh candidate set before asking; this is observation, not authorization.
    r = merge_scan(config, r, scan, CommandContext('submit.watch', Category.OBSERVE))
    return confirmation(config, r, scan, d)


def attest(config, request_id, prepared, context, words, reason, reader, *, now=None):
    if context.category != Category.HUMAN or not context.terminal_confirmed: raise FlowError(2, 'terminal_required')
    if not reason.strip(): raise FlowError(2, 'reason_required')
    ensure_safe(config, reason)
    before = read(config, request_id)
    # Only the selected pages are re-read after input; never rescan thousands of pages here.
    d = reader.detail(prepared['build_id'], fresh=True)
    comparison = bm_pages.compare(before, reader.variables(d['build_id'], variable_names(config)), config)
    with lock(config, request_id):
        with EventStore(config.data_root) as store:
            head = store.head(); events = store.events(); all_requests = requests(events); r = all_requests[request_id]
            if r['version'] != before['version']: raise FlowError(6, 'request_version_changed')
            hard_checks(config, r, d, all_requests)
            if r.get('binding'): return {'already_confirmed': True, 'binding': r['binding']}
            current = confirmation(config, r, r.get('scan', {}), d)
            if current['fingerprint'] != prepared['fingerprint'] or not comparison['matches']:
                raise FlowError(3, 'confirmation_basis_changed')
            if not set(current['required_words']) <= set(words):
                raise FlowError(3, 'confirmation_words_required', required=current['required_words'])
            if not current['required_words'] and d['build_id'] not in words:
                raise FlowError(3, 'build_number_confirmation_required')
            binding = {k: d[k] for k in ('build_id', 'hub_id', 'config_id', 'start_time')}
            changes = {'binding': binding, 'hub_id': d['hub_id'], 'mapping_pending': False,
                       'attestation': {'at': now or time.time(), 'reason': reason, 'words': list(words),
                                       'basis': '内容候选确认', 'unverified': 'claim-unverified' in words,
                                       'outside_candidates': 'claim-outside-candidates' in words},
                       'input_verification': '变量页已核对，待报告核对'}
            reruns = [e['payload'] for e in events if e['kind'] == 'submit_rerun_resolved'
                      and e['payload']['target'] == r['target'] and e['payload']['hub_id'] == d['hub_id']]
            changes['manual_reruns'] = reruns
            ref = HTTPReportReader(config, d['build_id']).build_ref
            entries = [{'kind': 'submit_decision', 'request_id': request_id, 'payload': {'changes': changes}},
                       {'kind': 'bind', 'request_id': request_id, 'build_key': digest(json_bytes(ref.to_dict())),
                        'payload': {'build_ref': ref.to_dict(), 'binding': binding, 'input_verification': '变量页已核对，待报告核对'}}]
            store.append_batch(context, entries, head)
    return read(config, request_id)


def rebind(config, request_id, build_id, context, reason, reader):
    if not reason.strip(): raise FlowError(2, 'reason_required')
    r = read(config, request_id)
    if not r.get('binding'): raise FlowError(6, 'binding_missing')
    d = reader.detail(str(build_id), fresh=True)
    with EventStore(config.data_root) as store: all_requests = requests(store.events())
    hard_checks(config, dict(r, binding=None), d, all_requests)
    comparison = bm_pages.compare(r, reader.variables(d['build_id'], variable_names(config)), config)
    if not comparison['matches']: raise FlowError(4, 'binding_inputs_mismatch')
    binding = {k: d[k] for k in ('build_id', 'hub_id', 'config_id', 'start_time')}
    history = r.get('binding_history', []) + [r['binding']]
    ref = HTTPReportReader(config, d['build_id']).build_ref
    previous_ref = HTTPReportReader(config, r['binding']['build_id']).build_ref
    key = digest(json_bytes(ref.to_dict()))
    extra = [{'kind': 'rebind', 'request_id': request_id, 'payload': {'old': r['binding'], 'new': binding, 'reason': reason}}]
    with EventStore(config.data_root) as store:
        existing = store.events(key, kinds=['bind'])
    if existing and existing[0]['request_id'] != request_id:
        raise FlowError(4, 'build_previously_bound_to_other_request')
    if not existing:
        extra.append({'kind': 'bind', 'request_id': request_id, 'build_key': key,
                      'payload': {'build_ref': ref.to_dict(), 'binding': binding,
                                  'previous_build': digest(json_bytes(previous_ref.to_dict()))}})
    return mutate(config, request_id, r['version'], context,
                  {'binding': binding, 'binding_history': history, 'rebind_reason': reason,
                   'observation_complete': False, 'input_verification': '待报告核对', 'result_caution': '旧映射产物已过期'},
                  extra=extra)


def abandon(config, request_id, context, reason):
    if not reason.strip(): raise FlowError(2, 'reason_required')
    r = read(config, request_id)
    if r['status'] in {'uncertain', 'manual_submit_pending', 'manual_action_pending'}:
        raise FlowError(6, 'resolve_uncertainty_before_abandon')
    return mutate(config, request_id, r['version'], context,
                  {'status': 'abandoned', 'submitted_before_abandon': r['status'] in {'accepted', 'submitted_manual', 'submitted_resolved'},
                   'abandon_reason': reason, 'observation_complete': True})
