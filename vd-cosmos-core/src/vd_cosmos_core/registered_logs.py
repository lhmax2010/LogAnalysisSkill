"""Read existing observation and log registrations without changing them."""
import json

from .errors import FlowError
from .task_package import checked_file


def is_log_event(event):
    return event['command'] == 'fetch.logs' or event['payload'].get('step') == 'logs'


def registrations(store, key=None):
    for event in reversed(store.events(key, kinds=['observation_recorded', 'workflow_result'])):
        payload = event['payload']
        if payload.get('exit_code') or not payload.get('artifact'):
            continue
        if is_log_event(event) or event['command'] == 'watch.observe' or payload.get('step') == 'observe':
            yield event


def read_registration(config, event):
    try:
        data = json.loads(checked_file(config, event['payload']['artifact']))
        return (data['observation'], data) if is_log_event(event) else (data, None)
    except (FlowError, KeyError, OSError, ValueError, TypeError):
        raise FlowError(4, 'analysis_verifier_latest_log_registration_invalid') from None


def failed_packages(observation):
    return {package_identity(p['key']): p for report in observation['reports'].values()
            for p in report.get('packages', []) if p['category'] in {'build_error', 'export_error'}}


def package_identity(key):
    return tuple(key[field] for field in ('name', 'arch', 'path'))
