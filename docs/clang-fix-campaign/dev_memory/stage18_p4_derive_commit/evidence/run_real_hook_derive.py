"""Offline P2-to-P4 handoff using the registered real Gerrit commit-msg hook."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

from ci_triage.derive_commit import derive
from ci_triage.submission_identity import generate_change_id_via_hook


def main() -> None:
    output = Path(__file__).resolve().parent
    config_path = output.parents[1] / "stage16_p2_submission_identity/real-hook-config.json"
    config = json.loads(config_path.read_text())
    hook = Path(config["gerrit_commit_msg_hook"])
    hook_bytes = hook.read_bytes()
    digest = hashlib.sha256(hook_bytes).hexdigest()
    assert digest == config["gerrit_commit_msg_hook_sha256"]
    message = "Fix build error for clang compiler: missing include\n\nRestore declaration.\n"
    calls = []
    with tempfile.TemporaryDirectory(prefix="p4-real-hook-") as directory:
        root = Path(directory)
        repo, home = root / "repo", root / "home"
        repo.mkdir()
        home.mkdir()
        env = {
            "PATH": os.environ.get("PATH", os.defpath), "LANG": "C", "HOME": str(home),
            "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
        }

        def git(*args: str, payload: str | None = None) -> str:
            result = subprocess.run(["git", "-C", str(repo), *args], env=env,
                                    input=payload, capture_output=True, text=True, check=True)
            calls.append({"argv": ["git", "-C", str(repo), *args], "exit": result.returncode})
            return result.stdout

        git("init", "-q")
        git("config", "user.name", "P4 smoke")
        git("config", "user.email", "p4@invalid")
        (repo / "source.c").write_text("base\n")
        git("add", "source.c")
        git("commit", "-qm", "base")
        parent = git("rev-parse", "HEAD").strip()
        (repo / "source.c").write_text("verified\n")
        git("add", "source.c")
        tree = git("write-tree").strip()
        (repo / "source.c").write_text("unstaged preserved\n")
        before_index = (repo / ".git/index").read_bytes()
        before_worktree = (repo / "source.c").read_bytes()
        objects = sorted(str(p) for p in (repo / ".git/objects").rglob("*") if p.is_file())
        change_id = generate_change_id_via_hook(
            hook_path=hook, hook_sha256=digest, submission_key="b" * 64, message=message,
        )
        assert re.fullmatch(r"I[0-9a-f]{40}", change_id)
        assert objects == sorted(
            str(p) for p in (repo / ".git/objects").rglob("*") if p.is_file()
        )
        final_message = message + f"\nChange-Id: {change_id}\n"
        commit = derive(repo, tree, parent, final_message,
                        "P4 Author <author@invalid>", "P4 Committer <committer@invalid>",
                        "2026-10-08T00:00:00+00:00", "2026-10-08T01:00:00+00:00")
        actual_message = git("cat-file", "commit", commit).split("\n\n", 1)[1]
        actual_tree = git("rev-parse", f"{commit}^{{tree}}").strip()
        trailers = git("interpret-trailers", "--parse", payload=actual_message).splitlines()
        assert actual_message == final_message
        assert trailers == [f"Change-Id: {change_id}"]
        assert actual_message.splitlines().count(f"Change-Id: {change_id}") == 1
        assert "X-Campaign-Submission-Key" not in actual_message
        assert actual_tree == tree and git("rev-parse", "HEAD").strip() == parent
        assert (repo / ".git/index").read_bytes() == before_index
        assert (repo / "source.c").read_bytes() == before_worktree
        assert hook.read_bytes() == hook_bytes
        result_data = {
            "hook_path": str(hook), "hook_sha256": digest, "change_id": change_id,
            "input_message": message, "final_message": final_message,
            "actual_message": actual_message, "trailers": trailers, "commit": commit,
            "input_tree": tree, "actual_tree": actual_tree, "parent": parent,
            "workspace_unchanged": True, "index_unchanged": True, "head_unchanged": True,
            "index_sha256": hashlib.sha256(before_index).hexdigest(),
            "setup_and_observation_calls": calls, "exit": 0,
        }
    (output / "real-hook-derive.json").write_text(json.dumps(result_data, indent=2) + "\n")
    print(f"hook_sha256={digest}")
    print(f"Change-Id: {change_id}")
    print(f"commit={commit}; input_tree={tree}; actual_tree={actual_tree}")
    print("change_id_trailers=1; auxiliary_lines=0; workspace/index/HEAD unchanged; exit=0")


if __name__ == "__main__":
    main()
