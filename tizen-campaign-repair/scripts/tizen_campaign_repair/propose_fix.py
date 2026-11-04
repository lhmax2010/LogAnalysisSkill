"""Prepare a guarded T1 edit spec or a context-only generation handoff."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, TextIO
from urllib.parse import urlsplit

import yaml
from gbs_patch_suggest.ingest import extract_first_diagnostic
from gbs_patch_suggest.render import write_outputs
from gbs_patch_suggest.resolver import resolve_context
from tizen_build_verify.edit_spec_guard import validate_edit_spec
from tizen_campaign_core import campaign_state as state
from tizen_campaign_core import previous_evidence
from tizen_campaign_core._campaign_io import JsonParser, config, lock, publish
from tizen_campaign_core._campaign_workspace import (
    _StepError,
    _unit_hash,
    _validate_source_identity,
)
from tizen_campaign_core._sandbox_git import SandboxGit
from tizen_campaign_core.diff_to_edit_spec import DiffUnsupported, convert
from tizen_campaign_core.kb import KbCorrupt
from tizen_ci_shared.state import StateDatabase


def _identity_runner(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    try:
        return SandboxGit().run(Path(argv[2]), *argv[3:])
    except (OSError, subprocess.SubprocessError) as exc:
        raise _StepError("REJECTED_IDENTITY_MISMATCH", "source_identity_unavailable", 4) from exc


def _evidence(
    db: StateDatabase, unit: state.Unit, arch: str, round_index: int
) -> dict[str, Any]:
    if round_index > 1:
        resolved = previous_evidence.resolve(db, unit.campaign_unit_key, arch_norm=arch)
        if isinstance(resolved, previous_evidence.MissingEvidence):
            raise _StepError("REJECTED_STATE_INCONSISTENT", "previous_evidence_missing", 4)
        return resolved.evidence
    try:
        if not unit.ci_evidence_ref or not unit.ci_evidence_sha256:
            raise ValueError("missing anchor")
        raw = Path(unit.ci_evidence_ref).read_bytes()
        if hashlib.sha256(raw).hexdigest() != unit.ci_evidence_sha256:
            raise ValueError("anchor digest mismatch")
        evidence = json.loads(raw)
        if not isinstance(evidence, dict):
            raise ValueError("anchor must be an object")
        return evidence
    except (OSError, ValueError) as exc:
        raise _StepError("REJECTED_CI_EVIDENCE_MISMATCH", "CI evidence anchor differs", 4) from exc


def _lookup(
    db: Path, unit: state.Unit, evidence: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    from tizen_campaign_core import kb

    description = kb.describe_evidence(evidence)
    result = kb.query(
        db,
        diagnosed_flag=description["diagnosed_flag"],
        package=unit.spec_name,
        gerrit_path=unit.project,
        category=description["root_cause_category"],
        warning_flags=description["warning_flags"],
        toolchain_profile=unit.toolchain_profile,
        error_signature=description["error_signature_raw"],
        min_status="CI_VERIFIED",
        limit_t2=5,
    )
    return result.t1, result.t2[:5]


def _fetch_diff(record: dict[str, Any], settings: dict[str, Any], project: str) -> str:
    ref = record.get("change_ref")
    if (not isinstance(ref, str)
            or re.fullmatch(r"refs/changes/[0-9]{2}/[0-9]+/[0-9]+", ref) is None):
        raise DiffUnsupported("invalid_change_ref")
    if record.get("gerrit_path") != project:
        raise DiffUnsupported("precedent_project_mismatch")
    if (re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/+-]*", project) is None
            or ".." in project or project.endswith("/")):
        raise DiffUnsupported("invalid_project")
    base = settings.get("gerrit_ssh_base")
    if not isinstance(base, str):
        raise ValueError("gerrit_ssh_base must be an SSH URL")
    parsed = urlsplit(base)
    if (parsed.scheme != "ssh" or not parsed.hostname or parsed.password
            or parsed.query or parsed.fragment or any(c.isspace() for c in base)):
        raise ValueError("gerrit_ssh_base must be an SSH URL")
    remote = base.rstrip("/") + "/" + project
    git = SandboxGit()
    # Fetch and diff never run in the canonical clone or a build worktree.
    with tempfile.TemporaryDirectory(prefix="campaign-propose-", dir="/tmp") as directory:
        transport = Path(directory) / "transport.git"
        git.run(None, "init", "--bare", str(transport))
        git.run(
            None, "fetch", "--no-tags", "--no-recurse-submodules", remote, ref,
            git_dir=transport, remote=True,
        )
        parents = git.run(
            None, "show", "--no-patch", "--format=%P", "FETCH_HEAD", git_dir=transport
        ).stdout.split()
        if len(parents) != 1:
            raise DiffUnsupported("change_requires_single_parent")
        return git.run(
            None, "diff", "--no-renames", "--binary", parents[0], "FETCH_HEAD", "--",
            git_dir=transport,
        ).stdout


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _baseline_provenance(
    unit: state.Unit, record: dict[str, Any] | None,
) -> dict[str, Any]:
    baseline = record.get("baseline_commit") if record is not None else None
    if record is not None and (
        not isinstance(baseline, str) or re.fullmatch(r"[0-9a-fA-F]{40}", baseline) is None
    ):
        raise _StepError("REJECTED_STATE_INCONSISTENT", "precedent baseline missing or invalid", 4)
    return dict(
        unit_base_commit=unit.base_commit,
        precedent_base_commit=baseline,
        baseline_drift=baseline.lower() != unit.base_commit.lower()
        if isinstance(baseline, str) else None,
    )


def _report(output: Path, baseline: dict[str, Any], result: dict[str, Any]) -> None:
    # Keep the eight-field command contract; version drift is an artifact, not a gate.
    publish(output / "provenance.json", _json_bytes(dict(
        **baseline, kb_precedent_ref=result["kb_precedent_ref"], mode=result["mode"],
        downgrade_reason=result["downgrade_reason"],
    )))


def _propose(args: Any) -> dict[str, Any]:
    arch = state.ARCH_RAW_TO_NORM.get(args.arch)
    if arch is None or args.round_index < 1:
        raise ValueError("invalid arch or round-index")
    settings = config(args.config)
    workspace = settings["campaign_workspace"]
    if not isinstance(workspace, str) or not workspace.strip():
        raise ValueError("campaign_workspace must be a non-empty path")
    kb_path = settings.get("kb_db")
    if not isinstance(kb_path, str) or not Path(kb_path).is_absolute():
        raise ValueError("kb_db must be an absolute path")
    db = StateDatabase(args.state_db)
    root = Path(workspace).resolve() / _unit_hash(args.campaign_unit_key)
    source = root / "src"
    output = args.output_dir.resolve()
    if output == source.resolve() or source.resolve() in output.parents:
        raise ValueError("output-dir must not be in the canonical source")
    with lock(root / arch / ".repair_step.lock"):
        unit = state.get_unit(db, args.campaign_unit_key)
        if unit is None:
            raise _StepError("REJECTED_IDENTITY_MISMATCH", "unknown campaign unit", 4)
        _validate_source_identity(source, unit, subprocess_runner=_identity_runner)
        evidence = _evidence(db, unit, arch, args.round_index)
        t1, t2 = _lookup(Path(kb_path), unit, evidence)
        baseline = _baseline_provenance(unit, t1[0] if t1 else None)
        # A fresh output prevents a failed conversion from exposing an old edit spec.
        output.mkdir(parents=True, exist_ok=False)
        result: dict[str, Any] = dict(
            mode="generate", needs_generation=True, edit_spec_path=None, source_kind=None,
            kb_precedent_ref=None, context_dir=None, t2_records=t2, downgrade_reason=None,
        )
        if t1:
            record = t1[0]
            precedent = record.get("id")
            if not isinstance(precedent, str) or not precedent:
                raise _StepError("REJECTED_STATE_INCONSISTENT", "precedent id missing", 4)
            result["kb_precedent_ref"] = precedent
            try:
                if record.get("origin") == "imported_shelve":
                    diff = record.get("diff")
                    if not isinstance(diff, str):
                        raise DiffUnsupported("imported_diff_missing")
                else:
                    diff = _fetch_diff(record, settings, unit.project)
                spec = convert(diff, source, "campaign-t1")
                spec["kb_precedent_ref"] = precedent
                spec["kb_provenance"] = baseline
                validate_edit_spec(spec, str(source))
            except DiffUnsupported as exc:
                reason = str(exc)
                result["downgrade_reason"] = (
                    "guard_rejected" if reason.startswith("guard_rejected:") else reason
                )
            except (OSError, subprocess.SubprocessError, UnicodeError):
                result["downgrade_reason"] = "t1_material_unavailable"
            else:
                path = output / "edit_spec.json"
                publish(path, _json_bytes(spec))
                result.update(
                    mode="t1", needs_generation=False, edit_spec_path=str(path),
                    source_kind="t1_cherry_pick",
                )
                _report(output, baseline, result)
                return result
        context = output / "context"
        evidence_path = context / "evidence_packet.json"
        publish(evidence_path, _json_bytes(evidence))
        # The full patch-suggest CLI also emits skeleton edits in some modes.
        # Its context-only primitives do not create edits or invoke a model.
        write_outputs(
            resolve_context(extract_first_diagnostic(evidence), src_root=source),
            context, evidence_path=evidence_path,
        )
        publish(context / "t2_records.json", _json_bytes(t2))
        result["context_dir"] = str(context)
        _report(output, baseline, result)
        return result


def main(argv: list[str], *, stdout: TextIO) -> int:
    parser = JsonParser(prog="tizen_campaign_repair propose-fix")
    for name in ("state-db", "config", "output-dir"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("campaign-unit-key", "arch"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--round-index", type=int, required=True)
    try:
        result, code = _propose(parser.parse_args(argv)), 0
    except _StepError as exc:
        result, code = dict(error_code=exc.code, reason=exc.code.lower()), exc.exit_code
    except KbCorrupt:
        result, code = dict(error_code="KB_SCHEMA_INVALID", reason="kb_corrupt"), 4
    except state.StateInconsistent:
        result = dict(error_code="REJECTED_STATE_INCONSISTENT", reason="state_inconsistent")
        code = 4
    except (OSError, ValueError, yaml.YAMLError):
        result, code = dict(error_code="INVALID_ARGS", reason="invalid_arguments"), 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True), file=stdout)
    return code
