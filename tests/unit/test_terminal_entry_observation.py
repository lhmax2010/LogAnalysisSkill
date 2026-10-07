"""Artificial source enumeration; no OBS producer or real entry executes here."""

import importlib
import sys
from pathlib import Path

import pytest

saved = sys.path[:]
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "docs/clang-fix-campaign/tools"))
try:
    M = importlib.import_module("terminal_entry_observation")
finally:
    sys.path[:] = saved


def fixture_tree(root: Path) -> list[str]:
    paths = []
    for prefix in ("", "release-v1.4.0/"):
        files = {
            "pyproject.toml": (
                '[project]\n[tool.setuptools.packages.find]\nwhere=["skill/scripts"]\n'
            ),
            "skill/scripts/demo/__main__.py": "from demo import cli\n",
            "skill/scripts/run_demo.py": "from demo import cli\n",
            "skill/SKILL.md": (
                "`python -m demo` and `python -m demo`\n"
                "`scripts/run_demo.py`\n"
                "```bash\npython /path/to/skill/scripts/run_demo.py format-patch\n```\n"
            ),
        }
        for relative, contents in files.items():
            path = root / prefix / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents)
            paths.append(prefix + relative)
    return paths


def test_entry_enumeration_keeps_contexts_and_documentation_sites(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    files = fixture_tree(tmp_path)
    monkeypatch.setattr(M, "tracked", lambda root: files)
    result = M.enumerate_entries(tmp_path)
    assert len(result["entries"]) == 8
    assert len(set(result["independent_enumeration"])) == 8
    assert {row["context"] for row in result["entries"]} == {"", "release-v1.4.0"}
    assert all(row["argv"][-1] == "--help" for row in result["entries"])
    assert any(row["argv"][-2:] == ["format-patch", "--help"] for row in result["entries"])
    assert all(doc["invocations"] for doc in result["skill_documents"])


def test_entry_missing_launcher_fails_instead_of_dropping_documentation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    files = fixture_tree(tmp_path)
    files.remove("skill/scripts/run_demo.py")
    monkeypatch.setattr(M, "tracked", lambda root: files)
    with pytest.raises(ValueError, match="documented launcher not tracked"):
        M.enumerate_entries(tmp_path)


def test_entry_consumers_do_not_cross_packaging_contexts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    files = fixture_tree(tmp_path)
    monkeypatch.setattr(M, "tracked", lambda root: files)
    live = M.consumers(tmp_path, "demo", "")
    release = M.consumers(tmp_path, "demo", "release-v1.4.0")
    assert len(live) == len(release) == 2
    assert all(not p.startswith("release-v1.4.0/") for p in live)
    assert all(p.startswith("release-v1.4.0/") for p in release)
