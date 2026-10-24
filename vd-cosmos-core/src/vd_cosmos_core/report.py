"""Pure HTML parsing. This module never opens files or fetches URLs."""
from collections import Counter
from dataclasses import dataclass, field
from html.parser import HTMLParser
import re
from urllib.parse import unquote, urljoin, urlsplit

from .errors import FlowError
from .models import Package, PackageKey


def normalize(value):
    return " ".join(value.split())


def label(value):
    return normalize(value).casefold().rstrip(":")


@dataclass
class Node:
    tag: str
    attrs: dict
    line: int
    order: int
    children: list = field(default_factory=list)

    def text(self):
        result = "".join(x.text() if isinstance(x, Node) else x for x in self.children)
        if self.tag in {"br", "tr", "p", "div", "h1", "h2", "h3", "h4"}:
            result += "\n"
        elif self.tag in {"td", "th"}:
            result += "\t"
        return result

    def descendants(self, tags):
        for child in self.children:
            if isinstance(child, Node):
                if child.tag in tags:
                    yield child
                yield from child.descendants(tags)


class Document(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = Node("root", {}, 1, 0)
        self.stack = [self.root]
        self.nodes = []
        self.feed(html)
        self.close()

    def handle_starttag(self, tag, attrs):
        # HTML permits omitted </p>. A new paragraph/block ends the preceding
        # paragraph; otherwise the real report's three snapshot fields nest.
        if tag in {"p", "div", "table", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.handle_endtag("p")
        node = Node(tag, dict(attrs), self.getpos()[0], len(self.nodes) + 1)
        self.nodes.append(node)
        self.stack[-1].children.append(node)
        if tag not in {"br", "hr", "img", "input", "meta", "link", "source", "wbr"}:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if self.stack[-1].tag == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        if self.stack[-1].tag not in {"script", "style"}:
            self.stack[-1].children.append(data)


HEADERS = {"profile": "profile", "arch": "arch", "start time": "start_time",
           "gbs version": "gbs_version", "base snapshot": "base",
           "product snapshot": "product", "build conf": "build_conf",
           "build.conf": "build_conf"}
COUNTS = {"total": "total", "succeeded": "succeeded", "export error": "export_error",
          "expansion error": "expansion_error", "build error": "build_error"}


def cells(row):
    return [x for x in row.children if isinstance(x, Node) and x.tag in {"td", "th"}]


def table_rows(table):
    return list(table.descendants({"tr"}))


def table_titles(table, document):
    titles = [x.text().rstrip("\n\t") for x in table.descendants({"caption"})]
    rows = table_rows(table)
    if rows and len(cells(rows[0])) == 1:
        titles.append(rows[0].text().rstrip("\n\t"))
    previous = [n for n in document.nodes if n.order < table.order
                and n.tag in {"h1", "h2", "h3", "h4", "h5", "h6", "b", "strong"}]
    if previous:
        titles.append(previous[-1].text().rstrip("\n\t"))
    return titles


def parse_path(value):
    match = re.fullmatch(r"(.+?)@(\d+)(?:\s*\(\s*shelve\s*\))?", value.strip(), re.I)
    if not match:
        raise ValueError("invalid package revision")
    return match[1].strip(), match[2], bool(re.search(r"\(\s*shelve\s*\)$", value, re.I))


def missing_items(cell):
    # Only HTML <br> separates messages. Source-code line wrapping is whitespace
    # within a message and must not create new signatures.
    lines = [""]

    def visit(node):
        for child in node.children:
            if isinstance(child, Node):
                if child.tag == "br":
                    lines.append("")
                else:
                    visit(child)
            else:
                lines[-1] += child

    visit(cell)
    items, other = [], []
    for line in map(normalize, lines):
        match = re.fullmatch(r"\s*nothing\s+provides\s+(.+?)(?:\s+needed\s+by\s+.+)?\s*", line, re.I)
        if match:
            value = normalize(match[1])
            if value not in items:
                items.append(value)
        elif line.strip():
            value = normalize(line)
            if value not in items:
                items.append(value)
            # Retain occurrences for the acceptance report's message count.
            other.append(value)
    if not items:
        raise ValueError("missing dependency list")
    return items, other


def count_label(value):
    return re.sub(r"\s+packages$", "", label(value))


def _header_and_counts(document, summary_prefix):
    headers, counts = {}, {}
    malformed = False
    for row in document.root.descendants({"tr"}):
        values = [normalize(c.text()) for c in cells(row)]
        if len(values) == 2 and label(values[0]) in HEADERS:
            key = HEADERS[label(values[0])]
            if key in headers and headers[key] != values[1]:
                malformed = True
            headers[key] = values[1]
    for line in document.root.text().splitlines():
        match = re.match(r"^\s*([^:\t]+):\s*(.+?)\s*$", line)
        if match and label(match[1]) in HEADERS:
            key = HEADERS[label(match[1])]
            if key in headers and headers[key] != match[2]:
                malformed = True
            headers[key] = match[2]
    for table in document.root.descendants({"table"}):
        rows = table_rows(table)
        candidates = table_titles(table, document)
        if rows:
            candidates += [c.text() for c in cells(rows[0])]
        if not any(label(value).startswith(label(summary_prefix)) for value in candidates):
            continue
        for index, row in enumerate(rows):
            values = [normalize(c.text()) for c in cells(row)]
            candidates = []
            if len(values) == 2 and count_label(values[0]) in COUNTS:
                candidates.append((COUNTS[count_label(values[0])], values[1]))
            if len(values) == 5 and set(map(count_label, values)) == set(COUNTS) and index + 1 < len(rows):
                numbers = [normalize(c.text()) for c in cells(rows[index + 1])]
                if len(numbers) == 5:
                    candidates.extend((COUNTS[count_label(k)], v) for k, v in zip(values, numbers))
            for key, raw in candidates:
                if not re.fullmatch(r"[0-9]+", raw):
                    malformed = True
                elif key in counts:
                    malformed = True
                else:
                    counts[key] = int(raw)
    return headers, counts, malformed


def parse_report(html, arch, cosmos, expected_packages, *, stable, source_url=""):
    """Return all rows, including duplicates; never deduplicate before reconciliation."""
    try:
        document = Document(html)
    except (ValueError, RecursionError):
        raise FlowError(5, "report_parse_failed") from None
    marker = label(cosmos["report_markers"]["report"])
    if marker not in label(document.root.text()):
        raise FlowError(5, "not_a_report")
    headers, counts, malformed = _header_and_counts(document, cosmos["report_markers"]["summary"])
    packages, inputs, issues, titles, warnings = [], [], [], {}, []
    prefixes = {"build": cosmos["detail_table_title_prefix"],
                "expansion": cosmos["report_markers"]["expansion"],
                "export": cosmos["report_markers"]["export"]}
    matched = set()
    for table in document.root.descendants({"table"}):
        names = table_titles(table, document)
        kind = next((key for key, prefix in prefixes.items()
                     if any(label(name).startswith(label(prefix)) for name in names)), None)
        if kind is None:
            continue
        if kind in matched:
            malformed = True
            issues.append("duplicate_detail_table")
        matched.add(kind)
        titles[kind] = next(name for name in names if label(name).startswith(label(prefixes[kind])))
        for row in table_rows(table):
            cols = cells(row)
            if not cols or all(c.tag == "th" for c in cols):
                continue
            if len(cols) == 1 and any(label(cols[0].text()).startswith(label(p)) for p in prefixes.values()):
                continue
            if len(cols) >= 2 and label(cols[0].text()) in {"package", "package name", "name"} and label(cols[1].text()) in {"path", "source", "p4 path", "package path"}:
                continue
            if len(cols) != 3:
                malformed = True
                issues.append("malformed_detail_row")
                continue
            name, raw_path = normalize(cols[0].text()), normalize(cols[1].text())
            raw_status = normalize(cols[2].text())
            try:
                path, cl, shelve = parse_path(raw_path)
                if not name:
                    raise ValueError()
                missing, other = missing_items(cols[2]) if kind == "expansion" else ([], [])
            except ValueError:
                malformed = True
                issues.append("unparsed_detail_row")
                continue
            links = [a.attrs.get("href", "") for a in cols[2].descendants({"a"})]
            log_url = urljoin(source_url, links[0]) if links else None
            category = "expansion_error" if kind == "expansion" else "export_error"
            if kind == "build":
                category = {"Succeeded": "succeeded", "Failed": "build_error"}.get(raw_status, "unknown")
                if category == "unknown":
                    malformed = True
                    issues.append("unknown_build_status")
                if links and ((raw_status == "Succeeded" and "/fail/" in links[0]) or
                              (raw_status == "Failed" and "/success/" in links[0])):
                    malformed = True
                    issues.append("status_link_conflict")
            version = None
            if log_url:
                parent = unquote(urlsplit(log_url).path).split("/")[-2:-1]
                if parent and parent[0].startswith(name + "-"):
                    version = parent[0][len(name) + 1:]
            package = Package(PackageKey(arch, name, path), version, cl, shelve,
                              category, log_url, missing, row.line, raw_path, raw_status, other)
            if other:
                warnings.append("other_expansion_message_format")
            packages.append(package.to_dict())
            inputs.append({"key": package.key.to_dict(), "path": path, "cl": cl,
                           "shelve": shelve, "raw": raw_path, "source_line": row.line})
    required = {"profile", "arch", "start_time", "gbs_version", "base", "product", "build_conf"}
    if not required <= headers.keys() or any(not headers.get(k) for k in required):
        issues.append("missing_report_header")
    if headers.get("arch") != arch:
        issues.append("architecture_mismatch")
    if set(counts) != set(COUNTS.values()):
        issues.append("missing_summary")
    else:
        if counts["total"] != sum(v for k, v in counts.items() if k != "total"):
            issues.append("summary_total_mismatch")
        actual = Counter(p["category"] for p in packages)
        for category in set(COUNTS.values()) - {"total"}:
            if counts[category] != actual[category]:
                issues.append("count_mismatch:" + category)
        if counts["export_error"] and "export" not in matched:
            malformed = True
            issues.append("unknown_export_structure")
    keys = [(p["key"]["arch"], p["key"]["name"], p["key"]["path"]) for p in packages]
    unique = len(keys) == len(set(keys))
    categories = {}
    for key, package in zip(keys, packages):
        categories.setdefault(key, set()).add(package["category"])
    disjoint = all(len(value) == 1 for value in categories.values())
    if not unique:
        issues.append("duplicate_package_key")
    if not disjoint:
        issues.append("category_overlap")
    missing, extra = [], []
    if expected_packages is None:
        issues.append("expected_package_set_missing")
    else:
        expected = [(p.get("arch", arch), p["name"], p["path"]) for p in expected_packages]
        if len(set(expected)) != len(expected) or any(k[0] != arch for k in expected):
            issues.append("invalid_expected_package_set")
        missing, extra = sorted(set(expected) - set(keys)), sorted(set(keys) - set(expected))
        if missing or extra:
            issues.append("package_set_mismatch")
    if not stable:
        issues.append("not_stable")
    state = "结构未知" if malformed else ("部分" if issues else "完整")
    result = "未知"
    if state == "完整":
        result = "失败" if any(p["category"] != "succeeded" for p in packages) else "成功"
    return {"arch": arch, "report_state": state, "result_state": result,
            "headers": headers, "counts": counts, "packages": packages, "input_rows": inputs,
            "raw_table_titles": titles, "issues": sorted(set(issues + warnings)),
            "package_keys_unique": unique, "categories_disjoint": disjoint,
            "missing_packages": missing, "extra_packages": extra, "stable": stable}
