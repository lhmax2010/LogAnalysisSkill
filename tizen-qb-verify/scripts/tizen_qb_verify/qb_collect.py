"""Read-only discovery producer. No analyzer, source checkout or campaign DB."""

from __future__ import annotations

import datetime
import hashlib
import json
import re
import tempfile
from pathlib import Path
from typing import Any, TextIO

import yaml
from tizen_campaign_core._campaign_io import JsonParser
from tizen_campaign_core.discovery_manifest import SCHEMA, atomic_write, require, validate

from tizen_qb_verify.qb_browser import QbBrowser, QbBrowserError
from tizen_qb_verify.qb_config import parse_qb_config, project_for_branch
from tizen_qb_verify.qb_redact import EvidenceRedactionError, PageRedactor


def collect(args: Any) -> dict[str, Any]:
    settings = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    require(isinstance(settings, dict))
    qb = parse_qb_config(settings.get("qb"))
    project = project_for_branch(qb, args.qb_project)
    require(args.build_id is None or re.fullmatch(r"[1-9][0-9]*", args.build_id))
    since = datetime.date.fromisoformat(args.since) if args.since else None
    args.state_root.mkdir(parents=True, exist_ok=True)
    root = args.state_root.resolve()
    output: dict[str, Any] = {"manifests": [], "outside_recent_window": [], "error_code": None}
    if since is not None:
        output["history_coverage"] = "outside_recent_window"
    with QbBrowser(qb) as browser:
        try:
            browser.login()
            started = browser.command(
                "discovery_start",
                overview_id=project["overview_id"],
                build_id=args.build_id,
                output_dir=str(root),
            )

            def read(path: str) -> dict[str, Any]:
                response = browser.command("discovery_read", path=path)
                # HTML is not evidence for other builds; only closed discovery facts leave here.
                output.setdefault("identity_counts", []).append(
                    {
                        "path": path,
                        "count": response["outside_identity_count"],
                    }
                )
                return dict(response["discovery"])

            first = read(started["path"])
            builds = [first]
            if since is not None:
                builds = []
                for row in first["builds"]:
                    require(re.match(r"^\d{4}-\d{2}-\d{2}(?: |T|$)", row["begin_date"]))
                    if datetime.date.fromisoformat(row["begin_date"][:10]) < since:
                        output["outside_recent_window"].append(row["build_id"])
                    else:
                        builds.append(read(f"/build/{row['build_id']}/overview"))
            for build in builds:
                if not build["child"]:
                    read(f"/build/{build['build_id']}/variables")
                children = (
                    [build]
                    if build["child"]
                    else [read(path) for path in build["paths"] if path.endswith("/overview")]
                )
                for child in children:
                    child_id = child["build_id"]
                    read(f"/build/{child_id}/variables")
                    entry = read(f"/build/{child_id}/html_report")
                    report = read(entry["paths"][0])
                    parent = root / "discovery" / report["build_id"]
                    require(parent.resolve() == parent)
                    parent.mkdir(parents=True, exist_ok=True)
                    require(parent.resolve() == parent)
                    now = datetime.datetime.now(datetime.timezone.utc)
                    run = Path(
                        tempfile.mkdtemp(prefix=now.strftime("%Y%m%dT%H%M%S.%fZ-"), dir=parent)
                    )
                    for row in report["packages"]:
                        if row["status"] != "ok":
                            continue
                        try:
                            response = browser.command(
                                "read_text",
                                build_id=child_id,
                                spec_name=row["spec_name"],
                                run_dir=run.name,
                            )
                            path = Path(response["path"]).resolve(strict=True)
                            expected = (
                                run / "logs" / f"{row['spec_name']}.{row['primary_arch']}.txt"
                            )
                            require(path == expected)
                            raw = path.read_bytes()
                            require(hashlib.sha256(raw).hexdigest() == response["sha256"])
                            PageRedactor().check_written(path)
                            row.update(
                                log_path=path.relative_to(run).as_posix(),
                                log_sha256=response["sha256"],
                            )
                        except QbBrowserError as error:
                            if error.code not in {
                                "DISCOVERY_LOG_UNREADABLE",
                                "QB_TEXT_ENCODING_UNSUPPORTED",
                                "QB_DOWNLOAD_UNSUPPORTED",
                            }:
                                raise
                            require(error.reason is not None)
                            row.update(status="DISCOVERY_LOG_UNREADABLE", reason=error.reason)
                    manifest = validate(
                        {
                            "schema_version": SCHEMA,
                            "qb_project": args.qb_project,
                            "build_id": report["build_id"],
                            "child_build_id": child_id,
                            "captured_at": now.isoformat(),
                            "report_dir": report["report_dir"],
                            "packages": report["packages"],
                        }
                    )
                    path = run / "discover-manifest.json"
                    atomic_write(
                        path, (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()
                    )
                    output["manifests"].append(str(path))
        finally:
            # QbBrowser retains only command names and validated error facts, never HTML/logs.
            output["commands"] = browser.trace
    return output


def main(argv: list[str], *, stdout: TextIO) -> int:
    parser = JsonParser(prog="qb-discover")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--state-root", type=Path, required=True)
    parser.add_argument("--qb-project", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--build-id")
    group.add_argument("--since")
    try:
        result, code = collect(parser.parse_args(argv)), 0
    except QbBrowserError as error:
        result, code = (
            {"error_code": error.code, "reason": error.reason, "failure": error.failure_facts()},
            4,
        )
    except EvidenceRedactionError:
        result, code = {"error_code": "QB_EVIDENCE_REDACTION_FAILED"}, 4
    except (ValueError, OSError, KeyError, TypeError, yaml.YAMLError):
        result, code = {"error_code": "INVALID_DISCOVERY_INPUT"}, 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True), file=stdout)
    return code
