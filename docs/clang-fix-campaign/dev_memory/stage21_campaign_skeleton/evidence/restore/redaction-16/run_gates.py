"""RESTORE-16 offline gates; immutable command logs and final-tree hashes."""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[7]
HERE = Path(__file__).resolve().parent
OLD = HERE.parent / "redaction-12"


def host() -> dict[str, object]:
    return {"loadavg": Path("/proc/loadavg").read_text().strip(), "cpu_count": os.cpu_count(),
            "top_cpu_names": subprocess.check_output(
                ["ps", "-eo", "comm=,pcpu=", "--sort=-pcpu"], text=True
            ).splitlines()[:10]}


def utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def run(name: str, argv: list[str]) -> int:
    directory = HERE / name
    directory.mkdir()
    env = os.environ.copy()
    env["P5Q_C5A_EVIDENCE"] = str(directory / "c5a")
    env["P5Q_C8_INVESTIGATION"] = str(directory / "c8")
    record = {"argv": argv, "started_utc": utc(), "before": host()}
    target = directory / "command.json"
    target.write_text(json.dumps(record, indent=2) + "\n")
    started = time.monotonic()
    with (directory / "stdout.log").open("w") as out:
        with (directory / "stderr.log").open("w") as err:
            result = subprocess.run(argv, cwd=ROOT, env=env, stdout=out, stderr=err)
    record.update(exit_code=result.returncode, elapsed_seconds=time.monotonic() - started,
                  finished_utc=utc(), after=host())
    target.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"gate": name, "exit": result.returncode}), flush=True)
    return result.returncode


def main() -> int:
    os.chdir(ROOT)
    protected = json.loads((OLD / "integrity-final.json").read_text())
    for path, value in protected.items():
        if isinstance(value, dict):
            assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == value["sha256"]
    tracked = subprocess.check_output(["git", "ls-files", "-z"], text=True).split("\0")
    sources = {p for p in tracked if p.endswith((".py", ".mjs")) and Path(p).is_file()}
    sources.update(str(p.relative_to(ROOT)) for p in HERE.rglob("*.py"))
    sources.update({"tests/unit/test_restore_capture_archive.py", str(
        (HERE.parent / "discovery-capture/capture_archive.py").relative_to(ROOT))})
    hashes = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sorted(sources)}
    (HERE / "inputs.json").write_text(json.dumps({"protected": protected, "sources": hashes},
                                                indent=2) + "\n")
    pytest = [".venv/bin/python", "tests/run_quiet.py"]
    focused = ["tests/unit/test_restore_capture_redaction.py",
               "tests/unit/test_restore_capture_archive.py",
               "tests/unit/test_restore_capture_browser.py"]
    if run("focused", [*pytest, *focused, "-q", f"--junitxml={HERE / 'focused/pytest.xml'}"]):
        return 4
    for name in ("mypy", "ruff", "imports", "design"):
        argv = json.loads((OLD / name / "command.json").read_text())["argv"]
        if name == "ruff":
            argv += ["tests/unit/test_restore_capture_archive.py", str(Path(__file__).resolve()),
                     str(HERE.parent / "discovery-capture/capture_archive.py")]
        if run(name, argv):
            return 4
    if run("capture-ruff", [".venv/bin/ruff", "check", "--no-respect-gitignore",
                           str(HERE / "run_gates.py"),
                           str(HERE.parent / "discovery-capture/capture_archive.py"),
                           str(HERE.parent / "discovery-capture/redact_capture.py")]):
        return 4
    result = run("full", [*pytest, "tests/", "-q", f"--junitxml={HERE / 'full/pytest.xml'}"])
    unchanged = all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h
                    for p, h in hashes.items())
    (HERE / "integrity-after.json").write_text(json.dumps({"source_count": len(hashes),
                                                          "unchanged": unchanged}) + "\n")
    assert unchanged
    return result


if __name__ == "__main__":
    raise SystemExit(main())
