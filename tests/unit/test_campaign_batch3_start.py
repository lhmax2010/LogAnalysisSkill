import io
import json
import subprocess

import pytest
import yaml
from test_campaign_batch2_intake import case as case
from test_campaign_fake_ssh import transport as transport
from tizen_campaign_core._campaign_workspace import _StepError
from tizen_campaign_intake import intake, start_check


@pytest.fixture
def ready(case):
    case.settings.update(
        gerrit_user="test",
        git_author_identity="Test <test@example.invalid>",
        git_committer_identity="Test <test@example.invalid>",
        push_timeout_sec=120,
        push_retry=1,
        target_arches=["aarch64", "armv7l", "x86_64"],
    )
    case.args.config.write_text(yaml.safe_dump(case.settings))
    binary = case.transport[0].parent / "bin/gbs"
    binary.write_text("#!/bin/sh\nexit 0\n")
    binary.chmod(0o700)
    return case


def execute(c):
    out = io.StringIO()
    code = start_check.main(
        [
            "--config",
            str(c.args.config),
            "--state-root",
            str(c.root / "state"),
            "--project",
            c.args.project,
        ],
        stdout=out,
    )
    return code, json.loads(out.getvalue())


def test_all_five_checks_full_ssh_project(ready):
    code, payload = execute(ready)
    assert code == 0 and len(payload["checks"]) == 5
    calls = [json.loads(line) for line in ready.transport[2].read_text().splitlines()]
    assert calls[-1] == dict(command="git-upload-pack", path=str(ready.transport[1]))


@pytest.mark.parametrize("fault", ["config", "clang_conf", "gbs", "gerrit", "state_directory"])
def test_each_start_failure(ready, fault):
    if fault == "config":
        del ready.settings["git_author_identity"]
    elif fault == "clang_conf":
        ready.settings["clang_conf_path"] += ".missing"
    elif fault == "gbs":
        (ready.transport[0].parent / "bin/gbs").write_text("#!/bin/sh\nexit 3\n")
    elif fault == "gerrit":
        ready.args.project = "missing/project"
    else:
        ready.root.mkdir(parents=True)
        (ready.root / "state").write_text("not a directory")
    ready.args.config.write_text(yaml.safe_dump(ready.settings))
    code, payload = execute(ready)
    assert code == 4 and payload["error_code"] == "PREFLIGHT_FAILED"
    check = next(row for row in payload["checks"] if row["name"] == fault)
    assert not check["passed"]
    if fault == "gerrit":
        assert check["reason"] == "unreachable"


@pytest.mark.parametrize("project", [None, "../escape", "-option", "repo/", "repo name"])
def test_bad_project_precedes_subprocess(ready, monkeypatch, project):
    def forbidden(*a, **k):
        pytest.fail("subprocess started")

    monkeypatch.setattr(subprocess, "run", forbidden)
    args = ["--config", str(ready.args.config), "--state-root", str(ready.root / "state")]
    if project is not None:
        args += ["--project=" + project]
    assert start_check.main(args, stdout=io.StringIO()) == 4


def test_local_path_both_commands_reject(ready):
    ready.settings["gerrit_ssh_base"] = str(ready.transport[0])
    ready.args.config.write_text(yaml.safe_dump(ready.settings))
    code, payload = execute(ready)
    assert code == 4
    assert (
        next(row for row in payload["checks"] if row["name"] == "gerrit")["reason"]
        == "config_not_ssh"
    )
    with pytest.raises(_StepError) as error:
        intake.add_unit(ready.args)
    assert error.value.code == "REJECTED_IDENTITY_MISMATCH"
    assert not (ready.root / "src").exists() and not list(ready.root.glob(".src.staging-*"))
