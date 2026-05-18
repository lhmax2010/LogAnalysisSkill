import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = ROOT / "tests" / "fixtures"
E2E_FIXTURES = sorted(path for path in FIXTURE_ROOT.glob("e2e_*") if path.is_dir())


def fixture_id(path: Path) -> str:
    return path.name


@pytest.mark.parametrize("fixture", E2E_FIXTURES, ids=fixture_id)
def test_m8_e2e_fixture_contracts(fixture: Path, tmp_path: Path) -> None:
    packet, perf, completed, _elapsed = run_fixture(fixture, tmp_path)
    expected = load_expected(fixture)["expected"]

    assert completed.returncode == 0
    assert completed.stdout == ""
    assert (tmp_path / fixture.name / "evidence_packet.json").is_file()
    assert (tmp_path / fixture.name / "evidence_packet.md").is_file()
    assert (tmp_path / fixture.name / "perf_report.json").is_file()
    assert (tmp_path / fixture.name / "trace.jsonl").is_file()

    assert packet["schema_version"] == "evidence_packet/v1"
    assert packet["verdict"] == expected["verdict"]
    assert packet["via"] == expected["via"]
    assert packet.get("matched_tier") == expected["matched_tier"]
    assert packet["primary_error"].get("kind") == expected["primary_error_kind"]
    if expected.get("matched_patterns"):
        assert set(expected["matched_patterns"]).issubset(set(packet["matched_patterns"]))
    if expected.get("semantic_class"):
        assert packet["root_cause_candidates"][0]["semantic_class"] == expected["semantic_class"]
    if expected.get("uses_fallback_raw_context"):
        assert "fallback_context" in packet["evidence"]
        assert "fallback_raw_context_used" in packet["degraded_reasons"]
    if expected.get("budget_conservation"):
        assert packet["token_budget"]["conservation_ok"] is True

    assert perf["schema_version"] == "perf_report/v1"
    assert perf["execution"]["exit_status"] == "success"
    assert perf["execution"]["fast_path_hit"] == (packet["via"] == "fast_path")
    assert perf["decisions"]["verdict"] == packet["verdict"]
    assert perf["tokens"]["packet_tokens"] >= 1


def test_m8_acceptance_metrics(tmp_path: Path) -> None:
    start = time.perf_counter()
    packets: list[dict[str, Any]] = []
    expectations: list[dict[str, Any]] = []
    for fixture in E2E_FIXTURES:
        packet, _perf, completed, _elapsed = run_fixture(fixture, tmp_path)
        assert completed.returncode == 0, completed.stderr
        packets.append(packet)
        expectations.append(load_expected(fixture)["expected"])
    elapsed = time.perf_counter() - start

    assert len(packets) == 20
    fast_path_rate = sum(packet["via"] == "fast_path" for packet in packets) / len(packets)
    direct_answer_rate = (
        sum(packet["verdict"] == "direct_answer" for packet in packets) / len(packets)
    )
    top1_accuracy = (
        sum(
            packet["primary_error"].get("kind") == expected["primary_error_kind"]
            for packet, expected in zip(packets, expectations, strict=True)
        )
        / len(packets)
    )
    full_path_budget_packets = [
        packet
        for packet in packets
        if packet["via"] == "full_path" and "conservation_ok" in packet["token_budget"]
    ]
    budget_conservation_rate = (
        sum(
            packet["token_budget"]["conservation_ok"] is True
            for packet in full_path_budget_packets
        )
        / len(full_path_budget_packets)
    )

    assert fast_path_rate >= 0.25
    assert direct_answer_rate >= 0.35
    assert top1_accuracy >= 0.80
    assert budget_conservation_rate == 1.0
    assert elapsed < 15.0


def run_fixture(
    fixture: Path,
    output_root: Path,
) -> tuple[dict[str, Any], dict[str, Any], subprocess.CompletedProcess[str], float]:
    expected = load_expected(fixture)
    output_dir = output_root / fixture.name
    cmd = [
        sys.executable,
        "-m",
        "gbs_analyzer",
        "analyze",
        str(fixture / "buildlog"),
        "--src-root",
        str(resolve_src_root(fixture, expected)),
        "--output-dir",
        str(output_dir),
        "--output-format",
        "both",
        "--package",
        "demo",
        "--no-tiktoken",
    ]
    if expected.get("spec_path"):
        cmd.extend(["--spec-path", str(fixture / str(expected["spec_path"]))])

    start = time.perf_counter()
    completed = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    elapsed = time.perf_counter() - start
    packet_path = output_dir / "evidence_packet.json"
    perf_path = output_dir / "perf_report.json"
    packet = json.loads(packet_path.read_text(encoding="utf-8")) if packet_path.exists() else {}
    perf = json.loads(perf_path.read_text(encoding="utf-8")) if perf_path.exists() else {}
    return packet, perf, completed, elapsed


def resolve_src_root(fixture: Path, expected: dict[str, Any]) -> Path:
    value = expected.get("src_root")
    return fixture / str(value) if value else fixture


def load_expected(fixture: Path) -> dict[str, Any]:
    return json.loads((fixture / "expected_packet.json").read_text(encoding="utf-8"))
