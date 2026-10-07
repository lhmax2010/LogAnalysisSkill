"""E4/E5 artificial controls, independent of production imports or OBS producers."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
saved = sys.path[:]
sys.path.insert(0, str(ROOT / "docs/clang-fix-campaign/tools"))
try:
    S = importlib.import_module("terminal_scan")
finally:
    sys.path[:] = saved


@pytest.mark.parametrize(
    ("path", "mode", "content", "expected"),
    [
        ("vendor", "160000", b"", "GITLINK"),
        ("alias.py", "120000", b"target", "SYMLINK"),
        ("native.so", "100644", b"\0", "IMPORTABLE_BINARY"),
        ("root.pth", "100644", b"../src", "PTH"),
        ("image.bin", "100644", b"\0", "BINARY"),
        ("module.py", "100644", b"x = 1\n", "PY_SOURCE"),
        ("pyproject.toml", "100644", b"", "PACKAGING"),
        (".github/workflows/ci.yml", "100644", b"run: python -m pkg", "CI_CONFIG"),
        ("run.sh", "100755", b"echo test", "SHELL"),
        ("Makefile", "100644", b"all:\n\tpython -m pkg", "BUILD"),
        ("README.md", "100644", b"pkg", "DOC"),
        (".importlinter", "100644", b"[importlinter]", "OTHER_TEXT"),
    ],
    ids=S.ENTRY_KINDS,
)
def test_e4_each_entry_kind(path: str, mode: str, content: bytes, expected: str) -> None:
    assert S.entry_kind(path, mode, content) == expected


def test_e4_unknown_git_mode_is_blocked() -> None:
    with pytest.raises(S.ScanError, match="UNKNOWN_PROVIDER_KIND"):
        S.entry_kind("docs/README.md", "040000", b"text")


@pytest.mark.parametrize(
    ("path", "mode", "data", "kind"),
    [
        ("docs/Makefile", "100644", b"", "BUILD"),
        ("docs/setup.cfg", "100644", b"", "PACKAGING"),
        ("docs/a.sh", "100644", b"", "SHELL"),
        ("docs/a.spec", "100644", b"", "BUILD"),
        ("docs/a.json", "100644", b"{}", "DOC"),
        ("docs/a.json", "100755", b"{}", "OTHER_TEXT"),
        ("docs/a.txt", "100644", b"#!custom\n", "OTHER_TEXT"),
        ("check", "100755", b"#!/usr/bin/env python3\n", "PY_SOURCE"),
        ("run", "100755", b"#!/bin/bash\n", "SHELL"),
        ("bad.py", "100644", b"\xff", "BINARY"),
        ("native.pyc", "100644", b"\xff", "IMPORTABLE_BINARY"),
        ("paths.pth", "100644", b"\0", "PTH"),
    ],
)
def test_e4_first_match_wins(path: str, mode: str, data: bytes, kind: str) -> None:
    assert S.entry_kind(path, mode, data) == kind


def description(where: tuple[str, ...] = ("src",)) -> bytes:
    return (
        "[tool.setuptools.packages.find]\nwhere = "
        + json.dumps(where)
        + '\ninclude = ["pkg*"]\nexclude = []\n'
    ).encode()


@pytest.fixture
def files() -> dict[str, bytes]:
    return {
        "pyproject.toml": description(),
        "src/pkg/__init__.py": b"",
        "src/pkg/twin.py": b"LIVE = 1\n",
        "src/pkg/live_only.py": b"LIVE = 1\n",
        "docs/readme.txt": b"pkg.twin",
        "release/pyproject.toml": description(),
        "release/src/pkg/__init__.py": b"",
        "release/src/pkg/twin.py": b"HISTORY = 1\n",
    }


def test_e5_release_absolute_import_stays_release(files: dict[str, bytes]) -> None:
    index = S.ModuleIndex(files, S.contexts(files))
    result = index.resolve("release", "pkg.twin", "release/src/pkg/consumer.py:1")
    assert result["kind"] == "LOCAL"
    assert result["targets"] == [{"context": "release", "path": "release/src/pkg/twin.py"}]
    assert index.events == [result]


def test_e5_release_missing_name_falls_back_live(files: dict[str, bytes]) -> None:
    index = S.ModuleIndex(files, S.contexts(files))
    result = index.resolve("release", "pkg.live_only", "release/src/pkg/consumer.py:2")
    assert result["kind"] == "CROSS_CONTEXT_FALLBACK"
    assert result["targets"] == [{"context": ".", "path": "src/pkg/live_only.py"}]
    assert index.events == [result]


def test_e5_live_absolute_import_stays_live(files: dict[str, bytes]) -> None:
    index = S.ModuleIndex(files, S.contexts(files))
    result = index.resolve(".", "pkg.twin", "src/pkg/consumer.py:1")
    assert result["kind"] == "LOCAL"
    assert result["targets"] == [{"context": ".", "path": "src/pkg/twin.py"}]


def test_e5_path_can_cross_context(files: dict[str, bytes]) -> None:
    index = S.ModuleIndex(files, S.contexts(files))
    result = index.resolve_path(".", "release/src/pkg/twin.py", "docs/readme.txt:1")
    assert result["kind"] == "PATH"
    assert result["targets"] == [{"context": "release", "path": "release/src/pkg/twin.py"}]


def test_e5_duplicate_within_context_is_ambiguous(files: dict[str, bytes]) -> None:
    files["pyproject.toml"] = description(("src", "alt"))
    files["alt/pkg/twin.py"] = b"OTHER = 1\n"
    index = S.ModuleIndex(files, S.contexts(files))
    assert index.events[0]["kind"] == "MODULE_IDENTITY_AMBIGUOUS"
    result = index.resolve(".", "pkg.twin", "src/pkg/consumer.py:1")
    assert result["kind"] == "MODULE_IDENTITY_AMBIGUOUS"
    assert len(result["targets"]) == 2


def test_e5_missing_and_multiple_foreign_names_are_recorded(files: dict[str, bytes]) -> None:
    files["other/pyproject.toml"] = description()
    files["other/src/pkg/twin.py"] = b"X = 1\n"
    files["empty/pyproject.toml"] = description()
    index = S.ModuleIndex(files, S.contexts(files))
    assert index.resolve("empty", "pkg.absent", "empty/source.py:1")["kind"] == "NON_CANDIDATE_NAME"
    result = index.resolve("empty", "pkg.twin", "empty/source.py:2")
    assert result["kind"] == "MODULE_IDENTITY_AMBIGUOUS"
    assert len(result["targets"]) == 3
    assert len(index.events) == 2


def test_e5_nested_context_and_unmapped_path(files: dict[str, bytes]) -> None:
    files["outside.py"] = b"X = 1\n"
    declarations = S.contexts(files)
    assert S.context_for("release/README.md", declarations).key == "release"
    assert S.context_for("release-not/README.md", declarations).key == "."
    assert S.context_for("README.md", declarations).key == "."
    index = S.ModuleIndex(files, declarations)
    assert "outside.py" not in index.by_path
    assert index.resolve_path(".", "outside.py", "README.md:1")["targets"] == [
        {"context": ".", "path": "outside.py"}
    ]


def test_registry_closed_sets_and_nonempty_required_detectors() -> None:
    entries, providers = S.registry()
    assert tuple(entries) == S.ENTRY_KINDS
    assert set(providers) == set(S.PROVIDER_KINDS)
    assert entries["BINARY"] == ["binary_record"]
    assert entries["DOC"] == ["doctest", "name_fallback"]


def test_empty_detector_registry_is_not_a_vacuous_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    entries, providers = S.registry()
    entries["BINARY"] = []
    monkeypatch.setattr(
        S, "load_json", lambda path: providers if path.name == "provider_registry.json" else entries
    )
    with pytest.raises(S.ScanError, match="REGISTRY_REQUIRED_DETECTORS"):
        S.registry()


def test_atomic_write_no_pending_file(tmp_path: Path) -> None:
    target = tmp_path / "data.json"
    S.write_atomic(target, {"x": 1})
    assert json.loads(target.read_text()) == {"x": 1}
    assert list(tmp_path.iterdir()) == [target]
