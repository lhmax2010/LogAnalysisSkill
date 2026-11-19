"""Fixed, in-memory parsers for recon15–22 management pages. No raw HTML escapes."""
import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit
from zoneinfo import ZoneInfo

from .build_inputs import parse_list, sanitize_repositories, variable_names
from .errors import FlowError
from .export import check_content
from .files import digest, json_bytes
from .report import Document, Node, cells, normalize
from .submit_config import NOT_LISTED, PROPERTIES, SECRET_NAME
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
    # Page tabs, not history navigation buttons, prove the requested build.
    from .detail_identity import tab_identity
    tab_identity(doc, b, url)
    configs = set()
    for n in doc.nodes:
        if n.tag != 'a' or 'nav-link' not in n.attrs.get('class','').split():continue
        target=urlsplit(urljoin(url,n.attrs.get('href','')))
        if re.fullmatch(r'/overview/[0-9]+',target.path):
            value=link_number(n.attrs.get('href',''),c['bm_host'],url,'overview')
            if value is None:raise FlowError(5,'bm_config_unrecognized')
            configs.add(value)
    if len(configs)!=1:raise FlowError(5,'bm_config_unrecognized')
    labels=[]
    for dashboard in (n for n in doc.nodes if n.attrs.get('id')=='build-dashboard'):
        for description in dashboard.descendants({'div','section'}):
            if {'html-content','description'} <= set(description.attrs.get('class','').split()):
                labels.extend(n for n in description.descendants({'h3'}) if normalize(n.text()).startswith('♦ Hub Link :'))
    labels=list({n.order:n for n in labels}.values())
    if len(labels)>1:raise FlowError(5,'bm_page_unrecognized')
    hub=None
    if labels:
        links=list(labels[0].descendants({'a'}))
        if len(links)!=1:raise FlowError(5,'bm_page_unrecognized')
        hub=link_number(links[0].attrs.get('href',''),c['hub_host'],url)
        if hub is None:raise FlowError(5,'bm_page_unrecognized')
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


BUILD_TARGET_VARS = frozenset({'HUB_CONFIG_ID', 'HUB_CONFIG_PATH', 'FROM_HUB_ID'})


def build_target(config, candidate, values, *, require=False):
    submit = config.raw['submit']
    expected = {'HUB_CONFIG_ID': submit['target_config_id'], 'HUB_CONFIG_PATH': submit['target_config'],
                'FROM_HUB_ID': candidate['hub_id']}
    evidence = {}
    for name, wanted in expected.items():
        entry = values.get(name)
        if entry is None:
            evidence[name] = {'status': 'unverified'}
            continue
        if entry['value'] != wanted:
            raise FlowError(4, 'build_target_mismatch', variable=name, build_id=candidate['build_id'],
                            expected=wanted, observed=entry['value'])
        evidence[name] = {'status': 'verified', 'value': entry['value'], 'sha256': entry['sha256']}
    if require:
        for name in ('HUB_CONFIG_ID', 'HUB_CONFIG_PATH'):
            if evidence[name]['status'] != 'verified':
                raise FlowError(4, 'build_target_unverified', variable=name, build_id=candidate['build_id'],
                                build_target=evidence)
    return evidence


def variables(data, config, build_id, names, *, write=True):
    names = set(names)
    if any(SECRET_NAME.search(n) for n in names) or not names <= set(PROPERTIES) | variable_names(config) | BUILD_TARGET_VARS | {
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
             {name: entry['value'] for name, entry in result.items()}, names, write=write)
    return result


def compare(request, values, config):
    result = {}; props = config.raw['submit']['property_map']
    for name in PROPERTIES:
        entry = props[name]; var = entry['variable']
        if name in NOT_LISTED or var == 'not_listed':
            result[name] = '未核验'; continue
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
            equal = cmp_v1(entry.get('variable_values', {}).get(expected, expected)) == cmp_v1(actual)
        result[name] = '一致' if equal else '不一致'
    return {'rule': 'cmp-v1', 'fields': result, 'matches': '不一致' not in result.values(),
            'description': '已核验字段一致', 'unverified': [k for k, v in result.items() if v.startswith('未核验')]}
