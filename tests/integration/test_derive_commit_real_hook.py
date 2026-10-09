from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

import pytest
from ci_triage.derive_commit import derive
from ci_triage.submission_identity import generate_change_id_via_hook

pytestmark = pytest.mark.integration


def test_registered_real_hook_then_derive(tmp_path: Path) -> None:
    config_path = Path(__file__).resolve().parents[2] / (
        "docs/clang-fix-campaign/dev_memory/stage16_p2_submission_identity/real-hook-config.json"
    )
    if not config_path.is_file():
        pytest.skip("P2 real hook configuration is absent; not verified")
    config = json.loads(config_path.read_text())
    hook = Path(config["gerrit_commit_msg_hook"])
    if not hook.is_file():
        pytest.skip("P2 registered real hook file is absent; not verified")
    hook_bytes = hook.read_bytes()
    digest = hashlib.sha256(hook_bytes).hexdigest()
    if digest != config["gerrit_commit_msg_hook_sha256"]:
        pytest.skip("P2 registered real hook SHA256 mismatch; not verified")
    repo, home = tmp_path / "repo", tmp_path / "home"
    repo.mkdir()
    home.mkdir()
    env = {
        "PATH": os.environ.get("PATH", os.defpath), "LANG": "C", "HOME": str(home),
        "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
    }

    def git(*args: str, payload: str | None = None) -> str:
        return subprocess.run(["git", "-C", str(repo), *args], env=env, input=payload,
                              capture_output=True, text=True, check=True).stdout

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
    message = "Fix build error for clang compiler: missing include\n\nRestore declaration.\n"
    change_id = generate_change_id_via_hook(
        hook_path=hook, hook_sha256=digest, submission_key="b" * 64, message=message,
    )
    assert re.fullmatch(r"I[0-9a-f]{40}", change_id)
    assert objects == sorted(str(p) for p in (repo / ".git/objects").rglob("*") if p.is_file())
    final_message = message + f"\nChange-Id: {change_id}\n"
    commit = derive(repo, tree, parent, final_message,
                    "P4 Author <author@invalid>", "P4 Committer <committer@invalid>",
                    "2026-10-08T00:00:00+00:00", "2026-10-08T01:00:00+00:00")
    actual_message = git("cat-file", "commit", commit).split("\n\n", 1)[1]
    assert actual_message == final_message
    assert git("interpret-trailers", "--parse", payload=actual_message).splitlines() == [
        f"Change-Id: {change_id}"
    ]
    assert actual_message.splitlines().count(f"Change-Id: {change_id}") == 1
    assert "X-Campaign-Submission-Key" not in actual_message
    assert git("rev-parse", f"{commit}^{{tree}}").strip() == tree
    assert git("rev-parse", "HEAD").strip() == parent
    assert (repo / ".git/index").read_bytes() == before_index
    assert (repo / "source.c").read_bytes() == before_worktree
    assert hook.read_bytes() == hook_bytes
