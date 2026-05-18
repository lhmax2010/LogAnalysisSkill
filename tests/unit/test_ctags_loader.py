import json
from pathlib import Path
from subprocess import CalledProcessError

from gbs_analyzer._utils.ctags_loader import extract_source_context


def source(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "foo.c"
    path.write_text(text, encoding="utf-8")
    return path


def test_ctags_context_uses_ctags_when_available(tmp_path: Path) -> None:
    path = source(
        tmp_path,
        "int helper(void) {\n"
        "  return 0;\n"
        "}\n"
        "int main(void) {\n"
        "  return helper();\n"
        "}\n",
    )

    def runner(_: Path) -> str:
        return json.dumps({"name": "main", "line": 4}) + "\n"

    context = extract_source_context(path, line=5, symbol="main", ctags_runner=runner)
    assert context.extraction_method == "ctags"
    assert context.start_line == 4
    assert "return helper" in context.text


def test_ctags_context_falls_back_to_regex_when_ctags_unavailable(tmp_path: Path) -> None:
    path = source(tmp_path, "int main(void) {\n  return 1;\n}\n")

    def runner(_: Path) -> str:
        raise CalledProcessError(1, "ctags")

    context = extract_source_context(path, line=2, ctags_runner=runner)
    assert context.extraction_method == "regex_brace"
    assert context.degraded is False


def test_ctags_context_falls_back_to_line_window_when_regex_cannot_match(
    tmp_path: Path,
) -> None:
    path = source(tmp_path, "\n".join(f"line {index}" for index in range(1, 80)))

    def runner(_: Path) -> str:
        raise OSError("ctags missing")

    context = extract_source_context(path, line=40, window=3, ctags_runner=runner)
    assert context.extraction_method == "line_window"
    assert context.degraded is True
    assert context.start_line == 37
    assert context.end_line == 43


def test_ctags_context_uses_symbol_match(tmp_path: Path) -> None:
    path = source(tmp_path, "int target(void) {\n  return 1;\n}\n")

    def runner(_: Path) -> str:
        return json.dumps({"name": "target", "line": 1}) + "\n"

    context = extract_source_context(path, symbol="target", ctags_runner=runner)
    assert context.extraction_method == "ctags"
    assert "target" in context.text
