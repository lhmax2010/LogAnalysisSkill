"""Terminal item4: six timeout mappings and unchanged external interruption."""

import importlib
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

F = importlib.import_module("tizen_gerrit_fetch.gerrit")
S = importlib.import_module("tizen_gerrit_submit.gerrit_submit")
W = importlib.import_module("tizen_ci_shared.workspace")


@pytest.mark.parametrize(
    "surface", ["query", "fetch-git", "submit-git", "remote", "shared-git", "exclude"]
)
@pytest.mark.parametrize("fault", ["timeout", "interrupt", "exit"])
def test_six_surfaces_timeout_and_interruption(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, surface: str, fault: str
) -> None:
    calls = []
    error: BaseException = (
        subprocess.TimeoutExpired(["fixture", surface], 0.125)
        if fault == "timeout"
        else KeyboardInterrupt()
        if fault == "interrupt"
        else SystemExit(9)
    )

    def runner(argv: Any, **kwargs: Any) -> Any:
        calls.append((argv, kwargs))
        raise error

    def invoke() -> Any:
        if surface == "query":
            return F.query_change_for_commit("abc", subprocess_runner=runner, timeout=0.125)
        if surface == "fetch-git":
            return F._run_git(["git", "status"], runner, env={}, timeout=0.125)
        if surface == "submit-git":
            return S._run_git(tmp_path, ["status"], runner, timeout=0.125)
        if surface == "remote":
            return S._target_warnings(
                SimpleNamespace(project="p", base_commit="abc"),
                SimpleNamespace(
                    submit_target="refs/for/main",
                    gerrit_user="u",
                    gerrit_host="h",
                    gerrit_port="1",
                    git_ssh_command=None,
                ),
                runner,
                timeout=0.125,
            )
        monkeypatch.setattr(W.subprocess, "run", runner)
        if surface == "shared-git":
            return W._run_git(["status"], timeout=0.125)
        return W._exclude_private_files(tmp_path, timeout=0.125)

    if fault != "timeout":
        with pytest.raises(type(error)) as caught:
            invoke()
        assert caught.value is error
    elif surface == "remote":
        assert invoke() == ["target_head_unknown:timeout"]
    else:
        cls = (
            F.GerritError
            if surface in {"query", "fetch-git"}
            else S.GerritSubmitError
            if surface == "submit-git"
            else W.WorkspaceViolation
        )
        with pytest.raises(cls) as caught:
            invoke()
        assert caught.value.__cause__ is error
        assert str(caught.value) == (
            "GIT_TIMEOUT: " if surface in {"shared-git", "exclude"} else ""
        ) + str(error)
        if surface in {"shared-git", "exclude"}:
            assert not hasattr(caught.value, "code")
        else:
            assert caught.value.code == (
                "GIT_TIMEOUT" if surface == "submit-git" else "FETCH_TIMEOUT"
            )
    assert len(calls) == 1 and calls[0][1]["timeout"] == 0.125
    assert list(tmp_path.iterdir()) == []
