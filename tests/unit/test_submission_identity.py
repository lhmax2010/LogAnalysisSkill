from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import time
from pathlib import Path

import pytest
from ci_triage import submission_identity as identity
from ci_triage.campaign_state import ensure_schema, get_or_create_change_id
from tizen_ci_shared.state import StateDatabase
from tizen_ci_shared.state.keys import build_submission_key

CHANGE_ID = "I" + "a" * 40
KEY = "b" * 64
MESSAGE = "Fix build error\n\nDetails.\n"
GOOD_HOOK = f"printf '\\nChange-Id: {CHANGE_ID}\\n' >> \"$1\"\n"


def _hook(tmp_path: Path, text: str = GOOD_HOOK) -> Path:
    path = tmp_path / "commit-msg"
    path.write_text(text, encoding="utf-8")
    return path


def _generate(path: Path, *, message: str = MESSAGE, key: str = KEY) -> str:
    return identity.generate_change_id_via_hook(
        hook_path=path,
        hook_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        submission_key=key,
        message=message,
    )


@pytest.fixture
def temporary_dirs(monkeypatch: pytest.MonkeyPatch) -> list[Path]:
    paths: list[Path] = []
    original = identity.tempfile.mkdtemp

    def track(*args: object, **kwargs: object) -> str:
        result = original(*args, **kwargs)
        paths.append(Path(result))
        return result

    monkeypatch.setattr(identity.tempfile, "mkdtemp", track)
    return paths


def test_keys_fixed_vectors_and_dimensions() -> None:
    args = dict(
        ci_system="quickbuild",
        project="platform/a",
        branch="tizen",
        spec_name="a",
        base_commit="a" * 40,
    )
    unit = identity.build_campaign_unit_key(source_build_id="101", **args)
    key = identity.build_submission_identity_key(**args)
    assert unit == '["quickbuild","101","platform/a","tizen","a","' + "a" * 40 + '"]'
    assert key == '["quickbuild","platform/a","tizen","a","' + "a" * 40 + '"]'
    assert len(json.loads(unit)) == 6
    assert len(json.loads(key)) == 5
    assert json.loads(unit)[1] == "101"
    assert "101" not in json.loads(key)
    assert unit != identity.build_campaign_unit_key(source_build_id="102", **args)
    expected = "457d881a61ba640725f0b9fb941d407a3e213c89615f15effefc6b076b544beb"
    assert identity.compute_submission_key(key, "c" * 40) == expected
    assert build_submission_key(failure_key=key, verified_tree_sha="c" * 40) == expected
    assert re.fullmatch("[0-9a-f]{64}", expected)


def test_keys_json_encoding_avoids_slash_collision_and_keeps_unicode() -> None:
    args = dict(ci_system="quickbuild", spec_name="包", base_commit="a" * 40)
    for fn, extra in (
        (identity.build_submission_identity_key, {}),
        (identity.build_campaign_unit_key, {"source_build_id": "1"}),
    ):
        left = fn(project="platform/a", branch="b/c", **args, **extra)
        right = fn(project="platform/a/b", branch="c", **args, **extra)
        assert left != right
        assert "包" in left
        assert "\\u" not in left


def test_compute_key_delegates(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []

    def build(**kwargs: str) -> str:
        calls.append(kwargs)
        return "sentinel"

    monkeypatch.setattr(identity, "build_submission_key", build)
    assert identity.compute_submission_key("key", "tree") == "sentinel"
    assert calls == [{"failure_key": "key", "verified_tree_sha": "tree"}]


@pytest.mark.parametrize(
    "line",
    [
        "Change-Id: " + CHANGE_ID,
        "CHANGE-ID: " + CHANGE_ID,
        "Change-ID: " + CHANGE_ID,
        "change-id : " + CHANGE_ID,
        "  cHaNgE-iD : old",
        "Link: https://review.invalid/id/" + CHANGE_ID,
    ],
)
def test_reject_existing_identity_before_reading_hook(tmp_path: Path, line: str) -> None:
    with pytest.raises(identity.ChangeIdHookError, match="already contains") as exc:
        identity.generate_change_id_via_hook(
            hook_path=tmp_path / "absent",
            hook_sha256="bad",
            submission_key=KEY,
            message="Fix build error\n" + line + "\nBody",
        )
    assert exc.value.code == "CHANGE_ID_HOOK_FAILED"


def test_hook_returns_only_id_without_mutating_message(
    tmp_path: Path,
    temporary_dirs: list[Path],
) -> None:
    message = MESSAGE + "\nLink: https://docs.invalid/manual\n"
    original = message
    assert _generate(_hook(tmp_path), message=message) == CHANGE_ID
    assert message == original
    assert "X-Campaign-Submission-Key" not in message
    assert temporary_dirs and all(not p.exists() for p in temporary_dirs)


@pytest.mark.parametrize(
    "body",
    [
        "exit 0\n",
        GOOD_HOOK * 2,
        "echo 'Change-Id: invalid' >> \"$1\"\n",
        GOOD_HOOK.replace("Iaaaa", "IAAAA"),
        GOOD_HOOK + "exit 9\n",
    ],
)
def test_invalid_hook_output_does_not_write_cache(
    tmp_path: Path,
    temporary_dirs: list[Path],
    body: str,
) -> None:
    hook = _hook(tmp_path, body)
    db = StateDatabase(tmp_path / "db")
    ensure_schema(db)
    with pytest.raises(identity.ChangeIdHookError) as exc:
        get_or_create_change_id(
            db,
            campaign_unit_key="unit",
            submission_key=KEY,
            hook_sha256="c" * 64,
            generate=lambda: _generate(hook),
        )
    assert exc.value.code == "CHANGE_ID_HOOK_FAILED"
    conn = db.connect()
    try:
        assert conn.execute("SELECT count(*) FROM campaign_change_ids").fetchone()[0] == 0
    finally:
        conn.close()
    assert temporary_dirs and all(not p.exists() for p in temporary_dirs)


def test_crlf_output_is_stored_as_41_characters(tmp_path: Path) -> None:
    hook = _hook(tmp_path, f"printf '\\r\\nChange-Id: {CHANGE_ID}\\r\\n' >> \"$1\"\n")
    db = StateDatabase(tmp_path / "db")
    result = get_or_create_change_id(
        db,
        campaign_unit_key="unit",
        submission_key=KEY,
        hook_sha256="c" * 64,
        generate=lambda: _generate(hook),
    )
    assert result == CHANGE_ID and len(result) == 41
    conn = db.connect()
    try:
        assert conn.execute("SELECT change_id FROM campaign_change_ids").fetchone()[0] == result
    finally:
        conn.close()


def test_hash_mismatch_and_missing_hook(tmp_path: Path, temporary_dirs: list[Path]) -> None:
    hook = _hook(tmp_path)
    for path in (hook, tmp_path / "absent"):
        with pytest.raises(identity.ChangeIdHookError):
            identity.generate_change_id_via_hook(
                hook_path=path,
                hook_sha256="0" * 64,
                submission_key=KEY,
                message=MESSAGE,
            )
    assert temporary_dirs == []


def test_verified_bytes_execute_after_original_hook_replaced(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hook = _hook(tmp_path)
    run = identity._run_isolated

    def replace_then_run(command: list[str], **kwargs: object) -> None:
        hook.write_text("exit 42\n", encoding="utf-8")
        run(command, **kwargs)

    monkeypatch.setattr(identity, "_run_isolated", replace_then_run)
    assert _generate(hook) == CHANGE_ID
    assert hook.read_text() == "exit 42\n"


def test_submission_key_is_hook_input_and_head_exists(tmp_path: Path) -> None:
    hook = _hook(
        tmp_path,
        "set -e\ngit rev-parse --verify HEAD >/dev/null\n"
        "grep '^X-Campaign-Submission-Key: ' \"$1\" >/dev/null\n"
        'id=$(git hash-object "$1")\nprintf \'\\nChange-Id: I%s\\n\' "$id" >> "$1"\n',
    )
    first, second = _generate(hook, key="a" * 64), _generate(hook, key="b" * 64)
    assert first != second
    assert re.fullmatch("I[0-9a-f]{40}", first)
    assert re.fullmatch("I[0-9a-f]{40}", second)


def test_git_configuration_and_business_repository_are_isolated(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    business = tmp_path / "business"
    business.mkdir()
    subprocess.run(["git", "init", "-q", str(business)], check=True)
    home = tmp_path / "caller-home"
    home.mkdir()
    config = home / ".gitconfig"
    config.write_text("[gerrit]\nreviewUrl = https://evil.invalid\ncreateChangeId = false\n")
    before = {
        str(p.relative_to(business)): p.read_bytes()
        for p in (business / ".git").rglob("*")
        if p.is_file()
    }
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home))
    monkeypatch.setenv("GIT_DIR", str(business / ".git"))
    monkeypatch.setenv("GIT_INDEX_FILE", str(business / ".git/index"))
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "gerrit.createChangeId")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "false")
    monkeypatch.setenv("TMPDIR", str(business))
    hook = _hook(
        tmp_path,
        "set -e\n"
        'test -z "${GIT_DIR+x}"\ntest -z "${GIT_INDEX_FILE+x}"\n'
        'test -z "${GIT_CONFIG_COUNT+x}"\n'
        'test "$(git config --bool gerrit.createChangeId)" = true\n'
        'test -z "$(git config gerrit.reviewUrl || :)"\n'
        "git rev-parse --verify HEAD >/dev/null\n" + GOOD_HOOK,
    )
    assert _generate(hook) == CHANGE_ID
    hook.write_text("exit 9\n", encoding="utf-8")
    with pytest.raises(identity.ChangeIdHookError):
        _generate(hook)
    after = {
        str(p.relative_to(business)): p.read_bytes()
        for p in (business / ".git").rglob("*")
        if p.is_file()
    }
    assert after == before
    assert list(business.iterdir()) == [business / ".git"]


def test_process_environment_is_exact_whitelist(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run = identity._run_isolated
    environments = []

    def capture(command: list[str], *, cwd: Path, env: dict[str, str]) -> None:
        environments.append(env.copy())
        run(command, cwd=cwd, env=env)

    monkeypatch.setattr(identity, "_run_isolated", capture)
    assert _generate(_hook(tmp_path)) == CHANGE_ID
    assert len(environments) == 6
    for env in environments:
        assert set(env) == {
            "PATH",
            "LANG",
            "HOME",
            "XDG_CONFIG_HOME",
            "GIT_CONFIG_NOSYSTEM",
            "GIT_CONFIG_GLOBAL",
        }
        assert env["HOME"] == env["XDG_CONFIG_HOME"]
        assert env["GIT_CONFIG_NOSYSTEM"] == "1"
        assert env["GIT_CONFIG_GLOBAL"] == "/dev/null"


def test_timeout_kills_process_group_and_removes_temporary_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    temporary_dirs: list[Path],
) -> None:
    assert identity._HOOK_TIMEOUT == 30
    pidfile = tmp_path / "child.pid"
    hook = _hook(tmp_path, f"sleep 60 &\necho $! > '{pidfile}'\nwait\n")
    monkeypatch.setattr(identity, "_HOOK_TIMEOUT", 0.5)
    with pytest.raises(identity.ChangeIdHookError) as exc:
        _generate(hook)
    assert exc.value.code == "CHANGE_ID_HOOK_FAILED"
    assert isinstance(exc.value.__cause__, subprocess.TimeoutExpired)
    child = int(pidfile.read_text())
    for _ in range(100):
        stat = Path(f"/proc/{child}/stat")
        if not stat.exists() or stat.read_text().split()[2] == "Z":
            break
        time.sleep(0.01)
    else:
        pytest.fail("hook child still running after process-group kill")
    assert all(not p.exists() for p in temporary_dirs)


def test_no_git_in_path_maps_to_hook_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    temporary_dirs: list[Path],
) -> None:
    hook = _hook(tmp_path)
    monkeypatch.setenv("PATH", str(tmp_path))
    with pytest.raises(identity.ChangeIdHookError):
        _generate(hook)
    assert temporary_dirs and all(not p.exists() for p in temporary_dirs)


def test_unwritable_temporary_directory_maps_to_hook_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hook = _hook(tmp_path)

    def deny(*args: object, **kwargs: object) -> str:
        raise PermissionError("temporary directory is not writable")

    monkeypatch.setattr(identity.tempfile, "mkdtemp", deny)
    with pytest.raises(identity.ChangeIdHookError, match="not writable"):
        _generate(hook)


def test_hook_process_start_failure_maps_and_cleans(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    temporary_dirs: list[Path],
) -> None:
    hook = _hook(tmp_path)
    original = subprocess.Popen

    def start(command: list[str], **kwargs: object) -> object:
        if command[0] == "sh":
            raise OSError("cannot start hook")
        return original(command, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", start)
    with pytest.raises(identity.ChangeIdHookError, match="cannot start"):
        _generate(hook)
    assert temporary_dirs and all(not p.exists() for p in temporary_dirs)


def test_cleanup_failure_warns_without_changing_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    temporary_dirs: list[Path],
) -> None:
    hook = _hook(tmp_path)
    remove = shutil.rmtree

    def deny(path: Path) -> None:
        raise PermissionError("cleanup denied")

    monkeypatch.setattr(shutil, "rmtree", deny)
    try:
        assert _generate(hook) == CHANGE_ID
        assert "cleanup denied" in caplog.text
        assert any(record.levelname == "WARNING" for record in caplog.records)
    finally:
        for path in temporary_dirs:
            remove(path)
