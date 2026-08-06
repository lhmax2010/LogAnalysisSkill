#!/usr/bin/env python3
"""Statically audit P4.9 step-0 attribution tables against the source tree.

This tool parses source text and Python ASTs only. It never imports or executes
the modules being audited. The hard-coded inventory transcribes the final v1.1
correction section of p49-step0-design-v1.0-draft.md together with the tables it
amends.
"""

from __future__ import annotations

import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SymbolSpec:
    name: str
    sections: tuple[str, ...]
    definition: str
    owner: str
    declared_consumers: tuple[str, ...] = ()
    declared_internal: tuple[str, ...] = ()
    format_authority: bool = False
    gbs_surface: bool = False
    quickbuild_surface: bool = False
    status: str = "existing"


WORKSPACE = "ci_triage/verify/workspace.py"
GBS_REPORT = "ci_triage/gbs_report.py"
QUICKBUILD = "ci_triage/quickbuild.py"


SPECS: tuple[SymbolSpec, ...] = (
    # §2, with the v1.1 additions applied.
    SymbolSpec(
        "SourceFetchResult",
        ("§2",),
        "ci_triage/gerrit.py",
        "shared/types",
        ("ci_triage.report",),
    ),
    SymbolSpec(
        "FailedPackage",
        ("§2",),
        "ci_triage/quickbuild_log.py",
        "shared/types",
        ("ci_triage.orchestrator", "ci_triage.report", "ci_triage.runner"),
    ),
    SymbolSpec(
        "DisposableWorktree",
        ("§2", "§3.2"),
        WORKSPACE,
        "shared",
    ),
    SymbolSpec(
        "WorkspaceViolation",
        ("§2", "§3.2"),
        WORKSPACE,
        "shared",
        ("ci_triage.campaign_repair_step",),
    ),
    SymbolSpec(
        "FailureClassification",
        ("§2",),
        "ci_triage/verify/failure_classify.py",
        "shared",
        ("ci_triage.verify.build_verify",),
    ),
    SymbolSpec(
        "GbsReportPackage",
        ("§2", "§4"),
        GBS_REPORT,
        "shared/types",
        ("ci_triage.runner", "ci_triage.orchestrator"),
        gbs_surface=True,
    ),
    SymbolSpec(
        "GbsReport",
        ("§2", "§4"),
        GBS_REPORT,
        "shared/types",
        gbs_surface=True,
    ),
    # §3.2, with the v1.1 line corrections and S-1 extraction applied.
    SymbolSpec(
        "create_worktree",
        ("§3.2",),
        WORKSPACE,
        "build-verify",
        ("ci_triage.verify.build_verify",),
    ),
    SymbolSpec(
        "check_disk_and_maybe_cleanup",
        ("§3.2",),
        WORKSPACE,
        "build-verify",
        ("ci_triage.verify.build_verify",),
    ),
    SymbolSpec(
        "_copy_repository",
        ("§3.2",),
        WORKSPACE,
        "build-verify",
        declared_internal=("create_worktree",),
    ),
    SymbolSpec(
        "cleanup_worktree",
        ("§3.2",),
        WORKSPACE,
        "shared",
        ("ci_triage.verify.build_verify",),
        ("cleanup_disposable_copy", "check_disk_and_maybe_cleanup"),
    ),
    SymbolSpec(
        "cleanup_disposable_copy",
        ("§3.2",),
        WORKSPACE,
        "shared",
        ("ci_triage.campaign_repair_step",),
    ),
    SymbolSpec(
        "is_protected",
        ("§3.2",),
        WORKSPACE,
        "shared",
        ("ci_triage.campaign_repair_step",),
        ("cleanup_disposable_copy", "check_disk_and_maybe_cleanup"),
    ),
    SymbolSpec(
        "release_worktree_protection",
        ("§3.2",),
        WORKSPACE,
        "shared",
        ("ci_triage.verify.gerrit_submit",),
    ),
    SymbolSpec(
        "mark_worktree_protected",
        ("§3.2",),
        WORKSPACE,
        "shared",
        ("ci_triage.verify.build_verify",),
    ),
    SymbolSpec(
        "_oldest_worktrees",
        ("§3.2",),
        WORKSPACE,
        "shared",
        declared_internal=("check_disk_and_maybe_cleanup",),
    ),
    SymbolSpec(
        "_run_git",
        ("§3.2",),
        WORKSPACE,
        "shared",
        declared_internal=("create_worktree",),
    ),
    SymbolSpec(
        "_verify_cleanup_handle",
        ("§3.2",),
        WORKSPACE,
        "shared",
        declared_internal=("cleanup_worktree", "mark_worktree_protected"),
    ),
    SymbolSpec(
        "_exclude_private_files",
        ("§3.2",),
        WORKSPACE,
        "shared",
        declared_internal=("create_worktree", "mark_worktree_protected"),
    ),
    SymbolSpec(
        "MARKER_FILENAME",
        ("§3.1", "§3.2"),
        WORKSPACE,
        "shared",
        format_authority=True,
    ),
    SymbolSpec(
        "PROTECTED_FILENAME",
        ("§3.1", "§3.2"),
        WORKSPACE,
        "shared",
        format_authority=True,
    ),
    SymbolSpec(
        "_read_marker",
        ("§3.1", "§3.2"),
        WORKSPACE,
        "shared",
        declared_internal=(
            "cleanup_disposable_copy",
            "_verify_cleanup_handle",
            "_oldest_worktrees",
        ),
        format_authority=True,
    ),
    SymbolSpec(
        "write_workdir_marker",
        ("§3.2", "S-1"),
        WORKSPACE,
        "shared",
        declared_internal=("create_worktree",),
        format_authority=True,
        status="to-be-created",
    ),
    # §4 fetch half and its explicitly named quickbuild dependencies.
    SymbolSpec(
        "fetch_gbs_report",
        ("§4",),
        GBS_REPORT,
        "shared",
        ("ci_triage.runner", "ci_triage.orchestrator"),
        gbs_surface=True,
    ),
    SymbolSpec(
        "download_gbs_package_buildlog",
        ("§4",),
        GBS_REPORT,
        "shared",
        ("ci_triage.runner", "ci_triage.orchestrator"),
        gbs_surface=True,
    ),
    SymbolSpec(
        "DEFAULT_ARCHES",
        ("§4",),
        GBS_REPORT,
        "orchestrator",
        ("ci_triage.orchestrator",),
        gbs_surface=True,
    ),
    SymbolSpec(
        "HttpFetcher",
        ("§4",),
        QUICKBUILD,
        "shared",
        ("ci_triage.gbs_report", "ci_triage.sources"),
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "QuickBuildError",
        ("§4",),
        QUICKBUILD,
        "shared",
        (
            "ci_triage.gbs_report",
            "ci_triage.orchestrator",
            "ci_triage.runner",
            "ci_triage.sources",
        ),
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "_raise_if_login_page",
        ("§4",),
        QUICKBUILD,
        "shared",
        ("ci_triage.gbs_report", "ci_triage.sources"),
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "_urllib_fetch",
        ("§4",),
        QUICKBUILD,
        "shared",
        ("ci_triage.gbs_report", "ci_triage.sources"),
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "DEFAULT_COOKIE_PATH",
        ("§4",),
        QUICKBUILD,
        "shared",
        (
            "ci_triage.batch_cli",
            "ci_triage.cli",
            "ci_triage.gbs_report",
            "ci_triage.orchestrator",
            "ci_triage.runner",
            "ci_triage.sources",
        ),
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "DEFAULT_QUICKBUILD_BASE_URL",
        ("§4",),
        QUICKBUILD,
        "shared",
        ("ci_triage.gbs_report", "ci_triage.sources"),
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "load_cookie_jar",
        ("§4", "v1.2-A"),
        QUICKBUILD,
        "shared",
        ("ci_triage.gbs_report", "ci_triage.sources"),
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "DOWNLOAD_LINK_MARKER",
        ("§4", "v1.2-A"),
        QUICKBUILD,
        "shared",
        declared_internal=("find_download_href",),
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "DOWNLOAD_TIZEN_BASE_URL",
        ("§4", "v1.2-A"),
        QUICKBUILD,
        "shared",
        declared_internal=("derive_package_buildlog_url",),
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "HttpResponse",
        ("§4", "v1.2-A"),
        QUICKBUILD,
        "shared",
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "QuickBuildDownload",
        ("§4", "v1.2-A"),
        QUICKBUILD,
        "shared",
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "PackageBuildLog",
        ("§4", "v1.2-A"),
        QUICKBUILD,
        "shared",
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "download_full_log",
        ("§4", "v1.2-A"),
        QUICKBUILD,
        "shared",
        ("ci_triage.orchestrator", "ci_triage.runner"),
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "find_download_href",
        ("§4", "v1.2-A"),
        QUICKBUILD,
        "shared",
        declared_internal=("download_full_log",),
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "derive_package_buildlog_url",
        ("§4", "v1.2-A"),
        QUICKBUILD,
        "shared",
        declared_internal=("download_package_buildlog",),
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "download_package_buildlog",
        ("§4", "v1.2-A"),
        QUICKBUILD,
        "shared",
        ("ci_triage.runner",),
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "normalize_quickbuild_url",
        ("§4", "v1.2-A"),
        QUICKBUILD,
        "shared",
        declared_internal=("_urllib_fetch",),
        quickbuild_surface=True,
    ),
    # §4 parse half. The v1.1 table groups all private helpers here; enumerate
    # them so the completeness guard cannot silently lose a cutting surface.
    SymbolSpec(
        "find_iframe_src",
        ("§4",),
        GBS_REPORT,
        "triage-report",
        declared_internal=("fetch_gbs_report",),
        gbs_surface=True,
    ),
    SymbolSpec(
        "parse_gbs_report_packages",
        ("§4",),
        GBS_REPORT,
        "triage-report",
        declared_internal=("fetch_gbs_report",),
        gbs_surface=True,
    ),
    SymbolSpec(
        "_Anchor",
        ("§4",),
        GBS_REPORT,
        "triage-report",
        gbs_surface=True,
    ),
    SymbolSpec("_Cell", ("§4",), GBS_REPORT, "triage-report", gbs_surface=True),
    SymbolSpec("_Row", ("§4",), GBS_REPORT, "triage-report", gbs_surface=True),
    SymbolSpec("_Table", ("§4",), GBS_REPORT, "triage-report", gbs_surface=True),
    SymbolSpec(
        "_CellBuilder",
        ("§4",),
        GBS_REPORT,
        "triage-report",
        gbs_surface=True,
    ),
    SymbolSpec(
        "_AnchorBuilder",
        ("§4",),
        GBS_REPORT,
        "triage-report",
        gbs_surface=True,
    ),
    SymbolSpec(
        "_IframeParser",
        ("§4",),
        GBS_REPORT,
        "triage-report",
        declared_internal=("find_iframe_src",),
        gbs_surface=True,
    ),
    SymbolSpec(
        "_ReportTableParser",
        ("§4",),
        GBS_REPORT,
        "triage-report",
        declared_internal=("parse_gbs_report_packages",),
        gbs_surface=True,
    ),
    SymbolSpec(
        "_looks_like_build_status_table",
        ("§4",),
        GBS_REPORT,
        "triage-report",
        declared_internal=("parse_gbs_report_packages",),
        gbs_surface=True,
    ),
    SymbolSpec(
        "_row_to_package",
        ("§4",),
        GBS_REPORT,
        "triage-report",
        declared_internal=("parse_gbs_report_packages",),
        gbs_surface=True,
    ),
    SymbolSpec(
        "_status_from_anchor",
        ("§4",),
        GBS_REPORT,
        "triage-report",
        declared_internal=("_row_to_package",),
        gbs_surface=True,
    ),
    SymbolSpec(
        "_attrs_to_map",
        ("§4",),
        GBS_REPORT,
        "triage-report",
        declared_internal=("_IframeParser.handle_starttag", "_ReportTableParser.handle_starttag"),
        gbs_surface=True,
    ),
    SymbolSpec(
        "_class_names",
        ("§4",),
        GBS_REPORT,
        "triage-report",
        declared_internal=("_ReportTableParser.handle_starttag",),
        gbs_surface=True,
    ),
    SymbolSpec(
        "_normalize_text",
        ("§4",),
        GBS_REPORT,
        "triage-report",
        declared_internal=("_ReportTableParser.handle_endtag",),
        gbs_surface=True,
    ),
)


MODULE_OWNERS: dict[str, str] = {
    "ci_triage.batch_cli": "orchestrator",
    "ci_triage.campaign_repair_step": "wrapper",
    "ci_triage.cli": "orchestrator",
    "ci_triage.orchestrator": "orchestrator",
    "ci_triage.report": "triage-report",
    "ci_triage.runner": "orchestrator",
    "ci_triage.sources": "quickbuild",
    "ci_triage.verify.build_verify": "build-verify",
    "ci_triage.verify.gerrit_submit": "submit",
}


@dataclass(frozen=True)
class SourceFile:
    path: Path
    relative: str
    module: str
    text: str
    tree: ast.Module
    top_level: frozenset[str]


@dataclass(frozen=True)
class AuditResult:
    spec: SymbolSpec
    definition: str
    consumers: tuple[str, ...]
    internal: tuple[str, ...]
    marker_reads: tuple[str, ...]
    marker_writes: tuple[str, ...]
    reasons: tuple[str, ...]
    evidence: tuple[str, ...]

    @property
    def verdict(self) -> str:
        return "OK" if not self.reasons else "MISMATCH: " + "; ".join(self.reasons)


def _module_name(relative: str) -> str:
    path = Path(relative)
    parts = list(path.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _top_level_symbols(tree: ast.Module) -> frozenset[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
    return frozenset(names)


def _load_sources(scripts_root: Path) -> tuple[SourceFile, ...]:
    sources: list[SourceFile] = []
    for path in sorted(scripts_root.rglob("*.py")):
        relative_path = path.relative_to(scripts_root)
        if "__pycache__" in relative_path.parts or "release-v1.4.0" in relative_path.parts:
            continue
        if "test" in relative_path.parts or "tests" in relative_path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(path))
        relative = relative_path.as_posix()
        sources.append(
            SourceFile(
                path=path,
                relative=relative,
                module=_module_name(relative),
                text=text,
                tree=tree,
                top_level=_top_level_symbols(tree),
            )
        )
    return tuple(sources)


def _definition_line(source: SourceFile, symbol: str) -> int | None:
    for node in source.tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name == symbol:
                return node.lineno
        elif isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == symbol for target in node.targets):
                return node.lineno
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == symbol:
                return node.lineno
    return None


class _ReferenceVisitor(ast.NodeVisitor):
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol
        self.lines: set[int] = set()

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load) and node.id == self.symbol:
            self.lines.add(node.lineno)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if isinstance(node.ctx, ast.Load) and node.attr == self.symbol:
            self.lines.add(node.lineno)
        self.generic_visit(node)


class _ScopedReferenceVisitor(ast.NodeVisitor):
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol
        self.scopes: dict[str, set[int]] = {}
        self._stack: list[str] = []

    def _enter(self, name: str, node: ast.AST) -> None:
        self._stack.append(name)
        self.generic_visit(node)
        self._stack.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._enter(node.name, node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        prefix = f"{self._stack[-1]}." if self._stack else ""
        self._enter(prefix + node.name, node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        prefix = f"{self._stack[-1]}." if self._stack else ""
        self._enter(prefix + node.name, node)

    def _record(self, node: ast.AST) -> None:
        if self._stack:
            line = getattr(node, "lineno", None)
            if isinstance(line, int):
                self.scopes.setdefault(self._stack[-1], set()).add(line)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load) and node.id == self.symbol:
            self._record(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if isinstance(node.ctx, ast.Load) and node.attr == self.symbol:
            self._record(node)
        self.generic_visit(node)


def _expr_uses_names(expr: ast.AST, names: set[str]) -> bool:
    return any(
        (isinstance(node, ast.Name) and node.id in names)
        or (isinstance(node, ast.Attribute) and node.attr in names)
        for node in ast.walk(expr)
    )


def _marker_accesses(source: SourceFile, symbol: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    reads: set[str] = set()
    writes: set[str] = set()
    read_methods = {"exists", "is_file", "read_bytes", "read_text", "stat"}
    write_methods = {"rename", "replace", "touch", "unlink", "write_bytes", "write_text"}

    for node in ast.walk(source.tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        scope = node.name
        tainted = {symbol}
        if symbol == "MARKER_FILENAME" and scope == "_verify_cleanup_handle":
            tainted.add("marker_path")
        changed = True
        while changed:
            changed = False
            for child in ast.walk(node):
                if not isinstance(child, (ast.Assign, ast.AnnAssign)):
                    continue
                value = child.value
                if value is None or not _expr_uses_names(value, tainted):
                    continue
                targets = child.targets if isinstance(child, ast.Assign) else [child.target]
                for target in targets:
                    if isinstance(target, ast.Name) and target.id not in tainted:
                        tainted.add(target.id)
                        changed = True
        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue
            if isinstance(child.func, ast.Name) and child.func.id == "_read_marker":
                if child.args and _expr_uses_names(child.args[0], tainted):
                    reads.add(f"{scope}@{child.lineno}")
            if not isinstance(child.func, ast.Attribute):
                continue
            if not _expr_uses_names(child.func.value, tainted):
                continue
            if child.func.attr in read_methods:
                reads.add(f"{scope}@{child.lineno}")
            if child.func.attr in write_methods:
                writes.add(f"{scope}@{child.lineno}")

    return tuple(sorted(reads)), tuple(sorted(writes))


def _raw_evidence(sources: tuple[SourceFile, ...], spec: SymbolSpec) -> tuple[str, ...]:
    pattern = re.compile(rf"\b{re.escape(spec.name)}\b")
    evidence: list[str] = []
    for source in sources:
        for line_number, line in enumerate(source.text.splitlines(), start=1):
            if pattern.search(line):
                evidence.append(f"{source.relative}:{line_number}:{line.strip()}")
    return tuple(evidence)


def _actual_consumers(
    sources: tuple[SourceFile, ...],
    definition_source: SourceFile,
    symbol: str,
) -> tuple[str, ...]:
    consumers: set[str] = set()
    for source in sources:
        if source.relative == definition_source.relative:
            continue
        if symbol in source.top_level:
            continue  # Same-spelled local implementation, not this definition.
        visitor = _ReferenceVisitor(symbol)
        visitor.visit(source.tree)
        if visitor.lines:
            consumers.add(source.module)
    return tuple(sorted(consumers))


def _internal_references(source: SourceFile, symbol: str) -> tuple[str, ...]:
    visitor = _ScopedReferenceVisitor(symbol)
    visitor.visit(source.tree)
    return tuple(
        f"{scope}@{','.join(str(line) for line in sorted(lines))}"
        for scope, lines in sorted(visitor.scopes.items())
        if scope != symbol
    )


def _scope_names(internal: tuple[str, ...]) -> set[str]:
    return {entry.split("@", 1)[0] for entry in internal}


def _audit_one(
    sources: tuple[SourceFile, ...],
    specs_by_name: dict[str, SymbolSpec],
    spec: SymbolSpec,
) -> AuditResult:
    by_relative = {source.relative: source for source in sources}
    evidence = _raw_evidence(sources, spec)
    if spec.status == "to-be-created":
        planned_reasons = (
            () if spec.owner == "shared" else ("to-be-created owner must be shared",)
        )
        return AuditResult(
            spec,
            "TO_BE_CREATED",
            (),
            (),
            (),
            (),
            planned_reasons,
            evidence,
        )
    if spec.status != "existing":
        return AuditResult(
            spec,
            "INVALID_STATUS",
            (),
            (),
            (),
            (),
            (f"unsupported inventory status {spec.status}",),
            evidence,
        )

    source = by_relative.get(spec.definition)
    if source is None:
        return AuditResult(
            spec,
            "NOT_FOUND",
            (),
            (),
            (),
            (),
            (f"definition file {spec.definition} not found",),
            evidence,
        )

    line = _definition_line(source, spec.name)
    if line is None:
        return AuditResult(
            spec,
            "NOT_FOUND",
            (),
            (),
            (),
            (),
            (f"definition {spec.name} not found in {spec.definition}",),
            evidence,
        )

    consumers = _actual_consumers(sources, source, spec.name)
    internal = _internal_references(source, spec.name)
    marker_reads: tuple[str, ...] = ()
    marker_writes: tuple[str, ...] = ()
    if spec.name in {"MARKER_FILENAME", "PROTECTED_FILENAME"}:
        marker_reads, marker_writes = _marker_accesses(source, spec.name)

    reasons: list[str] = []
    if spec.owner.startswith("UNRESOLVED"):
        reasons.append(f"declared owner is unresolved: {spec.owner}")

    declared_consumers = set(spec.declared_consumers)
    measured_consumers = set(consumers)
    for missing in sorted(declared_consumers - measured_consumers):
        reasons.append(f"declared consumer {missing} not found")
    for extra in sorted(measured_consumers - declared_consumers):
        reasons.append(f"undeclared consumer {extra}")

    if spec.declared_internal:
        actual_internal = _scope_names(internal)
        declared_internal = set(spec.declared_internal)
        for missing in sorted(declared_internal - actual_internal):
            reasons.append(f"declared internal consumer {missing} not found")
        for extra in sorted(actual_internal - declared_internal):
            reasons.append(f"undeclared internal consumer {extra}")

    if len(measured_consumers) > 1 and not spec.owner.startswith("shared"):
        reasons.append("multiple consumers require shared ownership")
    elif len(measured_consumers) == 1 and not (
        spec.owner.startswith("shared") or spec.owner.startswith("UNRESOLVED")
    ):
        consumer = next(iter(measured_consumers))
        consumer_owner = MODULE_OWNERS.get(consumer)
        if consumer_owner is not None and consumer_owner != spec.owner:
            reasons.append(
                f"single consumer {consumer} belongs to {consumer_owner}, "
                f"not declared owner {spec.owner}"
            )
    if spec.format_authority and not spec.owner.startswith("shared"):
        reasons.append("format authority requires shared ownership")

    if not (spec.owner.startswith("shared") or spec.owner.startswith("UNRESOLVED")):
        for scope in sorted(_scope_names(internal)):
            caller_name = scope.split(".", 1)[0]
            caller_spec = specs_by_name.get(caller_name)
            if caller_spec is None:
                continue
            caller_owner = caller_spec.owner
            if caller_owner.startswith("shared") or caller_owner.startswith("UNRESOLVED"):
                continue
            if caller_owner != spec.owner:
                reasons.append(
                    f"cross-boundary internal access from {scope} "
                    f"owned by {caller_owner}"
                )

    return AuditResult(
        spec=spec,
        definition=f"{spec.definition}:{line}",
        consumers=consumers,
        internal=internal,
        marker_reads=marker_reads,
        marker_writes=marker_writes,
        reasons=tuple(reasons),
        evidence=evidence,
    )


def _public_surface(source: SourceFile) -> set[str]:
    result: set[str] = set()
    for node in source.tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            result.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and re.fullmatch(r"[A-Z_][A-Z0-9_]*", target.id):
                    result.add(target.id)
        elif isinstance(node, ast.AnnAssign):
            target = node.target
            if isinstance(target, ast.Name) and re.fullmatch(r"[A-Z_][A-Z0-9_]*", target.id):
                result.add(target.id)
    return result


def _declared_text(spec: SymbolSpec) -> str:
    consumers = ",".join(spec.declared_consumers) or "-"
    internal = ",".join(spec.declared_internal) or "-"
    return (
        f"sections={'+'.join(spec.sections)}; status={spec.status}; owner={spec.owner}; "
        f"consumers=[{consumers}]; internal=[{internal}]"
    )


def _measured_text(result: AuditResult) -> str:
    consumers = ",".join(result.consumers) or "-"
    internal = ",".join(result.internal) or "-"
    marker = ""
    if result.spec.name in {"MARKER_FILENAME", "PROTECTED_FILENAME"}:
        reads = ",".join(result.marker_reads) or "-"
        writes = ",".join(result.marker_writes) or "-"
        marker = f"; marker_reads=[{reads}]; marker_writes=[{writes}]"
    return f"definition={result.definition}; consumers=[{consumers}]; internal=[{internal}]{marker}"


def run(repo_root: Path) -> int:
    scripts_root = repo_root / "tizen-ci-triage/scripts"
    sources = _load_sources(scripts_root)
    by_relative = {source.relative: source for source in sources}
    surface_checks = (
        (by_relative[GBS_REPORT], {spec.name for spec in SPECS if spec.gbs_surface}),
        (
            by_relative[QUICKBUILD],
            {spec.name for spec in SPECS if spec.quickbuild_surface},
        ),
    )
    incomplete = sorted(
        (source.relative, symbol)
        for source, audited in surface_checks
        for symbol in _public_surface(source) - audited
    )

    specs_by_name = {spec.name: spec for spec in SPECS}
    results = tuple(_audit_one(sources, specs_by_name, spec) for spec in SPECS)
    print("symbol | declared | measured_consumers | verdict")
    for result in results:
        print(
            f"{result.spec.name} | {_declared_text(result.spec)} | "
            f"{_measured_text(result)} | {result.verdict}"
        )
    for relative, symbol in incomplete:
        print(f"INCOMPLETE: {symbol} in {relative} public surface but not audited")

    mismatches = [result for result in results if result.reasons]
    print(
        f"SUMMARY | {len(results) - len(mismatches)} OK | "
        f"{len(mismatches)} MISMATCH | {len(incomplete)} INCOMPLETE"
    )
    if mismatches or incomplete:
        print("EVIDENCE")
        for result in mismatches:
            print(f"[{result.spec.name}] {result.verdict}")
            if result.evidence:
                for line in result.evidence:
                    print(f"  {line}")
            else:
                print("  (no source matches)")
        for relative, symbol in incomplete:
            source = by_relative[relative]
            pattern = re.compile(rf"\b{re.escape(symbol)}\b")
            print(f"[INCOMPLETE:{relative}:{symbol}]")
            for line_number, line in enumerate(source.text.splitlines(), start=1):
                if pattern.search(line):
                    print(f"  {source.relative}:{line_number}:{line.strip()}")
    return 1 if mismatches or incomplete else 0


def main() -> int:
    repo_root = Path(__file__).resolve().parents[3]
    return run(repo_root)


if __name__ == "__main__":
    sys.exit(main())
