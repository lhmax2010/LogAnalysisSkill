"""Shared rules for suppressing misleading edit-spec skeleton rows."""

from __future__ import annotations

import re

STRUCTURAL_ONLY_LINE_COMPACTS = frozenset(
    {
        "",
        ";",
        ")",
        ");",
        "))",
        "));",
        "}",
        "};",
        "})",
        "});",
    }
)

MESSAGE_TOKEN_STOPWORDS = frozenset(
    {
        "Wdeprecated",
        "Werror",
        "declarations",
        "deprecated",
        "error",
        "is",
        "please",
        "use",
        "warning",
    }
)

IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def should_suppress_skeleton(old: str, message: str) -> str | None:
    """Return why an edit-spec skeleton row would be misleading, if known."""

    old_compact = "".join(old.strip().split())
    if old_compact in STRUCTURAL_ONLY_LINE_COMPACTS:
        return "structural_closing_line"

    tokens = tuple(_source_like_message_tokens(message))
    if tokens and not any(token in old for token in tokens):
        return "no_message_symbol_in_line"
    return None


def _source_like_message_tokens(message: str) -> tuple[str, ...]:
    tokens: list[str] = []
    for token in IDENTIFIER_RE.findall(message):
        if token in MESSAGE_TOKEN_STOPWORDS:
            continue
        if token.startswith("W"):
            continue
        if _looks_like_source_symbol(token):
            tokens.append(token)
    return tuple(dict.fromkeys(tokens))


def _looks_like_source_symbol(token: str) -> bool:
    # Conservative on purpose: lowercase words are often prose, so B/advisory covers them.
    return "_" in token or any(char.isupper() for char in token)
