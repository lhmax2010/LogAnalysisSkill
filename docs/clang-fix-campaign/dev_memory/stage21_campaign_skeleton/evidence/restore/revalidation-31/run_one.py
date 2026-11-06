"""RESTORE-31 serial resource gate and evidence runner; no live services."""

import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def resources():
    memory = dict(line.split(":", 1) for line in Path("/proc/meminfo").read_text().splitlines())
    return {
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "available_kib": int(memory["MemAvailable"].split()[0]),
        "swap_free_kib": int(memory["SwapFree"].split()[0]),
        "loadavg": Path("/proc/loadavg").read_text().strip(),
        "free_m": subprocess.check_output(["free", "-m"], text=True),
        "cpu_count": os.cpu_count(),
        "top_cpu_names": subprocess.check_output(
            ["ps", "-eo", "comm=,pcpu=", "--sort=-pcpu"], text=True
        ).splitlines()[:10],
    }


def main():
    output = Path(sys.argv[1]).resolve()
    output.mkdir(parents=True, exist_ok=False)
    command = sys.argv[2:]
    start = time.monotonic()
    record = {"argv": command, "samples": [], "started": False,
              "limits": {"available_kib": 6291456, "load1_max": 4,
                         "swap_free_kib": 524288, "wait_max_seconds": 1800}}

    def save():
        (output / "command.json").write_text(json.dumps(record, indent=2) + "\n")

    while True:
        sample = resources()
        elapsed = time.monotonic() - start
        record["samples"].append({"wait_seconds": round(elapsed, 3), **sample})
        save()
        ready = (sample["available_kib"] >= 6291456
                 and sample["swap_free_kib"] >= 524288
                 and float(sample["loadavg"].split()[0]) <= 4)
        if elapsed >= 1800:
            record.update(stop="RESOURCE_WAIT_TIMEOUT", exit_code=125,
                          wait_seconds=round(elapsed, 3), after=sample)
            save()
            return 125
        if ready:
            break
        time.sleep(min(10, 1800 - elapsed))
    scope = ["systemd-run", "--user", "--scope", "-p", "CPUQuota=400%",
             "-p", "MemoryMax=6G", "-p", "MemorySwapMax=0", "nice", "-n", "10",
             *command]
    env = os.environ.copy()
    env.update(P5Q_C5A_EVIDENCE=str(output / "c5a"), P5Q_C8_INVESTIGATION=str(output / "c8"))
    record.update(before=sample, scope_argv=scope, wait_seconds=round(elapsed, 3),
                  start_utc=sample["utc"], started=True)
    save()
    with (output / "stdout.txt").open("x") as stdout, (output / "stderr.txt").open("x") as stderr:
        result = subprocess.run(scope, env=env, stdout=stdout, stderr=stderr, check=False)
    record.update(exit_code=result.returncode, after=resources(),
                  end_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    save()
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
