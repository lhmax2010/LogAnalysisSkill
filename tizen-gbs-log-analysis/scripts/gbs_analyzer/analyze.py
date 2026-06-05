"""M8 wrapper entrypoint for end-to-end GBS buildlog analysis."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeVar

from gbs_analyzer.error_clusters import ErrorClusterResult, build_error_clusters
from gbs_analyzer.evidence import Evidence
from gbs_analyzer.evidence.base import EvidenceCollector
from gbs_analyzer.evidence.router import collector_for_candidate
from gbs_analyzer.full_match import FullMatchResult, full_match
from gbs_analyzer.packet_assembler import (
    BudgetPool,
    MinimalRedactor,
    TokenEstimator,
    assemble_packet,
    render_packet_markdown,
)
from gbs_analyzer.quick_filter import QuickFilterResult, quick_filter
from gbs_analyzer.rank_causes import RankResult, rank_causes
from gbs_analyzer.scan_and_extract import ScanResult, scan_buildlog
from gbs_analyzer.tizen.spec_minimal import SpecMinimalParser
from gbs_analyzer.tracing import setup_tracing
from gbs_analyzer.tracing.perf_report import build_perf_report

EXIT_SUCCESS = 0
EXIT_FATAL = 1
EXIT_ARGS = 2
EXIT_BUILDLOG_UNREADABLE = 3
EXIT_TIMEOUT = 124
DEFAULT_MAX_TOKENS = 1800

T = TypeVar("T")


@dataclass
class AnalyzeOptions:
    buildlog_path: Path
    src_root: Path | None
    output_dir: Path
    max_tokens: int = DEFAULT_MAX_TOKENS
    output_format: str = "both"
    spec_path: Path | None = None
    package: str = "unknown"
    arch: str = "unknown"
    profile: str = "unknown"
    trace: bool = False
    use_tiktoken: bool = True


@dataclass
class AnalyzeResult:
    exit_code: int
    packet: dict[str, Any] | None = None
    perf_report: dict[str, Any] | None = None
    output_paths: dict[str, str] = field(default_factory=dict)
    error: str | None = None


@dataclass
class PipelineState:
    timings_ms: dict[str, float] = field(default_factory=dict)
    scan_result: ScanResult | None = None
    error_cluster_result: ErrorClusterResult | None = None
    quick_result: QuickFilterResult | None = None
    rank_result: RankResult | None = None
    evidence: Evidence | None = None
    full_match_result: FullMatchResult | None = None
    evidence_collector: str | None = None
    level_preferred: int | None = None
    level_achieved: int | None = None
    warnings: list[str] = field(default_factory=list)


def analyze_buildlog(options: AnalyzeOptions) -> AnalyzeResult:
    """Run the MVP pipeline and write all requested output files."""

    buildlog = options.buildlog_path
    if not buildlog.is_file():
        return AnalyzeResult(
            exit_code=EXIT_BUILDLOG_UNREADABLE,
            error=f"buildlog is not readable: {buildlog}",
        )

    options.output_dir.mkdir(parents=True, exist_ok=True)
    state = PipelineState()
    estimator = TokenEstimator(use_tiktoken=options.use_tiktoken)
    redactor = MinimalRedactor(workspace_root=options.src_root)

    try:
        with setup_tracing(options.output_dir, trace=options.trace) as trace_logger:
            trace_logger.info("wrapper", "analysis_started", buildlog_path=str(buildlog))
            src_root = options.src_root or buildlog.resolve().parent
            spec_path = options.spec_path or _find_spec_path(options.package, src_root)

            state.scan_result = _timed(
                state,
                "L0_scan",
                lambda: scan_buildlog(buildlog, cwd=src_root, trace_logger=trace_logger),
            )
            scan_result = state.scan_result
            state.error_cluster_result = _timed(
                state,
                "L1_error_clusters",
                lambda: build_error_clusters(scan_result),
            )
            state.quick_result = _timed(state, "L4a_quick", lambda: quick_filter(scan_result))

            if state.quick_result.hit and state.quick_result.match is not None:
                packet = _fast_path_packet(
                    state.quick_result,
                    options=options,
                    estimator=estimator,
                    error_clusters=(
                        state.error_cluster_result.summary
                        if state.error_cluster_result is not None
                        else None
                    ),
                )
            else:
                state.rank_result = _timed(state, "L2_rank", lambda: rank_causes(scan_result))
                candidate = _top_candidate(state.rank_result)
                collector = (
                    collector_for_candidate(
                        candidate,
                        scan_result,
                        src_root=src_root,
                        spec_path=spec_path,
                        buildlog_path=buildlog,
                    )
                    if candidate is not None
                    else None
                )
                state.evidence = _timed(
                    state,
                    "L3_evidence",
                    lambda: _collect_evidence(collector, candidate, state),
                )
                state.full_match_result = _timed(
                    state,
                    "L4b_full",
                    lambda: _run_full_match(scan_result, candidate, state.evidence),
                )
                packet = _timed(
                    state,
                    "L5_assembler",
                    lambda: assemble_packet(
                        scan_result,
                        state.rank_result or [],
                        state.evidence,
                        state.full_match_result,
                        package=options.package,
                        arch=options.arch,
                        profile=options.profile,
                        budget_pool=BudgetPool(total=options.max_tokens - 400),
                        estimator=estimator,
                        redactor=redactor,
                        trace_logger=trace_logger,
                        max_tokens=options.max_tokens,
                        error_clusters=(
                            state.error_cluster_result.summary
                            if state.error_cluster_result is not None
                            else None
                        ),
                    ),
                )
                packet["token_budget"]["limit_with_prompt"] = options.max_tokens

            perf = build_perf_report(
                buildlog_path=buildlog,
                packet=packet,
                timings_ms=state.timings_ms,
                estimator=estimator,
                evidence_collector=state.evidence_collector,
                level_preferred=state.level_preferred,
                level_achieved=state.level_achieved,
                warnings=state.warnings,
            )
            output_paths = write_outputs(
                packet,
                perf,
                options=options,
                redactor=redactor,
                estimator=estimator,
                error_cluster_sidecar=(
                    state.error_cluster_result.sidecar
                    if state.error_cluster_result is not None
                    else None
                ),
            )
            trace_logger.info(
                "wrapper",
                "analysis_completed",
                verdict=packet.get("verdict"),
                via=packet.get("via"),
            )
            return AnalyzeResult(
                exit_code=EXIT_SUCCESS,
                packet=packet,
                perf_report=perf,
                output_paths=output_paths,
            )
    except Exception as exc:
        return AnalyzeResult(exit_code=EXIT_FATAL, error=str(exc))


def write_outputs(
    packet: dict[str, Any],
    perf_report: dict[str, Any],
    *,
    options: AnalyzeOptions,
    redactor: MinimalRedactor,
    estimator: TokenEstimator,
    error_cluster_sidecar: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Write wrapper artifacts without printing to stdout."""

    output_paths: dict[str, str] = {}
    packet_json_tokens: int | None = None
    packet_markdown_tokens: int | None = None
    if options.output_format in {"json", "both"}:
        packet_path = options.output_dir / "evidence_packet.json"
        packet_json_text = json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        packet_path.write_text(packet_json_text, encoding="utf-8")
        packet_json_tokens = estimator.estimate_text(packet_json_text)
        output_paths["evidence_packet_json"] = str(packet_path)
    if options.output_format in {"md", "both"}:
        markdown_path = options.output_dir / "evidence_packet.md"
        markdown_text = render_packet_markdown(packet, redactor=redactor) + "\n"
        markdown_path.write_text(markdown_text, encoding="utf-8")
        packet_markdown_tokens = estimator.estimate_text(markdown_text)
        output_paths["evidence_packet_md"] = str(markdown_path)
    if error_cluster_sidecar is not None:
        cluster_path = options.output_dir / "error_clusters.json"
        cluster_path.write_text(
            json.dumps(error_cluster_sidecar, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        output_paths["error_clusters_json"] = str(cluster_path)

    _attach_downstream_output_tokens(
        perf_report,
        estimator=estimator,
        evidence_packet_md_tokens=packet_markdown_tokens,
        evidence_packet_json_tokens=packet_json_tokens,
    )
    perf_path = options.output_dir / "perf_report.json"
    perf_path.write_text(
        json.dumps(perf_report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    output_paths["perf_report_json"] = str(perf_path)
    return output_paths


def _attach_downstream_output_tokens(
    perf_report: dict[str, Any],
    *,
    estimator: TokenEstimator,
    evidence_packet_md_tokens: int | None,
    evidence_packet_json_tokens: int | None,
) -> None:
    """Add estimates for analyzer outputs that an outer Claude may read."""

    by_section = perf_report.get("tokens", {}).get("by_section", {})
    source_snippets_tokens = (
        by_section.get("source_snippets") if isinstance(by_section, dict) else None
    )
    total_claude_facing = evidence_packet_md_tokens or 0
    tokens = perf_report.setdefault("tokens", {})
    if not isinstance(tokens, dict):
        return
    tokens["downstream_outputs"] = {
        "scope": (
            "Estimated tokens of analyzer material intended for outer Claude "
            "recommended reading. Actual Claude consumption also includes any "
            "source files Claude reads on its own."
        ),
        "usage_note": (
            "Compare this baseline with Cline/client actual token usage; the "
            "difference approximates extra material Claude read outside analyzer outputs."
        ),
        "estimate_method": estimator.method,
        "total_claude_facing_tokens": total_claude_facing,
        "evidence_packet_md_tokens": evidence_packet_md_tokens,
        "evidence_packet_json_tokens": evidence_packet_json_tokens,
        "source_snippets_tokens": source_snippets_tokens,
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m gbs_analyzer",
        description="Analyze a Tizen gbs buildlog and write an Evidence Packet.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    analyze = subparsers.add_parser("analyze", help="analyze a buildlog")
    analyze.add_argument("buildlog_path", type=Path)
    analyze.add_argument("--src-root", default="auto")
    analyze.add_argument("--spec-path", type=Path)
    analyze.add_argument("--output-dir", type=Path, default=Path(".gbs_analysis"))
    analyze.add_argument("--output-format", choices=("json", "md", "both"), default="both")
    analyze.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    analyze.add_argument("--package", default="unknown")
    analyze.add_argument("--arch", default="unknown")
    analyze.add_argument("--profile", default="unknown")
    analyze.add_argument("--trace", action="store_true")
    analyze.add_argument("--no-tiktoken", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if args.command != "analyze":
        return EXIT_ARGS

    src_root = _resolve_src_root(args.src_root, args.buildlog_path)
    options = AnalyzeOptions(
        buildlog_path=args.buildlog_path,
        src_root=src_root,
        output_dir=args.output_dir,
        max_tokens=args.max_tokens,
        output_format=args.output_format,
        spec_path=args.spec_path,
        package=args.package,
        arch=args.arch,
        profile=args.profile,
        trace=args.trace,
        use_tiktoken=not args.no_tiktoken,
    )
    result = analyze_buildlog(options)
    if result.error:
        sys.stderr.write(result.error + "\n")
    return result.exit_code


def _timed(state: PipelineState, layer: str, func: Callable[[], T]) -> T:
    start = time.perf_counter()
    try:
        return func()
    finally:
        state.timings_ms[layer] = (time.perf_counter() - start) * 1000


def _top_candidate(rank_result: RankResult | None) -> dict[str, Any] | None:
    if rank_result is None:
        return None
    candidates = rank_result.as_dict()["root_cause_candidates"]
    return candidates[0] if candidates else None


def _collect_evidence(
    collector: EvidenceCollector | None,
    candidate: dict[str, Any] | None,
    state: PipelineState,
) -> Evidence | None:
    if collector is None or candidate is None:
        return None
    estimate = collector.estimate(candidate)
    preferred = int(estimate.get("preferred", 900))
    state.level_preferred = _level_for_preferred(preferred)
    granted = (
        preferred
        if candidate.get("semantic_class") == "undefined_reference"
        else min(preferred, 600)
    )
    evidence = collector.collect(candidate, granted)
    state.evidence_collector = evidence.collector
    state.level_achieved = evidence.level
    if evidence.warnings:
        state.warnings.extend(evidence.warnings)
    return evidence


def _run_full_match(
    scan_result: ScanResult | None,
    candidate: dict[str, Any] | None,
    evidence: Evidence | None,
) -> FullMatchResult | None:
    if scan_result is None or candidate is None or evidence is None:
        return None
    return full_match(scan_result, candidate, evidence)


def _fast_path_packet(
    result: QuickFilterResult,
    *,
    options: AnalyzeOptions,
    estimator: TokenEstimator,
    error_clusters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    assert result.match is not None
    packet = dict(result.match.minimal_packet)
    packet["package"] = options.package
    packet["arch"] = options.arch
    packet["profile"] = options.profile
    packet["token_budget"] = {
        **packet.get("token_budget", {}),
        "limit_with_prompt": options.max_tokens,
        "estimate_method": estimator.method,
    }
    if error_clusters is not None:
        packet["error_clusters"] = error_clusters
    packet["token_budget"]["used"] = estimator.estimate_obj(packet)
    return packet


def _resolve_src_root(src_root: str, buildlog_path: Path) -> Path | None:
    if src_root in {"", "auto"}:
        return buildlog_path.resolve().parent
    return Path(src_root)


def _find_spec_path(package: str, src_root: Path | None) -> Path | None:
    if src_root is None:
        return None
    try:
        return SpecMinimalParser.find_spec_file(package, src_root)
    except (FileNotFoundError, ValueError):
        return None


def _level_for_preferred(preferred: int) -> int:
    if preferred >= 900:
        return 3
    if preferred >= 600:
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
