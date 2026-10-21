"""Capture C8 offline gates and immutable input hashes."""

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
ROOT = Path(__file__).resolve().parents[7]
AGENT = "tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs"
DESIGN = ROOT / "docs/clang-fix-campaign"
INPUTS = {
    DESIGN / "p5q-qb-trigger-design-v1.5-FROZEN.md": (
        "f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c"
    ),
    DESIGN / "p5q-qb-trigger-design-v1.8-FROZEN.md": (
        "d0242ca8b708e9c1e3e714387bae963f8f6f16fc765179e6ed60d8be56493364"
    ),
    Path(
        "/home/linhao/Toolchain/p5q-live-validation/p5q-c6/state.db"
    ): "08ed202e69a73a480e7282a198565f32adae8157a332804df4df970238eacd30",
}


def audit():
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in INPUTS}
    assert hashes == {str(p): expected for p, expected in INPUTS.items()}
    source = (ROOT / AGENT).read_bytes()
    assert source == subprocess.check_output(["git", "show", "0b27c49:" + AGENT], cwd=ROOT)
    prefix = hashlib.sha256(source.split(b"export class Agent {")[0]).hexdigest()
    assert prefix == "40f8f22bd0f5f4078b6012083c457a7b423e52fd69e5603f03dfc7a09d363a16"
    return dict(hashes=hashes, protected_prefix_sha256=prefix, agent_unchanged=True)


def main():
    label, *argv = sys.argv[1:]
    output = HERE / label
    output.mkdir()
    env = os.environ.copy()
    for key in ("QB_COOKIE", "QB_PASSWORD", "DEBUG", "PWDEBUG", "NODE_OPTIONS"):
        env.pop(key, None)
    env["P5Q_C5A_EVIDENCE"] = str(output / "cli-artifacts")
    before = audit()
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    clock = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="p5q-c8-gate-") as export:
        cwd = ROOT
        if argv == ["@ruff-index"]:
            subprocess.run(
                ["git", "checkout-index", "--all", f"--prefix={export}/"], cwd=ROOT, check=True
            )
            argv = [str(ROOT / ".venv/bin/ruff"), "check", "."]
            cwd = Path(export)
        with (output / "output.log").open("wb") as stream:
            result = subprocess.run(argv, cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT)
    record = dict(
        argv=argv,
        cwd=str(cwd),
        started=started,
        ended=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        seconds=round(time.monotonic() - clock, 3),
        exit=result.returncode,
        before=before,
        after=audit(),
    )
    assert record["before"] == record["after"]
    (output / "command.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record), flush=True)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
