from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from ci_triage import cli
from ci_triage.verify.build_verify import BuildVerifyResult


def _build_verify_args(tmp_path: Path) -> list[str]:
    src = tmp_path / "src"
    src.mkdir()
    edit_spec = tmp_path / "edit_spec.json"
    edit_spec.write_text("{}", encoding="utf-8")
    gbs_conf = tmp_path / "gbs.conf"
    gbs_conf.write_text("[general]\n", encoding="utf-8")
    evidence = tmp_path / "evidence.json"
    evidence.write_text("{}", encoding="utf-8")
    return [
        "build-verify",
        "--src-clean",
        str(src),
        "--base-commit",
        "a" * 40,
        "--edit-spec",
        str(edit_spec),
        "--gbs-conf",
        str(gbs_conf),
        "--package",
        "demo",
        "--workspace-root",
        str(tmp_path / "workspaces"),
        "--baseline-evidence",
        str(evidence),
        "--output-dir",
        str(tmp_path / "out"),
        "--iter-index",
        "1",
        "--state-db",
        str(tmp_path / "state.sqlite3"),
        "--build-id",
        "1095003",
        "--project",
        "platform/test/demo",
        "--branch",
        "tizen",
        "--arch",
        "standard-armv7l",
    ]


def test_cli_build_verify_help_uses_build_verify_parser(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["build-verify", "--help"])

    assert excinfo.value.code == 0
    output = capsys.readouterr().out
    assert "ci_triage build-verify" in output
    assert "--src-clean" in output
    assert "--base-commit" in output
    assert "--gbs-conf" in output
    assert "--workspace-root" in output


def test_cli_main_none_reads_sys_argv_for_build_verify(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, object] = {}

    def fake_build_verify(options: object) -> BuildVerifyResult:
        seen["options"] = options
        return BuildVerifyResult(
            result="PASS",
            verification_id="verify-1",
            verified_commit_sha="b" * 40,
            verified_tree_sha="c" * 40,
            worktree_path=str(tmp_path / "worktree"),
            build_log=str(tmp_path / "build.log"),
        )

    monkeypatch.setattr(sys, "argv", ["ci_triage", *_build_verify_args(tmp_path)])
    monkeypatch.setattr(cli, "build_verify", fake_build_verify)

    assert cli.main(None, extra_pythonpath=()) == 0
    assert seen["options"].__class__.__name__ == "BuildVerifyOptions"


def test_cli_build_verify_minimal_args_dispatches_to_build_verify(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = {"value": False}

    def fake_build_verify(options: object) -> BuildVerifyResult:
        called["value"] = True
        return BuildVerifyResult(result="FAIL", failure_stage="build_timeout")

    monkeypatch.setattr(cli, "build_verify", fake_build_verify)

    assert cli.main(_build_verify_args(tmp_path), extra_pythonpath=()) == 1
    assert called["value"] is True


def test_python_m_ci_triage_build_verify_help_smoke() -> None:
    env = os.environ.copy()
    scripts_path = str(Path("tizen-ci-triage/scripts").resolve())
    env["PYTHONPATH"] = (
        scripts_path
        if not env.get("PYTHONPATH")
        else scripts_path + os.pathsep + env["PYTHONPATH"]
    )
    result = subprocess.run(
        [sys.executable, "-m", "ci_triage", "build-verify", "--help"],
        check=False,
        text=True,
        capture_output=True,
        env=env,
    )

    assert result.returncode == 0
    assert "--src-clean" in result.stdout
    assert "--base-commit" in result.stdout


def test_cli_check_convergence_help_uses_check_convergence_parser(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["check-convergence", "--help"])

    assert excinfo.value.code == 0
    output = capsys.readouterr().out
    assert "ci_triage check-convergence" in output
    assert "--current-evidence" in output
    assert "--previous-evidence" in output
    assert "--touched-files" in output


def test_cli_check_convergence_writes_output(tmp_path: Path) -> None:
    current = tmp_path / "current.json"
    previous = tmp_path / "previous.json"
    output = tmp_path / "result.json"
    packet = {
        "primary_error": {
            "kind": "werror",
            "file": "src/foo.c",
            "line": 1,
            "message": "error: use of 'OldApi' [-Werror,-Wdeprecated-declarations]",
        }
    }
    current.write_text(json.dumps(packet), encoding="utf-8")
    previous.write_text(json.dumps(packet), encoding="utf-8")

    assert (
        cli.main(
            [
                "check-convergence",
                "--current-evidence",
                str(current),
                "--previous-evidence",
                str(previous),
                "--output",
                str(output),
            ]
        )
        == 0
    )

    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["verdict"] == "stalled"


def test_cli_check_convergence_reports_missing_file(tmp_path: Path) -> None:
    assert (
        cli.main(
            [
                "check-convergence",
                "--current-evidence",
                str(tmp_path / "missing.json"),
                "--output",
                str(tmp_path / "out.json"),
            ]
        )
        == 2
    )


def test_cli_check_convergence_reports_invalid_json(tmp_path: Path) -> None:
    current = tmp_path / "current.json"
    current.write_text("{bad", encoding="utf-8")

    assert (
        cli.main(
            [
                "check-convergence",
                "--current-evidence",
                str(current),
                "--output",
                str(tmp_path / "out.json"),
            ]
        )
        == 3
    )


def test_python_m_ci_triage_check_convergence_help_smoke() -> None:
    env = os.environ.copy()
    scripts_path = str(Path("tizen-ci-triage/scripts").resolve())
    env["PYTHONPATH"] = (
        scripts_path
        if not env.get("PYTHONPATH")
        else scripts_path + os.pathsep + env["PYTHONPATH"]
    )
    result = subprocess.run(
        [sys.executable, "-m", "ci_triage", "check-convergence", "--help"],
        check=False,
        text=True,
        capture_output=True,
        env=env,
    )

    assert result.returncode == 0
    assert "--current-evidence" in result.stdout
    assert "--output" in result.stdout


def test_single_build_help_smoke(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--help"])

    assert excinfo.value.code == 0
    assert "QuickBuild build id" in capsys.readouterr().out


def test_batch_help_smoke(capsys: pytest.CaptureFixture[str]) -> None:
    from ci_triage import batch_cli

    with pytest.raises(SystemExit) as excinfo:
        batch_cli.main(["--help"])

    assert excinfo.value.code == 0
    assert "Discover recent QuickBuild failures" in capsys.readouterr().out
