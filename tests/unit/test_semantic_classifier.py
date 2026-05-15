from pathlib import Path

import pytest

from gbs_analyzer._utils.semantic_classifier import SemanticClassifier, classify_event


def scan_context(failed_phase: str | None = "%build") -> dict[str, object]:
    return {"failed_phase": failed_phase}


def event(message: str, **overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "id": "E001",
        "kind": "compiler",
        "message": message,
        "command_id": "C001",
        "raw_offset": 10,
        "phase": "%build",
    }
    data.update(overrides)
    return data


def test_load_semantic_classifier() -> None:
    classifier = SemanticClassifier.from_file()
    assert set(classifier.by_name) == {
        "syntax_error",
        "undeclared_identifier",
        "no_member",
        "type_mismatch",
        "template_instantiation",
        "undefined_reference",
        "missing_lib",
        "generic_error",
    }


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("syntax error before '}' token", "syntax_error"),
        ("use of undeclared identifier 'foo'", "undeclared_identifier"),
        ("no member named 'bar' in 'Foo'", "no_member"),
        ("cannot convert 'int' to 'char *'", "type_mismatch"),
        ("template instantiation failed", "template_instantiation"),
    ],
)
def test_classifies_compiler_messages(message: str, expected: str) -> None:
    assert classify_event(event(message), scan_context()).name == expected


def test_classifies_linker_undefined_by_event_kind() -> None:
    sem = classify_event(event("anything", kind="linker_undef"), scan_context())
    assert sem.name == "undefined_reference"
    assert sem.base_confidence == 0.85


def test_classifies_linker_missing_by_event_kind() -> None:
    sem = classify_event(event("anything", kind="linker_missing"), scan_context())
    assert sem.name == "missing_lib"
    assert sem.base_confidence == 0.95


def test_generic_error_uses_gated_confidence_when_context_satisfied() -> None:
    sem = classify_event(event("error: generic failure"), scan_context())
    assert sem.name == "generic_error"
    assert sem.base_confidence == 0.70
    assert sem.context_satisfied is True


def test_generic_error_uses_low_confidence_without_context() -> None:
    sem = classify_event(event("error: generic failure", phase="%install"), scan_context())
    assert sem.name == "generic_error"
    assert sem.base_confidence == 0.45
    assert sem.context_satisfied is False


def test_generic_error_does_not_gate_make_cascade() -> None:
    sem = classify_event(event("make failed", kind="make_cascade"), scan_context())
    assert sem.name == "generic_error"
    assert sem.base_confidence == 0.45


@pytest.mark.parametrize(
    "overrides",
    [
        {"command_id": None},
        {"raw_offset": None},
        {"phase": "%install"},
        {"kind": "make_cascade"},
    ],
)
def test_generic_error_gate_fails_when_one_required_context_is_missing(
    overrides: dict[str, object],
) -> None:
    sem = classify_event(event("error: generic failure", **overrides), scan_context())
    assert sem.name == "generic_error"
    assert sem.base_confidence == 0.45
    assert sem.context_satisfied is False


def test_generic_error_gate_fails_when_all_required_context_is_missing() -> None:
    sem = classify_event(
        event(
            "error: generic failure",
            command_id=None,
            raw_offset=None,
            phase="%install",
            kind="make_cascade",
        ),
        scan_context(),
    )
    assert sem.name == "generic_error"
    assert sem.base_confidence == 0.45
    assert sem.context_satisfied is False


def test_rejects_bad_schema_version(tmp_path: Path) -> None:
    path = tmp_path / "semantics.yaml"
    path.write_text("schema_version: 2\nsemantic_classes: {}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="schema_version"):
        SemanticClassifier.from_file(path)


def test_rejects_non_mapping_classes(tmp_path: Path) -> None:
    path = tmp_path / "semantics.yaml"
    path.write_text("schema_version: 1\nsemantic_classes: []\n", encoding="utf-8")
    with pytest.raises(ValueError, match="semantic_classes"):
        SemanticClassifier.from_file(path)
