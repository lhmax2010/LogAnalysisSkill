from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from ci_triage import aggregate
from tizen_ci_shared.state import StateDatabase, VerificationRecord, write_pass_record


@pytest.fixture
def records() -> tuple[VerificationRecord, ...]:
    return tuple(VerificationRecord(
        verification_id=f"v{index}", result="PASS", timestamp="2026-10-08T00:00:00Z",
        failure_key=f"failure-{arch}", base_commit="a" * 40,
        verified_commit_sha=str(index) * 40, verified_tree_sha="b" * 40,
        canonical_diff_sha256=str(index) * 64, patch_sha256=str(index) * 64,
        edit_spec_sha256="e" * 64, project="platform/example", branch="tizen",
        spec_name="example", arch=arch, gbs_conf_sha256="f" * 64,
        build_log_sha256=str(index) * 64, worktree_path=f"/work/{arch}",
        command_line=f"gbs build -A {arch}",
    ) for index, arch in enumerate(("standard-aarch64", "standard-armv7l", "standard-x86_64")))


def _store(tmp_path: Path, records: tuple[VerificationRecord, ...]) -> StateDatabase:
    db = StateDatabase(tmp_path / "state.sqlite3")
    for record in records:
        write_pass_record(db, record)
    return db


def _dump(db: StateDatabase) -> list[str]:
    conn = db.connect()
    try:
        return list(conn.iterdump())
    finally:
        conn.close()


def test_consistent_aggregate_binds_real_columns_without_writing(
    tmp_path: Path, records: tuple[VerificationRecord, ...],
) -> None:
    db = _store(tmp_path, records)
    before = _dump(db)
    result = aggregate.aggregate_verifications(["v2", "v0", "v1"], db)
    assert result.ok and result.reasons == ()
    assert result.records == (records[2], records[0], records[1])
    assert result.verified_tree_sha == "b" * 40
    assert result.base_commit == "a" * 40
    assert result.spec_name == "example"
    assert result.project == "platform/example"
    assert result.branch == "tizen"
    assert result.edit_spec_sha256 == "e" * 64
    assert result.gbs_conf_sha256 == "f" * 64
    assert _dump(db) == before


@pytest.mark.parametrize("field", [
    "verified_tree_sha", "base_commit", "spec_name", "project", "branch",
    "edit_spec_sha256", "gbs_conf_sha256",
])
def test_each_binding_mismatch_reports_concrete_values(
    tmp_path: Path, records: tuple[VerificationRecord, ...], field: str,
) -> None:
    changed = (records[0], replace(records[1], **{field: "different-value"}), records[2])
    db = _store(tmp_path, changed)
    before = _dump(db)
    result = aggregate.aggregate_verifications([r.verification_id for r in changed], db)
    assert not result.ok and len(result.reasons) == 1
    assert result.reasons[0].startswith("REJECTED_ARCH_AGGREGATE_MISMATCH:")
    assert f"{field}={getattr(records[0], field)!r}" in result.reasons[0]
    assert f"{field}='different-value'" in result.reasons[0]
    assert "verification_id='v1' arch='standard-armv7l'" in result.reasons[0]
    assert all(getattr(result, name) is None for name in (
        "verified_tree_sha", "base_commit", "spec_name", "project", "branch",
        "edit_spec_sha256", "gbs_conf_sha256",
    ))
    assert _dump(db) == before


@pytest.mark.parametrize("arch", [
    "standard_gcov-armv7l", "emulator-armv7l", "armv7l", "standard-riscv64", "",
])
def test_arch_whitelist_does_not_strip_profiles(
    tmp_path: Path, records: tuple[VerificationRecord, ...], arch: str,
) -> None:
    changed = (records[0], replace(records[1], arch=arch), records[2])
    result = aggregate.aggregate_verifications(["v0", "v1", "v2"], _store(tmp_path, changed))
    assert not result.ok
    assert f"REJECTED_ARCH_NOT_ALLOWED: verification_id='v1' arch={arch!r}" in result.reasons
    assert any("arch_norm=['aarch64', 'x86_64']" in reason for reason in result.reasons)


def test_arch_set_must_include_each_target(
    tmp_path: Path, records: tuple[VerificationRecord, ...],
) -> None:
    changed = (records[0], replace(records[1], arch="standard-aarch64"), records[2])
    result = aggregate.aggregate_verifications(["v0", "v1", "v2"], _store(tmp_path, changed))
    assert not result.ok and len(result.reasons) == 1
    assert "arch_norm=['aarch64', 'x86_64']" in result.reasons[0]
    assert "expected=['aarch64', 'armv7l', 'x86_64']" in result.reasons[0]


@pytest.mark.parametrize("ids", [[], ["v0", "v1"], ["v0", "v1", "v2", "v0"]])
def test_exactly_three_records_required(
    tmp_path: Path, records: tuple[VerificationRecord, ...], ids: list[str],
) -> None:
    result = aggregate.aggregate_verifications(ids, _store(tmp_path, records))
    assert not result.ok
    assert f"record_count={len(ids)} expected=3" in result.reasons[0]


def test_missing_id_is_not_silently_dropped(
    tmp_path: Path, records: tuple[VerificationRecord, ...],
) -> None:
    result = aggregate.aggregate_verifications(["v0", "absent", "v2"], _store(tmp_path, records))
    assert not result.ok
    assert any("verification_id='absent' record not found" in r for r in result.reasons)


def test_duplicate_id_cannot_supply_missing_arch(
    tmp_path: Path, records: tuple[VerificationRecord, ...],
) -> None:
    result = aggregate.aggregate_verifications(["v0", "v1", "v1"], _store(tmp_path, records))
    assert not result.ok and any("arch_norm=" in r for r in result.reasons)


def test_non_pass_record_is_rejected_defensively(
    tmp_path: Path, records: tuple[VerificationRecord, ...], monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The real DB's CHECK forbids non-PASS rows; exercise the read boundary with a fake.
    changed = {r.verification_id: r for r in records}
    changed["v1"] = replace(records[1], result="FAIL")
    monkeypatch.setattr(aggregate, "get_record", lambda db, key: changed[key])
    result = aggregate.aggregate_verifications(["v0", "v1", "v2"], StateDatabase(tmp_path / "db"))
    assert not result.ok and len(result.reasons) == 1
    assert "result='FAIL' expected='PASS'" in result.reasons[0]


def test_all_field_differences_are_reported_without_short_circuit(
    tmp_path: Path, records: tuple[VerificationRecord, ...],
) -> None:
    changed = (records[0], replace(records[1], spec_name="other", project="other/project"),
               replace(records[2], verified_tree_sha="c" * 40))
    result = aggregate.aggregate_verifications(["v0", "v1", "v2"], _store(tmp_path, changed))
    assert not result.ok and len(result.reasons) == 3
    assert any("spec_name='other'" in r for r in result.reasons)
    assert any("project='other/project'" in r for r in result.reasons)
    assert any("verified_tree_sha='" + "c" * 40 + "'" in r for r in result.reasons)


def test_only_branch_mismatch_rejects_otherwise_consistent_records(
    tmp_path: Path, records: tuple[VerificationRecord, ...],
) -> None:
    changed = (records[0], records[1], replace(records[2], branch="other-branch"))
    result = aggregate.aggregate_verifications(["v0", "v1", "v2"], _store(tmp_path, changed))
    assert not result.ok and result.branch is None
    assert len(result.reasons) == 1
    assert "verification_id='v2' arch='standard-x86_64' branch='other-branch'" in result.reasons[0]
    assert "branch='tizen'" in result.reasons[0]


@pytest.mark.parametrize("field", [
    "verified_tree_sha", "base_commit", "spec_name", "project", "branch",
    "edit_spec_sha256", "gbs_conf_sha256",
])
@pytest.mark.parametrize("empty", ["", " \t "])
def test_all_three_empty_bindings_report_each_record(
    tmp_path: Path, records: tuple[VerificationRecord, ...], field: str, empty: str,
) -> None:
    changed = tuple(replace(record, **{field: empty}) for record in records)
    db = _store(tmp_path, changed)
    before = _dump(db)
    result = aggregate.aggregate_verifications(["v0", "v1", "v2"], db)
    assert not result.ok
    assert len(result.reasons) == 3
    for record, reason in zip(changed, result.reasons, strict=True):
        assert f"verification_id={record.verification_id!r}" in reason
        assert f"{field}={empty!r} must be nonempty after strip" in reason
    assert all(getattr(result, name) is None for name in (
        "verified_tree_sha", "base_commit", "spec_name", "project", "branch",
        "edit_spec_sha256", "gbs_conf_sha256",
    ))
    assert _dump(db) == before
