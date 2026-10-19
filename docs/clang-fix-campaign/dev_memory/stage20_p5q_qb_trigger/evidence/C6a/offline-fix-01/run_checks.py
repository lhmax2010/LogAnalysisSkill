"""Capture offline commands, outputs, timestamps and immutable input hashes."""

import datetime
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]
INPUTS = [
    ROOT / "docs/clang-fix-campaign/p5q-qb-trigger-design-v1.5-FROZEN.md",
    Path("/home/linhao/Toolchain/p5q-live-validation/p5q-c6/state.db"),
]


def main():
    label, *argv = sys.argv[1:]
    output = HERE / label
    output.mkdir()
    env = os.environ.copy()
    for key in ("QB_COOKIE", "QB_PASSWORD", "DEBUG", "PWDEBUG", "NODE_OPTIONS"):
        env.pop(key, None)
    env.update(
        P5Q_C6_FIX_EVIDENCE=str(output / "artifacts"),
        P5Q_C5A_EVIDENCE=str(output / "cli-artifacts"),
        P5Q_C6_DIAG_EVIDENCE=str(output / "diagnostic-artifacts"),
    )
    before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in INPUTS}
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    clock = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="p5q-offline-gate-") as export:
        if argv == ["@ruff-index"]:
            subprocess.run(["git", "checkout-index", "--all", f"--prefix={export}/"],
                           cwd=ROOT, check=True)
            argv = [str(ROOT / ".venv/bin/ruff"), "check", "."]
            cwd = Path(export)
        else:
            cwd = ROOT
        with (output / "output.log").open("wb") as log:
            result = subprocess.run(argv, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT)
    record = dict(
        argv=argv, cwd=str(cwd), started=started,
        ended=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        seconds=round(time.monotonic() - clock, 3), exit=result.returncode,
        input_hashes_before=before,
        input_hashes_after={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in INPUTS},
    )
    (output / "command.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record), flush=True)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
