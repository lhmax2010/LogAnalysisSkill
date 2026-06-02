"""Launcher for the local tizen-gbs-build-workflow skill."""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

BUILD_SKILL_ENV = "TIZEN_GBS_BUILD_SKILL_DIR"
ANALYZER_SKILL_ENV = "TIZEN_GBS_LOG_ANALYSIS_SKILL_DIR"
PATCH_SUGGEST_SKILL_ENV = "TIZEN_GBS_PATCH_SUGGEST_SKILL_DIR"
MISSING_DEPENDENCY_MESSAGE = (
    "Install tizen-gbs-build and tizen-gbs-log-analysis next to this skill, "
    "or set TIZEN_GBS_BUILD_SKILL_DIR and TIZEN_GBS_LOG_ANALYSIS_SKILL_DIR."
)


def _add_python_path(path: Path, added: list[Path]) -> bool:
    resolved = path.resolve()
    if str(resolved) in sys.path:
        return False
    sys.path.insert(0, str(resolved))
    added.append(resolved)
    return True


def _env_skill_scripts(env_name: str, package_dir: str) -> Path | None:
    import os

    raw = os.environ.get(env_name)
    if not raw:
        return None
    root = Path(raw).expanduser().resolve()
    candidates = [root / "scripts", root] if root.name != "scripts" else [root]
    for candidate in candidates:
        if (candidate / package_dir).is_dir():
            return candidate
    raise RuntimeError(f"{env_name} must point to a skill root or scripts directory")


def _sibling_skill_scripts(skill_name: str, package_dir: str) -> Path | None:
    workflow_root = Path(__file__).resolve().parents[1]
    candidate = workflow_root.parent / skill_name / "scripts"
    if (candidate / package_dir).is_dir():
        return candidate
    return None


def _dependency_scripts(
    *,
    env_name: str,
    skill_name: str,
    package_dir: str,
) -> Path:
    env_path = _env_skill_scripts(env_name, package_dir)
    if env_path is not None:
        return env_path
    sibling_path = _sibling_skill_scripts(skill_name, package_dir)
    if sibling_path is not None:
        return sibling_path
    raise RuntimeError(MISSING_DEPENDENCY_MESSAGE)


def _optional_dependency_scripts(
    *,
    env_name: str,
    skill_name: str,
    package_dir: str,
) -> Path | None:
    try:
        env_path = _env_skill_scripts(env_name, package_dir)
    except RuntimeError:
        env_path = None
    if env_path is not None:
        return env_path
    return _sibling_skill_scripts(skill_name, package_dir)


def _load_main() -> tuple[Callable[..., int], tuple[Path, ...]]:
    added_paths: list[Path] = []
    own_scripts = Path(__file__).resolve().parent

    while True:
        try:
            from gbs_workflow.workflow import main

            return main, tuple(added_paths)
        except ModuleNotFoundError as exc:
            if exc.name == "gbs_workflow":
                added = _add_python_path(own_scripts, added_paths)
            elif exc.name == "gbs_build_skill":
                added = _add_python_path(
                    _dependency_scripts(
                        env_name=BUILD_SKILL_ENV,
                        skill_name="tizen-gbs-build",
                        package_dir="gbs_build_skill",
                    ),
                    added_paths,
                )
            elif exc.name == "gbs_analyzer":
                added = _add_python_path(
                    _dependency_scripts(
                        env_name=ANALYZER_SKILL_ENV,
                        skill_name="tizen-gbs-log-analysis",
                        package_dir="gbs_analyzer",
                    ),
                    added_paths,
                )
            else:
                raise
            if not added:
                raise RuntimeError(MISSING_DEPENDENCY_MESSAGE) from exc


if __name__ == "__main__":
    try:
        workflow_main, pythonpath = _load_main()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    patch_suggest_path = _optional_dependency_scripts(
        env_name=PATCH_SUGGEST_SKILL_ENV,
        skill_name="tizen-gbs-patch-suggest",
        package_dir="gbs_patch_suggest",
    )
    patch_pythonpath = (patch_suggest_path,) if patch_suggest_path is not None else ()
    raise SystemExit(
        workflow_main(
            None,
            analyzer_extra_pythonpath=pythonpath,
            patch_suggest_extra_pythonpath=patch_pythonpath,
        )
    )
