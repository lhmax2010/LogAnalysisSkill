"""Serial evidence runner with RESTORE-27 resource limits; no business defaults."""

import datetime
import json
import os
import pathlib
import subprocess
import sys
import time


def resources():
    memory = pathlib.Path("/proc/meminfo").read_text()
    available = int(
        next(line.split()[1] for line in memory.splitlines() if line.startswith("MemAvailable:"))
    )
    load = pathlib.Path("/proc/loadavg").read_text().strip()
    return {
        "free_m": subprocess.check_output(["free", "-m"], text=True),
        "loadavg": load,
        "available_kib": available,
        "cpu_count": os.cpu_count(),
        "top_cpu_names": subprocess.check_output(
            ["ps", "-eo", "comm=,pcpu=", "--sort=-pcpu"], text=True
        ).splitlines()[:10],
    }


def main():
    output = pathlib.Path(sys.argv[1])
    output.mkdir(parents=True, exist_ok=False)
    command = sys.argv[2:]
    started = time.monotonic()
    samples = []
    code = 125
    record = {"argv": command, "samples": samples}
    try:
        while True:
            before = resources()
            samples.append({"elapsed": round(time.monotonic() - started, 3), **before})
            if (
                before["available_kib"] >= 6 * 1024 * 1024
                and float(before["loadavg"].split()[0]) <= 10
            ):
                break
            if time.monotonic() - started >= 1800:
                record["stop"] = "RESOURCE_WAIT_TIMEOUT"
                return code
            time.sleep(10)
        argv = [
            "systemd-run",
            "--user",
            "--scope",
            "-p",
            "CPUQuota=400%",
            "-p",
            "MemoryMax=6G",
            "-p",
            "MemorySwapMax=0",
            "nice",
            "-n",
            "10",
            *command,
        ]
        record.update(
            scope_argv=argv,
            before=before,
            wait_seconds=round(time.monotonic() - started, 3),
            start_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )
        env = os.environ.copy()
        env.update(
            P5Q_C5A_EVIDENCE=str(output.resolve() / "c5a"),
            P5Q_C8_INVESTIGATION=str(output.resolve() / "c8"),
            RESTORE_DISCOVERY_EVIDENCE=str(output.resolve() / "discovery"),
        )
        running = time.monotonic()
        with (output / "stdout.txt").open("x") as out, (output / "stderr.txt").open("x") as err:
            code = subprocess.run(argv, stdout=out, stderr=err, env=env, check=False).returncode
        record["elapsed_seconds"] = round(time.monotonic() - running, 3)
        record["end_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        return code
    finally:
        record.update(exit_code=code, after=resources())
        (output / "command.json").write_text(json.dumps(record, indent=2) + "\n")


if __name__ == "__main__":
    sys.exit(main())
