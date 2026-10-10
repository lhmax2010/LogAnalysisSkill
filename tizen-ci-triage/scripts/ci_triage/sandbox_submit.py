"""Locked, policy-checked sandbox publication of three verified copies."""

from __future__ import annotations

import fcntl
import hashlib
import json
import re
import shutil
import sqlite3
import subprocess
import sys
import unicodedata
from collections.abc import Iterator, Mapping
from contextlib import ExitStack, contextmanager
from dataclasses import asdict, dataclass, fields
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, cast

import yaml
from tizen_ci_shared.state import StateDatabase, VerificationRecord
from tizen_ci_shared.workspace import is_protected

from ci_triage import campaign_state as state
from ci_triage._campaign_workspace import _StepError, _unit_hash, _validate_source_identity
from ci_triage._sandbox_git import SandboxGit
from ci_triage.aggregate import _BINDING_FIELDS, AggregateResult, aggregate_verifications
from ci_triage.derive_commit import _identity, derive
from ci_triage.submission_identity import (
    ChangeIdHookError,
    compute_submission_key,
    generate_change_id_via_hook,
)
from ci_triage.suppress_policy import PolicyInputError, SourceKind, evaluate

ARCH_ORDER = ("aarch64", "armv7l", "x86_64")
SUBJECT_PREFIX = "Fix build error for clang compiler: "
_BRANCH = re.compile(r"sandbox/[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)*\Z")
_STATUSES = {
    "REPAIR_ROUND_RUNNING",
    "LOCAL_3ARCH_PASS",
    "SANDBOX_PUSHING",
    "SANDBOX_PUSH_FAILED",
    "SANDBOX_PUSHED",
}
_POLICY_FIELDS = ("verdict", "fix_strategy_final", "edit_source_kind")


class RefClass(Enum):
    SANDBOX = "sandbox"
    REVIEW = "review"
    FORBIDDEN = "forbidden"


@dataclass(frozen=True)
class SandboxSubmitOptions:
    verification_ids: str
    state_db: Path
    config: Path
    sandbox_branch: str
    message_brief: str | None = None
    edit_source_kind: str | None = None


@dataclass(frozen=True)
class SandboxSubmitOutcome:
    exit_code: int
    payload: Mapping[str, object]


@dataclass(frozen=True)
class _Config:
    workspace: Path
    remote_base: str
    author: str
    committer: str
    hook: Path
    hook_sha256: str
    git: SandboxGit


@dataclass(frozen=True)
class DeriveInputs:
    worktree: Path
    tree_sha: str
    parent_sha: str
    message: str
    author_identity: str
    committer_identity: str
    author_date: str
    committer_date: str

    def run(self) -> str:
        return derive(**asdict(self))


@dataclass(frozen=True)
class SubmitSnapshot:
    unit: state.Unit
    round_: state.Round
    links: tuple[dict[str, Any], ...]
    expected_status: str
    aggregate: AggregateResult
    policy: Mapping[str, object]
    derive_payload: Mapping[str, object]
    change_id: str
    submission_key: str
    derive_inputs: DeriveInputs
    derived: str
    remote: str
    git: SandboxGit
    edit_spec: dict[str, Any]


@dataclass(frozen=True)
class TocTouResult:
    ok: bool
    error_code: str | None = None
    held_reason: str | None = None
    held_arch: str | None = None
    detail: str | None = None


class _Reject(Exception):
    def __init__(
        self,
        code: str,
        detail: str,
        *,
        held: str | None = None,
        arch: str | None = None,
        exit_code: int = 4,
    ) -> None:
        super().__init__(detail)
        self.code, self.detail, self.held, self.arch, self.exit_code = (
            code,
            detail,
            held,
            arch,
            exit_code,
        )


def _held(reason: str, detail: str, arch: str | None = None) -> _Reject:
    codes = {
        "aggregate_mismatch": "REJECTED_ARCH_AGGREGATE_MISMATCH",
        "suppress_policy_recheck": "REJECTED_SUPPRESS_POLICY",
    }
    return _Reject(codes.get(reason, "REJECTED_" + reason.upper()), detail, held=reason, arch=arch)


def empty_payload() -> dict[str, Any]:
    return dict(
        action=None,
        status=None,
        aggregate=dict(ok=None, verified_tree_sha=None, base_commit=None, reasons=[]),
        policy_verdict=None,
        fix_strategy_final=None,
        change_id=None,
        derived_commit_sha=None,
        push=dict(ref=None, result=None, url=None),
        reused=dict(message_brief=None, edit_source_kind=None),
        held=dict(reason=None, arch_norm=None, scope=None),
        surviving_worktrees=[],
        error_code=None,
        reason=None,
    )


def invalid_outcome(reason: str) -> SandboxSubmitOutcome:
    payload = empty_payload()
    payload.update(action="invalid_args", error_code="INVALID_ARGS", reason=reason)
    return SandboxSubmitOutcome(2, payload)


def _config(path: Path) -> _Config:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        required = (
            "campaign_workspace",
            "gerrit_ssh_base",
            "git_author_identity",
            "git_committer_identity",
            "gerrit_commit_msg_hook",
            "gerrit_commit_msg_hook_sha256",
        )
        if not isinstance(data, dict) or any(
            not isinstance(data.get(key), str) or not data[key].strip() for key in required
        ):
            raise ValueError("missing or invalid sandbox config key")
        if not (
            data["gerrit_ssh_base"].startswith("ssh://")
            or Path(data["gerrit_ssh_base"]).is_absolute()
        ):
            raise ValueError("gerrit_ssh_base must be ssh:// or an absolute local path")
        _identity(data["git_author_identity"])
        _identity(data["git_committer_identity"])
        if re.fullmatch(r"[0-9a-f]{64}", data["gerrit_commit_msg_hook_sha256"]) is None:
            raise ValueError("invalid hook sha256")
        timeout = data.get("push_timeout_seconds", 300)
        ssh = data.get("git_ssh_command", "ssh")
        if type(timeout) is not int or timeout <= 0 or not isinstance(ssh, str) or not ssh:
            raise ValueError("invalid push_timeout_seconds or git_ssh_command")
        return _Config(
            Path(data["campaign_workspace"]),
            data["gerrit_ssh_base"],
            data["git_author_identity"],
            data["git_committer_identity"],
            Path(data["gerrit_commit_msg_hook"]),
            data["gerrit_commit_msg_hook_sha256"],
            SandboxGit(ssh, timeout),
        )
    except (OSError, yaml.YAMLError, ValueError) as exc:
        raise _Reject("INVALID_ARGS", str(exc), exit_code=2) from exc


def check_push_ref(ref: str) -> RefClass:
    return _classify_ref(ref, SandboxGit())


def _classify_ref(ref: str, git: SandboxGit) -> RefClass:
    if ref.startswith("refs/heads/") and _BRANCH.fullmatch(ref[len("refs/heads/") :]):
        if git.run(None, "check-ref-format", ref, check=False).returncode == 0:
            return RefClass.SANDBOX
    if ref.startswith("refs/for/") and "%" not in ref:
        branch = ref[len("refs/for/") :]
        if (
            branch
            and git.run(None, "check-ref-format", "--branch", branch, check=False).returncode == 0
        ):
            return RefClass.REVIEW
    return RefClass.FORBIDDEN


@contextmanager
def _locks(root: Path) -> Iterator[None]:
    with ExitStack() as stack:
        for path in (
            root / ".sandbox_submit.lock",
            *(root / arch / ".repair_step.lock" for arch in ARCH_ORDER),
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            stream = stack.enter_context(path.open("a+", encoding="utf-8"))
            try:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise _Reject("CAMPAIGN_STATE_BUSY", str(path)) from exc
        yield


def _links(conn: sqlite3.Connection, ids: tuple[str, ...]) -> tuple[dict[str, Any], ...]:
    result = []
    for verification_id in ids:
        rows = conn.execute(
            "SELECT * FROM campaign_verifications WHERE verification_id = ?",
            (verification_id,),
        ).fetchall()
        if len(rows) != 1:
            raise _Reject("REJECTED_ARCH_AGGREGATE_MISMATCH", "missing or ambiguous link")
        result.append(dict(rows[0]))
    if (
        len({row["campaign_unit_key"] for row in result}) != 1
        or len({row["round_index"] for row in result}) != 1
        or {row["arch_norm"] for row in result} != state.ARCH_NORMS
    ):
        raise _Reject("REJECTED_ARCH_AGGREGATE_MISMATCH", "links differ in unit, round or arches")
    return tuple(sorted(result, key=lambda row: ARCH_ORDER.index(row["arch_norm"])))


def _status(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute(
        "SELECT status FROM campaign_status_log WHERE campaign_unit_key = ? "
        "ORDER BY log_id DESC LIMIT 1",
        (key,),
    ).fetchone()
    return str(row["status"]) if row else None


def _round(conn: sqlite3.Connection, key: str) -> state.Round | None:
    row = conn.execute(
        "SELECT * FROM campaign_rounds WHERE campaign_unit_key = ? "
        "ORDER BY round_index DESC LIMIT 1",
        (key,),
    ).fetchone()
    return state._round_from_row(row) if row else None


def _safe(git: SandboxGit, path: Path) -> None:
    reason = git.unsafe_reason(path)
    if reason:
        raise _Reject("REJECTED_UNSAFE_GIT_CONFIG", reason)


def _source(git: SandboxGit, path: Path, unit: state.Unit) -> None:
    _safe(git, path)

    def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return git.run(Path(command[2]), *command[3:])

    try:
        _validate_source_identity(path, unit, subprocess_runner=runner)
        if not git.clean(path):
            raise _Reject("REJECTED_IDENTITY_MISMATCH", "src_clean is dirty")
    except (_StepError, OSError, subprocess.SubprocessError) as exc:
        raise _Reject("REJECTED_IDENTITY_MISMATCH", str(exc)) from exc


def _records(aggregate: AggregateResult) -> tuple[VerificationRecord, ...]:
    return tuple(
        sorted(aggregate.records, key=lambda r: ARCH_ORDER.index(state.ARCH_RAW_TO_NORM[r.arch]))
    )


def _copies(aggregate: AggregateResult, git: SandboxGit, *, full: bool) -> None:
    missing = [
        state.ARCH_RAW_TO_NORM[r.arch]
        for r in _records(aggregate)
        if not Path(r.worktree_path).is_dir()
    ]
    if missing:
        raise _Reject("REJECTED_WORKTREE_MISSING", ",".join(missing))
    failures: list[_Reject] = []
    for record in _records(aggregate):
        path, arch = Path(record.worktree_path), state.ARCH_RAW_TO_NORM[record.arch]
        if not is_protected(path):
            failures.append(_held("verification_mismatch", f"{arch}: unprotected", arch))
        elif full:
            _safe(git, path)
            try:
                if (
                    git.run(path, "rev-parse", "HEAD^{tree}").stdout.strip()
                    != aggregate.verified_tree_sha
                ):
                    failures.append(_held("verification_mismatch", f"{arch}: tree changed", arch))
                elif not git.clean(path):
                    failures.append(_held("worktree_dirty", f"{arch}: dirty", arch))
            except (OSError, subprocess.SubprocessError) as exc:
                failures.append(_held("verification_mismatch", f"{arch}: {exc}", arch))
    if failures:
        first = failures[0]
        raise _Reject(
            first.code, "; ".join(f.detail for f in failures), held=first.held, arch=first.arch
        )


def _remote_check(git: SandboxGit, path: Path, remote: str) -> None:
    try:
        _safe(git, path)
        if remote in git.run(path, "remote").stdout.splitlines():
            raise _Reject("REJECTED_REF_NOT_ALLOWED", "remote is a configured remote name")
        if (
            git.run(path, "ls-remote", "--get-url", remote, remote=True).stdout.rstrip("\n")
            != remote
        ):
            raise _Reject("REJECTED_REF_NOT_ALLOWED", "remote URL rewritten")
    except (_Reject, OSError, subprocess.SubprocessError) as exc:
        raise _Reject("REJECTED_REF_NOT_ALLOWED", str(exc)) from exc


def _bound_bytes(round_: state.Round, expected: tuple[str, ...]) -> dict[str, Any]:
    try:
        raw = Path(round_.edit_spec_ref).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if any(digest != value for value in expected):
            raise ValueError("edit_spec sha256 binding changed")
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError("edit_spec must be an object")
        return value
    except (OSError, ValueError) as exc:
        raise _held("edit_spec_rebind_mismatch", str(exc)) from exc


@dataclass(frozen=True)
class _SnapshotDatabase(StateDatabase):
    """Reuse the aggregate API without opening a second read snapshot."""

    connection: sqlite3.Connection

    def get_verification_record(self, verification_id: str) -> dict[str, str] | None:
        names = [f.name for f in fields(VerificationRecord)]
        row = self.connection.execute(
            "SELECT " + ", ".join(names) + " FROM verification_records WHERE verification_id = ?",
            (verification_id,),
        ).fetchone()
        return {name: str(row[name]) for name in names} if row else None


def _recheck_database(state_db: StateDatabase, snapshot: SubmitSnapshot) -> AggregateResult:
    s = snapshot
    conn = state._read_connection(state_db)
    try:
        conn.execute("BEGIN")
        try:
            links = _links(conn, tuple(str(row["verification_id"]) for row in s.links))
            unit = state._require_unit(conn, s.unit.campaign_unit_key)
            if (
                links != s.links
                or unit != s.unit
                or _round(conn, unit.campaign_unit_key) != s.round_
                or _status(conn, unit.campaign_unit_key) != s.expected_status
            ):
                raise _held("state_inconsistent", "selection snapshot changed")
        except (state.CampaignStateError, _Reject) as exc:
            raise _held("state_inconsistent", str(exc)) from exc
        aggregate = aggregate_verifications(
            tuple(str(row["verification_id"]) for row in s.links),
            _SnapshotDatabase(state_db.path, conn),
        )
        if not aggregate.ok or any(
            getattr(aggregate, name) != getattr(s.aggregate, name) for name in _BINDING_FIELDS
        ):
            raise _held(
                "aggregate_mismatch", "aggregate snapshot changed: " + "; ".join(aggregate.reasons)
            )
        by_id = {record.verification_id: record for record in aggregate.records}
        for old in _records(s.aggregate):
            new = by_id[old.verification_id]
            if (old.worktree_path, old.arch) != (new.worktree_path, new.arch):
                raise _held(
                    "verification_mismatch",
                    "record path/arch changed",
                    state.ARCH_RAW_TO_NORM[old.arch],
                )
        view = state._gate_view_on_connection(conn, unit.campaign_unit_key)
        policy = state._policy_on_connection(conn, unit.campaign_unit_key, s.round_.round_index)
        if (
            view.derive != s.derive_payload
            or policy is None
            or any(policy.get(k) != s.policy.get(k) for k in _POLICY_FIELDS)
            or state._cached_change_id(conn, s.submission_key) != s.change_id
        ):
            raise _held("state_inconsistent", "gate or Change-Id snapshot changed")
        return aggregate
    finally:
        conn.close()


def toctou_recheck(
    state_db: StateDatabase,
    snapshot: SubmitSnapshot,
    *,
    src_clean: Path,
) -> TocTouResult:
    s = snapshot
    try:
        aggregate = _recheck_database(state_db, s)
        _copies(aggregate, s.git, full=True)
        # Rehash the file, but retain the originally parsed bytes for policy evaluation.
        try:
            digest = hashlib.sha256(Path(s.round_.edit_spec_ref).read_bytes()).hexdigest()
            if digest != s.round_.edit_spec_sha256:
                raise _held("edit_spec_rebind_mismatch", "round file changed")
        except OSError as exc:
            raise _held("edit_spec_rebind_mismatch", str(exc)) from exc
        _source(s.git, src_clean, s.unit)
        try:
            verdict = evaluate(
                s.edit_spec, src_clean, cast(SourceKind, s.policy["edit_source_kind"])
            )
        except PolicyInputError as exc:
            raise _held("edit_spec_rebind_mismatch", str(exc)) from exc
        if (verdict.verdict, verdict.fix_strategy_final) != (
            s.policy["verdict"],
            s.policy["fix_strategy_final"],
        ):
            raise _held("state_inconsistent", "policy changed during submission")
        if s.derive_inputs.run() != s.derived:
            raise _held("state_inconsistent", "derive changed during submission")
        _remote_check(s.git, s.derive_inputs.worktree, s.remote)
        return TocTouResult(True)
    except _Reject as exc:
        return TocTouResult(False, exc.code, exc.held, exc.arch, exc.detail)
    except (
        state.StateInconsistent,
        ValueError,
        OSError,
        subprocess.SubprocessError,
    ) as exc:
        return TocTouResult(
            False, "REJECTED_STATE_INCONSISTENT", "state_inconsistent", None, str(exc)
        )


def sandbox_submit(options: SandboxSubmitOptions) -> SandboxSubmitOutcome:
    payload = empty_payload()
    unit: state.Unit | None = None
    aggregate: AggregateResult | None = None
    db = StateDatabase(options.state_db)
    locks = ExitStack()
    try:
        config = _config(options.config)
        ids = tuple(part.strip() for part in options.verification_ids.split(","))
        if len(ids) != 3 or len(set(ids)) != 3 or not all(ids):
            raise _Reject(
                "INVALID_ARGS", "exactly three distinct verification ids required", exit_code=2
            )
        if options.message_brief is not None and (
            not 1 <= len(options.message_brief.strip()) <= 100
            or any(unicodedata.category(c) == "Cc" for c in options.message_brief)
        ):
            raise _Reject("INVALID_ARGS", "invalid message brief", exit_code=2)
        if options.edit_source_kind not in {None, "generated", "suppress", "t1_cherry_pick"}:
            raise _Reject("INVALID_ARGS", "invalid edit source kind", exit_code=2)
        ref = "refs/heads/" + options.sandbox_branch
        if (
            not _BRANCH.fullmatch(options.sandbox_branch)
            or config.git.run(
                None,
                "check-ref-format",
                ref,
                check=False,
            ).returncode
        ):
            raise _Reject("INVALID_BRANCH_NAME", "invalid sandbox branch", exit_code=2)
        conn = state._read_connection(db)
        try:
            lock_unit = str(_links(conn, ids)[0]["campaign_unit_key"])
        finally:
            conn.close()
        locks.enter_context(_locks(config.workspace / _unit_hash(lock_unit)))
        conn = state._read_connection(db)
        try:
            conn.execute("BEGIN")
            links = _links(conn, ids)
            key = str(links[0]["campaign_unit_key"])
            if key != lock_unit:
                raise _Reject("CAMPAIGN_STATE_BUSY", "unit changed during locking")
            unit = state._require_unit(conn, key)
            round_ = _round(conn, key)
            if round_ is None or links[0]["round_index"] != round_.round_index:
                raise _Reject(
                    "REJECTED_ROUND_SUPERSEDED",
                    f"selected={links[0]['round_index']} latest={round_}",
                )
            status = _status(conn, key)
            payload["status"] = status
            if status not in _STATUSES:
                raise _Reject("REJECTED_STATE_INCONSISTENT", f"not executable: {status}")
            existing_derive = (
                conn.execute(
                    "SELECT 1 FROM campaign_gate_events WHERE campaign_unit_key=? "
                    "AND event_type='DERIVE' LIMIT 1",
                    (key,),
                ).fetchone()
                is not None
            )
            existing_policy = state._policy_on_connection(conn, key, round_.round_index)
            if (
                not existing_derive
                and options.message_brief is None
                or existing_policy is None
                and options.edit_source_kind is None
            ):
                raise _Reject(
                    "INVALID_ARGS", "first submission needs brief and edit source kind", exit_code=2
                )
        finally:
            conn.close()
        aggregate = aggregate_verifications(ids, db)
        payload["aggregate"] = {
            name: getattr(aggregate, name)
            for name in (
                "ok",
                "verified_tree_sha",
                "base_commit",
                "reasons",
            )
        }
        if not aggregate.ok or any(
            getattr(aggregate, k) != getattr(unit, k)
            for k in (
                "base_commit",
                "project",
                "spec_name",
                "branch",
            )
        ):
            raise _held(
                "aggregate_mismatch", "; ".join(aggregate.reasons) or "aggregate differs from unit"
            )
        _copies(aggregate, config.git, full=False)
        if status == "REPAIR_ROUND_RUNNING":
            state.append_status(db, key, "LOCAL_3ARCH_PASS")
            status = "LOCAL_3ARCH_PASS"
        payload["status"] = status
        edit_spec = _bound_bytes(
            round_,
            (
                round_.edit_spec_sha256,
                str(aggregate.edit_spec_sha256),
                *(str(row["edit_spec_sha256"]) for row in links),
            ),
        )
        src_clean = config.workspace / _unit_hash(key) / "src"
        _source(config.git, src_clean, unit)
        kind = cast(
            SourceKind,
            existing_policy["edit_source_kind"] if existing_policy else options.edit_source_kind,
        )
        payload["reused"] = dict(
            message_brief=existing_derive, edit_source_kind=existing_policy is not None
        )
        try:
            verdict = evaluate(edit_spec, src_clean, kind)
        except PolicyInputError as exc:
            raise _held("edit_spec_rebind_mismatch", str(exc)) from exc
        policy = dict(
            round_index=round_.round_index,
            verdict=verdict.verdict,
            hits=[asdict(hit) for hit in verdict.hits],
            fix_strategy_initial={
                "generated": "code",
                "suppress": "suppress",
                "t1_cherry_pick": "cherry_pick",
            }[kind],
            fix_strategy_final=verdict.fix_strategy_final,
            edit_source_kind=kind,
            rules_version=verdict.rules_version,
        )
        payload.update(
            policy_verdict=verdict.verdict, fix_strategy_final=verdict.fix_strategy_final
        )
        if existing_policy is None:
            state.append_event(db, key, "POLICY", policy)
        elif any(policy[k] != existing_policy.get(k) for k in _POLICY_FIELDS):
            raise _held(
                "state_inconsistent",
                f"policy rules_version: stored={existing_policy.get('rules_version')} "
                f"current={verdict.rules_version}",
            )
        if verdict.verdict == "forbidden":
            raise _held("suppress_policy_recheck", "suppression forbidden")
        _copies(aggregate, config.git, full=True)
        try:
            view = state.gate_view(db, key)
        except state.StateInconsistent as exc:
            raise _held("state_inconsistent", str(exc)) from exc
        stored = view.derive
        if stored and stored["verified_tree_sha"] != aggregate.verified_tree_sha:
            raise _held("state_inconsistent", "DERIVE tree differs")
        date = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        identity = (
            {
                "message_brief": options.message_brief.strip() if options.message_brief else "",
                "author_identity": config.author,
                "committer_identity": config.committer,
                "author_date": date,
                "committer_date": date,
            }
            if stored is None
            else dict(stored)
        )
        subject = SUBJECT_PREFIX + str(identity["message_brief"])
        submission_key = compute_submission_key(
            unit.submission_identity_key, str(aggregate.verified_tree_sha)
        )

        def generate() -> str:
            return generate_change_id_via_hook(
                hook_path=config.hook,
                hook_sha256=config.hook_sha256,
                submission_key=submission_key,
                message=subject + "\n",
            )

        try:
            change_id = state.get_or_create_change_id(
                db,
                campaign_unit_key=key,
                submission_key=submission_key,
                hook_sha256=config.hook_sha256,
                generate=generate if stored is None else None,
            )
        except ChangeIdHookError as exc:
            raise _Reject("CHANGE_ID_HOOK_FAILED", str(exc)) from exc
        except state.StateInconsistent as exc:
            raise _held("state_inconsistent", str(exc)) from exc
        main = Path(next(r.worktree_path for r in aggregate.records if r.arch == unit.primary_arch))
        inputs = DeriveInputs(
            main,
            str(aggregate.verified_tree_sha),
            str(aggregate.base_commit),
            f"{subject}\n\nChange-Id: {change_id}\n",
            *(
                str(identity[k])
                for k in (
                    "author_identity",
                    "committer_identity",
                    "author_date",
                    "committer_date",
                )
            ),
        )
        try:
            derived = inputs.run()
        except (ValueError, subprocess.CalledProcessError) as exc:
            raise _held("state_inconsistent", str(exc)) from exc
        derive_payload = dict(
            identity, derived_commit_sha=derived, verified_tree_sha=aggregate.verified_tree_sha
        )
        if stored is None:
            state.append_event(db, key, "DERIVE", derive_payload)
        elif derived != stored["derived_commit_sha"]:
            raise _held("state_inconsistent", "recomputed DERIVE sha differs")
        payload.update(change_id=change_id, derived_commit_sha=derived)
        remote = config.remote_base.rstrip("/") + "/" + unit.project
        payload["push"].update(ref=ref, url=remote)
        if _classify_ref(ref, config.git) != RefClass.SANDBOX:
            raise _Reject("REJECTED_REF_NOT_ALLOWED", "not a sandbox ref")
        _remote_check(config.git, main, remote)
        snapshot = SubmitSnapshot(
            unit,
            round_,
            links,
            str(status),
            aggregate,
            policy,
            derive_payload,
            change_id,
            submission_key,
            inputs,
            derived,
            remote,
            config.git,
            edit_spec,
        )
        checked = toctou_recheck(db, snapshot, src_clean=src_clean)
        if not checked.ok:
            raise _Reject(
                str(checked.error_code),
                str(checked.detail),
                held=checked.held_reason,
                arch=checked.held_arch,
            )
        _publish(db, snapshot, ref, payload, config.workspace / _unit_hash(unit.campaign_unit_key))
        return SandboxSubmitOutcome(5 if payload["action"] == "push_failed" else 0, payload)
    except _Reject as exc:
        payload.update(error_code=exc.code, reason=exc.detail)
        if exc.held and unit:
            arch = exc.arch
            if arch is None and exc.held in state._ARCH_SCOPED_HELD_REASONS:
                arch = state.ARCH_RAW_TO_NORM[unit.primary_arch or ""]
            if state.latest_status(db, unit.campaign_unit_key) != state.HELD_FOR_INVESTIGATION:
                state.append_status(
                    db, unit.campaign_unit_key, state.HELD_FOR_INVESTIGATION, exc.held, arch
                )
            payload.update(
                action="held",
                status=state.HELD_FOR_INVESTIGATION,
                held=dict(reason=exc.held, arch_norm=arch, scope="copy" if exc.arch else "unit"),
            )
        elif exc.code == "REJECTED_WORKTREE_MISSING" and unit and aggregate:
            state.append_status(db, unit.campaign_unit_key, "WORKTREE_LOST", exc.detail)
            payload.update(
                action="worktree_lost",
                status="WORKTREE_LOST",
                surviving_worktrees=[
                    r.worktree_path for r in _records(aggregate) if Path(r.worktree_path).is_dir()
                ],
            )
        else:
            payload["action"] = (
                "invalid_args"
                if exc.exit_code == 2
                else ("busy" if exc.code == "CAMPAIGN_STATE_BUSY" else "rejected")
            )
        return SandboxSubmitOutcome(exc.exit_code, payload)
    finally:
        locks.close()


class _TransportFailure(RuntimeError):
    """A transport operation failed, as distinct from a bookkeeping failure."""


@contextmanager
def _transport_errors() -> Iterator[None]:
    try:
        yield
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        raise _TransportFailure(str(exc)) from exc


def _remote_sha(git: SandboxGit, path: Path, remote: str, ref: str) -> str | None:
    with _transport_errors():
        result = git.run(
            None,
            "ls-remote",
            "--exit-code",
            remote,
            ref,
            check=False,
            remote=True,
            git_dir=path,
        )
        if result.returncode == 2:
            return None
        result.check_returncode()
        rows = [line.split("\t") for line in result.stdout.splitlines()]
        if len(rows) != 1 or len(rows[0]) != 2 or rows[0][1] != ref:
            raise ValueError("unexpected ls-remote response")
        return rows[0][0]


def _push_event(db: StateDatabase, s: SubmitSnapshot, ref: str, result: str) -> None:
    state.append_event(
        db,
        s.unit.campaign_unit_key,
        "PUSH",
        dict(
            ref=ref,
            ref_class="sandbox",
            pushed_sha=s.derived,
            result=result,
            url=None,
            at=datetime.now(timezone.utc).isoformat(),
        ),
    )


@contextmanager
def _transport(s: SubmitSnapshot, unit_root: Path) -> Iterator[Path]:
    path = unit_root / ".transport"
    try:
        with _transport_errors():
            if path.is_symlink() or path.is_file():
                path.unlink()
            elif path.exists():
                shutil.rmtree(path)
            source = s.derive_inputs.worktree
            object_format = s.git.run(source, "rev-parse", "--show-object-format").stdout.strip()
            s.git.run(None, "init", "--bare", f"--object-format={object_format}", str(path))
            objects = Path(s.git.run(source, "rev-parse", "--git-path", "objects").stdout.strip())
            objects = (source / objects).resolve()
            (path / "objects/info/alternates").write_text(str(objects) + "\n", encoding="utf-8")
        yield path
    finally:
        try:
            if path.exists():
                shutil.rmtree(path)
        except OSError as exc:
            print(f"warning: transport cleanup failed: {exc}", file=sys.stderr)


def _publish(
    db: StateDatabase,
    s: SubmitSnapshot,
    ref: str,
    payload: dict[str, Any],
    unit_root: Path,
) -> None:
    try:
        with _transport(s, unit_root) as transport:
            _publish_in_transport(db, s, ref, payload, transport)
    except _TransportFailure as exc:
        _push_event(db, s, ref, "failed")
        state.append_status(db, s.unit.campaign_unit_key, "SANDBOX_PUSH_FAILED")
        payload.update(
            action="push_failed",
            status="SANDBOX_PUSH_FAILED",
            error_code="PUSH_FAILED",
            reason=str(exc),
        )
        payload["push"]["result"] = "failed"


def _publish_in_transport(
    db: StateDatabase,
    s: SubmitSnapshot,
    ref: str,
    payload: dict[str, Any],
    transport: Path,
) -> None:
    key, path = s.unit.campaign_unit_key, s.derive_inputs.worktree
    remote_sha = _remote_sha(s.git, transport, s.remote, ref)
    if remote_sha == s.derived:
        view = state.gate_view(db, key)
        status = state.latest_status(db, key)
        recorded = view.sandbox_push is not None and all(
            view.sandbox_push.get(k) == v
            for k, v in (
                ("ref", ref),
                ("pushed_sha", s.derived),
                ("result", "ok"),
            )
        )
        payload["action"] = (
            "already_pushed" if recorded and status == "SANDBOX_PUSHED" else "pushed"
        )
        if not recorded:
            _push_event(db, s, ref, "ok")
        if status != "SANDBOX_PUSHED":
            state.append_status(db, key, "SANDBOX_PUSHED")
    else:
        if state.latest_status(db, key) != "SANDBOX_PUSHING":
            state.append_status(db, key, "SANDBOX_PUSHING")
        payload["status"] = "SANDBOX_PUSHING"
        _safe(s.git, path)
        with _transport_errors():
            s.git.run(None, "cat-file", "-e", s.derived + "^{commit}", git_dir=transport)
            s.git.run(
                None,
                "push",
                "--porcelain",
                "--no-verify",
                "--no-follow-tags",
                "--recurse-submodules=no",
                s.remote,
                f"+{s.derived}:{ref}",
                remote=True,
                git_dir=transport,
            )
            if _remote_sha(s.git, transport, s.remote, ref) != s.derived:
                raise ValueError("pushed remote sha differs")
        _push_event(db, s, ref, "ok")
        state.append_status(db, key, "SANDBOX_PUSHED")
        payload["action"] = "pushed"
    payload.update(status="SANDBOX_PUSHED")
    payload["push"]["result"] = "ok"
