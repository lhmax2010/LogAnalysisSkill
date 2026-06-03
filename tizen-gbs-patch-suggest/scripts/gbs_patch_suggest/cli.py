"""CLI for tizen-gbs-patch-suggest."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from gbs_patch_suggest.analyzer_runner import (
    discover_analyzer_pythonpath,
    run_analyzer_for_buildlog,
)
from gbs_patch_suggest.formatter import FormatPatchOptions, format_patch
from gbs_patch_suggest.ingest import extract_first_diagnostic, load_evidence_packet
from gbs_patch_suggest.render import write_outputs
from gbs_patch_suggest.resolver import resolve_context

EXIT_SUCCESS = 0
EXIT_FATAL = 1
EXIT_EVIDENCE_UNREADABLE = 3
DEFAULT_OUTPUT_DIR = Path(".gbs_patch_suggest")


@dataclass(frozen=True)
class PatchSuggestOptions:
    evidence_path: Path | None = None
    buildlog_path: Path | None = None
    output_dir: Path = DEFAULT_OUTPUT_DIR
    src_root: Path | None = None
    analyzer_extra_pythonpath: tuple[Path, ...] = ()


@dataclass(frozen=True)
class PatchSuggestResult:
    exit_code: int
    output_dir: Path
    context_path: Path | None = None
    meta_path: Path | None = None
    status: str | None = None
    error: str | None = None


def run_patch_suggest(options: PatchSuggestOptions) -> PatchSuggestResult:
    """Generate patch context from an analyzer Evidence Packet."""

    evidence_path = options.evidence_path
    if evidence_path is None:
        if options.buildlog_path is None:
            return PatchSuggestResult(
                exit_code=EXIT_EVIDENCE_UNREADABLE,
                output_dir=options.output_dir,
                error="one of --evidence or --buildlog is required",
            )
        analyzer_result = run_analyzer_for_buildlog(
            options.buildlog_path,
            output_dir=options.output_dir / "analyzer_output",
            src_root=options.src_root,
            extra_pythonpath=options.analyzer_extra_pythonpath,
        )
        if analyzer_result.error:
            return PatchSuggestResult(
                exit_code=analyzer_result.exit_code,
                output_dir=options.output_dir,
                error=analyzer_result.error,
            )
        evidence_path = analyzer_result.evidence_path

    if not evidence_path.is_file():
        return PatchSuggestResult(
            exit_code=EXIT_EVIDENCE_UNREADABLE,
            output_dir=options.output_dir,
            error=f"evidence is not readable: {evidence_path}",
        )

    try:
        packet = load_evidence_packet(evidence_path)
        diagnostic = extract_first_diagnostic(packet)
        resolved = resolve_context(diagnostic, src_root=options.src_root)
        outputs = write_outputs(
            resolved,
            options.output_dir,
            evidence_path=evidence_path,
            buildlog_path=options.buildlog_path,
        )
    except (OSError, ValueError) as exc:
        return PatchSuggestResult(
            exit_code=EXIT_FATAL,
            output_dir=options.output_dir,
            error=str(exc),
        )

    return PatchSuggestResult(
        exit_code=EXIT_SUCCESS,
        output_dir=options.output_dir,
        context_path=outputs["context_md"],
        meta_path=outputs["meta_json"],
        status=resolved.status,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gbs_patch_suggest",
        description="Prepare LLM-ready patch context from analyzer Evidence Packet JSON.",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--evidence",
        type=Path,
        help="Path to analyzer evidence_packet.json.",
    )
    source.add_argument(
        "--buildlog",
        type=Path,
        help="Path to buildlog. Runs gbs_analyzer first and consumes its evidence output.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for context.md and meta.json. Defaults to ./.gbs_patch_suggest.",
    )
    parser.add_argument(
        "--src-root",
        type=Path,
        default=None,
        help="Optional source root for suffix-based source context search.",
    )
    return parser


def build_format_patch_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gbs_patch_suggest format-patch",
        description="Format an explicit edit spec into a git-apply-compatible patch.",
    )
    parser.add_argument(
        "--src-root",
        type=Path,
        required=True,
        help="Source root used to validate edit paths and run git apply --check.",
    )
    parser.add_argument(
        "--edit-spec",
        type=Path,
        required=True,
        help="Path to gbs_patch_suggest edit-spec JSON.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output .patch file path.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run git apply --check against src-root before writing output.",
    )
    return parser


def main(
    argv: list[str] | None = None,
    *,
    stderr: TextIO = sys.stderr,
    analyzer_extra_pythonpath: tuple[Path, ...] = (),
) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "format-patch":
        return _main_format_patch(argv[1:], stderr=stderr)

    parser = build_parser()
    args = parser.parse_args(argv)
    src_root = args.src_root.resolve() if args.src_root is not None else None
    extra_pythonpath = analyzer_extra_pythonpath
    if args.buildlog is not None and not extra_pythonpath:
        try:
            extra_pythonpath = discover_analyzer_pythonpath()
        except RuntimeError as exc:
            print(f"gbs_patch_suggest: {exc}", file=stderr)
            return EXIT_FATAL

    result = run_patch_suggest(
        PatchSuggestOptions(
            evidence_path=args.evidence,
            buildlog_path=args.buildlog,
            output_dir=args.output_dir,
            src_root=src_root,
            analyzer_extra_pythonpath=extra_pythonpath,
        )
    )
    if result.error:
        print(f"gbs_patch_suggest: {result.error}", file=stderr)
        return result.exit_code

    print(f"gbs_patch_suggest: context written to {result.context_path}", file=stderr)
    print(f"gbs_patch_suggest: meta written to {result.meta_path}", file=stderr)
    print(f"gbs_patch_suggest: status {result.status}", file=stderr)
    return result.exit_code


def _main_format_patch(argv: list[str], *, stderr: TextIO) -> int:
    parser = build_format_patch_parser()
    args = parser.parse_args(argv)
    result = format_patch(
        FormatPatchOptions(
            src_root=args.src_root,
            edit_spec=args.edit_spec,
            output=args.output,
            check=args.check,
        )
    )
    if result.error:
        print(
            f"gbs_patch_suggest: format-patch {result.error_code}: {result.error}",
            file=stderr,
        )
        return result.exit_code
    print(f"gbs_patch_suggest: patch written to {result.output_path}", file=stderr)
    if result.check_passed:
        print("gbs_patch_suggest: git apply --check passed", file=stderr)
    return result.exit_code
