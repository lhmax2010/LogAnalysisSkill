from __future__ import annotations

import copy
import hashlib
import json
import multiprocessing
import os
import stat
import time
import uuid
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest
from tizen_campaign_core import kb
from tizen_convergence_judge.convergence import _normalize_message, primary_fingerprint


def instance(**changes: Any) -> dict[str, Any]:
    values = dict(
        package="sample", gerrit_path="platform/upstream/sample", baseline_commit="a" * 40,
        verified_tree_sha="b" * 40, diagnosed_flag="-Wdeprecated", root_cause_category="type",
        toolchain_profile="clang", warning_flags=["-Werror", "-Wdeprecated"],
        error_signature_raw="ERROR: use OldAPI at foo.c:23:5", fix_summary="Replace OldAPI.",
        fix_strategy_initial="code", fix_strategy_final="code", status="CI_VERIFIED",
    )
    values.update(changes)
    return kb.make_record(**values)


def seed(**changes: Any) -> dict[str, Any]:
    values = dict(record_type="seed", diagnosed_flag="-Wdeprecated", root_cause_category="type",
                  toolchain_profile="clang", fix_summary="Replace the deprecated API.",
                  status="CI_VERIFIED")
    values.update(changes)
    return kb.make_record(**values)


def exact_query(db: Path, **changes: Any) -> kb.QueryResult:
    record = instance()
    args = dict(
        diagnosed_flag=record["diagnosed_flag"], package=record["package"],
        gerrit_path=record["gerrit_path"], category=record["root_cause_category"],
        warning_flags=record["warning_flags"], toolchain_profile=record["toolchain_profile"],
        error_signature=record["error_signature_raw"],
    )
    args.update(changes)
    return kb.query(db, **args)


@pytest.mark.parametrize("raw,expected", [
    ("ERROR at Foo.c:12:43 count 17", "error at foo.c:# count #"),
    ("\t Mixed\n SPACING  99 \r\n", "mixed spacing #"),
    ("v2 x86_64 12.34 :123:456:789", "v2 x86_64 #.# :#:#"),
    ("\u00c4PI \u4e2d\u6587 \u00a0 12", "\u00e4pi \u4e2d\u6587 #"),
    ("Warning: '-Werror,-Wdeprecated'", "warning: '-werror,-wdeprecated'"),
    ("", ""),
])
def test_normalizer_golden_parity(raw: str, expected: str) -> None:
    assert kb.normalize_signature(raw) == expected == _normalize_message(raw)


def test_describe_evidence_uses_primary_and_matching_candidate() -> None:
    packet = {
        "primary_error": {"id": "E2", "kind": "werror", "file": "a.c", "line": 4,
                          "message": "RAW Error: OldAPI [-Werror,-Wdeprecated]",
                          "warning_option": "-Wdeprecated"},
        "root_cause_candidates": [
            {"event_id": "E1", "semantic_class": "unrelated"},
            {"event_id": "E2", "semantic_class": "deprecated_api"},
        ],
    }
    before = copy.deepcopy(packet)
    result = kb.describe_evidence(packet)
    fingerprint = primary_fingerprint(packet, touched_files=None)
    assert fingerprint is not None
    assert result == {
        "diagnosed_flag": fingerprint.diagnostic_code,
        "root_cause_category": "deprecated_api",
        "warning_flags": ["-Wdeprecated", "-Werror"],
        "error_signature_raw": packet["primary_error"]["message"],
    }
    assert packet == before


def test_describe_real_analyzer_packet(tmp_path: Path) -> None:
    from gbs_analyzer.analyze import AnalyzeOptions, analyze_buildlog

    log = tmp_path / "ci.log"
    log.write_text("[1s] clang -c src/x.c\n"
                   "[2s] src/x.c:3:1: error: use of undeclared identifier 'missing'\n"
                   "[3s] make: *** [x.o] Error 1\n")
    result = analyze_buildlog(AnalyzeOptions(log, None, tmp_path / "analysis", use_tiktoken=False))
    assert result.exit_code == 0 and result.packet is not None
    description = kb.describe_evidence(result.packet)
    assert description["error_signature_raw"] == result.packet["primary_error"]["message"]
    assert description["diagnosed_flag"]
    assert description["root_cause_category"]


@pytest.mark.parametrize("packet", [{}, {"primary_error": {}}, {"primary_error": None},
                                     {"primary_error": {"message": 3}}])
def test_describe_invalid_packet(packet: dict[str, Any]) -> None:
    with pytest.raises(kb.KbSchemaError):
        kb.describe_evidence(packet)


@pytest.mark.parametrize("flag,category,profile,summary,expected", [
    ("-Werror", None, "clang", "Use a declaration.",
     "6651d857f84a03feee12339302f7a910db0e79e26a73e06462a27fd54248cd88"),
    (None, "type_mismatch", "clang", "  Cafe\u0301  ",
     "296e841e4609b509dfb98746ad67d4e6a20c98228e0d9faa413e62c56ef56a5b"),
    ("-Wfoo", "\u7c7b\u578b", "clang-18", " \u4fee\u590d\u58f0\u660e ",
     "60a357251881ef491545d5c166cbe3263ee66db961c9c06c5e4caf1c9e7f5b71"),
])
def test_seed_hardcoded_hash_vectors(
    flag: str | None, category: str | None, profile: str, summary: str, expected: str,
) -> None:
    record = seed(diagnosed_flag=flag, root_cause_category=category,
                  toolchain_profile=profile, fix_summary=summary)
    assert kb.dedupe_key(record) == expected


def test_seed_normalized_summary_dedupe_and_null_identity(tmp_path: Path) -> None:
    db = tmp_path / "kb.jsonl"
    first = kb.append(db, seed(fix_summary="  Cafe\u0301 \n"))
    before = db.read_bytes()
    assert kb.append(db, seed(fix_summary="Caf\u00e9")) == kb.AppendResult(first.id, True)
    assert db.read_bytes() == before
    second = kb.append(db, seed(fix_summary="Other strategy"))
    assert second.id != first.id
    row = kb.records(db)[0]
    for key in ("package", "gerrit_path", "baseline_commit", "verified_tree_sha", "files",
                "error_lines", "verified_archs", "error_signature_raw",
                "error_signature_normalized", "fix_strategy_initial", "fix_strategy_final"):
        assert row[key] is None
    assert row["fix_summary"] == "  Cafe\u0301 \n"
    assert exact_query(db).t1 == []
    assert len(exact_query(db).t2) == 2


@pytest.mark.parametrize("changes", [
    {"diagnosed_flag": None, "root_cause_category": None},
    {"diagnosed_flag": 1}, {"root_cause_category": []}, {"fix_summary": " \n\u00a0"},
    {"toolchain_profile": ""}, {"package": "invented"}, {"baseline_commit": "a" * 40},
])
def test_seed_invalid_input_rejected(changes: dict[str, Any]) -> None:
    with pytest.raises(kb.KbSchemaError):
        seed(**changes)


def test_ordinary_seven_part_formula_and_imported_raw_utf8(tmp_path: Path) -> None:
    row = instance()
    parts = [row[key] for key in ("package", "gerrit_path", "baseline_commit",
                                 "verified_tree_sha", "diagnosed_flag", "toolchain_profile",
                                 "error_signature_normalized")]
    assert kb.dedupe_key(row) == hashlib.sha256("".join(parts).encode("utf-8")).hexdigest()
    diff = b"--- a/a.c\r\n+++ b/a.c\r\n@@ -1 +1 @@\r\n-old\r\n+new\r\n"
    imported = instance(origin="imported_shelve", diff=diff.decode("utf-8"),
                        baseline_commit="A" * 40, verified_tree_sha=None,
                        fix_strategy_initial=None, fix_strategy_final=None)
    parts[2] = "A" * 40
    parts[3] = "imported:" + hashlib.sha256(diff).hexdigest()
    assert kb.dedupe_key(imported) == hashlib.sha256("".join(parts).encode()).hexdigest()
    db = tmp_path / "kb.jsonl"
    saved = kb.append(db, imported)
    assert kb.append(db, imported) == kb.AppendResult(saved.id, True)
    assert kb.records(db)[0]["diff"].encode("utf-8") == diff
    different = dict(imported, diff=imported["diff"].replace("new", "different"))
    assert kb.append(db, different).id != saved.id
    assert kb.records(db)[0]["baseline_commit"] == "A" * 40


@pytest.mark.parametrize("changes", [
    {"baseline_commit": None}, {"baseline_commit": "x" * 40}, {"verified_tree_sha": None},
    {"fix_strategy_initial": None}, {"fix_strategy_final": None},
    {"schema_version": "wrong"}, {"normalizer_version": "other"},
    {"error_signature_normalized": "wrong"}, {"status": "BROKEN"},
    {"warning_flags": [1]}, {"confidence": True}, {"confidence": float("nan")},
    {"change_ref": "refs/heads/main"}, {"change_ref": "refs/changes/12/123/1\n"},
    {"change_ref": "refs/changes/2/123/1"}, {"quickbuild_id": True},
])
def test_instance_schema_negative(changes: dict[str, Any]) -> None:
    with pytest.raises(kb.KbSchemaError):
        instance(**changes)


def test_imported_baseline_required_diff_strict_and_no_policy_fabrication(tmp_path: Path) -> None:
    base = dict(instance(), origin="imported_shelve", verified_tree_sha=None, diff="patch\r\n",
                fix_strategy_initial=None, fix_strategy_final=None)
    for change in ({"baseline_commit": None}, {"diff": b"patch"}, {"diff": "\udcff"}):
        with pytest.raises(kb.KbSchemaError):
            kb.append(tmp_path / "kb.jsonl", dict(base, **change))
    assert not (tmp_path / "kb.jsonl").exists()
    kb.append(tmp_path / "kb.jsonl", base)
    assert kb.records(tmp_path / "kb.jsonl")[0]["fix_strategy_final"] is None


@pytest.mark.parametrize("changed", [
    {"package": "other"}, {"gerrit_path": "platform/other"}, {"category": "other"},
    {"diagnosed_flag": "-Wother"}, {"warning_flags": ["-Werror"]},
    {"toolchain_profile": "gcc"}, {"error_signature": "different message"},
    {"package": None}, {"gerrit_path": None}, {"category": None},
    {"warning_flags": None}, {"toolchain_profile": None}, {"error_signature": None},
])
def test_t1_requires_every_key(tmp_path: Path, changed: dict[str, Any]) -> None:
    db = tmp_path / "kb.jsonl"
    kb.append(db, instance())
    assert len(exact_query(db).t1) == 1
    assert exact_query(db, **changed).t1 == []


def test_t1_baseline_not_key_warning_set_confidence_and_display_url(tmp_path: Path) -> None:
    db = tmp_path / "kb.jsonl"
    first = kb.append(db, instance(confidence=-10, gerrit_url="https://untrusted.invalid/payload"))
    second = kb.append(db, instance(baseline_commit="c" * 40, confidence=999))
    result = exact_query(db, warning_flags=["-Wdeprecated", "-Werror", "-Werror"])
    assert [row["id"] for row in result.t1] == [first.id, second.id]
    assert result.t1[0]["gerrit_url"] == "https://untrusted.invalid/payload"
    assert result.t1[0]["normalizer_version"] == kb.NORMALIZER_VERSION
    with pytest.raises(FrozenInstanceError):
        result.t1 = []  # type: ignore[misc]


def test_t2_priority_stability_limit_and_new_excluded(tmp_path: Path) -> None:
    db = tmp_path / "kb.jsonl"
    low = kb.append(db, instance(confidence=999))
    merged = kb.append(db, instance(baseline_commit="c" * 40, status="MERGED", confidence=-5))
    flag = kb.append(db, seed(root_cause_category=None, confidence=999))
    category = kb.append(db, seed(diagnosed_flag=None, confidence=-9))
    category2 = kb.append(db, seed(fix_summary="Another", diagnosed_flag=None, confidence=-9))
    higher = kb.append(db, seed(fix_summary="Higher confidence tie", confidence=0))
    kb.append(db, instance(baseline_commit="d" * 40, status="NEW"))
    kb.append(db, seed(fix_summary="NEW seed", status="NEW"))
    result = exact_query(db, min_status="NEW", limit_t2=20)
    assert [row["id"] for row in result.t2] == [
        higher.id, category.id, category2.id, flag.id, merged.id, low.id,
    ]
    assert len(exact_query(db).t2) == 5
    assert exact_query(db, limit_t2=0).t2 == []
    assert [row["id"] for row in exact_query(db, min_status="MERGED").t2] == [merged.id]
    assert all(row["record_type"] == "instance" for row in result.t1)


def test_append_promote_noop_identity_order_and_read_only_query(tmp_path: Path) -> None:
    db = tmp_path / "kb.jsonl"
    assert kb.records(db) == [] and not (tmp_path / ".lock").exists()
    assert exact_query(db) == kb.QueryResult([], [])
    source = instance(status="NEW")
    first = kb.append(db, source)
    second = kb.append(db, instance(baseline_commit="c" * 40))
    before = db.read_bytes(), db.stat().st_mtime_ns, db.stat().st_ino
    assert kb.append(db, source) == kb.AppendResult(first.id, True)
    kb.promote(db, second.id, "CI_VERIFIED")
    assert before == (db.read_bytes(), db.stat().st_mtime_ns, db.stat().st_ino)
    promoted = kb.promote(db, first.id, "MERGED")
    assert promoted["promoted_at"] and promoted["created_at"]
    assert str(uuid.UUID(first.id)) == first.id
    assert [r["id"] for r in kb.records(db)] == [first.id, second.id]
    before = db.read_bytes()
    for action in (lambda: kb.promote(db, first.id, "NEW"),
                   lambda: kb.promote(db, first.id, "INVALID"),
                   lambda: kb.promote(db, str(uuid.uuid4()), "MERGED")):
        with pytest.raises(kb.KbSchemaError):
            action()
        assert db.read_bytes() == before
    exact_query(db)
    assert db.read_bytes() == before
    assert "id" not in source and "created_at" not in source


def test_promote_keyword_contract(tmp_path: Path) -> None:
    db = tmp_path / "kb.jsonl"
    result = kb.append(db, instance(status="NEW"))
    row = kb.promote(db=db, id=result.id, to_status="CI_VERIFIED")
    assert row["id"] == result.id and row["status"] == "CI_VERIFIED"


@pytest.mark.parametrize("damage", ["invalid-json", "encoding", "duplicate-key", "duplicate-row",
                                    "schema", "dedupe", "blank", "nonfinite", "missing"])
def test_corrupt_database_fails_closed_every_operation(tmp_path: Path, damage: str) -> None:
    db = tmp_path / "kb.jsonl"
    saved = kb.append(db, instance())
    good = db.read_bytes()
    mutations = {
        "invalid-json": good + b"{bad\n", "encoding": good + b"\xff\n",
        "duplicate-key": good.replace(b'"package": "sample"', b'"package":"x","package":"y"'),
        "duplicate-row": good + good, "schema": good.replace(b"clang_kb/v1", b"clang_kb/v9"),
        "dedupe": good.replace(b'"dedupe_key": "', b'"dedupe_key": "0'),
        "blank": good + b"\n", "nonfinite": good.replace(b'"confidence": 0', b'"confidence": NaN'),
        "missing": good.replace(b'"status":', b'"wrong_status":'),
    }
    db.write_bytes(mutations[damage])
    before = db.read_bytes()
    for action in (lambda: kb.records(db), lambda: exact_query(db),
                   lambda: kb.append(db, instance()), lambda: kb.promote(db, saved.id, "MERGED")):
        with pytest.raises(kb.KbCorrupt):
            action()
        assert db.read_bytes() == before


def test_atomic_publish_order_and_failure_cleanup(tmp_path: Path, monkeypatch: Any) -> None:
    db = tmp_path / "kb.jsonl"
    first = kb.append(db, instance())
    old = db.read_bytes()
    events: list[str] = []
    fsync, replace = os.fsync, os.replace

    def sync(fd: int) -> None:
        events.append("dirsync" if stat.S_ISDIR(os.fstat(fd).st_mode) else "filesync")
        fsync(fd)

    def rename(src: Any, dst: Any) -> None:
        assert kb.records(db)[0]["id"] == first.id and db.read_bytes() == old
        events.append("replace")
        replace(src, dst)

    monkeypatch.setattr(kb.os, "fsync", sync)
    monkeypatch.setattr(kb.os, "replace", rename)
    kb.append(db, instance(baseline_commit="c" * 40))
    assert events == ["filesync", "replace", "dirsync"]
    before = db.read_bytes()

    def failed_replace(src: Any, dst: Any) -> None:
        raise OSError("injected replace failure")

    monkeypatch.setattr(kb.os, "replace", failed_replace)
    with pytest.raises(OSError):
        kb.promote(db, first.id, "MERGED")
    assert db.read_bytes() == before
    assert sorted(p.name for p in tmp_path.iterdir()) == [".lock", "kb.jsonl"]


@pytest.mark.parametrize("stage", ["temp", "file-fsync", "replace", "dir-fsync"])
def test_atomic_failures_leave_complete_old_or_new_database(
    tmp_path: Path, monkeypatch: Any, stage: str,
) -> None:
    db = tmp_path / "kb.jsonl"
    kb.append(db, instance())
    before = db.read_bytes()
    fsync = os.fsync

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise OSError("injected storage failure")

    def sync(fd: int) -> None:
        directory = stat.S_ISDIR(os.fstat(fd).st_mode)
        if (stage == "dir-fsync" and directory) or (stage == "file-fsync" and not directory):
            fail()
        fsync(fd)

    if stage == "temp":
        monkeypatch.setattr(kb.tempfile, "mkstemp", fail)
    elif stage == "replace":
        monkeypatch.setattr(kb.os, "replace", fail)
    else:
        monkeypatch.setattr(kb.os, "fsync", sync)
    with pytest.raises(OSError):
        kb.append(db, instance(baseline_commit="c" * 40))
    assert len(kb.records(db)) == (2 if stage == "dir-fsync" else 1)
    if stage != "dir-fsync":
        assert db.read_bytes() == before
    assert sorted(p.name for p in tmp_path.iterdir()) == [".lock", "kb.jsonl"]


@pytest.mark.parametrize("changes", [
    {"limit_t2": -1}, {"limit_t2": True}, {"limit_t2": 1.2}, {"min_status": "bad"},
    {"diagnosed_flag": ""}, {"warning_flags": "-Wfoo"}, {"warning_flags": [1]},
])
def test_query_invalid_arguments_do_not_create_files(
    tmp_path: Path, changes: dict[str, Any],
) -> None:
    with pytest.raises(kb.KbSchemaError):
        exact_query(tmp_path / "kb.jsonl", **changes)
    assert list(tmp_path.iterdir()) == []


def test_huge_confidence_is_schema_error_not_overflow() -> None:
    with pytest.raises(kb.KbSchemaError, match="invalid_confidence"):
        instance(confidence=10 ** 400)


def _writer(db: Path, barrier: Any, index: int, shared_id: str) -> None:
    barrier.wait(timeout=20)
    kb.append(db, seed())
    kb.append(db, instance(baseline_commit=f"{index + 1:040x}"))
    kb.promote(db, shared_id, "MERGED")


def test_process_concurrency_append_and_promote_no_loss(tmp_path: Path) -> None:
    db = tmp_path / "kb.jsonl"
    first = kb.append(db, instance(status="NEW"))
    ctx = multiprocessing.get_context("fork")
    barrier = ctx.Barrier(6)
    workers = [ctx.Process(target=_writer, args=(db, barrier, i, first.id)) for i in range(6)]
    for process in workers:
        process.start()
    for process in workers:
        process.join(timeout=30)
    try:
        assert all(not process.is_alive() and process.exitcode == 0 for process in workers)
    finally:
        for process in workers:
            if process.is_alive():
                process.terminate()
                process.join(timeout=10)
    rows = kb.records(db)
    assert len(rows) == 8
    assert rows[0]["id"] == first.id and rows[0]["status"] == "MERGED"
    assert sum(row["record_type"] == "seed" for row in rows) == 1


def test_unicode_line_separators_roundtrip(tmp_path: Path) -> None:
    db = tmp_path / "kb.jsonl"
    kb.append(db, instance(fix_summary="one\u2028two\u0085three"))
    assert kb.records(db)[0]["fix_summary"] == "one\u2028two\u0085three"


def test_query_ten_thousand_rows_under_one_second(tmp_path: Path) -> None:
    db = tmp_path / "kb.jsonl"
    kb.append(db, instance())
    template = kb.records(db)[0]
    rows = []
    for number in range(10_000):
        row = dict(template, baseline_commit=f"{number:040x}", id=str(uuid.uuid4()))
        row["dedupe_key"] = kb.dedupe_key(row)
        rows.append(row)
    db.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
                  encoding="utf-8")
    started = time.perf_counter()
    result = exact_query(db)
    elapsed = time.perf_counter() - started
    assert len(result.t1) == 10_000 and len(result.t2) == 5
    assert elapsed < 1.0, f"10k query: {elapsed:.3f}s"
