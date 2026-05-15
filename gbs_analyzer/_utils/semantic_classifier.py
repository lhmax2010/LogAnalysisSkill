"""Semantic classification for root-cause ranking."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

DEFAULT_SEMANTICS_PATH = Path("patterns/error_semantics.yaml")


@dataclass(frozen=True)
class SemanticClass:
    name: str
    base_confidence: float
    cascade_probability: float
    default_level: int | str | None
    context_satisfied: bool = False


@dataclass(frozen=True)
class _SemanticRule:
    name: str
    base_confidence: float
    gated_base_confidence: float | None
    cascade_probability: float
    default_level: int | str | None
    patterns: tuple[re.Pattern[str], ...]


class SemanticClassifier:
    """Classify scanner events into the 8 v0.5 semantic classes."""

    def __init__(self, rules: list[_SemanticRule]) -> None:
        self.rules = rules
        self.by_name = {rule.name: rule for rule in rules}

    @classmethod
    def from_file(cls, path: str | Path = DEFAULT_SEMANTICS_PATH) -> SemanticClassifier:
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or raw.get("schema_version") != 1:
            raise ValueError("error semantics schema_version must be 1")
        classes = raw.get("semantic_classes", {})
        if not isinstance(classes, dict):
            raise ValueError("semantic_classes must be a mapping")

        rules: list[_SemanticRule] = []
        for name, spec in classes.items():
            if not isinstance(spec, dict):
                raise ValueError(f"{name}: semantic class spec must be a mapping")
            rules.append(
                _SemanticRule(
                    name=str(name),
                    base_confidence=float(spec["base_confidence"]),
                    gated_base_confidence=(
                        float(spec["gated_base_confidence"])
                        if spec.get("gated_base_confidence") is not None
                        else None
                    ),
                    cascade_probability=float(spec["cascade_probability"]),
                    default_level=spec.get("default_level"),
                    patterns=tuple(
                        re.compile(str(pattern), re.IGNORECASE)
                        for pattern in spec.get("patterns", [])
                    ),
                )
            )
        return cls(rules)

    def classify(self, event: dict[str, Any], scan_result: dict[str, Any]) -> SemanticClass:
        kind = event.get("kind")
        if kind == "linker_undef":
            return self._semantic("undefined_reference")
        if kind == "linker_missing":
            return self._semantic("missing_lib")

        message = str(event.get("message", ""))
        for rule in self.rules:
            if rule.name in {"generic_error", "undefined_reference", "missing_lib"}:
                continue
            if any(pattern.search(message) for pattern in rule.patterns):
                return self._semantic(rule.name)

        return self._generic(event, scan_result)

    def _semantic(self, name: str, *, context_satisfied: bool = False) -> SemanticClass:
        rule = self.by_name[name]
        return SemanticClass(
            name=rule.name,
            base_confidence=rule.base_confidence,
            cascade_probability=rule.cascade_probability,
            default_level=rule.default_level,
            context_satisfied=context_satisfied,
        )

    def _generic(self, event: dict[str, Any], scan_result: dict[str, Any]) -> SemanticClass:
        rule = self.by_name["generic_error"]
        context_satisfied = all(
            [
                event.get("command_id"),
                event.get("raw_offset") is not None,
                event.get("phase") == scan_result.get("failed_phase"),
                event.get("kind") not in ("make_cascade", "rpm_phase", "rpm_phase_failure"),
            ]
        )
        base = (
            rule.gated_base_confidence
            if context_satisfied and rule.gated_base_confidence is not None
            else rule.base_confidence
        )
        return SemanticClass(
            name=rule.name,
            base_confidence=base,
            cascade_probability=rule.cascade_probability,
            default_level=rule.default_level,
            context_satisfied=bool(context_satisfied),
        )


def classify_event(
    event: dict[str, Any],
    scan_result: dict[str, Any],
    classifier: SemanticClassifier | None = None,
) -> SemanticClass:
    """Classify one scanner event with the default semantic classifier."""

    active = classifier or SemanticClassifier.from_file()
    return active.classify(event, scan_result)
