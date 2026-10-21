"""Offline delivery checks; no browser, network or state DB writes."""

import hashlib
import json
import subprocess
from pathlib import Path

from ci_triage.qb_browser import _check_diagnostic_strings
from ci_triage.qb_redact import PageRedactor
from run_live import HERE, PREP, REPO, ROOT, write


def main():
    assert PREP.digest(ROOT / "state.db") == (
        "c346b6b8d065ad14a5dbab2bb9e9d66f370234e8ac73133426789002075b2c63"
    )
    assert not (HERE / "live-02/fetch").exists()
    assert not (HERE / "live-02/preflight-passed.json").exists()
    profiles = [str(path) for path in Path("/dev/shm").glob("p5q-browser-*")]
    transports = [str(path) for path in ROOT.rglob(".transport")]
    assert not profiles and not transports
    source = (REPO / "tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs").read_bytes()
    prefix = hashlib.sha256(source.split(b"export class Agent {")[0]).hexdigest()
    assert prefix == "40f8f22bd0f5f4078b6012083c457a7b423e52fd69e5603f03dfc7a09d363a16"
    raw_log = str((HERE / "investigation/navigation-01/pytest.xml").relative_to(REPO))
    raw_diff = subprocess.run(
        ["git", "diff", "--cached", "--check"], cwd=REPO, text=True, capture_output=True
    )
    assert raw_diff.returncode == 2
    assert raw_diff.stdout == f"{raw_log}:10: trailing whitespace.\n+E     \n"
    assert not raw_diff.stderr
    commands = [
        [
            ".venv/bin/ruff",
            "check",
            str(HERE / "run_read_recovery.py"),
            str(Path(__file__)),
            str(HERE / "investigation/history.py"),
            "tests/unit/test_p5q_c8_investigation.py",
        ],
        ["/home/linhao/.local/bin/node", "--check", "tests/node/p5q_c8_investigation.mjs"],
        ["/home/linhao/.local/bin/node", "--check", "tests/node/p5q_fake_quickbuild.mjs"],
        ["/home/linhao/.local/bin/node", "--test", "tests/node/test_qb_agent_source_guards.mjs"],
        [
            ".venv/bin/python",
            "docs/clang-fix-campaign/tools/check_design_doc.py",
            "docs/clang-fix-campaign/design.md",
        ],
        ["git", "diff", "--exit-code", "9a688a0", "--", "tizen-ci-triage/scripts/ci_triage"],
        ["git", "diff", "--check", "--", "tests", "docs/clang-fix-campaign/dev_memory"],
        ["git", "diff", "--cached", "--check", "--", ".", f":!{raw_log}"],
    ]
    gates = []
    for command in commands:
        started = PREP.stamp()
        result = subprocess.run(command, cwd=REPO, text=True, capture_output=True)
        gates.append(
            dict(
                argv=command,
                started=started,
                ended=PREP.stamp(),
                exit=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        )
        assert result.returncode == 0, result.stdout
    files = []
    checker = PageRedactor()
    for directory in (HERE / "live-02", HERE / "investigation"):
        for path in sorted(directory.rglob("*")):
            if not path.is_file() or path.name == "audit-final.json" or "__pycache__" in path.parts:
                continue
            raw = path.read_bytes()
            checker.check_bytes(raw)
            if path.suffix == ".json":
                _check_diagnostic_strings(json.loads(raw), checker)
            files.append(dict(path=str(path.relative_to(HERE)), sha256=PREP.digest(path)))
    report = dict(
        at=PREP.stamp(),
        immutable=PREP.immutable(),
        c6_tree_unchanged=True,
        c8_db_sha256=PREP.digest(ROOT / "state.db"),
        protected_prefix_sha256=prefix,
        p5q_profiles=profiles,
        transports=transports,
        gates=gates,
        raw_staged_diff_check=dict(
            exit=raw_diff.returncode,
            stdout=raw_diff.stdout,
            stderr=raw_diff.stderr,
            exception=(
                "Original failed JUnit evidence retained byte-for-byte; only this file excluded"
            ),
        ),
        files=files,
        redaction_failures=0,
        real_qb_commands=0,
        live_result="PREFLIGHT_STOPPED",
    )
    write(HERE / "investigation/audit-final.json", report)
    print(json.dumps(dict(audit="PASS", files=len(files), gates=len(gates))))


if __name__ == "__main__":
    main()
