"""Continuous content and execution windows, independent of bounded audit history."""
from .dates import parse_datetime
from datetime import datetime


def seconds(value):
    return parse_datetime(value).timestamp()


def effective_state(execution):
    return execution.get('state', '未知') if execution.get('identity') == 'strong' else '未知'


def execution_clock(previous, execution, at, report_success=False):
    state = effective_state(execution)
    epoch, unknown = previous.get('terminal_epoch'), previous.get('unknown_since')
    if state == '已结束':
        epoch, unknown = epoch or at, None
    elif state in {'运行', '排队'}:
        epoch, unknown = None, None
    else:
        epoch = None
        if report_success and unknown is None:
            unknown = at
    if epoch and seconds(epoch) > seconds(at):
        epoch = at if state == '已结束' else None
    if unknown and seconds(unknown) > seconds(at):
        unknown = at if report_success else None
    return {'terminal_epoch': epoch, 'unknown_since': unknown, 'effective_state': state}


def advance(previous, sha, at, version, execution=None):
    if (not previous or previous['sha256'] != sha or previous['parsing_version'] != version
            or seconds(at) < seconds(previous['last_seen_at'])):
        previous = {'sha256': sha, 'first_seen_at': at, 'count': 0, 'parsing_version': version,
                    'observations': [], 'unknown_observations': []}
    record = {**previous, 'last_seen_at': at, 'count': previous['count'] + 1,
              'observations': (previous.get('observations', []) + [at])[-2:]}
    state = (execution or {}).get('effective_state', '未知')
    record['unknown_observations'] = ((previous.get('unknown_observations', []) + [at])[-2:]
                                      if state == '未知' else [])
    return record


def maturity(record, poll, execution, manual=None):
    """Mutate only the derived basis; retain the actual observation timestamps."""
    if isinstance(execution, bool):
        raise TypeError('execution window required')
    record['settled_basis'] = None
    end, start = seconds(record['last_seen_at']), seconds(record['first_seen_at'])
    stable = end - start >= poll['interval_s']
    candidates = []
    if manual:
        candidates.append(('manual_terminal', manual['confirmed_at'], poll['interval_s'], record['observations']))
    elif execution.get('effective_state') == '已结束' and execution.get('terminal_epoch'):
        candidates.append(('trusted_terminal', execution['terminal_epoch'], poll['interval_s'], record['observations']))
    elif execution.get('effective_state') == '未知' and execution.get('unknown_since'):
        candidates.append(('elapsed_window', execution['unknown_since'], poll['settle_s'], record['unknown_observations']))
    for basis, epoch, required, samples in candidates:
        beginning = max(start, seconds(epoch))
        if stable and end - beginning >= required and sum(seconds(t) >= beginning for t in samples) >= 2:
            record['settled_basis'] = basis
            return True, True
    return stable, False
