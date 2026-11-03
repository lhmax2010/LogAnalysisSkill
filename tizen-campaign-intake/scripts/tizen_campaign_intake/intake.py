"""Manual campaign intake with immutable evidence and staged source publication."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, TextIO

from tizen_campaign_core import campaign_state as state
from tizen_campaign_core._campaign_io import (
    JsonParser,
    analyze,
    config,
    fsync_parent,
    lock,
    publish,
    sha256,
)
from tizen_campaign_core._campaign_workspace import (
    _normalize_project,
    _StepError,
    _unit_hash,
    _validate_source_identity,
)
from tizen_campaign_core._sandbox_git import SandboxGit
from tizen_campaign_core.submission_identity import (
    build_campaign_unit_key,
    build_submission_identity_key,
)
from tizen_ci_shared.state import StateDatabase

INTAKE_ANALYZER_FAILED = "INTAKE_ANALYZER_FAILED"
INTAKE_CLONE_FAILED = "INTAKE_CLONE_FAILED"


def _identity_runner(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    return SandboxGit().run(Path(argv[2]), *argv[3:])


def _prepare_source(root: Path, unit: state.Unit, remote: str) -> Path:
    for leftover in root.glob(".src.staging-*"):
        if leftover.is_symlink() or not leftover.is_dir():
            leftover.unlink()
        else:
            shutil.rmtree(leftover)
    canonical = root / "src"
    if canonical.exists():
        _validate_source_identity(canonical, unit, subprocess_runner=_identity_runner)
        return canonical
    temporary = Path(tempfile.mkdtemp(dir=root, prefix=".src.staging-"))
    git = SandboxGit()
    try:
        git.run(None, "clone", remote, str(temporary), remote=True)
        git.run(temporary, "checkout", "--detach", unit.base_commit)
        head = git.run(temporary, "rev-parse", "HEAD").stdout.strip()
        origin = git.run(temporary, "remote", "get-url", "origin").stdout.strip()
        if head != unit.base_commit or _normalize_project(origin) != unit.project:
            raise _StepError(
                "REJECTED_IDENTITY_MISMATCH",
                "source HEAD or origin does not match campaign unit",
                4,
            )
        marker = {
            "unit_key": unit.campaign_unit_key,
            "project": unit.project,
            "base_commit": unit.base_commit,
        }
        with (temporary / ".campaign_clone").open("w", encoding="utf-8") as stream:
            json.dump(marker, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        fsync_parent(temporary / ".campaign_clone")
        if canonical.exists():
            raise _StepError("INTAKE_CLONE_FAILED", "source appeared before publish", 5)
        os.rename(temporary, canonical)
        fsync_parent(canonical)
        return canonical
    except _StepError:
        raise
    except (OSError, subprocess.SubprocessError) as exc:
        raise _StepError(INTAKE_CLONE_FAILED, type(exc).__name__, 5) from exc
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def add_unit(args: Any) -> dict[str, Any]:
    settings = config(args.config)
    identity = dict(
        ci_system="quickbuild",
        source_build_id=args.source_build_id,
        project=args.project,
        branch=args.branch,
        spec_name=args.spec_name,
        base_commit=args.base_commit,
    )
    key = build_campaign_unit_key(**identity)
    submission = build_submission_identity_key(
        **{k: v for k, v in identity.items() if k != "source_build_id"}
    )
    arches = state._canonical_failed_arches(args.failed_arches.split(","))
    if not arches:
        raise ValueError("failed arches must not be empty")
    for name in ("max_rounds", "max_build_invocations"):
        if type(settings.get(name)) is not int or settings[name] < 1:
            raise ValueError(name + " must be positive")
    remote = settings.get("gerrit_ssh_base")
    if not isinstance(remote, str) or not (
        remote.startswith("ssh://") or Path(remote).is_absolute()
    ):
        raise ValueError("invalid gerrit_ssh_base")
    root = Path(settings["campaign_workspace"]).resolve() / _unit_hash(key)
    db = StateDatabase(args.state_db)
    common = dict(
        campaign_unit_key=key,
        submission_identity_key=submission,
        failed_arches=arches,
        max_rounds=settings["max_rounds"],
        max_build_invocations=settings["max_build_invocations"],
        **identity,
    )
    with lock(root / ".intake.lock"):
        if any(arch not in state.ARCH_RAW_TO_NORM for arch in arches):
            state.create_arch_rejected_unit(
                db, reason="arch_not_allowed", toolchain_profile=args.toolchain_profile, **common
            )
            raise _StepError("REJECTED_ARCH_NOT_ALLOWED", "failed arch outside allowlist", 4)
        try:
            with tempfile.TemporaryDirectory(dir=root, prefix=".analysis-") as temporary:
                evidence = analyze(args.ci_log.resolve(), Path(temporary))
                raw = evidence.read_bytes()
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            raise _StepError(INTAKE_ANALYZER_FAILED, type(exc).__name__, 5) from exc
        canonical = root / "ci_evidence.json"
        publish(canonical, raw)
        created = state.get_unit(db, key) is None
        state.create_unit(
            db,
            primary_arch=arches[0],
            toolchain_profile=args.toolchain_profile,
            ci_evidence_ref=str(canonical),
            ci_evidence_sha256=sha256(canonical),
            **common,
        )
        if state.latest_status(db, key) is None:
            state.append_status(db, key, "DISCOVERED")
        if state.latest_status(db, key) == "DISCOVERED":
            state.append_status(db, key, "CI_EVIDENCE_READY")
        unit = state.get_unit(db, key)
        assert unit is not None
        source = _prepare_source(root, unit, remote.rstrip("/") + "/" + unit.project)
        return dict(
            campaign_unit_key=key,
            primary_arch=unit.primary_arch,
            failed_arches=list(unit.failed_arches),
            ci_evidence_ref=str(canonical),
            ci_evidence_sha256=unit.ci_evidence_sha256,
            src_clean=str(source),
            created=created,
            error_code=None,
        )


def main(argv: list[str], *, stdout: TextIO) -> int:
    parser = JsonParser(prog="tizen_campaign_intake campaign-add-unit")
    for name in ("state-db", "config", "ci-log"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in (
        "project",
        "branch",
        "spec-name",
        "base-commit",
        "source-build-id",
        "failed-arches",
    ):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--toolchain-profile", default="clang")
    try:
        result, code = add_unit(parser.parse_args(argv)), 0
    except _StepError as exc:
        result, code = dict(error_code=exc.code, reason=exc.reason), exc.exit_code
    except state.StateInconsistent as exc:
        result, code = dict(error_code="REJECTED_STATE_INCONSISTENT", reason=str(exc)), 4
    except state.CampaignStateBusy as exc:
        result, code = dict(error_code="CAMPAIGN_STATE_BUSY", reason=str(exc)), 4
    except (ValueError, OSError) as exc:
        result, code = dict(error_code="INVALID_ARGS", reason=str(exc)), 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True), file=stdout)
    return code
