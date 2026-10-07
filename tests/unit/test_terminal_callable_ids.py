"""E10 external answers; no observed module is imported or executed."""

import copy
import importlib
import sys
from pathlib import Path
from typing import Any, cast

import pytest

saved = sys.path[:]
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "docs/clang-fix-campaign/tools"))
try:
    C = importlib.import_module("terminal_callable_ids")
finally:
    sys.path[:] = saved


def rows(source: str) -> list[dict[str, Any]]:
    result = C.callable_ids(source, "pkg/proxy.py", ["AST_SCAN", "pkg/proxy.py"])
    assert result["issues"] == []
    return cast(list[dict[str, Any]], result["callables"])


def test_e10_two_lambdas_unique_and_collision_red() -> None:
    found = rows("import a,b\ndef f():\n return (lambda: a.f(), lambda: b.g())\n")
    assert [r["qualname"] for r in found] == ["f", "f.<locals>.<lambda>#1", "f.<locals>.<lambda>#2"]
    C.assert_unique(found)
    bad = copy.deepcopy(found)
    bad[2]["candidate_id"] = bad[1]["candidate_id"]
    with pytest.raises(C.ScanError, match="SEAL-7"):
        C.assert_unique(bad)


def test_e10_nested_and_repeat_are_stable() -> None:
    source = "import m\ndef f():\n return lambda: lambda: m.g()\n"
    found = rows(source)
    assert found == rows(source)
    assert found[-1]["qualname"] == "f.<locals>.<lambda>#1.<locals>.<lambda>#1"
    assert found[-1]["co_qualname"] == "f.<locals>.<lambda>.<locals>.<lambda>"


def test_e10_local_lambda_and_def_mechanical_evidence() -> None:
    found = rows("import m\ndef f():\n def g():return m.g()\n return lambda:m.g()\n")
    for row in found[1:]:
        evidence = row["admission"]
        assert evidence["status"] == "REJECTED_NOT_SHIM"
        assert evidence["authority"] == "E10-2"
        assert evidence["command"] == ["AST_SCAN", "pkg/proxy.py"]
        assert evidence["output"] == {"span": row["span"], "co_qualname": row["co_qualname"]}


def test_e10_module_and_class_binding_near_miss() -> None:
    found = rows("import mod\nf = lambda:mod.g()\nclass C:\n g = lambda:mod.g()\n")
    assert [r["qualname"] for r in found] == ["<lambda>#1", "C.<lambda>#1"]
    assert [r["binding_name"] for r in found] == ["f", "g"]
    assert all("admission" not in row for row in found)


def test_e10_default_argument_compiler_parent_not_ast_parent() -> None:
    found = rows("import m\nf = lambda x=(lambda:m.g()): (lambda:m.h())\n")
    assert [r["qualname"] for r in found] == [
        "<lambda>#1",
        "<lambda>#2",
        "<lambda>#1.<locals>.<lambda>#1",
    ]
    assert "admission" not in found[1]


def test_e10_unbound_lambda_has_no_invented_binding() -> None:
    found = rows("import m\nx = [lambda:m.f()]\n")
    assert found[0]["binding_name"] is None
    assert C.name_forms(found[0], "pkg.proxy") == [
        {"kind": "source_path", "value": "pkg/proxy.py"},
        {"kind": "package_path", "value": "pkg/"},
        {"kind": "dotted_module", "value": "pkg.proxy"},
        {"kind": "split_import", "module": "pkg", "name": "proxy"},
    ]


def test_e10_bound_name_forms_and_non_packaged_near_miss() -> None:
    found = rows("import m\nf=lambda:m.g()\n")[0]
    forms = C.name_forms(found, "pkg.proxy")
    assert forms[-2:] == [
        {"kind": "dotted_binding", "value": "pkg.proxy.f"},
        {"kind": "split_import", "module": "pkg.proxy", "name": "f"},
    ]
    assert all(f["kind"] in {"source_path", "package_path"} for f in C.name_forms(found, None))


def test_e10_named_ids_unchanged() -> None:
    found = rows("def f():\n def g():return 1\n return g\nclass C:\n def m(self):return 1\n")
    assert [r["qualname"] for r in found] == ["f", "f.<locals>.g", "C.m"]
    assert all(r["qualname"] == r["co_qualname"] for r in found)


def test_e10_mutually_exclusive_lambdas_are_not_n1_merged() -> None:
    found = rows("import m\nif flag:\n f=lambda:m.a()\nelse:\n f=lambda:m.b()\n")
    assert [r["qualname"] for r in found] == ["<lambda>#1", "<lambda>#2"]
    assert [r["binding_name"] for r in found] == ["f", "f"]
    C.assert_unique(found)
