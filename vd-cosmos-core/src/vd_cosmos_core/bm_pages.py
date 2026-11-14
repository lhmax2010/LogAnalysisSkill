"""Fixed, in-memory parsers for recon15–22 management pages. No raw HTML escapes."""
import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit
from zoneinfo import ZoneInfo

from .build_inputs import parse_list, sanitize_repositories
from .errors import FlowError
from .export import check_content
from .files import digest, json_bytes
from .report import Document, Node, cells, normalize
from .submit_config import PROPERTIES, SECRET_NAME
from .variable_pages import parse as parse_variables, remember


def document(data):
    try:
        return Document(data.decode('utf-8'))
    except (UnicodeError, ValueError):
        raise FlowError(5, 'bm_page_unrecognized') from None


def page_time(value, zone):
    try:
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S').replace(tzinfo=ZoneInfo(zone)).timestamp()
    except ValueError:
        raise FlowError(5, 'bm_time_unrecognized') from None


def duration(value):
    compact = re.fullmatch(r'(?:(\d+)h:)?(?:(\d+)m:)?(\d+)s', value.strip())
    if compact:
        h, m, s = [int(x or 0) for x in compact.groups()]
        return h * 3600 + m * 60 + s
    parts = re.findall(r'(\d+)\s+(hours?|minutes?|seconds?)', value)
    if not parts or re.sub(r'\d+\s+(?:hours?|minutes?|seconds?)', '', value).strip():
        raise FlowError(5, 'bm_duration_unrecognized')
    return sum(int(n) * (3600 if unit.startswith('hour') else 60 if unit.startswith('minute') else 1) for n, unit in parts)


def nodes_without_promotions(node):
    if normalize(node.attrs.get('title', '')).startswith('Promoted to build'):
        return []
    return [node] + [n for c in node.children if isinstance(c, Node) for n in nodes_without_promotions(c)]


def link_number(href, host, page_url, path='build'):
    u = urlsplit(urljoin(page_url, href))
    if (u.scheme != 'https' or u.netloc != host or u.username or u.password or u.query or u.fragment
            or not re.fullmatch('/' + path + r'/[0-9]+', u.path)):
        return None
    return u.path.rsplit('/', 1)[-1]


def own_rows(table):
    def walk(n):
        for c in n.children:
            if isinstance(c, Node) and c.tag != 'table':
                if c.tag == 'tr':
                    yield c
                else:
                    yield from walk(c)
    return list(walk(table))


def columns(table, required):
    rows = own_rows(table)
    for i, row in enumerate(rows):
        names = [normalize(c.text()) for c in cells(row)]
        if set(required) <= set(names):
            if any(names.count(k) != 1 for k in required):
                raise FlowError(5, 'bm_table_ambiguous')
            return names, rows[i + 1:]
    return None


def detail(data, config, build_id, *, summary_required=True):
    c = config.raw['cosmos']; b = str(build_id); url = 'https://' + c['bm_host'] + '/build/' + b
    doc = document(data)
    heads = [n for n in doc.nodes if 'build-header' in n.attrs.get('class', '').split()]
    if len(heads) != 1:
        raise FlowError(5, 'bm_identity_mismatch')
    head = heads[0]; nodes = nodes_without_promotions(head)
    statuses = [n for n in nodes if re.fullmatch(r'Build is .+', normalize(n.attrs.get('title', '')), re.I)]
    if len(statuses) != 1:
        raise FlowError(5, 'bm_identity_mismatch')
    # Read label position, not URLs found by whole-page searching. Promotions are excluded.
    tokens = []
    def tokens_of(n):
        if normalize(n.attrs.get('title', '')).startswith('Promoted to build'):
            return
        if n.tag == 'a':
            tokens.append(n); return
        for child in n.children:
            if isinstance(child, Node): tokens_of(child)
            elif child.strip(): tokens.append(child)
        if n.tag in {'br', 'div', 'p', 'li'}: tokens.append('\n')
    tokens_of(head)
    labels = []
    for i, token in enumerate(tokens):
        if isinstance(token, str) and re.search(r'\bHub\s+Link\s*:', token):
            if normalize(token).removeprefix('♦').strip() != 'Hub Link :':
                raise FlowError(5, 'bm_page_unrecognized')
            labels.append(i)
    if len(labels) > 1:
        raise FlowError(5, 'bm_page_unrecognized')
    hub_node = None; hub = None
    if labels:
        i = labels[0] + 1
        if i >= len(tokens) or not isinstance(tokens[i], Node):
            raise FlowError(5, 'bm_page_unrecognized')
        hub_node = tokens[i]
        if i + 1 < len(tokens) and isinstance(tokens[i + 1], Node):
            raise FlowError(5, 'bm_page_unrecognized')
        hub = link_number(hub_node.attrs.get('href', ''), c['hub_host'], url)
        if hub is None:
            raise FlowError(5, 'bm_page_unrecognized')
    links = [n for n in nodes if n.tag == 'a' and n is not hub_node]
    own = [link_number(n.attrs.get('href', ''), c['bm_host'], url) for n in links
           if re.match(r'^/build/[^/]+$', urlsplit(urljoin(url, n.attrs.get('href', ''))).path)]
    if not own or any(x != b for x in own):
        raise FlowError(5, 'bm_identity_mismatch')
    configs = {link_number(n.attrs.get('href', ''), c['bm_host'], url, 'overview') for n in links
               if '/overview/' in urlsplit(urljoin(url, n.attrs.get('href', ''))).path}
    if len(configs) != 1 or None in configs:
        raise FlowError(5, 'bm_config_unrecognized')
    pairs, references = [], []
    for n in head.descendants({'a', 'span', 'div'}):
        if not normalize(n.attrs.get('title', '')).startswith('Promoted to build'):
            continue
        match = re.fullmatch(r'UPDATE_BUILDINFO:\s*\[(\d+):(\d+):([A-Z_]+)\]', normalize(n.text()))
        if match:
            entry = {'hub_id': match[1], 'build_id': match[2], 'status': match[3]}
            (pairs if match[2] == b else references).append(entry)
    if not summary_required:
        return {'identity': 'strong', 'config_id': next(iter(configs)), 'hub_id': hub}
    summaries = [columns(t, ['Id', 'Status', 'Begin Date', 'Duration']) for t in doc.nodes if t.tag == 'table']
    summaries = [s for s in summaries if s]
    if len(summaries) != 1:
        raise FlowError(5, 'bm_summary_unrecognized')
    names, rows = summaries[0]
    found = [dict(zip(names, [normalize(n.text()) for n in cells(row)])) for row in rows]
    found = [r for r in found if r.get('Id') == b]
    if len(found) != 1:
        raise FlowError(5, 'bm_summary_unrecognized')
    summary = found[0]; start = page_time(summary['Begin Date'], c['bm_display_tz'])
    state = normalize(statuses[0].attrs['title'])[9:].casefold()
    ended = state in {str(w).casefold() for w in (c.get('status_source') or {}).get('terminal_words', ['successful', 'failed', 'cancelled'])}
    conflict = bool(hub and any(p['hub_id'] != hub for p in pairs)) or len({p['hub_id'] for p in pairs}) > 1
    return {'build_id': b, 'hub_id': hub, 'identity': 'strong', 'config_id': next(iter(configs)),
            'state': state, 'ended': ended, 'start_time': start,
            'end_time': start + duration(summary['Duration']) if ended else None,
            'duration_s': duration(summary['Duration']), 'requester': summary.get('Triggered By'),
            'pairs': pairs, 'references': references, 'conflict': conflict,
            'relation': '冲突' if conflict else 'Hub Link' if hub else '无 Hub Link'}


def listing(data, config, kind):
    c = config.raw['cosmos']; doc = document(data)
    required = ['Hub ID', 'Requester', 'Build Version', 'Schedule Date', 'Process Status'] if kind == 'overview' else ['Version', 'Begin Date', 'Duration']
    tables = [(t, columns(t, required)) for t in doc.nodes if t.tag == 'table']
    tables = [(t, v) for t, v in tables if v]
    if len(tables) != 1:
        raise FlowError(5, 'bm_table_unrecognized')
    _, (names, rows) = tables[0]; result = []
    if kind == 'overview' and names != c['bm_overview_headers']:
        raise FlowError(5, 'bm_table_unrecognized')
    url = 'https://' + c['bm_host'] + '/' + kind + '/' + c['bm_config_id']
    for row in rows:
        cs = cells(row)
        if not cs or all(n.tag == 'th' for n in cs): continue
        values = dict(zip(names, [normalize(n.text()) for n in cs]))
        ids = {link_number(n.attrs.get('href', ''), c['bm_host'], url) for n in row.descendants({'a'})
               if re.fullmatch(r'/build/\d+', urlsplit(urljoin(url, n.attrs.get('href', ''))).path)}
        if not ids: continue
        if len(ids) != 1 or None in ids: raise FlowError(5, 'bm_row_unrecognized')
        entry = {'build_id': ids.pop(), 'version': values.get('Build Version', values.get('Version', '')),
                 'hub_id': values.get('Hub ID') or None, 'requester': values.get('Requester'),
                 'process_status': values.get('Process Status'), 'schedule_date': values.get('Schedule Date'), 'start_time': None,
                 'running': bool(re.search(r'\b\d+%', row.text()))}
        if kind == 'overview' and entry['hub_id'] and not entry['hub_id'].isdecimal():
            raise FlowError(5, 'bm_row_unrecognized')
        if values.get('Begin Date'):
            entry['start_time'] = page_time(values['Begin Date'], c['bm_display_tz'])
            entry['duration_s'] = duration(values['Duration'])
        result.append(entry)
    samples = []
    for table in (n for n in doc.nodes if n.tag == 'table'):
        cols = columns(table, ['Version', 'Begin Date', 'Duration'])
        if not cols: continue
        ns, rs = cols
        for r in rs:
            if not re.search(r'\b\d+%', r.text()): continue
            v = dict(zip(ns, [normalize(n.text()) for n in cells(r)]))
            samples.append({'start_time': page_time(v['Begin Date'], c['bm_display_tz']), 'duration_s': duration(v['Duration'])})
    answer = {'rows': result, 'samples': samples, 'next': None}
    if kind == 'history':
        counts = set(re.findall(r'Showing\s+(\d+)\s+to\s+(\d+)\s+of\s+(\d+)', doc.root.text()))
        if len(counts) != 1: raise FlowError(5, 'bm_history_count_unrecognized')
        first, last, total = map(int, counts.pop())
        if last - first + 1 != len(result) or last > total or first < 1:
            raise FlowError(5, 'bm_history_count_unrecognized')
        nexts = {urljoin(url, n.attrs['href']) for n in doc.nodes if n.tag == 'a' and n.attrs.get('href')
                 and (normalize(n.text()) == '>' or n.attrs.get('title', '').casefold() == 'next')}
        if len(nexts) > 1: raise FlowError(5, 'bm_history_next_ambiguous')
        answer.update(first=first, last=last, total=total, next=next(iter(nexts), None))
    return answer


def cmp_v1(value):
    return '\n'.join(line.rstrip() for line in value.replace('\r\n', '\n').replace('\r', '\n').split('\n')).rstrip('\n')


def base_digest(text, config):
    records = parse_list(text, config.raw['cosmos']['branch_markers'])
    return digest(json_bytes(sorted((r['package_key'], r['path'], r['cl']) for r in records.values())))


def value_shape(value):
    lines = value.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    leading = next((i for i, line in enumerate(lines) if line.strip()), len(lines))
    trailing = next((i for i, line in enumerate(reversed(lines)) if line.strip()), len(lines))
    return {'leading_blank_lines': leading, 'trailing_blank_lines': trailing,
            'indented_lines': sum(bool(line and line[0].isspace()) for line in lines),
            'first_line_indent': len(lines[0]) - len(lines[0].lstrip()),
            'line_lengths': [len(line) for line in lines]}


def variables(data, config, build_id, names):
    names = set(names)
    if any(SECRET_NAME.search(n) for n in names) or not names <= set(PROPERTIES) | {
            e['variable'] for e in config.raw['submit']['property_map'].values() if e['variable'] not in (None, 'not_listed')}:
        raise FlowError(4, 'variable_name_forbidden')
    identity = detail(data, config, build_id, summary_required=False)
    if identity['config_id'] != config.raw['cosmos']['bm_config_id']:
        raise FlowError(4, 'bm_wrong_config')
    result = {}
    for name, entry in parse_variables(data, names).items():
        value = entry['value']
        value, removed = sanitize_repositories(value)
        if not check_content(value.encode(), config)['allowed']:
            raise FlowError(4, 'credential_pattern_blocked')
        result[name] = {'value': value, 'sha256': digest(value.encode()), 'cmp_sha256': digest(cmp_v1(value).encode()),
                        'credentials_removed': removed, 'cells': entry['cells'],
                        'value_column': entry['value_column'], 'table_columns': entry['table_columns'],
                        'enum_display': cmp_v1(value) if cmp_v1(value).casefold() in {'', 'true', 'false', 'yes', 'no', 'on', 'off', 'full', 'partial', 'armv7l'} else None,
                        **value_shape(value)}
    remember(config, build_id, 'https://' + config.raw['cosmos']['bm_host'] + '/build/' + str(build_id) + '/variables',
             {name: entry['value'] for name, entry in result.items()}, names)
    return result


def compare(request, values, config):
    result = {}; props = config.raw['submit']['property_map']
    for name in PROPERTIES:
        if name == 'EMAIL_CC': continue
        entry = props[name]; var = entry['variable']
        if name in {'PACKAGE_LIST', 'SHELVE_LIST'}: var = name
        if name == 'SHELVE_LIST':
            result[name] = '一致' if not values.get(var, {}).get('value', '').strip() else '不一致'; continue
        if var in (None, 'not_listed') or var not in values:
            result[name] = '未核验'; continue
        expected = request['form'].get(name, '')
        actual = values[var]['value']
        if name == 'PACKAGE_LIST':
            try: equal = base_digest(expected, config) == base_digest(actual, config)
            except FlowError: equal = False
        elif entry['encoding'] is None:
            result[name] = '未核验'; continue
        elif entry['encoding'] in {'enum', 'boolean', 'ks'} and str(expected) not in entry['observed_values']:
            result[name] = '未核验'; continue
        else:
            equal = cmp_v1(str(expected)) == cmp_v1(actual)
        result[name] = '一致' if equal else '不一致'
    return {'rule': 'cmp-v1', 'fields': result, 'matches': '不一致' not in result.values(),
            'description': '已核验字段一致', 'unverified': [k for k, v in result.items() if v.startswith('未核验')]}
