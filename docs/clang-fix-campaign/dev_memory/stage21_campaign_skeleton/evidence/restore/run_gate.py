"""Archive offline gate output and load observations; never reinterpret failures."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def load() -> dict[str, object]:
    return {"loadavg": Path("/proc/loadavg").read_text().strip(), "cpu_count": os.cpu_count()}


def main() -> int:
    root = Path(__file__).resolve().parents[6]
    output = Path(sys.argv[1]).resolve()
    output.mkdir(parents=True, exist_ok=False)
    argv = sys.argv[2:]
    facts = {
        "argv": argv, "started_utc": datetime.now(timezone.utc).isoformat(),
        "load_before": load(),
        "top_cpu_names": subprocess.run(
            ["ps", "-eo", "comm,pcpu", "--sort=-pcpu"], capture_output=True, text=True, check=True
        ).stdout.splitlines()[:11],
    }
    env = os.environ.copy()
    env["P5Q_C8_INVESTIGATION"] = str(output / "c8")
    env["P5Q_C5A_EVIDENCE"] = str(output / "c5a")
    started = time.monotonic()
    with (output / "stdout.log").open("w") as stdout, (output / "stderr.log").open("w") as stderr:
        result = subprocess.run(argv, cwd=root, env=env, stdout=stdout, stderr=stderr)
    facts.update(
        exit_code=result.returncode, finished_utc=datetime.now(timezone.utc).isoformat(),
        elapsed_seconds=time.monotonic() - started, load_after=load(),
    )
    (output / "command.json").write_text(json.dumps(facts, indent=2) + "\n")
    print(json.dumps(facts))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
