"""GbsBuildWorkflow orchestration entrypoint."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gbs_build_skill.runner import BuildOptions, BuildResult, run_gbs_build
from gbs_workflow.suggesters import DEFAULT_SUGGESTERS, SuggesterBase, Suggestion

DEFAULT_TIMEOUT_SECONDS = 1800
DEFAULT_MAX_TOKENS = 1800
EXIT_WORKFLOW_ERROR = 1
EXIT_ARGS = 2
EXIT_PACKET_UNREADABLE = 3

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
    analyzer_output_dir: Path | None = None
    evidence_packet_path: Path | None = None
    evidence_markdown_path: Path | None = None
    suggestion_paths: list[Path] = field(default_factory=list)
    error: str | None = None


def run_workflow(
    options: WorkflowOptions,
    *,
    suggesters: Sequence[SuggesterBase] = DEFAULT_SUGGESTERS,
    build_runner: BuildRunner = run_gbs_build,
    subprocess_runner: SubprocessRunner = subprocess.run,
    python_executable: str = sys.executable,
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
        summary_path.write_text(
            render_workflow_summary(
                build_status="success",
                build_exit_code=0,
                packet=None,
                suggestions=[],
                suggestion_files=[],
            ),
            encoding="utf-8",
        )
        return WorkflowResult(
            exit_code=0,
            build_exit_code=0,
            build_succeeded=True,
            output_dir=options.output_dir,
            summary_path=summary_path,
            compiler_log_path=compiler_log,
        )

    analyzer_dir = options.output_dir / "analyzer_output"
    analyzer_dir.mkdir(parents=True, exist_ok=True)
    analyzer_command = [
        python_executable,
        "-m",
        "gbs_analyzer",
        "analyze",
        str(compiler_log),
        "--src-root",
        str(options.src_root),
        "--max-tokens",
        str(options.max_tokens),
        "--output-dir",
        str(analyzer_dir),
    ]
    try:
        subprocess_runner(analyzer_command, check=True, text=True)
    except subprocess.CalledProcessError as exc:
        summary_path.write_text(
            render_workflow_summary(
                build_status=f"failed (exit {build_result.exit_code})",
                build_exit_code=build_result.exit_code,
                packet=None,
                suggestions=[],
                suggestion_files=[],
                error=f"gbs_analyzer exited with {exc.returncode}",
            ),
            encoding="utf-8",
        )
        return WorkflowResult(
            exit_code=EXIT_WORKFLOW_ERROR,
            build_exit_code=build_result.exit_code,
            build_succeeded=False,
            output_dir=options.output_dir,
            summary_path=summary_path,
            compiler_log_path=compiler_log,
            analyzer_output_dir=analyzer_dir,
            error=f"gbs_analyzer exited with {exc.returncode}",
        )

    packet_path = analyzer_dir / "evidence_packet.json"
    markdown_path = analyzer_dir / "evidence_packet.md"
    try:
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        summary_path.write_text(
            render_workflow_summary(
                build_status=f"failed (exit {build_result.exit_code})",
                build_exit_code=build_result.exit_code,
                packet=None,
                suggestions=[],
                suggestion_files=[],
                error=f"cannot read evidence_packet.json: {exc}",
            ),
            encoding="utf-8",
        )
        return WorkflowResult(
            exit_code=EXIT_PACKET_UNREADABLE,
            build_exit_code=build_result.exit_code,
            build_succeeded=False,
            output_dir=options.output_dir,
            summary_path=summary_path,
            compiler_log_path=compiler_log,
            analyzer_output_dir=analyzer_dir,
            evidence_packet_path=packet_path,
            evidence_markdown_path=markdown_path,
            error=f"cannot read evidence_packet.json: {exc}",
        )

    suggestions = collect_suggestions(packet, options.src_root, suggesters)
    suggestion_files = write_suggestions(suggestions, suggestions_dir)
    summary_path.write_text(
        render_workflow_summary(
            build_status=f"failed (exit {build_result.exit_code})",
            build_exit_code=build_result.exit_code,
            packet=packet,
            suggestions=suggestions,
            suggestion_files=suggestion_files,
        ),
        encoding="utf-8",
    )
    return WorkflowResult(
        exit_code=build_result.exit_code,
        build_exit_code=build_result.exit_code,
        build_succeeded=False,
        output_dir=options.output_dir,
        summary_path=summary_path,
        compiler_log_path=compiler_log,
        analyzer_output_dir=analyzer_dir,
        evidence_packet_path=packet_path,
        evidence_markdown_path=markdown_path,
        suggestion_paths=suggestion_files,
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
    return (
        "# Workflow Summary\n\n"
        f"**Build status**: {build_status}\n"
        f"**Build exit code**: {build_exit_code}\n"
        f"**Failed phase**: {failed_phase or 'n/a'}\n"
        f"**Top-1 root cause**: {root_cause}\n"
        f"{error_block}\n"
        "## Suggestions Generated\n\n"
        "| # | Suggester | Title | Confidence | Has Patch |\n"
        "|---|-----------|-------|------------|-----------|\n"
        + "\n".join(rows)
        + "\n\n"
        "## Files Written\n\n"
        f"{files}\n\n"
        "## What to do next\n\n"
        "1. Read `analyzer_output/evidence_packet.md` for full diagnosis.\n"
        "2. Read each `suggestions/*.md` for proposed fixes.\n"
        "3. For patch suggestions: run `git apply suggestions/<file>.patch` if you accept.\n"
        "4. For advisory suggestions: follow manual_steps in the .md.\n"
        "5. Re-run `python -m gbs_workflow` after applying changes.\n"
    )


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


def main(argv: list[str] | None = None) -> int:
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
        )
    )
    print(f"workflow summary: {result.summary_path}", file=sys.stderr)
    return result.exit_code
