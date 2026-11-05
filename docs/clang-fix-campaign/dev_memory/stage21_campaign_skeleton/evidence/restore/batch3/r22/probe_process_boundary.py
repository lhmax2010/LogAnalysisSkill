"""Observe the first intake subprocess without starting it or accessing a network."""

from __future__ import annotations

import datetime
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import yaml
from tizen_campaign_core._campaign_workspace import _StepError
from tizen_campaign_intake import intake

ROOT = Path(__file__).resolve().parents[8]
HERE = Path(__file__).resolve().parent
PROTECTED = (
    ".importlinter",
    "tizen-campaign-intake/scripts/tizen_campaign_intake/intake.py",
    "tizen-campaign-core/scripts/tizen_campaign_core/_campaign_io.py",
    "tizen-qb-verify/scripts/tizen_qb_verify/qb_browser_agent.mjs",
    "docs/clang-fix-campaign/campaign-skeleton-design-v1.3-FROZEN.md",
    "docs/clang-fix-campaign/p5q-qb-trigger-design-v1.8-FROZEN.md",
)


def hashes() -> dict[str, str]:
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in PROTECTED}


def main() -> None:
    before = hashes()
    observed = []
    with tempfile.TemporaryDirectory(prefix="restore22-process-") as temporary:
        root = Path(temporary)
        config = root / "config.yaml"
        config.write_text(yaml.safe_dump(dict(
            campaign_workspace=str(root / "ws"),
            gerrit_ssh_base="ssh://gerrit.invalid:29418",
            max_rounds=3, max_build_invocations=9,
        )))
        args = SimpleNamespace(
            config=config, state_db=root / "state.db",
            ci_log=ROOT / "tests/fixtures/e2e_clang_compile/buildlog",
            project="platform/upstream/example", branch="tizen_base", spec_name="example",
            base_commit="1" * 40, source_build_id="101",
            failed_arches="standard-aarch64", toolchain_profile="clang",
        )

        def intercept(argv, **kwargs):
            observed.append([str(item).replace(temporary, "<temporary>") for item in argv])
            assert argv[:4] == [sys.executable, "-m", "gbs_analyzer", "analyze"]
            raise subprocess.CalledProcessError(99, argv)

        with patch("subprocess.run", intercept):
            try:
                intake.add_unit(args)
            except _StepError as error:
                failure = {"error_code": error.code, "exit_code": error.exit_code}
            else:
                raise AssertionError("intake unexpectedly bypassed analyzer subprocess")
        assert len(observed) == 1
        assert failure == {"error_code": "INTAKE_ANALYZER_FAILED", "exit_code": 5}
        assert not args.state_db.exists()
    assert not root.exists() and hashes() == before
    result = {"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "observed_argv": observed, "interception": "subprocess.run before process creation",
              "processes_started_by_intake": 0, "network_requests": 0,
              "failure": failure, "state_db_created": False,
              "temporary_removed": True, "protected_unchanged": True, "hashes": before}
    (HERE / "probe.json").write_text(json.dumps(result, indent=2) + "\n")
    print("first subprocess is python -m gbs_analyzer; blocked before launch; assertions passed")


if __name__ == "__main__":
    main()
