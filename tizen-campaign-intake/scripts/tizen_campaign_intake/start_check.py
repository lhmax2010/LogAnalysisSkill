"""Campaign startup checks without QuickBuild access or credential output."""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, TextIO

import yaml
from tizen_campaign_core._campaign_io import JsonParser
from tizen_campaign_core._sandbox_git import SandboxGit

REQUIRED = (
    "gerrit_ssh_base",
    "gerrit_user",
    "git_author_identity",
    "git_committer_identity",
    "push_timeout_sec",
    "push_retry",
    "target_arches",
    "campaign_workspace",
    "clang_conf_path",
)


def check(config: Path, state_root: Path, projects: list[str]) -> dict[str, Any]:
    valid_projects = bool(projects) and all(
        re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/+-]*", p) is not None
        and ".." not in p
        and not p.endswith("/")
        for p in projects
    )
    try:
        data = yaml.safe_load(config.read_text(encoding="utf-8"))
        settings = data if isinstance(data, dict) else {}
    except (OSError, yaml.YAMLError):
        settings = {}
    missing = [key for key in REQUIRED if settings.get(key) in (None, "")]
    checks = [
        dict(
            name="config",
            passed=not missing and valid_projects,
            reason="invalid_project" if not valid_projects else "missing_keys" if missing else None,
            missing_keys=missing,
        )
    ]
    conf = settings.get("clang_conf_path")
    valid_conf = (
        isinstance(conf, str)
        and Path(conf).is_file()
        and "/reference/" not in conf
        and "/reference/" not in str(Path(conf).resolve())
    )
    checks.append(
        dict(
            name="clang_conf",
            passed=valid_conf,
            reason=None if valid_conf else "invalid_clang_conf",
        )
    )
    if missing or not valid_projects:
        checks.extend(
            dict(name=n, passed=False, reason="config_failed")
            for n in ("gbs", "gerrit", "state_directory")
        )
    else:
        try:
            available = (
                subprocess.run(
                    ["gbs", "--version"], check=False, capture_output=True, timeout=30
                ).returncode
                == 0
            )
        except (OSError, subprocess.SubprocessError):
            available = False
        checks.append(
            dict(name="gbs", passed=available, reason=None if available else "unavailable")
        )
        base = settings.get("gerrit_ssh_base")
        valid_base = isinstance(base, str) and base.startswith("ssh://")
        reachability = []
        if valid_base:
            assert isinstance(base, str)
            for project in projects:
                try:
                    ok = (
                        SandboxGit()
                        .run(
                            None,
                            "ls-remote",
                            base.rstrip("/") + "/" + project,
                            remote=True,
                            check=False,
                        )
                        .returncode
                        == 0
                    )
                except (OSError, subprocess.SubprocessError):
                    ok = False
                reachability.append(dict(project=project, passed=ok))
        reachable = valid_base and all(row["passed"] for row in reachability)
        checks.append(
            dict(
                name="gerrit",
                passed=reachable,
                projects=reachability,
                reason="config_not_ssh" if not valid_base else None if reachable else "unreachable",
            )
        )
        try:
            state_root.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryFile(dir=state_root) as stream:
                stream.write(b"startup-check")
                stream.flush()
            writable = True
        except OSError:
            writable = False
        checks.append(
            dict(name="state_directory", passed=writable, reason=None if writable else "unwritable")
        )
    return dict(
        checks=checks,
        error_code=None if all(row["passed"] for row in checks) else "PREFLIGHT_FAILED",
    )


def main(argv: list[str], *, stdout: TextIO) -> int:
    parser = JsonParser(prog="campaign-start-check")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--state-root", type=Path, required=True)
    parser.add_argument("--project", action="append", required=True)
    try:
        args = parser.parse_args(argv)
        result = check(args.config, args.state_root, args.project)
    except ValueError:
        result = dict(
            error_code="PREFLIGHT_FAILED",
            checks=[dict(name="config", passed=False, reason="invalid_args")],
        )
    print(json.dumps(result, sort_keys=True), file=stdout)
    return 0 if result["error_code"] is None else 4
