"""Archive C6 diagnostic gates; all browser traffic is local synthetic traffic."""

import argparse
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[7]
HERE = Path(__file__).resolve().parent
BIN = ROOT / ".venv/bin"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("label")
    parser.add_argument("group", choices=["full", "focused", "tools", "safety", "ruff"])
    args = parser.parse_args()
    output = HERE / args.label
    output.mkdir()
    env = os.environ.copy()
    for key in ("QB_COOKIE", "QB_PASSWORD", "DEBUG", "PWDEBUG", "NODE_OPTIONS"):
        env.pop(key, None)
    env["P5Q_C6_DIAG_EVIDENCE"] = str(output / "artifacts")
    node = str(Path.home() / ".local/bin/node")
    commands = {
        "full": [
            ("pytest", [str(BIN / "pytest"), "-v", "-s", f"--junitxml={output / 'pytest.xml'}"])
        ],
        "focused": [
            (
                "pytest",
                [
                    str(BIN / "pytest"),
                    "-v",
                    "-s",
                    "tests/unit/test_p5q_c6_diagnostics.py",
                    "tests/unit/test_qb_browser.py",
                    f"--junitxml={output / 'pytest.xml'}",
                ],
            )
        ],
        "tools": [
            ("mypy", [str(BIN / "mypy")]),
            ("lint-imports", [str(BIN / "lint-imports")]),
            (
                "design",
                [
                    str(BIN / "python"),
                    "docs/clang-fix-campaign/tools/check_design_doc.py",
                    "docs/clang-fix-campaign/design.md",
                ],
            ),
            (
                "node",
                [
                    node,
                    "--test",
                    "tests/node/test_qb_browser_agent.mjs",
                    "tests/node/test_qb_failure_categories.mjs",
                    "tests/node/test_qb_agent_source_guards.mjs",
                ],
            ),
        ],
        "safety": [
            (
                "safety",
                [
                    node,
                    "tests/node/p5q_c2b_safety.mjs",
                    str(Path.home() / ".bun/install/cache/playwright-core/1.58.2@@@1/index.mjs"),
                    str(Path.home() / ".cache/ms-playwright/chromium-1208/chrome-linux64/chrome"),
                ],
            )
        ],
        "ruff": [("ruff", [str(BIN / "ruff"), "check", "."])],
    }[args.group]
    records = []
    with tempfile.TemporaryDirectory(prefix="p5q-c6-diagnostic-export-") as export:
        if args.group == "ruff":
            subprocess.run(
                ["git", "checkout-index", "--all", f"--prefix={export}/"], cwd=ROOT, check=True
            )
        for name, argv in commands:
            started = time.monotonic()
            with (output / f"{name}.log").open("wb") as log:
                result = subprocess.run(
                    argv,
                    cwd=export if args.group == "ruff" else ROOT,
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                )
            row = dict(
                argv=argv,
                exit=result.returncode,
                seconds=round(time.monotonic() - started, 3),
                log=f"{name}.log",
            )
            records.append(row)
            print(json.dumps(row), flush=True)
            (output / "commands.json").write_text(json.dumps(records, indent=2) + "\n")
    return int(any(row["exit"] for row in records))


if __name__ == "__main__":
    raise SystemExit(main())
