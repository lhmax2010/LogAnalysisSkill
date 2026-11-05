"""RESTORE-14 evidence runner. Uses only existing offline gate entry points."""

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
NODEID = (
    "tests/unit/test_qb_browser_node.py::"
    "test_node_c2c_trusted_reads_and_fields[test_qb_browser_fields.mjs]"
)


def host() -> dict[str, object]:
    return {
        "loadavg": Path("/proc/loadavg").read_text().strip(),
        "cpu_count": os.cpu_count(),
        "top_cpu_names": subprocess.check_output(
            ["ps", "-eo", "comm=,pcpu=", "--sort=-pcpu"], text=True
        ).splitlines()[:10],
    }


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
    assert (ROOT / "pyproject.toml").is_file()
    os.chdir(ROOT)
    protected = json.loads((HERE.parent / "redaction-12/integrity-final.json").read_text())
    for name, value in protected.items():
        if isinstance(value, dict):
            assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == value["sha256"]
    old = HERE.parent / "redaction-12"
    old_hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in sorted(old.rglob("*")) if p.is_file()}
    tracked = subprocess.check_output(["git", "ls-files", "-z"], text=True).split("\0")
    source_hashes = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in tracked
                     if p.endswith((".py", ".mjs")) and Path(p).is_file()}
    (HERE / "inputs.json").write_text(json.dumps({
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "old_evidence": old_hashes, "sources": source_hashes, "protected": protected,
    }, indent=2) + "\n")
    pytest = [".venv/bin/python", "tests/run_quiet.py"]
    for index in range(1, 4):
        name = f"fields-rerun-{index:02d}"
        if run(name, [*pytest, NODEID, "-q", f"--junitxml={HERE / name / 'pytest.xml'}"]):
            return 4
    full = run("full", [*pytest, "tests/", "-q", f"--junitxml={HERE / 'full/pytest.xml'}"])
    if full:
        # The model applies the ruling to exact failing nodeids; never auto-retry all tests.
        return full
    for name in ("mypy", "ruff", "imports", "design"):
        command = json.loads((old / name / "command.json").read_text())["argv"]
        if name == "ruff":
            command.append(str(Path(__file__).resolve()))
        if run(name, command):
            return 4
    for name, digest in source_hashes.items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest
    for name, digest in old_hashes.items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest
    (HERE / "unchanged-after.json").write_text(json.dumps({
        "sources_unchanged": len(source_hashes), "old_evidence_unchanged": len(old_hashes),
    }, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
