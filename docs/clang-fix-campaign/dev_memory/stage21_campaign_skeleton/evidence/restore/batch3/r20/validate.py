"""Offline checks for RESTORE-20 registration and the network-boundary probe."""

from __future__ import annotations

import datetime
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[8]
HERE = Path(__file__).resolve().parent


def main() -> None:
    results = []
    paths = ["docs/clang-fix-campaign/design.md",
             "docs/clang-fix-campaign/dev_memory/INDEX.md",
             "docs/clang-fix-campaign/dev_memory/stage21_campaign_skeleton/progress.md"]
    for name, argv in (
        ("probe", [".venv/bin/python", str(HERE / "probe_offline_intake.py")]),
        ("imports", [".venv/bin/lint-imports", "--no-cache"]),
        ("design", [".venv/bin/python", "docs/clang-fix-campaign/tools/check_design_doc.py",
                    paths[0]]),
        ("ruff", [".venv/bin/ruff", "check", "--no-respect-gitignore", str(HERE)]),
        ("diff", ["git", "diff", "--check", "--", *paths]),
    ):
        started = datetime.datetime.now(datetime.timezone.utc).isoformat()
        result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
        (HERE / f"{name}.stdout.log").write_text(result.stdout)
        (HERE / f"{name}.stderr.log").write_text(result.stderr)
        results.append({"name": name, "argv": argv, "started_utc": started,
                        "finished_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        "exit_code": result.returncode})
    before = json.loads((HERE / "probe.json").read_text())["protected_hashes"]
    unchanged = all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == digest
                    for p, digest in before.items())
    (HERE / "validation.json").write_text(json.dumps(
        {"commands": results, "protected_count": len(before), "unchanged": unchanged,
         "full_pytest_run": False, "live_commands_run": False}, indent=2) + "\n")
    assert unchanged and all(row["exit_code"] == 0 for row in results)
    print(json.dumps({"checks": len(results), "failed": 0, "unchanged": unchanged}))


if __name__ == "__main__":
    main()
