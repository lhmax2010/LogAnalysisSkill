import subprocess
from pathlib import Path

import pytest

from gbs_workflow.suggesters.compile_error import CompileErrorSuggester
from gbs_workflow.suggesters.fallback import FallbackSuggester
from gbs_workflow.suggesters.linker_missing import (
    LinkerMissingSuggester,
    candidate_devel_package,
    parse_missing_library,
)
from gbs_workflow.suggesters.linker_undef import LinkerUndefSuggester, parse_undefined_symbol
from gbs_workflow.suggesters.patch_failed import PatchFailedSuggester
from gbs_workflow.suggesters.spec_script import SpecScriptSuggester
from gbs_workflow.workflow import collect_suggestions, write_suggestions


def packet(kind: str, message: str, **extra: object) -> dict[str, object]:
    primary_error: dict[str, object] = {"kind": kind, "message": message}
    primary_error.update(extra)
    return {
        "package": "ffmpeg",
        "failed_phase": "%build",
        "primary_error": primary_error,
    }


def write_spec(root: Path, text: str = "Name: ffmpeg\nBuildRequires:  gcc\n%prep\n") -> Path:
    spec = root / "packaging" / "ffmpeg.spec"
    spec.parent.mkdir(parents=True)
    spec.write_text(text, encoding="utf-8")
    return spec


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("ld: cannot find -lssl", "ssl"),
        ("ld: cannot find libssl.so", "libssl"),
        ("library not found for -lavcodec", "avcodec"),
    ],
)
def test_parse_missing_library_formats(message: str, expected: str) -> None:
    assert parse_missing_library(packet("linker_missing", message)) == expected


def test_candidate_devel_package_normalizes_library_names() -> None:
    assert candidate_devel_package("ssl") == "libssl-devel"
    assert candidate_devel_package("libssl") == "libssl-devel"
    assert candidate_devel_package("libssl.so") == "libssl-devel"


def test_linker_missing_generates_low_confidence_patch(tmp_path: Path) -> None:
    write_spec(tmp_path)

    suggestions = LinkerMissingSuggester().generate(
        packet("linker_missing", "ld: cannot find -lssl"),
        tmp_path,
    )

    assert len(suggestions) == 1
    suggestion = suggestions[0]
    assert suggestion.suggester == "linker_missing"
    assert suggestion.confidence == "low"
    assert suggestion.patch_content is not None
    assert "BuildRequires:  libssl-devel" in suggestion.patch_content

    patch_path = tmp_path / "linker_missing.patch"
    patch_path.write_text(suggestion.patch_content, encoding="utf-8")
    subprocess.run(["git", "apply", "--check", patch_path], cwd=tmp_path, check=True)


def test_linker_missing_falls_back_to_markdown_when_library_unparseable(tmp_path: Path) -> None:
    suggestions = LinkerMissingSuggester().generate(
        packet("linker_missing", "ld failed"),
        tmp_path,
    )

    assert suggestions[0].patch_content is None
    assert suggestions[0].manual_steps is not None
    assert "Identify the package" in suggestions[0].manual_steps[0]


def test_linker_undef_advises_symbol_and_location(tmp_path: Path) -> None:
    suggestions = LinkerUndefSuggester().generate(
        packet(
            "linker_undef",
            "undefined reference to `nonexistent_helper_xxxyzz'",
            file="libavcodec/foo.c",
            line=42,
        ),
        tmp_path,
    )

    assert parse_undefined_symbol(packet("linker_undef", "undefined reference to `foo'")) == "foo"
    assert suggestions[0].patch_content is None
    assert suggestions[0].target_files == ["libavcodec/foo.c:42"]
    assert "nonexistent_helper_xxxyzz" in suggestions[0].title


def test_patch_failed_suggester_outputs_recovery_steps(tmp_path: Path) -> None:
    suggestions = PatchFailedSuggester().generate(
        packet("patch", "Hunk #1 FAILED at 10"),
        tmp_path,
    )

    assert suggestions[0].suggester == "patch_failed"
    assert suggestions[0].patch_content is None
    assert any(".rej" in step for step in suggestions[0].manual_steps or [])


@pytest.mark.parametrize("kind", ["spec_script", "rpm_phase"])
def test_spec_script_suggester_matches_spec_kinds(kind: str, tmp_path: Path) -> None:
    suggester = SpecScriptSuggester()
    pkt = packet(kind, "cp: cannot stat file")

    assert suggester.matches(pkt) is True
    suggestion = suggester.generate(pkt, tmp_path)[0]
    assert suggestion.patch_content is None
    assert "%build" in suggestion.title


def test_compile_error_suggester_uses_source_location(tmp_path: Path) -> None:
    suggestions = CompileErrorSuggester().generate(
        packet(
            "compiler",
            "error: unknown type name",
            file="libavcodec/foo.c",
            line=7,
            semantic_class="undeclared_identifier",
        ),
        tmp_path,
    )

    assert suggestions[0].target_files == ["libavcodec/foo.c:7"]
    assert "undeclared_identifier" in suggestions[0].description


def test_fallback_only_matches_unknown_kind(tmp_path: Path) -> None:
    suggester = FallbackSuggester()

    assert suggester.matches(packet("raw_error", "unknown failure")) is True
    assert suggester.matches(packet("depsolve", "nothing provides foo")) is False
    suggestion = suggester.generate(packet("raw_error", "unknown failure"), tmp_path)[0]
    assert suggestion.suggester == "fallback"
    assert suggestion.patch_content is None


def test_collect_suggestions_routes_known_and_unknown_packets(tmp_path: Path) -> None:
    known = collect_suggestions(
        packet("linker_undef", "undefined reference to `foo'"),
        tmp_path,
        suggesters=[LinkerUndefSuggester(), FallbackSuggester()],
    )
    unknown = collect_suggestions(
        packet("raw_error", "unknown failure"),
        tmp_path,
        suggesters=[LinkerUndefSuggester(), FallbackSuggester()],
    )

    assert [suggestion.suggester for suggestion in known] == ["linker_undef"]
    assert [suggestion.suggester for suggestion in unknown] == ["fallback"]


def test_advisory_suggestions_write_markdown_without_patch(tmp_path: Path) -> None:
    suggestion = LinkerUndefSuggester().generate(
        packet("linker_undef", "undefined reference to `foo'"),
        tmp_path,
    )[0]

    files = write_suggestions([suggestion], tmp_path / "suggestions")

    assert [path.suffix for path in files] == [".md"]
    assert "Has Patch**: No" in files[0].read_text(encoding="utf-8")
