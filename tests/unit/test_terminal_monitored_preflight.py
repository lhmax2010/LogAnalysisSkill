"""E7 preflight controls only; these do not certify consumer-edge detection."""

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
finally:
    sys.path[:] = saved


def inspect(source: str) -> dict[str, Any]:
    return dict(P.inspect_source(source, "fixture.py", "."))


@pytest.mark.parametrize(
    "statement",
    [
        'compile(src, "<x>", "exec")',
        "callback = compile",
        'import builtins\nbuiltins.compile(src, "<x>", "exec")',
    ],
)
def test_compile_call_and_read_excluded(statement: str) -> None:
    result = inspect(statement)
    assert len(result["excluded_compile"]) == 1
    assert not [p for p in result["participants"] if p["match_count"] != 1]


@pytest.mark.parametrize(
    "source",
    [
        'exec("import sentinel")',
        'eval("1")',
        "exec(code_var)",
        'exec(compile(src, "<x>", "exec"))',
    ],
)
def test_c9_classification(source: str) -> None:
    result = inspect(source)
    calls = [p for p in result["participants"] if p["kind"] == "CALL"]
    assert len(calls) == 1 and calls[0]["forms"] == ["C9"]
    if "sentinel" in source:
        assert any(
            p["qualified_name"] == "sentinel" and p["origin"] != "file"
            for p in result["participants"]
        )


@pytest.mark.parametrize(
    "source,name",
    [
        ("import subprocess\ndef f(runner=subprocess.run): pass", "subprocess.run"),
        ("import subprocess as sp\nf = sp.Popen", "subprocess.Popen"),
        ("from importlib import reload as again\nf = again", "importlib.reload"),
        ("import importlib\nimportlib.reload(module)", "importlib.reload"),
        ("f = eval", "builtins.eval"),
        ("import sys\nsys.modules.update({})", "sys.modules.update"),
        ("import sys\nf = sys.modules.items", "sys.modules.items"),
    ],
)
def test_monitored_unknown_forms_are_red(source: str, name: str) -> None:
    red = [p for p in inspect(source)["participants"] if p["match_count"] != 1]
    assert len(red) == 1 and red[0]["qualified_name"] == name


@pytest.mark.parametrize(
    "source",
    [
        "def f(eval):\n    eval(data)",
        "import subprocess\ndef f(subprocess):\n    return subprocess.run",
        "import subprocess\ndef f():\n    subprocess = local\n    return subprocess.run",
        "def exec(value): pass\nexec(data)",
        "import re\nre.compile('x')",
        "import subprocess\nsubprocess.run(['git', 'status'])",
        "import sys\nsys.modules['x'] = value\nx = sys.modules.get('x')\nassert 'x' in sys.modules",
        "import unittest.mock\nunittest.mock.MagicMock()",
    ],
)
def test_shadowing_and_known_calls_do_not_false_alarm(source: str) -> None:
    assert not [p for p in inspect(source)["participants"] if p["match_count"] != 1]


def test_source_loader_method_provenance_without_execution() -> None:
    source = """import importlib.util
from pathlib import Path
path = Path("never_executed.py")
spec = importlib.util.spec_from_file_location("fixture", path)
assert spec is not None and spec.loader is not None
spec.loader.exec_module(module)
"""
    red = [p for p in inspect(source)["participants"] if p["match_count"] != 1]
    assert len(red) == 1
    assert red[0]["qualified_name"] == "importlib.machinery.SourceFileLoader.exec_module"


def test_lookalike_loader_is_not_importlib() -> None:
    assert inspect("def f(spec): spec.loader.exec_module(m)")["participants"] == []


def test_all_points_collected_instead_of_first_failure() -> None:
    result = inspect("import subprocess\na = subprocess.run\nb = subprocess.Popen\nf = eval")
    assert len([p for p in result["participants"] if p["match_count"] == 0]) == 3


def test_docstring_doctest_and_c_payload_are_scanned() -> None:
    result = inspect('''""">>> import subprocess
>>> f = subprocess.run
"""
import subprocess
subprocess.run(["python3", "-c", "f = eval"])
''')
    red = [p for p in result["participants"] if p["match_count"] == 0]
    assert {p["qualified_name"] for p in red} == {"subprocess.run", "builtins.eval"}


def test_invalid_embedded_python_is_not_silent() -> None:
    assert inspect('exec("if")')["parse_errors"]


def test_multiple_bindings_are_not_arbitrarily_selected() -> None:
    result = inspect("""if flag:
    from importlib import import_module as invoke
else:
    from unittest.mock import patch as invoke
invoke("pkg")
""")
    red = [p for p in result["participants"] if p["match_count"] != 1]
    assert len(red) == 1 and red[0]["forms"] == ["C2a", "C3"]


def test_one_known_binding_does_not_hide_one_unknown() -> None:
    result = inspect("""if flag:
    from importlib import import_module as invoke
else:
    from importlib import reload as invoke
invoke("pkg")
""")
    assert any(p["match_count"] == 0 for p in result["participants"])


def test_pytest_monkeypatch_context_binding() -> None:
    result = inspect("""import pytest
with pytest.MonkeyPatch.context() as mp:
    mp.setattr("pkg.attr", value)
""")
    assert any(p["forms"] == ["C3"] for p in result["participants"])
