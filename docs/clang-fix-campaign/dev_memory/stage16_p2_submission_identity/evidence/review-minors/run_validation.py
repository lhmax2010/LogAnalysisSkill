"""Replay the existing gate catalog in a clean worktree, preserving raw results."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    root = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    output.mkdir(parents=True, exist_ok=True)
    python = sys.executable
    env = os.environ.copy()
    paths = [str(path) for path in sorted(root.glob("*/scripts"))]
    env["PYTHONPATH"] = env["MYPYPATH"] = os.pathsep.join(paths)
    env["PATH"] = str(Path(python).parent) + os.pathsep + env["PATH"]
    catalog = json.loads((root / (
        "docs/clang-fix-campaign/dev_memory/stage14_p49_terminal_batch/"
        "a0-evidence/phase2/execution/C13R/checkers/commands.json"
    )).read_text())
    commands = [
        ("pytest", [python, "-m", "pytest", "tests/", "-v", "--cov=gbs_analyzer",
                    "--cov-report=term-missing", "--cov-fail-under=80",
                    f"--junitxml={output / 'pytest.xml'}"], 0),
        ("mypy", [python, "-m", "mypy"], 0),
        ("ruff", [python, "-m", "ruff", "check", "."], 0),
        ("lint-imports", [str(Path(python).parent / "lint-imports")], 0),
    ]
    commands.extend((row["name"], [python, *row["argv"][1:]], row["expected_exit"])
                    for row in catalog["results"])
    results = []
    for name, argv, expected in commands:
        result = subprocess.run(argv, cwd=root, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        (output / f"{name}.log").write_bytes(result.stdout)
        results.append({"name": name, "argv": argv, "cwd": str(root),
                        "exit": result.returncode, "expected_exit": expected,
                        "sha256": hashlib.sha256(result.stdout).hexdigest()})
        print(f"{name}: exit={result.returncode} expected={expected}", flush=True)
        (output / "commands.json").write_text(json.dumps({
            "python": python, "PYTHONPATH": paths, "MYPYPATH": paths, "results": results,
        }, indent=2) + "\n")
    unexpected = sum(row["exit"] != row["expected_exit"] for row in results)
    print(f"completed={len(results)} unexpected={unexpected}", flush=True)


if __name__ == "__main__":
    main()
