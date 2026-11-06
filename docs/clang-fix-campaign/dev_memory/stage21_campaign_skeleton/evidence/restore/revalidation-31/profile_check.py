"""Read-only reference check of the one RESTORE-31 authorized profile."""

import datetime
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
PROFILE = Path("/dev/shm/p5q-browser-3ByKn8")
results = {
    "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "path": str(PROFILE), "exists": PROFILE.exists(), "is_symlink": PROFILE.is_symlink(),
    "producer": "qb_browser_agent.mjs:createRuntime mkdtemp('/dev/shm/p5q-browser-')",
    "test_entry": "tests/node/p5q_cli_agent.mjs calls production createRuntime",
    "commands": [], "deleted": False,
}
if PROFILE.exists() and not PROFILE.is_symlink():
    for argv in (["fuser", "-v", str(PROFILE)], ["lsof", "-nP", "+D", str(PROFILE)]):
        try:
            process = subprocess.run(argv, capture_output=True, text=True, check=False, timeout=120)
            results["commands"].append({"argv": argv, "exit": process.returncode,
                                        "stdout": process.stdout, "stderr": process.stderr})
        except (OSError, subprocess.TimeoutExpired) as error:
            results["commands"].append({"argv": argv, "failure_class": type(error).__name__})
(HERE / "profile-check.json").write_text(json.dumps(results, indent=2) + "\n")
print(json.dumps(results, indent=2))
