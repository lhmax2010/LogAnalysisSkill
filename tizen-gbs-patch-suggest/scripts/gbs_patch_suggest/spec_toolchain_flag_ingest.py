"""Ingest Clang unknown warning-option diagnostics for spec flag fixes."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

UNKNOWN_WARNING_RE = re.compile(r"unknown warning option ['\"](?P<option>-W(?:no-)?[^'\"]+)['\"]")
WARNING_OPTION_MARKER = "-Wunknown-warning-option"


@dataclass(frozen=True)
class SpecToolchainFlagDiagnostic:
    """Unknown Clang warning option details extracted from evidence."""

    options: tuple[str, ...]
    messages: tuple[str, ...]

    @property
    def has_options(self) -> bool:
        return bool(self.options)


def ingest_spec_toolchain_flags(packet: dict[str, Any]) -> SpecToolchainFlagDiagnostic:
    """Return unknown warning options visible in analyzer evidence."""

    messages = tuple(_iter_candidate_messages(packet))
    options: list[str] = []
    seen: set[str] = set()
    for message in messages:
        if WARNING_OPTION_MARKER not in message and "unknown warning option" not in message:
            continue
        for match in UNKNOWN_WARNING_RE.finditer(message):
            option = match.group("option")
            if option not in seen:
                seen.add(option)
                options.append(option)
    return SpecToolchainFlagDiagnostic(options=tuple(options), messages=messages)


def _iter_candidate_messages(packet: dict[str, Any]) -> list[str]:
    messages: list[str] = []
    primary = packet.get("primary_error")
    if isinstance(primary, dict):
        message = primary.get("message")
        if isinstance(message, str):
            messages.append(message)
    candidates = packet.get("root_cause_candidates")
    if isinstance(candidates, list):
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            message = candidate.get("message")
            if isinstance(message, str):
                messages.append(message)
    return messages
