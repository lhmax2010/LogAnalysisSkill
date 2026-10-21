"""The offline test launcher must never fall back to the user's desktop."""

import importlib.util
import os
from pathlib import Path

import pytest
from test_qb_browser_node import browser_paths

SPEC = importlib.util.spec_from_file_location(
    "quiet_runner", Path(__file__).resolve().parents[1] / "run_quiet.py"
)
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def test_private_display_preserves_arguments_and_parent_environment(monkeypatch):
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.setenv("XAUTHORITY", "/desktop/auth")
    monkeypatch.setattr(runner.shutil, "which", lambda name, **_: f"/bin/{name}")
    before = dict(os.environ)
    args = ["tests/unit", "-q", "-k", "browser and not slow"]
    argv, env = runner.command(args)
    assert argv[-len(args):] == args
    assert argv[4:7] == [runner.sys.executable, "-m", "pytest"]
    assert "--auto-servernum" in argv
    assert "-nolisten tcp" in argv[3]
    assert env["P5Q_TEST_DISPLAY"] == "virtual"
    assert not {"DISPLAY", "WAYLAND_DISPLAY", "XAUTHORITY"} & env.keys()
    assert dict(os.environ) == before


@pytest.mark.parametrize("missing", ["xvfb-run", "Xvfb", "xauth"])
def test_missing_display_dependency_never_launches(monkeypatch, capsys, missing):
    monkeypatch.setattr(
        runner.shutil, "which", lambda name, **_: None if name == missing else f"/bin/{name}"
    )
    monkeypatch.setattr(runner.os, "execvpe", lambda *_: pytest.fail("unexpected launch"))
    assert runner.main() == 2
    assert "refusing desktop browser fallback" in capsys.readouterr().err


def test_launcher_replaces_process_without_shell(monkeypatch):
    monkeypatch.setattr(runner.shutil, "which", lambda name, **_: f"/bin/{name}")
    monkeypatch.setattr(runner.sys, "argv", ["run_quiet.py", "-q"])
    calls = []
    monkeypatch.setattr(runner.os, "execvpe", lambda *args: calls.append(args))
    assert runner.main() == 0
    assert len(calls) == 1
    executable, argv, env = calls[0]
    assert executable == "/bin/xvfb-run"
    assert argv[-1] == "-q"
    assert env["P5Q_TEST_DISPLAY"] == "virtual"


@pytest.mark.parametrize("private", [False, True])
def test_browser_tests_require_explicit_virtual_display(monkeypatch, tmp_path, private):
    executable = tmp_path / "runtime"
    executable.touch()
    monkeypatch.setenv("P5Q_TEST_PLAYWRIGHT", str(executable))
    monkeypatch.setenv("P5Q_TEST_CHROMIUM", str(executable))
    monkeypatch.setenv("DISPLAY", ":123")
    monkeypatch.delenv("P5Q_TEST_DISPLAY", raising=False)
    if private:
        monkeypatch.setenv("P5Q_TEST_DISPLAY", "virtual")
        assert browser_paths() == (str(executable), str(executable))
    else:
        with pytest.raises(pytest.fail.Exception, match="private display"):
            browser_paths()
