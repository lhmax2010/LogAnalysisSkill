"""Offline post-run checks; never start a browser or open the campaign database."""

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from ci_triage.qb_redact import PageRedactor

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]
EXPECTED_DB = "bd4380eacf2409c40137ad8b648939261b3a3eebe20d4101a6e2269b2c4eb405"
EXPECTED_DESIGN = "f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c"


def main():
    checker = PageRedactor()
    report = {"checked_at": datetime.now(timezone.utc).isoformat(), "files": {}, "commands": []}
    for name in ("result.json", "command.json", "stop-report.md"):
        path = HERE / name
        checker.check_bytes(path.read_bytes())
        checker.check_written(path)
        report["files"][name] = hashlib.sha256(path.read_bytes()).hexdigest()
    result = json.loads((HERE / "result.json").read_text())
    assert result["ok"] is False
    assert [row["ok"] for row in result["commands"]] == [True, True, True, False]
    assert result["trace"][-1] == {"command": "close", "ok": True}
    assert result["commands"][-1]["agent_exit_code"] == -15
    assert result["commands"][-1]["failure_category"] is None
    assert result["release_state"] == "not_released"
    assert result["form_action_releases"] == 0
    assert result["state_db_access"] is False
    expected = {
        name + ("/selection" if isinstance(value, list) else "/value"): value
        for name, value in result["requested_fields"].items()
    }
    expected["SNAPSHOT_NUM/value"] = "tizen-base-toolchain_20260924.094908"
    assert result["readback"] == expected
    canonical = json.dumps(expected, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert hashlib.sha256(canonical.encode()).hexdigest() == result["fingerprint"]
    for key, path, expected_hash in (
        (
            "dedicated_db",
            Path("/home/linhao/Toolchain/p5q-live-validation/p5q-c6/state.db"),
            EXPECTED_DB,
        ),
        (
            "frozen_design",
            ROOT / "docs/clang-fix-campaign/p5q-qb-trigger-design-v1.5-FROZEN.md",
            EXPECTED_DESIGN,
        ),
    ):
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == expected_hash
        report[key + "_sha256"] = actual
    report["remaining_browser_profile_paths"] = [
        str(path) for path in sorted(Path("/dev/shm").glob("p5q-browser-*"))
    ]
    for name, argv in (
        (
            "static",
            [
                sys.executable, "-m", "pytest", "-q",
                "tests/unit/test_p5q_c6_diagnostics.py::test_probe_source_is_non_mutating",
            ],
        ),
        (
            "design",
            [
                sys.executable, "docs/clang-fix-campaign/tools/check_design_doc.py",
                "docs/clang-fix-campaign/design.md",
            ],
        ),
        ("ruff", [sys.executable, "-m", "ruff", "check", str(Path(__file__))]),
        ("diff", ["git", "diff", "--check"]),
    ):
        completed = subprocess.run(argv, cwd=ROOT, capture_output=True, check=False)
        log = completed.stdout + completed.stderr
        checker.check_bytes(log)
        output = HERE / (name + ".log")
        output.write_bytes(log)
        checker.check_written(output)
        report["commands"].append({"argv": argv, "exit": completed.returncode, "log": output.name})
        assert completed.returncode == 0
    report["evidence_checks"] = "PASS; live diagnosis remains STOPPED"
    raw = (json.dumps(report, indent=2) + "\n").encode()
    checker.check_bytes(raw)
    (HERE / "validation.json").write_bytes(raw)
    checker.check_written(HERE / "validation.json")
    print(raw.decode())


if __name__ == "__main__":
    main()
