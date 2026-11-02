"""Deterministic source snapshots and provenance; never modifies a P4 workspace."""
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import hashlib
import posixpath
import re
import subprocess
import sys
from urllib.parse import urlsplit
from vd_cosmos_core.build_inputs import package_root, package_key
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.files import atomic_write, digest, json_bytes

RELIABLE = {'版本确定（报告行）', '请求 base（shelve 包同步方式待确认）', '原样叠加', '已合并'}
ANSI = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')


def diagnostics(log):
    lines = ANSI.sub('', log.decode('utf-8', errors='surrogateescape')).splitlines()
    found = []
    for i, text in enumerate(lines):
        match = re.match(r'(.+?):([0-9]+):(?:[0-9]+:)?\s*(fatal error|error|warning):', text)
        if not match:
            continue
        source = lines[i+1] if i+2 < len(lines) and '^' in lines[i+2] else None
        found.append({'path': match[1], 'line': int(match[2]), 'level': match[3], 'source_line': source})
    return sorted(found, key=lambda d: d['level'] == 'warning')


def classify_path(path, name, log=''):
    if '\0' in path or '..' in path.split('/'):
        return {'kind': '外部路径', 'relative': None}
    buildroot = re.search(r'/BUILDROOT/([^/]+)/(.+)$', path)
    if buildroot:
        own = set(re.findall(r'(?:RPM_BUILD_ROOT=|\+ cd\s+)[\x22\x27]?([^\s\x22\x27]*/BUILDROOT/[^/\s\x22\x27]+)', log))
        root = path[:path.index('/BUILDROOT/')] + '/BUILDROOT/' + buildroot[1]
        inferred = not own
        belongs = root in own if own else buildroot[1].casefold().startswith(name.casefold())
        return {'kind': '本包已安装文件' if belongs else '外部依赖', 'relative': buildroot[2] if belongs else None, 'inferred': inferred}
    match = re.search(r'/rpmbuild/BUILD/[^/]+/(.+)$', path)
    if match and not match[1].startswith('/'):
        return {'kind': '源码', 'relative': match[1]}
    return {'kind': '外部依赖', 'relative': None}


def generated(relative):
    return bool(re.search(r'(^|/)(?:build|_build|obj-[^/]+)(/|$)', relative) or
                re.fullmatch(r'config\.h|.+\.pb\.h|moc_.+|.+\.tab\.[ch]', posixpath.basename(relative)))


def locate(classification, root, inventory):
    relative = classification.get('relative')
    if relative is None:
        return None, classification['kind']
    target = root + '/' + relative
    if classification['kind'] == '源码' and target in inventory:
        return target, '直接定位'
    if classification['kind'] == '源码' and generated(relative):
        return None, '生成文件'
    parts = relative.split('/')
    if len(parts) < 3:
        return None, '无法定位'
    suffix = '/' + '/'.join(parts[-3:])
    candidates = [p for p in inventory if p.startswith(root + '/') and p.endswith(suffix)]
    return (candidates[0], '回退候选') if len(candidates) == 1 else (None, '无法定位')


def clang_display(raw):
    text = raw.decode('utf-8', errors='surrogateescape')
    output = []
    for char in text:
        code = ord(char)
        if 0xdc80 <= code <= 0xdcff:
            output.append('<%02X>' % (code - 0xdc00))
        elif char == '\t' or char.isprintable():
            output.append(char)
        else:
            output.append('<U+%04X>' % code)
    return ''.join(output).expandtabs(8)


def compare_source(content, diagnostic, *, merged=False, transcoded=False):
    source = diagnostic.get('source_line')
    if source is None:
        return '未核对'
    if transcoded:
        return '无法核对'
    lines = content.split(b'\n')
    number = diagnostic['line']
    if not 0 < number <= len(lines):
        return '不一致'
    raw = lines[number-1].rstrip(b'\r')
    if merged and re.search(rb'\$(?:Id|Header|Revision|Date|DateTime|Author|File|Change)(?::[^$]*)?\$', raw):
        return '无法核对'
    shown = ANSI.sub('', source).rstrip('\r')
    prefix = re.match(r'^\s*([0-9]+) \| ', shown)
    if prefix:
        if int(prefix[1]) != number:
            return '不一致'
        shown = shown[prefix.end():]
    return '源码行一致' if clang_display(raw) == shown else '不一致'


def merge(config, folder, current, ancestor, shelf):
    inputs = [atomic_write(config.data_root, folder + '/' + n, v) for n, v in
              [('current', current), ('ancestor', ancestor), ('shelved', shelf)]]
    try:
        process = subprocess.run(['git', 'merge-file', '-p', '--', *[i['path'] for i in inputs]],
            cwd=config.data_root, capture_output=True, timeout=config.raw['snapshot']['merge_timeout_s'])
    except (OSError, subprocess.TimeoutExpired):
        return {'kind': '工具错误', 'content': None, 'inputs': inputs}
    code = process.returncode
    return {'kind': '无冲突' if code == 0 else '内容冲突' if 1 <= code <= 127 else '工具错误',
            'content': process.stdout if code == 0 else None, 'returncode': code, 'inputs': inputs}


def after_start(update, start, server_date):
    match = re.search(r'([+-][0-9]{4})', server_date)
    if not match:
        raise FlowError(5, 'p4_server_timezone_missing')
    tz = datetime.strptime(match[1], '%z').tzinfo
    def date(value):
        if str(value).isdigit():
            return datetime.fromtimestamp(int(value), tz)
        value = value.replace('/', '-')
        stamp = datetime.fromisoformat(value)
        return stamp.replace(tzinfo=tz) if stamp.tzinfo is None else stamp
    return date(update) >= date(start).replace(second=0, microsecond=0)


def notice(build_id, name, path, scl, base_rev, current_rev, result):
    return f'[shelve 已自动合并] 构建 {build_id} 包 {name} 文件 {path}：shelve {scl} 基于 #{base_rev}，本轮为 #{current_rev}，结果：{result}'


def archive_sources(adapter, inventory, root, revision, limit):
    archives = {p for p in inventory if posixpath.dirname(p) == root and re.search(r'\.(?:tar\.[^/]+|tgz|zip)$', p)}
    if not archives:
        return []
    matched = set()
    for path in inventory:
        if not path.endswith('.spec'):
            continue
        size = adapter.file_size(path, revision)
        if size is None or size > limit:
            continue
        spec = adapter.print_file(path, revision).decode('utf-8', errors='replace')
        macros = {m[1].lower(): m[2].strip() for m in re.finditer(r'(?im)^(Name|Version):\s*(.+)$', spec)}
        for match in re.finditer(r'(?im)^Source[0-9]*:\s*(.+)$', spec):
            source = match[1].strip()
            for name, value in macros.items():
                source = source.replace('%{' + name + '}', value)
            if '%{' in source:
                matched.update(archives)
            elif root + '/' + posixpath.basename(urlsplit(source).path) in archives:
                matched.add(root + '/' + posixpath.basename(urlsplit(source).path))
    return sorted(matched)


def snapshot(config, adapter, package, headers, log, folder, *, build_id, lists=None, input_confirmations=(), log_metadata=None, notice_seen=()):
    adapter.login_status()
    info = adapter.info()
    started = datetime.now(timezone.utc)
    row_root = package_root(package['key']['path'])
    shelved, scl = package['shelve'], str(package['cl'])
    key = package_key(row_root, config.raw['cosmos']['branch_markers'])
    base = lists.get('base', {}).get(key) if lists else None
    root = base['root'] if shelved and base else row_root
    revision = '@' + (base['cl'] if shelved and base else scl)
    if shelved and not base:
        points = [scl, *(log_metadata or {}).get('known_sync_cls', [])]
        if not all(str(point).isdigit() for point in points):
            raise FlowError(4, 'invalid_known_sync_cl')
        revision = '@' + str(min(int(point) for point in points))
    inventory = {r['depotFile']: r for r in adapter.list_files(root, revision)}
    desc = adapter.describe(scl) if shelved else None
    change = adapter.change(scl) if desc and not desc['historical_missing'] else None
    history_lost = bool(desc and desc['historical_missing'])
    if change and change['category'] == 'ok' and desc['digest'] not in input_confirmations:
        history_lost |= after_start(change['records'][0]['shelveUpdate'], headers['start_time'], info['serverDate'])
    own = {f['depotFile']: f for f in (desc or {}).get('files', []) if f['depotFile'].startswith(row_root + '/')}
    foreign = [f['depotFile'] for f in (desc or {}).get('files', []) if f['depotFile'] not in own]
    cross = shelved and base and row_root != root
    affected = {root + p[len(row_root):]: f for p, f in own.items()}
    candidates = diagnostics(log)
    if not candidates:
        adapter.login_status(require_minimum=False)
        return {'mode': '仅诊断', 'reason': '未取得错误位置', 'files': [], 'notices': [], 'known_effect': '读取 shelve 会更新 shelveAccess'}
    available = set(inventory) | set(affected)
    selected, locations = [], []
    log_text = log.decode('utf-8', errors='replace')
    for diagnostic in candidates:
        classification = classify_path(diagnostic['path'], package['key']['name'], log_text)
        path, location = locate(classification, root, available)
        locations.append({'diagnostic': diagnostic, 'classification': classification, 'depotFile': path, 'location': location})
        if path and path not in selected and len(selected) < config.raw['analyzer']['snapshot_max_files']:
            selected.append(path)
    scripts = {'CMakeLists.txt', 'Makefile', 'meson.build', 'configure.ac'}
    for path in sorted(inventory):
        if path.endswith('.spec') or (posixpath.dirname(path) == root and posixpath.basename(path) in scripts):
            if path not in selected:
                selected.append(path)
    result, notices, total = [], [], 0
    primary = locations[0]['depotFile']
    diagnostic_only = primary is None
    if primary is None and locations[0]['classification']['kind'] == '源码':
        archives = archive_sources(adapter, inventory, root, revision, config.raw['analyzer']['snapshot_max_file_bytes'])
        if archives:
            locations[0]['location'] = '源码在压缩包内'
    for index, path in enumerate(selected):
        record = inventory.get(path)
        file = affected.get(path)
        entry = {'depotFile': path, 'rev': record.get('rev') if record else None,
                 'type': (record or file or {}).get('type'), 'snapshot_provenance': '版本确定（报告行）',
                 'diagnostic_line_match': '未核对', 'content': None}
        content, merged, merge_inputs = None, False, []
        estimates = [adapter.file_size(path, revision)] if record else []
        if file and file.get('fileSize') is not None:
            estimates.append(int(file['fileSize']))
        if any(size is not None and (size > config.raw['analyzer']['snapshot_max_file_bytes'] or total + size > config.raw['analyzer']['snapshot_max_total_bytes']) for size in estimates):
            entry.update(unavailable_reason='超过大小上限', snapshot_provenance='尚未取得内容', edits_eligible=False)
            result.append(entry)
            diagnostic_only |= path == primary
            continue
        provenance = '请求 base（shelve 包同步方式待确认）' if shelved else '版本确定（报告行）'
        if shelved and not base:
            metadata = log_metadata or {}
            upper = metadata.get('Last-Modified') or metadata.get('first_failure_observed_at')
            if upper:
                try:
                    end = parsedate_to_datetime(upper) if ',' in upper else datetime.fromisoformat(upper.replace('Z', '+00:00'))
                    offset = re.search(r'[+-][0-9]{4}', info['serverDate'])
                    if not offset:
                        raise FlowError(5, 'p4_server_timezone_missing')
                    server_tz = datetime.strptime(offset[0], '%z').tzinfo
                    end = end.replace(tzinfo=server_tz) if end.tzinfo is None else end.astimezone(server_tz)
                    end += timedelta(seconds=config.raw['snapshot']['clock_margin_s'])
                    version = '@' + end.strftime('%Y/%m/%d:%H:%M:%S')
                    latter = adapter.files(path, version)
                    same = latter['category'] == 'ok' and record and latter['records'][0]['rev'] == record['rev']
                    provenance = '区间内一致' if same else '版本不确定'
                    entry['candidate_interval'] = [revision, version]
                    entry['candidate_revisions'] = [record.get('rev') if record else None,
                        latter['records'][0].get('rev') if latter['category'] == 'ok' else None]
                except (ValueError, TypeError):
                    provenance = '版本不确定'
            else:
                provenance = '版本不确定'
        if history_lost:
            provenance = '历史输入不可还原'
        if file:
            if history_lost:
                provenance = '历史输入不可还原'
            elif cross:
                provenance = '跨分支 shelve，来源无法核实'
            elif not base:
                provenance = 'shelve 基础版本无法比对'
            else:
                action = file['action']
                current_rev = int(record['rev']) if record else None
                base_rev = int(file['rev'])
                equal = current_rev == base_rev
                if action in {'add', 'move/add'}:
                    equal = record is None
                if action.startswith('move/'):
                    partner = file.get('movedFile')
                    other = own.get(partner)
                    old = file if action == 'move/delete' else other
                    new = file if action == 'move/add' else other
                    equal = bool(old and new and old['action'] == 'move/delete' and new['action'] == 'move/add'
                        and old['depotFile'] in inventory and int(inventory[old['depotFile']]['rev']) == int(old['rev'])
                        and new['depotFile'] not in inventory)
                if equal:
                    provenance = '原样叠加'
                    if action in {'delete', 'move/delete'}:
                        entry['deleted'] = True
                    else:
                        raw = adapter.print_file(file['depotFile'], '@=' + scl)
                        if hashlib.md5(raw).hexdigest().casefold() != file['digest'].casefold():
                            raise FlowError(5, 'shelve_print_digest_mismatch')
                        content = adapter.print_file(file['depotFile'], '@=' + scl, keywords=True)
                elif action == 'edit' and current_rev is not None and base_rev < current_rev and file['type'].split('+')[0] in {'text', 'unicode', 'utf8', 'utf16'}:
                    current = adapter.print_file(path, revision)
                    ancestor_size = adapter.file_size(path, '#' + str(base_rev))
                    if ancestor_size is None or ancestor_size > config.raw['analyzer']['snapshot_max_file_bytes']:
                        raise FlowError(5, 'merge_input_size_limit')
                    ancestor = adapter.print_file(path, '#' + str(base_rev))
                    raw = adapter.print_file(file['depotFile'], '@=' + scl)
                    if hashlib.md5(raw).hexdigest().casefold() != file['digest'].casefold():
                        raise FlowError(5, 'shelve_print_digest_mismatch')
                    if total + len(current) + len(ancestor) + len(raw) > config.raw['analyzer']['snapshot_max_total_bytes']:
                        combined = {'kind': '超过大小上限', 'content': None, 'inputs': []}
                        entry['unavailable_reason'] = '超过大小上限'
                    else:
                        combined = merge(config, folder + '/merge-' + str(index), current, ancestor, raw)
                        total += sum(i['size'] for i in combined['inputs'])
                    merge_inputs = combined['inputs']
                    content, merged = combined['content'], combined['kind'] == '无冲突'
                    provenance = '已合并' if merged else '合并失败'
                    entry.update(merge_result=combined['kind'], keywords='关键字未展开', merge_inputs=merge_inputs)
                else:
                    provenance = 'shelve 基础版本超前' if action == 'edit' and current_rev is not None and base_rev > current_rev else '合并失败'
        if content is None and record and not entry.get('deleted') and not entry.get('unavailable_reason'):
            content = adapter.print_file(path, revision, keywords=True)
        entry['snapshot_provenance'] = provenance
        if file and provenance != '原样叠加':
            message = notice(build_id, package['key']['name'], path, scl, file['rev'], entry['rev'], entry.get('merge_result', provenance))
            identity = digest(json_bytes({'build': build_id, 'package': package['key'], 'path': path,
                'inputs': [i['sha256'] for i in merge_inputs] or [desc.get('digest'), digest(content or b'')]}))
            notices.append({'reason': 'snapshot_notice', 'basis_version': identity, 'hint': True, 'message': message})
            if identity not in notice_seen:
                print(message, file=sys.stderr)
        if content is not None:
            entry['sha256'] = digest(content)
            entry['size'] = len(content)
            if entry['type'] and entry['type'].split('+')[0] == 'symlink':
                entry['symlink_target'] = content.decode('utf-8', errors='replace')
                entry['unavailable_reason'] = 'symlink 仅记目标'
            elif len(content) > config.raw['analyzer']['snapshot_max_file_bytes'] or total+len(content) > config.raw['analyzer']['snapshot_max_total_bytes']:
                entry['unavailable_reason'] = '超过大小上限'
            else:
                entry['content'] = atomic_write(config.data_root, folder + '/files/' + str(index), content)
                total += len(content)
                matches = [compare_source(content, d['diagnostic'], merged=merged) for d in locations if d['depotFile']==path]
                entry['diagnostic_line_match'] = ('不一致' if '不一致' in matches else '无法核对' if '无法核对' in matches
                    else '源码行一致' if '源码行一致' in matches else '未核对')
        if path == primary and (not entry['content'] or provenance not in RELIABLE or entry['diagnostic_line_match'] in {'不一致', '无法核对'}):
            diagnostic_only = True
        entry['edits_eligible'] = bool(entry['content'] and provenance in RELIABLE)
        result.append(entry)
    if shelved and adapter.describe(scl) != desc:
        raise FlowError(5, 'shelve_changed_during_snapshot')
    remaining = adapter.login_status(require_minimum=False)
    if remaining < 2 * (datetime.now(timezone.utc)-started).total_seconds():
        notices.append({'reason': 'p4_ticket_low_after_snapshot', 'basis_version': digest(json_bytes(package)), 'hint': True})
    return {'mode': '仅诊断' if diagnostic_only else '可分析', 'files': result, 'locations': locations,
            'package': package['key'], 'notices': notices, 'cross_package_files': foreign,
            'shelve_digest': (desc or {}).get('digest'), 'cross_branch': bool(cross), 'historical_input_unrecoverable': history_lost,
            'task_notice_interface': notices, 'round_report_rows': [n.get('message') for n in notices],
            'known_effect': '读取 shelve 会更新 shelveAccess', 'p4_audit': adapter.audit}
