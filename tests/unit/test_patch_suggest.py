import json
from pathlib import Path

from gbs_patch_suggest.cli import (
    EXIT_EVIDENCE_UNREADABLE,
    PatchSuggestOptions,
    main,
    run_patch_suggest,
)
from gbs_patch_suggest.ingest import extract_first_diagnostic
from gbs_patch_suggest.render import MANDATORY_INSTRUCTIONS


def compiler_packet(
    *,
    file: str | None = "src/demo.c",
    line: int | None = 12,
    source_snippet: dict[str, object] | None = None,
) -> dict[str, object]:
    primary_error: dict[str, object] = {
        "kind": "compiler",
        "message": "implicit declaration of function 'av_temp_lss'",
    }
    if file is not None:
        primary_error["file"] = file
    if line is not None:
        primary_error["line"] = line
    packet: dict[str, object] = {
        "primary_error": primary_error,
        "root_cause_candidates": [
            {
                "kind": "compiler",
                "semantic_class": "undeclared_identifier",
                "confidence": 0.8,
            }
        ],
        "evidence": {},
    }
    if source_snippet is not None:
        packet["evidence"] = {"source_snippet": source_snippet}
    return packet


def write_packet(tmp_path: Path, packet: dict[str, object]) -> Path:
    path = tmp_path / "evidence_packet.json"
    path.write_text(json.dumps(packet), encoding="utf-8")
    return path


def read_meta(output_dir: Path) -> dict[str, object]:
    return json.loads((output_dir / "meta.json").read_text(encoding="utf-8"))


def write_source(root: Path, relative: str, *, lines: int = 20) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(f"{relative} line {index}" for index in range(1, lines + 1)))
    return path


def test_extract_first_diagnostic_uses_primary_error_and_top_candidate() -> None:
    diagnostic = extract_first_diagnostic(compiler_packet())

    assert diagnostic.kind == "compiler"
    assert diagnostic.semantic_class == "undeclared_identifier"
    assert diagnostic.file == "src/demo.c"
    assert diagnostic.line == 12
    assert diagnostic.message == "implicit declaration of function 'av_temp_lss'"


def test_level_a_uses_evidence_source_snippet(tmp_path: Path) -> None:
    evidence_path = write_packet(
        tmp_path,
        compiler_packet(
            source_snippet={
                "path": "src/demo.c",
                "start_line": 10,
                "end_line": 13,
                "text": "int value = av_temp_lss();",
            }
        ),
    )
    output_dir = tmp_path / "out"

    result = run_patch_suggest(PatchSuggestOptions(evidence_path, output_dir=output_dir))

    assert result.exit_code == 0
    meta = read_meta(output_dir)
    assert meta["status"] == "source_context_available"
    assert meta["level"] == "A"
    assert meta["has_source_context"] is True
    context = (output_dir / "context.md").read_text(encoding="utf-8")
    assert "int value = av_temp_lss();" in context
    assert MANDATORY_INSTRUCTIONS.strip() in context
    assert not list(output_dir.glob("*.patch"))


def test_level_b_reports_file_line_without_source_context(tmp_path: Path) -> None:
    evidence_path = write_packet(tmp_path, compiler_packet())
    output_dir = tmp_path / "out"

    result = run_patch_suggest(PatchSuggestOptions(evidence_path, output_dir=output_dir))

    assert result.exit_code == 0
    meta = read_meta(output_dir)
    assert meta["status"] == "source_context_unavailable"
    assert meta["level"] == "B"
    assert meta["has_source_context"] is False
    context = (output_dir / "context.md").read_text(encoding="utf-8")
    assert "Source context for `src/demo.c:12` is unavailable" in context
    assert "Do NOT run `git apply` / `patch`" in context
    assert not list(output_dir.glob("*.patch"))


def test_suffix_search_unique_match_upgrades_to_level_a(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    write_source(src_root, "gst-libs/ext/ffmpeg/libavcodec/utils.c")
    evidence_path = write_packet(
        tmp_path,
        compiler_packet(file="libavcodec/utils.c", line=12),
    )
    output_dir = tmp_path / "out"

    result = run_patch_suggest(
        PatchSuggestOptions(evidence_path, output_dir=output_dir, src_root=src_root)
    )

    assert result.exit_code == 0
    meta = read_meta(output_dir)
    assert meta["status"] == "source_context_available"
    assert meta["level"] == "A"
    assert meta["source_context"]["origin"] == "src_root_suffix_search"  # type: ignore[index]
    context = (output_dir / "context.md").read_text(encoding="utf-8")
    assert "gst-libs/ext/ffmpeg/libavcodec/utils.c line 12" in context


def test_suffix_search_zero_match_stays_level_b(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    write_source(src_root, "other/utils.c")
    evidence_path = write_packet(
        tmp_path,
        compiler_packet(file="libavcodec/utils.c", line=12),
    )
    output_dir = tmp_path / "out"

    result = run_patch_suggest(
        PatchSuggestOptions(evidence_path, output_dir=output_dir, src_root=src_root)
    )

    assert result.exit_code == 0
    meta = read_meta(output_dir)
    assert meta["status"] == "source_context_unavailable"
    assert meta["level"] == "B"
    assert meta["candidate_paths"] == []


def test_suffix_search_multiple_matches_stays_level_b_with_candidates(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    first = write_source(src_root, "a/libavcodec/utils.c")
    second = write_source(src_root, "b/libavcodec/utils.c")
    evidence_path = write_packet(
        tmp_path,
        compiler_packet(file="libavcodec/utils.c", line=12),
    )
    output_dir = tmp_path / "out"

    result = run_patch_suggest(
        PatchSuggestOptions(evidence_path, output_dir=output_dir, src_root=src_root)
    )

    assert result.exit_code == 0
    meta = read_meta(output_dir)
    assert meta["status"] == "source_context_ambiguous"
    assert meta["level"] == "B"
    assert set(meta["candidate_paths"]) == {str(first), str(second)}
    context = (output_dir / "context.md").read_text(encoding="utf-8")
    assert "Candidate matches found" in context


def test_suffix_search_uses_path_segment_alignment(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    write_source(src_root, "mylibavcodec/utils.c")
    evidence_path = write_packet(
        tmp_path,
        compiler_packet(file="libavcodec/utils.c", line=12),
    )
    output_dir = tmp_path / "out"

    result = run_patch_suggest(
        PatchSuggestOptions(evidence_path, output_dir=output_dir, src_root=src_root)
    )

    assert result.exit_code == 0
    meta = read_meta(output_dir)
    assert meta["status"] == "source_context_unavailable"
    assert meta["candidate_paths"] == []


def test_suffix_search_skips_heavy_directories(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    write_source(src_root, ".git/libavcodec/utils.c")
    write_source(src_root, "GBS-ROOT-LOCAL/libavcodec/utils.c")
    write_source(src_root, "build/libavcodec/utils.c")
    write_source(src_root, ".gbs_workflow/libavcodec/utils.c")
    write_source(src_root, ".gbs_patch_suggest/libavcodec/utils.c")
    write_source(src_root, "node_modules/libavcodec/utils.c")
    evidence_path = write_packet(
        tmp_path,
        compiler_packet(file="libavcodec/utils.c", line=12),
    )
    output_dir = tmp_path / "out"

    result = run_patch_suggest(
        PatchSuggestOptions(evidence_path, output_dir=output_dir, src_root=src_root)
    )

    assert result.exit_code == 0
    meta = read_meta(output_dir)
    assert meta["status"] == "source_context_unavailable"
    assert meta["candidate_paths"] == []


def test_absolute_path_inside_src_root_upgrades_to_level_a(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    source = write_source(src_root, "libavcodec/utils.c")
    evidence_path = write_packet(
        tmp_path,
        compiler_packet(file=str(source), line=12),
    )
    output_dir = tmp_path / "out"

    result = run_patch_suggest(
        PatchSuggestOptions(evidence_path, output_dir=output_dir, src_root=src_root)
    )

    assert result.exit_code == 0
    meta = read_meta(output_dir)
    assert meta["status"] == "source_context_available"
    assert meta["level"] == "A"


def test_absolute_path_outside_src_root_stays_level_b(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    outside = write_source(tmp_path / "outside", "libavcodec/utils.c")
    evidence_path = write_packet(
        tmp_path,
        compiler_packet(file=str(outside), line=12),
    )
    output_dir = tmp_path / "out"

    result = run_patch_suggest(
        PatchSuggestOptions(evidence_path, output_dir=output_dir, src_root=src_root)
    )

    assert result.exit_code == 0
    meta = read_meta(output_dir)
    assert meta["status"] == "source_context_unavailable"
    assert meta["candidate_paths"] == []


def test_absolute_path_missing_stays_level_b(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    src_root.mkdir()
    evidence_path = write_packet(
        tmp_path,
        compiler_packet(file=str(src_root / "libavcodec" / "missing.c"), line=12),
    )
    output_dir = tmp_path / "out"

    result = run_patch_suggest(
        PatchSuggestOptions(evidence_path, output_dir=output_dir, src_root=src_root)
    )

    assert result.exit_code == 0
    meta = read_meta(output_dir)
    assert meta["status"] == "source_context_unavailable"


def test_level_c_reports_diagnostic_only_without_file_line(tmp_path: Path) -> None:
    evidence_path = write_packet(tmp_path, compiler_packet(file=None, line=None))
    output_dir = tmp_path / "out"

    result = run_patch_suggest(PatchSuggestOptions(evidence_path, output_dir=output_dir))

    assert result.exit_code == 0
    meta = read_meta(output_dir)
    assert meta["status"] == "diagnostic_only"
    assert meta["level"] == "C"
    context = (output_dir / "context.md").read_text(encoding="utf-8")
    assert "has no usable file and line number" in context
    assert MANDATORY_INSTRUCTIONS.strip() in context
    assert not list(output_dir.glob("*.patch"))


def test_non_compiler_packet_is_not_applicable(tmp_path: Path) -> None:
    evidence_path = write_packet(
        tmp_path,
        {
            "primary_error": {"kind": "depsolve", "message": "nothing provides foo"},
            "root_cause_candidates": [],
            "evidence": {},
        },
    )
    output_dir = tmp_path / "out"

    result = run_patch_suggest(PatchSuggestOptions(evidence_path, output_dir=output_dir))

    assert result.exit_code == 0
    meta = read_meta(output_dir)
    assert meta["status"] == "not_applicable"
    assert meta["applicable"] is False
    context = (output_dir / "context.md").read_text(encoding="utf-8")
    assert "this skill is not applicable" in context
    assert not list(output_dir.glob("*.patch"))


def test_cli_rejects_missing_evidence(tmp_path: Path) -> None:
    code = main(["--evidence", str(tmp_path / "missing.json"), "--output-dir", str(tmp_path)])

    assert code == EXIT_EVIDENCE_UNREADABLE
