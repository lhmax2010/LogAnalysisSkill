#!/usr/bin/env python3
"""Statically audit P4.9 step-0 attribution tables against the source tree.

This tool parses source text and Python ASTs only. It never imports or executes
the modules being audited. The inventory covers the step-0 shared moves and the
extracted convergence-judge, qb-discover, and gerrit-fetch skills. gbs_report.py
is intentionally out of scope and deferred as a whole to the triage-report
extraction batch.
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, replace
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
    quickbuild_surface: bool = False
    status: str = "existing"
    expected_owner: str | None = None


@dataclass(frozen=True)
class ModuleScopeSpec:
    module: str
    sections: tuple[str, ...]
    definition: str
    owner: str
    legacy_path: str
    legacy_mode: str
    import_root: str
    expected_top_level_count: int


WORKSPACE = "ci_triage/verify/workspace.py"
SHARED_WORKSPACE = "tizen_ci_shared/workspace/__init__.py"
QUICKBUILD = "tizen_ci_shared/quickbuild_http.py"
SHARED_TYPES = "tizen_ci_shared/types.py"
SHARED_CLASSIFY = "tizen_ci_shared/classify.py"
SHARED_STATE_DB = "tizen_ci_shared/state/db.py"
SHARED_STATE_KEYS = "tizen_ci_shared/state/keys.py"
SHARED_STATE_RECORDS = "tizen_ci_shared/state/records.py"
SKILL_CONVERGENCE = "tizen_convergence_judge/convergence.py"
SKILL_QB_DISCOVER = "tizen_qb_discover/sources.py"
SKILL_GERRIT_FETCH = "tizen_gerrit_fetch/gerrit.py"

SpecKey = tuple[str, str]


# Keep this high-to-low order and the registered skill roots synchronized with
# .importlinter's root-layers contract. A skill owner is valid only when its
# import root is explicitly registered here and in that contract.
ROOT_LAYERS_HIGH_TO_LOW = (
    "ci_triage",
    "tizen_convergence_judge",
    "tizen_qb_discover",
    "tizen_gerrit_fetch",
    "tizen_ci_shared",
)
REGISTERED_SKILL_ROOTS: dict[str, str] = {
    "skill/tizen_convergence_judge": "tizen_convergence_judge",
    "skill/tizen_qb_discover": "tizen_qb_discover",
    "skill/tizen_gerrit_fetch": "tizen_gerrit_fetch",
}


CONVERGENCE_SYMBOLS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("DEFAULT_BUILD_PREFIXES", ()),
    ("SOURCE_CLUSTER_KINDS", ()),
    ("SOURCE_DIAGNOSTIC_KINDS", ()),
    ("ERROR_DIAGNOSTIC_KINDS", ()),
    ("_WARNING_OPTION_RE", ()),
    ("_IDENTIFIER_RE", ()),
    ("_BUILD_PACKAGE_RE", ()),
    ("ConvergenceResult", ("ci_triage.campaign_repair_step",)),
    ("_Fingerprint", ()),
    ("_ClusterView", ()),
    (
        "check_convergence",
        ("ci_triage.campaign_repair_step", "ci_triage.cli"),
    ),
    ("write_convergence_result", ("ci_triage.cli",)),
    ("touched_files_from_json", ("ci_triage.cli",)),
    ("_fingerprint_dict", ()),
    ("_primary_fingerprint", ()),
    ("_diagnostic_code", ()),
    ("_anchor", ()),
    ("_regression_reason", ()),
    ("_regression_suspected", ()),
    ("_clusters", ()),
    ("_cluster_view", ()),
    ("_cluster_diagnostic_code", ()),
    ("_cluster_files", ()),
    ("_location_dicts", ()),
    ("_is_source_level_cluster", ()),
    ("_error_count", ()),
    ("_is_error_cluster", ()),
    ("_normalize_file", ()),
    ("_normalize_message", ()),
    ("_stable_hash", ()),
    ("_string", ()),
    ("_int", ()),
    ("_string_list", ()),
    ("primary_fingerprint", ("ci_triage.campaign_state",)),
    ("error_count", ("ci_triage.campaign_state",)),
)

QB_DISCOVER_SYMBOLS: tuple[
    tuple[str, tuple[str, ...], tuple[str, ...]], ...
] = (
    (
        "QUICKBUILD_OVERVIEW_CONFIG_ID",
        ("ci_triage.batch_cli",),
        ("QuickBuildSource", "QuickBuildSource.discover"),
    ),
    ("_STATUS_CLASSES", (), ("_status_from_classes",)),
    (
        "FailedBuild",
        ("ci_triage.orchestrator",),
        ("FailedBuildSource.discover", "QuickBuildSource.discover", "_row_to_build"),
    ),
    ("FailedBuildSource", ("ci_triage.orchestrator",), ()),
    (
        "QuickBuildSource",
        ("ci_triage.batch_cli", "ci_triage.orchestrator"),
        (),
    ),
    (
        "_Anchor",
        (),
        ("_BuildsTableParser.handle_endtag", "_Cell", "_CellBuilder"),
    ),
    ("_Cell", (), ("_BuildsTableParser.__init__", "_BuildsTableParser.handle_endtag", "_Row")),
    (
        "_Row",
        (),
        (
            "_BuildsTable",
            "_BuildsTableParser.__init__",
            "_BuildsTableParser.handle_endtag",
            "_row_to_build",
        ),
    ),
    ("_BuildsTable", (), ("_parse_builds_table",)),
    (
        "_CellBuilder",
        (),
        ("_BuildsTableParser.__init__", "_BuildsTableParser.handle_starttag"),
    ),
    (
        "_AnchorBuilder",
        (),
        ("_BuildsTableParser.__init__", "_BuildsTableParser.handle_starttag"),
    ),
    ("_BuildsTableParser", (), ("_parse_builds_table",)),
    ("_parse_builds_table", (), ("QuickBuildSource.discover",)),
    ("_row_to_build", (), ("QuickBuildSource.discover",)),
    ("_status_from_classes", (), ("_row_to_build",)),
    ("_strip_snapshot_prefix", (), ("_row_to_build",)),
    ("_attrs_to_map", (), ("_BuildsTableParser.handle_starttag",)),
    ("_class_names", (), ("_BuildsTableParser.handle_starttag",)),
    ("_normalize_text", (), ("_BuildsTableParser.handle_endtag",)),
)

GERRIT_FETCH_SYMBOLS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("GERRIT_HOST", ()),
    ("GERRIT_PORT", ()),
    ("SubprocessRunner", ()),
    ("GerritError", ()),
    ("query_change_for_commit", ()),
    ("parse_gerrit_query_output", ()),
    ("change_from_query_obj", ()),
    ("find_patchset_by_revision", ()),
    ("fetch_source_for_commit", ("ci_triage.runner",)),
    ("_run_git", ()),
    ("_reset_generated_source_dir", ()),
    ("_optional_int", ()),
)


SPECS: tuple[SymbolSpec | ModuleScopeSpec, ...] = (
    ModuleScopeSpec(
        "state/db.py",
        ("§1.2a", "v2.0-revision-7a"),
        SHARED_STATE_DB,
        "shared/state",
        "tizen-ci-triage/scripts/ci_triage/state/db.py",
        "deleted",
        "tizen_ci_shared.state",
        10,
    ),
    ModuleScopeSpec(
        "state/keys.py",
        ("§1.2a", "v2.0-revision-7a"),
        SHARED_STATE_KEYS,
        "shared/state",
        "tizen-ci-triage/scripts/ci_triage/state/keys.py",
        "deleted",
        "tizen_ci_shared.state",
        3,
    ),
    ModuleScopeSpec(
        "state/records.py",
        ("§1.2a", "v2.0-revision-7a"),
        SHARED_STATE_RECORDS,
        "shared/state",
        "tizen-ci-triage/scripts/ci_triage/state/records.py",
        "deleted",
        "tizen_ci_shared.state",
        8,
    ),
    ModuleScopeSpec(
        "classify.py",
        ("§1.2a", "v2.0-revision-7a"),
        SHARED_CLASSIFY,
        "shared/classify",
        "tizen-ci-triage/scripts/ci_triage/verify/failure_classify.py",
        "pure-shim",
        "tizen_ci_shared.classify",
        27,
    ),
    # §2, with the v1.1 additions applied.
    SymbolSpec(
        "GerritPatchSet",
        ("§2", "v2.0-revision-1"),
        SHARED_TYPES,
        "shared/types",
        ("tizen_gerrit_fetch.gerrit",),
    ),
    SymbolSpec(
        "GerritChange",
        ("§2", "v2.0-revision-1"),
        SHARED_TYPES,
        "shared/types",
        ("tizen_gerrit_fetch.gerrit",),
    ),
    SymbolSpec(
        "SourceFetchResult",
        ("§2", "v2.0-revision-1"),
        SHARED_TYPES,
        "shared/types",
        ("ci_triage.report", "tizen_gerrit_fetch.gerrit"),
    ),
    SymbolSpec(
        "FailedPackage",
        ("§2",),
        SHARED_TYPES,
        "shared/types",
        (
            "ci_triage.orchestrator",
            "ci_triage.quickbuild_log",
            "ci_triage.report",
            "ci_triage.runner",
        ),
    ),
    SymbolSpec(
        "DisposableWorktree",
        ("§2", "§3.2"),
        SHARED_WORKSPACE,
        "shared/workspace",
        ("ci_triage.verify.workspace",),
    ),
    SymbolSpec(
        "WorkspaceViolation",
        ("§2", "§3.2"),
        SHARED_WORKSPACE,
        "shared/workspace",
        ("ci_triage.campaign_repair_step", "ci_triage.verify.workspace"),
    ),
    SymbolSpec(
        "discover_sibling_pythonpath",
        ("§3.3",),
        "tizen_ci_shared/env.py",
        "shared/env",
        (
            "ci_triage.batch_cli",
            "ci_triage.cli",
            "ci_triage.orchestrator",
            "ci_triage.verify.build_verify",
        ),
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
        SHARED_WORKSPACE,
        "shared/workspace",
        ("ci_triage.verify.build_verify", "ci_triage.verify.workspace"),
        ("cleanup_disposable_copy",),
    ),
    SymbolSpec(
        "cleanup_disposable_copy",
        ("§3.2",),
        SHARED_WORKSPACE,
        "shared/workspace",
        ("ci_triage.campaign_repair_step",),
    ),
    SymbolSpec(
        "is_protected",
        ("§3.2",),
        SHARED_WORKSPACE,
        "shared/workspace",
        ("ci_triage.campaign_repair_step", "ci_triage.verify.workspace"),
        ("cleanup_disposable_copy",),
    ),
    SymbolSpec(
        "release_worktree_protection",
        ("§3.2",),
        SHARED_WORKSPACE,
        "shared/workspace",
        ("ci_triage.verify.gerrit_submit",),
    ),
    SymbolSpec(
        "mark_worktree_protected",
        ("§3.2",),
        SHARED_WORKSPACE,
        "shared/workspace",
        ("ci_triage.verify.build_verify",),
    ),
    SymbolSpec(
        "_oldest_worktrees",
        ("§3.2",),
        SHARED_WORKSPACE,
        "shared/workspace",
        ("ci_triage.verify.workspace",),
    ),
    SymbolSpec(
        "_run_git",
        ("§3.2",),
        SHARED_WORKSPACE,
        "shared/workspace",
        ("ci_triage.verify.workspace",),
        ("clean_repository_preserving_markers",),
    ),
    SymbolSpec(
        "_verify_cleanup_handle",
        ("§3.2",),
        SHARED_WORKSPACE,
        "shared/workspace",
        declared_internal=("cleanup_worktree", "mark_worktree_protected"),
    ),
    SymbolSpec(
        "_is_relative_to",
        ("§3.2", "v2.0-revision-6"),
        SHARED_WORKSPACE,
        "shared/workspace",
        declared_internal=("_verify_cleanup_handle",),
    ),
    SymbolSpec(
        "_exclude_private_files",
        ("§3.2",),
        SHARED_WORKSPACE,
        "shared/workspace",
        ("ci_triage.verify.workspace",),
        ("mark_worktree_protected",),
    ),
    SymbolSpec(
        "MARKER_FILENAME",
        ("§3.1", "§3.2"),
        SHARED_WORKSPACE,
        "shared/workspace",
        format_authority=True,
    ),
    SymbolSpec(
        "PROTECTED_FILENAME",
        ("§3.1", "§3.2"),
        SHARED_WORKSPACE,
        "shared/workspace",
        format_authority=True,
    ),
    SymbolSpec(
        "_read_marker",
        ("§3.1", "§3.2"),
        SHARED_WORKSPACE,
        "shared/workspace",
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
        SHARED_WORKSPACE,
        "shared/workspace",
        ("ci_triage.verify.workspace",),
        format_authority=True,
    ),
    SymbolSpec(
        "clean_repository_preserving_markers",
        ("§3.2", "S-1", "v2.0-revision-3"),
        SHARED_WORKSPACE,
        "shared/workspace",
        ("ci_triage.verify.workspace",),
    ),
    # §4 quickbuild.py HTTP public surface. gbs_report.py is out of scope.
    SymbolSpec(
        "HttpFetcher",
        ("§4",),
        QUICKBUILD,
        "shared/quickbuild_http",
        ("ci_triage.gbs_report", "tizen_qb_discover.sources"),
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "QuickBuildError",
        ("§4",),
        QUICKBUILD,
        "shared/quickbuild_http",
        (
            "ci_triage.gbs_report",
            "ci_triage.orchestrator",
            "ci_triage.runner",
            "tizen_qb_discover.sources",
        ),
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "_raise_if_login_page",
        ("§4",),
        QUICKBUILD,
        "shared/quickbuild_http",
        ("ci_triage.gbs_report", "tizen_qb_discover.sources"),
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "_urllib_fetch",
        ("§4",),
        QUICKBUILD,
        "shared/quickbuild_http",
        ("ci_triage.gbs_report", "tizen_qb_discover.sources"),
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "DEFAULT_COOKIE_PATH",
        ("§4",),
        QUICKBUILD,
        "shared/quickbuild_http",
        (
            "ci_triage.batch_cli",
            "ci_triage.cli",
            "ci_triage.gbs_report",
            "ci_triage.orchestrator",
            "ci_triage.runner",
            "tizen_qb_discover.sources",
        ),
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "DEFAULT_QUICKBUILD_BASE_URL",
        ("§4",),
        QUICKBUILD,
        "shared/quickbuild_http",
        ("ci_triage.gbs_report", "tizen_qb_discover.sources"),
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "load_cookie_jar",
        ("§4", "v1.2-A"),
        QUICKBUILD,
        "shared/quickbuild_http",
        ("ci_triage.gbs_report", "tizen_qb_discover.sources"),
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "DOWNLOAD_LINK_MARKER",
        ("§4", "v1.2-A"),
        QUICKBUILD,
        "shared/quickbuild_http",
        declared_internal=("find_download_href",),
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "DOWNLOAD_TIZEN_BASE_URL",
        ("§4", "v1.2-A"),
        QUICKBUILD,
        "shared/quickbuild_http",
        declared_internal=("derive_package_buildlog_url",),
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "HttpResponse",
        ("§4", "v1.2-A"),
        QUICKBUILD,
        "shared/quickbuild_http",
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "QuickBuildDownload",
        ("§4", "v1.2-A"),
        QUICKBUILD,
        "shared/quickbuild_http",
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "PackageBuildLog",
        ("§4", "v1.2-A"),
        QUICKBUILD,
        "shared/quickbuild_http",
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "download_full_log",
        ("§4", "v1.2-A"),
        QUICKBUILD,
        "shared/quickbuild_http",
        ("ci_triage.orchestrator", "ci_triage.runner"),
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "find_download_href",
        ("§4", "v1.2-A"),
        QUICKBUILD,
        "shared/quickbuild_http",
        declared_internal=("download_full_log",),
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "derive_package_buildlog_url",
        ("§4", "v1.2-A"),
        QUICKBUILD,
        "shared/quickbuild_http",
        declared_internal=("download_package_buildlog",),
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "download_package_buildlog",
        ("§4", "v1.2-A"),
        QUICKBUILD,
        "shared/quickbuild_http",
        ("ci_triage.runner",),
        quickbuild_surface=True,
    ),
    SymbolSpec(
        "normalize_quickbuild_url",
        ("§4", "v1.2-A"),
        QUICKBUILD,
        "shared/quickbuild_http",
        declared_internal=("_urllib_fetch",),
        quickbuild_surface=True,
    ),
    *(
        SymbolSpec(
            name,
            ("skill1-§1.2", "skill1-v1.3"),
            SKILL_CONVERGENCE,
            "skill/tizen_convergence_judge",
            consumers,
        )
        for name, consumers in CONVERGENCE_SYMBOLS
    ),
    *(
        SymbolSpec(
            name,
            ("skill2-§2.2", "skill2-v1.3"),
            SKILL_QB_DISCOVER,
            "skill/tizen_qb_discover",
            consumers,
            internal,
        )
        for name, consumers, internal in QB_DISCOVER_SYMBOLS
    ),
    *(
        SymbolSpec(
            name,
            ("skill3-§0", "skill3-v1.3.1"),
            SKILL_GERRIT_FETCH,
            "skill/tizen_gerrit_fetch",
            consumers,
        )
        for name, consumers in GERRIT_FETCH_SYMBOLS
    ),
)


MODULE_OWNERS: dict[str, str] = {
    "ci_triage.batch_cli": "orchestrator",
    "ci_triage.campaign_repair_step": "wrapper",
    "ci_triage.cli": "orchestrator",
    "ci_triage.orchestrator": "orchestrator",
    "ci_triage.report": "triage-report",
    "ci_triage.runner": "orchestrator",
    "tizen_qb_discover.sources": "skill/tizen_qb_discover",
    "tizen_gerrit_fetch.gerrit": "skill/tizen_gerrit_fetch",
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
class _ImportBinding:
    source_module: str
    source_symbol: str
    local_name: str


ConsumerFinder = Callable[
    [tuple[SourceFile, ...], SourceFile, str],
    tuple[str, ...],
]


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


@dataclass(frozen=True)
class ModuleScopeResult:
    spec: ModuleScopeSpec
    covered_symbols: tuple[str, ...]
    consumers: tuple[str, ...]
    reasons: tuple[str, ...]

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


def _import_from_module(source: SourceFile, node: ast.ImportFrom) -> str | None:
    if node.module is None:
        return None
    if node.level == 0:
        return node.module

    package_parts = source.module.split(".")
    if source.path.name != "__init__.py":
        package_parts.pop()
    parent_count = node.level - 1
    if parent_count > len(package_parts):
        return None
    base_parts = package_parts[: len(package_parts) - parent_count]
    return ".".join((*base_parts, *node.module.split(".")))


def _module_scope_import_bindings(source: SourceFile) -> tuple[_ImportBinding, ...]:
    bindings: list[_ImportBinding] = []
    # This deliberately covers only named module-scope ImportFrom bindings.
    # It does not cover ``import X; X.S`` attribute access, ImportFrom nodes
    # nested inside functions/classes, or ``from X import *``. Those known
    # limitations are intentional for this contract; do not "fix" them
    # without a new attribution design and matching fixtures.
    for node in source.tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        source_module = _import_from_module(source, node)
        if source_module is None:
            continue
        for alias in node.names:
            if alias.name == "*":
                continue
            bindings.append(
                _ImportBinding(
                    source_module=source_module,
                    source_symbol=alias.name,
                    local_name=alias.asname or alias.name,
                )
            )
    return tuple(bindings)


def _resolve_import_origin(
    binding: _ImportBinding,
    sources_by_module: dict[str, SourceFile],
    bindings_by_module: dict[str, tuple[_ImportBinding, ...]],
    *,
    seen: frozenset[tuple[str, str]] = frozenset(),
) -> tuple[str, str]:
    key = (binding.source_module, binding.source_symbol)
    if key in seen:
        return key
    source = sources_by_module.get(binding.source_module)
    if source is None or binding.source_symbol in source.top_level:
        return key

    reexports = tuple(
        candidate
        for candidate in bindings_by_module.get(binding.source_module, ())
        if candidate.local_name == binding.source_symbol
    )
    if len(reexports) != 1:
        return key
    return _resolve_import_origin(
        reexports[0],
        sources_by_module,
        bindings_by_module,
        seen=seen | {key},
    )


def _legacy_actual_consumers(
    sources: tuple[SourceFile, ...],
    definition_source: SourceFile,
    symbol: str,
) -> tuple[str, ...]:
    consumers: set[str] = set()
    for source in sources:
        if source.relative == definition_source.relative:
            continue
        if symbol in source.top_level:
            # Known limit: this twin guard intentionally skips a module that
            # shadows a name even if it also imports the original definition.
            # That over-skip is deliberate; do not "fix" it without a new
            # attribution design and a fixture for the ambiguous import.
            continue
        visitor = _ReferenceVisitor(symbol)
        visitor.visit(source.tree)
        if visitor.lines:
            consumers.add(source.module)
    return tuple(sorted(consumers))


def _actual_consumers(
    sources: tuple[SourceFile, ...],
    definition_source: SourceFile,
    symbol: str,
) -> tuple[str, ...]:
    consumers: set[str] = set()
    sources_by_module = {source.module: source for source in sources}
    bindings_by_module = {
        source.module: _module_scope_import_bindings(source) for source in sources
    }
    target = (definition_source.module, symbol)

    for source in sources:
        if source.relative == definition_source.relative:
            continue
        if symbol in source.top_level:
            # Known limit: this twin guard intentionally skips a module that
            # shadows a name even if it also imports the original definition.
            # That over-skip is deliberate; do not "fix" it without a new
            # attribution design and a fixture for the ambiguous import.
            continue

        bindings_by_local_name = {
            binding.local_name: binding
            for binding in bindings_by_module[source.module]
        }
        origins_by_local_name = {
            local_name: _resolve_import_origin(
                binding,
                sources_by_module,
                bindings_by_module,
            )
            for local_name, binding in bindings_by_local_name.items()
        }
        matched = False
        for local_name, origin in origins_by_local_name.items():
            if origin != target:
                continue
            visitor = _ReferenceVisitor(local_name)
            visitor.visit(source.tree)
            if visitor.lines:
                matched = True
                break

        # Preserve name-only attribution for code without a named ImportFrom
        # binding. When the name is bound, its measured origin is authoritative.
        if not matched and symbol not in origins_by_local_name:
            visitor = _ReferenceVisitor(symbol)
            visitor.visit(source.tree)
            matched = bool(visitor.lines)
        if matched:
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


def _type_closure_reasons(
    sources: tuple[SourceFile, ...],
    source: SourceFile,
    symbol: str,
) -> tuple[str, ...]:
    """Reject shared/types dataclass fields that reference higher repo types."""

    repo_types: dict[str, set[str]] = {}
    for candidate in sources:
        for node in candidate.tree.body:
            if isinstance(node, ast.ClassDef):
                repo_types.setdefault(node.name, set()).add(candidate.relative)

    class_node = next(
        (
            node
            for node in source.tree.body
            if isinstance(node, ast.ClassDef) and node.name == symbol
        ),
        None,
    )
    if class_node is None:
        return ()

    reasons: list[str] = []
    for field in class_node.body:
        if not isinstance(field, ast.AnnAssign) or not isinstance(field.target, ast.Name):
            continue
        referenced_names = {
            node.id for node in ast.walk(field.annotation) if isinstance(node, ast.Name)
        }
        for referenced in sorted(referenced_names):
            external_definitions = repo_types.get(referenced, set()) - {source.relative}
            if external_definitions:
                locations = ",".join(sorted(external_definitions))
                reasons.append(
                    "type-closure escapes L-1: "
                    f"{symbol}.{field.target.id} references {referenced} from {locations}"
                )
    return tuple(reasons)


def _module_root(module: str) -> str:
    return module.split(".", 1)[0]


def _skill_layer_reasons(
    owner: str,
    consumers: set[str],
    *,
    registered_skill_roots: dict[str, str] = REGISTERED_SKILL_ROOTS,
) -> tuple[str, ...]:
    """Enforce root-layers ownership for a registered skill API.

    The owner module itself is an internal consumer, not a cross-boundary
    dependency. Every other consumer must be in the higher ci_triage layer.
    A shared consumer is an uplink; a peer skill consumer is a same-layer edge.
    """

    if not owner.startswith("skill/"):
        return ()
    owner_root = registered_skill_roots.get(owner)
    if owner_root is None:
        return (f"skill owner {owner} is not registered in root-layers",)

    known_skill_roots = set(registered_skill_roots.values())
    reasons: list[str] = []
    for consumer in sorted(consumers):
        consumer_root = _module_root(consumer)
        if consumer_root == owner_root:
            continue
        if consumer_root == "ci_triage":
            continue
        if consumer_root == "tizen_ci_shared":
            reasons.append(
                f"skill owner {owner} is above shared consumer {consumer}"
            )
        elif consumer_root in known_skill_roots:
            reasons.append(
                f"skill owner {owner} has same-layer skill consumer {consumer}"
            )
        else:
            reasons.append(
                f"consumer {consumer} is outside registered root-layers "
                f"{ROOT_LAYERS_HIGH_TO_LOW}"
            )
    return tuple(reasons)


def _audit_one(
    sources: tuple[SourceFile, ...],
    specs_by_key: dict[SpecKey, SymbolSpec],
    spec: SymbolSpec,
    *,
    consumer_finder: ConsumerFinder = _actual_consumers,
) -> AuditResult:
    by_relative = {source.relative: source for source in sources}
    evidence = _raw_evidence(sources, spec)
    if spec.status == "to-be-created":
        planned_reasons: tuple[str, ...]
        if spec.expected_owner is None:
            planned_reasons = ("to-be-created expected_owner must be declared",)
        elif spec.owner == spec.expected_owner:
            planned_reasons = ()
        else:
            planned_reasons = (
                f"to-be-created owner must be {spec.expected_owner}",
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

    consumers = consumer_finder(sources, source, spec.name)
    internal = _internal_references(source, spec.name)
    marker_reads: tuple[str, ...] = ()
    marker_writes: tuple[str, ...] = ()
    if spec.name in {"MARKER_FILENAME", "PROTECTED_FILENAME"}:
        marker_reads, marker_writes = _marker_accesses(source, spec.name)

    reasons: list[str] = []
    if spec.owner.startswith("UNRESOLVED"):
        reasons.append(f"declared owner is unresolved: {spec.owner}")

    if spec.owner.startswith("skill/"):
        skill_root = REGISTERED_SKILL_ROOTS.get(spec.owner)
        definition_root = Path(spec.definition).parts[0]
        if skill_root is None:
            reasons.append(
                f"skill owner {spec.owner} is not registered in root-layers"
            )
        elif definition_root != skill_root:
            reasons.append(
                "skill-owned symbol defined outside its registered root: "
                f"{spec.definition} is not under {skill_root}"
            )

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

    # Ownership is checked against the same ci_triage > registered skills >
    # tizen_ci_shared order as .importlinter's root-layers contract. Shared is
    # the bottom layer, so all consumer combinations remain valid. A skill API
    # may have one or many orchestration consumers, but no shared or peer-skill
    # consumer. Non-skill ci_triage owners retain the original single-consumer
    # attribution check.
    reasons.extend(_skill_layer_reasons(spec.owner, measured_consumers))
    if len(measured_consumers) > 1 and not (
        spec.owner.startswith("shared") or spec.owner.startswith("skill/")
    ):
        reasons.append("multiple consumers require lower-layer ownership")
    elif len(measured_consumers) == 1 and not (
        spec.owner.startswith("shared") or spec.owner.startswith("UNRESOLVED")
        or spec.owner.startswith("skill/")
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

    if spec.owner == "shared/types":
        reasons.extend(_type_closure_reasons(sources, source, spec.name))

    if not (spec.owner.startswith("shared") or spec.owner.startswith("UNRESOLVED")):
        for scope in sorted(_scope_names(internal)):
            caller_name = scope.split(".", 1)[0]
            caller_spec = specs_by_key.get((spec.definition, caller_name))
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


def _module_consumers(
    sources: tuple[SourceFile, ...],
    *,
    import_root: str,
) -> tuple[str, ...]:
    consumers: set[str] = set()
    for source in sources:
        if source.module == import_root or source.module.startswith(import_root + "."):
            continue
        for node in ast.walk(source.tree):
            if isinstance(node, ast.Import):
                matched = any(
                    alias.name == import_root or alias.name.startswith(import_root + ".")
                    for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                matched = node.module == import_root or node.module.startswith(
                    import_root + "."
                )
            else:
                matched = False
            if matched:
                consumers.add(source.module)
                break
    return tuple(sorted(consumers))


def _pure_reexport_reasons(source: SourceFile, import_root: str) -> tuple[str, ...]:
    reasons: list[str] = []
    for node in source.tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str):
                continue
        if isinstance(node, ast.ImportFrom) and node.module == import_root:
            if all(alias.asname == alias.name for alias in node.names):
                continue
        reasons.append(
            f"legacy pure-shim contains non-re-export {type(node).__name__} "
            f"at {source.relative}:{getattr(node, 'lineno', '?')}"
        )
    return tuple(reasons)


def _audit_module_scope(
    repo_root: Path,
    sources: tuple[SourceFile, ...],
    symbol_specs: tuple[SymbolSpec, ...],
    spec: ModuleScopeSpec,
) -> ModuleScopeResult:
    by_relative = {source.relative: source for source in sources}
    reasons: list[str] = []
    source = by_relative.get(spec.definition)

    if not spec.definition.startswith("tizen_ci_shared/"):
        reasons.append("module-scope definition is outside tizen_ci_shared")
    if source is None:
        reasons.append(f"module-scope definition file {spec.definition} not found")
        covered_symbols: tuple[str, ...] = ()
    else:
        covered_symbols = tuple(sorted(_public_surface(source)))
        if len(covered_symbols) != spec.expected_top_level_count:
            reasons.append(
                "module-scope top-level count drift: "
                f"expected {spec.expected_top_level_count}, measured "
                f"{len(covered_symbols)}"
            )

    overlaps = sorted(
        symbol_spec.name
        for symbol_spec in symbol_specs
        if symbol_spec.definition == spec.definition
    )
    if overlaps:
        reasons.append(
            "module-scope conflicts with per-symbol inventory: " + ",".join(overlaps)
        )

    legacy_path = repo_root / spec.legacy_path
    if spec.legacy_mode == "deleted":
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", spec.legacy_path],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
        if tracked.returncode == 0:
            reasons.append(f"legacy module remains tracked: {spec.legacy_path}")
        elif tracked.returncode != 1:
            detail = tracked.stderr.strip() or f"exit {tracked.returncode}"
            reasons.append(f"git ls-files failed for {spec.legacy_path}: {detail}")
        if legacy_path.exists():
            reasons.append(f"legacy module remains on disk: {spec.legacy_path}")
    elif spec.legacy_mode == "pure-shim":
        legacy_source = next(
            (candidate for candidate in sources if candidate.path == legacy_path),
            None,
        )
        if legacy_source is None:
            reasons.append(f"legacy shim {spec.legacy_path} not found")
        else:
            reasons.extend(_pure_reexport_reasons(legacy_source, spec.import_root))
    else:
        reasons.append(f"unsupported module-scope legacy mode {spec.legacy_mode}")

    consumers = _module_consumers(sources, import_root=spec.import_root)
    return ModuleScopeResult(spec, covered_symbols, consumers, tuple(reasons))


def _declared_text(spec: SymbolSpec) -> str:
    consumers = ",".join(spec.declared_consumers) or "-"
    internal = ",".join(spec.declared_internal) or "-"
    expected_owner = spec.expected_owner or "-"
    return (
        f"sections={'+'.join(spec.sections)}; status={spec.status}; owner={spec.owner}; "
        f"expected_owner={expected_owner}; consumers=[{consumers}]; "
        f"internal=[{internal}]"
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
    triage_scripts_root = repo_root / "tizen-ci-triage/scripts"
    shared_scripts_root = repo_root / "tizen-ci-shared/scripts"
    convergence_scripts_root = repo_root / "tizen-convergence-judge/scripts"
    qb_discover_scripts_root = repo_root / "tizen-qb-discover/scripts"
    gerrit_fetch_scripts_root = repo_root / "tizen-gerrit-fetch/scripts"
    sources = (
        _load_sources(triage_scripts_root)
        + _load_sources(shared_scripts_root)
        + _load_sources(convergence_scripts_root)
        + _load_sources(qb_discover_scripts_root)
        + _load_sources(gerrit_fetch_scripts_root)
    )
    by_relative = {source.relative: source for source in sources}
    symbol_specs = tuple(spec for spec in SPECS if isinstance(spec, SymbolSpec))
    module_specs = tuple(spec for spec in SPECS if isinstance(spec, ModuleScopeSpec))
    module_scope_paths = {spec.definition for spec in module_specs}
    # Completeness follows the physical shared boundary. Once a module moves
    # into tizen_ci_shared, every top-level public-surface symbol must be in
    # the attribution inventory in the same change.
    surface_checks = tuple(
        (
            source,
            (
                _public_surface(source)
                if source.relative in module_scope_paths
                else {
                    spec.name
                    for spec in symbol_specs
                    if spec.definition == source.relative
                }
            ),
        )
        for source in sources
        if source.relative == "tizen_ci_shared/__init__.py"
        or source.relative.startswith("tizen_ci_shared/")
        or source.relative == SKILL_CONVERGENCE
        or source.relative == SKILL_QB_DISCOVER
        or source.relative == SKILL_GERRIT_FETCH
    )
    incomplete = sorted(
        (source.relative, symbol)
        for source, audited in surface_checks
        for symbol in _public_surface(source) - audited
    )

    specs_by_key = {(spec.definition, spec.name): spec for spec in symbol_specs}
    if len(specs_by_key) != len(symbol_specs):
        print(
            "SUMMARY | 0 SYMBOL OK | 0 MODULE-SCOPE OK (0 SYMBOLS COVERED) | "
            "1 MISMATCH | 0 INCOMPLETE"
        )
        print("EVIDENCE")
        print("[SPECS] duplicate (definition, symbol) inventory key")
        return 1
    results = tuple(_audit_one(sources, specs_by_key, spec) for spec in symbol_specs)
    module_results = tuple(
        _audit_module_scope(repo_root, sources, symbol_specs, spec)
        for spec in module_specs
    )
    print("symbol | declared | measured_consumers | verdict")
    for result in results:
        print(
            f"{result.spec.name} | {_declared_text(result.spec)} | "
            f"{_measured_text(result)} | {result.verdict}"
        )
    print("module | scope | owner | coverage_and_consumers | verdict")
    for module_result in module_results:
        consumers = ",".join(module_result.consumers) or "-"
        print(
            f"{module_result.spec.module} | module-scope | "
            f"{module_result.spec.owner} | "
            f"{len(module_result.covered_symbols)}/"
            f"{module_result.spec.expected_top_level_count} symbols covered; "
            f"consumers=[{consumers}] | {module_result.verdict}"
        )
    for relative, symbol in incomplete:
        print(f"INCOMPLETE: {symbol} in {relative} public surface but not audited")

    mismatches = [result for result in results if result.reasons]
    module_mismatches = [result for result in module_results if result.reasons]
    covered_count = sum(len(result.covered_symbols) for result in module_results)
    print(
        f"SUMMARY | {len(results) - len(mismatches)} SYMBOL OK | "
        f"{len(module_results) - len(module_mismatches)} MODULE-SCOPE OK "
        f"({covered_count} SYMBOLS COVERED) | "
        f"{len(mismatches) + len(module_mismatches)} MISMATCH | "
        f"{len(incomplete)} INCOMPLETE"
    )
    if mismatches or module_mismatches or incomplete:
        print("EVIDENCE")
        for result in mismatches:
            print(f"[{result.spec.name}] {result.verdict}")
            if result.evidence:
                for line in result.evidence:
                    print(f"  {line}")
            else:
                print("  (no source matches)")
        for module_result in module_mismatches:
            print(
                f"[MODULE-SCOPE:{module_result.spec.module}] "
                f"{module_result.verdict}"
            )
            print(f"  definition={module_result.spec.definition}")
            print(
                f"  legacy={module_result.spec.legacy_mode}:"
                f"{module_result.spec.legacy_path}"
            )
        for relative, symbol in incomplete:
            source = by_relative[relative]
            pattern = re.compile(rf"\b{re.escape(symbol)}\b")
            print(f"[INCOMPLETE:{relative}:{symbol}]")
            for line_number, line in enumerate(source.text.splitlines(), start=1):
                if pattern.search(line):
                    print(f"  {source.relative}:{line_number}:{line.strip()}")
    return 1 if mismatches or module_mismatches or incomplete else 0


def _run_negative_fixture(name: str) -> int:
    registered = dict(REGISTERED_SKILL_ROOTS)
    if name == "skill-owner-shared-consumer":
        consumers = {"tizen_ci_shared.types"}
    elif name == "skill-owner-peer-skill-consumer":
        registered["skill/fake_peer"] = "fake_peer_skill"
        consumers = {"fake_peer_skill.api"}
    elif name == "duplicate-spec-root-mismatch":
        repo_root = Path(__file__).resolve().parents[3]
        sources = _fixture_sources(repo_root)
        spec = SymbolSpec(
            "_attrs_to_map",
            ("fixture",),
            "ci_triage/gbs_report.py",
            "skill/tizen_qb_discover",
            declared_internal=(
                "_IframeParser.handle_starttag",
                "_ReportTableParser.handle_starttag",
            ),
        )
        REGISTERED_SKILL_ROOTS[spec.owner] = "tizen_qb_discover"
        try:
            result = _audit_one(
                sources,
                {(spec.definition, spec.name): spec},
                spec,
            )
        finally:
            del REGISTERED_SKILL_ROOTS[spec.owner]
        print(f"NEGATIVE_FIXTURE | {name} | {result.verdict}")
        expected = "skill-owned symbol defined outside its registered root"
        return 1 if any(expected in reason for reason in result.reasons) else 0
    elif name == "twin-both-name-only":
        specs = _twin_specs(Path(__file__).resolve().parents[3])
        by_name = {spec.name: spec for spec in specs}
        if len(by_name) != len(specs):
            print(
                f"NEGATIVE_FIXTURE | {name} | MISMATCH: "
                "name-only SPECS key overwrote one definition"
            )
            return 1
        print(f"NEGATIVE_FIXTURE | {name} | OK")
        return 0
    elif name == "import-binding-legacy-alias":
        _, _, legacy_a, _ = _aliased_binding_measurements()
        if legacy_a != ("fixture.consumer",):
            print(
                f"NEGATIVE_FIXTURE | {name} | MISMATCH: legacy consumers "
                f"for fixture.a:S were {legacy_a}, expected "
                "('fixture.consumer',)"
            )
            return 1
        print(f"NEGATIVE_FIXTURE | {name} | OK")
        return 0
    else:
        print(f"unknown negative fixture: {name}")
        return 2
    reasons = _skill_layer_reasons(
        "skill/tizen_convergence_judge",
        consumers,
        registered_skill_roots=registered,
    )
    verdict = "MISMATCH: " + "; ".join(reasons) if reasons else "OK"
    print(f"NEGATIVE_FIXTURE | {name} | {verdict}")
    return 1 if reasons else 0


def _fixture_sources(repo_root: Path) -> tuple[SourceFile, ...]:
    roots = (
        repo_root / "tizen-ci-triage/scripts",
        repo_root / "tizen-ci-shared/scripts",
        repo_root / "tizen-convergence-judge/scripts",
        repo_root / "tizen-qb-discover/scripts",
        repo_root / "tizen-gerrit-fetch/scripts",
    )
    return tuple(
        source
        for root in roots
        if root.is_dir()
        for source in _load_sources(root)
    )


def _synthetic_source(module: str, text: str) -> SourceFile:
    path = Path(*module.split(".")).with_suffix(".py")
    tree = ast.parse(text, filename=str(path))
    return SourceFile(
        path=path,
        relative=path.as_posix(),
        module=module,
        text=text,
        tree=tree,
        top_level=_top_level_symbols(tree),
    )


def _aliased_binding_measurements(
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    definition_a = _synthetic_source("fixture.a", "class S:\n    pass\n")
    definition_b = _synthetic_source("fixture.b", "class S:\n    pass\n")
    consumer = _synthetic_source(
        "fixture.consumer",
        "from fixture.a import S as LocalS\n\n"
        "def use():\n"
        "    return LocalS()\n",
    )
    sources = (definition_a, definition_b, consumer)
    return (
        _actual_consumers(sources, definition_a, "S"),
        _actual_consumers(sources, definition_b, "S"),
        _legacy_actual_consumers(sources, definition_a, "S"),
        _legacy_actual_consumers(sources, definition_b, "S"),
    )


def _legacy_convergence_specs(
    specs: tuple[SymbolSpec, ...],
) -> tuple[SymbolSpec, ...]:
    legacy_consumers = {
        "_primary_fingerprint": ("ci_triage.campaign_state",),
        "_error_count": ("ci_triage.campaign_state",),
        "primary_fingerprint": (),
        "error_count": (),
    }
    return tuple(
        replace(spec, declared_consumers=legacy_consumers[spec.name])
        if spec.definition == SKILL_CONVERGENCE and spec.name in legacy_consumers
        else spec
        for spec in specs
    )


def _run_binding_fixture(name: str) -> int:
    repo_root = Path(__file__).resolve().parents[3]
    if name == "regression-lock":
        sources = _fixture_sources(repo_root)
        # This lock preserves the 96-symbol topology that existed when the
        # import-binding rule landed. Skill-3's intentional old/new difference
        # is covered separately by planned-run-git.
        locked_definitions = {
            WORKSPACE,
            SHARED_WORKSPACE,
            QUICKBUILD,
            SHARED_TYPES,
            "tizen_ci_shared/env.py",
            SKILL_CONVERGENCE,
            SKILL_QB_DISCOVER,
        }
        current_specs = tuple(
            spec
            for spec in SPECS
            if isinstance(spec, SymbolSpec)
            and spec.definition in locked_definitions
        )
        legacy_specs = _legacy_convergence_specs(current_specs)
        current_by_key = {
            (spec.definition, spec.name): spec for spec in current_specs
        }
        legacy_by_key = {
            (spec.definition, spec.name): spec for spec in legacy_specs
        }
        current_results = {
            (spec.definition, spec.name): _audit_one(
                sources,
                current_by_key,
                spec,
            ).verdict
            for spec in current_specs
        }
        legacy_results = {
            (spec.definition, spec.name): _audit_one(
                sources,
                legacy_by_key,
                spec,
                consumer_finder=_legacy_actual_consumers,
            ).verdict
            for spec in legacy_specs
        }
        changed = tuple(
            key
            for key in sorted(current_results)
            if current_results[key] != legacy_results[key]
        )
        convergence = next(
            source for source in sources if source.module == "tizen_convergence_judge.convergence"
        )
        public_consumers = _actual_consumers(
            sources, convergence, "primary_fingerprint"
        )
        private_consumers = _actual_consumers(
            sources, convergence, "_primary_fingerprint"
        )
        print(
            f"BINDING_FIXTURE | {name} | symbols={len(current_results)} | "
            f"verdict_changes={len(changed)}"
        )
        print(
            "BINDING_FIXTURE | campaign-state-alias | "
            f"primary_fingerprint consumers={public_consumers} | "
            f"_primary_fingerprint consumers={private_consumers}"
        )
        expected_consumer = "ci_triage.campaign_state"
        passed = (
            not changed
            and expected_consumer in public_consumers
            and expected_consumer not in private_consumers
        )
        return 0 if passed else 1

    if name == "aliased-import":
        current_a, current_b, legacy_a, legacy_b = _aliased_binding_measurements()
        print(
            f"BINDING_FIXTURE | {name} | new A.S={current_a} | "
            f"new B.S={current_b}"
        )
        print(
            f"BINDING_FIXTURE | {name} | legacy A.S={legacy_a} | "
            f"legacy B.S={legacy_b} | OLD_VERDICT=MISMATCH"
        )
        return 0 if (
            current_a == ("fixture.consumer",)
            and current_b == ()
            and legacy_a == ()
            and legacy_b == ()
        ) else 1

    if name == "same-name-import":
        definition_a = _synthetic_source("fixture.a", "class S:\n    pass\n")
        consumer = _synthetic_source(
            "fixture.consumer",
            "from fixture.a import S as S\n\n"
            "def use():\n"
            "    return S()\n",
        )
        consumers = _actual_consumers((definition_a, consumer), definition_a, "S")
        print(
            f"BINDING_FIXTURE | {name} | A.S={consumers} | "
            "degenerate same-name case only; not alias-generalization evidence"
        )
        return 0 if consumers == ("fixture.consumer",) else 1

    if name == "planned-run-git":
        sources = _fixture_sources(repo_root)
        planned_gerrit = next(
            (
                source
                for source in sources
                if source.module == "tizen_gerrit_fetch.gerrit"
            ),
            None,
        )
        if planned_gerrit is None:
            planned_gerrit = _synthetic_source(
                "tizen_gerrit_fetch.gerrit",
                "def _run_git():\n    return None\n",
            )
            sources = (*sources, planned_gerrit)
        workspace = next(
            source for source in sources if source.module == "tizen_ci_shared.workspace"
        )
        gerrit_consumers = _actual_consumers(sources, planned_gerrit, "_run_git")
        workspace_consumers = _actual_consumers(sources, workspace, "_run_git")
        print(
            f"BINDING_FIXTURE | {name} | gerrit._run_git={gerrit_consumers} | "
            f"workspace._run_git={workspace_consumers}"
        )
        passed = (
            gerrit_consumers == ()
            and "ci_triage.verify.workspace" in workspace_consumers
        )
        return 0 if passed else 1

    print(f"unknown binding fixture: {name}")
    return 2


def _twin_specs(repo_root: Path) -> tuple[SymbolSpec, SymbolSpec]:
    extracted = (repo_root / "tizen-qb-discover/scripts/tizen_qb_discover/sources.py").is_file()
    source_definition = (
        "tizen_qb_discover/sources.py" if extracted else "ci_triage/sources.py"
    )
    source_owner = "skill/tizen_qb_discover" if extracted else "quickbuild"
    return (
        SymbolSpec(
            "_attrs_to_map",
            ("fixture",),
            source_definition,
            source_owner,
            declared_internal=("_BuildsTableParser.handle_starttag",),
        ),
        SymbolSpec(
            "_attrs_to_map",
            ("fixture",),
            "ci_triage/gbs_report.py",
            "triage-report",
            declared_internal=(
                "_IframeParser.handle_starttag",
                "_ReportTableParser.handle_starttag",
            ),
        ),
    )


def _run_key_fixture(name: str) -> int:
    repo_root = Path(__file__).resolve().parents[3]
    sources = _fixture_sources(repo_root)
    source_spec, report_spec = _twin_specs(repo_root)
    specs = (source_spec,) if name == "source-twin-only" else (source_spec, report_spec)
    if name not in {"source-twin-only", "twin-both-binary-key"}:
        print(f"unknown key fixture: {name}")
        return 2
    specs_by_key = {(spec.definition, spec.name): spec for spec in specs}
    registered_here = (
        source_spec.owner not in REGISTERED_SKILL_ROOTS
        and source_spec.owner.startswith("skill/")
    )
    if registered_here:
        REGISTERED_SKILL_ROOTS[source_spec.owner] = "tizen_qb_discover"
    try:
        results = tuple(
            _audit_one(sources, specs_by_key, spec) for spec in specs
        )
    finally:
        if registered_here:
            del REGISTERED_SKILL_ROOTS[source_spec.owner]
    for result in results:
        print(
            f"KEY_FIXTURE | {name} | {result.spec.definition}:"
            f"{result.spec.name} | consumers={result.consumers} | "
            f"internal={result.internal} | {result.verdict}"
        )
    return 1 if any(result.reasons for result in results) else 0


def main() -> int:
    if len(sys.argv) == 3 and sys.argv[1] == "--negative-fixture":
        return _run_negative_fixture(sys.argv[2])
    if len(sys.argv) == 3 and sys.argv[1] == "--key-fixture":
        return _run_key_fixture(sys.argv[2])
    if len(sys.argv) == 3 and sys.argv[1] == "--binding-fixture":
        return _run_binding_fixture(sys.argv[2])
    if len(sys.argv) != 1:
        print(
            "usage: symbol_audit.py "
            "[--negative-fixture skill-owner-shared-consumer|"
            "skill-owner-peer-skill-consumer|duplicate-spec-root-mismatch|"
            "twin-both-name-only|import-binding-legacy-alias|"
            "--key-fixture source-twin-only|twin-both-binary-key|"
            "--binding-fixture regression-lock|aliased-import|"
            "same-name-import|planned-run-git]"
        )
        return 2
    repo_root = Path(__file__).resolve().parents[3]
    return run(repo_root)


if __name__ == "__main__":
    sys.exit(main())
