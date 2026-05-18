"""Example Compiling Agent adapter for the GBS analyzer wrapper."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, cast


class GbsLogAnalysisIntegration:
    """Small subprocess wrapper for unattended build-monitoring agents."""

    def __init__(
        self,
        analyzer_path: str = "python -m gbs_analyzer",
        output_dir: str | Path = "/tmp/gbs_analysis_agent",
    ) -> None:
        self.analyzer_path = analyzer_path
        self.output_dir = Path(output_dir)

    def analyze(
        self,
        buildlog_path: str | Path,
        *,
        src_root: str | Path = "auto",
        max_tokens: int = 1800,
        timeout: int = 30,
    ) -> dict[str, Any]:
        """Return an Evidence Packet or a degraded error packet."""

        cmd = [
            *self.analyzer_path.split(),
            "analyze",
            str(buildlog_path),
            "--src-root",
            str(src_root),
            "--max-tokens",
            str(max_tokens),
            "--output-format",
            "json",
            "--output-dir",
            str(self.output_dir),
        ]
        try:
            subprocess.run(cmd, capture_output=True, timeout=timeout, check=True)
            packet_path = self.output_dir / "evidence_packet.json"
            return cast(dict[str, Any], json.loads(packet_path.read_text(encoding="utf-8")))
        except subprocess.TimeoutExpired:
            return _degraded_packet("analyzer_timeout")
        except subprocess.CalledProcessError as exc:
            return _degraded_packet(f"analyzer_exit_{exc.returncode}")
        except OSError as exc:
            return _degraded_packet(f"analyzer_os_error:{exc}")

    def feed_to_llm(self, packet: dict[str, Any], llm_client: Any) -> str:
        """Use direct answers when available, otherwise send the packet prompt."""

        if packet.get("verdict") == "direct_answer":
            return str(packet.get("direct_answer", ""))
        prompt = packet.get("prompt")
        if not prompt:
            return "Analysis failed; please inspect the raw buildlog."
        return str(llm_client.complete(prompt))


def _degraded_packet(reason: str) -> dict[str, Any]:
    return {
        "schema_version": "evidence_packet/v1",
        "verdict": "needs_llm",
        "via": "wrapper_error",
        "degraded": True,
        "degraded_reasons": [reason],
        "prompt": None,
        "allowed_next_actions": [],
    }
