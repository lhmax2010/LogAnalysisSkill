from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
import tizen_gerrit_fetch
from tizen_ci_shared.types import GerritChange, GerritPatchSet, SourceFetchResult
from tizen_gerrit_fetch import GERRIT_HOST, GERRIT_PORT, GerritError, gerrit
from tizen_gerrit_fetch.gerrit import (
    fetch_source_for_commit,
    find_patchset_by_revision,
)

COMMIT = "ba0d7cc0f960da15cbd1134d213a3708dddde59f"
PROJECT = "platform/upstream/lightweight-web-engine"


class ControlledInterruption(RuntimeError):
    """Deterministic stand-in for an externally interrupted subprocess call."""


def _change_obj(
    *,
    commit: str = COMMIT,
    status: str = "NEW",
    branch: str = "tizen",
    matching_patchset: bool = True,
    number: int = 338415,
) -> dict[str, Any]:
    revision = commit if matching_patchset else "d4ce79de7e83e323aef427249eb4d0d2924d9263"
    return {
        "project": PROJECT,
        "branch": branch,
        "status": status,
        "number": number,
        "subject": "test",
        "url": f"https://review.tizen.org/{number}",
        "patchSets": [
            {
                "number": 6,
                "revision": revision,
                "ref": "refs/changes/15/338415/6",
            }
        ],
    }


def _query_output(*changes: dict[str, Any]) -> str:
    return "\n".join(
        [*(json.dumps(change) for change in changes), json.dumps({"type": "stats"})]
    )


def _git_operation(command: Sequence[str]) -> str:
    if command[:2] == ["git", "init"]:
        return "init"
    if "remote" in command and "add" in command:
        return "remote-add"
    if "fetch" in command:
        if "50" in command:
            return "branch-fallback-fetch"
        if command[-1].startswith("refs/"):
            return "new-fetch"
        return "commit-fetch"
    if "checkout" in command:
        return "new-checkout" if command[-1] == "FETCH_HEAD" else "non-new-checkout"
    raise AssertionError(f"unexpected git command: {command}")


class FakeRunner:
    def __init__(
        self,
        destination: Path,
        *,
        change: dict[str, Any] | None = None,
        query_output: str | None = None,
        query_error: BaseException | None = None,
        fail_at: str | None = None,
        fail_commit_fetch_once: bool = False,
        interrupt_at: str | None = None,
        interrupt_error: BaseException | None = None,
    ) -> None:
        self.destination = destination
        self.query_output = query_output or _query_output(change or _change_obj())
        self.query_error = query_error
        self.fail_at = fail_at
        self.fail_commit_fetch_once = fail_commit_fetch_once
        self.interrupt_at = interrupt_at
        self.interrupt_error = interrupt_error
        self.calls: list[tuple[list[str], dict[str, Any]]] = []
        self._commit_fetch_failed = False

    def __call__(
        self,
        command: Sequence[str],
        **kwargs: Any,
    ) -> subprocess.CompletedProcess[str]:
        argv = list(command)
        self.calls.append((argv, dict(kwargs)))
        if argv[0] == "ssh":
            if self.query_error is not None:
                raise self.query_error
            return subprocess.CompletedProcess(argv, 0, stdout=self.query_output, stderr="")

        operation = _git_operation(argv)
        if operation == self.interrupt_at:
            if self.interrupt_error is None:
                raise AssertionError("interrupt_at requires interrupt_error")
            raise self.interrupt_error
        if operation == self.fail_at:
            raise subprocess.CalledProcessError(1, argv)
        if (
            operation == "commit-fetch"
            and self.fail_commit_fetch_once
            and not self._commit_fetch_failed
        ):
            self._commit_fetch_failed = True
            raise subprocess.CalledProcessError(1, argv)

        self._record_success(operation)
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    def _record_success(self, operation: str) -> None:
        stage_names = {
            "init": "01-init",
            "remote-add": "02-remote-add",
            "new-fetch": "03-new-fetch",
            "commit-fetch": "03-commit-fetch",
            "branch-fallback-fetch": "04-branch-fallback-fetch",
            "new-checkout": "05-new-checkout",
            "non-new-checkout": "05-non-new-checkout",
        }
        if operation == "init":
            (self.destination / ".git").mkdir()
        stages = self.destination / ".stages"
        stages.mkdir(exist_ok=True)
        (stages / stage_names[operation]).write_text(operation, encoding="utf-8")
        if operation == "branch-fallback-fetch":
            (self.destination / "generated-link").symlink_to(
                self.destination / "generated"
            )
        if operation.endswith("checkout"):
            (self.destination / "source.c").write_text("int main(void) {}\n", encoding="utf-8")


def _stage_names(destination: Path) -> tuple[str, ...]:
    stages = destination / ".stages"
    if not stages.is_dir():
        return ()
    return tuple(path.name for path in sorted(stages.iterdir()))


def _fetch_calls(runner: FakeRunner) -> list[list[str]]:
    return [argv for argv, _ in runner.calls if argv[0] == "git" and "fetch" in argv]


def _change_payload(change: GerritChange | None) -> dict[str, Any] | None:
    if change is None:
        return None
    patchset = change.matching_patchset
    patchset_payload = None
    if patchset is not None:
        patchset_payload = {
            "number": patchset.number,
            "revision": patchset.revision,
            "ref": patchset.ref,
        }
    return {
        "project": change.project,
        "branch": change.branch,
        "status": change.status,
        "number": change.number,
        "subject": change.subject,
        "url": change.url,
        "matching_patchset": patchset_payload,
    }


def _destination_tree(destination: Path) -> list[dict[str, Any]]:
    tree: list[dict[str, Any]] = []
    for path in sorted(destination.rglob("*")):
        relative = path.relative_to(destination).as_posix()
        if path.is_symlink():
            tree.append(
                {
                    "path": relative,
                    "kind": "symlink",
                    "value": os.readlink(path),
                }
            )
        elif path.is_dir():
            tree.append({"path": relative, "kind": "directory", "value": None})
        else:
            tree.append(
                {
                    "path": relative,
                    "kind": "file",
                    "value": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
    return tree


def parity_payload(
    module: ModuleType,
    destination: Path,
    *,
    git_ssh_command: str = "ssh -i /tmp/parity-key",
) -> dict[str, Any]:
    change = _change_obj(status="MERGED")
    runner = FakeRunner(
        destination,
        change=change,
        fail_commit_fetch_once=True,
    )
    result = module.fetch_source_for_commit(
        PROJECT,
        COMMIT,
        destination,
        subprocess_runner=runner,
        git_ssh_command=git_ssh_command,
    )
    return {
        "result": {
            "status": result.status,
            "src_root": str(result.src_root) if result.src_root is not None else None,
            "remote_url": result.remote_url,
            "change": _change_payload(result.change),
            "error": result.error,
        },
        "runner_trace": [
            {
                "argv": argv,
                "check": kwargs.get("check"),
                "capture_output": kwargs.get("capture_output"),
                "text": kwargs.get("text"),
            }
            for argv, kwargs in runner.calls
        ],
        "controlled_environment": {"GIT_SSH_COMMAND": git_ssh_command},
        "destination_state": {
            "tree": _destination_tree(destination),
            "stage_markers": list(_stage_names(destination)),
        },
    }


def _mask_destination(value: str, destination: Path) -> str:
    prefix = str(destination)
    if value == prefix:
        return "<DEST>"
    if value.startswith(prefix + os.sep):
        return "<DEST>" + value[len(prefix) :]
    return value


def normalize_parity_payload(payload: Mapping[str, Any], destination: Path) -> dict[str, Any]:
    normalized = copy.deepcopy(dict(payload))
    result = normalized["result"]
    if result["src_root"] is not None:
        result["src_root"] = _mask_destination(result["src_root"], destination)
    for call in normalized["runner_trace"]:
        call["argv"] = [
            _mask_destination(argument, destination) for argument in call["argv"]
        ]
    for entry in normalized["destination_state"]["tree"]:
        if entry["kind"] == "symlink":
            entry["value"] = _mask_destination(entry["value"], destination)
    return normalized


def assert_parity(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    left_destination: Path,
    right_destination: Path,
) -> None:
    assert normalize_parity_payload(left, left_destination) == normalize_parity_payload(
        right, right_destination
    )


def parity_sha(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


# Skill behavior: frozen section 5.1 branch table.


@pytest.mark.parametrize(
    ("case", "expected_exception", "expected_code"),
    [
        pytest.param("command-failed", GerritError, "GERRIT_QUERY_FAILED", id="command-failed"),
        pytest.param("not-found", GerritError, "GERRIT_CHANGE_NOT_FOUND", id="not-found"),
        pytest.param("ambiguous", GerritError, "GERRIT_CHANGE_AMBIGUOUS", id="ambiguous"),
        pytest.param("malformed-json", json.JSONDecodeError, None, id="malformed-json"),
        pytest.param("timeout", subprocess.TimeoutExpired, None, id="timeout"),
    ],
)
def test_fetch_source_query_outcomes_preserve_destination(
    tmp_path: Path,
    case: str,
    expected_exception: type[BaseException],
    expected_code: str | None,
) -> None:
    destination = tmp_path / "src"
    destination.mkdir()
    sentinel = destination / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")
    kwargs: dict[str, Any] = {}
    if case == "command-failed":
        kwargs["query_error"] = subprocess.CalledProcessError(1, ["ssh"])
    elif case == "not-found":
        kwargs["query_output"] = _query_output()
    elif case == "ambiguous":
        kwargs["query_output"] = _query_output(
            _change_obj(number=1),
            _change_obj(number=2),
        )
    elif case == "malformed-json":
        kwargs["query_output"] = "{not-json"
    elif case == "timeout":
        kwargs["query_error"] = subprocess.TimeoutExpired(["ssh"], timeout=1)
    runner = FakeRunner(destination, **kwargs)

    with pytest.raises(expected_exception) as captured:
        fetch_source_for_commit(PROJECT, COMMIT, destination, subprocess_runner=runner)

    if expected_code is not None:
        assert isinstance(captured.value, GerritError)
        assert captured.value.code == expected_code
    assert destination.is_dir()
    assert sentinel.read_text(encoding="utf-8") == "keep"
    assert len(runner.calls) == 1
    assert runner.calls[0][0][0] == "ssh"


def test_find_patchset_by_revision_uses_matching_revision_not_current() -> None:
    change = {
        "patchSets": [
            {
                "number": 6,
                "revision": "ba0d7cc0f960da15cbd1134d213a3708dddde59f",
                "ref": "refs/changes/15/338415/6",
            },
            {
                "number": 7,
                "revision": "d4ce79de7e83e323aef427249eb4d0d2924d9263",
                "ref": "refs/changes/15/338415/7",
            },
        ]
    }

    patchset = find_patchset_by_revision(
        change,
        "ba0d7cc0f960da15cbd1134d213a3708dddde59f",
    )

    assert patchset is not None
    assert patchset.ref == "refs/changes/15/338415/6"


def test_fetch_source_for_new_change_fetches_matching_patchset_ref(tmp_path: Path) -> None:
    commands: list[list[str]] = []
    commit = "ba0d7cc0f960da15cbd1134d213a3708dddde59f"
    gerrit_output = "\n".join(
        [
            json.dumps(
                {
                    "project": "platform/upstream/lightweight-web-engine",
                    "branch": "tizen",
                    "status": "NEW",
                    "number": 338415,
                    "subject": "test",
                    "patchSets": [
                        {
                            "number": 6,
                            "revision": commit,
                            "ref": "refs/changes/15/338415/6",
                        },
                        {
                            "number": 7,
                            "revision": "d4ce79de7e83e323aef427249eb4d0d2924d9263",
                            "ref": "refs/changes/15/338415/7",
                        },
                    ],
                }
            ),
            json.dumps({"type": "stats", "rowCount": 1}),
        ]
    )

    def runner(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        if command[:3] == ["ssh", "-p", "29418"]:
            return subprocess.CompletedProcess(command, 0, stdout=gerrit_output, stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    result = fetch_source_for_commit(
        "platform/upstream/lightweight-web-engine",
        commit,
        tmp_path / "src",
        subprocess_runner=runner,
    )

    assert result.status == "source_available"
    assert result.remote_url == "ssh://review.tizen.org:29418/platform/upstream/lightweight-web-engine"
    assert any("refs/changes/15/338415/6" in command for command in commands)
    assert not any("refs/changes/15/338415/7" in command for command in commands)


def test_fetch_source_new_without_matching_patchset_returns_code(tmp_path: Path) -> None:
    destination = tmp_path / "src"
    runner = FakeRunner(
        destination,
        change=_change_obj(matching_patchset=False),
    )

    result = fetch_source_for_commit(
        PROJECT,
        COMMIT,
        destination,
        subprocess_runner=runner,
    )

    assert result.status == "PATCHSET_REVISION_NOT_FOUND"
    assert result.error is not None
    assert destination.is_dir()
    assert (destination / ".git").is_dir()
    assert _stage_names(destination) == ("01-init", "02-remote-add")
    assert _fetch_calls(runner) == []


@pytest.mark.parametrize(
    "case",
    [
        pytest.param("direct-fetch", id="direct-fetch"),
        pytest.param("branch-fallback", id="branch-fallback"),
        pytest.param("failed-without-branch", id="failed-without-branch"),
    ],
)
def test_fetch_source_non_new_paths(tmp_path: Path, case: str) -> None:
    destination = tmp_path / "src"
    branch = "" if case == "failed-without-branch" else "tizen"
    runner = FakeRunner(
        destination,
        change=_change_obj(status="MERGED", branch=branch),
        fail_commit_fetch_once=case != "direct-fetch",
    )

    result = fetch_source_for_commit(
        PROJECT,
        COMMIT,
        destination,
        subprocess_runner=runner,
    )

    fetches = _fetch_calls(runner)
    assert destination.is_dir()
    assert (destination / ".git").is_dir()
    if case == "direct-fetch":
        assert result.status == "source_available"
        assert len(fetches) == 1
        assert fetches[0][fetches[0].index("--depth") + 1] == "1"
        assert (destination / "source.c").is_file()
    elif case == "branch-fallback":
        assert result.status == "source_available"
        assert len(fetches) == 2
        assert [command[command.index("--depth") + 1] for command in fetches] == ["1", "50"]
        assert (destination / "source.c").is_file()
    else:
        assert result.status == "FAILED_SOURCE"
        assert len(fetches) == 1
        assert _stage_names(destination) == ("01-init", "02-remote-add")
        assert not (destination / "source.c").exists()


@pytest.mark.parametrize("initial", ["missing", "directory", "file"])
def test_fetch_source_rebuilds_destination(tmp_path: Path, initial: str) -> None:
    destination = tmp_path / "src"
    sentinel = destination / "old.txt"
    if initial == "directory":
        destination.mkdir()
        sentinel.write_text("old", encoding="utf-8")
    elif initial == "file":
        destination.write_text("old file", encoding="utf-8")
    runner = FakeRunner(destination)

    result = fetch_source_for_commit(
        PROJECT,
        COMMIT,
        destination,
        subprocess_runner=runner,
    )

    assert result.status == "source_available"
    assert destination.is_dir()
    assert not sentinel.exists()
    assert (destination / ".git").is_dir()
    assert (destination / "source.c").is_file()


def test_fetch_source_rejects_live_symlink(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    sentinel = target / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")
    destination = tmp_path / "src"
    destination.symlink_to(target, target_is_directory=True)
    runner = FakeRunner(destination)

    with pytest.raises(GerritError) as captured:
        fetch_source_for_commit(PROJECT, COMMIT, destination, subprocess_runner=runner)

    assert captured.value.code == "SOURCE_DIR_UNSAFE"
    assert destination.is_symlink()
    assert sentinel.read_text(encoding="utf-8") == "keep"
    assert len(runner.calls) == 1


def test_fetch_source_dangling_symlink_propagates_file_exists_error(tmp_path: Path) -> None:
    destination = tmp_path / "src"
    missing_target = tmp_path / "missing"
    destination.symlink_to(missing_target, target_is_directory=True)
    runner = FakeRunner(destination)

    with pytest.raises(FileExistsError):
        fetch_source_for_commit(PROJECT, COMMIT, destination, subprocess_runner=runner)

    assert destination.is_symlink()
    assert not missing_target.exists()
    assert len(runner.calls) == 1


def test_fetch_source_sets_git_ssh_command_on_all_git_calls(tmp_path: Path) -> None:
    destination = tmp_path / "src"
    runner = FakeRunner(destination)
    ssh_command = "ssh -i /tmp/test-key -o BatchMode=yes"

    result = fetch_source_for_commit(
        PROJECT,
        COMMIT,
        destination,
        subprocess_runner=runner,
        git_ssh_command=ssh_command,
    )

    assert result.status == "source_available"
    git_calls = [kwargs for argv, kwargs in runner.calls if argv[0] == "git"]
    assert git_calls
    assert all(kwargs["env"]["GIT_SSH_COMMAND"] == ssh_command for kwargs in git_calls)


@pytest.mark.parametrize(
    ("fail_point", "status", "fallback", "expected_stages"),
    [
        pytest.param("init", "NEW", False, (), id="init"),
        pytest.param("remote-add", "NEW", False, ("01-init",), id="remote-add"),
        pytest.param(
            "new-fetch",
            "NEW",
            False,
            ("01-init", "02-remote-add"),
            id="new-fetch",
        ),
        pytest.param(
            "new-checkout",
            "NEW",
            False,
            ("01-init", "02-remote-add", "03-new-fetch"),
            id="new-checkout",
        ),
        pytest.param(
            "branch-fallback-fetch",
            "MERGED",
            True,
            ("01-init", "02-remote-add"),
            id="branch-fallback-fetch",
        ),
        pytest.param(
            "non-new-checkout",
            "MERGED",
            False,
            ("01-init", "02-remote-add", "03-commit-fetch"),
            id="non-new-checkout",
        ),
    ],
)
def test_fetch_source_git_failures_leave_observable_state(
    tmp_path: Path,
    fail_point: str,
    status: str,
    fallback: bool,
    expected_stages: tuple[str, ...],
) -> None:
    destination = tmp_path / "src"
    runner = FakeRunner(
        destination,
        change=_change_obj(status=status),
        fail_at=fail_point,
        fail_commit_fetch_once=fallback,
    )

    result = fetch_source_for_commit(
        PROJECT,
        COMMIT,
        destination,
        subprocess_runner=runner,
    )

    assert result.status == "FAILED_SOURCE"
    assert destination.is_dir()
    assert _stage_names(destination) == expected_stages
    assert (destination / ".git").is_dir() is (fail_point != "init")
    assert not (destination / "source.c").exists()


@pytest.mark.parametrize(
    ("case", "interrupt_at", "error_kind", "expected_stages"),
    [
        pytest.param(
            "timeout-after-init",
            "remote-add",
            "timeout",
            ("01-init",),
            id="timeout-after-init",
        ),
        pytest.param(
            "interrupt-during-fetch",
            "new-fetch",
            "interrupt",
            ("01-init", "02-remote-add"),
            id="interrupt-during-fetch",
        ),
        pytest.param(
            "timeout-before-checkout",
            "new-checkout",
            "timeout",
            ("01-init", "02-remote-add", "03-new-fetch"),
            id="timeout-before-checkout",
        ),
    ],
)
def test_fetch_source_git_interruption_propagates_and_leaves_state(
    tmp_path: Path,
    case: str,
    interrupt_at: str,
    error_kind: str,
    expected_stages: tuple[str, ...],
) -> None:
    destination = tmp_path / "src"
    error: BaseException
    if error_kind == "timeout":
        error = subprocess.TimeoutExpired([interrupt_at], timeout=1)
        expected_exception: type[BaseException] = subprocess.TimeoutExpired
    else:
        error = ControlledInterruption(case)
        expected_exception = ControlledInterruption
    runner = FakeRunner(
        destination,
        interrupt_at=interrupt_at,
        interrupt_error=error,
    )

    with pytest.raises(expected_exception):
        fetch_source_for_commit(PROJECT, COMMIT, destination, subprocess_runner=runner)

    assert destination.is_dir()
    assert _stage_names(destination) == expected_stages
    assert (destination / ".git").is_dir()
    assert not (destination / "source.c").exists()


@pytest.mark.parametrize("operation", ["rmtree", "unlink", "mkdir"])
def test_fetch_source_filesystem_errors_propagate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
) -> None:
    destination = tmp_path / "src"
    sentinel = destination / "keep.txt"
    original_mkdir = Path.mkdir
    if operation == "rmtree":
        destination.mkdir()
        sentinel.write_text("keep", encoding="utf-8")

        def fail_rmtree(path: Path) -> None:
            assert path == destination
            raise OSError("rmtree blocked")

        monkeypatch.setattr(gerrit.shutil, "rmtree", fail_rmtree)
    elif operation == "unlink":
        destination.write_text("keep", encoding="utf-8")

        def fail_unlink(path: Path, *args: Any, **kwargs: Any) -> None:
            assert path == destination
            raise OSError("unlink blocked")

        monkeypatch.setattr(Path, "unlink", fail_unlink)
    else:

        def fail_mkdir(path: Path, *args: Any, **kwargs: Any) -> None:
            if path == destination:
                raise OSError("mkdir blocked")
            original_mkdir(path, *args, **kwargs)

        monkeypatch.setattr(Path, "mkdir", fail_mkdir)
    runner = FakeRunner(destination)

    with pytest.raises(OSError, match=operation):
        fetch_source_for_commit(PROJECT, COMMIT, destination, subprocess_runner=runner)

    assert len(runner.calls) == 1
    if operation == "rmtree":
        assert destination.is_dir()
        assert sentinel.read_text(encoding="utf-8") == "keep"
    elif operation == "unlink":
        assert destination.is_file()
        assert destination.read_text(encoding="utf-8") == "keep"
    else:
        assert not destination.exists()


def test_fetch_source_subprocess_calls_have_no_timeout(tmp_path: Path) -> None:
    destination = tmp_path / "src"
    runner = FakeRunner(destination)

    result = fetch_source_for_commit(
        PROJECT,
        COMMIT,
        destination,
        subprocess_runner=runner,
    )

    assert result.status == "source_available"
    assert any(argv[0] == "ssh" for argv, _ in runner.calls)
    assert any(argv[0] == "git" for argv, _ in runner.calls)
    assert all("timeout" not in kwargs for _, kwargs in runner.calls)


# Package-root API contract. These are skill tests, not legacy wiring tests.


def test_package_root_exports_only_public_contract_by_identity() -> None:
    public_contract = (
        "fetch_source_for_commit",
        "GerritError",
        "GERRIT_HOST",
        "GERRIT_PORT",
    )
    assert set(tizen_gerrit_fetch.__all__) == set(public_contract)
    for name in public_contract:
        assert getattr(tizen_gerrit_fetch, name) is getattr(gerrit, name)


def test_package_root_does_not_export_implementation_symbols() -> None:
    for name in (
        "SubprocessRunner",
        "query_change_for_commit",
        "parse_gerrit_query_output",
        "change_from_query_obj",
        "find_patchset_by_revision",
        "_run_git",
        "_reset_generated_source_dir",
        "_optional_int",
    ):
        assert not hasattr(tizen_gerrit_fetch, name)


# Parity normalizer contract. Pre-shim behavioral evidence is captured before
# the legacy module becomes a shim; these tests keep the comparator verifiable.


def test_parity_normalizer_masks_only_destination_fields(tmp_path: Path) -> None:
    left_destination = tmp_path / "left"
    right_destination = tmp_path / "right"
    left = parity_payload(gerrit, left_destination)
    right = parity_payload(gerrit, right_destination)

    assert str(left_destination) != str(right_destination)
    assert_parity(left, right, left_destination, right_destination)


@pytest.mark.parametrize("mutation", ["error", "command-order", "status"])
def test_parity_normalizer_rejects_non_path_differences(
    tmp_path: Path,
    mutation: str,
) -> None:
    left_destination = tmp_path / "left"
    right_destination = tmp_path / "right"
    left = parity_payload(gerrit, left_destination)
    right = parity_payload(gerrit, right_destination)
    if mutation == "error":
        right["result"]["error"] = "NON_PATH_ERROR: changed diagnostic"
    elif mutation == "command-order":
        right["runner_trace"][0], right["runner_trace"][1] = (
            right["runner_trace"][1],
            right["runner_trace"][0],
        )
    else:
        right["result"]["status"] = "FAILED_SOURCE"

    with pytest.raises(AssertionError):
        assert_parity(left, right, left_destination, right_destination)


def test_shared_gerrit_types_are_not_package_root_exports() -> None:
    for name in ("GerritChange", "GerritPatchSet", "SourceFetchResult"):
        assert not hasattr(tizen_gerrit_fetch, name)
    assert GERRIT_HOST == "review.tizen.org"
    assert GERRIT_PORT == "29418"
    assert GerritChange is not None
    assert GerritPatchSet is not None
    assert SourceFetchResult is not None


# Legacy wiring: identity checks only, not a substitute for pre-shim parity.


def test_legacy_module_reexports_implementation_and_types_by_identity() -> None:
    from ci_triage import gerrit as legacy

    implementation_symbols = (
        "GERRIT_HOST",
        "GERRIT_PORT",
        "SubprocessRunner",
        "GerritError",
        "query_change_for_commit",
        "parse_gerrit_query_output",
        "change_from_query_obj",
        "find_patchset_by_revision",
        "fetch_source_for_commit",
        "_run_git",
        "_reset_generated_source_dir",
        "_optional_int",
    )
    for symbol in implementation_symbols:
        assert getattr(legacy, symbol) is getattr(gerrit, symbol)

    shared_types = {
        "GerritChange": GerritChange,
        "GerritPatchSet": GerritPatchSet,
        "SourceFetchResult": SourceFetchResult,
    }
    for symbol, shared_type in shared_types.items():
        assert getattr(legacy, symbol) is shared_type
