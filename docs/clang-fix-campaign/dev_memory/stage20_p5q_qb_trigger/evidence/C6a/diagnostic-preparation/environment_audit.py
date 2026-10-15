"""Record environment metadata; remove only unreferenced owned browser profiles."""

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from ci_triage.qb_redact import PageRedactor

HERE = Path(__file__).resolve().parent
DB = Path("/home/linhao/Toolchain/p5q-live-validation/p5q-c6/state.db")
EXPECTED = "bd4380eacf2409c40137ad8b648939261b3a3eebe20d4101a6e2269b2c4eb405"


def command(argv):
    result = subprocess.run(argv, capture_output=True, text=True, check=False)
    return dict(argv=argv, exit=result.returncode, stdout=result.stdout, stderr=result.stderr)


def references(path):
    run = command(["lsof", "-nP", "-F", "p", "+D", str(path)])
    pids = sorted({int(line[1:]) for line in run["stdout"].splitlines() if line.startswith("p")})
    # Warnings or inability to inspect are not evidence of absence.
    return dict(
        pids=pids, exit=run["exit"], uncertain=bool(run["stderr"]) or run["exit"] not in {0, 1}
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    before = hashlib.sha256(DB.read_bytes()).hexdigest()
    assert before == EXPECTED
    report = dict(
        started_at=datetime.now(timezone.utc).isoformat(),
        db_sha256_before=before,
        commands=[command(["df", "-h", "/dev/shm", "/home"]), command(["free", "-h"])],
        profiles=[],
        d_samples=[],
    )
    for index in range(3):
        if index:
            time.sleep(10)
        output = command(["ps", "-eo", "state,pid,comm"])
        rows = [line for line in output["stdout"].splitlines() if line.split()[:1] == ["D"]]
        details = []
        for row in rows:
            _, pid, name = row.split(maxsplit=2)
            try:
                wchan = (Path("/proc") / pid / "wchan").read_text().strip()
            except OSError:
                wchan = "UNAVAILABLE"
            details.append(dict(pid=int(pid), name=name, wchan=wchan))
        report["d_samples"].append(
            dict(
                at=datetime.now(timezone.utc).isoformat(),
                argv=output["argv"],
                exit=output["exit"],
                count=len(rows),
                rows=rows,
                details=details,
            )
        )
    for path in sorted(Path("/dev/shm").glob("p5q-browser-*")):
        info = path.lstat()
        row = dict(
            path=str(path),
            uid=info.st_uid,
            inode=info.st_ino,
            mtime=datetime.fromtimestamp(info.st_mtime, timezone.utc).isoformat(),
            size=command(["du", "-sb", str(path)]),
            references=references(path),
            deletion="NOT_REQUESTED",
        )
        report["profiles"].append(row)
        if args.clean:
            fresh = references(path)
            row["pre_delete_references"] = fresh
            current = path.lstat()
            if (
                info.st_uid != os.getuid()
                or not stat.S_ISDIR(info.st_mode)
                or current.st_ino != info.st_ino
                or fresh["pids"]
                or fresh["uncertain"]
                or row["references"]["pids"]
                or row["references"]["uncertain"]
            ):
                row["deletion"] = "RETAINED_NOT_PROVEN_UNREFERENCED"
            else:
                # Persist metadata before the explicitly authorized deletion.
                row["deletion"] = "ABOUT_TO_REMOVE"
                write(args.output, report)
                try:
                    shutil.rmtree(path)
                    row["deletion"] = "REMOVED" if not path.exists() else "STILL_EXISTS"
                except OSError as error:
                    row["deletion"] = type(error).__name__
    report["db_sha256_after"] = hashlib.sha256(DB.read_bytes()).hexdigest()
    assert report["db_sha256_after"] == EXPECTED
    report["ended_at"] = datetime.now(timezone.utc).isoformat()
    write(args.output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def write(path, report):
    raw = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode()
    redactor = PageRedactor()
    redactor.check_bytes(raw)
    path.write_bytes(raw)
    redactor.check_written(path)


if __name__ == "__main__":
    main()
