"""Offline contract facts only; no KB implementation or state mutation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[7]
    output = Path(sys.argv[1]).resolve()
    output.mkdir(parents=True, exist_ok=False)
    log = root / "tests/fixtures/e2e_clang_compile/buildlog"
    argv = [sys.executable, "-m", "gbs_analyzer", "analyze", str(log),
            "--output-dir", str(output / "analyzer"), "--output-format", "both"]
    result = subprocess.run(argv, cwd=root, capture_output=True, text=True, check=False)
    (output / "analyzer.stdout.log").write_text(result.stdout)
    (output / "analyzer.stderr.log").write_text(result.stderr)
    assert result.returncode == 0
    evidence = json.loads((output / "analyzer/evidence_packet.json").read_text())

    def key_paths(value: object, prefix: str = "") -> list[str]:
        paths: list[str] = []
        if isinstance(value, dict):
            for key, child in value.items():
                path = f"{prefix}.{key}" if prefix else str(key)
                paths.append(path)
                paths.extend(key_paths(child, path))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                paths.extend(key_paths(child, f"{prefix}[{index}]"))
        return paths

    keys = key_paths(evidence)
    commit_paths = [key for key in keys if key.rsplit(".", 1)[-1] in {
        "baseline_commit", "base_commit", "revision", "commit_sha", "verified_tree_sha",
    }]
    assert not commit_paths
    fixed = {"mode", "edit_spec_path", "source_kind", "kb_precedent_ref", "context_dir",
             "t2_records", "downgrade_reason"}
    seven = dict(mode="generate", edit_spec_path=None, source_kind="generated",
                 kb_precedent_ref=None, context_dir="context", t2_records=[],
                 downgrade_reason=None)
    eight = dict(seven, needs_generation=True)
    candidates = []
    for name, value in (("seven_fields", seven), ("explicit_generation_flag", eight)):
        facts = dict(name=name, exact_fixed_keys=set(value) == fixed,
                     needs_generation_true=value.get("needs_generation") is True)
        assert not (facts["exact_fixed_keys"] and facts["needs_generation_true"])
        candidates.append(facts)
    print(json.dumps(dict(
        analyzer_argv=argv, analyzer_exit=result.returncode, log=str(log.relative_to(root)),
        log_text=log.read_text(), evidence_keys=keys, commit_paths=commit_paths,
        output_candidates=candidates,
        scope="Facts only; no inferred baseline, KB row, or output-contract decision.",
    ), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
