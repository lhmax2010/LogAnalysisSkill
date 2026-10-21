"""Parse the registered QuickBuild page shapes from already-redacted HTML only."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlsplit

from ci_triage.qb_config import ARCHITECTURES, BASE_URL, child_configuration_path

BINDING = "REJECTED_QB_BINDING_MISMATCH"
UNRECOGNIZED = "QB_RESULT_UNRECOGNIZED"
STATES = {
    "Successful": "PASS",
    "Failed": "FAIL",
    "Cancelled": "CANCELLED",
    "Timeout": "TIMEOUT",
    "Running": "RUNNING",
    "Waiting": "WAITING",
    "Queued": "QUEUED",
}
TERMINAL = {"PASS", "FAIL", "CANCELLED", "TIMEOUT"}
SNAPSHOT_ROOT = "http://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/"


class ResultCheckError(ValueError):
    def __init__(self, code: str, check: str) -> None:
        super().__init__(code)
        self.code, self.check = code, check


def require(condition: bool, check: str, code: str = BINDING) -> None:
    if not condition:
        raise ResultCheckError(code, check)


@dataclass(eq=False)
class Element:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list[Element | str] = field(default_factory=list)
    parent: Element | None = field(default=None, repr=False)

    def has(self, cls: str) -> bool:
        return cls in self.attrs.get("class", "").split()

    def find(self, tag: str | None = None, *, cls: str | None = None) -> list[Element]:
        found = []
        for child in self.children:
            if isinstance(child, Element):
                if (tag is None or child.tag == tag) and (cls is None or child.has(cls)):
                    found.append(child)
                found.extend(child.find(tag, cls=cls))
        return found

    def text(self) -> str:
        if self.tag == "br":
            return "\n"
        return "".join(c if isinstance(c, str) else c.text() for c in self.children)


class Document(HTMLParser):
    def __init__(self, html: str) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Element("document")
        self.stack = [self.root]
        self.feed(html)
        self.close()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = Element(tag, {k: v or "" for k, v in attrs}, parent=self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in {
            "area",
            "base",
            "br",
            "col",
            "embed",
            "hr",
            "img",
            "input",
            "link",
            "meta",
            "param",
            "source",
            "track",
            "wbr",
        }:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data: str) -> None:
        self.stack[-1].children.append(data)


def one(nodes: list[Element], check: str, code: str = BINDING) -> Element:
    require(len(nodes) == 1, check, code)
    return nodes[0]


def cells(row: Element) -> list[Element]:
    return [n for n in row.children if isinstance(n, Element) and n.tag in {"td", "th"}]


def config_path(doc: Element, expected: str) -> None:
    crumb = one([n for n in doc.find() if n.attrs.get("id") == "breadcrumb"], "breadcrumb")
    segments = [n for n in crumb.children if isinstance(n, Element) and n.tag == "span"]
    require(
        bool(segments) and "/".join(n.text().strip() for n in segments) == expected,
        "breadcrumb_path",
    )
    require(not segments[-1].find("a"), "breadcrumb_current")
    copies = [
        match
        for script in doc.find("script")
        for match in re.findall(
            r"onCopyClipboardLinkDomReady\('[^']*',\s*'([^']*)'\)", script.text()
        )
    ]
    require(copies == [expected], "copy_path")


def summary(doc: Element) -> dict[str, str]:
    section = one(
        [
            n
            for n in doc.find(cls="build-summary")
            if any(h.text().strip() == "Summary" for h in n.find(cls="box-head"))
        ],
        "summary",
        UNRECOGNIZED,
    )
    table = one(section.find("table"), "summary_table", UNRECOGNIZED)
    header = one(table.find("thead"), "summary_header", UNRECOGNIZED)
    names = [n.text().strip() for n in header.find("th")]
    body = one(table.find("tbody"), "summary_body", UNRECOGNIZED)
    row = one(body.find("tr"), "summary_row", UNRECOGNIZED)
    values = [n.text().strip() for n in cells(row)]
    require(
        len(names) == len(values) and len(set(names)) == len(names), "summary_columns", UNRECOGNIZED
    )
    result = dict(zip(names, values, strict=True))
    require("Status" in result, "summary_status", UNRECOGNIZED)
    return result


def recent_builds(html: str, profile: dict[str, Any]) -> list[str]:
    """Registered configuration identity and six-column Recent Builds table."""
    doc = Document(html).root
    title = one(doc.find("title"), "configuration_title").text().strip()
    expected = "QuickBuild - " + profile["configuration_path"]
    require(title == expected or title.startswith(expected + " - "), "configuration_title")
    config_path(doc, profile["configuration_path"])
    headings = [head for head in doc.find(cls="box-head") if any(
        isinstance(child, Element) and child.has("flex-1")
        and child.text().strip() == "Recent Builds" for child in head.children
    )]
    heading = one(headings, "recent_builds_title")
    require(heading.parent is not None, "recent_builds_box")
    assert heading.parent is not None
    table = one(heading.parent.find("table"), "recent_builds_table")
    header = one(table.find("thead"), "recent_builds_header")
    require([n.text().strip() for n in header.find("th")] == [
        "Id", "Version", "Master Node", "Begin Date", "Duration", "Triggered By"
    ], "recent_builds_columns")
    body = one(table.find("tbody"), "recent_builds_body")
    rows = body.find("tr")
    require(len(rows) <= 50, "recent_builds_limit")
    builds: list[str] = []
    for item in rows:
        values = cells(item)
        require(len(values) == 6, "recent_builds_row_columns")
        build = values[0].text().strip()
        require(re.fullmatch(r"\d+", build) is not None, "recent_builds_id")
        links = [match[1] for link in values[1].find("a")
                 if (match := re.fullmatch(r"/build/(\d+)", link.attrs.get("href", "")))]
        require(links == [build], "recent_builds_link")
        require(build not in builds, "recent_builds_duplicate_id")
        builds.append(build)
    return builds


def parent_overview(html: str, path: str, profile: dict[str, Any]) -> dict[str, Any]:
    doc = Document(html).root
    for cls, kind in (
        ("tab-ConfigurationOverview", "overview"),
        ("tab-PipelinePage", "pipeline"),
        ("tab-ChildrenPage", "children"),
    ):
        tab = one(doc.find("li", cls=cls), kind + "_tab")
        link = one(tab.find("a", cls="nav-link"), kind + "_link")
        href = link.attrs.get("href", "")
        resolved = urljoin(BASE_URL + path, href)
        require(resolved == f"{BASE_URL}/{kind}/{profile['overview_id']}", kind + "_url")
        require(not urlsplit(href).query and "?" not in href and "#" not in href, kind + "_query")
    config_path(doc, profile["configuration_path"])
    header = one(doc.find(cls="build-header"), "build_header")
    names = [
        n.text().strip()
        for n in header.find("span")
        if not n.find() and n.text().strip().startswith("TIZEN_")
    ]
    prefix = profile["configuration_path"].removeprefix("root/CI_TIZEN/").replace("/", "_") + "_"
    require(len(names) == 1 and names[0].startswith(prefix), "build_name")
    values = summary(doc)
    sr = values.get("SR_STATUS")
    facts: dict[str, Any] = dict(
        parent_status_text=values["Status"],
        accepted=None if sr is None else re.fullmatch(r"ACCEPTED(\s*\(.*\))?", sr) is not None,
        child_build_id=None,
        child_build_result_text=None,
    )
    headings = [
        n
        for n in doc.find()
        if n.tag in {"h1", "h2", "h3", "h4"}
        and n.text().strip().removeprefix("◆").strip() == "Child Build"
    ]
    if not headings:
        return facts
    title = one(headings, "child_title", UNRECOGNIZED)
    assert title.parent is not None
    siblings = [n for n in title.parent.children if isinstance(n, Element)]
    i = siblings.index(title) + 1
    require(i < len(siblings) and siblings[i].tag == "table", "child_table", UNRECOGNIZED)
    table = siblings[i]
    head = one(table.find("thead"), "child_header", UNRECOGNIZED)
    labels = [n.text().strip() for row in head.find("tr") for n in cells(row)]
    require(
        labels == ["Repository-Architecture", "QB Build URL", "Build Result", "Build Profiling"],
        "child_columns",
        UNRECOGNIZED,
    )
    rows = [row for body in table.find("tbody") for row in body.find("tr") if cells(row)]
    require(len(rows) <= 1, "child_row_count", UNRECOGNIZED)
    if not rows:
        return facts
    columns = cells(rows[0])
    require(len(columns) == 4, "child_cells", UNRECOGNIZED)
    require(columns[0].text().strip() == ARCHITECTURES, "child_arch")
    href = one(columns[1].find("a"), "child_link").attrs.get("href", "")
    match = re.fullmatch(r"https://quickbuild\.tizen\.org/build/(\d+)", href)
    require(match is not None, "child_href")
    assert match is not None
    facts.update(child_build_id=match[1], child_build_result_text=columns[2].text().strip())
    return facts


def variables(html: str) -> dict[str, tuple[str, str]]:
    tables = []
    for table in Document(html).root.find("table"):
        rows = table.find("tr")
        if rows and [n.text().strip() for n in cells(rows[0])] == ["Name", "Display Name", "Value"]:
            tables.append(table)
    table = one(tables, "variables_table")
    result = {}
    for row in table.find("tr")[1:]:
        columns = cells(row)
        require(len(columns) == 3, "variable_columns")
        key, display, value = (n.text().strip() for n in columns)
        require(bool(key) and key not in result, "variable_unique")
        result[key] = (display, value)
    return result


def value(rows: dict[str, tuple[str, str]], key: str, display: str | None = None) -> str:
    require(key in rows, "missing_" + key)
    require(display is None or rows[key][0] == display, "display_" + key)
    return rows[key][1]


def lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def parent_variables(
    html: str, parent: str, request: str, target: str, profile: dict[str, Any]
) -> dict[str, Any]:
    rows = variables(html)
    require(value(rows, "QB_TRIGGER_ID") == parent, "parent_QB_TRIGGER_ID")
    require(
        lines(value(rows, "BUILD_PKG_LIST_MODIFY", "Build Package List")) == [target],
        "parent_target",
    )
    marker = value(rows, "BUILD_NOTES", "BUILD NOTES")
    require(marker == "clang-fix-campaign request=" + request, "request_marker")
    for key in ("BUILD_TYPE", "BUILD_REFERENCE", "PROJECT_BRANCH"):
        require(value(rows, key) == profile["form"][key], "parent_" + key)
    require(value(rows, "FAIL_FAST", "Immediate Stop With Error") == "yes", "parent_FAIL_FAST")
    require(value(rows, "CHILD_CONFIGURATIONS") == ARCHITECTURES, "parent_arch")
    return dict(
        request_marker_echo=marker,
        params_echo={
            key: value(rows, key)
            for key in (
                "BUILD_TYPE",
                "BUILD_REFERENCE",
                "SNAPSHOT_NUM",
                "PROJECT_BRANCH",
                "FAIL_FAST",
            )
        },
        pkg_list_echo={
            k: v for k, (_, v) in rows.items() if "@" in v and k != "BUILD_PKG_LIST_MODIFY"
        },
    )


def child_overview(html: str, profile: dict[str, Any], build_result: str) -> dict[str, Any]:
    doc = Document(html).root
    expected = child_configuration_path(profile["configuration_path"])
    config_path(doc, expected)
    status = summary(doc)["Status"]
    normalized = STATES.get(status)
    if normalized is None and re.fullmatch(r"Not Finished \(.*\)", build_result):
        normalized = "RUNNING"
    require(normalized is not None, "status_text", UNRECOGNIZED)
    errors = doc.find(cls="build-errors")
    error = None
    if len(errors) == 1:
        bodies = errors[0].find(cls="box-body")
        if len(bodies) == 1:
            error = bodies[0].text().strip()
    return dict(
        status=normalized,
        child_status_text=status,
        child_configuration_path=expected,
        child_error_message=error,
    )


def child_variables(html: str, parent: str, child: str, target: str) -> dict[str, Any]:
    rows = variables(html)
    for key, wanted in (
        ("TRIGGER_ID", parent),
        ("QB_TRIGGER_ID", child),
        ("FAIL_FAST", "yes"),
        ("REPO_ARCH", ARCHITECTURES),
        ("CHILD_CONFIGURATIONS", ARCHITECTURES),
    ):
        require(value(rows, key) == wanted, "child_" + key)
    targets = lines(value(rows, "BUILD_PKG_LIST"))
    project = target.split("@", 1)[0] + "@"
    require(
        targets.count(target) == 1 and [v for v in targets if v.startswith(project)] == [target],
        "child_target",
    )
    return dict(
        sbs_target_echo=target,
        per_arch_status=None,
        child_params_echo={
            "BUILD_REFERENCE": value(rows, "BUILD_REFERENCE"),
            "SNAPSHOT_NUM_URL": rows.get("SNAPSHOT_NUM_URL", ("", ""))[1],
        },
        each_status=value(rows, "EACH_GBS_BUILD_STATUS"),
    )


def snapshot_kind(url: str, frozen: str) -> tuple[str, str]:
    try:
        parsed = urlsplit(url)
    except ValueError:
        return "unsupported", url
    if not (
        url.startswith(SNAPSHOT_ROOT)
        and parsed.scheme == "http"
        and parsed.netloc == "download.tizen.org"
        and "?" not in url
        and "#" not in url
    ):
        return "unsupported", url
    name = url[len(SNAPSHOT_ROOT) :]
    if not name or "/" in name:
        return "unsupported", url
    if name == frozen:
        return "same", name
    prefix, separator, _ = frozen.rpartition("_")
    other, sep, date = name.rpartition("_")
    if separator and sep and prefix == other and re.fullmatch(r"\d{8}\.\d{6}", date):
        return "drift", name
    return "unsupported", url


def failed_steps(html: str) -> str | None:
    doc = Document(html).root
    failed = [n for n in doc.find(cls="step") if n.has("failed")]
    leaves = [n for n in failed if not any(c.has("failed") for c in n.find(cls="step"))]
    paths = []
    for leaf in leaves:
        path = []
        node: Element | None = leaf
        while node is not None:
            if node.has("step"):
                heads = [c for c in node.children if isinstance(c, Element) and c.has("step-head")]
                if len(heads) != 1 or len(heads[0].find(cls="step-name")) != 1:
                    return None
                path.append(heads[0].find(cls="step-name")[0].text().strip())
            node = node.parent
        if not all(path):
            return None
        paths.append(" > ".join(reversed(path)))
    return "\n".join(paths) if paths else None
