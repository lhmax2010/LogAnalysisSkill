"""E6/E9 registry projections; registration alone does not prove scanner completion."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from terminal_predicates import load_json
from terminal_scan import DATA, ENTRY_KINDS, RULES, RULES_SHA, ScanError, sha256

NAMESPACES = frozenset({"consumer", "ledger", "scan", "resolve", "provider", "entry"})
ENTRY_OWNERS = {
    "entry.binary_record": "二进制记录器",
    "entry.name_backstop": "名字命中兜底",
    "entry.interpreter_line": "解释器行兜底",
    "entry.doctest_extract": "doctest 提取器",
}
LEGACY_OWNERS = {
    "ledger.seg1": "第一段",
    "scan.module": "UNREGISTERED_CANDIDATE + admission",
    "scan.reexport": "粒度②",
    "scan.inline": "粒度③",
    "scan.proxy_callable": "粒度④",
    "resolve.dynamic_attr": "解析层",
    "resolve.import_redirect": "解析层",
    "provider.unsupported": "provider 分类器",
}


def authority(root: Path) -> dict[str, str]:
    raw = (root / RULES).read_bytes()
    if sha256(raw) != RULES_SHA:
        raise ScanError("RULES_HASH")
    text = raw.decode()
    forms = re.findall(r"^(?:> )?\| `(C[0-9]+[a-z]?)` \|", text, re.MULTILINE)
    if len(forms) != len(set(forms)) or len(forms) != 24:
        raise ScanError("ATOMIC_TABLE_PARSE")
    nine = text.split("**(三)不覆盖清单", 1)[1].split("**兜底完整性**", 1)[0]
    table_rows = "\n".join(line for line in nine.splitlines() if line.startswith("|"))
    branches = set(re.findall(r"`((?:ledger|scan|resolve|provider)\.[^`]+)`", table_rows))
    if branches != LEGACY_OWNERS.keys():
        raise ScanError("NINE_TABLE_PARSE")
    e6 = text.split("**E6-1", 1)[1].split("**E6-2", 1)[0]
    entries = dict(re.findall(r"^> \| `(entry\.[^`]+)` \| ([^|]+?) \|", e6, re.MULTILINE))
    if entries != ENTRY_OWNERS:
        raise ScanError("ENTRY_TABLE_PARSE")
    return {**LEGACY_OWNERS, **entries, **{f"consumer.{f}": "消费者识别" for f in forms}}


def required_from_authority(root: Path) -> dict[str, list[str]]:
    domain = authority(root)
    text = (root / RULES).read_text()
    e4 = text.split("**E4-2", 1)[1].split("**E4-3", 1)[0]
    rows = re.findall(r"^> \| [0-9]+ \| `([A-Z_]+)` \|.*?\| ([^|]+) \|$", e4, re.MULTILINE)
    e9 = text.split("**E9-1", 1)[1].split("**E9-2", 1)[0]
    added = re.findall(r"^> \| 10a \| `([A-Z_]+)` \|.*?\| ([^|]+) \|$", e9, re.MULTILINE)
    if len(added) != 1:
        raise ScanError("E9_ENTRY_TABLE_PARSE")
    rows[10:10] = added
    if tuple(kind for kind, _ in rows) != ENTRY_KINDS:
        raise ScanError("ENTRY_KIND_TABLE_PARSE")
    result: dict[str, list[str]] = {}
    for kind, description in rows:
        # Parenthetical explanations may mention other detectors (BINARY does).
        description = re.sub(r"\([^()]*\)", "", description)
        required: set[str] = set()
        if "解析层" in description:
            required.update(b for b in domain if b.startswith("resolve."))
        if "provider 分类器" in description:
            required.add("provider.unsupported")
        if "四级粒度候选扫描" in description:
            required.update(b for b in domain if b.startswith("scan."))
        if "消费者参与点识别" in description:
            required.update(
                b for b in domain if b.startswith("consumer.") and not b.startswith("consumer.C7")
            )
        for form in ("C7a", "C7b", "C7c", "C7d", "C7e"):
            if f"{form} 识别" in description:
                required.add(f"consumer.{form}")
        for branch, owner in ENTRY_OWNERS.items():
            if owner in description:
                required.add(branch)
        if not required:
            raise ScanError(f"REQUIRED_EDGE_EMPTY: {kind}")
        result[kind] = sorted(required)
    return result


def pairs(registry: list[dict[str, Any]]) -> set[tuple[str, str]]:
    values = [(row["branch"], row["detector_owner"]) for row in registry]
    if len(values) != len(set(values)) or len(values) != len({b for b, _ in values}):
        raise ScanError("CAPABILITY_DUPLICATE")
    if any(b.split(".")[0] not in NAMESPACES for b, _ in values):
        raise ScanError("CAPABILITY_NAMESPACE")
    return set(values)


def reconcile_entry(
    root: Path,
    registry: list[dict[str, Any]],
    controls: list[dict[str, Any]],
) -> set[tuple[str, str]]:
    expected = {(b, o) for b, o in authority(root).items() if b.startswith("entry.")}
    mapped = {
        b
        for values in required_from_authority(root).values()
        for b in values
        if b.startswith("entry.")
    }
    actual = {(b, o) for b, o in pairs(registry) if b.startswith("entry.")}
    tested = {
        (c["branch"], c["detector_owner"])
        for c in controls
        if c.get("branch", "").startswith("entry.")
    }
    if {b for b, _ in expected} != mapped or actual != expected or tested != expected:
        raise ScanError(
            f"ENTRY_THREE_WAY: expected={sorted(expected)} "
            f"registry={sorted(actual)} controls={sorted(tested)}"
        )
    for branch, _ in expected:
        kinds = {c.get("polarity") for c in controls if c.get("branch") == branch}
        if not {"POSITIVE", "NEAR_MISS"} <= kinds:
            raise ScanError(f"ENTRY_CONTROLS_INCOMPLETE: {branch}")
    return actual


def reconcile_domains(
    root: Path,
    registry: list[dict[str, Any]],
    controls: list[dict[str, Any]],
    consumer_sources: list[set[tuple[str, str]]],
    legacy_sources: list[set[tuple[str, str]]],
) -> set[tuple[str, str]]:
    """The callers supply projections with retained raw records, not inferred passes."""
    entry = reconcile_entry(root, registry, controls)
    all_pairs = pairs(registry)
    consumer = {(b, o) for b, o in all_pairs if b.startswith("consumer.")}
    legacy = {(b, o) for b, o in all_pairs if b.split(".")[0] not in {"consumer", "entry"}}
    if len(consumer_sources) != 4 or any(s != consumer for s in consumer_sources):
        raise ScanError("CONSUMER_FIVE_WAY")
    if len(legacy_sources) != 3 or any(s != legacy for s in legacy_sources):
        raise ScanError("LEGACY_FOUR_WAY")
    if consumer | legacy | entry != set(authority(root).items()):
        raise ScanError("REGISTRY_UNION")
    return consumer | legacy | entry


def load_registry(root: Path) -> list[dict[str, Any]]:
    value = load_json(DATA / "capability_registry.json")
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise ScanError("REGISTRY_SHAPE")
    registry: list[dict[str, Any]] = list(value)
    if pairs(registry) != set(authority(root).items()):
        raise ScanError("REGISTRY_AUTHORITY_DIFFERENCE")
    if load_json(DATA / "entry_registry.json") != required_from_authority(root):
        raise ScanError("REQUIRED_EDGE_DIFFERENCE")
    return registry
