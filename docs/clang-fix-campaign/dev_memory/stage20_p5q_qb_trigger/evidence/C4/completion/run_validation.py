"""Archive C4 offline validation commands, outputs and exit codes."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]
PYTHON = ROOT / ".venv/bin/python"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("group", choices=["pytest", "focused", "tools", "node", "ruff"])
    group = parser.parse_args().group
    if group == "ruff":
        tree = subprocess.check_output(["git", "write-tree"], cwd=ROOT, text=True).strip()
        with tempfile.TemporaryDirectory(prefix="p5q-c4-ruff-") as exported:
            subprocess.run(
                ["git", "checkout-index", "--all", f"--prefix={exported}/"], cwd=ROOT, check=True
            )
            argv = [str(ROOT / ".venv/bin/ruff"), "check", "."]
            with (HERE / "ruff.log").open("wb") as log:
                log.write(f"tree={tree}\nexport={exported}\n".encode())
                log.flush()
                completed = subprocess.run(argv, cwd=exported, stdout=log, stderr=subprocess.STDOUT)
        record = dict(
            command=argv,
            tree=tree,
            cwd=exported,
            exit=completed.returncode,
            export_cleaned=True,
            log="ruff.log",
        )
        (HERE / "commands-ruff.json").write_text(json.dumps([record], indent=2) + "\n")
        print(json.dumps(record), flush=True)
        return completed.returncode
    commands = {
        "pytest": [
            ("pytest", [str(PYTHON), "-m", "pytest", "-v", f"--junitxml={HERE / 'pytest.xml'}"])
        ],
        "focused": [
            (
                "focused",
                [
                    str(PYTHON),
                    "-m",
                    "pytest",
                    "-v",
                    "-s",
                    "tests/unit/test_qb_result_fetch.py",
                    "tests/unit/test_qb_browser.py",
                    "tests/unit/test_qb_trigger.py::test_sha256_remote_residual",
                    f"--junitxml={HERE / 'focused.xml'}",
                ],
            )
        ],
        "tools": [
            ("mypy", [str(ROOT / ".venv/bin/mypy")]),
            ("lint-imports", [str(ROOT / ".venv/bin/lint-imports")]),
            (
                "design-check",
                [
                    str(PYTHON),
                    "docs/clang-fix-campaign/tools/check_design_doc.py",
                    "docs/clang-fix-campaign/design.md",
                ],
            ),
        ],
        "node": [
            (
                "node-gates",
                [
                    str(PYTHON),
                    "-m",
                    "pytest",
                    "-v",
                    "-s",
                    "tests/unit/test_qb_browser_node.py",
                    f"--junitxml={HERE / 'node-gates.xml'}",
                ],
            )
        ],
    }[group]
    env = os.environ.copy()
    for key in ("QB_COOKIE", "QB_PASSWORD", "DEBUG", "PWDEBUG", "NODE_OPTIONS"):
        env.pop(key, None)
    records = []
    for name, argv in commands:
        start = time.monotonic()
        with (HERE / f"{name}.log").open("wb") as log:
            result = subprocess.run(argv, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        record = dict(
            command=argv,
            cwd=str(ROOT),
            exit=result.returncode,
            seconds=round(time.monotonic() - start, 3),
            log=f"{name}.log",
        )
        records.append(record)
        print(json.dumps(record), flush=True)
    (HERE / f"commands-{group}.json").write_text(json.dumps(records, indent=2) + "\n")
    return int(any(r["exit"] for r in records))


if __name__ == "__main__":
    sys.exit(main())
