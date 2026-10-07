"""E8 artificial participant and alias fixed-point controls; no OBS production."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
saved = sys.path[:]
sys.path.insert(0, str(ROOT / "docs/clang-fix-campaign/tools"))
try:
    P = importlib.import_module("terminal_monitored_preflight")
    A = importlib.import_module("terminal_alias_preflight")
finally:
    sys.path[:] = saved


def inspect(source: str) -> dict[str, Any]:
    return dict(P.inspect_source(source, "fixture.py", "."))


@pytest.mark.parametrize(
    "source",
    [
        'def f(*, runner=subprocess.run): runner([sys.executable, "-m", "sentinel"])',
        'def g(r): r([sys.executable, "-m", "sentinel"])\ndef f(runner=subprocess.run): g(runner)',
        'real_run=subprocess.run\ndef f():\n def inner(): real_run(["python", "-m", "sentinel"])',
        'def f(runner=subprocess.run):\n runner=fake\n runner(["python", "-m", "sentinel"])',
        'run=subprocess.run\nagain=run\nagain(["python", "-m", "sentinel"])',
    ],
)
def test_e8_fixed_point_reaches_alias_call(source: str) -> None:
    result = inspect("import sys, subprocess\n" + source)
    calls = [p for p in result["participants"] if p["kind"] == "ALIAS_CALL"]
    assert len(calls) == 1
    assert calls[0]["forms"] == ["C8a"]
    assert calls[0]["payload"]["payload"] == "sentinel"
    assert calls[0]["source_reads"]
    assert not result["dynamic_unresolved"]
    assert result["alias_bindings"][-1]["source_reads"]


def test_e8_cross_module_keyword_and_shim_resolution() -> None:
    units = [
        A.Unit(
            "import subprocess, shim as mod\nmod.f(runner=subprocess.run)", "test.py", ".", "test"
        ),
        A.Unit("from actual import f", "shim.py", ".", "shim"),
        A.Unit(
            'def f(*, runner): runner(["python", "-m", "sentinel"])', "actual.py", ".", "actual"
        ),
    ]
    world = A.AliasWorld(units)
    world.run()
    calls = world.result("actual.py")["participants"]
    assert len(calls) == 1 and calls[0]["forms"] == ["C8a"]
    assert calls[0]["source_reads"][0]["path"] == "test.py"
    assert not world.dynamic


@pytest.mark.parametrize(
    "source",
    [
        "self._run=subprocess.run",
        "def f(): return subprocess.run",
        "h(*[subprocess.run])",
        "f=lambda runner=subprocess.run: None",
        "def f(*args): pass\nf(subprocess.run)",
        "def f(**kwargs): pass\nf(runner=subprocess.run)",
        "def f(runner=subprocess.run): return runner",
        "def f(runner=subprocess.run): runner.attr",
    ],
)
def test_e8_c8c_escape(source: str) -> None:
    result = inspect("import subprocess\n" + source)
    dynamic = result["dynamic_unresolved"]
    assert len(dynamic) == 1 and dynamic[0]["category"] == "C8c_ESCAPE"
    assert not [p for p in result["participants"] if p["match_count"] != 1]


@pytest.mark.parametrize(
    "source",
    [
        "def f(p: subprocess.Popen[str]): pass",
        "def f() -> subprocess.Popen[str]: pass",
        "p: subprocess.Popen[str]",
        "p: importlib.import_module",
    ],
)
def test_e8_annotation_read_excluded(source: str) -> None:
    result = inspect("import subprocess, importlib\n" + source)
    assert len(result["excluded_annotations"]) == 1
    assert all(p["kind"] == "IMPORT_ALIAS" for p in result["participants"])
    assert not result["dynamic_unresolved"]


def test_annotation_call_is_not_excluded() -> None:
    result = inspect("import importlib\ndef f(x: importlib.reload(m)): pass")
    assert any(p["match_count"] == 0 for p in result["participants"])


def test_non_process_bare_read_remains_unknown() -> None:
    result = inspect("import importlib\nf=importlib.import_module")
    assert len([p for p in result["participants"] if p["match_count"] == 0]) == 1


def test_nested_rebinding_does_not_inherit_alias() -> None:
    result = inspect("""import subprocess
real_run=subprocess.run
def inner(real_run): real_run(["python", "-m", "not_a_process"])
""")
    assert not [p for p in result["participants"] if p["kind"] == "ALIAS_CALL"]


def test_different_signatures_are_dynamic() -> None:
    result = inspect("""import subprocess, os
def f(runner): runner("python -m sentinel")
f(subprocess.run)
f(os.system)
""")
    assert len(result["dynamic_unresolved"]) == 1
    assert result["dynamic_unresolved"][0]["category"] == "ALIAS_PAYLOAD"
    assert "different" in result["dynamic_unresolved"][0]["detail"]


@pytest.mark.parametrize(
    "name,args",
    [
        ("os.system", '"python -m sentinel"'),
        ("os.execve", '"/python", ["python", "-m", "sentinel"], env'),
        ("os.spawnve", '0, "/python", ["python", "-m", "sentinel"], env'),
        ("os.execlp", '"python", "python", "-m", "sentinel"'),
        ("os.spawnle", '0, "python", "python", "-m", "sentinel", env'),
        ("os.posix_spawn", '"python", ["python", "-m", "sentinel"], env'),
        ("pty.spawn", '["python", "-m", "sentinel"]'),
        ("asyncio.create_subprocess_exec", '"python", "-m", "sentinel"'),
        ("subprocess.run", 'args=["python", "-m", "sentinel"]'),
    ],
)
def test_alias_signature_payloads(name: str, args: str) -> None:
    result = inspect(f"import os, subprocess, asyncio, pty\nrun={name}\nrun({args})")
    calls = [p for p in result["participants"] if p["kind"] == "ALIAS_CALL"]
    assert len(calls) == 1 and calls[0]["forms"] == ["C8a"]
    assert not result["dynamic_unresolved"]


def test_alias_code_payload_is_scanned() -> None:
    result = inspect('import subprocess\nr=subprocess.run\nr(["python", "-c", "f=eval"])')
    assert any(
        p["qualified_name"] == "builtins.eval" and p["match_count"] == 0
        for p in result["participants"]
    )


@pytest.mark.parametrize("factory", ["spec_from_file_location", "spec_from_loader", "find_spec"])
def test_c5f_links_unique_c5d(factory: str) -> None:
    result = inspect(f"""import importlib.util
spec=importlib.util.{factory}("n", "sentinel.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
""")
    calls = [p for p in result["participants"] if p["forms"] == ["C5f"]]
    assert len(calls) == 1 and calls[0]["c5d_link"]["line"] == 2
    assert not result["dynamic_unresolved"]


@pytest.mark.parametrize(
    "source",
    [
        "def load(loader,m): loader.exec_module(m)",
        'spec=importlib.util.find_spec("n")\nspec=other\nspec.loader.exec_module(m)',
        'spec=importlib.util.find_spec("n")\ndef f(): spec.loader.exec_module(m)',
    ],
)
def test_c5f_unproven_receiver_is_dynamic(source: str) -> None:
    result = inspect("import importlib.util\n" + source)
    assert len(result["dynamic_unresolved"]) == 1
    assert result["dynamic_unresolved"][0]["category"] == "C5f"


def test_c5f_constructor_not_swallowed() -> None:
    result = inspect('import importlib.machinery\nimportlib.machinery.SourceFileLoader("n", p)')
    assert len([p for p in result["participants"] if p["match_count"] == 0]) == 1
