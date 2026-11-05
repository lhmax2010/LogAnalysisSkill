"""Exercise real intake with a temporary DB; intercept git before any transport."""

from __future__ import annotations

import datetime
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import yaml
from tizen_campaign_core import campaign_state as state
from tizen_campaign_core._campaign_workspace import _StepError, _unit_hash
from tizen_campaign_core._sandbox_git import SandboxGit
from tizen_campaign_core.submission_identity import build_campaign_unit_key
from tizen_campaign_intake import intake
from tizen_ci_shared.state import StateDatabase

ROOT = Path(__file__).resolve().parents[8]
HERE = Path(__file__).resolve().parent


def hashes() -> dict[str, str]:
    names = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT, text=True).split("\0")
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in names
            if (name.endswith((".py", ".mjs", "-FROZEN.md")) or name == ".importlinter")
            and (ROOT / name).is_file()}


def main() -> None:
    before = hashes()
    attempts = []
    with tempfile.TemporaryDirectory(prefix="restore20-intake-") as temporary:
        directory = Path(temporary)
        config = directory / "config.yaml"
        config.write_text(yaml.safe_dump(dict(
            campaign_workspace=str(directory / "ws"),
            gerrit_ssh_base="ssh://gerrit.invalid:29418",
            max_rounds=3, max_build_invocations=9,
        )))
        args = SimpleNamespace(
            config=config, state_db=directory / "state.db",
            ci_log=ROOT / "tests/fixtures/e2e_clang_compile/buildlog",
            project="platform/upstream/example", branch="tizen_base", spec_name="example",
            base_commit="1" * 40, source_build_id="101",
            failed_arches="standard-x86_64,standard-aarch64", toolchain_profile="clang",
        )
        key = build_campaign_unit_key(ci_system="quickbuild", **{
            name: getattr(args, name) for name in
            ("project", "branch", "spec_name", "base_commit", "source_build_id")})
        db = StateDatabase(args.state_db)
        root = directory / "ws" / _unit_hash(key)

        def blocked_git(self, cwd, *argv, **kwargs):
            attempts.append({
                "operation": argv[0], "remote": argv[1],
                "remote_flag": kwargs.get("remote"), "cwd_is_none": cwd is None,
                "unit_exists_at_call": state.get_unit(db, key) is not None,
                "status_at_call": state.latest_status(db, key),
                "evidence_exists_at_call": (root / "ci_evidence.json").is_file(),
            })
            raise OSError("PROBE_NETWORK_DISABLED")

        with patch.object(SandboxGit, "run", blocked_git):
            try:
                intake.add_unit(args)
            except _StepError as exc:
                failure = {"code": exc.code, "exit_code": exc.exit_code}
            else:
                raise AssertionError("fresh intake unexpectedly avoided source preparation")
        result = {
            "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "head": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "real_intake": True, "real_analyzer": True,
            "git_intercepted_before_subprocess": True, "git_processes_started": 0,
            "network_requests": 0, "attempts": attempts, "failure": failure,
            "unit_exists_after_failure": state.get_unit(db, key) is not None,
            "status_after_failure": state.latest_status(db, key),
            "canonical_source_exists": (root / "src").exists(),
            "staging_remaining": len(list(root.glob(".src.staging-*"))),
        }
        assert len(attempts) == 1 and attempts[0]["operation"] == "clone"
        assert attempts[0]["remote_flag"] is True
        assert attempts[0]["unit_exists_at_call"]
        assert failure == {"code": "INTAKE_CLONE_FAILED", "exit_code": 5}
        assert result["status_after_failure"] == "CI_EVIDENCE_READY"
        assert not result["canonical_source_exists"] and result["staging_remaining"] == 0
    result["temporary_directory_removed"] = not directory.exists()
    result["protected_unchanged"] = before == hashes()
    result["protected_hashes"] = before
    assert result["temporary_directory_removed"] and result["protected_unchanged"]
    (HERE / "probe.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key != "protected_hashes"}))


if __name__ == "__main__":
    main()
