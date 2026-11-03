"""Verify the stopped tree without running network or browser commands."""

from __future__ import annotations

import hashlib
import json
import subprocess

from capture import HERE, ROOT, run


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


if __name__ == "__main__":
    run(
        "restored-probe-final",
        [".venv/bin/pytest", "-q", "-s", str(HERE / "test_probe_handoff.py")],
    )
    run("collect-final", [".venv/bin/pytest", "--collect-only", "-q"])
    run(
        "design-final",
        [
            ".venv/bin/python",
            "docs/clang-fix-campaign/tools/check_design_doc.py",
            "docs/clang-fix-campaign/design.md",
        ],
    )
    run(
        "ruff-evidence-final",
        [
            ".venv/bin/ruff",
            "check",
            str(HERE / "capture.py"),
            str(HERE / "checks.py"),
            str(HERE / "test_probe_handoff.py"),
        ],
    )
    baseline_path = HERE.parents[1] / "batch2/implementation/nodeids-final.txt"
    before = set(baseline_path.read_text().splitlines())
    after = {
        line
        for line in (HERE / "collect-final/stdout.log").read_text().splitlines()
        if line.startswith("tests/") and "::" in line
    }
    (HERE / "nodeids-final.txt").write_text("\n".join(sorted(after)) + "\n")
    files = [
        "docs/clang-fix-campaign/campaign-skeleton-design-v1.3-FROZEN.md",
        "tizen-qb-verify/scripts/tizen_qb_verify/qb_browser_agent.mjs",
        "tizen-ci-shared/scripts/tizen_ci_shared/state/db.py",
        "tizen-ci-shared/scripts/tizen_ci_shared/state/keys.py",
        "tizen-ci-shared/scripts/tizen_ci_shared/state/records.py",
        "tizen-build-verify/scripts/tizen_build_verify/build_verify.py",
        "tizen-campaign-core/scripts/tizen_campaign_core/_campaign_workspace.py",
        "tizen-qb-verify/scripts/tizen_qb_verify/qb_result_fetch.py",
        "tizen-campaign-core/scripts/tizen_campaign_core/campaign_state.py",
    ]
    integrity = {}
    for name in files:
        old = subprocess.run(
            ["git", "show", "0417ff3:" + name], cwd=ROOT, check=True, capture_output=True
        ).stdout
        current = (ROOT / name).read_bytes()
        integrity[name] = dict(before=digest(old), after=digest(current), identical=old == current)
    agent = (ROOT / files[1]).read_bytes()
    marker = b"export class Agent {"
    prefix = agent[: agent.index(marker)]
    changes = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "--",
            "tests",
            *[p.name for p in ROOT.glob("tizen-*") if p.is_dir()],
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    facts = dict(
        baseline_nodeids=len(before),
        current_nodeids=len(after),
        removed=sorted(before - after),
        added=sorted(after - before),
        integrity=integrity,
        agent_prefix_sha256=digest(prefix),
        production_or_old_test_changes=changes,
        checks={
            name: json.loads((HERE / name / "command.json").read_text())["exit_code"]
            for name in (
                "restored-probe-final",
                "collect-final",
                "design-final",
                "ruff-evidence-final",
            )
        },
        full_pytest="NOT_RUN",
        mypy="NOT_RUN",
        import_linter="NOT_RUN",
        safety_groups="NOT_RUN",
    )
    (HERE / "checks.json").write_text(json.dumps(facts, indent=2) + "\n")
    assert before == after and len(after) == 3028
    assert digest(prefix) == "40f8f22bd0f5f4078b6012083c457a7b423e52fd69e5603f03dfc7a09d363a16"
    assert all(item["identical"] for item in integrity.values())
    assert not changes and all(code == 0 for code in facts["checks"].values())
