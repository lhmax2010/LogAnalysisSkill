from __future__ import annotations

import io
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from test_campaign_fake_ssh import transport as transport
from tizen_campaign_core import campaign_state as state
from tizen_campaign_core._campaign_io import lock, publish
from tizen_campaign_core._campaign_workspace import (
    _StepError,
    _unit_hash,
    _validate_source_identity,
)
from tizen_campaign_core._sandbox_git import SandboxGit
from tizen_campaign_core.submission_identity import build_campaign_unit_key
from tizen_campaign_intake import intake
from tizen_ci_shared.state import StateDatabase

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def case(tmp_path, transport):
    git = SandboxGit()
    seed = tmp_path / "seed"
    git.run(None, "init", str(seed))
    (seed / "src").mkdir()
    (seed / "src/clang_case.c").write_text("int main() { return missing; }\n")
    git.run(seed, "add", ".")
    git.run(
        seed,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "-m",
        "seed",
    )
    sha = git.run(seed, "rev-parse", "HEAD").stdout.strip()
    git.run(
        seed,
        "push",
        "ssh://gerrit.invalid:29418/platform/upstream/example",
        "HEAD:refs/heads/main",
        remote=True,
    )
    conf = tmp_path / "clang.conf"
    conf.write_text("[general]\n")
    settings = dict(
        campaign_workspace=str(tmp_path / "ws"),
        clang_conf_path=str(conf),
        gerrit_ssh_base="ssh://gerrit.invalid:29418",
        max_rounds=3,
        max_build_invocations=9,
    )
    config = tmp_path / "campaign.yaml"
    config.write_text(yaml.safe_dump(settings))
    args = SimpleNamespace(
        state_db=tmp_path / "state.db",
        config=config,
        ci_log=FIXTURES / "e2e_clang_compile/buildlog",
        project="platform/upstream/example",
        branch="tizen_base",
        spec_name="example",
        base_commit=sha,
        source_build_id="101",
        failed_arches="standard-x86_64,standard-aarch64",
        toolchain_profile="clang",
    )
    key = build_campaign_unit_key(
        ci_system="quickbuild",
        **{
            k: getattr(args, k)
            for k in ("project", "branch", "spec_name", "base_commit", "source_build_id")
        },
    )
    return SimpleNamespace(
        args=args,
        db=StateDatabase(args.state_db),
        settings=settings,
        key=key,
        root=Path(settings["campaign_workspace"]) / _unit_hash(key),
        transport=transport,
    )


def test_intake_ssh_clone_marker_identity_and_idempotence(case):
    first = intake.add_unit(case.args)
    assert first["created"] and first["primary_arch"] == "standard-aarch64"
    src = Path(first["src_clean"])
    assert set(json.loads((src / ".campaign_clone").read_text())) == {
        "unit_key",
        "project",
        "base_commit",
    }
    assert (
        SandboxGit().run(src, "remote", "get-url", "origin").stdout.strip()
        == "ssh://gerrit.invalid:29418/platform/upstream/example"
    )
    _validate_source_identity(
        src, state.get_unit(case.db, case.key), subprocess_runner=intake._identity_runner
    )
    before = case.db.path.read_bytes()
    second = intake.add_unit(case.args)
    assert second == dict(first, created=False)
    assert case.db.path.read_bytes() == before
    assert state.latest_status(case.db, case.key) == "CI_EVIDENCE_READY"


def test_intake_absolute_remote_rejected_in_staging(case):
    case.settings["gerrit_ssh_base"] = str(case.transport[0])
    case.args.config.write_text(yaml.safe_dump(case.settings))
    with pytest.raises(_StepError, match="source HEAD or origin") as error:
        intake.add_unit(case.args)
    assert error.value.code == "REJECTED_IDENTITY_MISMATCH"
    assert error.value.exit_code == 4
    assert not (case.root / "src").exists()
    assert not list(case.root.glob(".src.staging-*"))


@pytest.mark.parametrize("change", ["head", "origin", "marker", "extra_marker_key"])
def test_existing_source_identity_never_repaired(case, change):
    result = intake.add_unit(case.args)
    src = Path(result["src_clean"])
    git = SandboxGit()
    if change == "head":
        git.run(
            src,
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "--allow-empty",
            "-m",
            "other",
        )
    elif change == "origin":
        git.run(src, "remote", "set-url", "origin", "ssh://gerrit.invalid:29418/other")
    else:
        marker = json.loads((src / ".campaign_clone").read_text())
        marker["extra" if change == "extra_marker_key" else "unit_key"] = "bad"
        (src / ".campaign_clone").write_text(json.dumps(marker))
    before = (src / ".campaign_clone").read_bytes()
    with pytest.raises(_StepError) as error:
        intake.add_unit(case.args)
    assert error.value.code == "REJECTED_IDENTITY_MISMATCH"
    assert src.is_dir() and (src / ".campaign_clone").read_bytes() == before


def test_evidence_changed_log_preserves_old_bytes(case):
    intake.add_unit(case.args)
    before = (case.root / "ci_evidence.json").read_bytes()
    case.args.ci_log = FIXTURES / "e2e_link_undefined_reference/buildlog"
    with pytest.raises(_StepError) as error:
        intake.add_unit(case.args)
    assert error.value.code == "REJECTED_STATE_INCONSISTENT"
    assert (case.root / "ci_evidence.json").read_bytes() == before


def test_analyzer_failure_preserves_evidence_without_unit(case):
    case.root.mkdir(parents=True)
    (case.root / "ci_evidence.json").write_bytes(b"old")
    case.args.ci_log = case.root / "missing.log"
    with pytest.raises(_StepError) as error:
        intake.add_unit(case.args)
    assert error.value.code == "INTAKE_ANALYZER_FAILED"
    assert (case.root / "ci_evidence.json").read_bytes() == b"old"
    assert not case.db.path.exists()


def test_intake_lock_preserves_other_staging(case):
    with lock(case.root / ".intake.lock"):
        staging = case.root / ".src.staging-active"
        staging.mkdir()
        pid = os.fork()
        if pid == 0:
            try:
                intake.add_unit(case.args)
            except _StepError as error:
                os._exit(0 if error.code == "CAMPAIGN_STATE_BUSY" else 1)
            except BaseException:
                os._exit(2)
            os._exit(3)
        _, status = os.waitpid(pid, 0)
        assert os.waitstatus_to_exitcode(status) == 0
        assert staging.exists() and not case.db.path.exists()


@pytest.mark.parametrize("point", ["evidence", "unit", "clone", "checkout", "marker"])
def test_intake_crash_resume(case, monkeypatch, point):
    # A child exits without finally handlers, matching process death between publication steps.
    pid = os.fork()
    if pid == 0:
        if point == "evidence":
            monkeypatch.setattr(state, "create_unit", lambda *a, **kw: os._exit(77))
        elif point == "unit":
            monkeypatch.setattr(intake, "_prepare_source", lambda *a: os._exit(77))
        elif point == "marker":
            monkeypatch.setattr(intake.os, "rename", lambda *a: os._exit(77))
        else:
            original = SandboxGit.run

            def interrupted(self, cwd, *args, **kw):
                if args[0] == "clone" and point == "clone":
                    os._exit(77)
                result = original(self, cwd, *args, **kw)
                if args[0] == "checkout" and point == "checkout":
                    os._exit(77)
                return result

            monkeypatch.setattr(SandboxGit, "run", interrupted)
        try:
            intake.add_unit(case.args)
        except BaseException:
            os._exit(78)
        os._exit(79)
    _, status = os.waitpid(pid, 0)
    assert os.waitstatus_to_exitcode(status) == 77
    assert not (case.root / "src").exists()
    intake.add_unit(case.args)
    assert (case.root / "src/.campaign_clone").is_file()
    assert not list(case.root.glob(".src.staging-*"))


@pytest.mark.parametrize("same", [True, False])
def test_evidence_concurrent_hardlink_publication(tmp_path, same):
    import multiprocessing

    context = multiprocessing.get_context("fork")
    barrier = context.Barrier(2)
    queue = context.Queue()
    path = tmp_path / "ci.json"

    def worker(raw):
        barrier.wait()
        try:
            publish(path, raw)
            queue.put(True)
        except _StepError:
            queue.put(False)

    processes = [
        context.Process(target=worker, args=(raw,))
        for raw in [b"first", b"first" if same else b"second"]
    ]
    for process in processes:
        process.start()
    result = [queue.get(timeout=10) for _ in processes]
    for process in processes:
        process.join(10)
        assert process.exitcode == 0
    queue.close()
    assert sum(result) == (2 if same else 1)
    assert path.read_bytes() in (b"first", b"second")
    assert list(tmp_path.iterdir()) == [path]


def test_hardlink_failure_is_not_rename_fallback(tmp_path, monkeypatch):
    def reject(*a):
        raise OSError("unsupported")

    monkeypatch.setattr(os, "link", reject)
    with pytest.raises(_StepError) as error:
        publish(tmp_path / "ci.json", b"data")
    assert error.value.code == "WORKSPACE_FS_UNSUPPORTED"
    assert not list(tmp_path.iterdir())


def test_rejected_arch_has_no_analyzer_or_source(case, monkeypatch):
    case.args.failed_arches = "emulator-x86_64"
    monkeypatch.setattr(intake, "analyze", lambda *a: pytest.fail("analyzer ran"))
    with pytest.raises(_StepError) as error:
        intake.add_unit(case.args)
    assert error.value.code == "REJECTED_ARCH_NOT_ALLOWED"
    assert state.latest_status(case.db, case.key) == "REJECTED_ARCH_NOT_ALLOWED"
    assert not (case.root / "src").exists()


def test_intake_invalid_cli_json():
    output = io.StringIO()
    assert intake.main([], stdout=output) == 2
    assert json.loads(output.getvalue())["error_code"] == "INVALID_ARGS"


def test_clone_failure_cleans_staging(case, monkeypatch):
    import subprocess

    original = SandboxGit.run

    def fail_clone(self, cwd, *args, **kwargs):
        if args[0] == "clone":
            raise subprocess.CalledProcessError(128, "git")
        return original(self, cwd, *args, **kwargs)

    monkeypatch.setattr(SandboxGit, "run", fail_clone)
    with pytest.raises(_StepError) as error:
        intake.add_unit(case.args)
    assert (error.value.code, error.value.exit_code) == ("INTAKE_CLONE_FAILED", 5)
    assert not (case.root / "src").exists()
    assert not list(case.root.glob(".src.staging-*"))
