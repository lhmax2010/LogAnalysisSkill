"""Locked, first-party-evidence-only Gerrit review publication."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from contextlib import ExitStack
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO, cast

from tizen_campaign_core import campaign_state as state
from tizen_campaign_core._campaign_io import JsonParser
from tizen_campaign_core._campaign_workspace import _unit_hash
from tizen_campaign_core.aggregate import aggregate_verifications
from tizen_campaign_core.campaign_lifecycle import is_abandoned
from tizen_campaign_core.submission_identity import compute_submission_key
from tizen_campaign_core.suppress_policy import PolicyInputError, SourceKind, evaluate
from tizen_ci_shared.state import StateDatabase
from tizen_sandbox_submit import sandbox_submit as sandbox

RESULT_KEYS = frozenset(
    "qb_build_id child_build_id status sbs_target_echo per_arch_status accepted "
    "configuration_path child_configuration_path parent_status_text child_status_text "
    "child_build_result_text child_failed_step child_error_message request_marker_echo "
    "params_echo child_params_echo snapshot_used snapshot_drift_accepted pkg_list_echo "
    "evidence fetched_at".split()
)


@dataclass(frozen=True)
class ReviewOptions:
    verification_ids: str
    state_db: Path
    config: Path
    qb_result: Path
    review_target: str


@dataclass(frozen=True)
class QbGateResult:
    ok: bool
    source: str
    degraded: bool
    matched_event_id: int | None
    reasons: tuple[str, ...]


def pending_message(request_id: str) -> str:
    return (
        f"该 unit 最新的验证请求(request_id={request_id})还没有结果。"
        "若 qb-result-fetch 曾报告结果无法识别(QB_RESULT_UNRECOGNIZED,例如各架构状态非空或快照漂移;"
        "可在运行 qb-result-fetch 时所用的 state_root 下查看该 request 的 trace 确认),"
        "重读不会改变结果,请按其输出的指引处置,或用 campaign-release-worktrees --abandon "
        "放弃该 unit;否则稍后重跑 qb-result-fetch。"
    )


def _schema(result: Any) -> bool:
    if not isinstance(result, dict) or set(result) != RESULT_KEYS:
        return False
    optional = {"per_arch_status", "accepted", "child_failed_step", "child_error_message"}
    structures = {
        "params_echo",
        "child_params_echo",
        "pkg_list_echo",
        "evidence",
        "snapshot_drift_accepted",
    }
    if any(not isinstance(result[key], str) for key in RESULT_KEYS - optional - structures):
        return False
    for key, keys in (
        (
            "params_echo",
            {"BUILD_TYPE", "BUILD_REFERENCE", "SNAPSHOT_NUM", "PROJECT_BRANCH", "FAIL_FAST"},
        ),
        ("child_params_echo", {"BUILD_REFERENCE", "SNAPSHOT_NUM_URL"}),
        ("pkg_list_echo", None),
    ):
        value = result[key]
        if not isinstance(value, dict) or (keys is not None and set(value) != keys):
            return False
        if any(not isinstance(k, str) or not isinstance(v, str) for k, v in value.items()):
            return False
    return (
        type(result["accepted"]) in {bool, type(None)}
        and type(result["snapshot_drift_accepted"]) is bool
        and isinstance(result["evidence"], list)
        and all(isinstance(p, str) for p in result["evidence"])
        and all(
            result[k] is None or isinstance(result[k], str)
            for k in ("child_failed_step", "child_error_message")
        )
        and (result["per_arch_status"] is None or isinstance(result["per_arch_status"], dict))
    )


def _qb_gate(
    db: StateDatabase, unit: state.Unit, path: Path, derived: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    conn = state._read_connection(db)
    try:
        conn.execute("BEGIN")
        request = conn.execute(
            "SELECT * FROM campaign_qb_requests WHERE campaign_unit_key=? "
            "ORDER BY request_seq DESC LIMIT 1",
            (unit.campaign_unit_key,),
        ).fetchone()
        if request is None:
            raise sandbox._Reject("REJECTED_QB_NOT_VERIFIED", "no verification request")
        row = conn.execute(
            "SELECT * FROM campaign_qb_events WHERE request_seq=? AND event_type='RESULT' "
            "ORDER BY event_id DESC LIMIT 1",
            (request["request_seq"],),
        ).fetchone()
        if row is None:
            raise sandbox._Reject(
                "REJECTED_QB_REQUEST_PENDING", pending_message(request["request_id"])
            )
        event = dict(row)
        try:
            raw = path.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            if digest != event["qb_result_sha256"]:
                old = conn.execute(
                    "SELECT 1 FROM campaign_qb_events e JOIN campaign_qb_requests r "
                    "ON r.request_seq=e.request_seq WHERE r.campaign_unit_key=? "
                    "AND e.event_type='RESULT' AND e.qb_result_sha256=? AND e.event_id<>?",
                    (unit.campaign_unit_key, digest, event["event_id"]),
                ).fetchone()
                if old:
                    raise sandbox._Reject("REJECTED_QB_SUPERSEDED", "result is superseded")
                raise ValueError("result bytes changed")
            result = json.loads(raw)
            if not _schema(result):
                raise ValueError("result schema differs")
            target = unit.project + "@" + derived
            if request["sbs_target"] != target or event["sbs_target_echo"] != target:
                raise ValueError("target differs")
            if any(
                result[k] != event[k]
                for k in ("qb_build_id", "status", "accepted", "sbs_target_echo")
            ):
                raise ValueError("event and file differ")
            if (
                result["request_marker_echo"]
                != "clang-fix-campaign request=" + request["request_id"]
            ):
                raise ValueError("request marker differs")
            per_arch = (
                json.loads(event["per_arch_status_json"])
                if event["per_arch_status_json"] is not None
                else None
            )
            if result["per_arch_status"] != per_arch:
                raise ValueError("architecture statuses differ")
            profile = conn.execute(
                "SELECT * FROM campaign_qb_profiles WHERE branch=?", (unit.branch,)
            ).fetchone()
            if (
                profile is None
                or hashlib.sha256(profile["profile_json"].encode()).hexdigest()
                != profile["profile_sha256"]
            ):
                raise sandbox._held("state_inconsistent", "frozen profile missing or changed")
            require_accept = json.loads(profile["profile_json"])["qb_pass_requires_accept"]
            if type(require_accept) is not bool:
                raise ValueError("invalid acceptance policy")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise sandbox._Reject("REJECTED_QB_BINDING_MISMATCH", type(exc).__name__) from exc
        if (
            event["status"] != "PASS"
            or (require_accept and event["accepted"] != 1)
            or (
                per_arch is not None
                and (
                    not isinstance(per_arch, dict)
                    or set(per_arch) != state.ARCH_NORMS
                    or any(v != "PASS" for v in per_arch.values())
                )
            )
        ):
            raise sandbox._Reject("REJECTED_QB_NOT_VERIFIED", "QuickBuild pass gate failed")
        return event, result
    finally:
        conn.close()


def validate_qb_gate(
    state_db: StateDatabase,
    campaign_unit_key: str,
    qb_result_path: Path,
    *,
    allow_manual: bool = False,
) -> QbGateResult:
    """The legacy allow_manual flag never authorizes fallback in this workflow."""
    try:
        unit = state.get_unit(state_db, campaign_unit_key)
        derive = state.gate_view(state_db, campaign_unit_key).derive
        if unit is None or derive is None:
            raise sandbox._held("state_inconsistent", "unit or DERIVE missing")
        event, _ = _qb_gate(state_db, unit, qb_result_path, str(derive["derived_commit_sha"]))
        return QbGateResult(True, "first_party", False, event["event_id"], ())
    except sandbox._Reject as exc:
        return QbGateResult(False, "first_party", False, None, (exc.code, exc.detail))


def _trace(root: Path, stage: str, **facts: object) -> None:
    with (root / "review-trace.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(
            json.dumps(dict(stage=stage, **facts), ensure_ascii=False, sort_keys=True) + "\n"
        )


def run(options: ReviewOptions) -> sandbox.SandboxSubmitOutcome:
    db = StateDatabase(options.state_db)
    payload: dict[str, Any] = dict(
        action=None,
        status=None,
        error_code=None,
        message=None,
        review_url=None,
        qb_event_id=None,
        change_id=None,
        derived_commit_sha=None,
        snapshot_used=None,
        snapshot_drift_accepted=None,
    )
    unit = None
    root = None
    locks = ExitStack()
    try:
        config = sandbox._config(options.config)
        ids = tuple(p.strip() for p in options.verification_ids.split(","))
        if len(ids) != 3 or len(set(ids)) != 3 or not all(ids):
            raise sandbox._Reject(
                "INVALID_ARGS", "three distinct verification ids required", exit_code=2
            )
        conn = state._read_connection(db)
        try:
            key = str(sandbox._links(conn, ids)[0]["campaign_unit_key"])
        finally:
            conn.close()
        root = config.workspace / _unit_hash(key)
        locks.enter_context(sandbox._locks(root))
        _trace(root, "locked")
        if is_abandoned(db, key):
            raise sandbox._Reject("REJECTED_UNIT_ABANDONED", "unit abandoned")
        conn = state._read_connection(db)
        try:
            conn.execute("BEGIN")
            links = sandbox._links(conn, ids)
            if links[0]["campaign_unit_key"] != key:
                raise sandbox._held("state_inconsistent", "unit changed while locking")
            unit = state._require_unit(conn, key)
            round_ = sandbox._round(conn, key)
            if round_ is None or links[0]["round_index"] != round_.round_index:
                raise sandbox._Reject("REJECTED_ROUND_SUPERSEDED", "not final round")
            status = sandbox._status(conn, key)
        finally:
            conn.close()
        if options.review_target != "refs/for/" + unit.branch:
            raise sandbox._Reject("REJECTED_REVIEW_TARGET_MISMATCH", "review branch differs")
        if sandbox.check_push_ref(options.review_target) != sandbox.RefClass.REVIEW:
            raise sandbox._Reject("REJECTED_REF_NOT_ALLOWED", "not a review ref")
        aggregate = aggregate_verifications(ids, db)
        if not aggregate.ok or any(
            getattr(aggregate, k) != getattr(unit, k)
            for k in ("base_commit", "project", "branch", "spec_name")
        ):
            raise sandbox._held("aggregate_mismatch", "; ".join(aggregate.reasons))
        _trace(root, "aggregate_verified")
        view = state.gate_view(db, key)
        stored = view.derive
        if stored is None:
            raise sandbox._held("state_inconsistent", "missing DERIVE")
        derived = str(stored["derived_commit_sha"])
        qb, result = _qb_gate(db, unit, options.qb_result, derived)
        payload.update(
            qb_event_id=qb["event_id"],
            snapshot_used=result["snapshot_used"],
            snapshot_drift_accepted=result["snapshot_drift_accepted"],
        )
        _trace(root, "qb_verified", event_id=qb["event_id"])
        edit = sandbox._bound_bytes(
            round_,
            (
                round_.edit_spec_sha256,
                str(aggregate.edit_spec_sha256),
                *(r.edit_spec_sha256 for r in aggregate.records),
            ),
        )
        _trace(root, "edit_spec_verified")
        policy = state.latest_policy_for_round(db, key, round_.round_index)
        if policy is None or policy.get("edit_source_kind") not in {"generated", "suppress"}:
            raise sandbox._held("state_inconsistent", "missing or unsupported source kind")
        src = root / "src"
        sandbox._source(config.git, src, unit)
        try:
            verdict = evaluate(edit, src, cast(SourceKind, policy["edit_source_kind"]))
        except PolicyInputError as exc:
            raise sandbox._held("edit_spec_rebind_mismatch", type(exc).__name__) from exc
        if (verdict.verdict, verdict.fix_strategy_final) != (
            policy["verdict"],
            policy["fix_strategy_final"],
        ):
            raise sandbox._held("state_inconsistent", "stored and recomputed policy differ")
        if verdict.verdict == "forbidden":
            raise sandbox._held("suppress_policy_recheck", "forbidden suppression")
        _trace(root, "policy_verified")
        if verdict.fix_strategy_final != "code" or not view.reproduced:
            state.append_status(db, key, "REVIEW_INELIGIBLE", "review_gate")
            raise sandbox._Reject("REJECTED_REVIEW_GATE", "A2 quality gate failed")
        if status not in {
            "SANDBOX_QB_PASS",
            "REVIEW_PUSHING",
            "REVIEW_PUSH_FAILED",
            "REVIEW_PUSHED",
        }:
            raise sandbox._held("state_inconsistent", "review status is not eligible")
        _trace(root, "quality_gate_verified")
        submission_key = compute_submission_key(
            unit.submission_identity_key, str(aggregate.verified_tree_sha)
        )
        change_id = state.lookup_change_id(db, submission_key)
        if change_id is None:
            raise sandbox._held("state_inconsistent", "cached Change-Id missing")
        main = Path(next(r.worktree_path for r in aggregate.records if r.arch == unit.primary_arch))
        inputs = sandbox.DeriveInputs(
            main,
            str(aggregate.verified_tree_sha),
            str(aggregate.base_commit),
            f"{sandbox.SUBJECT_PREFIX}{stored['message_brief']}\n\nChange-Id: {change_id}\n",
            *(
                str(stored[k])
                for k in ("author_identity", "committer_identity", "author_date", "committer_date")
            ),
        )
        snapshot = sandbox.SubmitSnapshot(
            unit,
            round_,
            links,
            str(status),
            aggregate,
            policy,
            stored,
            change_id,
            submission_key,
            inputs,
            derived,
            config.remote_base.rstrip("/") + "/" + unit.project,
            config.git,
            edit,
        )
        checked = sandbox.toctou_recheck(db, snapshot, src_clean=src)
        if not checked.ok:
            raise sandbox._Reject(
                str(checked.error_code),
                str(checked.detail),
                held=checked.held_reason,
                arch=checked.held_arch,
            )
        again, _ = _qb_gate(db, unit, options.qb_result, derived)
        if again != qb:
            raise sandbox._Reject("REJECTED_QB_SUPERSEDED", "result changed during review")
        _trace(root, "toctou_verified")
        payload.update(change_id=change_id, derived_commit_sha=derived)
        _push(db, snapshot, options.review_target, qb["event_id"], payload, root)
        return sandbox.SandboxSubmitOutcome(0, payload)
    except sandbox._Reject as exc:
        payload.update(action="rejected", error_code=exc.code, message=exc.detail)
        if root is not None and root.exists():
            _trace(root, "rejected", error_code=exc.code)
        if unit is not None:
            if exc.held:
                arch = exc.arch or (
                    state.ARCH_RAW_TO_NORM[unit.primary_arch or ""]
                    if exc.held in state._ARCH_SCOPED_HELD_REASONS
                    else None
                )
                state.append_status(
                    db, unit.campaign_unit_key, state.HELD_FOR_INVESTIGATION, exc.held, arch
                )
            elif exc.code == "REJECTED_WORKTREE_MISSING":
                state.append_status(db, unit.campaign_unit_key, "WORKTREE_LOST", exc.detail)
            payload["status"] = state.latest_status(db, unit.campaign_unit_key)
        return sandbox.SandboxSubmitOutcome(exc.exit_code, payload)
    finally:
        locks.close()


def _push(
    db: StateDatabase,
    snapshot: sandbox.SubmitSnapshot,
    ref: str,
    event_id: int,
    payload: dict[str, Any],
    root: Path,
) -> None:
    key = snapshot.unit.campaign_unit_key
    view = state.gate_view(db, key)
    if (
        view.review_push
        and all(
            view.review_push.get(k) == v
            for k, v in (("ref", ref), ("pushed_sha", snapshot.derived), ("result", "ok"))
        )
        and view.review
        and view.review.get("outcome") == "pushed"
    ):
        if state.latest_status(db, key) != "REVIEW_PUSHED":
            state.append_status(db, key, "REVIEW_PUSHED")
        payload.update(
            action="already_pushed",
            status="REVIEW_PUSHED",
            review_url=view.review.get("review_url"),
        )
        _trace(root, "already_pushed")
        return
    state.append_status(db, key, "REVIEW_PUSHING")
    try:
        with sandbox._transport(snapshot, root) as transport:
            with sandbox._transport_errors():
                snapshot.git.run(
                    None, "cat-file", "-e", snapshot.derived + "^{commit}", git_dir=transport
                )
                completed = snapshot.git.run(
                    None,
                    "push",
                    "--porcelain",
                    "--no-verify",
                    "--no-follow-tags",
                    "--recurse-submodules=no",
                    snapshot.remote,
                    snapshot.derived + ":" + ref,
                    remote=True,
                    git_dir=transport,
                )
    except sandbox._TransportFailure as exc:
        state.append_status(db, key, "REVIEW_PUSH_FAILED")
        _trace(root, "push_failed")
        raise sandbox._Reject("PUSH_FAILED", type(exc).__name__, exit_code=5) from exc
    urls = re.findall(r"https?://[^\s<>]+", completed.stdout + "\n" + completed.stderr)
    url = urls[0] if urls else None
    _trace(
        root,
        "push_completed",
        review_url_found=bool(url),
        reason=None if url else "no_change_url_in_push_output",
    )
    now = datetime.now(timezone.utc).isoformat()
    state.append_event(
        db,
        key,
        "PUSH",
        dict(
            ref=ref, ref_class="review", pushed_sha=snapshot.derived, result="ok", url=url, at=now
        ),
    )
    state.append_event(
        db,
        key,
        "REVIEW",
        dict(outcome="pushed", review_url=url, degraded=False, qb_event_id=event_id, at=now),
    )
    state.append_status(db, key, "REVIEW_PUSHED")
    payload.update(action="pushed", status="REVIEW_PUSHED", review_url=url)


def main(argv: list[str], *, stdout: TextIO) -> int:
    try:
        parser = JsonParser(prog="review-submit")
        for name in ("verification-ids", "review-target"):
            parser.add_argument("--" + name, required=True)
        for name in ("state-db", "config", "qb-result"):
            parser.add_argument("--" + name, type=Path, required=True)
        result = run(ReviewOptions(**vars(parser.parse_args(argv))))
    except ValueError as exc:
        result = sandbox.SandboxSubmitOutcome(2, dict(error_code="INVALID_ARGS", message=str(exc)))
    except state.CampaignStateBusy:
        result = sandbox.SandboxSubmitOutcome(4, dict(error_code="CAMPAIGN_STATE_BUSY"))
    except (state.CampaignStateError, OSError, subprocess.SubprocessError) as exc:
        result = sandbox.SandboxSubmitOutcome(
            5, dict(error_code="INTERNAL_ERROR", message=type(exc).__name__)
        )
    print(json.dumps(dict(result.payload), ensure_ascii=False, sort_keys=True), file=stdout)
    return result.exit_code
