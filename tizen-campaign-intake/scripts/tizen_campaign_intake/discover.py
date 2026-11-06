"""Consume a verified discovery manifest without QuickBuild or browser access."""

from __future__ import annotations

import datetime
import json
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any, TextIO

import yaml
from tizen_campaign_core import campaign_state as state
from tizen_campaign_core._campaign_io import JsonParser, analyze, config
from tizen_campaign_core._campaign_workspace import _StepError
from tizen_campaign_core.discovery_manifest import atomic_write, load, require

from tizen_campaign_intake.intake import add_unit


def compilation_failure(evidence: dict[str, Any]) -> bool:
    primary = evidence.get("primary_error") or {}
    return (
        evidence.get("failed_phase") in {"%build", "compile"}
        and primary.get("severity") in {"error", "fatal error"}
        and primary.get("kind") in {"compiler", "werror"}
        and bool(primary.get("file"))
        and isinstance(primary.get("line"), int)
    )


def discover(args: Any) -> dict[str, Any]:
    settings = config(args.config)
    manifest, logs = load(args.manifest, args.state_root)
    if settings.get("state_root") is not None:
        require(Path(settings["state_root"]).resolve() == args.state_root.resolve())
    # Validate every package and every log before the first write to the state DB.
    results: list[dict[str, Any]] = []
    for package in manifest["packages"]:
        row = {
            "spec_name": package["spec_name"],
            "status": package["status"],
            "reason": package["reason"],
            "campaign_unit_key": None,
            "intake": None,
        }
        results.append(row)
        rejected_arch = package["status"] == "ARCH_NOT_ALLOWED"
        if package["status"] != "ok" and not rejected_arch:
            continue
        if not all(package[k] for k in ("project", "branch", "base_commit")):
            row.update(status="DISCOVERY_SOURCE_UNRESOLVED", reason="SOURCE_VARIABLES")
            continue
        if not rejected_arch:
            try:
                with tempfile.TemporaryDirectory(prefix="campaign-discover-analysis-") as tmp:
                    evidence = json.loads(
                        analyze(logs[package["spec_name"]], Path(tmp)).read_text()
                    )
                if not args.include_non_compile and not compilation_failure(evidence):
                    row.update(status="skipped", reason="NON_COMPILE_FAILURE")
                    continue
            except (OSError, ValueError, subprocess.SubprocessError):
                row.update(status="skipped", reason="INTAKE_ANALYZER_FAILED")
                continue
        if args.dry_run:
            if not rejected_arch:
                row.update(status="dry_run", reason=None)
            continue
        intake_args = SimpleNamespace(
            config=args.config,
            state_db=args.state_db,
            project=package["project"],
            branch=package["branch"],
            spec_name=package["spec_name"],
            base_commit=package["base_commit"],
            source_build_id=manifest["build_id"],
            failed_arches=",".join(package["failed_arches"]),
            toolchain_profile="clang",
            ci_log=logs.get(package["spec_name"]),
        )
        try:
            result = add_unit(intake_args)
            row.update(
                status="created" if result["created"] else "existing",
                reason=None,
                campaign_unit_key=result["campaign_unit_key"],
                intake=result,
            )
        except _StepError as error:
            row.update(status="ARCH_NOT_ALLOWED" if rejected_arch else "skipped", reason=error.code)
        except (ValueError, OSError, state.StateInconsistent, state.CampaignStateBusy):
            row.update(status="skipped", reason="INTAKE_FAILED")
    report = {
        "build_id": manifest["build_id"],
        "child_build_id": manifest["child_build_id"],
        "dry_run": args.dry_run,
        "packages": results,
    }
    parent = args.manifest.resolve().parent
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ-")
    output = Path(tempfile.mkdtemp(prefix="intake-" + stamp, dir=parent))
    atomic_write(
        output / "discover.json", (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode()
    )
    lines = ["# Campaign Discovery", "", "| Package | Status | Reason |", "| --- | --- | --- |"]
    lines.extend(
        f"| {row['spec_name']} | {row['status']} | {row['reason'] or ''} |" for row in results
    )
    atomic_write(output / "discover.md", ("\n".join(lines) + "\n").encode())
    return {**report, "report_dir": str(output), "error_code": None}


def main(argv: list[str], *, stdout: TextIO) -> int:
    parser = JsonParser(prog="campaign-discover")
    for name in ("manifest", "state-db", "state-root", "config"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--include-non-compile", action="store_true")
    try:
        result, code = discover(parser.parse_args(argv)), 0
    except (ValueError, OSError, TypeError, KeyError, yaml.YAMLError):
        result, code = {"error_code": "INVALID_DISCOVERY_MANIFEST"}, 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True), file=stdout)
    return code
