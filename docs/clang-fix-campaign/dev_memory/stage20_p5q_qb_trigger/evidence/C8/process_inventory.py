"""Process metadata only: distinguish owned P5Q trees from other browsers."""

import os
import subprocess
from pathlib import Path

from run_live import REPO

CHROMIUM = "/home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome"
AGENT = REPO / "tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs"


def inventory():
    result = subprocess.run(
        ["ps", "-eo", "pid=,ppid=,lstart=,comm="],
        env={**os.environ, "LC_ALL": "C", "TZ": "UTC"},
        text=True,
        capture_output=True,
        check=True,
    )
    metadata, own, browsers, errors = {}, set(), set(), []
    for line in result.stdout.splitlines():
        fields = line.split(maxsplit=7)
        pid, ppid = int(fields[0]), int(fields[1])
        if fields[7] not in {
            "node", "MainThread", "chrome", "chromium", "chromium-browse", "headless_shell"
        }:
            continue
        entry = Path("/proc") / str(pid)
        try:
            exe = os.readlink(entry / "exe")
        except (FileNotFoundError, ProcessLookupError):
            continue
        except PermissionError:
            # Kernel/system processes are not this user's browser processes.
            if entry.stat().st_uid == os.getuid():
                errors.append(dict(pid=pid, error="PROCESS_METADATA_UNREADABLE"))
            continue
        row = dict(pid=pid, ppid=ppid, exe=exe, started_utc=" ".join(fields[2:7]))
        metadata[pid] = row
        name = Path(exe).name
        if name in {"chrome", "chromium", "chromium-browser", "headless_shell"}:
            browsers.add(pid)
        if "playwright" in exe and name == "node":
            browsers.add(pid)
        if name != "node" and exe != CHROMIUM:
            continue
        try:
            # Only inspect argv in memory for ownership, never return/persist argv.
            args = os.fsdecode((entry / "cmdline").read_bytes()).split("\0")
            if name == "node":
                for arg in args[1:]:
                    if Path(arg).name != AGENT.name:
                        continue
                    candidate = Path(arg)
                    if not candidate.is_absolute():
                        candidate = Path(os.readlink(entry / "cwd")) / candidate
                    if candidate.resolve() == AGENT:
                        own.add(pid)
                        row["kind"] = "agent"
            elif any(arg.startswith("--user-data-dir=/dev/shm/p5q-browser-") for arg in args):
                own.add(pid)
                row["kind"] = "chromium"
        except (FileNotFoundError, ProcessLookupError):
            metadata.pop(pid, None)
            browsers.discard(pid)
            own.discard(pid)
        except PermissionError:
            errors.append(dict(pid=pid, error="OWNERSHIP_UNREADABLE"))
    while True:
        children = {pid for pid, row in metadata.items() if row["ppid"] in own}
        if children <= own:
            break
        own.update(children)
    for pid in own:
        metadata[pid].setdefault("kind", "chromium" if pid in browsers else "descendant")
    other = browsers - own
    for pid in other:
        root, parent = pid, metadata[pid]["ppid"]
        while parent in metadata:
            if parent in other:
                root = parent
            parent = metadata[parent]["ppid"]
        metadata[pid].update(
            root_pid=root,
            root_exe=metadata[root]["exe"],
            root_started_utc=metadata[root]["started_utc"],
        )
    return dict(
        own=[metadata[pid] for pid in sorted(own)],
        other=[metadata[pid] for pid in sorted(other)],
        errors=errors,
    )
