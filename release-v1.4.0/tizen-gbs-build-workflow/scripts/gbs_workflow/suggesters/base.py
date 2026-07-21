"""Base types for workflow suggestion generators."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Suggestion:
    """A workflow suggestion rendered as markdown and optionally a git patch."""

    suggester: str
    title: str
    description: str
    patch_content: str | None
    target_files: list[str]
    confidence: str
    risks: list[str]
    manual_steps: list[str] | None


class SuggesterBase(ABC):
    """Generate suggestions for one class of evidence packet."""

    @abstractmethod
    def matches(self, packet: dict[str, Any]) -> bool:
        """Return true when this suggester should inspect a packet."""

    @abstractmethod
    def generate(self, packet: dict[str, Any], src_root: Path) -> list[Suggestion]:
        """Return zero or more suggestions for a matched packet."""
