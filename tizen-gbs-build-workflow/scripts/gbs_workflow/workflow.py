"""GbsBuildWorkflow orchestration entrypoint."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gbs_analyzer.packet_assembler import TokenEstimator
from gbs_build_skill.runner import BuildOptions, BuildResult, run_gbs_build

from gbs_workflow.suggesters import DEFAULT_SUGGESTERS, SuggesterBase, Suggestion

DEFAULT_TIMEOUT_SECONDS = 1800
DEFAULT_MAX_TOKENS = 1800
EXIT_WORKFLOW_ERROR = 1
EXIT_ARGS = 2
EXIT_PACKET_UNREADABLE = 3
PATCH_CONTEXT_KINDS = frozenset({"compiler", "werror"})

BuildRunner = Callable[[BuildOptions], BuildResult]
SubprocessRunner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class WorkflowOptions:
    """Options for one workflow invocation."""

    conf: Path
    arch: str
    src_root: Path
    output_dir: Path
    include_all: bool = False
    timeout: int = DEFAULT_TIMEOUT_SECONDS
    max_tokens: int = DEFAULT_MAX_TOKENS


@dataclass(frozen=True)
class WorkflowResult:
    """Result paths and status from one workflow invocation."""

    exit_code: int
    build_exit_code: int
    build_succeeded: bool
    output_dir: Path
    summary_path: Path
    compiler_log_path: Path
    analysis_log_path: Path | None = None
    analyzer_output_dir: Path | None = None
    evidence_packet_path: Path | None = None
    evidence_markdown_path: Path | None = None
    patch_context_dir: Path | None = None
    patch_context_path: Path | None = None
    patch_context_error: str | None = None
    suggestion_paths: list[Path] = field(default_factory=list)
    downstream_token_estimate: dict[str, Any] | None = None
    error: str | None = None


@dataclass(frozen=True)
class PatchContextResult:
    """Result of the optional patch-suggest context stage."""

    triggered: bool
    output_dir: Path | None = None
    context_path: Path | None = None
    status: str | None = None
    error: str | None = None


def run_workflow(
    options: WorkflowOptions,
    *,
    suggesters: Sequence[SuggesterBase] = DEFAULT_SUGGESTERS,
    build_runner: BuildRunner = run_gbs_build,
    subprocess_runner: SubprocessRunner = subprocess.run,
    python_executable: str = sys.executable,
    analyzer_extra_pythonpath: Sequence[str | Path] = (),
    patch_suggest_extra_pythonpath: Sequence[str | Path] = (),
) -> WorkflowResult:
    """Run build, analyze failures, and write suggestion artifacts."""

    options.output_dir.mkdir(parents=True, exist_ok=True)
    suggestions_dir = options.output_dir / "suggestions"
    suggestions_dir.mkdir(parents=True, exist_ok=True)
    compiler_log = options.output_dir / "compiler.log"
    summary_path = options.output_dir / "workflow_summary.md"

    build_result = build_runner(
        BuildOptions(
            conf=options.conf,
            arch=options.arch,
            output_log=compiler_log,
            include_all=options.include_all,
            timeout=options.timeout,
            cwd=options.src_root,
        )
    )
    if build_result.exit_code == 0:
        summary_text, downstream_tokens = render_workflow_summary_with_tokens(
            summary_path=summary_path,
            build_status="success",
            build_exit_code=0,
            packet=None,
            suggestions=[],
            suggestion_files=[],
        )
        summary_path.write_text(summary_text, encoding="utf-8")
        return WorkflowResult(
            exit_code=0,
            build_exit_code=0,
            build_succeeded=True,
            output_dir=options.output_dir,
            summary_path=summary_path,
            compiler_log_path=compiler_log,
            downstream_token_estimate=downstream_tokens,
        )

    analysis_log = build_result.analysis_log_path or build_result.log_path
    analyzer_dir = options.output_dir / "analyzer_output"
    analyzer_dir.mkdir(parents=True, exist_ok=True)
    analyzer_command = [
        python_executable,
        "-m",
        "gbs_analyzer",
        "analyze",
        str(analysis_log),
        "--src-root",
        str(options.src_root),
        "--max-tokens",
        str(options.max_tokens),
        "--output-dir",
        str(analyzer_dir),
    ]
    subprocess_kwargs: dict[str, object] = {"check": True, "text": True}
    analyzer_env = build_analyzer_subprocess_env(analyzer_extra_pythonpath)
    if analyzer_env is not None:
        subprocess_kwargs["env"] = analyzer_env
    try:
        subprocess_runner(analyzer_command, **subprocess_kwargs)
    except subprocess.CalledProcessError as exc:
        summary_text, downstream_tokens = render_workflow_summary_with_tokens(
            summary_path=summary_path,
            build_status=f"failed (exit {build_result.exit_code})",
            build_exit_code=build_result.exit_code,
            packet=None,
            suggestions=[],
            suggestion_files=[],
            error=f"gbs_analyzer exited with {exc.returncode}",
        )
        summary_path.write_text(summary_text, encoding="utf-8")
        return WorkflowResult(
            exit_code=EXIT_WORKFLOW_ERROR,
            build_exit_code=build_result.exit_code,
            build_succeeded=False,
            output_dir=options.output_dir,
            summary_path=summary_path,
            compiler_log_path=compiler_log,
            analysis_log_path=analysis_log,
            analyzer_output_dir=analyzer_dir,
            downstream_token_estimate=downstream_tokens,
            error=f"gbs_analyzer exited with {exc.returncode}",
        )

    packet_path = analyzer_dir / "evidence_packet.json"
    markdown_path = analyzer_dir / "evidence_packet.md"
    try:
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        summary_text, downstream_tokens = render_workflow_summary_with_tokens(
            summary_path=summary_path,
            build_status=f"failed (exit {build_result.exit_code})",
            build_exit_code=build_result.exit_code,
            packet=None,
            suggestions=[],
            suggestion_files=[],
            error=f"cannot read evidence_packet.json: {exc}",
        )
        summary_path.write_text(summary_text, encoding="utf-8")
        return WorkflowResult(
            exit_code=EXIT_PACKET_UNREADABLE,
            build_exit_code=build_result.exit_code,
            build_succeeded=False,
            output_dir=options.output_dir,
            summary_path=summary_path,
            compiler_log_path=compiler_log,
            analysis_log_path=analysis_log,
            analyzer_output_dir=analyzer_dir,
            evidence_packet_path=packet_path,
            evidence_markdown_path=markdown_path,
            downstream_token_estimate=downstream_tokens,
            error=f"cannot read evidence_packet.json: {exc}",
        )

    suggestions = collect_suggestions(packet, options.src_root, suggesters)
    patch_context = maybe_write_patch_context(
        packet=packet,
        evidence_packet_path=packet_path,
        src_root=options.src_root,
        output_dir=options.output_dir / "patch_context",
        subprocess_runner=subprocess_runner,
        python_executable=python_executable,
        extra_pythonpath=patch_suggest_extra_pythonpath,
    )
    visible_suggestions = filter_suggestions_for_patch_context(suggestions, patch_context)
    suggestion_files = write_suggestions(visible_suggestions, suggestions_dir)
    summary_text, downstream_tokens = render_workflow_summary_with_tokens(
        summary_path=summary_path,
        evidence_markdown_path=markdown_path,
        analyzer_output_dir=analyzer_dir,
        build_status=f"failed (exit {build_result.exit_code})",
        build_exit_code=build_result.exit_code,
        packet=packet,
        suggestions=visible_suggestions,
        suggestion_files=suggestion_files,
        patch_context_path=patch_context.context_path,
        patch_context_status=patch_context.status,
        patch_context_error=patch_context.error,
    )
    summary_path.write_text(summary_text, encoding="utf-8")
    return WorkflowResult(
        exit_code=build_result.exit_code,
        build_exit_code=build_result.exit_code,
        build_succeeded=False,
        output_dir=options.output_dir,
        summary_path=summary_path,
        compiler_log_path=compiler_log,
        analysis_log_path=analysis_log,
        analyzer_output_dir=analyzer_dir,
        evidence_packet_path=packet_path,
        evidence_markdown_path=markdown_path,
        patch_context_dir=patch_context.output_dir if patch_context.triggered else None,
        patch_context_path=patch_context.context_path,
        patch_context_error=patch_context.error,
        suggestion_paths=suggestion_files,
        downstream_token_estimate=downstream_tokens,
    )


def collect_suggestions(
    packet: dict[str, Any],
    src_root: Path,
    suggesters: Sequence[SuggesterBase],
) -> list[Suggestion]:
    """Run matching suggesters and return generated suggestions."""

    suggestions: list[Suggestion] = []
    for suggester in suggesters:
        if suggester.matches(packet):
            suggestions.extend(suggester.generate(packet, src_root))
    return suggestions


def filter_suggestions_for_patch_context(
    suggestions: Sequence[Suggestion],
    patch_context: PatchContextResult,
) -> list[Suggestion]:
    """Hide generic fallback once patch-suggest produced patch-ready context."""

    if not patch_context_has_patch_ready_context(patch_context):
        return list(suggestions)
    return [suggestion for suggestion in suggestions if suggestion.suggester != "fallback"]


def patch_context_has_patch_ready_context(patch_context: PatchContextResult) -> bool:
    """Return true only for patch-suggest statuses that contain patch-ready context."""

    return bool(patch_context.status and patch_context.status.endswith("_context_available"))


def maybe_write_patch_context(
    *,
    packet: dict[str, Any],
    evidence_packet_path: Path,
    src_root: Path,
    output_dir: Path,
    subprocess_runner: SubprocessRunner,
    python_executable: str,
    extra_pythonpath: Sequence[str | Path],
) -> PatchContextResult:
    """Run patch-suggest for source diagnostic packets as a non-fatal optional stage."""

    if primary_error_kind(packet) not in PATCH_CONTEXT_KINDS:
        return PatchContextResult(triggered=False)

    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        python_executable,
        "-m",
        "gbs_patch_suggest",
        "--evidence",
        str(evidence_packet_path),
        "--src-root",
        str(src_root),
        "--output-dir",
        str(output_dir),
    ]
    subprocess_kwargs: dict[str, object] = {"check": True, "text": True}
    patch_env = build_extra_pythonpath_env(extra_pythonpath)
    if patch_env is not None:
        subprocess_kwargs["env"] = patch_env

    try:
        subprocess_runner(command, **subprocess_kwargs)
    except subprocess.CalledProcessError as exc:
        return PatchContextResult(
            triggered=True,
            output_dir=output_dir,
            error=f"gbs_patch_suggest exited with {exc.returncode}",
        )

    context_path = output_dir / "context.md"
    if not context_path.is_file():
        return PatchContextResult(
            triggered=True,
            output_dir=output_dir,
            error="gbs_patch_suggest did not write patch_context/context.md",
        )
    return PatchContextResult(
        triggered=True,
        output_dir=output_dir,
        context_path=context_path,
        status=read_patch_context_status(output_dir),
    )


def read_patch_context_status(output_dir: Path) -> str | None:
    """Read patch-suggest meta status when available."""

    meta_path = output_dir / "meta.json"
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(meta, dict):
        return None
    status = meta.get("status")
    return str(status) if status else None


def primary_error_kind(packet: dict[str, Any]) -> str:
    """Return the primary error kind from an analyzer packet."""

    value = packet.get("primary_error")
    if not isinstance(value, dict):
        return ""
    return str(value.get("kind") or "")


def build_analyzer_subprocess_env(extra_pythonpath: Sequence[str | Path]) -> dict[str, str] | None:
    """Return a subprocess env with extra Python paths prepended for analyzer calls."""

    return build_extra_pythonpath_env(extra_pythonpath)


def build_extra_pythonpath_env(extra_pythonpath: Sequence[str | Path]) -> dict[str, str] | None:
    """Return a subprocess env with extra Python paths prepended."""

    if not extra_pythonpath:
        return None
    env = os.environ.copy()
    entries = [str(Path(path)) for path in extra_pythonpath]
    existing = env.get("PYTHONPATH")
    if existing:
        entries.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(entries)
    return env


def write_suggestions(suggestions: Sequence[Suggestion], suggestions_dir: Path) -> list[Path]:
    """Write suggestion patch and markdown files."""

    suggestions_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for index, suggestion in enumerate(suggestions, start=1):
        prefix = f"{index:03d}_{suggestion.suggester}_{slugify(suggestion.title)}"
        if suggestion.patch_content is not None:
            patch_path = suggestions_dir / f"{prefix}.patch"
            patch_path.write_text(suggestion.patch_content, encoding="utf-8")
            written.append(patch_path)
        markdown_path = suggestions_dir / f"{prefix}.md"
        markdown_path.write_text(render_suggestion_markdown(suggestion), encoding="utf-8")
        written.append(markdown_path)
    return written


def render_suggestion_markdown(suggestion: Suggestion) -> str:
    """Render one suggestion as user-readable markdown."""

    patch_state = "Yes" if suggestion.patch_content is not None else "No"
    target_files = "\n".join(f"- `{path}`" for path in suggestion.target_files) or "- None"
    risks = "\n".join(f"- {risk}" for risk in suggestion.risks) or "- None"
    manual_steps = "\n".join(
        f"{idx}. {step}" for idx, step in enumerate(suggestion.manual_steps or [], 1)
    )
    if not manual_steps:
        manual_steps = "None"
    return (
        f"# {suggestion.title}\n\n"
        f"**Suggester**: {suggestion.suggester}\n"
        f"**Confidence**: {suggestion.confidence}\n"
        f"**Has Patch**: {patch_state}\n\n"
        "## Description\n\n"
        f"{suggestion.description}\n\n"
        "## Target Files\n\n"
        f"{target_files}\n\n"
        "## Risks\n\n"
        f"{risks}\n\n"
        "## Manual Steps\n\n"
        f"{manual_steps}\n"
    )


def render_workflow_summary(
    *,
    build_status: str,
    build_exit_code: int,
    packet: dict[str, Any] | None,
    suggestions: Sequence[Suggestion],
    suggestion_files: Sequence[Path],
    error: str | None = None,
    patch_context_path: Path | None = None,
    patch_context_status: str | None = None,
    patch_context_error: str | None = None,
) -> str:
    """Render the workflow summary markdown."""

    failed_phase = packet.get("failed_phase") if packet else None
    primary_error = packet.get("primary_error") if packet else None
    root_cause = "n/a"
    if isinstance(primary_error, dict):
        root_cause = f"{primary_error.get('kind', 'unknown')} ({primary_error.get('message', '')})"
    rows = []
    for index, suggestion in enumerate(suggestions, start=1):
        has_patch = "Yes" if suggestion.patch_content is not None else "No"
        rows.append(
            f"| {index:03d} | {suggestion.suggester} | {suggestion.title} | "
            f"{suggestion.confidence} | {has_patch} |"
        )
    if not rows:
        rows.append("| - | - | No automated suggestion generated | - | No |")

    files = "\n".join(f"- `{path}`" for path in suggestion_files) or "- None"
    error_block = f"\n**Workflow error**: {error}\n" if error else ""
    patch_context_block = render_patch_context_summary(
        patch_context_path=patch_context_path,
        patch_context_status=patch_context_status,
        patch_context_error=patch_context_error,
    )
    return (
        "# Workflow Summary\n\n"
        f"**Build status**: {build_status}\n"
        f"**Build exit code**: {build_exit_code}\n"
        f"**Failed phase**: {failed_phase or 'n/a'}\n"
        f"**Top-1 root cause**: {root_cause}\n"
        f"{error_block}\n"
        f"{patch_context_block}"
        "## Suggestions Generated\n\n"
        "| # | Suggester | Title | Confidence | Has Patch |\n"
        "|---|-----------|-------|------------|-----------|\n"
        + "\n".join(rows)
        + "\n\n"
        "## Files Written\n\n"
        f"{files}\n\n"
        "## What to do next\n\n"
        "1. Read `analyzer_output/evidence_packet.md` for full diagnosis.\n"
        "2. If `patch_context/context.md` exists, read it before generic "
        "advisory suggestions; patch-suggest context is more specific.\n"
        "3. Read each `suggestions/*.md` for additional proposed fixes.\n"
        "4. If `patch_context/context.md` exists, generate candidate "
        "patch files as the outer assistant. Do not apply them automatically.\n"
        "5. For patch suggestions: run `git apply suggestions/<file>.patch` if you accept.\n"
        "6. For advisory suggestions: follow manual_steps in the .md.\n"
        "7. Re-run `python -m gbs_workflow` after applying changes.\n"
    )


def render_patch_context_summary(
    *,
    patch_context_path: Path | None,
    patch_context_status: str | None,
    patch_context_error: str | None,
) -> str:
    """Render the optional patch-suggest context status."""

    if patch_context_path is not None:
        status_line = (
            f"**Patch-suggest status**: `{patch_context_status}`\n\n"
            if patch_context_status
            else ""
        )
        priority_line = (
            "Patch-suggest produced patch-ready context. Read this before generic "
            "advisory suggestions.\n\n"
            if patch_context_status and patch_context_status.endswith("_context_available")
            else ""
        )
        return (
            "## Patch Context\n\n"
            f"Patch generation context was written to `{patch_context_path}`.\n\n"
            f"{status_line}"
            f"{priority_line}"
            "The workflow only generated context. It did not generate a final patch, "
            "did not apply any patch, and did not modify the source tree. The outer "
            "Claude/Cline assistant should read this context and prepare candidate "
            "patch files for user review.\n\n"
        )
    if patch_context_error:
        return (
            "## Patch Context\n\n"
            "Patch context generation was skipped or unavailable.\n\n"
            f"Reason: {patch_context_error}\n\n"
            "This is non-fatal: the build analysis and workflow suggestions above are "
            "still valid.\n\n"
        )
    return ""


def render_workflow_summary_with_tokens(
    *,
    summary_path: Path,
    evidence_markdown_path: Path | None = None,
    suggestion_files: Sequence[Path] = (),
    patch_context_path: Path | None = None,
    patch_context_status: str | None = None,
    analyzer_output_dir: Path | None = None,
    estimator: TokenEstimator | None = None,
    **summary_kwargs: Any,
) -> tuple[str, dict[str, Any]]:
    """Render the workflow summary plus Claude-facing downstream token estimates."""

    active_estimator = estimator or TokenEstimator()
    base_summary = render_workflow_summary(
        suggestion_files=suggestion_files,
        patch_context_path=patch_context_path,
        patch_context_status=patch_context_status,
        **summary_kwargs,
    )
    section = ""
    estimate = estimate_workflow_downstream_tokens(
        summary_text=base_summary,
        summary_path=summary_path,
        evidence_markdown_path=evidence_markdown_path,
        suggestion_files=suggestion_files,
        patch_context_path=patch_context_path,
        analyzer_output_dir=analyzer_output_dir,
        estimator=active_estimator,
    )
    for _ in range(3):
        section = render_downstream_token_section(estimate)
        rendered = base_summary + section
        estimate = estimate_workflow_downstream_tokens(
            summary_text=rendered,
            summary_path=summary_path,
            evidence_markdown_path=evidence_markdown_path,
            suggestion_files=suggestion_files,
            patch_context_path=patch_context_path,
            analyzer_output_dir=analyzer_output_dir,
            estimator=active_estimator,
        )
    return base_summary + render_downstream_token_section(estimate), estimate


def estimate_workflow_downstream_tokens(
    *,
    summary_text: str,
    summary_path: Path,
    evidence_markdown_path: Path | None,
    suggestion_files: Sequence[Path],
    patch_context_path: Path | None,
    analyzer_output_dir: Path | None,
    estimator: TokenEstimator,
) -> dict[str, Any]:
    """Estimate markdown material that workflow recommends Claude read."""

    files: list[dict[str, Any]] = [
        {
            "path": str(summary_path),
            "role": "workflow_summary",
            "tokens": estimator.estimate_text(summary_text),
            "included_in_total": True,
        }
    ]
    if evidence_markdown_path is not None and evidence_markdown_path.is_file():
        files.append(
            {
                "path": str(evidence_markdown_path),
                "role": "evidence_packet_md",
                "tokens": _estimate_file_tokens(evidence_markdown_path, estimator),
                "included_in_total": True,
            }
        )
    for path in sorted(suggestion_files):
        if path.suffix == ".md" and path.is_file():
            files.append(
                {
                    "path": str(path),
                    "role": "suggestion_md",
                    "tokens": _estimate_file_tokens(path, estimator),
                    "included_in_total": True,
                }
            )
    if patch_context_path is not None and patch_context_path.is_file():
        files.append(
            {
                "path": str(patch_context_path),
                "role": "patch_context_md",
                "tokens": _estimate_file_tokens(patch_context_path, estimator),
                "included_in_total": True,
            }
        )

    total = sum(int(file["tokens"]) for file in files if file["included_in_total"])
    return {
        "scope": (
            "Estimated tokens of material this workflow feeds to Claude "
            "(recommended reading). Actual Claude consumption also includes any "
            "source files Claude reads on its own."
        ),
        "usage_note": (
            "Compare this baseline with Cline/client actual token usage; the "
            "difference approximates extra material Claude read outside workflow outputs."
        ),
        "estimate_method": estimator.method,
        "total_claude_facing_tokens": total,
        "source_snippets_tokens": _read_source_snippets_tokens(analyzer_output_dir),
        "files": files,
    }


def render_downstream_token_section(estimate: dict[str, Any]) -> str:
    """Render workflow downstream token estimates as a markdown section."""

    rows = [
        f"| `{file['path']}` | {file['role']} | {file['tokens']} |"
        for file in estimate.get("files", [])
    ]
    if not rows:
        rows.append("| - | - | 0 |")
    source_snippets = estimate.get("source_snippets_tokens")
    source_line = (
        f"\nSource snippets subset from analyzer perf_report: {source_snippets} tokens "
        "(already included in evidence packet estimate).\n"
        if source_snippets is not None
        else ""
    )
    return (
        "\n## Downstream Token Estimate\n\n"
        f"{estimate['scope']}\n\n"
        f"{estimate['usage_note']}\n\n"
        f"**Estimate method**: {estimate['estimate_method']}\n"
        f"**Total Claude-facing tokens**: {estimate['total_claude_facing_tokens']}\n"
        f"{source_line}\n"
        "| File | Role | Estimated Tokens |\n"
        "|------|------|------------------|\n"
        + "\n".join(rows)
        + "\n"
    )


def _estimate_file_tokens(path: Path, estimator: TokenEstimator) -> int:
    try:
        return estimator.estimate_text(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return 0


def _read_source_snippets_tokens(analyzer_output_dir: Path | None) -> int | None:
    if analyzer_output_dir is None:
        return None
    perf_path = analyzer_output_dir / "perf_report.json"
    try:
        report = json.loads(perf_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    value = (
        report.get("tokens", {})
        .get("by_section", {})
        .get("source_snippets")
    )
    return int(value) if isinstance(value, int) else None


def slugify(value: str) -> str:
    """Return a short lowercase slug for file names."""

    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return slug[:48] or "suggestion"


def build_arg_parser() -> argparse.ArgumentParser:
    """Create the workflow CLI parser."""

    parser = argparse.ArgumentParser(
        prog="python -m gbs_workflow",
        description="Run gbs, analyze failures, and generate suggestion files.",
    )
    parser.add_argument("--conf", required=True, type=Path)
    parser.add_argument("--arch", required=True)
    parser.add_argument("--include-all", action="store_true")
    parser.add_argument("--src-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    return parser


def main(
    argv: list[str] | None = None,
    *,
    analyzer_extra_pythonpath: Sequence[str | Path] = (),
    patch_suggest_extra_pythonpath: Sequence[str | Path] = (),
) -> int:
    """CLI entrypoint for `python -m gbs_workflow`."""

    parser = build_arg_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else EXIT_ARGS
    result = run_workflow(
        WorkflowOptions(
            conf=args.conf,
            arch=args.arch,
            include_all=args.include_all,
            src_root=args.src_root,
            output_dir=args.output_dir,
            timeout=args.timeout,
        ),
        analyzer_extra_pythonpath=analyzer_extra_pythonpath,
        patch_suggest_extra_pythonpath=patch_suggest_extra_pythonpath,
    )
    print(f"workflow summary: {result.summary_path}", file=sys.stderr)
    if result.downstream_token_estimate is not None:
        total = result.downstream_token_estimate.get("total_claude_facing_tokens")
        print(f"workflow downstream tokens: {total} estimated", file=sys.stderr)
    return result.exit_code
