from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

import pytest
from ci_triage.cli import main as legacy_main
from tizen_campaign_core import kb
from tizen_campaign_kb.cli import main

LOG = Path(__file__).resolve().parents[1] / "fixtures/e2e_clang_compile/buildlog"


def invoke(args):
    output = io.StringIO()
    code = main(args, stdout=output)
    return code, json.loads(output.getvalue())


@pytest.fixture
def imported(tmp_path):
    diff = tmp_path / "fix.diff"
    diff.write_bytes(b"--- a/file.c\n+++ b/file.c\n@@ -1 +1 @@\n-old\n+new\n")
    db = tmp_path / "kb/records.jsonl"
    args = ["kb", "import-diff", "--db", str(db), "--diff", str(diff),
            "--ci-log", str(LOG), "--package", "example", "--gerrit-path",
            "platform/upstream/example", "--toolchain-profile", "clang",
            "--fix-summary", "Offline repair", "--baseline-commit", "a" * 40]
    return args, db, diff


@pytest.mark.parametrize("commit", [None, "", "a" * 39, "g" * 40, "a" * 41])
def test_import_requires_valid_baseline_before_analyzer(imported, monkeypatch, commit):
    import tizen_campaign_kb.cli as cli

    args, db, _ = imported
    args = args[:-2]
    if commit is not None:
        args += ["--baseline-commit", commit]
    monkeypatch.setattr(cli, "analyze", lambda *a: pytest.fail("analyzer ran"))
    code, out = invoke(args)
    assert code == 2 and out["error_code"] == "INVALID_ARGS"
    assert not db.exists()


def test_real_analyzer_import_dedupe_and_different_diff(imported):
    args, db, diff = imported
    code, first = invoke(args)
    assert code == 0, first
    raw = db.read_bytes()
    assert invoke(args) == (0, {"id": first["id"], "deduped": True})
    assert db.read_bytes() == raw
    record = kb.records(db)[0]
    assert record["origin"] == "imported_shelve" and record["status"] == "NEW"
    assert record["baseline_commit"] == "a" * 40 and record["verified_tree_sha"] is None
    assert record["diff"].encode() == diff.read_bytes()
    assert record["error_signature_raw"] and record["error_signature_normalized"]
    assert record["normalizer_version"] == "campaign.v1(parity: convergence)"
    diff.write_bytes(diff.read_bytes().replace(b"+new", b"+other"))
    code, changed = invoke(args)
    assert code == 0 and changed["id"] != first["id"] and not changed["deduped"]
    assert len(kb.records(db)) == 2


def test_import_crlf_hashes_original_bytes_and_supplied_ci(imported):
    args, db, diff = imported
    diff.write_bytes(diff.read_bytes().replace(b"\n", b"\r\n"))
    code, out = invoke(args + ["--quickbuild-id", "123", "--change-ref", "refs/changes/12/12/1"])
    assert code == 0, out
    record = kb.records(db)[0]
    assert record["diff"].encode() == diff.read_bytes()
    assert record["status"] == "CI_VERIFIED" and record["quickbuild_id"] == 123
    parts = [record[k] for k in ("package", "gerrit_path", "baseline_commit")]
    parts += ["imported:" + hashlib.sha256(diff.read_bytes()).hexdigest(),
              record["diagnosed_flag"], record["toolchain_profile"],
              record["error_signature_normalized"]]
    assert record["dedupe_key"] == hashlib.sha256("".join(parts).encode()).hexdigest()


@pytest.mark.parametrize("extra", [
    ["--change-ref", "refs/heads/main"], ["--quickbuild-id", "0"],
    ["--quickbuild-id", "invalid"], ["--toolchain-profile", "gcc"],
    ["--package", ""], ["--fix-summary", " "],
])
def test_bad_import_arguments_never_write(imported, extra):
    args, db, _ = imported
    code, out = invoke(args + extra)
    assert code == 2 and out["error_code"] == "INVALID_ARGS"
    assert not db.exists()


def test_cli_query_promote_and_corrupt_jsonl(imported):
    args, db, _ = imported
    code, stored = invoke(args)
    assert code == 0
    record = kb.records(db)[0]
    query = ["kb", "query", "--db", str(db), "--diagnosed-flag", record["diagnosed_flag"]]
    assert invoke(query) == (0, {"t1_records": [], "t2_records": []})
    promote = ["kb", "promote", "--db", str(db), "--id", stored["id"], "--to", "CI_VERIFIED"]
    assert invoke(promote)[0] == 0
    assert len(invoke(query)[1]["t2_records"]) == 1
    raw = db.read_bytes()
    invoke(promote)
    assert db.read_bytes() == raw
    db.write_bytes(raw + b"invalid json\n")
    assert invoke(query) == (
        4, {"error_code": "KB_SCHEMA_INVALID", "reason": "invalid_jsonl_record"},
    )
    assert db.read_bytes() == raw + b"invalid json\n"


@pytest.mark.parametrize("args", [["kb"], ["kb", "import-diff"], ["campaign-kb-sync"]])
def test_legacy_and_package_invalid_args_same(args):
    stdout = io.StringIO()
    expected = invoke(args)
    code = legacy_main(args, stdout=stdout)
    assert (code, json.loads(stdout.getvalue())) == expected


@pytest.mark.parametrize("summary,flag,category,ok", [
    ("Normalize casts", "-Wexample", None, True),
    ("Normalize casts", None, "conversion", True),
    ("Normalize casts", None, None, False),
    (" \n", "-Wexample", None, False),
])
def test_seed_cli_append_contract(tmp_path, summary, flag, category, ok):
    record = dict(record_type="seed", diagnosed_flag=flag, root_cause_category=category,
                  toolchain_profile="clang", fix_summary=summary, status="CI_VERIFIED")
    record_path, db = tmp_path / "record.json", tmp_path / "kb/db.jsonl"
    record_path.write_text(json.dumps(record))
    args = ["kb", "append", "--db", str(db), "--record", str(record_path)]
    code, result = invoke(args)
    assert code == (0 if ok else 2), result
    if ok:
        row = kb.records(db)[0]
        assert row["package"] is None and row["baseline_commit"] is None
        assert row["fix_strategy_initial"] is None and row["fix_strategy_final"] is None
        assert invoke(args) == (0, dict(id=result["id"], deduped=True))
    else:
        assert result["error_code"] == "INVALID_ARGS" and not db.exists()


@pytest.mark.parametrize("value", [[], None, "record"])
def test_append_nonobject_is_json_error_without_output_db(tmp_path, value):
    record, db = tmp_path / "record.json", tmp_path / "db.jsonl"
    record.write_text(json.dumps(value))
    assert invoke(["kb", "append", "--db", str(db), "--record", str(record)])[0] == 2
    assert not db.exists()


def test_malformed_config_does_not_echo_values_or_write_state(tmp_path):
    config, db = tmp_path / "config.yaml", tmp_path / "state.db"
    config.write_text("campaign_workspace: [SYNTHETIC_SECRET_DO_NOT_ECHO")
    code, result = invoke(["campaign-kb-sync", "--state-db", str(db),
                           "--config", str(config), "--campaign-unit-key", "unit"])
    assert code == 2
    assert result == dict(error_code="INVALID_ARGS", reason="invalid_configuration")
    assert not db.exists()
