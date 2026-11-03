from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_campaign_batch2_intake import case as case
from test_campaign_fake_ssh import transport as transport
from tizen_baseline_reproduce import baseline
from tizen_campaign_core import campaign_state as state
from tizen_campaign_core import reproduce
from tizen_campaign_core._campaign_io import lock
from tizen_campaign_core._campaign_workspace import _StepError
from tizen_campaign_intake import intake
from tizen_campaign_report import report


@pytest.fixture
def prepared(case, monkeypatch, tmp_path):
    first = intake.add_unit(case.args)
    binary = case.transport[0].parent / "bin/gbs"
    binary.write_text(
        "#!/usr/bin/env python3\nimport os, pathlib, sys\n"
        "sys.stdout.write(pathlib.Path(os.environ['FAKE_BASELINE_LOG']).read_text())\n"
        "sys.exit(int(os.environ['FAKE_BASELINE_EXIT']))\n"
    )
    binary.chmod(0o700)
    monkeypatch.setenv("FAKE_BASELINE_LOG", str(case.args.ci_log))
    monkeypatch.setenv("FAKE_BASELINE_EXIT", "1")
    args = SimpleNamespace(
        state_db=case.db.path,
        config=case.args.config,
        arch="standard-aarch64",
        campaign_unit_key=case.key,
        src_clean=Path(first["src_clean"]),
        base_commit=case.args.base_commit,
        package=case.args.spec_name,
        profile=case.args.toolchain_profile,
        gbs_conf=Path(case.settings["clang_conf_path"]),
        evidence_ci=None,
        output_dir=tmp_path / "baseline-aarch64",
        wall_timeout=10,
        keep_copy=False,
    )
    return case, args


def test_baseline_three_arches_real_analyzer_and_fake_gbs(prepared, monkeypatch, tmp_path):
    case, args = prepared
    code, payload = baseline.run(args)
    assert code == 0 and payload["outcome"] == "matched"
    assert not (args.output_dir / "baseline_ws/iter_0").exists()
    args.arch, args.output_dir = "standard-armv7l", tmp_path / "arm"
    code, payload = baseline.run(args)
    assert code == 0 and payload["outcome"] == "matched"
    monkeypatch.setenv("FAKE_BASELINE_EXIT", "0")
    args.arch, args.output_dir = "standard-x86_64", tmp_path / "x86"
    code, payload = baseline.run(args)
    assert code == 0 and payload["outcome"] == "baseline_pass" and payload["synthetic_zero_error"]
    assert (
        Path(payload["evidence_local"]).read_bytes()
        == (
            json.dumps(baseline.EMPTY, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            + "\n"
        ).encode()
    )
    assert state.latest_status(case.db, case.key) == "BASELINE_REPRODUCED"
    assert state.invocations_used(case.db, case.key) == 0


@pytest.mark.parametrize("pass_build", [True, False])
def test_primary_not_reproduced(prepared, monkeypatch, pass_build):
    case, args = prepared
    if pass_build:
        monkeypatch.setenv("FAKE_BASELINE_EXIT", "0")
    else:
        other = (
            Path(__file__).resolve().parents[1] / "fixtures/e2e_link_undefined_reference/buildlog"
        )
        monkeypatch.setenv("FAKE_BASELINE_LOG", str(other))
    code, payload = baseline.run(args)
    assert code == 4 and payload["error_code"] == "NOT_REPRODUCED"
    assert state.latest_status(case.db, case.key) == "NOT_REPRODUCED"
    assert Path(payload["evidence_local"]).is_file()


def test_secondary_requires_primary_before_any_event(prepared):
    case, args = prepared
    args.arch = "standard-armv7l"
    before = case.db.path.read_bytes()
    with pytest.raises(_StepError) as error:
        baseline.run(args)
    assert error.value.code == "REJECTED_PRIMARY_BASELINE_MISSING"
    assert case.db.path.read_bytes() == before
    assert not args.output_dir.exists()


def test_secondary_different_failure_and_primary_pass(prepared, monkeypatch, tmp_path):
    case, args = prepared
    monkeypatch.setenv("FAKE_BASELINE_EXIT", "0")
    baseline.run(args)
    args.arch, args.output_dir = "standard-armv7l", tmp_path / "arm"
    monkeypatch.setenv("FAKE_BASELINE_EXIT", "1")
    code, payload = baseline.run(args)
    assert code == 0 and payload["outcome"] == "different_failure"
    assert state.latest_status(case.db, case.key) != "BASELINE_REPRODUCED"


@pytest.mark.parametrize("field", ["base_commit", "package", "profile", "gbs_conf", "evidence_ci"])
def test_baseline_inputs_validated_before_build(prepared, monkeypatch, tmp_path, field):
    case, args = prepared
    monkeypatch.setattr(baseline, "run_gbs_build", lambda *a: pytest.fail("build ran"))
    setattr(args, field, tmp_path / "wrong" if field in {"gbs_conf", "evidence_ci"} else "wrong")
    with pytest.raises((ValueError, _StepError)):
        baseline.run(args)


def test_baseline_anchor_tamper_refused(prepared):
    case, args = prepared
    (case.root / "ci_evidence.json").write_text("{}")
    with pytest.raises(_StepError) as error:
        baseline.run(args)
    assert error.value.code == "REJECTED_CI_EVIDENCE_MISMATCH"


def test_baseline_abandoned_and_lock(prepared, monkeypatch):
    case, args = prepared
    with lock(case.root / "aarch64/.repair_step.lock"):
        with pytest.raises(_StepError) as error:
            baseline.run(args)
        assert error.value.code == "CAMPAIGN_STATE_BUSY"
    report.release(case.db, case.key, case.settings, "Operator", True)
    monkeypatch.setattr(baseline, "create_worktree", lambda *a: pytest.fail("copy created"))
    with pytest.raises(_StepError) as error:
        baseline.run(args)
    assert error.value.code == "REJECTED_UNIT_ABANDONED"


def test_abandon_cannot_interleave_after_baseline_check(prepared, monkeypatch):
    case, args = prepared
    original = baseline.create_worktree

    def create(*a):
        with pytest.raises(report._Reject) as error:
            report.release(case.db, case.key, case.settings, "Operator", True)
        assert error.value.code == "CAMPAIGN_STATE_BUSY"
        return original(*a)

    monkeypatch.setattr(baseline, "create_worktree", create)
    assert baseline.run(args)[0] == 0


@pytest.mark.parametrize("failure", ["timeout", "missing_gbs", "analyzer"])
def test_baseline_tooling_failures_cleanup(prepared, monkeypatch, failure):
    from dataclasses import replace

    case, args = prepared
    original = baseline.run_gbs_build

    def run(options):
        result = original(options)
        return replace(
            result, timed_out=failure == "timeout", exit_code=127 if failure == "missing_gbs" else 1
        )

    monkeypatch.setattr(baseline, "run_gbs_build", run)
    if failure == "analyzer":

        def fail(*a, **kw):
            raise ValueError("bad analyzer")

        monkeypatch.setattr(baseline, "analyze", fail)
    with pytest.raises(_StepError) as error:
        baseline.run(args)
    assert error.value.code == "BASELINE_TOOLING_FAILED"
    assert not (args.output_dir / "baseline_ws/iter_0").exists()
    assert state.latest_reproduce(case.db, case.key, arch_norm="aarch64") is None


def test_keep_copy_and_residual_cleanup_event(prepared):
    case, args = prepared
    args.keep_copy = True
    baseline.run(args)
    assert (args.output_dir / "baseline_ws/iter_0").is_dir()
    args.keep_copy = False
    baseline.run(args)
    assert state.latest_event(case.db, case.key, "WORKSPACE_CLEANUP") is not None
    assert not (args.output_dir / "baseline_ws/iter_0").exists()


def test_reproduce_ignores_count_but_compares_phase_and_identity():
    import copy

    ci = dict(
        primary_error=dict(
            file="src/a.c", diagnostic_code="-Werror=abc", symbol="foo", phase="%build"
        )
    )
    local = copy.deepcopy(ci)
    local["error_clusters"] = dict(
        clusters=[dict(kind="compiler", diagnostic_kinds=["compiler"], count=5)]
    )

    def check():
        return reproduce.check(
            ci, local, package="p", arch_norm="aarch64", toolchain_profile="clang"
        )

    assert check().reproduced and check().basis["error_count_drift"]
    local["primary_error"]["phase"] = "%prep"
    assert not check().reproduced
    local["primary_error"]["phase"] = "%build"
    local["primary_error"]["symbol"] = "other"
    assert not check().reproduced
