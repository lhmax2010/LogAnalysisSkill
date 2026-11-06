"""Delete only the explicitly authorized, freshly checked abandoned profile."""

import datetime
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
PROFILE = Path("/dev/shm/p5q-browser-3ByKn8")
previous = json.loads((HERE / "profile-check.json").read_text())
assert previous["exists"] and not previous["is_symlink"]
assert all(item["exit"] == 1 and not item["stdout"] and not item["stderr"]
           for item in previous["commands"])
checks = []
for argv in (["fuser", "-v", str(PROFILE)], ["lsof", "-nP", "+D", str(PROFILE)]):
    result = subprocess.run(argv, capture_output=True, text=True, check=False, timeout=120)
    checks.append({"argv": argv, "exit": result.returncode,
                   "stdout": result.stdout, "stderr": result.stderr})
assert all(item["exit"] == 1 and not item["stdout"] and not item["stderr"] for item in checks)
assert PROFILE.is_dir() and not PROFILE.is_symlink()
argv = ["rm", "-r", "--one-file-system", "--", str(PROFILE)]
result = subprocess.run(argv, capture_output=True, text=True, check=False)
record = {"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
          "checks": checks, "argv": argv, "exit": result.returncode,
          "stdout": result.stdout, "stderr": result.stderr,
          "exists_after": PROFILE.exists()}
(HERE / "profile-removal.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record, indent=2))
