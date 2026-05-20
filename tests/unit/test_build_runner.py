import os
import sys
from pathlib import Path

from gbs_build_skill.runner import (
    DEFAULT_TIMEOUT_SECONDS,
    EXIT_COMMAND_NOT_FOUND,
    EXIT_TIMEOUT,
    BuildOptions,
    build_command,
    main,
    run_gbs_build,
)


def write_executable(path: Path, body: str) -> Path:
    path.write_text(f"#!{sys.executable}\n{body}", encoding="utf-8")
    path.chmod(path.stat().st_mode | 0o111)
    return path


def test_build_command_includes_required_gbs_args(tmp_path: Path) -> None:
    options = BuildOptions(
        conf=tmp_path / "gbs.conf",
        arch="armv7l",
        output_log=tmp_path / "build.log",
        include_all=True,
    )

    assert build_command(options) == [
        "gbs",
        "-c",
        str(tmp_path / "gbs.conf"),
        "build",
        "-A",
        "armv7l",
        "--include-all",
    ]


def test_build_command_omits_include_all_when_disabled(tmp_path: Path) -> None:
    options = BuildOptions(
        conf=tmp_path / "gbs.conf",
        arch="x86_64",
        output_log=tmp_path / "build.log",
    )

    assert "--include-all" not in build_command(options)


def test_run_gbs_build_streams_stdout_and_stderr_and_passthrough_exit(
    tmp_path: Path,
) -> None:
    fake_gbs = write_executable(
        tmp_path / "fake_gbs.py",
        """
import sys
print("stdout line")
print("stderr line", file=sys.stderr)
sys.exit(7)
""",
    )
    output_log = tmp_path / "logs" / "compiler.log"

    result = run_gbs_build(
        BuildOptions(
            conf=tmp_path / "gbs.conf",
            arch="armv7l",
            output_log=output_log,
            include_all=True,
            gbs_binary=str(fake_gbs),
            cwd=tmp_path,
        )
    )

    assert result.exit_code == 7
    assert result.timed_out is False
    assert result.log_path == output_log
    assert result.command[-1] == "--include-all"
    assert "stdout line" in output_log.read_text(encoding="utf-8")
    assert "stderr line" in output_log.read_text(encoding="utf-8")


def test_run_gbs_build_returns_124_on_timeout(tmp_path: Path) -> None:
    fake_gbs = write_executable(
        tmp_path / "slow_gbs.py",
        """
import time
print("starting")
time.sleep(10)
""",
    )
    output_log = tmp_path / "compiler.log"

    result = run_gbs_build(
        BuildOptions(
            conf=tmp_path / "gbs.conf",
            arch="armv7l",
            output_log=output_log,
            timeout=0,
            gbs_binary=str(fake_gbs),
        )
    )

    assert result.exit_code == EXIT_TIMEOUT
    assert result.timed_out is True
    assert "timeout after 0s" in output_log.read_text(encoding="utf-8")


def test_run_gbs_build_returns_127_when_gbs_binary_missing(tmp_path: Path) -> None:
    output_log = tmp_path / "compiler.log"

    result = run_gbs_build(
        BuildOptions(
            conf=tmp_path / "gbs.conf",
            arch="armv7l",
            output_log=output_log,
            gbs_binary=str(tmp_path / "missing-gbs"),
        )
    )

    assert result.exit_code == EXIT_COMMAND_NOT_FOUND
    assert result.timed_out is False
    assert "command not found" in output_log.read_text(encoding="utf-8")


def test_cli_main_returns_runner_exit_code_and_writes_log(tmp_path: Path) -> None:
    write_executable(
        tmp_path / "gbs",
        """
import sys
print("cli output")
sys.exit(3)
""",
    )
    old_path = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{tmp_path}:{old_path}"
    try:
        output_log = tmp_path / "compiler.log"
        exit_code = main(
            [
                "--conf",
                str(tmp_path / "gbs.conf"),
                "--arch",
                "armv7l",
                "--output-log",
                str(output_log),
                "--timeout",
                str(DEFAULT_TIMEOUT_SECONDS),
            ]
        )
    finally:
        os.environ["PATH"] = old_path

    assert exit_code == 3
    assert output_log.read_text(encoding="utf-8") == "cli output\n"
