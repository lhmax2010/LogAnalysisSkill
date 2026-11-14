"""Browser-free submission tracking defaults and registered comparison contract."""
import re
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from .errors import FlowError

PROPERTIES = ('BUILD_TYPE', 'BASE_REPOS', 'BUILD_CONF', 'PRODUCT_REPOS', 'ARCH',
              'PACKAGE_LIST', 'GITURL', 'SHELVE_LIST', 'KS_LIST', 'Product Version (ks)',
              'rpm Add & Delete', 'PACKAGE_LIST (DELETE)', 'PACKAGE_LIST (x86 arch)',
              'Ignore package build failure?', "Keep 'Full' build type", 'Image Skip?',
              'EMAIL_CC', 'EXTRA_BUILD_PARAMETER')
TEXT_PROPERTIES = set(PROPERTIES) - {'BUILD_TYPE', 'ARCH', 'GITURL', 'KS_LIST',
    'Ignore package build failure?', "Keep 'Full' build type", 'Image Skip?'}
SECRET_NAME = re.compile(r'(?:password|passwd|secret|token|cookie|ticket|saml|relaystate|profile_data)', re.I)  # credential-test-sample


def configure(raw):
    c = raw['cosmos']
    source = c.get('status_source') or {}
    c.setdefault('bm_host', urlsplit(source.get('url_template', 'https://bm.example.invalid')).netloc)
    c.setdefault('hub_host', 'hub.example.invalid')
    c.setdefault('bm_config_id', '4362')
    c['bm_config_id'] = str(c['bm_config_id'])
    c.setdefault('bm_display_tz', 'Asia/Seoul')
    ZoneInfo(c['bm_display_tz'])
    c.setdefault('bm_overview_headers', ['Id', 'Next Build Version', 'Schedule', 'Requested By', 'Schedule Date', 'Priority', 'Process Status', 'Build Version', 'Configuration Path', 'Hub ID', 'Requester'])
    c.setdefault('hub_link_rule', 'build-header-label-following-link-v1')
    if c['hub_link_rule'] != 'build-header-label-following-link-v1':
        raise FlowError(2, 'unregistered_hub_link_rule')
    for key in ('bm_host', 'hub_host'):
        u = urlsplit('https://' + c[key])
        if not u.hostname or u.username or u.password or u.path or u.query or u.fragment:
            raise FlowError(2, 'invalid_management_host')
    if not c['bm_config_id'].isdecimal():
        raise FlowError(2, 'invalid_management_config')
    for key, value in [('bm_history_max_pages', 400), ('bm_lookup_detail_max', 1000),
                       ('bm_pending_max', 200), ('hub_id_slack', 3000)]:
        c.setdefault(key, value)
        if type(c[key]) is not int or c[key] < 1:
            raise FlowError(2, 'invalid_lookup_limit')
    c.setdefault('bm_scan_interval_s', .2)
    if type(c['bm_scan_interval_s']) not in (int, float) or not 0 <= c['bm_scan_interval_s'] < float('inf'):
        raise FlowError(2, 'invalid_scan_interval')
    poll = raw['poll']
    for key, value in [('claim_margin_s', 900), ('claim_wait_s', 1800), ('lock_wait_s', 120),
                       ('watch_interval_s', 300), ('rerun_watch_s', 7200), ('expected_hours', 30)]:
        poll.setdefault(key, value)
        if type(poll[key]) not in (int, float) or not 0 < poll[key] < float('inf'):
            raise FlowError(2, 'invalid_submit_interval')
    submit = raw.setdefault('submit', {})
    for key, value in [('target_instance', c['hub_host']), ('target_config', 'configure-target'),
                       ('target_config_id', 'configure-target-id'), ('account', 'configure-account'),
                       ('hub_id_monotonic_confirmed', False), ('form', {})]:
        submit.setdefault(key, value)
    if (not isinstance(submit['form'], dict) or set(submit['form']) - set(PROPERTIES)
            or any(not isinstance(v, str) for v in submit['form'].values())
            or type(submit['hub_id_monotonic_confirmed']) is not bool
            or not isinstance(c['bm_overview_headers'], list)
            or any(not isinstance(x, str) for x in c['bm_overview_headers'])):
        raise FlowError(2, 'invalid_submit_configuration')
    for key in ('target_instance', 'target_config', 'target_config_id', 'account'):
        if not isinstance(submit[key], str) or not submit[key] or any(ch in submit[key] for ch in '\n\r\0'):
            raise FlowError(2, 'invalid_submit_configuration')
    props = submit.setdefault('property_map', {})
    if set(props) - set(PROPERTIES):
        raise FlowError(2, 'unknown_submit_property')
    for index, name in enumerate(PROPERTIES):
        entry = props.setdefault(name, {})
        for key, value in [('control_index', index), ('variable', None), ('encoding', None),
                           ('affects_build', name != 'EMAIL_CC'), ('comparison', 'cmp-v1'),
                           ('request_text_verified', False), ('observed_values', [])]:
            entry.setdefault(key, value)
        if (entry['control_index'] != index or entry['comparison'] != 'cmp-v1'
                or entry['affects_build'] != (name != 'EMAIL_CC')
                or entry['encoding'] not in (None, 'text', 'enum', 'boolean', 'ks')
                or not isinstance(entry['observed_values'], list)
                or (entry['variable'] is not None and
                    (not isinstance(entry['variable'], str) or SECRET_NAME.search(entry['variable'])))):
            raise FlowError(2, 'invalid_property_map')
