"""Prepare only C8 unit 1; no browser, QuickBuild command or remote write."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml
from ci_triage import campaign_state as state
from ci_triage import qb_trigger as trigger
from ci_triage import sandbox_submit as sandbox
from ci_triage._campaign_workspace import _unit_hash
from ci_triage._sandbox_git import SandboxGit
from ci_triage.qb_config import parse_qb_config
from ci_triage.qb_redact import PageRedactor
from tizen_ci_shared.state import StateDatabase, VerificationRecord, write_pass_record

REPO = Path(__file__).resolve().parents[7]
HERE = Path(__file__).resolve().parent
ROOT = Path("/home/linhao/Toolchain/p5q-live-validation/p5q-c8")
C6 = ROOT.with_name("p5q-c6")
PROJECT = "platform/upstream/libtirpc"
SHA = "7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0"
TARGET = PROJECT + "@" + SHA
REMOTE = ROOT / "remotes" / PROJECT
REF = "refs/heads/sandbox/p5q-c8-libtirpc"
KEY = "p5q-c8-libtirpc-20261021"
IDS = tuple(f"{KEY}-v{i}" for i in range(3))
SOURCE = "ssh://review.tizen.org:29418/" + PROJECT


def stamp():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()
    checked_write(HERE / name, raw)


def checked_write(path, raw):
    redactor = PageRedactor()
    redactor.check_bytes(raw)
    path.write_bytes(raw)
    redactor.check_bytes(path.read_bytes())


def c6_tree():
    return {
        str(p.relative_to(C6)): {"link": os.readlink(p)} if p.is_symlink() else digest(p)
        for p in sorted(C6.rglob("*"))
        if p.is_file() or p.is_symlink()
    }


def immutable():
    design = REPO / "docs/clang-fix-campaign"
    expected = {
        design / "p5q-qb-trigger-design-v1.8-FROZEN.md": (
            "d0242ca8b708e9c1e3e714387bae963f8f6f16fc765179e6ed60d8be56493364"
        ),
        design / "p5q-qb-trigger-design-v1.5-FROZEN.md": (
            "f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c"
        ),
        C6 / "state.db": "08ed202e69a73a480e7282a198565f32adae8157a332804df4df970238eacd30",
    }
    hashes = {str(p): digest(p) for p in expected}
    assert hashes == {str(p): sha for p, sha in expected.items()}
    before = HERE / "c6-tree-before.json"
    if before.exists():
        assert c6_tree() == json.loads(before.read_text())
    return hashes


def fetch():
    immutable()
    assert not ROOT.exists(), "C8 directory already exists; do not overwrite"
    write("c6-tree-before.json", c6_tree())
    ROOT.mkdir()
    REMOTE.parent.mkdir(parents=True)
    git = SandboxGit(
        ssh_command="ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=20",
        remote_timeout=180,
    )
    rows = []
    for cwd, args, remote in [
        (None, ("init", "--bare", str(REMOTE)), False),
        (REMOTE, ("fetch", "--no-tags", "--no-recurse-submodules", "--depth=1", SOURCE, SHA), True),
        (REMOTE, ("cat-file", "-t", SHA), False),
        (REMOTE, ("rev-parse", SHA + "^{tree}"), False),
        (REMOTE, ("update-ref", REF, SHA), False),
        (REMOTE, ("show-ref", "--verify", REF), False),
    ]:
        row = dict(started=stamp(), cwd=str(cwd) if cwd else None, arguments=args, remote=remote)
        rows.append(row)
        try:
            result = git.run(cwd, *args, remote=remote, check=False)
            row.update(
                argv=result.args,
                exit=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                ended=stamp(),
            )
        except (OSError, subprocess.SubprocessError) as exc:
            row.update(error_class=type(exc).__name__, ended=stamp())
            write("mirror-commands.json", rows)
            raise
        write("mirror-commands.json", rows)
        assert result.returncode == 0, "Mirror command failed; no retry"
    assert rows[2]["stdout"] == "commit\n" and rows[5]["stdout"] == f"{SHA} {REF}\n"
    write(
        "mirror.json",
        dict(
            source=SOURCE,
            target=TARGET,
            remote=str(REMOTE),
            ref=REF,
            tree=str(rows[3]["stdout"]).strip(),
            fetches=1,
            pushes=0,
            immutable=immutable(),
        ),
    )


def connect():
    conn = sqlite3.connect((ROOT / "state.db").as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def construct():
    immutable()
    assert not (ROOT / "state.db").exists() and not (ROOT / "config.yaml").exists()
    mirror = json.loads((HERE / "mirror.json").read_text())
    source_config = HERE.parents[1] / "C6a/preparation/config.yaml"
    config = yaml.safe_load(source_config.read_text())
    identity = "C8 Synthetic Fixture <p5q-c8@example.invalid>"
    config.update(
        campaign_workspace=str(ROOT / "ws"),
        gerrit_ssh_base=str(ROOT / "remotes"),
        git_author_identity=identity,
        git_committer_identity=identity,
    )
    assert config["qb"]["projects"]["tizen_base"]["form"]["SNAPSHOT_NUM"] == "@freeze"
    parse_qb_config(config["qb"])
    raw = yaml.safe_dump(config, allow_unicode=True, sort_keys=True).encode()
    checked_write(ROOT / "config.yaml", raw)
    checked_write(HERE / "config.yaml", raw)
    sandbox._config(ROOT / "config.yaml")
    (ROOT / "ws").mkdir()
    (ROOT / "state").mkdir()
    basis = HERE / "synthetic-basis.json"
    write(
        basis.name,
        dict(
            authority="P5Q-C6-01 + P5Q-C8-01",
            target=TARGET,
            template="C6 preparation and tests/unit/test_p5q_c5a_integration.py",
            synthetic=["three PASS verification records", "unit/round", "DERIVE", "PUSH"],
            real_facts=["read-only fetched commit and tree", "local sandbox ref"],
            warning="No real gbs verification, derived commit creation or Gerrit push occurred.",
            manifest="NOT_REQUESTED (optional); current snapshot remains unfrozen",
        ),
    )
    db = StateDatabase(ROOT / "state.db")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
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
        ci_evidence_sha256=digest(basis),
        max_rounds=3,
        max_build_invocations=9,
    )
    state.create_round(
        db, KEY, round_index=1, edit_spec_ref="synthetic:C6-01/C8", edit_spec_sha256="e" * 64
    )
    for i, arch in enumerate(("aarch64", "armv7l", "x86_64")):
        record = VerificationRecord(
            verification_id=IDS[i],
            result="PASS",
            timestamp=now,
            failure_key=f"{KEY}-{arch}",
            base_commit=SHA,
            verified_commit_sha=SHA,
            verified_tree_sha=mirror["tree"],
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
            command_line="SYNTHETIC P5Q-C6-01/C8 fixture; no gbs build executed",
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
                        now,
                    ),
                )
        finally:
            conn.close()
    state.append_event(
        db,
        KEY,
        "DERIVE",
        dict(
            message_brief="SYNTHETIC C6-01/C8: reuse fetched commit; no derive executed",
            author_identity=identity,
            committer_identity=identity,
            author_date=now,
            committer_date=now,
            derived_commit_sha=SHA,
            verified_tree_sha=mirror["tree"],
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
            at=now,
        ),
    )
    state.append_status(db, KEY, "SANDBOX_PUSHED")
    conn = connect()
    try:
        checked_write(HERE / "state-before.sql", ("\n".join(conn.iterdump()) + "\n").encode())
    finally:
        conn.close()
    write(
        "prepared.json",
        dict(
            unit=KEY,
            verification_ids=IDS,
            target=TARGET,
            at=now,
            db=str(db.path),
            db_sha256=digest(db.path),
            state_root=str(ROOT / "state"),
            config=str(ROOT / "config.yaml"),
            unit2_created=False,
            immutable=immutable(),
        ),
    )


def command(argv):
    run = subprocess.run(argv, capture_output=True, text=True, check=False)
    assert run.returncode == 0
    return dict(argv=argv, exit=run.returncode, stdout=run.stdout, stderr=run.stderr)


def preflight():
    before = digest(ROOT / "state.db")
    config = sandbox._config(ROOT / "config.yaml")
    qb = parse_qb_config(yaml.safe_load((ROOT / "config.yaml").read_text())["qb"])
    snap = trigger._snapshot(StateDatabase(ROOT / "state.db"), IDS, KEY, qb)
    assert trigger._idempotency(snap, False) is None
    unit_root = config.workspace / _unit_hash(KEY)
    with trigger._lock(unit_root):
        trigger._remote_check(config, snap, unit_root)
    conn = connect()
    try:
        counts = {
            name: conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
            for name in ("campaign_qb_requests", "campaign_qb_profiles", "campaign_qb_events")
        }
        status = dict(
            conn.execute(
                "SELECT * FROM campaign_status_log ORDER BY log_id DESC LIMIT 1"
            ).fetchone()
        )
        units = conn.execute("SELECT COUNT(*) FROM campaign_units").fetchone()[0]
    finally:
        conn.close()
    report = dict(
        at=stamp(),
        unit=KEY,
        db_sha256=before,
        counts=counts,
        latest_status=status,
        units=units,
        remote_check="PASS",
        remote_commit=snap.derived,
        profiles=[str(p) for p in Path("/dev/shm").glob("p5q-browser-*")],
        transports=[str(p) for p in ROOT.rglob(".transport")],
        processes=[],
        process_scan_errors=[],
        d_samples=[],
        immutable=immutable(),
        commands=[
            command(["df", "-h", "/home", "/dev/shm"]),
            command(["free", "-h"]),
            command(["findmnt", "-T", "/home"]),
        ],
    )
    for p in Path("/proc").iterdir():
        if not p.name.isdigit() or int(p.name) == os.getpid():
            continue
        try:
            args = (p / "cmdline").read_bytes().split(b"\0")
            matched = [
                kind
                for kind, needle in (
                    ("agent", b"qb_browser_agent.mjs"),
                    ("test_agent", b"p5q_cli_agent.mjs"),
                    ("chromium", b"ms-playwright/chromium"),
                    ("profile", b"p5q-browser-"),
                )
                if any(needle in part for part in args)
            ]
            if matched:
                report["processes"].append(dict(pid=int(p.name), kinds=matched))
        except FileNotFoundError:
            pass
        except PermissionError:
            report["process_scan_errors"].append(dict(pid=int(p.name), error="PERMISSION_DENIED"))
    for index in range(3):
        if index:
            time.sleep(10)
        output = command(["ps", "-eo", "state,pid,comm"])
        rows = [line for line in output["stdout"].splitlines() if line.split()[:1] == ["D"]]
        details = []
        for row in rows:
            _, pid, name = row.split(maxsplit=2)
            p = Path("/proc") / pid
            details.append(
                dict(
                    pid=int(pid),
                    name=name,
                    wchan=(p / "wchan").read_text().strip() if p.exists() else "EXITED",
                )
            )
        report["d_samples"].append(dict(at=stamp(), rows=details))
    report["persistent_d_pids"] = sorted(
        set.intersection(*[{r["pid"] for r in sample["rows"]} for sample in report["d_samples"]])
    )
    report["db_sha256_after"] = digest(ROOT / "state.db")
    report["ready_without_user_authorization"] = (
        before == report["db_sha256_after"]
        and units == 1
        and all(v == 0 for v in counts.values())
        and status["status"] == "SANDBOX_PUSHED"
        and snap.derived == SHA
        and not report["profiles"]
        and not report["transports"]
        and not report["processes"]
        and not report["process_scan_errors"]
    )
    write("preflight.json", report)
    assert report["ready_without_user_authorization"], "Preparation preflight failed"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=("fetch", "construct", "preflight"))
    args = parser.parse_args()
    {"fetch": fetch, "construct": construct, "preflight": preflight}[args.step]()
    print(json.dumps(dict(step=args.step, result="PASS")))
