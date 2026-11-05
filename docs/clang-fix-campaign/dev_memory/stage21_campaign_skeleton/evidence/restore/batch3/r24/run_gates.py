"""Offline RESTORE-24 gates with per-command evidence, never live services."""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
HERE = BASE / sys.argv[1] if len(sys.argv) == 2 else BASE
ROOT = next(p for p in HERE.parents if (p / ".git").exists())


def host():
    return {
        "loadavg": Path("/proc/loadavg").read_text().strip(),
        "cpu_count": os.cpu_count(),
        "top_cpu_names": subprocess.check_output(
            ["ps", "-eo", "comm=,pcpu=", "--sort=-pcpu"], text=True
        ).splitlines()[:10],
    }


def run(name, argv):
    directory = HERE / name
    directory.mkdir()
    env = os.environ.copy()
    env.update(P5Q_C5A_EVIDENCE=str(directory / "c5a"),
               P5Q_C8_INVESTIGATION=str(directory / "c8"),
               RESTORE_DISCOVERY_EVIDENCE=str(directory / "discovery"))
    record = dict(argv=argv, before=host(),
                  started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    target = directory / "command.json"
    target.write_text(json.dumps(record, indent=2) + "\n")
    started = time.monotonic()
    with (directory / "stdout.log").open("w") as out:
        with (directory / "stderr.log").open("w") as err:
            result = subprocess.run(argv, cwd=ROOT, env=env, stdout=out, stderr=err)
    record.update(exit_code=result.returncode, elapsed_seconds=time.monotonic() - started,
                  after=host(),
                  finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    target.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"gate": name, "exit": result.returncode}), flush=True)
    return result.returncode


def main():
    os.chdir(ROOT)
    HERE.mkdir(exist_ok=True)
    sources = subprocess.check_output(["git", "ls-files", "-z"], text=True).split("\0")
    sources += [str(p.relative_to(ROOT)) for pattern in (
        "tizen-*/scripts/**/*.py", "tizen-*/scripts/**/*.mjs",
        "tests/unit/*discover*.py", "tests/unit/test_qb_collect.py",
        "tests/unit/test_campaign_restore_e2e.py", "tests/node/*discover*.mjs",
        "tests/node/elapsed_trace.mjs",
    ) for p in ROOT.glob(pattern)]
    hashes = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
              for p in sorted(set(sources)) if Path(p).is_file()
              and p.endswith((".py", ".mjs", "FROZEN.md"))}
    (HERE / "inputs.json").write_text(json.dumps(hashes, indent=2) + "\n")
    pytest = [".venv/bin/python", "tests/run_quiet.py"]
    focused = ["tests/unit/test_campaign_discovery.py", "tests/unit/test_qb_collect.py",
               "tests/unit/test_qb_discovery_node.py", "tests/unit/test_campaign_restore_e2e.py",
               "tests/unit/test_campaign_batch3_script.py"]
    if run("focused", [*pytest, *focused, "-q", f"--junitxml={HERE / 'focused/pytest.xml'}"]):
        return 4
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest() != h for p, h in hashes.items()):
        (HERE / "not-final.json").write_text('{"reason":"source_changed_before_full"}\n')
        return 4
    commands = {
        "mypy": [".venv/bin/mypy"],
        "ruff": [".venv/bin/ruff", "check", "--force-exclude",
                 *[p for p in hashes if p.endswith(".py")], str(Path(__file__).resolve())],
        "imports": [".venv/bin/lint-imports"],
        "design": [".venv/bin/python", "docs/clang-fix-campaign/tools/check_design_doc.py",
                   "docs/clang-fix-campaign/design.md"],
        "static": [*pytest, "tests/unit/test_qb_browser_node.py::"
                   "test_node_c2c_source_guard_mutations", "-q", "-s"],
        "safety": [*pytest, "tests/unit/test_qb_browser_node.py::"
                   "test_node_c2b_local_https_safety", "-q", "-s"],
        "collect": [".venv/bin/python", "-m", "pytest", "tests/", "--collect-only", "-q"],
    }
    for name, argv in commands.items():
        if run(name, argv):
            return 4
    result = run("full", [*pytest, "tests/", "-q", f"--junitxml={HERE / 'full/pytest.xml'}"])
    changed = [p for p, digest in hashes.items()
               if hashlib.sha256(Path(p).read_bytes()).hexdigest() != digest]
    (HERE / "integrity-after.json").write_text(json.dumps({"changed": changed}) + "\n")
    assert not changed
    return result


if __name__ == "__main__":
    sys.exit(main())
