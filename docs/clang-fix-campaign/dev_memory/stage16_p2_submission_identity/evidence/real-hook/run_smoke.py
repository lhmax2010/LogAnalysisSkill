"""Evidence-only smoke: observe the production generator, never replace its execution."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

from ci_triage import submission_identity as identity


def main() -> None:
    output_dir = Path(__file__).resolve().parent
    config = json.loads((output_dir.parent.parent / "real-hook-config.json").read_text())
    hook_path = Path(config["gerrit_commit_msg_hook"])
    hook_bytes = hook_path.read_bytes()
    assert hashlib.sha256(hook_bytes).hexdigest() == config["gerrit_commit_msg_hook_sha256"]
    message = "Fix build error\n\nP2 real hook smoke.\n"
    submission_key = identity.compute_submission_key(
        identity.build_submission_identity_key(
            ci_system="quickbuild",
            project="platform/example",
            branch="main",
            spec_name="example",
            base_commit="a" * 40,
        ),
        "b" * 40,
    )
    calls: list[dict[str, object]] = []
    completed: list[dict[str, object]] = []
    original_run = identity._run_isolated

    def observe(command: list[str], *, cwd: Path, env: dict[str, str]) -> None:
        calls.append({"argv": command, "cwd": str(cwd), "env": env})
        original_run(command, cwd=cwd, env=env)
        if command[0] == "sh":
            text = Path(command[2]).read_text()
            lines = [line for line in text.splitlines() if line.startswith("Change-Id:")]
            assert len(lines) == 1 and re.fullmatch(r"Change-Id: I[0-9a-f]{40}", lines[0])
            count = subprocess.check_output(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=cwd,
                env=env,
                text=True,
            ).strip()
            tree = subprocess.check_output(
                ["git", "ls-tree", "HEAD"],
                cwd=cwd,
                env=env,
                text=True,
            )
            assert count == "1" and tree == ""
            completed.append(
                {
                    "change_id_lines": lines,
                    "message_after_hook": text,
                    "initial_commit_count": count,
                    "initial_tree_listing": tree,
                    "executed_hook_sha256": hashlib.sha256(
                        Path(command[1]).read_bytes()
                    ).hexdigest(),
                }
            )

    with patch.object(identity, "_run_isolated", side_effect=observe):
        real_id = identity.generate_change_id_via_hook(
            hook_path=hook_path,
            hook_sha256=config["gerrit_commit_msg_hook_sha256"],
            submission_key=submission_key,
            message=message,
        )
    assert re.fullmatch(r"I[0-9a-f]{40}", real_id)
    assert completed[0]["change_id_lines"] == [f"Change-Id: {real_id}"]
    assert message == "Fix build error\n\nP2 real hook smoke.\n"
    assert completed[0]["executed_hook_sha256"] == config["gerrit_commit_msg_hook_sha256"]

    # Remove only the real hook's no-HEAD fallback, retaining all other bytes.
    old = (
        b"if git rev-parse --verify HEAD >/dev/null 2>&1; then\n"
        b'  refhash="$(git rev-parse HEAD)"\nelse\n'
        b'  refhash="$(git hash-object -t tree /dev/null)"\nfi\n'
    )
    new = b'refhash="$(git rev-parse --verify HEAD)" || exit 1\n'
    assert hook_bytes.count(old) == 1
    variant_bytes = hook_bytes.replace(old, new)
    variant_sha = hashlib.sha256(variant_bytes).hexdigest()
    with tempfile.TemporaryDirectory(prefix="p2-hook-head-control-") as temporary:
        root = Path(temporary)
        variant = root / "commit-msg-head-required"
        variant.write_bytes(variant_bytes)
        repo, home = root / "repo", root / "home"
        repo.mkdir()
        home.mkdir()
        env = {
            "PATH": os.environ.get("PATH", os.defpath),
            "LANG": "C",
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(home),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
        }
        for args in (
            ["init", "-q"],
            ["config", "--local", "user.name", "campaign"],
            ["config", "--local", "user.email", "campaign@invalid"],
            ["config", "--local", "gerrit.createChangeId", "true"],
        ):
            subprocess.run(["git", *args], cwd=repo, env=env, check=True)
        message_file = root / "message"
        message_file.write_text(f"{message}\nX-Campaign-Submission-Key: {submission_key}\n")
        no_head = subprocess.run(
            ["sh", str(variant), str(message_file)],
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert no_head.returncode == 1
        assert not any(
            line.startswith("Change-Id:") for line in message_file.read_text().splitlines()
        )
        with patch.object(identity, "_run_isolated", side_effect=observe):
            variant_id = identity.generate_change_id_via_hook(
                hook_path=variant,
                hook_sha256=variant_sha,
                submission_key=submission_key,
                message=message,
            )
        assert re.fullmatch(r"I[0-9a-f]{40}", variant_id)
        assert completed[1]["change_id_lines"] == [f"Change-Id: {variant_id}"]

    roots = {str(Path(str(call["cwd"])).parent) for call in calls}
    assert all(not Path(root).exists() for root in roots)
    assert hook_path.read_bytes() == hook_bytes
    result = {
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "hook_path": str(hook_path),
        "hook_sha256": config["gerrit_commit_msg_hook_sha256"],
        "submission_key": submission_key,
        "message_input": message,
        "real_change_id": real_id,
        "variant_change_id": variant_id,
        "variant_sha256": variant_sha,
        "variant_removed": old.decode(),
        "variant_added": new.decode(),
        "no_head_control": {
            "exit": no_head.returncode,
            "stdout": no_head.stdout,
            "stderr": no_head.stderr,
            "change_id_lines": 0,
        },
        "generator_calls": calls,
        "completed_hooks": completed,
        "temporary_directories_removed": sorted(roots),
        "hook_original_unchanged": True,
        "input_message_unchanged": True,
        "exit": 0,
    }
    (output_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(f"hook_sha256={config['gerrit_commit_msg_hook_sha256']}")
    print(f"Change-Id: {real_id}")
    print("real_hook: valid_change_id_lines=1; initial_commits=1; initial_tree_entries=0; exit=0")
    print(f"no_head_variant_without_initial_commit: exit={no_head.returncode}; change_id_lines=0")
    print(f"head_required_variant: Change-Id: {variant_id}; exit=0")
    print(
        "original_hook_unchanged=true; input_message_unchanged=true; "
        "temporary_directories_removed=true"
    )


if __name__ == "__main__":
    main()
