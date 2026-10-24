"""Continuous runs remain valid independently of the bounded audit history."""
from datetime import datetime


def seconds(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()


def advance(previous, sha, at, version):
    if (not previous or previous['sha256'] != sha or previous['parsing_version'] != version
            or seconds(at) < seconds(previous['last_seen_at'])):
        return {'sha256': sha, 'first_seen_at': at, 'last_seen_at': at, 'count': 1, 'parsing_version': version}
    return {**previous, 'last_seen_at': at, 'count': previous['count'] + 1}


def maturity(record, poll, terminal):
    elapsed = seconds(record['last_seen_at']) - seconds(record['first_seen_at'])
    stable = elapsed >= poll['interval_s']
    return stable, stable and (terminal or elapsed >= poll['settle_s'])
