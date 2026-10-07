from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

import pytest
from tizen_ci_shared import workspace


@pytest.mark.parametrize("scene", ["exclude", "marker-write"])
def test_protection_interruption_preserves_failure_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, scene: str
) -> None:
    root = tmp_path / "workspaces"
    path = root / "iter_0"
    path.mkdir(parents=True)
    subprocess.run(["git", "init", str(path)], check=True, capture_output=True)
    marker = workspace.write_workdir_marker(
        path,
        workspace_root=root,
        baseline_repo=tmp_path / "baseline",
        base_commit="fixture",
        iter_index=0,
    )
    workdir_bytes = marker.read_bytes()
    handle = workspace.DisposableWorktree(
        str(path), str(tmp_path / "baseline"), "fixture", str(root), 0, str(marker)
    )
    protected = path / workspace.PROTECTED_FILENAME
    exclude = path / ".git/info/exclude"
    events: list[str] = []
    interrupted = KeyboardInterrupt("fixture interruption")
    real_verify = workspace._verify_cleanup_handle
    real_exclude = workspace._exclude_private_files
    real_write = Path.write_text
    partial = b'{"protected_reason":'

    def verify(value: workspace.DisposableWorktree) -> None:
        real_verify(value)
        events.append("verified")

    def exclude_files(worktree_path: Path, *, timeout: float | None = None) -> None:
        assert events == ["verified"]
        assert not protected.exists()
        if scene == "exclude":
            exclude.write_bytes((workspace.MARKER_FILENAME + "\n").encode())
            events.append("exclude-partial")
            raise interrupted
        real_exclude(worktree_path, timeout=timeout)
        events.append("exclude-complete")

    def write(value: Path, data: str, *args: object, **kwargs: object) -> int:
        if value == protected:
            assert events == ["verified", "exclude-complete"]
            value.write_bytes(partial)
            events.append("marker-partial")
            raise interrupted
        return real_write(value, data, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(workspace, "_verify_cleanup_handle", verify)
        patch.setattr(workspace, "_exclude_private_files", exclude_files)
        patch.setattr(Path, "write_text", write)
        with pytest.raises(KeyboardInterrupt) as captured:
            workspace.mark_worktree_protected(
                handle, verification_id="fixture", failure_key="fixture"
            )
    assert captured.value is interrupted
    assert marker.read_bytes() == workdir_bytes
    assert path.is_dir()
    if scene == "exclude":
        assert events == ["verified", "exclude-partial"]
        assert not protected.exists()
        assert exclude.read_bytes() == (workspace.MARKER_FILENAME + "\n").encode()
    else:
        assert events == ["verified", "exclude-complete", "marker-partial"]
        assert protected.read_bytes() == partial
        assert hashlib.sha256(protected.read_bytes()).hexdigest() == (
            "87c1f578e028105c6c36684cdffaee0863ed2459bcf45e872bba090e66cd3a54"
        )
        assert {workspace.MARKER_FILENAME, workspace.PROTECTED_FILENAME} <= set(
            exclude.read_text().splitlines()
        )

    # Readers can mutate their worktree; each observes an independent failure copy.
    readers = (
        workspace.clean_repository_preserving_markers,
        workspace.release_worktree_protection,
        workspace.is_protected,
        workspace._exclude_private_files,
    )
    observed = []
    for reader in readers:
        copy = tmp_path / reader.__name__
        shutil.copytree(path, copy)
        observed.append(repr(reader(worktree_path=copy)))
    assert observed == (
        ["None", "False", "False", "None"]
        if scene == "exclude"
        else ["None", "True", "True", "None"]
    )
