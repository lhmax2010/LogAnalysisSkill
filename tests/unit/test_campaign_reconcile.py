from __future__ import annotations

import inspect
import json
import shutil
import sqlite3
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import pytest
from ci_triage import campaign_state
from ci_triage.campaign_state import (
    CAMPAIGN_SCHEMA_VERSION,
    HELD_FOR_INVESTIGATION,
    CampaignStateBusy,
    ReconcileResult,
    consume_build_invocation,
    create_round,
    create_unit,
    ensure_schema,
    link_verification_with_convergence,
    reconcile_pass_and_invocations,
)
from ci_triage.state import StateDatabase, VerificationRecord, write_pass_record

UNIT_KEY = "campaign:test-unit"
FAILURE_KEY = "quickbuild/failure/aarch64"
EDIT_ONE = "1" * 64
EDIT_TWO = "2" * 64

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git not available")


@dataclass(frozen=True)
class GitFixture:
    template: Path
    base_commit: str
    verified_commit: str
    verified_tree: str
    changed_paths: tuple[str, ...]


def _git(cwd: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _git_fixture(tmp_path: Path) -> GitFixture:
    repo = tmp_path / "template"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "ci-triage-test@example.invalid")
    _git(repo, "config", "user.name", "CI Triage Test")
    files = {
        "src/main.c": "int main(void) { return 0; }\n",
        "src/name with space.c": "int spaced = 0;\n",
        'src/say"hi.c': "int quoted = 0;\n",
    }
    for relative, content in files.items():
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD")
    for relative in files:
        path = repo / relative
        path.write_text(path.read_text(encoding="utf-8") + "/* fixed */\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "verified")
    verified = _git(repo, "rev-parse", "HEAD")
    tree = _git(repo, "rev-parse", "HEAD^{tree}")
    return GitFixture(
        template=repo,
        base_commit=base,
        verified_commit=verified,
        verified_tree=tree,
        changed_paths=tuple(sorted(files)),
    )


def _db(tmp_path: Path) -> StateDatabase:
    db = StateDatabase(tmp_path / "state.sqlite3")
    ensure_schema(db)
    return db


def _create_unit(
    db: StateDatabase,
    git: GitFixture,
    *,
    unit_key: str = UNIT_KEY,
    build_id: str = "1234",
) -> None:
    create_unit(
        db,
        campaign_unit_key=unit_key,
        submission_identity_key=f"submission:{unit_key}",
        primary_arch="standard-aarch64",
        failed_arches=("standard-aarch64",),
        toolchain_profile="tizen_unified_standard",
        ci_evidence_ref="/tmp/ci-evidence.json",
        ci_evidence_sha256="c" * 64,
        max_rounds=4,
        max_build_invocations=12,
        ci_system="quickbuild",
        source_build_id=build_id,
        project="platform/core/appfw/united-service",
        branch="tizen",
        spec_name="united-service",
        base_commit=git.base_commit,
    )


def _create_campaign_round(
    db: StateDatabase,
    round_index: int,
    edit_sha: str,
    *,
    unit_key: str = UNIT_KEY,
) -> None:
    create_round(
        db,
        unit_key,
        round_index=round_index,
        edit_spec_ref=f"relative/round-{round_index}.json",
        edit_spec_sha256=edit_sha,
    )


def _protected_worktree(
    tmp_path: Path,
    git: GitFixture,
    verification_id: str,
) -> Path:
    path = tmp_path / f"worktree-{verification_id}"
    shutil.copytree(git.template, path, symlinks=True)
    exclude = Path(_git(path, "rev-parse", "--git-path", "info/exclude"))
    if not exclude.is_absolute():
        exclude = path / exclude
    with exclude.open("a", encoding="utf-8") as stream:
        stream.write("\n.ci_triage_protected\n")
    (path / ".ci_triage_protected").write_text(
        json.dumps(
            {
                "protected_reason": "GERRIT_READY",
                "verification_id": verification_id,
                "failure_key": FAILURE_KEY,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    assert _git(path, "status", "--porcelain") == ""
    return path


def _write_record(
    db: StateDatabase,
    tmp_path: Path,
    git: GitFixture,
    verification_id: str,
    *,
    edit_sha: str = EDIT_ONE,
    failure_key: str = FAILURE_KEY,
    valid_worktree: bool = True,
) -> VerificationRecord:
    worktree = (
        _protected_worktree(tmp_path, git, verification_id)
        if valid_worktree
        else tmp_path / f"missing-{verification_id}"
    )
    record = VerificationRecord(
        verification_id=verification_id,
        result="PASS",
        timestamp=f"2026-08-05T00:00:{verification_id[-1:]}0+00:00",
        failure_key=failure_key,
        base_commit=git.base_commit,
        verified_commit_sha=git.verified_commit,
        verified_tree_sha=git.verified_tree,
        canonical_diff_sha256="d" * 64,
        patch_sha256="e" * 64,
        edit_spec_sha256=edit_sha,
        project="platform/core/appfw/united-service",
        branch="tizen",
        spec_name="united-service",
        arch="standard-aarch64",
        gbs_conf_sha256="f" * 64,
        build_log_sha256="a" * 64,
        worktree_path=str(worktree),
        command_line="gbs -c conf build -A aarch64 --include-all",
    )
    write_pass_record(db, record)
    return record


def _pass_payload(
    invocation_event_id: int,
    verification_id: str,
    *,
    round_index: int,
) -> dict[str, object]:
    return {
        "round_index": round_index,
        "arch_norm": "aarch64",
        "invocation_event_id": invocation_event_id,
        "result": "PASS",
        "verdict": "n_a",
        "reason": "build_passed",
        "evidence_path": None,
        "evidence_sha256": None,
        "verification_id": verification_id,
        "actual_changed_paths": ["src/main.c"],
        "previous_basis": "none",
        "at": "2026-08-05T00:00:00+00:00",
    }


def _reconcile(
    db: StateDatabase,
    *,
    round_index: int = 1,
    edit_sha: str = EDIT_ONE,
) -> ReconcileResult:
    return reconcile_pass_and_invocations(
        db,
        UNIT_KEY,
        round_index=round_index,
        arch_norm="aarch64",
        failure_key=FAILURE_KEY,
        edit_spec_sha256=edit_sha,
    )


def _events(db: StateDatabase, event_type: str) -> list[sqlite3.Row]:
    conn = db.connect()
    try:
        return conn.execute(
            "SELECT * FROM campaign_gate_events WHERE campaign_unit_key = ? "
            "AND event_type = ? ORDER BY event_id",
            (UNIT_KEY, event_type),
        ).fetchall()
    finally:
        conn.close()


def _latest_campaign_status(db: StateDatabase) -> sqlite3.Row | None:
    conn = db.connect()
    try:
        return cast(
            sqlite3.Row | None,
            conn.execute(
                "SELECT * FROM campaign_status_log WHERE campaign_unit_key = ? "
                "ORDER BY log_id DESC LIMIT 1",
                (UNIT_KEY,),
            ).fetchone(),
        )
    finally:
        conn.close()


def test_reconcile_relinks_current_pass_in_one_transaction_and_rebuilds_paths(
    tmp_path: Path,
) -> None:
    git = _git_fixture(tmp_path)
    db = _db(tmp_path)
    _create_unit(db, git)
    _create_campaign_round(db, 1, EDIT_ONE)
    receipt = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
    _write_record(db, tmp_path, git, "V1")

    result = _reconcile(db)

    assert result.branch == "relinked"
    assert result.current_verification_id == "V1"
    assert result.current_relinked_invocation_event_id == receipt.event_id
    assert result.other_round_relinks == ()
    convergence = _events(db, "CONVERGENCE")
    assert len(convergence) == 1
    payload = json.loads(convergence[0]["payload_json"])
    assert payload["invocation_event_id"] == receipt.event_id
    assert payload["actual_changed_paths"] == list(git.changed_paths)


def test_reconcile_uses_transaction_internal_link_primitive() -> None:
    source = inspect.getsource(reconcile_pass_and_invocations)

    assert "_link_verification_with_convergence_on_connection(" in source
    assert "link_verification_with_convergence(" not in source


def test_linked_current_branch_still_backfills_other_orphan_invocations(
    tmp_path: Path,
) -> None:
    git = _git_fixture(tmp_path)
    db = _db(tmp_path)
    _create_unit(db, git)
    _create_campaign_round(db, 1, EDIT_ONE)
    orphan = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
    _create_campaign_round(db, 2, EDIT_TWO)
    current = consume_build_invocation(db, UNIT_KEY, round_index=2, arch_norm="aarch64")
    record = _write_record(db, tmp_path, git, "V2", edit_sha=EDIT_TWO)
    link_verification_with_convergence(
        db,
        UNIT_KEY,
        convergence_payload=_pass_payload(current.event_id, "V2", round_index=2),
        arch_raw=record.arch,
        arch_norm="aarch64",
        verification_id="V2",
        round_index=2,
        edit_spec_sha256=EDIT_TWO,
    )

    result = _reconcile(db, round_index=2, edit_sha=EDIT_TWO)

    assert result.branch == "linked_already"
    assert result.current_verification_id == "V2"
    assert result.backfilled_invocation_event_ids == (orphan.event_id,)
    payloads = [json.loads(row["payload_json"]) for row in _events(db, "CONVERGENCE")]
    assert any(
        item["invocation_event_id"] == orphan.event_id and item["reason"] == "orphan_invocation"
        for item in payloads
    )


def test_historical_relink_repairs_ledger_without_granting_current_success(
    tmp_path: Path,
) -> None:
    git = _git_fixture(tmp_path)
    db = _db(tmp_path)
    _create_unit(db, git)
    _create_campaign_round(db, 1, EDIT_ONE)
    old = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
    _write_record(db, tmp_path, git, "V1")
    _create_campaign_round(db, 2, EDIT_TWO)

    result = _reconcile(db, round_index=2, edit_sha=EDIT_TWO)

    assert result.branch == "proceed"
    assert result.current_verification_id is None
    assert result.other_round_relinks == ((1, "V1", old.event_id),)


def test_linked_pass_from_prior_round_does_not_short_circuit_new_round(
    tmp_path: Path,
) -> None:
    git = _git_fixture(tmp_path)
    db = _db(tmp_path)
    _create_unit(db, git)
    _create_campaign_round(db, 1, EDIT_ONE)
    old = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
    record = _write_record(db, tmp_path, git, "V1")
    link_verification_with_convergence(
        db,
        UNIT_KEY,
        convergence_payload=_pass_payload(old.event_id, "V1", round_index=1),
        arch_raw=record.arch,
        arch_norm="aarch64",
        verification_id="V1",
        round_index=1,
        edit_spec_sha256=EDIT_ONE,
    )
    _create_campaign_round(db, 2, EDIT_TWO)

    result = _reconcile(db, round_index=2, edit_sha=EDIT_TWO)

    assert result.branch == "proceed"
    assert result.current_verification_id is None
    assert result.other_round_relinks == ()


@pytest.mark.parametrize("orphan_count", [0, 2])
def test_single_pass_without_exactly_one_invocation_is_held(
    tmp_path: Path,
    orphan_count: int,
) -> None:
    git = _git_fixture(tmp_path)
    db = _db(tmp_path)
    _create_unit(db, git)
    _create_campaign_round(db, 1, EDIT_ONE)
    for _ in range(orphan_count):
        consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
    _write_record(db, tmp_path, git, "V1")

    result = _reconcile(db)

    assert result.branch == "orphan_pass_held"
    assert result.orphan_pass_verification_ids == ("V1",)
    assert result.held_rounds == (1,)
    assert len(_events(db, "ORPHAN_PASS")) == 1
    orphan = json.loads(_events(db, "ORPHAN_PASS")[0]["payload_json"])
    assert orphan["reason"] == (
        "no_free_invocation_slot" if orphan_count == 0 else "ambiguous"
    )
    status = _latest_campaign_status(db)
    assert status is not None
    assert status["status"] == HELD_FOR_INVESTIGATION
    assert not _events(db, "CONVERGENCE")


def test_multiple_passes_are_all_recorded_and_freeze_the_round(tmp_path: Path) -> None:
    git = _git_fixture(tmp_path)
    db = _db(tmp_path)
    _create_unit(db, git)
    _create_campaign_round(db, 1, EDIT_ONE)
    consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
    _write_record(db, tmp_path, git, "V1")
    _write_record(db, tmp_path, git, "V2")

    result = _reconcile(db)

    assert result.branch == "orphan_pass_held"
    assert result.orphan_pass_verification_ids == ("V1", "V2")
    assert len(_events(db, "ORPHAN_PASS")) == 2
    assert not _events(db, "CONVERGENCE")


def test_damaged_worktree_becomes_orphan_pass_instead_of_partial_link(
    tmp_path: Path,
) -> None:
    git = _git_fixture(tmp_path)
    db = _db(tmp_path)
    _create_unit(db, git)
    _create_campaign_round(db, 1, EDIT_ONE)
    consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
    _write_record(db, tmp_path, git, "V1", valid_worktree=False)

    result = _reconcile(db)

    assert result.branch == "orphan_pass_held"
    orphan = json.loads(_events(db, "ORPHAN_PASS")[0]["payload_json"])
    assert orphan["reason"] == "worktree_damaged"
    conn = db.connect()
    try:
        assert conn.execute("SELECT COUNT(*) FROM campaign_verifications").fetchone()[0] == 0
    finally:
        conn.close()


def test_non_campaign_pass_is_reported_without_events_or_held_status(tmp_path: Path) -> None:
    git = _git_fixture(tmp_path)
    db = _db(tmp_path)
    _create_unit(db, git)
    _create_campaign_round(db, 1, EDIT_ONE)
    _write_record(db, tmp_path, git, "VX", edit_sha="9" * 64)

    result = _reconcile(db)

    assert result.branch == "proceed"
    assert result.non_campaign_verification_ids == ("VX",)
    assert not _events(db, "ORPHAN_PASS")
    assert _latest_campaign_status(db) is None


def test_a0_half_state_is_held_before_orphan_backfill_can_mask_it(tmp_path: Path) -> None:
    git = _git_fixture(tmp_path)
    db = _db(tmp_path)
    _create_unit(db, git)
    _create_campaign_round(db, 1, EDIT_ONE)
    receipt = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
    record = _write_record(db, tmp_path, git, "V1")
    link_verification_with_convergence(
        db,
        UNIT_KEY,
        convergence_payload=_pass_payload(receipt.event_id, "V1", round_index=1),
        arch_raw=record.arch,
        arch_norm="aarch64",
        verification_id="V1",
        round_index=1,
        edit_spec_sha256=EDIT_ONE,
    )
    conn = db.connect()
    try:
        conn.execute("DELETE FROM campaign_gate_events WHERE event_type = 'CONVERGENCE'")
        conn.commit()
    finally:
        conn.close()

    result = _reconcile(db)

    assert result.branch == "state_inconsistent_held"
    assert not _events(db, "CONVERGENCE")
    status = _latest_campaign_status(db)
    assert status is not None
    assert status["reason"] == "state_inconsistent"
    assert status["arch_norm"] == "aarch64"


def test_a0_pass_convergence_with_null_invocation_is_held(tmp_path: Path) -> None:
    git = _git_fixture(tmp_path)
    db = _db(tmp_path)
    _create_unit(db, git)
    _create_campaign_round(db, 1, EDIT_ONE)
    receipt = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
    record = _write_record(db, tmp_path, git, "V1")
    link_verification_with_convergence(
        db,
        UNIT_KEY,
        convergence_payload=_pass_payload(receipt.event_id, "V1", round_index=1),
        arch_raw=record.arch,
        arch_norm="aarch64",
        verification_id="V1",
        round_index=1,
        edit_spec_sha256=EDIT_ONE,
    )
    conn = db.connect()
    try:
        row = conn.execute(
            "SELECT event_id, payload_json FROM campaign_gate_events "
            "WHERE event_type = 'CONVERGENCE'"
        ).fetchone()
        payload = json.loads(row["payload_json"])
        payload["invocation_event_id"] = None
        conn.execute(
            "UPDATE campaign_gate_events SET invocation_event_id = NULL, payload_json = ? "
            "WHERE event_id = ?",
            (json.dumps(payload, sort_keys=True, separators=(",", ":")), row["event_id"]),
        )
        conn.commit()
    finally:
        conn.close()

    result = _reconcile(db)

    assert result.branch == "state_inconsistent_held"
    status = _latest_campaign_status(db)
    assert status is not None
    assert status["reason"] == "state_inconsistent"


def test_a0_ignores_malformed_convergence_payload_in_another_unit(tmp_path: Path) -> None:
    git = _git_fixture(tmp_path)
    db = _db(tmp_path)
    other_unit = "campaign:other-unit"
    _create_unit(db, git)
    _create_unit(db, git, unit_key=other_unit, build_id="5678")
    _create_campaign_round(db, 1, EDIT_ONE)
    _create_campaign_round(db, 1, EDIT_ONE, unit_key=other_unit)
    target_receipt = consume_build_invocation(
        db,
        UNIT_KEY,
        round_index=1,
        arch_norm="aarch64",
    )
    target_record = _write_record(db, tmp_path, git, "V-target")
    link_verification_with_convergence(
        db,
        UNIT_KEY,
        convergence_payload=_pass_payload(target_receipt.event_id, "V-target", round_index=1),
        arch_raw=target_record.arch,
        arch_norm="aarch64",
        verification_id="V-target",
        round_index=1,
        edit_spec_sha256=EDIT_ONE,
    )
    other_receipt = consume_build_invocation(
        db,
        other_unit,
        round_index=1,
        arch_norm="aarch64",
    )
    other_record = _write_record(db, tmp_path, git, "V-other")
    link_verification_with_convergence(
        db,
        other_unit,
        convergence_payload=_pass_payload(other_receipt.event_id, "V-other", round_index=1),
        arch_raw=other_record.arch,
        arch_norm="aarch64",
        verification_id="V-other",
        round_index=1,
        edit_spec_sha256=EDIT_ONE,
    )
    conn = db.connect()
    try:
        conn.execute(
            "UPDATE campaign_gate_events SET payload_json = '{malformed' "
            "WHERE campaign_unit_key = ? AND event_type = 'CONVERGENCE'",
            (other_unit,),
        )
        conn.commit()
    finally:
        conn.close()

    result = _reconcile(db)

    assert result.branch == "linked_already"
    assert result.current_verification_id == "V-target"
    assert _latest_campaign_status(db) is None


def test_a0_rejects_duplicate_pass_binding_that_weak_exists_check_would_accept(
    tmp_path: Path,
) -> None:
    git = _git_fixture(tmp_path)
    db = _db(tmp_path)
    _create_unit(db, git)
    _create_campaign_round(db, 1, EDIT_ONE)
    first = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
    record = _write_record(db, tmp_path, git, "V1")
    link_verification_with_convergence(
        db,
        UNIT_KEY,
        convergence_payload=_pass_payload(first.event_id, "V1", round_index=1),
        arch_raw=record.arch,
        arch_norm="aarch64",
        verification_id="V1",
        round_index=1,
        edit_spec_sha256=EDIT_ONE,
    )
    second = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
    duplicate = _pass_payload(second.event_id, "V1", round_index=1)
    conn = db.connect()
    try:
        conn.execute(
            "INSERT INTO campaign_gate_events "
            "(campaign_unit_key, round_index, arch_norm, verdict, invocation_event_id, "
            "event_type, payload_json, created_at) VALUES (?, 1, 'aarch64', 'n_a', ?, "
            "'CONVERGENCE', ?, ?)",
            (
                UNIT_KEY,
                second.event_id,
                json.dumps(duplicate, sort_keys=True, separators=(",", ":")),
                "2026-08-05T01:00:00+00:00",
            ),
        )
        conn.commit()
        weak_exists = conn.execute(
            "SELECT COUNT(*) FROM campaign_gate_events WHERE event_type = 'CONVERGENCE' "
            'AND payload_json LIKE \'%"verification_id":"V1"%\''
        ).fetchone()[0]
    finally:
        conn.close()

    result = _reconcile(db)

    assert weak_exists >= 1
    assert result.branch == "state_inconsistent_held"


def test_a0_rejects_single_pass_bound_to_wrong_round_invocation(tmp_path: Path) -> None:
    git = _git_fixture(tmp_path)
    db = _db(tmp_path)
    _create_unit(db, git)
    _create_campaign_round(db, 1, EDIT_ONE)
    first = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
    record = _write_record(db, tmp_path, git, "V1")
    link_verification_with_convergence(
        db,
        UNIT_KEY,
        convergence_payload=_pass_payload(first.event_id, "V1", round_index=1),
        arch_raw=record.arch,
        arch_norm="aarch64",
        verification_id="V1",
        round_index=1,
        edit_spec_sha256=EDIT_ONE,
    )
    _create_campaign_round(db, 2, EDIT_TWO)
    wrong = consume_build_invocation(db, UNIT_KEY, round_index=2, arch_norm="aarch64")
    conn = db.connect()
    try:
        row = conn.execute(
            "SELECT event_id, payload_json FROM campaign_gate_events "
            "WHERE event_type = 'CONVERGENCE'"
        ).fetchone()
        payload = json.loads(row["payload_json"])
        payload["invocation_event_id"] = wrong.event_id
        conn.execute(
            "UPDATE campaign_gate_events SET invocation_event_id = ?, payload_json = ? "
            "WHERE event_id = ?",
            (
                wrong.event_id,
                json.dumps(payload, sort_keys=True, separators=(",", ":")),
                row["event_id"],
            ),
        )
        conn.commit()
    finally:
        conn.close()

    result = _reconcile(db)

    assert result.branch == "state_inconsistent_held"
    payloads = [json.loads(row["payload_json"]) for row in _events(db, "CONVERGENCE")]
    assert all(item["reason"] != "orphan_invocation" for item in payloads)


def test_multiple_round_attribution_is_state_inconsistent_when_guard_is_bypassed(
    tmp_path: Path,
) -> None:
    git = _git_fixture(tmp_path)
    db = _db(tmp_path)
    _create_unit(db, git)
    _create_campaign_round(db, 1, EDIT_ONE)
    conn = db.connect()
    try:
        conn.execute("PRAGMA foreign_keys=OFF")
        conn.executescript(
            """
            DROP TABLE campaign_verifications;
            ALTER TABLE campaign_rounds RENAME TO campaign_rounds_guarded;
            CREATE TABLE campaign_rounds (
              campaign_unit_key TEXT NOT NULL,
              round_index INTEGER NOT NULL,
              edit_spec_ref TEXT NOT NULL,
              edit_spec_sha256 TEXT NOT NULL,
              created_at TEXT NOT NULL,
              PRIMARY KEY (campaign_unit_key, round_index)
            );
            INSERT INTO campaign_rounds SELECT * FROM campaign_rounds_guarded;
            DROP TABLE campaign_rounds_guarded;
            CREATE TABLE campaign_verifications (
              link_id INTEGER PRIMARY KEY AUTOINCREMENT,
              campaign_unit_key TEXT NOT NULL,
              arch_raw TEXT NOT NULL,
              arch_norm TEXT NOT NULL,
              verification_id TEXT NOT NULL UNIQUE,
              round_index INTEGER NOT NULL,
              edit_spec_sha256 TEXT NOT NULL,
              campaign_schema_version TEXT NOT NULL,
              created_at TEXT NOT NULL,
              UNIQUE (campaign_unit_key, arch_norm, round_index)
            );
            """
        )
        conn.execute(
            "INSERT INTO campaign_rounds VALUES (?, 2, ?, ?, ?)",
            (
                UNIT_KEY,
                str((tmp_path / "round-2.json").resolve()),
                EDIT_ONE,
                "2026-08-05T00:00:00+00:00",
            ),
        )
        conn.commit()
    finally:
        conn.close()
    _write_record(db, tmp_path, git, "V1")

    result = _reconcile(db)

    assert result.branch == "state_inconsistent_held"
    assert not _events(db, "ORPHAN_PASS")
    status = _latest_campaign_status(db)
    assert status is not None
    assert status["reason"] == "state_inconsistent"


def test_relink_savepoint_prevents_half_link_when_event_insert_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    git = _git_fixture(tmp_path)
    db = _db(tmp_path)
    _create_unit(db, git)
    _create_campaign_round(db, 1, EDIT_ONE)
    consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
    _write_record(db, tmp_path, git, "V1")
    original = campaign_state._insert_event_row

    def fail_pass_event(
        conn: sqlite3.Connection,
        campaign_unit_key: str,
        event_type: str,
        payload: dict[str, object],
    ) -> int:
        if event_type == "CONVERGENCE":
            raise sqlite3.IntegrityError("injected convergence failure")
        return original(conn, campaign_unit_key, event_type, payload)

    monkeypatch.setattr(campaign_state, "_insert_event_row", fail_pass_event)

    result = _reconcile(db)

    assert result.branch == "orphan_pass_held"
    conn = db.connect()
    try:
        assert conn.execute("SELECT COUNT(*) FROM campaign_verifications").fetchone()[0] == 0
    finally:
        conn.close()


def test_reconcile_busy_lock_is_retryable_and_writes_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    git = _git_fixture(tmp_path)
    db = _db(tmp_path)
    _create_unit(db, git)
    _create_campaign_round(db, 1, EDIT_ONE)
    lock = db.connect()
    lock.execute("BEGIN IMMEDIATE")
    original_connect = campaign_state._connect

    def connect_with_short_timeout(state_db: StateDatabase) -> sqlite3.Connection:
        conn = original_connect(state_db)
        conn.execute("PRAGMA busy_timeout=1")
        return conn

    monkeypatch.setattr(campaign_state, "_connect", connect_with_short_timeout)
    try:
        with pytest.raises(CampaignStateBusy, match="CAMPAIGN_STATE_BUSY"):
            _reconcile(db)
    finally:
        lock.rollback()
        lock.close()

    assert not _events(db, "CONVERGENCE")
    assert _latest_campaign_status(db) is None


def test_orphan_pass_overrides_current_linked_success_but_keeps_clean_writes(
    tmp_path: Path,
) -> None:
    git = _git_fixture(tmp_path)
    db = _db(tmp_path)
    _create_unit(db, git)
    _create_campaign_round(db, 1, EDIT_ONE)
    consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
    _write_record(db, tmp_path, git, "V1")
    _write_record(db, tmp_path, git, "V1B")
    _create_campaign_round(db, 2, EDIT_TWO)
    current = consume_build_invocation(db, UNIT_KEY, round_index=2, arch_norm="aarch64")
    record = _write_record(db, tmp_path, git, "V2", edit_sha=EDIT_TWO)
    link_verification_with_convergence(
        db,
        UNIT_KEY,
        convergence_payload=_pass_payload(current.event_id, "V2", round_index=2),
        arch_raw=record.arch,
        arch_norm="aarch64",
        verification_id="V2",
        round_index=2,
        edit_spec_sha256=EDIT_TWO,
    )

    result = _reconcile(db, round_index=2, edit_sha=EDIT_TWO)

    assert result.branch == "orphan_pass_held"
    assert result.current_verification_id is None
    assert result.held_rounds == (1,)
    conn = db.connect()
    try:
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM campaign_verifications WHERE verification_id = 'V2'"
            ).fetchone()[0]
            == 1
        )
    finally:
        conn.close()


def test_orphan_pass_overrides_current_relink_but_commits_the_clean_relink(
    tmp_path: Path,
) -> None:
    git = _git_fixture(tmp_path)
    db = _db(tmp_path)
    _create_unit(db, git)
    _create_campaign_round(db, 1, EDIT_ONE)
    current = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
    _write_record(db, tmp_path, git, "V1")
    _create_campaign_round(db, 2, EDIT_TWO)
    consume_build_invocation(db, UNIT_KEY, round_index=2, arch_norm="aarch64")
    _write_record(db, tmp_path, git, "V2A", edit_sha=EDIT_TWO)
    _write_record(db, tmp_path, git, "V2B", edit_sha=EDIT_TWO)

    result = _reconcile(db)

    assert result.branch == "orphan_pass_held"
    assert result.current_verification_id is None
    assert result.orphan_pass_verification_ids == ("V2A", "V2B")
    conn = db.connect()
    try:
        link = conn.execute(
            "SELECT verification_id FROM campaign_verifications WHERE round_index = 1"
        ).fetchone()
        convergence = conn.execute(
            "SELECT payload_json FROM campaign_gate_events "
            "WHERE event_type = 'CONVERGENCE' AND invocation_event_id = ?",
            (current.event_id,),
        ).fetchone()
    finally:
        conn.close()
    assert link["verification_id"] == "V1"
    assert json.loads(convergence["payload_json"])["result"] == "PASS"


def test_reconcile_result_lists_are_deterministically_sorted(tmp_path: Path) -> None:
    git = _git_fixture(tmp_path)
    db = _db(tmp_path)
    _create_unit(db, git)
    _create_campaign_round(db, 1, EDIT_ONE)
    _write_record(db, tmp_path, git, "VZ", edit_sha="9" * 64)
    _write_record(db, tmp_path, git, "VA", edit_sha="8" * 64)

    result = _reconcile(db)

    assert result.non_campaign_verification_ids == ("VA", "VZ")


def test_reconcile_keeps_existing_link_api_behavior(tmp_path: Path) -> None:
    git = _git_fixture(tmp_path)
    db = _db(tmp_path)
    _create_unit(db, git)
    _create_campaign_round(db, 1, EDIT_ONE)
    receipt = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
    record = _write_record(db, tmp_path, git, "V1")

    link_verification_with_convergence(
        db,
        UNIT_KEY,
        convergence_payload=_pass_payload(receipt.event_id, "V1", round_index=1),
        arch_raw=record.arch,
        arch_norm="aarch64",
        verification_id="V1",
        round_index=1,
        edit_spec_sha256=EDIT_ONE,
    )

    result = _reconcile(db)
    assert result.branch == "linked_already"
    assert result.current_verification_id == "V1"
    assert CAMPAIGN_SCHEMA_VERSION == "campaign/v1"
