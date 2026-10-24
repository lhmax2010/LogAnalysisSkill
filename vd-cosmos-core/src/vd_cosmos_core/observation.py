"""Shared saved/HTTP state projection; no I/O or authorization."""
from collections import Counter
import re

from .report import Document, normalize


def detail_state(data, status_source):
    result = {"state": "未知", "trust": "unknown", "basis": "first_build_status_title", "subresult": None}
    if not status_source:
        return result
    for node in Document(data.decode('utf-8')).nodes:
        title = normalize(node.attrs.get('title') or '')
        if not re.fullmatch(r'Build is .+', title, re.I):
            continue
        match = re.fullmatch(status_source['status_title_regex'], title, re.I)
        word = normalize(match[1]).casefold() if match and match[1] else None
        result.update(title=node.attrs['title'], source_line=node.line, element_order=node.order, subresult=word)
        for field, state in [('terminal_words', '已结束'), ('running_words', '运行'), ('queued_words', '排队')]:
            if word in {normalize(w).casefold() for w in status_source[field]}:
                result.update(state=state, trust='configured_detail_title')
                break
        break
    return result


def report_todos(arch, report):
    todos = []
    state = report.get('report_state')
    if state == '对账失败':
        checks = report.get('reconciliation_checks', [])
        rows = report.get('source_rows', [])
        counts = Counter(tuple(r['key'].values()) for r in rows)
        global_error = any(c in checks for c in ('summary_total_mismatch', 'architecture_mismatch'))
        selected = [r for r in rows if global_error or 'count_mismatch:' + r['category'] in checks
                    or (counts[tuple(r['key'].values())] > 1 and
                        any(c in checks for c in ('duplicate_package_key', 'category_overlap')))]
        todos.append({'arch': arch, 'reason': 'reconciliation_failed', 'checks': checks, 'rows': selected[:20]})
    if state == '结构未知':
        todos.append({'arch': arch, 'reason': 'unknown_report_structure', 'issues': report.get('issues', [])})
    if report.get('package_coverage') == '不一致':
        todos.append({'arch': arch, 'reason': 'package_coverage_mismatch',
                      'missing': report.get('missing_packages', [])[:20], 'extra': report.get('extra_packages', [])[:20]})
    if 'other_expansion_message_format' in report.get('issues', []):
        todos.append({'arch': arch, 'reason': 'other_expansion_message_format'})
    if report.get('error') == 'credential_pattern_blocked':
        todos.append({'arch': arch, 'reason': 'report_credential_pattern_blocked'})
    return todos


def summarize(build_ref, cosmos, reports, execution, *, backend, detail_failed=False):
    arches = cosmos['archs']
    failures = detail_failed or any(r.get('observation_failed') for r in reports.values())
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
    if all(all(r.get('headers', {}).get(k) for k in keys) for r in reports.values()):
        consistency = '一致' if all(len({r['headers'][k] for r in reports.values()}) == 1 for k in keys) else '不一致'
    coverage_values = [r.get('package_coverage', '未核') for r in reports.values()]
    coverage = '不一致' if '不一致' in coverage_values else '未核' if '未核' in coverage_values else '一致'
    result = '未知'
    if complete and not failures and consistency == '一致' and coverage != '不一致':
        result = ('部分' if set(arches) < set(cosmos['regular_archs']) else
                  '失败' if any(r['result_state'] == '失败' for r in reports.values()) else '成功')
    todos = [todo for arch, report in reports.items() for todo in report_todos(arch, report)]
    if consistency == '不一致':
        todos.append({'reason': 'header_inconsistent'})
    return {'schema_version': 1, 'backend': backend, 'build_ref': build_ref.to_dict(),
            'execution_state': None if failures else execution['state'],
            'execution_evidence': None if failures else execution,
            'report_state': state, 'result_state': result, 'header_consistency': consistency,
            'package_coverage': coverage,
            'terminal_inference': '终态推定（依据：报告完整）' if complete and execution['state'] == '未知' else None,
            'terminal_prerequisite_met': bool(complete and consistency == '一致' and coverage == '一致'
                and not failures and execution['state'] == '已结束' and build_ref.execution_kind == 'cosmos'),
            'reports': reports, 'todos': todos, 'observation_failed': bool(failures),
            'observed_at': max((r.get('observed_at', '') for r in reports.values()), default=''),
            'exit_code': 5 if failures else 0}
