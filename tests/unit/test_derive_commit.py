from __future__ import annotations

import hashlib
import os
import subprocess
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest
from ci_triage import derive_commit
from ci_triage.submission_identity import generate_change_id_via_hook

AUTHOR = "Campaign Author <author@invalid>"
COMMITTER = "Campaign Committer <committer@invalid>"
AUTHOR_DATE = "2026-10-08T00:00:00+00:00"
COMMITTER_DATE = "2026-10-08T01:00:00+00:00"
CHANGE_ID = "I" + "a" * 40
MESSAGE = (
    "Fix build error for clang compiler: missing include\n"
    "\nRestore the declaration required by clang.\n"
    f"\nChange-Id: {CHANGE_ID}\n"
)


def _git(repo: Path, *args: str) -> str:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull})
    return subprocess.run(["git", "-C", str(repo), *args], env=env, check=True,
                          capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> tuple[Path, str, str]:
    path = tmp_path / "repo"
    path.mkdir()
    _git(path, "init", "-q")
    _git(path, "config", "user.name", "Initial")
    _git(path, "config", "user.email", "initial@invalid")
    _git(path, "commit", "--allow-empty", "-qm", "root")
    (path / "source.c").write_text("base\n")
    _git(path, "add", "source.c")
    _git(path, "commit", "-qm", "base")
    parent = _git(path, "rev-parse", "HEAD")
    (path / "source.c").write_text("verified\n")
    _git(path, "add", "source.c")
    tree = _git(path, "write-tree")
    (path / "source.c").write_text("staged but not verified\n")
    _git(path, "add", "source.c")
    (path / "source.c").write_text("unstaged\n")
    (path / "untracked").write_bytes(b"preserve\x00bytes")
    (path / "link").symlink_to("source.c")
    return path, tree, parent


def _snapshot(path: Path) -> dict[str, object]:
    entries: dict[str, object] = {}
    for item in path.rglob("*"):
        rel = item.relative_to(path)
        if ".git" in rel.parts:
            continue
        stat = item.lstat()
        entries[str(rel)] = (stat.st_mode, stat.st_mtime_ns,
                             os.readlink(item) if item.is_symlink() else item.read_bytes())
    entries["index"] = (path / ".git/index").read_bytes()
    entries["HEAD"] = (path / ".git/HEAD").read_bytes()
    entries["refs"] = _git(path, "show-ref")
    return entries


def _derive(repo: tuple[Path, str, str], **changes: str) -> str:
    path, tree, parent = repo
    args = dict(tree_sha=tree, parent_sha=parent, message=MESSAGE,
                author_identity=AUTHOR, committer_identity=COMMITTER,
                author_date=AUTHOR_DATE, committer_date=COMMITTER_DATE)
    args.update(changes)
    return derive_commit.derive(path, **args)


def test_tree_parent_identities_message_snapshot_and_worktree_index_unchanged(
    repo: tuple[Path, str, str],
) -> None:
    path, tree, parent = repo
    assert _git(path, "write-tree") != tree
    before = _snapshot(path)
    commit = _derive(repo)
    assert _git(path, "rev-parse", f"{commit}^{{tree}}") == tree
    assert _git(path, "rev-parse", f"{commit}^") == parent
    assert _git(path, "show", "-s", "--format=%an <%ae>", commit) == AUTHOR
    assert _git(path, "show", "-s", "--format=%cn <%ce>", commit) == COMMITTER
    raw = subprocess.check_output(["git", "-C", str(path), "cat-file", "commit", commit])
    headers = raw.split(b"\n\n", 1)[0].decode().splitlines()
    # Compare stored dates, not Git-version-dependent ISO display (Z versus +00:00).
    for kind, identity, date in (
        ("author", AUTHOR, AUTHOR_DATE), ("committer", COMMITTER, COMMITTER_DATE),
    ):
        timestamp = int(datetime.fromisoformat(date).timestamp())
        assert f"{kind} {identity} {timestamp} +0000" in headers
    assert raw.split(b"\n\n", 1)[1] == MESSAGE.encode()
    assert _snapshot(path) == before
    assert _derive(repo) == commit
    assert _snapshot(path) == before


@pytest.mark.parametrize("field", [
    "tree_sha", "parent_sha", "message", "author_identity", "committer_identity",
    "author_date", "committer_date",
])
def test_each_derivation_input_participates_in_identity(
    repo: tuple[Path, str, str], field: str,
) -> None:
    path, _, parent = repo
    values = {
        "tree_sha": _git(path, "rev-parse", f"{parent}^{{tree}}"),
        "parent_sha": _git(path, "rev-parse", f"{parent}^"),
        "message": MESSAGE.replace("missing include", "missing declaration"),
        "author_identity": "Other Author <other@invalid>",
        "committer_identity": "Other Committer <other@invalid>",
        "author_date": "2026-10-08T02:00:00+00:00",
        "committer_date": "2026-10-08T03:00:00+00:00",
    }
    assert _derive(repo, **{field: values[field]}) != _derive(repo)


def test_ambient_git_routing_and_local_hooks_do_not_touch_worktree(
    repo: tuple[Path, str, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path, _, _ = repo
    hook = path / ".git/hooks/commit-msg"
    hook.write_text("#!/bin/sh\ntouch should-not-exist\nexit 9\n")
    hook.chmod(0o755)
    _git(path, "config", "commit.gpgsign", "true")
    before = _snapshot(path)
    expected = _derive(repo)
    for key, value in {
        "GIT_DIR": str(tmp_path / "not-a-repo"), "GIT_WORK_TREE": str(tmp_path),
        "GIT_INDEX_FILE": str(tmp_path / "other-index"),
        "GIT_AUTHOR_NAME": "Wrong", "GIT_COMMITTER_DATE": "invalid",
    }.items():
        monkeypatch.setenv(key, value)
    assert _derive(repo) == expected
    assert _snapshot(path) == before
    assert not (tmp_path / "other-index").exists()


def test_invalid_tree_leaves_worktree_and_index_unchanged(repo: tuple[Path, str, str]) -> None:
    path, _, _ = repo
    before = _snapshot(path)
    with pytest.raises(subprocess.CalledProcessError):
        _derive(repo, tree_sha="0" * 40)
    assert _snapshot(path) == before


@pytest.mark.parametrize("changes", [
    {"author_identity": "no email"}, {"committer_identity": "A <a@b>\nInjected"},
    {"tree_sha": "--help"}, {"parent_sha": "HEAD"}, {"author_date": ""},
])
def test_invalid_parameters_refuse_before_git(
    repo: tuple[Path, str, str], monkeypatch: pytest.MonkeyPatch, changes: dict[str, str],
) -> None:
    run = Mock()
    monkeypatch.setattr(derive_commit.subprocess, "run", run)
    with pytest.raises(ValueError):
        _derive(repo, **changes)
    run.assert_not_called()


def test_tree_postcondition_is_enforced(
    repo: tuple[Path, str, str], monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = subprocess.run

    def run(command, **kwargs):
        result = original(command, **kwargs)
        if "rev-parse" in command:
            result.stdout = b"0" * 40 + b"\n"
        return result

    monkeypatch.setattr(derive_commit.subprocess, "run", run)
    with pytest.raises(RuntimeError, match="derived tree mismatch"):
        _derive(repo)


def test_hook_identity_goes_to_final_trailer_without_auxiliary_line(
    repo: tuple[Path, str, str], tmp_path: Path,
) -> None:
    hook = tmp_path / "commit-msg"
    hook.write_text(f"printf '\\nChange-Id: {CHANGE_ID}\\n' >> \"$1\"\n")
    message = MESSAGE.split("\nChange-Id:")[0].rstrip() + "\n"
    change_id = generate_change_id_via_hook(
        hook_path=hook, hook_sha256=hashlib.sha256(hook.read_bytes()).hexdigest(),
        submission_key="b" * 64, message=message,
    )
    final_message = message + f"\nChange-Id: {change_id}\n"
    commit = _derive(repo, message=final_message)
    raw = subprocess.check_output(["git", "-C", str(repo[0]), "cat-file", "commit", commit])
    actual = raw.split(b"\n\n", 1)[1].decode()
    assert actual == MESSAGE
    trailers = subprocess.run(["git", "interpret-trailers", "--parse"],
                              input=actual, text=True, capture_output=True, check=True).stdout
    assert trailers.splitlines() == [f"Change-Id: {change_id}"]
    assert "X-Campaign-Submission-Key" not in actual
