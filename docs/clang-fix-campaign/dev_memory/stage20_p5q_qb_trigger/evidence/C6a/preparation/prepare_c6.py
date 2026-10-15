"""One-shot C6a preparation evidence; never launches a real browser or submits."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sqlite3
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import yaml
from ci_triage import campaign_state as state
from ci_triage import cli
from ci_triage import qb_trigger as trigger
from ci_triage import sandbox_submit as sandbox
from ci_triage._campaign_workspace import _unit_hash
from ci_triage._sandbox_git import SandboxGit
from ci_triage.qb_config import parse_qb_config
from ci_triage.qb_redact import PageRedactor
from tizen_ci_shared.state import StateDatabase, VerificationRecord, write_pass_record

ROOT = Path("/home/linhao/Toolchain/p5q-live-validation/p5q-c6")
EVIDENCE = Path(__file__).resolve().parent
PROJECT = "platform/upstream/libtirpc"
SHA = "7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0"
TARGET = PROJECT + "@" + SHA
REMOTE = ROOT / "remotes" / PROJECT
REF = "refs/heads/sandbox/p5q-c6-libtirpc"
KEY = "p5q-c6-libtirpc-20261015"
IDS = tuple(f"{KEY}-v{i}" for i in range(3))
REPO = Path("/home/linhao/Toolchain/development/LogAnalysisSkill")
URL = "ssh://review.tizen.org:29418/" + PROJECT
MANIFEST_URL = (
    "http://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/"
    "tizen-base-toolchain_20260924.094908/builddata/manifest/"
    "tizen-base-toolchain_20260924.094908_standard.xml"
)


def write(name: str, value: object) -> None:
    content = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    redactor = PageRedactor()
    redactor.check_bytes(content.encode())
    path = EVIDENCE / name
    path.write_text(content, encoding="utf-8")
    redactor.check_bytes(path.read_bytes())


def manifest() -> None:
    raw = (ROOT / "preparation/manifest.xml").read_bytes()
    tree = ET.fromstring(raw)
    matches = [p for p in tree.findall("project") if p.get("name") == PROJECT]
    assert len(matches) == 1
    project = matches[0]
    assert project.get("revision") == SHA and project.get("path") == PROJECT
    sources = []
    for number, line in enumerate(raw.decode("utf-8", errors="strict").splitlines(), 1):
        if line.lstrip().startswith("<project "):
            parsed = ET.fromstring(line)
            if parsed.attrib == project.attrib:
                sources.append({"line": number, "original_line": line})
    assert len(sources) == 1
    PageRedactor().check_bytes(raw)
    (EVIDENCE / "manifest.xml").write_bytes(raw)
    write(
        "manifest-check.json",
        {
            "target_confirmation": TARGET,
            "source_url": MANIFEST_URL,
            "command": [
                "curl",
                "--silent",
                "--show-error",
                "--retry",
                "0",
                "--max-time",
                "60",
                "--max-redirs",
                "0",
                "--proto",
                "=http",
                "--output",
                str(ROOT / "preparation/manifest.xml"),
                "--write-out",
                "%{json}\\n",
                MANIFEST_URL,
            ],
            "http_status": 200,
            "exit_code": 0,
            "request_count": 1,
            "redirect_count": 0,
            "content_type": "text/xml; charset=utf-8",
            "size_bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "attributes": project.attrib,
            "source": sources[0],
            "exact_revision_match": True,
        },
    )


def fetch() -> None:
    assert not REMOTE.exists(), "Preparation mirror must not already exist"
    REMOTE.parent.mkdir(parents=True, exist_ok=True)
    git = SandboxGit(
        ssh_command="ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=20",
        remote_timeout=180,
    )
    records: list[dict[str, object]] = []
    commands = [
        (None, ("init", "--bare", str(REMOTE)), False),
        (REMOTE, ("fetch", "--no-tags", "--no-recurse-submodules", "--depth=1", URL, SHA), True),
        (REMOTE, ("cat-file", "-t", SHA), False),
        (REMOTE, ("rev-parse", SHA + "^{tree}"), False),
        (REMOTE, ("update-ref", REF, SHA), False),
        (REMOTE, ("show-ref", "--verify", REF), False),
    ]
    for cwd, args, remote in commands:
        record: dict[str, object] = {
            "at": datetime.now(timezone.utc).isoformat(),
            "cwd": str(cwd) if cwd else None,
            "git_arguments": list(args),
            "ssh_command": git.ssh_command,
            "remote": remote,
        }
        records.append(record)
        try:
            result = git.run(cwd, *args, remote=remote, check=False)
            record.update(
                argv=result.args,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        except (OSError, subprocess.SubprocessError) as error:
            record.update(error_class=type(error).__name__)
            write("mirror-commands.json", records)
            raise
        write("mirror-commands.json", records)
        assert result.returncode == 0, "Mirror command failed; do not retry"
    assert records[2]["stdout"] == "commit\n"
    assert records[5]["stdout"] == f"{SHA} {REF}\n"
    write(
        "mirror-check.json",
        {
            "remote": str(REMOTE),
            "source": URL,
            "fetched_commit": SHA,
            "tree": str(records[3]["stdout"]).strip(),
            "sandbox_ref": REF,
            "local_ref_matches": True,
            "fetch_count": 1,
            "gerrit_push_count": 0,
            "synthetic_ref": True,
        },
    )


def dump_db() -> str:
    conn = sqlite3.connect((ROOT / "state.db").as_uri() + "?mode=ro", uri=True)
    try:
        return "\n".join(conn.iterdump()) + "\n"
    finally:
        conn.close()


def construct() -> None:
    assert not (ROOT / "state.db").exists() and not (ROOT / "config.yaml").exists()
    mirror = json.loads((EVIDENCE / "mirror-check.json").read_text())
    assert mirror["fetched_commit"] == SHA and mirror["local_ref_matches"]
    tree = mirror["tree"]
    hook = Path("/home/linhao/gerrit-hook/commit-msg")
    project = dict(
        enabled=True,
        overview_id=1917,
        configuration_path="root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER",
        project_name="Tizen-Base-Toolchain",
        qb_pass_requires_accept=False,
        form={
            "BUILD_TYPE": "Full",
            "REPO_TYPE": "ALL",
            "BUILD_REFERENCE": "Ref. Snapshot",
            "SNAPSHOT_NUM": "@freeze",
            "PROJECT_BRANCH": "tizen_base",
            "Immediate Stop With Error": True,
            "CHILD_CONFIGURATIONS": ["standard-armv7l:aarch64:x86_64"],
            "TARGET_IMAGE": [],
            "Add Package List": "",
            "Remove Package List": "",
        },
    )
    identity = "C6 Synthetic Fixture <p5q-c6@example.invalid>"
    config = dict(
        campaign_workspace=str(ROOT / "ws"),
        gerrit_ssh_base=str(ROOT / "remotes"),
        git_author_identity=identity,
        git_committer_identity=identity,
        gerrit_commit_msg_hook=str(hook),
        gerrit_commit_msg_hook_sha256=hashlib.sha256(hook.read_bytes()).hexdigest(),
        qb=dict(
            base_url="https://quickbuild.tizen.org",
            browser=dict(
                node="/home/linhao/.local/bin/node",
                playwright_module="/home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs",
                chromium="/home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome",
                login_timeout_seconds=600,
            ),
            projects={"tizen_base": project},
        ),
    )
    parse_qb_config(config["qb"])
    config_text = yaml.safe_dump(config, allow_unicode=True, sort_keys=True)
    PageRedactor().check_bytes(config_text.encode())
    (ROOT / "config.yaml").write_text(config_text, encoding="utf-8")
    sandbox._config(ROOT / "config.yaml")
    (ROOT / "state").mkdir()
    (ROOT / "ws").mkdir()
    write(
        "synthetic-basis.json",
        {
            "authority": "P5Q-C6-01",
            "target": TARGET,
            "template": "tests/unit/test_p5q_c5a_integration.py -> test_qb_trigger.Campaign.add",
            "synthetic": ["three PASS verification records", "unit and round", "DERIVE", "PUSH"],
            "real_facts": ["manifest revision", "fetched commit and tree", "local sandbox ref"],
            "warning": "No real gbs verification, derived commit creation or Gerrit push occurred.",
            "placeholder_digests": {
                "patch": "d" * 64,
                "edit": "e" * 64,
                "gbs_conf": "f" * 64,
                "build_log": "b" * 64,
            },
        },
    )
    basis = EVIDENCE / "synthetic-basis.json"
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    db = StateDatabase(ROOT / "state.db")
    state.create_unit(
        db,
        campaign_unit_key=KEY,
        submission_identity_key=KEY,
        ci_system="quickbuild",
        source_build_id="1",
        project=PROJECT,
        branch="tizen_base",
        spec_name="libtirpc",
        base_commit=SHA,
        primary_arch="standard-aarch64",
        failed_arches=["standard-aarch64"],
        toolchain_profile="clang",
        ci_evidence_ref=str(basis),
        ci_evidence_sha256=hashlib.sha256(basis.read_bytes()).hexdigest(),
        max_rounds=3,
        max_build_invocations=9,
    )
    state.create_round(
        db, KEY, round_index=1, edit_spec_ref="synthetic:C6-01", edit_spec_sha256="e" * 64
    )
    for i, arch in enumerate(("aarch64", "armv7l", "x86_64")):
        record = VerificationRecord(
            verification_id=IDS[i],
            result="PASS",
            timestamp=stamp,
            failure_key=f"{KEY}-{arch}",
            base_commit=SHA,
            verified_commit_sha=SHA,
            verified_tree_sha=tree,
            canonical_diff_sha256="d" * 64,
            patch_sha256="d" * 64,
            edit_spec_sha256="e" * 64,
            project=PROJECT,
            branch="tizen_base",
            spec_name="libtirpc",
            arch="standard-" + arch,
            gbs_conf_sha256="f" * 64,
            build_log_sha256="b" * 64,
            worktree_path=str(ROOT / "synthetic-not-built" / arch),
            command_line="SYNTHETIC P5Q-C6-01 fixture; no gbs build executed",
        )
        write_pass_record(db, record)
        conn = db.connect()
        try:
            with conn:
                conn.execute(
                    "INSERT INTO campaign_verifications (campaign_unit_key,arch_raw,arch_norm,"
                    "verification_id,round_index,edit_spec_sha256,"
                    "campaign_schema_version,created_at) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (
                        KEY,
                        record.arch,
                        arch,
                        record.verification_id,
                        1,
                        "e" * 64,
                        "campaign/v1",
                        stamp,
                    ),
                )
        finally:
            conn.close()
    state.append_event(
        db,
        KEY,
        "DERIVE",
        dict(
            message_brief="SYNTHETIC C6-01: reuse fetched snapshot commit; no derive executed",
            author_identity=identity,
            committer_identity=identity,
            author_date=stamp,
            committer_date=stamp,
            derived_commit_sha=SHA,
            verified_tree_sha=tree,
        ),
    )
    state.append_event(
        db,
        KEY,
        "PUSH",
        dict(
            ref=REF,
            ref_class="sandbox",
            pushed_sha=SHA,
            result="ok",
            url=None,
            at=stamp,
        ),
    )
    state.append_status(db, KEY, "SANDBOX_PUSHED")
    sql = dump_db()
    PageRedactor().check_bytes(sql.encode())
    (EVIDENCE / "state-before.sql").write_text(sql, encoding="utf-8")
    (EVIDENCE / "config.yaml").write_text(config_text, encoding="utf-8")
    write(
        "state-prepared.json",
        {
            "synthetic": True,
            "unit": KEY,
            "verification_ids": IDS,
            "state_db": str(db.path),
            "state_root": str(ROOT / "state"),
            "config": str(ROOT / "config.yaml"),
            "target": TARGET,
            "sql_sha256": hashlib.sha256(sql.encode()).hexdigest(),
            "db_sha256": hashlib.sha256(db.path.read_bytes()).hexdigest(),
            "config_sha256": hashlib.sha256(config_text.encode()).hexdigest(),
            "at": stamp,
            "gerrit_push_count": 0,
            "quickbuild_request_count": 0,
        },
    )


def preflight() -> None:
    script = ROOT / "preparation/fake-replies.json"
    transcript = ROOT / "preparation/fake-commands.jsonl"
    assert not script.exists() and not transcript.exists()
    script.write_text(json.dumps([{"ok": False, "error": "QB_LOGIN_ABORTED"}]))
    original = subprocess.Popen
    calls = []

    def popen(argv, *args, **kwargs):
        requested = [str(item) for item in argv]
        executed = requested
        if any(item.endswith("qb_browser_agent.mjs") for item in requested):
            executed = [
                sys.executable,
                str(REPO / "tests/fixtures/qb_fake_agent.py"),
                str(script),
                str(transcript),
            ]
        else:
            assert requested[0] == "git", "Unexpected subprocess"
            assert "push" not in requested and "fetch" not in requested
            if "ls-remote" in requested:
                assert str(REMOTE) in requested
            assert str(REPO) not in requested
        calls.append({"requested": requested, "executed": executed})
        return original(executed, *args, **kwargs)

    before = dump_db()
    before_hash = hashlib.sha256((ROOT / "state.db").read_bytes()).hexdigest()
    args = [
        "qb-trigger",
        "--verification-ids",
        ",".join(IDS),
        "--state-db",
        str(ROOT / "state.db"),
        "--state-root",
        str(ROOT / "state"),
        "--config",
        str(ROOT / "config.yaml"),
    ]
    out, err = io.StringIO(), io.StringIO()
    with patch.object(subprocess, "Popen", popen):
        code = cli.main(args, stdout=out, stderr=err)
        raw = yaml.safe_load((ROOT / "config.yaml").read_text())
        config = sandbox._config(ROOT / "config.yaml")
        snapshot = trigger._snapshot(
            StateDatabase(ROOT / "state.db"), IDS, KEY, parse_qb_config(raw["qb"])
        )
        unit_root = config.workspace / _unit_hash(KEY)
        with trigger._lock(unit_root):
            trigger._remote_check(config, snapshot, unit_root)
    commands = [json.loads(line) for line in transcript.read_text().splitlines()]
    write(
        "preflight.json",
        {
            "cli_argv": args,
            "cli_exit": code,
            "stdout": json.loads(out.getvalue()),
            "stderr": err.getvalue(),
            "fake_commands": commands,
            "subprocess_calls": calls,
            "expected_boundary": (
                "fake login deliberately returns QB_LOGIN_ABORTED after prerequisites"
            ),
            "remote_check": "PASS",
            "remote_sha": snapshot.derived,
            "db_unchanged": dump_db() == before,
            "db_sha256_before": before_hash,
            "db_sha256_after": hashlib.sha256((ROOT / "state.db").read_bytes()).hexdigest(),
            "transport_removed": not (unit_root / ".transport").exists(),
            "real_browser_count": 0,
            "quickbuild_request_count": 0,
            "gerrit_push_count": 0,
        },
    )
    payload = json.loads(out.getvalue())
    assert code == 5 and payload[0]["error_code"] == "QB_LOGIN_ABORTED"
    assert payload[0]["status"] == "SANDBOX_PUSHED" and payload[0]["request_id"] is None
    assert [row["command"] for row in commands] == ["login", "close"]
    assert len([c for c in calls if "qb_fake_agent.py" in c["executed"][1]]) == 1
    assert dump_db() == before
    assert hashlib.sha256((ROOT / "state.db").read_bytes()).hexdigest() == before_hash
    assert snapshot.derived == SHA and not (unit_root / ".transport").exists()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=("manifest", "fetch", "construct", "preflight"))
    options = parser.parse_args()
    {"manifest": manifest, "fetch": fetch, "construct": construct, "preflight": preflight}[
        options.step
    ]()
    print(json.dumps({"step": options.step, "result": "PASS"}))
