"""Independent prototype line parser and row-based coverage projection."""
from collections import Counter
from .errors import FlowError


def baseline_revision(line):
    """Parse the prototype's line format independently of the report parser."""
    value = line.strip()
    shelved = value.endswith("(shelve)")
    if shelved:
        value = value[:-len("(shelve)")].rstrip()
    path, separator, revision = value.rpartition("@")
    if not separator or not path.strip() or not revision.isascii() or not revision.isdecimal():
        raise FlowError(2, "invalid_baseline_revision")
    return path.strip(), revision, shelved


def apply_rows_coverage(report, rows):
    if rows is None:
        return report
    actual = Counter((r['path'], r['cl'], r['shelve']) for r in report['input_rows'])
    expected = Counter(rows)
    missing, extra = list((expected - actual).elements()), list((actual - expected).elements())
    report.update(package_coverage='不一致' if missing or extra else '一致',
                  missing_packages=missing, extra_packages=extra)
    if missing or extra:
        report['result_state'] = '未知'
        report['issues'].append('package_set_mismatch')
    return report

