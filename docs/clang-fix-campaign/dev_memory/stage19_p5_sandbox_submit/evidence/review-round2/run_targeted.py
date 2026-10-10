"""Record the same review regression fixtures before and after the fixes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("before", "after"))
    parser.add_argument("tree", type=Path)
    args = parser.parse_args()
    root = args.tree.resolve()
    output = Path(__file__).resolve().parent / args.phase
    output.mkdir(exist_ok=True)
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(str(p) for p in sorted(root.glob("*/scripts")))
    tests = ["tests/unit/test_suppress_policy.py", "tests/unit/test_sandbox_submit.py"]
    argv = [
        sys.executable,
        "-m",
        "pytest",
        *tests,
        "-q",
        "-s",
        "-k",
        "review2",
        f"--junitxml={output / 'pytest.xml'}",
    ]
    result = subprocess.run(
        argv, cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    (output / "pytest.log").write_bytes(result.stdout)
    sources = [
        "tizen-ci-triage/scripts/ci_triage/" + name + ".py"
        for name in ("suppress_policy", "sandbox_submit")
    ]
    record = {
        "argv": argv,
        "cwd": str(root),
        "PYTHONPATH": env["PYTHONPATH"],
        "exit": result.returncode,
        "sha256": {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in tests + sources},
    }
    (output / "command.json").write_text(json.dumps(record, indent=2) + "\n")
    print(result.stdout.decode())
    print(f"pytest_exit={result.returncode}")
    expected = 1 if args.phase == "before" else 0
    assert result.returncode == expected


if __name__ == "__main__":
    main()
