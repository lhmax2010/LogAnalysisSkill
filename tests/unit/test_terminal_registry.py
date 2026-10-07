"""Artificial E6 projection checks, not scanner or detector acceptance tests."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
saved = sys.path[:]
sys.path.insert(0, str(ROOT / "docs/clang-fix-campaign/tools"))
try:
    R = importlib.import_module("terminal_registry")
finally:
    sys.path[:] = saved


def projections() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    registry = [
        {"branch": branch, "detector_owner": owner} for branch, owner in R.authority(ROOT).items()
    ]
    controls = [
        {"branch": branch, "detector_owner": owner, "polarity": polarity}
        for branch, owner in R.ENTRY_OWNERS.items()
        for polarity in ("POSITIVE", "NEAR_MISS")
    ]
    return registry, controls


def test_e6_namespaces_and_mapping() -> None:
    domain = R.authority(ROOT)
    mapping = R.required_from_authority(ROOT)
    assert {branch.split(".")[0] for branch in domain} == R.NAMESPACES
    assert tuple(mapping) == R.ENTRY_KINDS
    assert mapping["BINARY"] == ["entry.binary_record"]
    assert mapping["DOC"] == ["entry.doctest_extract", "entry.name_backstop"]
    assert mapping["GITLINK"] == ["resolve.dynamic_attr", "resolve.import_redirect"]
    assert mapping["IMPORTABLE_BINARY"] == ["provider.unsupported"]
    assert set(mapping["PY_SOURCE"]) == {
        b
        for b in domain
        if b.startswith(("scan.", "resolve.", "provider.", "consumer."))
        and not b.startswith("consumer.C7")
    } | {"entry.name_backstop"}
    for kind, form in zip(
        ("PACKAGING", "CI_CONFIG", "SHELL", "BUILD"), ("C7a", "C7b", "C7c", "C7d"), strict=True
    ):
        assert mapping[kind] == [
            f"consumer.{form}",
            "entry.interpreter_line",
            "entry.name_backstop",
        ]


def test_e6_entry_projection_positive() -> None:
    registry, controls = projections()
    assert R.reconcile_entry(ROOT, registry, controls) == set(R.ENTRY_OWNERS.items())


@pytest.mark.parametrize("branch", sorted(R.ENTRY_OWNERS))
def test_e6_missing_entry_projection_is_red(branch: str) -> None:
    registry, controls = projections()
    registry = [row for row in registry if row["branch"] != branch]
    with pytest.raises(R.ScanError, match="ENTRY_THREE_WAY"):
        R.reconcile_entry(ROOT, registry, controls)


def test_e6_wrong_owner_is_red() -> None:
    registry, controls = projections()
    for row in registry:
        if row["branch"] == "entry.binary_record":
            row["detector_owner"] = "wrong"
    with pytest.raises(R.ScanError, match="ENTRY_THREE_WAY"):
        R.reconcile_entry(ROOT, registry, controls)


def test_e6_missing_near_miss_projection_is_red() -> None:
    registry, controls = projections()
    controls = [row for row in controls if row["polarity"] != "NEAR_MISS"]
    with pytest.raises(R.ScanError, match="ENTRY_CONTROLS_INCOMPLETE"):
        R.reconcile_entry(ROOT, registry, controls)


@pytest.mark.parametrize("mutate", ["duplicate", "namespace"])
def test_e6_registry_shape_is_closed(mutate: str) -> None:
    registry, _ = projections()
    if mutate == "duplicate":
        registry.append(registry[0].copy())
        error = "CAPABILITY_DUPLICATE"
    else:
        registry.append({"branch": "other.fake", "detector_owner": "wrong"})
        error = "CAPABILITY_NAMESPACE"
    with pytest.raises(R.ScanError, match=error):
        R.pairs(registry)


@pytest.mark.parametrize("bad_group", [None, "consumer", "legacy"])
def test_e6_three_domain_projection_union(bad_group: str | None) -> None:
    registry, controls = projections()
    pairs = R.pairs(registry)
    consumer = [{(b, o) for b, o in pairs if b.startswith("consumer.")} for _ in range(4)]
    legacy = [
        {(b, o) for b, o in pairs if b.split(".")[0] not in {"consumer", "entry"}} for _ in range(3)
    ]
    if bad_group == "consumer":
        consumer[0] = set()
    elif bad_group == "legacy":
        legacy[0] = {(b, o) for b, o in pairs if not b.startswith("consumer.")}
    if bad_group is None:
        assert R.reconcile_domains(ROOT, registry, controls, consumer, legacy) == pairs
    else:
        error = "CONSUMER_FIVE_WAY" if bad_group == "consumer" else "LEGACY_FOUR_WAY"
        with pytest.raises(R.ScanError, match=error):
            R.reconcile_domains(ROOT, registry, controls, consumer, legacy)
