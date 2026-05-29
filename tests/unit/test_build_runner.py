import os
import subprocess
import sys
from pathlib import Path

from gbs_build_skill.runner import (
    DEFAULT_TIMEOUT_SECONDS,
    EXIT_ARGS,
    EXIT_COMMAND_NOT_FOUND,
    EXIT_TIMEOUT,
    BuildOptions,
    _extract_failure_log_path,
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
    assert result.failure_log_path is None
    assert result.analysis_log_path == output_log
    assert result.package_name is None
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
    assert result.analysis_log_path == output_log
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
    assert result.analysis_log_path == output_log
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


def test_python_module_invocation_runs_fake_gbs(tmp_path: Path) -> None:
    write_executable(
        tmp_path / "gbs",
        """
print("module invocation output")
""",
    )
    output_log = tmp_path / "module.log"
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}:{env.get('PATH', '')}"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "gbs_build_skill",
            "--conf",
            str(tmp_path / "gbs.conf"),
            "--arch",
            "armv7l",
            "--output-log",
            str(output_log),
        ],
        capture_output=True,
        cwd=tmp_path,
        env=env,
        text=True,
        timeout=10,
        check=False,
    )

    assert result.returncode == 0
    assert "build succeeded (exit 0)" in result.stderr
    assert "compiler log written to" in result.stderr
    assert output_log.read_text(encoding="utf-8") == "module invocation output\n"


def test_extract_failure_log_path_returns_path_and_package(tmp_path: Path) -> None:
    failure_log = tmp_path / "GBS-ROOT/local/repos/tizen/armv7l/logs/fail/ffmpeg-8.0.1-0/log.txt"
    failure_log.parent.mkdir(parents=True)
    failure_log.write_text("real failure\n", encoding="utf-8")
    compiler_log = tmp_path / "compiler.log"
    compiler_log.write_text(
        f"warning: build failed, Leaving the logs in {failure_log}\n",
        encoding="utf-8",
    )

    path, package = _extract_failure_log_path(compiler_log)

    assert path == failure_log
    assert package == "ffmpeg-8.0.1-0"


def test_extract_failure_log_path_uses_last_existing_match(tmp_path: Path) -> None:
    first_log = tmp_path / "root/local/repos/tizen/armv7l/logs/fail/first-1/log.txt"
    second_log = tmp_path / "root/local/repos/tizen/armv7l/logs/fail/second-2/log.txt"
    first_log.parent.mkdir(parents=True)
    second_log.parent.mkdir(parents=True)
    first_log.write_text("first\n", encoding="utf-8")
    second_log.write_text("second\n", encoding="utf-8")
    compiler_log = tmp_path / "compiler.log"
    compiler_log.write_text(
        "\n".join(
            [
                f"Leaving the logs in {first_log}",
                f"Leaving the logs in {second_log}",
            ]
        ),
        encoding="utf-8",
    )

    path, package = _extract_failure_log_path(compiler_log)

    assert path == second_log
    assert package == "second-2"


def test_extract_failure_log_path_returns_none_without_match(tmp_path: Path) -> None:
    compiler_log = tmp_path / "compiler.log"
    compiler_log.write_text("no structured log here\n", encoding="utf-8")

    assert _extract_failure_log_path(compiler_log) == (None, None)


def test_extract_failure_log_path_returns_none_when_file_missing(tmp_path: Path) -> None:
    missing_log = tmp_path / "root/local/repos/tizen/armv7l/logs/fail/pkg-1/log.txt"
    compiler_log = tmp_path / "compiler.log"
    compiler_log.write_text(f"Leaving the logs in {missing_log}\n", encoding="utf-8")

    assert _extract_failure_log_path(compiler_log) == (None, None)


def test_run_gbs_build_sets_failure_and_analysis_log_when_failure_log_exists(
    tmp_path: Path,
) -> None:
    failure_log = tmp_path / "root/local/repos/tizen/armv7l/logs/fail/pkg-1/log.txt"
    failure_log.parent.mkdir(parents=True)
    failure_log.write_text("failure detail\n", encoding="utf-8")
    fake_gbs = write_executable(
        tmp_path / "gbs",
        f"""
import sys
print("warning: build failed, Leaving the logs in {failure_log}")
sys.exit(1)
""",
    )

    result = run_gbs_build(
        BuildOptions(
            conf=tmp_path / "gbs.conf",
            arch="armv7l",
            output_log=tmp_path / "compiler.log",
            gbs_binary=str(fake_gbs),
        )
    )

    assert result.exit_code == 1
    assert result.log_path == tmp_path / "compiler.log"
    assert result.failure_log_path == failure_log
    assert result.analysis_log_path == failure_log
    assert result.package_name == "pkg-1"


def test_run_gbs_build_falls_back_to_compiler_log_when_failure_log_missing(
    tmp_path: Path,
) -> None:
    fake_gbs = write_executable(
        tmp_path / "gbs",
        """
import sys
print("warning: build failed, no structured log")
sys.exit(1)
""",
    )
    output_log = tmp_path / "compiler.log"

    result = run_gbs_build(
        BuildOptions(
            conf=tmp_path / "gbs.conf",
            arch="armv7l",
            output_log=output_log,
            gbs_binary=str(fake_gbs),
        )
    )

    assert result.exit_code == 1
    assert result.failure_log_path is None
    assert result.analysis_log_path == output_log
    assert result.package_name is None


def test_cli_src_dir_runs_gbs_from_source_directory(tmp_path: Path) -> None:
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    write_executable(
        tmp_path / "gbs",
        """
from pathlib import Path
print(Path.cwd())
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
                "--src-dir",
                str(src_dir),
            ]
        )
    finally:
        os.environ["PATH"] = old_path

    assert exit_code == 0
    assert output_log.read_text(encoding="utf-8").strip() == str(src_dir.resolve())


def test_cli_src_dir_missing_returns_argument_error(tmp_path: Path, capsys: object) -> None:
    output_log = tmp_path / "compiler.log"

    exit_code = main(
        [
            "--conf",
            str(tmp_path / "gbs.conf"),
            "--arch",
            "armv7l",
            "--output-log",
            str(output_log),
            "--src-dir",
            str(tmp_path / "missing"),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == EXIT_ARGS
    assert "source directory not found" in captured.err
