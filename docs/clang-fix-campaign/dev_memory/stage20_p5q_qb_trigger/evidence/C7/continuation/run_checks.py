"""Archive offline gates without changing the frozen inputs or live state DB."""

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
INPUTS = [
    ROOT / "docs/clang-fix-campaign/p5q-qb-trigger-design-v1.5-FROZEN.md",
    ROOT / "docs/clang-fix-campaign/p5q-qb-trigger-design-v1.8-FROZEN.md",
    Path("/home/linhao/Toolchain/p5q-live-validation/p5q-c6/state.db"),
]
AGENT = "tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs"


def audit():
    source = (ROOT / AGENT).read_bytes()
    baseline = subprocess.check_output(["git", "show", "48b0aa9:" + AGENT], cwd=ROOT)
    prefix = source.split(b"export class Agent {")[0]
    assert prefix == baseline.split(b"export class Agent {")[0]
    expected = baseline.replace(
        b"response = await this.page.goto(expected);",
        b"response = await this.page.goto(expected, { timeout: 30000 });",
    ).replace(
        "请在窗口中登录;登录后工具会自动继续。".encode(),
        "请在窗口中登录;若提示登录失败,可在窗口中重新输入;登录后工具会自动继续。".encode(),
    )
    assert source == expected
    return dict(
        hashes={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in INPUTS},
        protected_prefix_sha256=hashlib.sha256(prefix).hexdigest(),
        agent_only_two_authorized_edits=True,
    )


def main():
    label, *argv = sys.argv[1:]
    output = HERE / label
    output.mkdir()
    env = os.environ.copy()
    for key in ("QB_COOKIE", "QB_PASSWORD", "DEBUG", "PWDEBUG", "NODE_OPTIONS"):
        env.pop(key, None)
    env.update(P5Q_C5A_EVIDENCE=str(output / "cli-artifacts"))
    before = audit()
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    clock = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="p5q-c7-gate-") as export:
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
