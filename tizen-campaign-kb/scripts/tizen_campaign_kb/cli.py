"""Shared JSON adapters for knowledge import, retrieval and synchronization."""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO

import yaml
from tizen_campaign_core import campaign_state, kb
from tizen_campaign_core._campaign_io import JsonParser, analyze, config
from tizen_ci_shared.state import StateDatabase
from tizen_sandbox_submit.sandbox_submit import _Reject


def _parser() -> JsonParser:
    parser = JsonParser(prog="tizen_campaign_kb")
    commands = parser.add_subparsers(dest="command", required=True)
    store = commands.add_parser("kb")
    actions = store.add_subparsers(dest="action", required=True)
    for name in ("query", "append", "promote", "import-diff"):
        action = actions.add_parser(name)
        action.add_argument("--db", type=Path, required=True)
        if name == "query":
            action.add_argument("--diagnosed-flag", required=True)
            for key in ("package", "gerrit-path", "category", "toolchain-profile",
                        "error-signature", "warning-flags"):
                action.add_argument("--" + key)
            action.add_argument("--min-status", choices=("CI_VERIFIED", "MERGED"),
                                default="CI_VERIFIED")
            action.add_argument("--limit-t2", type=int, default=5)
        elif name == "append":
            action.add_argument("--record", type=Path, required=True)
        elif name == "promote":
            action.add_argument("--id", required=True)
            action.add_argument("--to", choices=("CI_VERIFIED", "MERGED"), required=True)
        else:
            action.add_argument("--diff", type=Path, required=True)
            action.add_argument("--ci-log", type=Path, required=True)
            for key in ("package", "gerrit-path", "fix-summary", "baseline-commit"):
                action.add_argument("--" + key, required=True)
            action.add_argument("--toolchain-profile", choices=("clang",), required=True)
            action.add_argument("--change-ref")
            action.add_argument("--quickbuild-id")
    sync = commands.add_parser("campaign-kb-sync")
    sync.add_argument("--state-db", type=Path, required=True)
    sync.add_argument("--config", type=Path, required=True)
    sync.add_argument("--campaign-unit-key", required=True)
    return parser


def _import_diff(args: Any) -> dict[str, Any]:
    if re.fullmatch(r"[0-9a-fA-F]{40}", args.baseline_commit) is None:
        raise ValueError("baseline-commit must be 40 hexadecimal characters")
    if args.change_ref is not None and re.fullmatch(
        r"refs/changes/[0-9]{2}/[0-9]+/[0-9]+", args.change_ref
    ) is None:
        raise ValueError("invalid change-ref")
    if args.quickbuild_id is not None and re.fullmatch(r"[1-9][0-9]*", args.quickbuild_id) is None:
        raise ValueError("quickbuild-id must be a positive integer")
    if not args.package.strip() or not args.gerrit_path.strip() or not args.fix_summary.strip():
        raise ValueError("package, gerrit-path and fix-summary must not be empty")
    # Preserve line endings: the imported tree slot binds the original UTF-8 bytes.
    diff = args.diff.read_bytes().decode("utf-8")
    if not diff.strip():
        raise ValueError("diff must not be empty")
    with tempfile.TemporaryDirectory(prefix="campaign-kb-import-") as temporary:
        evidence = json.loads(analyze(args.ci_log, Path(temporary)).read_bytes())
    primary = evidence.get("primary_error") or {}
    status = "CI_VERIFIED" if args.quickbuild_id is not None else "NEW"
    record = kb.make_record(
        record_type="instance", origin="imported_shelve",
        package=args.package, gerrit_path=args.gerrit_path,
        baseline_commit=args.baseline_commit, verified_tree_sha=None, diff=diff,
        toolchain_profile=args.toolchain_profile, fix_summary=args.fix_summary,
        fix_strategy_initial=None, fix_strategy_final=None, reused_from=None,
        files=[primary["file"]] if isinstance(primary.get("file"), str) else [],
        error_lines=[primary["line"]] if type(primary.get("line")) is int else [],
        confidence=0.0, verified_archs=[], sandbox_branch=None, gerrit_url=None,
        change_ref=args.change_ref, change_id=None,
        quickbuild_id=int(args.quickbuild_id) if args.quickbuild_id is not None else None,
        status=status, promoted_at=datetime.now(timezone.utc).isoformat()
        if status == "CI_VERIFIED" else None,
        **kb.describe_evidence(evidence),
    )
    return asdict(kb.append(args.db, record))


def main(argv: list[str], *, stdout: TextIO) -> int:
    try:
        args = _parser().parse_args(argv)
        result: Any
        if args.command == "campaign-kb-sync":
            from tizen_campaign_kb.sync import run

            result = run(StateDatabase(args.state_db), args.campaign_unit_key, config(args.config))
        elif args.action == "query":
            flags = (None if args.warning_flags is None else
                     args.warning_flags.split(",") if args.warning_flags else [])
            found = kb.query(
                args.db, diagnosed_flag=args.diagnosed_flag, package=args.package,
                gerrit_path=args.gerrit_path, category=args.category,
                toolchain_profile=args.toolchain_profile, error_signature=args.error_signature,
                warning_flags=flags, min_status=args.min_status, limit_t2=args.limit_t2,
            )
            result = dict(t1_records=found.t1, t2_records=found.t2)
        elif args.action == "append":
            record = json.loads(args.record.read_bytes())
            if not isinstance(record, dict):
                raise ValueError("record must be an object")
            result = asdict(kb.append(args.db, record))
        elif args.action == "promote":
            result = kb.promote(args.db, args.id, args.to)
        else:
            result = _import_diff(args)
        code = 0
    except kb.KbCorrupt as exc:
        code, result = 4, dict(error_code="KB_SCHEMA_INVALID", reason=str(exc))
    except yaml.YAMLError:
        code, result = 2, dict(error_code="INVALID_ARGS", reason="invalid_configuration")
    except (kb.KbSchemaError, ValueError) as exc:
        code, result = 2, dict(error_code="INVALID_ARGS", reason=str(exc))
    except campaign_state.StateInconsistent as exc:
        code, result = 4, dict(error_code="REJECTED_STATE_INCONSISTENT", reason=str(exc))
    except _Reject as exc:
        code, result = exc.exit_code, dict(error_code=exc.code, reason=exc.detail)
    except subprocess.SubprocessError:
        code, result = 4, dict(error_code="KB_SCHEMA_INVALID", reason="analyzer_failed")
    except OSError:
        code, result = 4, dict(error_code="KB_SCHEMA_INVALID", reason="io_failed")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True), file=stdout)
    return code
