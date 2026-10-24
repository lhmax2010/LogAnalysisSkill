"""Independent prototype line parser and pure coverage projection."""
from collections import Counter
from copy import deepcopy
import posixpath
from .errors import FlowError

COVERAGE_BASES = frozenset({'none', 'manual_file', 'request', 'previous_report'})
COVERAGE_STATES = frozenset({'一致', '不一致', '未核', '人工接受'})


def normalize_path(path):
    return posixpath.normpath(path.strip())


def baseline_revision(line):
    value = line.strip()
    shelved = value.endswith('(shelve)')
    if shelved:
        value = value[:-len('(shelve)')].rstrip()
    path, separator, revision = value.rpartition('@')
    if not separator or not path.strip() or not revision.isascii() or not revision.isdecimal():
        raise FlowError(2, 'invalid_baseline_revision')
    return normalize_path(path), revision, shelved


def apply_rows_coverage(report, rows, basis=None):
    result = deepcopy(report)
    basis = basis or ('manual_file' if rows is not None else 'none')
    if basis not in COVERAGE_BASES:
        raise FlowError(2, 'invalid_coverage_basis')
    result['issues'] = sorted(set(result.get('issues', [])) - {'package_set_mismatch', 'expected_package_set_missing'})
    result.update(coverage_basis=basis, package_coverage='未核', missing_packages=[], extra_packages=[])
    if rows is None or not result.get('settled') or basis == 'none':
        return result
    try:
        expected = Counter((normalize_path(path), cl, shelve) for path, cl, shelve in rows)
        if any(not path or not isinstance(cl, str) or not cl.isdecimal() or type(shelve) is not bool
               for path, cl, shelve in expected):
            raise ValueError()
    except (TypeError, ValueError, AttributeError):
        raise FlowError(2, 'invalid_expected_package_set') from None
    actual = Counter((normalize_path(r['path']), r['cl'], r['shelve']) for r in result.get('input_rows', []))
    missing, extra = sorted((expected - actual).elements()), sorted((actual - expected).elements())
    result.update(package_coverage='不一致' if missing or extra else '一致',
                  missing_packages=missing[:20], extra_packages=extra[:20],
                  missing_count=len(missing), extra_count=len(extra))
    if missing or extra:
        result['issues'] = sorted(result['issues'] + ['package_set_mismatch'])
    return result
