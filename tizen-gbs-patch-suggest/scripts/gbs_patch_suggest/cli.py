"""CLI for tizen-gbs-patch-suggest PS-M1."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from gbs_patch_suggest.ingest import extract_first_diagnostic, load_evidence_packet
from gbs_patch_suggest.render import write_outputs
from gbs_patch_suggest.resolver import resolve_context

EXIT_SUCCESS = 0
EXIT_FATAL = 1
EXIT_ARGS = 2
EXIT_EVIDENCE_UNREADABLE = 3
DEFAULT_OUTPUT_DIR = Path(".gbs_patch_suggest")


@dataclass(frozen=True)
class PatchSuggestOptions:
    evidence_path: Path
    output_dir: Path = DEFAULT_OUTPUT_DIR
    src_root: Path | None = None


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

    if not options.evidence_path.is_file():
        return PatchSuggestResult(
            exit_code=EXIT_EVIDENCE_UNREADABLE,
            output_dir=options.output_dir,
            error=f"evidence is not readable: {options.evidence_path}",
        )

    try:
        packet = load_evidence_packet(options.evidence_path)
        diagnostic = extract_first_diagnostic(packet)
        resolved = resolve_context(diagnostic, src_root=options.src_root)
        outputs = write_outputs(resolved, options.output_dir)
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
    parser.add_argument(
        "--evidence",
        required=True,
        type=Path,
        help="Path to analyzer evidence_packet.json. PS-M1 supports evidence input only.",
    )
    parser.add_argument(
        "--src-root",
        type=Path,
        default=None,
        help="Optional source root used to read file:line context when evidence lacks a snippet.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for context.md and meta.json. Defaults to ./.gbs_patch_suggest.",
    )
    return parser


def main(argv: list[str] | None = None, *, stderr: TextIO = sys.stderr) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    src_root = args.src_root.resolve() if args.src_root is not None else None
    if src_root is not None and not src_root.is_dir():
        print(f"gbs_patch_suggest: src root is not a directory: {src_root}", file=stderr)
        return EXIT_ARGS

    result = run_patch_suggest(
        PatchSuggestOptions(
            evidence_path=args.evidence,
            output_dir=args.output_dir,
            src_root=src_root,
        )
    )
    if result.error:
        print(f"gbs_patch_suggest: {result.error}", file=stderr)
        return result.exit_code

    print(f"gbs_patch_suggest: context written to {result.context_path}", file=stderr)
    print(f"gbs_patch_suggest: meta written to {result.meta_path}", file=stderr)
    print(f"gbs_patch_suggest: status {result.status}", file=stderr)
    return result.exit_code
