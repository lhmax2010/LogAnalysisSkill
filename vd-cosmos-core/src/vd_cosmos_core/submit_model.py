"""Append-only request model. Browser effects are deliberately absent."""
from contextlib import nullcontext
import copy
import time
import uuid

from .bm_pages import base_digest
from .commands import Category
from .errors import FlowError
from .export import check_content
from .files import digest, json_bytes
from .locks import OperationLock
from .state import EventStore
from .submit_config import PROPERTIES

OBSERVED = {'scan', 'pending', 'seen', 'cache', 'anchor', 'next_scan_at', 'todos',
            'candidates', 'observation_complete', 'deadline', 'result_caution', 'lower_bound'}
SUBMITTED = {'accepted', 'submitted_manual', 'submitted_resolved'}

def was_submitted(r):
    return r['status'] in SUBMITTED or r.get('submitted_before_abandon', False)
TERMINAL = SUBMITTED | {'rejected', 'not_submitted', 'blocked_before_send', 'abandoned'}


def requests(events):
    result = {}
    for event in events:
        kind, p, r = event['kind'], event['payload'], event['request_id']
        if kind == 'submit_request':
            if r not in result:
                result[r] = dict(copy.deepcopy(p), request_id=r, version=1)
        elif kind in {'submit_outcome', 'submit_decision', 'submit_observation'} and r in result:
            updates = p['changes']
            if kind == 'submit_observation': updates = {k: v for k, v in updates.items() if k in OBSERVED}
            result[r].update(copy.deepcopy(updates)); result[r]['version'] += 1
    return result


def lock(config, request):
    return OperationLock(config.data_root, 'request', request, wait_s=config.raw['poll']['lock_wait_s'])


def read(config, request):
    with EventStore(config.data_root) as store:
        all_requests = requests(store.events())
    if request not in all_requests: raise FlowError(6, 'request_not_found')
    return all_requests[request]


def target(config):
    s = config.raw['submit']
    return {'instance': s['target_instance'], 'config': s['target_config']}


def ensure_safe(config, value):
    if not check_content(json_bytes(value), config)['allowed']:
        raise FlowError(4, 'credential_pattern_blocked')


def request_digest(config, form):
    if set(form) != set(PROPERTIES): raise FlowError(2, 'all_18_properties_required')
    if any(not isinstance(x, str) for x in form.values()): raise FlowError(2, 'business_values_must_be_strings')
    if form['SHELVE_LIST'].strip(): raise FlowError(4, 'shelve_requires_batch4')
    ensure_safe(config, form)
    normalized = dict(form, PACKAGE_LIST=base_digest(form['PACKAGE_LIST'], config))
    return digest(json_bytes({'target': target(config), 'form': normalized}))


def task(request, now):
    if request.get('observation'): return request['observation']
    click = request.get('click_time')
    return {'created_at': now, 'entry': request['status'], 'supplementary_start': now if click is None else None,
            'clock_source': 'local', 'calibrated': bool(request.get('click_clock', {}).get('valid')),
            'click_time': click}


def unresolved(all_requests, events, wanted):
    for r in all_requests.values():
        if r['target'] == wanted and (r['status'] in {'uncertain', 'manual_submit_pending', 'manual_action_pending'}
                                     or r.get('click_time') is not None and r['status'] not in TERMINAL):
            return True
    resolved = {e['operation_id'] for e in events if e['kind'] == 'submit_rerun_resolved'}
    normally_closed = {e['operation_id'] for e in events if e['kind'] == 'submit_session_finished'
                       and e['payload'].get('normal_close') is True}
    for event in events:
        if event['kind'] == 'click_intent':
            request = all_requests.get(event['request_id'])
            if request and request['target'] == wanted and request['status'] not in TERMINAL:
                return True
        if (event['kind'] in {'hub_page_exposed', 'submit_form_exposed', 'manual_action_pending'}
                and event['operation_id'] not in resolved | normally_closed
                and event['payload'].get('target') == wanted):
            request = all_requests.get(event['request_id'])
            if event['kind'] == 'submit_form_exposed' and request and request['status'] in {'not_submitted','submitted_manual','submitted_resolved'}:
                continue
            return True
    return False


def create_request(config, context, form, reason, *, resubmit_of=None, now=None):
    if context.category != Category.EXTERNAL or not context.terminal_confirmed:
        raise FlowError(2, 'terminal_required')
    if not reason.strip(): raise FlowError(2, 'reason_required')
    sha = request_digest(config, form); ensure_safe(config, reason)
    with OperationLock(config.data_root, 'submit-target', digest(json_bytes(target(config)))):
        with EventStore(config.data_root) as store:
            head = store.head(); events = store.events(); all_requests = requests(events)
            if unresolved(all_requests, events, target(config)): raise FlowError(6, 'unresolved_submission')
            same = [r for r in all_requests.values() if r['digest'] == sha and r['target'] == target(config)]
            history = [r for r in same if was_submitted(r)]
            latest = history[-1] if history else None
            if latest and resubmit_of != latest['request_id']:
                raise FlowError(6, 'duplicate_round', latest_request=latest['request_id'], submissions=sum(1 + len(r.get('manual_reruns', [])) for r in history))
            if resubmit_of and (not latest or resubmit_of != latest['request_id']):
                raise FlowError(6, 'invalid_resubmit_reference')
            unfinished = [r for r in same if r['status'] not in TERMINAL]
            if unfinished: return unfinished[-1]
            r = uuid.uuid4().hex
            value = {'target': target(config), 'digest': sha, 'form': form, 'reason': reason,
                     'status': 'prepared', 'created_at': now if now is not None else time.time(),
                     'previous_request': resubmit_of or (same[-1]['request_id'] if same else None),
                     'previous_disposition': same[-1]['status'] if same else None,
                     'hub_id': None, 'binding': None, 'click_time': None, 'click_clock': {}, 'H_pre': None,
                     'mapping_pending': False, 'observation': None, 'pending': [], 'seen': {}, 'cache': {}, 'todos': []}
            store.append(context, 'submit_request', value, head, request_id=r)
    return read(config, r)


def mutate(config, request_id, expected_version, context, changes, *, kind='submit_decision', extra=None):
    ensure_safe(config, changes)
    with lock(config, request_id):
        with EventStore(config.data_root) as store:
            head = store.head(); current = requests(store.events()).get(request_id)
            if current is None or current['version'] != expected_version:
                raise FlowError(6, 'request_version_changed')
            if changes.get('hub_id') or changes.get('binding'):
                for other in requests(store.events()).values():
                    if other['request_id'] == request_id: continue
                    if (changes.get('hub_id') and other.get('hub_id') == changes['hub_id']
                            or changes.get('binding') and (other.get('binding') or {}).get('build_id') == changes['binding']['build_id']):
                        raise FlowError(4, 'candidate_owned_by_other_request')
            if kind == 'submit_observation' and set(changes) - OBSERVED:
                raise FlowError(4, 'observation_cannot_authorize')
            entries = [{'kind': kind, 'request_id': request_id, 'payload': {'changes': changes}}]
            entries.extend(extra or [])
            store.append_batch(context, entries, head)
    return read(config, request_id)


def record_outcome(config, request_id, context, status, *, now=None, click_time=None, click_clock=None, H_pre=None):
    """B2 integration seam; no navigation, click or transport is implemented here."""
    if status not in {'accepted', 'rejected', 'uncertain', 'blocked_before_send'}:
        raise FlowError(2, 'invalid_submit_outcome')
    r = read(config, request_id)
    if r['status'] != 'prepared': raise FlowError(6, 'request_already_processed')
    changed = dict(r, status=status, click_time=click_time, click_clock=click_clock or {}, H_pre=H_pre)
    changes = {k: changed[k] for k in ('status', 'click_time', 'click_clock', 'H_pre')}
    if status == 'accepted':
        changes.update(mapping_pending=True, observation=task(changed, time.time() if now is None else now))
    return mutate(config, request_id, r['version'], context, changes, kind='submit_outcome')


def resolve(config, context, *, request_id=None, session=None, hub_id=None, mode, reason,
            checked_at=None, words=(), now=None):
    if not reason.strip(): raise FlowError(2, 'reason_required')
    ensure_safe(config, {'reason': reason, 'checked_at': checked_at})
    now = time.time() if now is None else now
    if mode == 'manual-rerun':
        if not session or not hub_id or not str(hub_id).isdecimal(): raise FlowError(2, 'rerun_identity_required')
        with OperationLock(config.data_root, 'submit-target', digest(json_bytes(target(config)))):
            with EventStore(config.data_root) as store:
                head = store.head(); events = store.events(); all_requests = requests(events)
                if any(e['kind'] == 'submit_rerun_resolved' and e['operation_id'] == session for e in events):
                    raise FlowError(6, 'session_already_resolved')
                owners = [r for r in all_requests.values() if r['target'] == target(config) and r.get('hub_id') == str(hub_id)]
                entries = [{'kind': 'submit_rerun_resolved', 'operation_id': session,
                    'payload': {'target': target(config), 'hub_id': str(hub_id), 'at': now, 'reason': reason,
                                'pending': not owners}}]
                if owners:
                    r = owners[0]
                    entries.append({'kind': 'submit_decision', 'request_id': r['request_id'],
                                    'payload': {'changes': {'manual_reruns': r.get('manual_reruns', []) + [entries[0]['payload']]}}})
                with lock(config, owners[0]['request_id']) if owners else nullcontext():
                    store.append_batch(context, entries, head)
        return {'recorded': True, 'pending': not owners, 'read_queues_changed': False}
    r = read(config, request_id)
    if mode in {'build-id', 'manual-submit'}:
        if not hub_id or not str(hub_id).isdecimal(): raise FlowError(2, 'hub_id_required')
        if r.get('hub_id') and r['hub_id'] != str(hub_id): raise FlowError(4, 'hub_identity_conflict')
        with EventStore(config.data_root) as store:
            events = store.events(); others = requests(events)
        if any(x['request_id'] != request_id and x.get('hub_id') == str(hub_id) for x in others.values()):
            raise FlowError(4, 'hub_already_claimed')
        if r['status'] in SUBMITTED:
            return r
        changed = dict(r, status='submitted_manual' if mode == 'manual-submit' else 'submitted_resolved')
        reruns = [e['payload'] for e in events if e['kind'] == 'submit_rerun_resolved'
                  and e['payload']['target'] == r['target'] and e['payload']['hub_id'] == str(hub_id)]
        changes = {'status': changed['status'], 'hub_id': str(hub_id), 'mapping_pending': True,
                   'observation': task(changed, now), 'manual_reruns': reruns, 'resolution_reason': reason}
    elif mode in {'not-submitted', 'no-manual-submit'}:
        if not checked_at: raise FlowError(2, 'checked_at_required')
        if r['status'] in SUBMITTED: raise FlowError(4, 'submitted_cannot_be_erased')
        with EventStore(config.data_root) as store:
            hanging = [e for e in store.events(kinds=['submit_rerun_resolved']) if e['payload'].get('pending') and e['payload']['target'] == r['target']]
        if hanging and 'rerun-records-unrelated' not in words:
            raise FlowError(3, 'rerun_records_confirmation_required', records=[{'at':e['payload']['at'], 'hub_id':e['payload']['hub_id']} for e in hanging])
        if '未定位' in reason or 'not located' in reason.casefold(): raise FlowError(4, 'lookup_absence_not_resolution_evidence')
        changes = {'status': 'not_submitted', 'resolution_reason': reason, 'checked_at': checked_at}
    else: raise FlowError(2, 'invalid_resolve_mode')
    return mutate(config, request_id, r['version'], context, changes)
