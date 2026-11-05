"""RESTORE-16: offline, private-first capture and closed redaction failures."""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

HERE = Path(__file__).resolve().parents[2] / (
    "docs/clang-fix-campaign/dev_memory/stage21_campaign_skeleton/evidence/restore/discovery-capture"
)
IDENTITY = "SyntheticAccount"
DISPLAY = "SyntheticDisplay"


@pytest.fixture
def module(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> ModuleType:
    monkeypatch.setenv("HOME", str(tmp_path / "private-home"))
    spec = importlib.util.spec_from_file_location(
        "capture_archive_test", HERE / "capture_archive.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def create(module: ModuleType, tmp_path: Path):  # type: ignore[no-untyped-def]
    output = tmp_path / "repository/discovery-capture/run"
    output.mkdir(parents=True)
    return module.Archive(output)


def store(archive, source: str):  # type: ignore[no-untyped-def]
    body = archive.store("01.response.html", "html", source.encode(), source)
    return {"status": "CAPTURED", "failure": None, "browser_closed": True,
            "profile_removed": True, "pages": [{"body": body}]}


def no_leaks(value: object) -> None:
    result = json.dumps(value)
    for private in (IDENTITY, DISPLAY, "PrivateException", "Traceback"):
        assert private not in result


@pytest.mark.parametrize("welcome", [IDENTITY, DISPLAY, f"{IDENTITY} ({DISPLAY})"])
def test_private_first_permissions_zero_residue_and_delete(module, tmp_path, welcome):  # type: ignore[no-untyped-def]
    archive = create(module, tmp_path)
    source = (f'<span>Welcome! {welcome}</span>\r\n\r<td>{IDENTITY} ({DISPLAY})</td>'
              f'<title>{DISPLAY}</title><a title="{IDENTITY}">{DISPLAY}</a>')
    record = store(archive, source)
    assert list(archive.output.iterdir()) == []
    assert archive.private.stat().st_mode & 0o777 == 0o700
    for path in archive.private.iterdir():
        assert path.stat().st_mode & 0o777 == 0o600
    assert (archive.private / "01.response.html.raw").read_bytes() == source.encode()
    result = archive.finish(record)
    assert result["ok"]
    assert result["record"]["archive"]["identity_remaining_count"] == 0
    assert result["record"]["archive"]["private_removed"]
    assert not archive.private.exists()
    assert b'\r\n\r' in (archive.output / '01.response.html').read_bytes()
    no_leaks(result)
    for path in archive.output.iterdir():
        assert IDENTITY not in path.read_text() and DISPLAY not in path.read_text()


@pytest.mark.parametrize("source", ["<p>no greeting</p>", "<span>Welcome! </span>"])
def test_missing_welcome_retains_private_originals(module, tmp_path, source):  # type: ignore[no-untyped-def]
    archive = create(module, tmp_path)
    result = archive.finish(store(archive, source))
    assert result["stage"] == "IDENTITY_EMPTY"
    assert not result["ok"] and archive.private.exists()
    assert not (archive.output / "01.response.html").exists()
    assert (archive.private / "01.response.html.raw").read_text() == source
    no_leaks(result)


@pytest.mark.parametrize("stage", ["IDENTITY_REGISTER", "REDACT", "PRECHECK", "WRITE", "POSTCHECK"])
def test_closed_stage_failures_preserve_raw_and_hide_exception(  # type: ignore[no-untyped-def]
    module, tmp_path, monkeypatch, stage,
):
    archive = create(module, tmp_path)
    record = store(archive, f'<span>Welcome! {IDENTITY}</span>')

    def fail(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError(f"PrivateException {IDENTITY} {DISPLAY}")

    if stage == "IDENTITY_REGISTER":
        monkeypatch.setattr(archive.redactor, "register", fail)
    elif stage == "REDACT":
        monkeypatch.setattr(archive.redactor, "redact_registered", fail)
    elif stage in {"PRECHECK", "POSTCHECK"}:
        original = module.check
        calls = 0

        def injected(*args):  # type: ignore[no-untyped-def]
            nonlocal calls
            calls += 1
            if calls == (1 if stage == "PRECHECK" else 2):
                fail()
            return original(*args)

        monkeypatch.setattr(module, "check", injected)
    else:
        (archive.output / "01.response.html").mkdir()
    result = archive.finish(record)
    assert not result["ok"] and result["stage"] == stage
    assert result["registered_identities"] >= 0
    assert result["welcome_regions"] >= 0
    assert result["identity_replacement_count"] >= 0
    assert archive.private.exists()
    no_leaks(result)
    no_leaks(json.loads((archive.output / "run.json").read_text()))


def test_whole_directory_scan_blocks_then_offline_replay(module, tmp_path):  # type: ignore[no-untyped-def]
    archive = create(module, tmp_path)
    record = store(archive, f'<span>Welcome! {IDENTITY}</span>')
    old_file = archive.scan_root / "old-run.txt"
    old_file.write_text(IDENTITY)
    result = archive.finish(record)
    assert not result["ok"] and result["stage"] == "POSTCHECK"
    assert archive.private.exists()
    assert not (archive.output / "01.response.html").exists()
    old_file.write_text("<USER>")
    output = archive.scan_root / "replayed"
    process = subprocess.run([sys.executable, str(HERE / "redact_capture.py"),
                              "--replay", archive.private.name, "--output", str(output)],
                             capture_output=True, text=True, check=False)
    assert process.returncode == 0
    assert json.loads(process.stdout)["ok"]
    assert not archive.private.exists()
    assert (output / "01.response.html").is_file()
    no_leaks(process.stdout + process.stderr)


@pytest.mark.parametrize("flag", ["browser_closed", "profile_removed"])
def test_no_offline_redaction_before_cleanup(module, tmp_path, monkeypatch, flag):  # type: ignore[no-untyped-def]
    archive = create(module, tmp_path)
    record = store(archive, f'<span>Welcome! {IDENTITY}</span>')
    record[flag] = False

    def forbidden(*args):  # type: ignore[no-untyped-def]
        pytest.fail("redaction before browser cleanup")

    monkeypatch.setattr(archive.redactor, "register", forbidden)
    result = archive.finish(record)
    assert result["stage"] == "WRITE" and archive.private.exists()


def test_private_directory_must_not_be_in_repository(module, tmp_path, monkeypatch):  # type: ignore[no-untyped-def]
    monkeypatch.setenv("HOME", str(tmp_path / "repository/discovery-capture/private"))
    with pytest.raises(ValueError):
        create(module, tmp_path)


def test_private_directory_symlink_is_rejected(module, tmp_path, monkeypatch):  # type: ignore[no-untyped-def]
    real = tmp_path / "real-home"
    real.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    monkeypatch.setenv("HOME", os.fspath(alias))
    with pytest.raises(ValueError):
        create(module, tmp_path)
