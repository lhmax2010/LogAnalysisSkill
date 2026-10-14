"""Archive offline C5a runs without replacing earlier evidence."""

import argparse
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[6]
BIN = ROOT / ".venv/bin"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("label")
    parser.add_argument("group", choices=["focused", "full", "tools", "ruff"])
    args = parser.parse_args()
    output = HERE / args.label
    output.mkdir()
    env = os.environ.copy()
    for key in ("QB_COOKIE", "QB_PASSWORD", "DEBUG", "PWDEBUG", "NODE_OPTIONS"):
        env.pop(key, None)
    env["P5Q_C5A_EVIDENCE"] = str(output / "artifacts")
    commands = {
        "focused": [
            (
                "focused",
                [
                    str(BIN / "python"),
                    "-m",
                    "pytest",
                    "-v",
                    "-s",
                    "tests/unit/test_p5q_c5a_integration.py",
                    "tests/unit/test_qb_browser_node.py",
                    f"--junitxml={output / 'focused.xml'}",
                ],
            )
        ],
        "full": [
            (
                "pytest",
                [
                    str(BIN / "python"),
                    "-m",
                    "pytest",
                    "-v",
                    "-s",
                    f"--junitxml={output / 'pytest.xml'}",
                ],
            )
        ],
        "tools": [
            ("mypy", [str(BIN / "mypy")]),
            ("lint-imports", [str(BIN / "lint-imports")]),
            (
                "design-check",
                [
                    str(BIN / "python"),
                    "docs/clang-fix-campaign/tools/check_design_doc.py",
                    "docs/clang-fix-campaign/design.md",
                ],
            ),
        ],
        "ruff": [("ruff", [str(BIN / "ruff"), "check", "."])],
    }[args.group]
    records = []
    with tempfile.TemporaryDirectory(prefix="p5q-c5a-export-") as export:
        if args.group == "ruff":
            subprocess.run(
                ["git", "checkout-index", "--all", f"--prefix={export}/"], check=True, cwd=ROOT
            )
        for name, argv in commands:
            started = time.monotonic()
            with (output / f"{name}.log").open("wb") as log:
                run = subprocess.run(
                    argv,
                    cwd=export if args.group == "ruff" else ROOT,
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                )
            row = dict(
                argv=argv,
                exit=run.returncode,
                seconds=round(time.monotonic() - started, 3),
                log=f"{name}.log",
            )
            records.append(row)
            print(json.dumps(row), flush=True)
    (output / "commands.json").write_text(json.dumps(records, indent=2) + "\n")
    return int(any(row["exit"] for row in records))


if __name__ == "__main__":
    raise SystemExit(main())
