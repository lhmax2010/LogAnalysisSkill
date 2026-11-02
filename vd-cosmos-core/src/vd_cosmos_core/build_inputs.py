"""Whitelisted, immutable build-variable inputs. Full HTML never reaches disk."""
import re
from urllib.parse import urlsplit, urlunsplit
from .defaults import VARIABLES
from .errors import FlowError
from .export import check_content
from .files import atomic_write, digest, json_bytes, load_json
from .observation import detail_state
from .report import Document, cells, normalize
from .versions import build_key


def package_root(path):
    path = path.strip()
    if path.endswith('/...'):
        path = path[:-4]
    if not path.startswith('//') or any(x in {'.', '..'} for x in path[2:].split('/')) or '...' in path:
        raise FlowError(4, 'invalid_package_root')
    return path.rstrip('/')


def package_key(path, markers):
    return '/' + '/'.join(p for p in package_root(path).split('/') if p and p not in markers)


def parse_list(text, markers, *, shelved=False):
    entries = {}
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        match = re.fullmatch(r'(//.+)@' + ('=' if shelved else '') + r'([0-9]+)', line)
        if not match:
            raise mismatch('invalid_line', line_number=number)
        path, cl = match.groups()
        key = package_key(path, markers)
        if key in entries:
            raise mismatch('duplicate_package_key', line_number=number)
        entries[key] = {'package_key': key, 'path': path, 'root': package_root(path),
                        'cl': cl, 'shelve': shelved, 'line_number': number, 'raw': line}
    if not entries and not shelved:
        raise mismatch('empty_base_list')
    return entries


def mismatch(kind, **details):
    return FlowError(4, 'build_inputs_report_mismatch', todo={'reason': 'build_inputs_report_mismatch',
        'message': '构建输入与报告不符', 'difference': kind, **details})


def compare_lists(base_text, shelve_text, reports, markers):
    base = parse_list(base_text, markers)
    shelves = parse_list(shelve_text, markers, shelved=True) if shelve_text is not None else None
    rows = {}
    for arch, report in reports.items():
        seen = set()
        for row in report.get('input_rows', []):
            key = package_key(row['path'], markers)
            value = (row['path'], str(row['cl']), bool(row['shelve']))
            if key in seen or (key in rows and rows[key] != value):
                raise mismatch('report_duplicate_or_ambiguous', arch=arch)
            seen.add(key)
            rows[key] = value
    if not rows:
        raise mismatch('report_inputs_missing')
    for key, (path, cl, shelve) in rows.items():
        if key not in base:
            raise mismatch('missing_base_package', package_key=key)
        if not shelve and (base[key]['path'], base[key]['cl']) != (path, cl):
            raise mismatch('non_shelve_row_differs', package_key=key)
    expected = {(key, path, cl) for key, (path, cl, sh) in rows.items() if sh}
    if shelves is not None:
        actual = {(key, e['path'], e['cl']) for key, e in shelves.items()}
        if actual != expected:
            raise mismatch('shelve_list_differs', missing=sorted(expected-actual), extra=sorted(actual-expected))
    return {'base': base, 'shelve': shelves, 'extra_base_packages': sorted(set(base)-set(rows)),
            'shelve_list_verified': shelves is not None,
            'note': '逐项核对通过' if shelves is not None else '人工绑定 base、未取得原始 shelve 清单'}


def sanitize_repositories(value):
    changed = False
    def strip(match):
        nonlocal changed
        parsed = urlsplit(match[0])
        if parsed.username is None and parsed.password is None:
            return match[0]
        changed = True
        return urlunsplit((parsed.scheme, parsed.netloc.rsplit('@', 1)[-1], parsed.path, parsed.query, parsed.fragment))
    return re.sub(r'[A-Za-z][A-Za-z0-9+.-]*://[^\s]+', strip, value), changed


def variables(data, config, build_id, page_url):
    source = config.raw['cosmos'].get('status_source')
    if not source or detail_state(data, source, build_id, page_url).get('identity') != 'strong':
        raise FlowError(5, 'variables_identity_mismatch', todo={'reason': 'bind_base_list_required'})
    document = Document(data.decode('utf-8'))
    values = {}
    # Only the name cell is inspected to choose a row. No value from a rejected
    # row is read out or included in exceptions, logs, or evidence.
    for row in (n for n in document.nodes if n.tag == 'tr'):
        columns = cells(row)
        if len(columns) < 2:
            continue
        name = columns[0].text().strip()
        if name not in VARIABLES:
            continue
        if name in values:
            raise mismatch('duplicate_whitelisted_variable')
        values[name] = '\n'.join(line.strip() for line in columns[1].text().splitlines() if line.strip())
    if set(values) != set(VARIABLES):
        raise FlowError(5, 'variables_missing', todo={'reason': 'bind_base_list_required'})
    stripped = []
    for name in ('BASE_REPOS', 'PRODUCT_REPOS'):
        values[name], changed = sanitize_repositories(values[name])
        if changed:
            stripped.append(name)
    for name, value in values.items():
        if not check_content(value.encode(), config)['allowed']:
            raise FlowError(4, 'build_input_credential_blocked', todo={'reason': 'build_input_credential_blocked'})
    return values, {'credentials_removed': stripped, 'note': '已去除凭据' if stripped else None}


def freeze(config, key, values, reports, *, source, note=None):
    markers = config.raw['cosmos']['branch_markers']
    for text in values.values():
        if text is not None and not check_content(text.encode(), config)['allowed']:
            raise FlowError(4, 'build_input_credential_blocked')
    compared = compare_lists(values['PACKAGE_LIST'], values.get('SHELVE_LIST'), reports, markers)
    folder = 'rounds/' + key + '/inputs/build-lists'
    identity = {k: digest(v.encode()) for k, v in values.items() if v is not None}
    destination = config.output(folder + '/manifest.json')
    if destination.exists():
        previous = load_json(destination)
        if previous['digests'] != identity:
            raise FlowError(4, 'immutable_build_inputs_changed', todo={'reason': 'immutable_build_inputs_changed'})
        for name, artifact in previous['files'].items():
            path = config.output(artifact['path'])
            if not path.is_file() or digest(path.read_bytes()) != artifact['sha256']:
                raise FlowError(4, 'immutable_input_digest_mismatch')
        return previous
    files = {name: atomic_write(config.data_root, folder + '/' + name + '.txt', value.encode())
             for name, value in values.items() if value is not None}
    result = {'source': source, 'digests': identity, 'files': files, **compared, 'security': note or {}}
    atomic_write(config.data_root, destination, json_bytes(result))
    return result


def fetch_build_inputs(reader):
    observed = reader.observe(reader.build_ref)
    if observed.get('observation_failed') or observed.get('header_consistency') == '不一致':
        raise mismatch('reports_not_available')
    config, build_id = reader.config, reader.build_ref.run_id
    template = config.raw['cosmos'].get('variables_url_template')
    if not template:
        raise FlowError(6, 'variables_url_required')
    url = template.format(build_id=build_id)
    if urlsplit(url).scheme != 'https':
        raise FlowError(4, 'variables_https_required')
    if hasattr(reader, 'manifest'):
        path = reader.manifest.get('variables_page')
        if not path:
            raise FlowError(5, 'fixture_variables_missing')
        from .files import confined
        body = confined(reader.base, path).read_bytes()
    else:
        response = reader.transport.get(url, config.raw['fetch']['max_page_bytes'])
        if response['status'] != 200:
            raise FlowError(5, 'variables_fetch_failed')
        body = response['body']
    values, note = variables(body, config, build_id, url)
    for field, name in [('base', 'BASE_REPOS'), ('product', 'PRODUCT_REPOS'), ('build_conf', 'BUILD_CONF')]:
        if any(normalize(r.get('headers', {}).get(field, '')) != normalize(values[name]) for r in observed['reports'].values()):
            raise mismatch('header_variable_differs', field=field)
    return freeze(config, build_key(reader), values, observed['reports'], source='variables_page', note=note)
