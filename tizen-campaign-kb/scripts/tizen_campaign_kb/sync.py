"""Synchronize audited campaign provenance without campaign state transitions."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tizen_campaign_core import campaign_state as state
from tizen_campaign_core import kb
from tizen_campaign_core._campaign_workspace import _unit_hash
from tizen_campaign_core.aggregate import aggregate_verifications
from tizen_campaign_core.submission_identity import compute_submission_key
from tizen_ci_shared.state import StateDatabase
from tizen_sandbox_submit.sandbox_submit import _locks, _SnapshotDatabase


def _bound_json(path: str | None, digest: str | None) -> dict[str, Any]:
    try:
        if not path or not digest:
            raise ValueError("missing artifact binding")
        raw = Path(path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError("artifact digest differs")
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError("artifact is not an object")
        return value
    except (ValueError, OSError) as exc:
        raise state.StateInconsistent("KB provenance artifact is unavailable or changed") from exc


def _provenance(
    conn: sqlite3.Connection, db: StateDatabase, key: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None]:
    unit = state._require_unit(conn, key)
    view = state._gate_view_on_connection(conn, key)
    push, derive = view.sandbox_push, view.derive
    if not push or push.get("result") != "ok" or not derive:
        raise state.StateInconsistent("KB synchronization requires a successful sandbox PUSH")
    if push.get("pushed_sha") != derive.get("derived_commit_sha"):
        raise state.StateInconsistent("sandbox PUSH and DERIVE differ")
    row = conn.execute(
        "SELECT * FROM campaign_rounds WHERE campaign_unit_key=? ORDER BY round_index DESC LIMIT 1",
        (key,),
    ).fetchone()
    if row is None:
        raise state.StateInconsistent("KB synchronization requires a bound round")
    round_index = row["round_index"]
    policy = state._policy_on_connection(conn, key, round_index)
    if not policy or policy.get("verdict") != "allowed":
        raise state.StateInconsistent("KB synchronization requires an allowed bound POLICY")
    source = policy.get("edit_source_kind")
    if source not in {"generated", "suppress", "t1_cherry_pick"}:
        raise state.StateInconsistent("invalid bound POLICY source")
    if policy.get("fix_strategy_initial") != {
        "generated": "code", "suppress": "suppress", "t1_cherry_pick": "cherry_pick",
    }[source] or policy.get("fix_strategy_final") not in {"code", "suppress", "cherry_pick"}:
        raise state.StateInconsistent("invalid bound POLICY strategy")
    links = conn.execute(
        "SELECT * FROM campaign_verifications WHERE campaign_unit_key=? AND round_index=?",
        (key, round_index),
    ).fetchall()
    aggregate = aggregate_verifications(
        [link["verification_id"] for link in links], _SnapshotDatabase(db.path, conn),
    )
    if not aggregate.ok or any((
        aggregate.verified_tree_sha != derive.get("verified_tree_sha"),
        aggregate.edit_spec_sha256 != row["edit_spec_sha256"],
        aggregate.base_commit != unit.base_commit,
        aggregate.project != unit.project,
        aggregate.branch != unit.branch,
        aggregate.spec_name != unit.spec_name,
    )) or any(
        link["edit_spec_sha256"] != row["edit_spec_sha256"]
        or link["arch_norm"] != state.ARCH_RAW_TO_NORM.get(link["arch_raw"])
        or not any(record.verification_id == link["verification_id"]
                   and record.arch == link["arch_raw"] for record in aggregate.records)
        for link in links
    ):
        raise state.StateInconsistent("KB provenance verification binding differs")
    spec = _bound_json(row["edit_spec_ref"], row["edit_spec_sha256"])
    evidence = _bound_json(unit.ci_evidence_ref, unit.ci_evidence_sha256)
    precedent = spec.get("kb_precedent_ref")
    if precedent is not None and (not isinstance(precedent, str) or not precedent.strip()):
        raise state.StateInconsistent("invalid bound precedent reference")
    if source == "t1_cherry_pick" and precedent is None:
        raise state.StateInconsistent("T1 provenance requires a bound precedent reference")
    edits = spec.get("edits")
    if not isinstance(edits, list) or not edits or any(
        not isinstance(edit, dict) or not isinstance(edit.get("file"), str)
        or not edit["file"] for edit in edits
    ):
        raise state.StateInconsistent("invalid bound edit entries")
    change_id = state._cached_change_id(
        conn, compute_submission_key(
            unit.submission_identity_key, str(aggregate.verified_tree_sha),
        ),
    )
    if not change_id:
        raise state.StateInconsistent("KB provenance requires the cached Change-Id")
    push_row = conn.execute(
        "SELECT event_id FROM campaign_gate_events WHERE campaign_unit_key=? "
        "AND event_type='PUSH' AND json_extract(payload_json,'$.ref_class')='sandbox' "
        "ORDER BY event_id DESC LIMIT 1", (key,),
    ).fetchone()
    description = kb.describe_evidence(evidence)
    if not unit.source_build_id.isascii() or not unit.source_build_id.isdigit():
        raise state.StateInconsistent("invalid CI build provenance")
    record = kb.make_record(
        schema_version="clang_kb/v1", record_type="instance",
        fix_strategy_initial=policy["fix_strategy_initial"],
        fix_strategy_final=policy["fix_strategy_final"], reused_from=precedent,
        package=unit.spec_name, gerrit_path=unit.project,
        files=sorted({edit["file"] for edit in edits}),
        error_lines=[description["error_signature_raw"]],
        fix_summary=derive["message_brief"], confidence=0,
        quickbuild_id=int(unit.source_build_id), baseline_commit=unit.base_commit,
        verified_tree_sha=aggregate.verified_tree_sha,
        verified_archs=sorted(state.ARCH_NORMS), sandbox_branch=push["ref"],
        gerrit_url=None, change_ref=None, change_id=change_id, status="NEW",
        created_at=push["at"], promoted_at=None, toolchain_profile=unit.toolchain_profile,
        **description,
    )
    audit = dict(
        round_index=round_index, source_kind=source, kb_precedent_ref=precedent,
        push_event_id=push_row["event_id"], qb_event_id=None,
    )
    result = state._qb_result_on_connection(conn, key)
    if result is not None and result["status"] == "PASS":
        request = conn.execute(
            "SELECT * FROM campaign_qb_requests WHERE request_seq=?", (result["request_seq"],),
        ).fetchone()
        target = unit.project + "@" + str(derive["derived_commit_sha"])
        bound = conn.execute(
            "SELECT qb_build_id FROM campaign_qb_events WHERE request_seq=? "
            "AND event_type='BUILD_BOUND' ORDER BY event_id DESC LIMIT 1",
            (result["request_seq"],),
        ).fetchone()
        if (request is None or request["sbs_target"] != target
                or result["sbs_target_echo"] != target or bound is None
                or bound["qb_build_id"] != result["qb_build_id"]):
            raise state.StateInconsistent("latest QB PASS binding differs")
    else:
        result = None
    return record, audit, result


def run(state_db: StateDatabase, key: str, settings: dict[str, Any]) -> dict[str, Any]:
    """Retry safely across a KB publication followed by an interrupted DB commit."""
    path = settings.get("kb_db")
    workspace = settings.get("campaign_workspace")
    if (not isinstance(path, str) or not Path(path).is_absolute()
            or not isinstance(workspace, str) or not Path(workspace).is_absolute()):
        raise ValueError("kb_db and campaign_workspace must be absolute paths")
    kb_db = Path(path)
    with _locks(Path(workspace) / _unit_hash(key)):
        conn = state_db.connect()
        try:
            # KB publication precedes the audit. Hold one provenance snapshot and
            # use append/promote idempotence to recover after a failed DB commit.
            with state._immediate_transaction(conn):
                record, audit, result = _provenance(conn, state_db, key)
                previous = conn.execute(
                    "SELECT event_id,payload_json FROM campaign_gate_events "
                    "WHERE campaign_unit_key=? AND event_type='KB_SYNC' "
                    "AND round_index=? ORDER BY event_id DESC LIMIT 1", (key, audit["round_index"]),
                ).fetchone()
                old = json.loads(previous["payload_json"]) if previous is not None else {}
                if old:
                    known = [item for item in kb.records(kb_db) if item["id"] == old["kb_id"]]
                    if (len(known) != 1 or known[0]["dedupe_key"] != old["dedupe_key"]
                            or old["dedupe_key"] != kb.dedupe_key(record)):
                        raise state.StateInconsistent("audited KB record is missing or rebound")
                appended = kb.append(kb_db, record)
                matches = [item for item in kb.records(kb_db) if item["id"] == appended.id]
                if len(matches) != 1 or matches[0]["dedupe_key"] != kb.dedupe_key(record):
                    raise state.StateInconsistent("published KB record could not be read back")
                stored = matches[0]
                if result is not None:
                    audit["qb_event_id"] = result["event_id"]
                    if stored["status"] == "NEW":
                        stored = kb.promote(kb_db, appended.id, "CI_VERIFIED")
                audit.update(
                    kb_id=stored["id"], dedupe_key=stored["dedupe_key"], status=stored["status"],
                )
                if all(old.get(name) == value for name, value in audit.items()):
                    event_id = previous["event_id"]
                else:
                    audit["at"] = datetime.now(timezone.utc).isoformat()
                    event_id = state._append_event_on_connection(conn, key, "KB_SYNC", audit)
                return dict(
                    kb_id=stored["id"], status=stored["status"], deduped=appended.deduped,
                    event_id=event_id, kb_precedent_ref=audit["kb_precedent_ref"],
                    source_kind=audit["source_kind"],
                )
        finally:
            conn.close()
