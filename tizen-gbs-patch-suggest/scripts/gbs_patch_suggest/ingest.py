"""Evidence Packet ingestion for patch context preparation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CompileErrorEvidence:
    """First diagnostic selected from an analyzer Evidence Packet."""

    kind: str
    message: str
    semantic_class: str
    file: str | None = None
    line: int | None = None
    column: int | None = None
    source_snippet: dict[str, Any] | None = None
    raw_primary_error: dict[str, Any] | None = None

    @property
    def is_compiler(self) -> bool:
        return self.kind == "compiler"


def load_evidence_packet(path: Path) -> dict[str, Any]:
    """Read analyzer evidence packet JSON."""

    raw = path.read_text(encoding="utf-8")
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("evidence packet must be a JSON object")
    return parsed


def extract_first_diagnostic(packet: dict[str, Any]) -> CompileErrorEvidence:
    """Extract the primary analyzer diagnostic and semantic class."""

    primary = packet.get("primary_error")
    if not isinstance(primary, dict):
        primary = {}

    evidence = packet.get("evidence")
    if not isinstance(evidence, dict):
        evidence = {}
    source_snippet = evidence.get("source_snippet")
    if not isinstance(source_snippet, dict):
        source_snippet = None

    return CompileErrorEvidence(
        kind=_string(primary.get("kind"), default="unknown"),
        message=_string(primary.get("message"), default=""),
        semantic_class=_semantic_class(packet, primary),
        file=_optional_string(primary.get("file")),
        line=_optional_int(primary.get("line")),
        column=_optional_int(primary.get("column")),
        source_snippet=source_snippet,
        raw_primary_error=primary,
    )


def _semantic_class(packet: dict[str, Any], primary: dict[str, Any]) -> str:
    direct = primary.get("semantic_class") or primary.get("category")
    if direct:
        return str(direct)
    candidates = packet.get("root_cause_candidates")
    if isinstance(candidates, list) and candidates:
        first = candidates[0]
        if isinstance(first, dict) and first.get("semantic_class"):
            return str(first["semantic_class"])
    return "unknown"


def _string(value: Any, *, default: str) -> str:
    return value if isinstance(value, str) else default


def _optional_string(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _optional_int(value: Any) -> int | None:
    return value if isinstance(value, int) else None
