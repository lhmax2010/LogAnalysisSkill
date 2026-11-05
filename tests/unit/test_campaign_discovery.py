from __future__ import annotations

import copy
import hashlib
import json
import os
import socket
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_campaign_batch2_intake import case as case
from test_campaign_fake_ssh import transport as transport
from tizen_campaign_core.discovery_manifest import SCHEMA, atomic_write, load, validate
from tizen_campaign_intake.discover import discover


def manifest_case(tmp_path, case):
    root = tmp_path / "state"
    run = root / "discovery/101/run-01"
    raw = case.args.ci_log.read_bytes()
    row = dict(
        spec_name="example",
        failed_arches=["standard-aarch64", "standard-x86_64"],
        primary_arch="standard-aarch64",
        project=case.args.project,
        branch=case.args.branch,
        base_commit=case.args.base_commit,
        log_path="logs/example.standard-aarch64.txt",
        log_sha256=hashlib.sha256(raw).hexdigest(),
        status="ok",
        reason=None,
    )
    value = dict(
        schema_version=SCHEMA,
        qb_project="tizen_base",
        build_id="101",
        child_build_id="102",
        captured_at="2026-11-05T00:00:00+00:00",
        report_dir="HTML REPORT",
        packages=[row],
    )
    atomic_write(run / row["log_path"], raw)
    path = run / "discover-manifest.json"
    atomic_write(path, json.dumps(value).encode())
    args = SimpleNamespace(
        manifest=path,
        state_root=root,
        state_db=case.args.state_db,
        config=case.args.config,
        dry_run=False,
        include_non_compile=False,
    )
    return args, value


def test_discovery_subprocess_boundary_clone_and_analyzer(tmp_path, case, monkeypatch):
    args, value = manifest_case(tmp_path, case)
    calls = []
    original = subprocess.Popen

    def popen(argv, *a, **kw):
        calls.append(list(argv))
        assert argv[0] in {"git", sys.executable}
        if argv[0] == sys.executable:
            assert argv[1:4] == ["-m", "gbs_analyzer", "analyze"]
        if "clone" in argv:
            assert argv[argv.index("clone") + 1] == (
                "ssh://gerrit.invalid:29418/" + value["packages"][0]["project"]
            )
        return original(argv, *a, **kw)

    def no_network(*a, **kw):
        pytest.fail("consumer opened a network socket")

    monkeypatch.setattr(subprocess, "Popen", popen)
    monkeypatch.setattr(socket, "create_connection", no_network)
    monkeypatch.setattr(socket.socket, "connect", no_network)
    first = discover(args)
    assert first["packages"][0]["status"] == "created", first
    before = args.state_db.read_bytes()
    second = discover(args)
    assert second["packages"][0]["status"] == "existing"
    assert args.state_db.read_bytes() == before
    assert any(argv[0] == sys.executable for argv in calls)
    assert any("clone" in argv for argv in calls)
    assert args.manifest.read_text() == json.dumps(value)
    destination = os.environ.get("RESTORE_DISCOVERY_EVIDENCE")
    if destination:
        Path(destination).mkdir(parents=True, exist_ok=True)
        (Path(destination) / "consumer-processes.json").write_text(
            json.dumps({"argv": calls, "http_requests": 0, "browser_processes": 0}, indent=2)
        )


@pytest.mark.parametrize(
    "change",
    [
        "extra",
        "missing",
        "project",
        "sha",
        "log_traversal",
        "primary",
        "duplicate",
        "status",
        "build",
        "timestamp",
    ],
)
def test_manifest_rejected_before_process_or_db(tmp_path, case, monkeypatch, change):
    args, value = manifest_case(tmp_path, case)
    row = value["packages"][0]
    if change == "extra":
        value["extra"] = True
    elif change == "missing":
        del row["reason"]
    elif change == "project":
        row["project"] = "../outside"
    elif change == "sha":
        row["log_sha256"] = "a" * 64
    elif change == "log_traversal":
        row["log_path"] = "../other.txt"
    elif change == "primary":
        row["primary_arch"] = "standard-x86_64"
    elif change == "duplicate":
        value["packages"].append(copy.deepcopy(row))
    elif change == "status":
        row["status"] = "invented"
    elif change == "build":
        value["build_id"] = "999"
    else:
        value["captured_at"] = "2026-11-05"
    args.manifest.write_text(json.dumps(value))
    monkeypatch.setattr(
        subprocess, "Popen", lambda *a, **kw: pytest.fail("process before validation")
    )
    with pytest.raises(ValueError):
        discover(args)
    assert not args.state_db.exists()


@pytest.mark.parametrize("which", ["manifest", "log"])
def test_resolve_rejects_symlink_escape(tmp_path, case, which):
    args, value = manifest_case(tmp_path, case)
    victim = (
        args.manifest
        if which == "manifest"
        else args.manifest.parent / value["packages"][0]["log_path"]
    )
    outside = tmp_path / "outside"
    outside.write_bytes(victim.read_bytes())
    victim.unlink()
    victim.symlink_to(outside)
    with pytest.raises(ValueError):
        load(args.manifest, args.state_root)


def test_dry_run_no_db_or_git_and_reports(tmp_path, case, monkeypatch):
    args, _ = manifest_case(tmp_path, case)
    args.dry_run = True
    original = subprocess.Popen

    def popen(argv, *a, **kw):
        assert argv[:4] == [sys.executable, "-m", "gbs_analyzer", "analyze"]
        return original(argv, *a, **kw)

    monkeypatch.setattr(subprocess, "Popen", popen)
    result = discover(args)
    assert result["packages"][0]["status"] == "dry_run", result
    assert not args.state_db.exists()
    assert "example | dry_run" in (Path(result["report_dir"]) / "discover.md").read_text()


@pytest.mark.parametrize(
    "status,reason",
    [
        ("DISCOVERY_SOURCE_UNRESOLVED", "SOURCE_VARIABLES"),
        ("DISCOVERY_LOG_UNREADABLE", "ENCODING"),
        ("DISCOVERY_REPORT_AMBIGUOUS", "REPORT_STRUCTURE"),
    ],
)
def test_manifest_status_passthrough(tmp_path, case, status, reason):
    args, value = manifest_case(tmp_path, case)
    value["packages"][0].update(status=status, reason=reason, log_path=None, log_sha256=None)
    args.manifest.write_text(json.dumps(validate(value)))
    assert discover(args)["packages"][0]["status"] == status
    assert not args.state_db.exists()


def test_manifest_atomic_no_overwrite(tmp_path):
    path = tmp_path / "manifest"
    atomic_write(path, b"first")
    with pytest.raises(ValueError):
        atomic_write(path, b"second")
    assert path.read_bytes() == b"first"
    assert not list(tmp_path.glob(".publish-*"))


def test_consumer_no_qb_import():
    root = Path(__file__).resolve().parents[2] / "tizen-campaign-intake/scripts"
    for path in root.rglob("*.py"):
        assert "tizen_qb_verify" not in path.read_text()


@pytest.mark.parametrize("dry", [False, True])
def test_arch_gate_before_analyzer_or_clone(tmp_path, case, monkeypatch, dry):
    args, value = manifest_case(tmp_path, case)
    args.dry_run = dry
    row = value["packages"][0]
    row.update(
        failed_arches=["emulator-x86_64"],
        primary_arch=None,
        status="ARCH_NOT_ALLOWED",
        reason="ARCH_NOT_ALLOWED",
        log_path=None,
        log_sha256=None,
    )
    args.manifest.write_text(json.dumps(value))
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: pytest.fail("arch before process"))
    assert discover(args)["packages"][0]["status"] == "ARCH_NOT_ALLOWED"
    if dry:
        assert not args.state_db.exists()
    else:
        from tizen_campaign_core import campaign_state as state

        assert state.latest_status(case.db, case.key) == "REJECTED_ARCH_NOT_ALLOWED"


@pytest.mark.parametrize("include", [False, True])
def test_compile_filter_and_explicit_override(tmp_path, case, include):
    args, value = manifest_case(tmp_path, case)
    args.dry_run, args.include_non_compile = True, include
    row = value["packages"][0]
    raw = (
        Path(__file__).parents[1] / "fixtures/e2e_link_undefined_reference/buildlog"
    ).read_bytes()
    (args.manifest.parent / row["log_path"]).write_bytes(raw)
    row["log_sha256"] = hashlib.sha256(raw).hexdigest()
    args.manifest.write_text(json.dumps(value))
    result = discover(args)["packages"][0]
    assert result["status"] == ("dry_run" if include else "skipped")
    assert result["reason"] == (None if include else "NON_COMPILE_FAILURE")
    assert not args.state_db.exists()
