"""Run gbs_analyzer as a subprocess for patch-suggest buildlog mode."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

ANALYZER_SKILL_ENV = "TIZEN_GBS_LOG_ANALYSIS_SKILL_DIR"
ANALYZER_SKILL_NAME = "tizen-gbs-log-analysis"
ANALYZER_PACKAGE_DIR = "gbs_analyzer"

SubprocessRunner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class AnalyzerRunResult:
    """Analyzer subprocess result for buildlog convenience mode."""

    exit_code: int
    output_dir: Path
    evidence_path: Path
    error: str | None = None


def run_analyzer_for_buildlog(
    buildlog_path: Path,
    *,
    output_dir: Path,
    src_root: Path | None = None,
    python_executable: str = sys.executable,
    subprocess_runner: SubprocessRunner = subprocess.run,
    extra_pythonpath: Sequence[str | Path] = (),
) -> AnalyzerRunResult:
    """Run analyzer CLI and return the generated evidence path."""

    if not buildlog_path.is_file():
        return AnalyzerRunResult(
            exit_code=3,
            output_dir=output_dir,
            evidence_path=output_dir / "evidence_packet.json",
            error=f"buildlog is not readable: {buildlog_path}",
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        python_executable,
        "-m",
        "gbs_analyzer",
        "analyze",
        str(buildlog_path),
        "--output-dir",
        str(output_dir),
    ]
    if src_root is not None:
        command.extend(["--src-root", str(src_root)])

    env = build_analyzer_subprocess_env(extra_pythonpath)
    kwargs: dict[str, object] = {"check": True, "text": True}
    if env is not None:
        kwargs["env"] = env

    try:
        subprocess_runner(command, **kwargs)
    except subprocess.CalledProcessError as exc:
        return AnalyzerRunResult(
            exit_code=1,
            output_dir=output_dir,
            evidence_path=output_dir / "evidence_packet.json",
            error=f"gbs_analyzer exited with {exc.returncode}",
        )

    evidence_path = output_dir / "evidence_packet.json"
    if not evidence_path.is_file():
        return AnalyzerRunResult(
            exit_code=3,
            output_dir=output_dir,
            evidence_path=evidence_path,
            error=f"gbs_analyzer did not write evidence_packet.json: {evidence_path}",
        )
    return AnalyzerRunResult(exit_code=0, output_dir=output_dir, evidence_path=evidence_path)


def build_analyzer_subprocess_env(extra_pythonpath: Sequence[str | Path]) -> dict[str, str] | None:
    """Return subprocess env with extra analyzer Python paths prepended."""

    if not extra_pythonpath:
        return None
    env = os.environ.copy()
    entries = [str(Path(path)) for path in extra_pythonpath]
    existing = env.get("PYTHONPATH")
    if existing:
        entries.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(entries)
    return env


def discover_analyzer_pythonpath(*, launcher_path: Path | None = None) -> tuple[Path, ...]:
    """Return analyzer sibling scripts path when available for direct-folder usage."""

    env_path = _env_skill_scripts(ANALYZER_SKILL_ENV, ANALYZER_PACKAGE_DIR)
    if env_path is not None:
        return (env_path,)
    sibling_path = _sibling_skill_scripts(
        ANALYZER_SKILL_NAME,
        ANALYZER_PACKAGE_DIR,
        launcher_path=launcher_path,
    )
    if sibling_path is not None:
        return (sibling_path,)
    return ()


def _env_skill_scripts(env_name: str, package_dir: str) -> Path | None:
    raw = os.environ.get(env_name)
    if not raw:
        return None
    root = Path(raw).expanduser().resolve()
    candidates = [root / "scripts", root] if root.name != "scripts" else [root]
    for candidate in candidates:
        if (candidate / package_dir).is_dir():
            return candidate
    raise RuntimeError(f"{env_name} must point to a skill root or scripts directory")


def _sibling_skill_scripts(
    skill_name: str,
    package_dir: str,
    *,
    launcher_path: Path | None,
) -> Path | None:
    if launcher_path is None:
        return None
    skill_root = launcher_path.resolve().parents[1]
    candidate = skill_root.parent / skill_name / "scripts"
    if (candidate / package_dir).is_dir():
        return candidate
    return None
