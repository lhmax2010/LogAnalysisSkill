"""Capture local diagnostic commands and preserve, but never apply, unfinished edits."""

from __future__ import annotations

import datetime
import json
import os
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]
FILES = [
    "tizen-campaign-intake/scripts/tizen_campaign_intake/__main__.py",
    "tizen-review-submit/scripts/tizen_review_submit/__main__.py",
    "tizen-campaign-intake/scripts/tizen_campaign_intake/start_check.py",
    "tizen-review-submit/scripts/tizen_review_submit/review_submit.py",
    "tests/unit/test_campaign_batch3_start.py",
    "tests/unit/test_campaign_batch3_review.py",
    "tests/unit/test_campaign_batch3_e2e.py",
]


def run(name: str, argv: list[str]) -> None:
    directory = HERE / name
    directory.mkdir()
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    load = Path("/proc/loadavg").read_text().strip()
    with (directory / "stdout.log").open("wb") as out, (directory / "stderr.log").open("wb") as err:
        result = subprocess.run(argv, cwd=ROOT, stdout=out, stderr=err, check=False)
    (directory / "command.json").write_text(
        json.dumps(
            dict(
                argv=argv,
                start_utc=start,
                end_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                exit_code=result.returncode,
                cpu_count=os.cpu_count(),
                load_before=load,
                load_after=Path("/proc/loadavg").read_text().strip(),
            ),
            indent=2,
        )
        + "\n"
    )
    print(name, result.returncode, flush=True)


if __name__ == "__main__":
    chunks = []
    for filename in FILES:
        tracked = (
            subprocess.run(
                ["git", "ls-files", "--error-unmatch", filename],
                cwd=ROOT,
                capture_output=True,
                check=False,
            ).returncode
            == 0
        )
        argv = (
            ["git", "diff", "--", filename]
            if tracked
            else ["git", "diff", "--no-index", "--", "/dev/null", filename]
        )
        result = subprocess.run(argv, cwd=ROOT, capture_output=True, check=False)
        assert result.returncode in {0, 1}
        chunks.append(result.stdout)
    (HERE / "implementation-wip.patch").write_bytes(b"".join(chunks))
    run(
        "draft-focused",
        [
            ".venv/bin/pytest",
            "-q",
            "tests/unit/test_campaign_batch3_review.py",
            "tests/unit/test_campaign_batch3_start.py",
        ],
    )
    run("e2e-stop", [".venv/bin/pytest", "-xq", "tests/unit/test_campaign_batch3_e2e.py"])
    run("probe", [".venv/bin/pytest", "-q", "-s", str(HERE / "test_probe_handoff.py")])
