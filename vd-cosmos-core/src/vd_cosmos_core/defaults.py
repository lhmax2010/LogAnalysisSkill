"""Read-side defaults for HLD v0.9.18; no connection is made during loading."""
import re
from pathlib import Path
from string import Formatter
from urllib.parse import urlsplit
from .errors import FlowError
from .versions import PARSER_VERSION

HEADER_RULE = 'unique-build-header-with-own-link'
VARIABLES = ('PACKAGE_LIST', 'SHELVE_LIST', 'BASE_REPOS', 'BUILD_CONF', 'PRODUCT_REPOS')
CODE0_TABLE = {'2026.1': {
    '554768759': {'category': 'file_missing', 'severity': 2, 'exit_code': 0},
    '554768749': {'category': 'history_missing', 'severity': 2, 'exit_code': 0},
    '822220826': {'category': 'history_missing', 'severity': 3, 'exit_code': 1},
    '807672853': {'category': 'not_logged_in', 'severity': 3, 'exit_code': 1}}}


def configure(raw):
    cosmos = raw['cosmos']
    source = cosmos.get('status_source')
    if source:
        if source.setdefault('header_rule', HEADER_RULE) != HEADER_RULE:
            raise FlowError(2, 'header_rule_migration_required', required=HEADER_RULE)
        cosmos.setdefault('variables_url_template', 'https://' + urlsplit(source['url_template']).netloc + '/build/{build_id}/variables')
    cosmos.setdefault('variables_whitelist', list(VARIABLES))
    if sorted(cosmos['variables_whitelist']) != sorted(VARIABLES):
        raise ValueError('variable whitelist must contain the five supported names')
    cosmos.setdefault('branch_markers', ['[INT]', '[FET]', '[COSMOS]'])
    markers = cosmos['branch_markers']
    if not isinstance(markers, list) or len(set(markers)) != len(markers) or not all(isinstance(m, str) and m and '/' not in m and m not in {'.', '..'} for m in markers):
        raise ValueError()
    template = cosmos.get('variables_url_template')
    if template:
        url = urlsplit(template)
        fields = [f for _, f, spec, conv in Formatter().parse(template) if f is not None]
        if (fields != ['build_id'] or '{build_id}' not in template or url.scheme != 'https'
                or not url.hostname or url.username or url.password or url.query or url.fragment
                or url.path != '/build/{build_id}/variables'
                or (source and url.hostname != urlsplit(source['url_template']).hostname)):
            raise FlowError(2, 'invalid_variables_url_template')
    for key, default in [('arch_lag_s', 14400), ('post_terminal_watch_s', 7200), ('retry_after_event_s', 5)]:
        positive(raw['poll'], key, default)
    positive(raw.setdefault('loop', {}), 'max_uncounted_skip_s', 1800)
    p4 = raw.setdefault('p4', {})
    values = {'port': 'example.invalid:1666', 'user': 'configure-user',
              'expected_server_address': 'example.invalid:1666', 'no_client_name': 'vd-cosmos-noclient',
              'unknown_client_marker': '*unknown*', 'read_config_name': None,
              'tickets_file': str(Path.home() / '.p4tickets'), 'executable': 'p4',
              'version': '2026.1', 'output_protocol': '-G', 'code0_table': CODE0_TABLE}
    for key, value in values.items():
        p4.setdefault(key, value)
    for key in ('port', 'user', 'expected_server_address', 'no_client_name', 'unknown_client_marker', 'tickets_file', 'executable', 'version'):
        if not isinstance(p4[key], str) or not p4[key] or any(c in p4[key] for c in '\r\n\0'):
            raise ValueError()
    if p4['output_protocol'] != '-G' or not isinstance(p4['code0_table'], dict):
        raise ValueError()
    if p4['read_config_name'] is not None and (not isinstance(p4['read_config_name'], str) or '/' in p4['read_config_name'] or p4['read_config_name'] in {'', '.', '..'}):
        raise ValueError()
    for key, value in [('min_ticket_minutes', 60), ('unclassified_retry_limit', 3), ('timeout_s', 120), ('min_root_depth', 5)]:
        positive(p4, key, value)
    if type(p4['unclassified_retry_limit']) is not int or type(p4['min_root_depth']) is not int:
        raise ValueError()
    snapshot = raw.setdefault('snapshot', {})
    if snapshot.setdefault('merge_tool', 'git-merge-file') != 'git-merge-file' or 'merge_command' in snapshot:
        raise ValueError()
    positive(snapshot, 'clock_margin_s', 300)
    positive(snapshot, 'merge_timeout_s', 60)
    analyzer = raw.setdefault('analyzer', {})
    for key, value in [('root_list_max_files', 20000), ('ambiguity_candidates_max', 50), ('clang_tabstop', 8), ('snapshot_max_files', 20), ('snapshot_max_file_bytes', 2097152), ('snapshot_max_total_bytes', 20971520)]:
        positive(analyzer, key, value)
        if type(analyzer[key]) is not int:
            raise ValueError()
    pattern = analyzer.setdefault('log_line_prefix_regex', r'^\[\s*\d+s\] ')
    if not isinstance(pattern, str) or not pattern.startswith('^') or re.compile(pattern).match(''):
        raise ValueError('invalid log prefix regex')
    analyzer.setdefault('line_mapped_exts', ['.y', '.yy', '.ypp', '.l', '.ll', '.lex', '.re', '.rl', '.gperf'])
    if not isinstance(analyzer['line_mapped_exts'], list) or not all(isinstance(x, str) and x.startswith('.') for x in analyzer['line_mapped_exts']):
        raise ValueError('invalid line mapped extensions')
    # An old generated default is migrated; custom user agents stay explicit.
    agent = raw.setdefault('fetch', {}).get('user_agent', '')
    if not agent or agent.startswith('VD-Cosmos-LogAnalyzer/'):
        raw['fetch']['user_agent'] = 'VD-Cosmos-LogAnalyzer/' + PARSER_VERSION


def positive(target, key, default):
    value = target.setdefault(key, default)
    if type(value) not in (int, float) or not 0 < value < float('inf'):
        raise ValueError()
