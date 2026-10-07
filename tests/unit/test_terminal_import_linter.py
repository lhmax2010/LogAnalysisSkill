"""E9-4 C7e controls: real parsing/resolution, no observed-code execution."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any, cast

import pytest

ROOT = Path(__file__).resolve().parents[2]
saved = sys.path[:]
sys.path.insert(0, str(ROOT / "docs/clang-fix-campaign/tools"))
try:
    L = importlib.import_module("terminal_import_linter")
    S = importlib.import_module("terminal_scan")
    R = importlib.import_module("terminal_registry")
finally:
    sys.path[:] = saved


def scan(
    text: str, path: str = ".importlinter", names: tuple[str, ...] = ("sentinel",)
) -> dict[str, Any]:
    files = {"pyproject.toml": b'[tool.setuptools.packages.find]\nwhere=["src"]\ninclude=["*"]\n'}
    for name in (
        "sentinel",
        "sentinel.z",
        "x",
        "x.y",
        "a",
        "pkg",
        "pkg.leaf",
        "other",
        "other.leaf",
    ):
        files["src/" + name.replace(".", "/") + "/__init__.py"] = b""
    files[path] = text.encode()
    index = S.ModuleIndex(files, S.contexts(files))
    hits = []
    for line, raw in enumerate(text.splitlines(), 1):
        for name in names:
            start = 0
            while (column := raw.find(name, start)) >= 0:
                hits.append(
                    dict(line=line, column=column, name=name, candidate_id=f"{name}#REEXPORT#S")
                )
                start = column + len(name)
    return cast(dict[str, Any], L.inspect(path, "100644", text.encode(), index, hits))


def modules(result: dict[str, Any]) -> list[str]:
    return [edge["target"]["module"] for edge in result["module_edges"]]


def test_e9_root_packages() -> None:
    result = scan("[importlinter]\nroot_packages = sentinel\n")
    assert modules(result) == ["sentinel"]
    assert result["name_hits"][0]["status"] == "C7e"


def test_e9_layers_siblings() -> None:
    result = scan("[importlinter:contract:c]\nlayers = a | sentinel\n")
    assert modules(result) == ["a", "sentinel"]
    assert len(result["participants"]) == 2


def test_e9_containers() -> None:
    result = scan("[importlinter:contract:c]\ncontainers = pkg\nlayers = leaf\n")
    assert modules(result) == ["pkg", "pkg.leaf"]


def test_e9_ignore_imports() -> None:
    result = scan("[importlinter:contract:c]\nignore_imports = x.y -> sentinel.z\n")
    assert modules(result) == ["x.y", "sentinel.z"]
    assert len(result["participants"]) == 2


@pytest.mark.parametrize("wildcard", ["*", "**"])
def test_e9_wildcard(wildcard: str) -> None:
    result = scan(f"[importlinter:contract:c]\nmodules = sentinel.{wildcard}\n")
    assert not modules(result)
    assert len(result["dynamic_unresolved"]) == 1
    assert result["dynamic_unresolved"][0]["form"] == "C7e"
    assert result["name_hits"][0]["status"] == "C7e"


@pytest.mark.parametrize("path", [".importlinter", "docs/.importlinter"])
def test_e9_entry_kind(path: str) -> None:
    result = scan("[importlinter]\nroot_packages = sentinel\n", path)
    assert result["entry_kind"] == "IMPORT_LINTER"
    assert modules(result) == ["sentinel"]


@pytest.mark.parametrize("comment", ["# python -m sentinel", "  ; python -m sentinel"])
def test_e9_comment_near_miss(comment: str) -> None:
    result = scan(f"[importlinter]\n{comment}\n")
    assert not result["participants"]
    assert not modules(result)
    assert result["exclusions"][0]["class"] == 9
    assert result["exclusions"][0]["interpreter_line"] is False
    assert result["name_hits"][0]["status"] == "EXCLUDED_CLASS9"


def test_e9_name_near_miss() -> None:
    result = scan("[importlinter:contract:c]\nname = show sentinel here\n")
    assert not result["participants"]
    assert result["name_hits"][0]["status"] == "EXCLUDED_CLASS9"


def test_e9_unknown_key_near_miss() -> None:
    result = scan("[importlinter:contract:c]\nfoo = sentinel\n")
    assert not result["participants"]
    assert result["name_hits"][0]["status"] == "UNKNOWN_CAPABILITY"


def test_e9_binding_not_consumed() -> None:
    result = scan("[importlinter:contract:c]\nmodules = sentinel\n")
    assert modules(result) == ["sentinel"]
    assert result["name_hits"][0]["candidate_id"] == "sentinel#REEXPORT#S"
    assert result["name_hits"][0]["status"] == "C7e"
    assert result["binding_edges"] == []
    assert all(edge["granularity"] == "MODULE" for edge in result["module_edges"])


@pytest.mark.parametrize("section", ["other", "importlinter:wrong:c", "importlinter:contract:"])
def test_e9_unknown_section(section: str) -> None:
    result = scan(f"[{section}]\nmodules = sentinel\n")
    assert result["name_hits"][0]["status"] == "UNKNOWN_CAPABILITY"


def test_e9_colon_optional_multiline_and_multiple_containers() -> None:
    result = scan(
        "[importlinter:contract:c]\ncontainers =\n  pkg\n  other\nlayers = (leaf) : leaf\n"
    )
    assert modules(result) == ["pkg", "other", "pkg.leaf", "other.leaf", "pkg.leaf", "other.leaf"]
    assert len(result["participants"]) == 4


def test_e9_parse_error_never_passes_names() -> None:
    result = scan("[importlinter]\nroot_packages=sentinel\nunparseable sentinel\n")
    assert result["parse_errors"]
    assert not result["participants"]
    assert {hit["status"] for hit in result["name_hits"]} == {"UNKNOWN_CAPABILITY"}


def test_e9_ini_defaults_or_interpolation_not_given_guessed_provenance() -> None:
    result = scan(
        "[DEFAULT]\nroot_packages=sentinel\n[importlinter]\n[importlinter:contract:c]\nmodules=a\n"
    )
    assert len(result["unknown_capabilities"]) == 1
    assert result["unknown_capabilities"][0]["kind"] == "UNKNOWN_CAPABILITY"
    assert result["unknown_capabilities"][0]["reason"] == "C7E_VALUE_PROVENANCE"
    assert modules(result) == ["a"]
    assert result["name_hits"][0]["status"] == "UNKNOWN_CAPABILITY"


def test_e9_other_packaging_not_reclassified() -> None:
    for path in ("setup.cfg", "pyproject.toml"):
        assert S.entry_kind(path, "100644", b"[importlinter]\nmodules=sentinel\n") == "PACKAGING"


def test_e9_registry_and_mapping() -> None:
    registry = R.load_registry(ROOT)
    assert len([row for row in registry if row["branch"].startswith("consumer.")]) == 24
    assert "consumer.C7e" in R.required_from_authority(ROOT)["IMPORT_LINTER"]
    assert len(R.required_from_authority(ROOT)) == 13


@pytest.mark.parametrize("value", ["a", "a -> x -> sentinel", "-> sentinel", "a ->"])
def test_e9_invalid_ignore_pair_fails_closed(value: str) -> None:
    with pytest.raises(S.ScanError, match="C7E_IGNORE_IMPORTS_ARITY"):
        scan(f"[importlinter:contract:c]\nignore_imports = {value}\n")
