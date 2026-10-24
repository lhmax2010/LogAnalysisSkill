"""Shared state projection and detail interpretation; no authorization."""
from collections import Counter
import re
from .report import Document, normalize
from .versions import PARSER_VERSION


def detail_state(data, status_source, build_id=None):
    result = {'state': '未知', 'trust': 'unknown', 'basis': 'title_not_matched',
              'subresult': None, 'rule_version': PARSER_VERSION, 'candidates': [], 'identity_match': False}
    if not status_source:
        return result
    document = Document(data.decode('utf-8'))
    if build_id is not None:
        pattern = status_source.get('identity_regex', r'(?<![0-9]){build_id}(?![0-9])').format(build_id=re.escape(build_id))
        if not re.search(pattern, document.root.text()):
            return {**result, 'basis': 'detail_fetch_failed', 'failure': 'identity_mismatch'}
    result['identity_match'] = build_id is not None
    selected = None
    for node in document.nodes:
        title = normalize(node.attrs.get('title') or '')
        if not re.fullmatch(r'Build is .+', title, re.I):
            continue
        match = re.fullmatch(status_source['status_title_regex'], title, re.I)
        word = normalize(match[1]).casefold() if match and match[1] else None
        if len(result['candidates']) < 20:
            result['candidates'].append({'element_order': node.order, 'source_line': node.line, 'word': word})
        if selected is None:
            selected = (node, word)
    if selected:
        node, word = selected
        result.update(title=node.attrs['title'], source_line=node.line, element_order=node.order, subresult=word,
                      selected={'tag': node.tag, 'class': node.attrs.get('class'), 'id': node.attrs.get('id')},
                      selection_reason='first_build_status_title')
        for field, state in [('terminal_words', '已结束'), ('running_words', '运行'), ('queued_words', '排队')]:
            if word in {normalize(w).casefold() for w in status_source[field]}:
                result.update(state=state, trust='configured_detail_title', basis='first_build_status_title')
                break
    return result


def report_todos(arch, report):
    if not report.get('settled'):
        return []
    todos = []
    version = report.get('evidence', {}).get('sha256')
    state = report.get('report_state')
    if state == '对账失败':
        checks = sorted(report.get('reconciliation_checks', []))
        rows = report.get('source_rows', [])
        counts = Counter(tuple(r['key'][k] for k in ('arch', 'name', 'path')) for r in rows)
        global_error = any(c in checks for c in ('summary_total_mismatch', 'architecture_mismatch', 'missing_header_settled', 'missing_summary_settled'))
        selected = [r for r in rows if global_error or 'count_mismatch:' + r['category'] in checks
                    or counts[tuple(r['key'][k] for k in ('arch', 'name', 'path'))] > 1]
        todos.append({'reason': 'reconciliation_failed', 'checks': checks, 'rows': sorted(selected, key=lambda r: r['source_line'])[:20]})
    if state == '结构未知':
        todos.append({'reason': 'unknown_report_structure', 'issues': sorted(report.get('issues', []))})
    if report.get('package_coverage') == '不一致':
        todos.append({'reason': 'package_coverage_mismatch', 'missing': sorted(report.get('missing_packages', []))[:20],
                      'extra': sorted(report.get('extra_packages', []))[:20]})
    if 'other_expansion_message_format' in report.get('issues', []):
        todos.append({'reason': 'other_expansion_message_format'})
    return [dict(todo, arch=arch, basis_version=version) for todo in todos]


def stopped(observation):
    return (observation.get('report_state') in {'对账失败', '结构未知'}
            or observation.get('header_consistency') == '不一致'
            or any(r.get('coverage_basis') in {'manual_file', 'request'} and r.get('package_coverage') == '不一致'
                   for r in observation.get('reports', {}).values()))


def summarize(build_ref, cosmos, reports, execution, *, backend, detail_failed=False):
    arches = cosmos['archs']
    failures = any(r.get('observation_failed') for r in reports.values())
    values = [reports[a].get('report_state') for a in arches]
    complete = all(v == '完整' for v in values)
    if failures:
        state = None
    elif '结构未知' in values:
        state = '结构未知'
    elif '对账失败' in values:
        state = '对账失败'
    elif all(v == '未发布' for v in values):
        state = '未发布'
    elif all(v == '未知' for v in values):
        state = '未知'
    else:
        state = '完整' if complete else '部分'
    keys = cosmos['header_must_match']
    consistency = '未核'
    if all(r.get('settled') and all(r.get('headers', {}).get(k) for k in keys) for r in reports.values()):
        consistency = '一致' if all(len({r['headers'][k] for r in reports.values()}) == 1 for k in keys) else '不一致'
    coverage_values = [r.get('package_coverage', '未核') for r in reports.values()]
    coverage = '不一致' if '不一致' in coverage_values else '未核' if '未核' in coverage_values else '人工接受' if '人工接受' in coverage_values else '一致'
    result = '未知'
    if complete and not failures and consistency == '一致':
        result = ('部分' if set(arches) < set(cosmos['regular_archs']) else
                  '失败' if any(r['result_state'] == '失败' for r in reports.values()) else '成功')
    todos = [todo for arch, report in reports.items() for todo in report_todos(arch, report)]
    if consistency == '不一致':
        from .files import digest, json_bytes
        todos.append({'reason': 'header_inconsistent', 'basis_version': digest(json_bytes({a: r.get('evidence', {}).get('sha256') for a, r in reports.items()}))})
    gate_coverage = all(r.get('package_coverage') == '人工接受' or
        (r.get('coverage_basis') == 'request' and r.get('package_coverage') == '一致') for r in reports.values())
    data = {'schema_version': 2, 'backend': backend, 'build_ref': build_ref.to_dict(),
            'execution_state': execution['state'], 'execution_evidence': execution,
            'report_state': state, 'result_state': result, 'header_consistency': consistency,
            'package_coverage': coverage, 'terminal_inference': '终态推定（依据：报告完整）' if complete and execution['state'] == '未知' else None,
            'terminal_prerequisite_met': bool(complete and consistency == '一致' and gate_coverage
                and not failures and execution['state'] == '已结束' and build_ref.execution_kind == 'cosmos'),
            'reports': reports, 'todos': todos, 'observation_failed': bool(failures),
            'observed_at': max((r.get('observed_at', '') for r in reports.values()), default=''),
            'exit_code': 5 if failures else 0}
    if not failures and stopped(data):
        data['exit_code'] = 3
    return data
