"""Compiler-emitted flags, versioned family membership and location facts."""
import re
from xml.etree import ElementTree

from .analysis_tools import ROOT
from .errors import FlowError
from .files import atomic_write, digest, json_bytes, load_json

RELEASE = re.compile(r'[0-9][A-Za-z0-9.+_~]*-[0-9][A-Za-z0-9.+_~]*')
FLAG = re.compile(r'-W[A-Za-z0-9][A-Za-z0-9_-]*')
OPTION = r'-W(?:error=)?[A-Za-z0-9_-]+'
GROUP = re.compile(r'\[(' + OPTION + r'(?:,\s*' + OPTION + r')*)\]\s*$')
DIAGNOSTIC = re.compile(r'^(?P<file>.+?):(?P<line>[0-9]+)(?::(?P<column>[0-9]+))?:\s+'
                        r'(?:warning|error|fatal error):\s+(?P<body>.*)$')
ANSI = re.compile(r'\x1b\[[0-9;]*m')
MANDATORY_FAMILIES = frozenset({
    '-Wformat', '-Wdangling', '-Wuninitialized', '-Warray-bounds',
    '-Wincompatible-pointer-types', '-Wtautological-compare',
})
PEEK_OVERRIDES = frozenset({'-Wformat-pedantic', '-Wformat-zero-length',
                            '-Wincompatible-pointer-types-discards-qualifiers'})
PEEK_FAMILIES = frozenset({'-Wswitch', '-Wlogical-not-parentheses'})


def seed_tiers():
    path = ROOT / 'docs/enhance/vd-cosmos-loganalyzer-hld-v0.9.18.md'
    text = path.read_text(encoding='utf-8')
    strong = next(s for s in text.splitlines() if s.lstrip().startswith('- **强制人工定性档**'))
    peek = next(s for s in text.splitlines() if s.lstrip().startswith('- **需看一眼档**'))
    return {'mandatory': set(re.findall(r'`(-W[\w-]+)`', strong)).union(MANDATORY_FAMILIES),
            'peek': set(re.findall(r'`(-W[\w-]+)`', peek.partition('。')[0])).union(PEEK_OVERRIDES)}


def normalize(value):
    if value.startswith('-Werror='):
        value = '-W' + value.removeprefix('-Werror=')
    return value if FLAG.fullmatch(value) and value not in {'-Werror', '-Wfatal-errors'} else None


def compiler_locations(log, prefix_regex, snapshot, input_digest):
    prefix = re.compile(prefix_regex)
    source_locations = {(r.get('diagnostic', {}).get('path'), r.get('diagnostic', {}).get('line'),
                         r.get('diagnostic', {}).get('column'), r.get('diagnostic', {}).get('log_line')): r
                        for r in snapshot.get('locations', [])}
    found = []
    for number, original in enumerate(log.decode('utf-8', 'replace').splitlines(), 1):
        line = ANSI.sub('', prefix.sub('', original, count=1))
        match = DIAGNOSTIC.fullmatch(line)
        group = GROUP.search(match['body']) if match else None
        if not group:
            continue
        row = (match['file'], int(match['line']), int(match['column']) if match['column'] else None)
        location = source_locations.get((*row, number), {})
        for flag in set(filter(None, map(normalize, re.split(r',\s*', group[1])))):
            data = {'path': location.get('depotFile') or row[0], 'line': row[1], 'column': row[2],
                    'path_class': (location.get('classification') or {}).get('class'), 'line_check': location.get('diagnostic_line_match'),
                    'log_line': number, 'flag': flag, 'context_sha256': digest(line.encode()),
                    'source_input_digest': input_digest}
            found.append(dict(data, location_id=digest(json_bytes(data))))
    return sorted(found, key=lambda row: (row['log_line'], row['flag']))


def repodata_opener(suffix):
    try:
        if suffix == '.xz':
            import lzma
            return lzma.open, (lzma.LZMAError,)
        if suffix == '.bz2':
            import bz2
            return bz2.open, ()
        if suffix == '.gz':
            import gzip
            import zlib
            return gzip.open, (zlib.error,)
    except ImportError:
        module, advice = {
            '.xz': ('lzma', 'use the .gz repodata or a Python built with liblzma'),
            '.bz2': ('bz2', 'use the .gz repodata or a Python built with libbz2'),
            '.gz': ('zlib', 'use uncompressed repodata or a Python built with zlib'),
        }[suffix]
        reason = module + '_unavailable'
        raise FlowError(6, reason, todo={'reason': reason, 'message': advice}) from None
    return open, ()


def clang_release(path):
    opener, codec_errors = repodata_opener(path.suffix)
    invalid = (OSError, ValueError, KeyError, ElementTree.ParseError, EOFError) + codec_errors
    namespace = '{http://linux.duke.edu/metadata/common}'
    try:
        with opener(path, 'rb') as stream:
            # Primary XML is local, imported evidence. Bound decompression before parsing.
            raw = stream.read(256 * 1024 * 1024 + 1)
        if len(raw) > 256 * 1024 * 1024 or re.search(br'<!\s*(?:DOCTYPE|ENTITY)', raw, re.I):
            raise ValueError
        root = ElementTree.fromstring(raw)
        matches = {f'{node.attrib["ver"]}-{node.attrib["rel"]}'
                   for package in root.findall(namespace+'package')
                   if package.findtext(namespace+'name') == 'clang'
                   for node in package.findall(namespace+'version')}
        if root.tag != namespace+'metadata' or len(matches) != 1:
            raise ValueError
        release = matches.pop()
        if not RELEASE.fullmatch(release):
            raise ValueError
        return release
    except invalid:
        raise FlowError(4, 'clang_primary_repodata_invalid') from None


def validate_family(value):
    if (type(value) is not dict or set(value) != {'schema_version', 'clang_release', 'tiers'}
            or value['schema_version'] != 1 or not isinstance(value['clang_release'], str)
            or not RELEASE.fullmatch(value['clang_release']) or type(value['tiers']) is not dict
            or set(value['tiers']) != {'mandatory', 'peek'}):
        raise FlowError(4, 'diagnosis_family_invalid')
    tiers = value['tiers']
    for flags in tiers.values():
        if (type(flags) is not list or len(flags) > 4096
                or any(not isinstance(f, str) or normalize(f) != f for f in flags)
                or len(set(flags)) != len(flags)):
            raise FlowError(4, 'diagnosis_family_invalid')
    required = seed_tiers()
    if (set(tiers['mandatory']) & set(tiers['peek'])
            or not all(required[k].issubset(tiers[k]) for k in required)):
        raise FlowError(4, 'diagnosis_family_invalid')
    return value


def version_source(config, build, override=None):
    if override:
        path = config.output(override)
        return clang_release(path)
    base = config.output(f'rounds/{build}/inputs/base-repodata')
    paths = sorted(p for p in base.glob('primary.xml*') if p.is_file() and not p.is_symlink())
    if not paths:
        return None
    if len(paths) != 1:
        raise FlowError(4, 'clang_primary_repodata_ambiguous')
    return clang_release(paths[0])


def import_family(config, build, source, primary=None):
    if not re.fullmatch(r'[0-9a-f]{64}', build):
        raise FlowError(2, 'invalid_analysis_build')
    release = version_source(config, build, primary)
    family = validate_family(load_json(config.source(source)))
    if not release or release != family['clang_release']:
        raise FlowError(4, 'diagnosis_family_release_mismatch')
    return atomic_write(config.data_root, f'diagnosis-families/{release}.json', json_bytes(family))


def loaded_family(config, release):
    if release:
        path = config.output(f'diagnosis-families/{release}.json')
        if path.exists():
            family = validate_family(load_json(path))
            if family['clang_release'] != release:
                raise FlowError(4, 'diagnosis_family_release_mismatch')
            return family
    return None


def classify(config, log, snapshot, source_digest, release):
    family = loaded_family(config, release)
    tiers = family['tiers'] if family else seed_tiers()
    extra = config.raw.get('rules', {}).get('suspect_bug_flags', [])
    if not isinstance(extra, list) or any(not isinstance(f, str) or normalize(f) != f for f in extra):
        raise FlowError(2, 'analysis_bug_flags_invalid')
    mandatory, peek = set(tiers['mandatory']) | set(extra), set(tiers['peek'])
    prefix = config.raw['analyzer']['log_line_prefix_regex']
    locations = compiler_locations(log, prefix, snapshot, source_digest)
    for row in locations:
        flag = row['flag']
        promoted = not family and flag not in peek and any(
            flag.startswith(parent+'-') for parent in MANDATORY_FAMILIES)
        row['tier'] = 'mandatory' if flag in mandatory or promoted else 'peek' if flag in peek else 'ordinary'
        row['temporary_prefix_upgrade'] = promoted
    return {'clang_release': release, 'family_sha256': digest(json_bytes(family)) if family else None,
            'family_state': 'matched' if family else 'unverified', 'locations': locations}


def grouping(task):
    diagnosis = task.get('diagnosis', {})
    groups = {}
    for loc in diagnosis.get('locations', []):
        if loc['tier'] != 'ordinary':
            groups.setdefault((loc['flag'], loc['tier']), []).append(loc['location_id'])
    return [{'flag': flag, 'tier': tier, 'locations': locations}
            for (flag, tier), locations in sorted(groups.items())]
