#!/usr/bin/env python3
"""Test-only SSH transport to a contained local bare repository."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import sys
from pathlib import Path, PurePosixPath


def main() -> int:
    args = sys.argv[1:]
    while args and args[0] in ("-p", "-o"):
        if len(args) < 2:
            return 2
        flag, value = args[:2]
        if (flag == "-p" and value != "29418") or (
            flag == "-o" and value != "SendEnv=GIT_PROTOCOL"
        ):
            return 2
        args = args[2:]
    if len(args) != 2 or args[0] != "gerrit.invalid":
        return 2
    try:
        command = shlex.split(args[1])
        if len(command) != 2 or command[0] not in ("git-upload-pack", "git-receive-pack"):
            return 2
        relative = PurePosixPath(command[1])
        if ".." in relative.parts or "\\" in command[1]:
            return 2
        root = Path(os.environ["SKEL_FAKE_SSH_ROOT"]).resolve(strict=True)
        target = (root / str(relative).lstrip("/")).resolve(strict=True)
        if not target.is_relative_to(root) or target == root or not target.is_dir():
            return 2
        executable = shutil.which(command[0])
        if executable is None:
            return 2
        if log := os.environ.get("SKEL_FAKE_SSH_LOG"):
            with Path(log).open("a", encoding="utf-8") as stream:
                stream.write(json.dumps({"command": command[0], "path": str(target)}) + "\n")
        os.execv(executable, [executable, str(target)])
    except (KeyError, OSError, ValueError):
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
