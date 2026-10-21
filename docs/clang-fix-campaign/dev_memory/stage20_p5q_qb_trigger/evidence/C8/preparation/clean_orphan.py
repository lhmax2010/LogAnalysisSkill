"""Remove one verified orphan socket directory, never follow or expose its link."""

import os
import shutil
import stat
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from prepare_c8 import immutable, write

PATH = Path("/dev/shm/p5q-browser-M9aRkY")


def main():
    immutable()
    info = PATH.lstat()
    assert stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
    paths = [PATH, *sorted(PATH.rglob("*"))]
    expected = {
        ".",
        "org.chromium.Chromium.PVos3b",
        "org.chromium.Chromium.PVos3b/SingletonSocket",
        "org.chromium.Chromium.PVos3b/SingletonCookie",
    }
    assert {str(p.relative_to(PATH)) for p in paths} == expected
    rows = []
    for p in paths:
        meta = p.lstat()
        assert meta.st_uid == os.getuid()
        assert (
            stat.S_ISDIR(meta.st_mode) or stat.S_ISSOCK(meta.st_mode) or stat.S_ISLNK(meta.st_mode)
        )
        rows.append(
            dict(
                path=str(p.relative_to(PATH)),
                mode=stat.filemode(meta.st_mode),
                size=meta.st_size,
                uid=meta.st_uid,
            )
        )
    refs = subprocess.run(
        ["lsof", "-nP", "-F", "p", "+D", str(PATH)], capture_output=True, text=True
    )
    assert refs.returncode == 1 and not refs.stdout and not refs.stderr
    assert PATH.lstat().st_ino == info.st_ino
    report = dict(
        path=str(PATH),
        entries=rows,
        lsof_exit=1,
        lsof_stdout="",
        lsof_stderr="",
        mtime=datetime.fromtimestamp(info.st_mtime, timezone.utc).isoformat(),
        action="ABOUT_TO_REMOVE",
        at=datetime.now(timezone.utc).isoformat(),
    )
    write("orphan-cleanup.json", report)
    shutil.rmtree(PATH)
    assert not PATH.exists()
    report.update(action="REMOVED", immutable=immutable())
    write("orphan-cleanup.json", report)


if __name__ == "__main__":
    main()
