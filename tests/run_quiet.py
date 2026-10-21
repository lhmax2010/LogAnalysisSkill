"""Run pytest on a private virtual display, without changing production Chromium."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def command(args: list[str]) -> tuple[list[str], dict[str, str]]:
    env = os.environ.copy()
    local = Path.home() / ".local/share/p5q-test-display/usr/bin"
    path = env.get("PATH", os.defpath)
    if local.is_dir():
        path = f"{local}{os.pathsep}{path}"
    runner = shutil.which("xvfb-run", path=path)
    if not runner or not shutil.which("Xvfb", path=path) or not shutil.which("xauth", path=path):
        raise RuntimeError("Xvfb/xvfb-run/xauth required; refusing desktop browser fallback")
    env["PATH"] = path
    env["P5Q_TEST_DISPLAY"] = "virtual"
    # Only the child test process receives these changes. Real login keeps its desktop.
    for key in ("DISPLAY", "WAYLAND_DISPLAY", "XAUTHORITY"):
        env.pop(key, None)
    env["XDG_SESSION_TYPE"] = "x11"
    return [
        runner,
        "--auto-servernum",
        "--error-file=/dev/stderr",
        "--server-args=-screen 0 1920x1080x24 -nolisten tcp",
        sys.executable,
        "-m",
        "pytest",
        *args,
    ], env


def main() -> int:
    try:
        argv, env = command(sys.argv[1:])
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 2
    os.execvpe(argv[0], argv, env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
