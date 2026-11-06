"""Run three independent C5a cases serially; stop immediately on a nonzero exit."""

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NODEID = (
    "tests/unit/test_p5q_c5a_integration.py::test_real_cli_browser_submit_bind_pending_pass[build]"
)
results = []
for number in range(1, 4):
    output = HERE / f"retry-{number}"
    argv = [
        sys.executable,
        str(HERE / "run_one.py"),
        str(output),
        sys.executable,
        "tests/run_quiet.py",
        NODEID,
        "-q",
        f"--junitxml={output / 'pytest.xml'}",
    ]
    result = subprocess.run(argv, check=False)
    results.append({"number": number, "argv": argv, "exit": result.returncode})
    (HERE / "three-results.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps({"number": number, "exit": result.returncode}), flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)
