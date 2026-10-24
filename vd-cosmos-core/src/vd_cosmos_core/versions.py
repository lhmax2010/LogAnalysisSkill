"""Stable identities for storage and interpretation, never connection secrets."""
from .files import digest, json_bytes

PARSER_VERSION = '0.5.4'


def build_key(reader):
    return digest(json_bytes(reader.build_ref.to_dict()))


def parsing_digest(config):
    cosmos = config.raw['cosmos']
    keys = ('archs', 'regular_archs', 'report_markers', 'header_must_match',
            'detail_table_title_prefix', 'status_source', 'index_link_regex')
    return digest(json_bytes({'cosmos': {k: cosmos.get(k) for k in keys},
        'poll': {k: config.raw['poll'][k] for k in ('interval_s', 'settle_s')}, 'parser': PARSER_VERSION}))


def evaluation(reader, observation):
    return digest(json_bytes({'reports': {a: r.get('evidence', {}).get('sha256')
        for a, r in observation.get('reports', {}).items()},
        'expected': reader.expected_digest(), 'parsing': parsing_digest(reader.config), 'parser': PARSER_VERSION}))
