"""Read-only source predicates plus the real policy/guard, without review execution."""

from __future__ import annotations

import ast
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace


def main() -> None:
    repo = Path(__file__).resolve().parents[6]
    for package in ("tizen-campaign-core", "tizen-build-verify", "tizen-ci-shared"):
        sys.path.insert(0, str(repo / package / "scripts"))
    from tizen_campaign_core.suppress_policy import evaluate

    source_path = repo / "tizen-review-submit/scripts/tizen_review_submit/review_submit.py"
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    run = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "run"
    )
    source_gate = [
        node for node in ast.walk(run)
        if isinstance(node, ast.If) and 'policy.get(\'edit_source_kind\')' in ast.unparse(node.test)
    ]
    a2_gate = [
        node for node in ast.walk(run)
        if isinstance(node, ast.If)
        and "verdict.fix_strategy_final != 'code'" in ast.unparse(node.test)
    ]
    assert len(source_gate) == len(a2_gate) == 1

    def rejected(node: ast.If, scope: dict[str, object]) -> bool:
        expression = ast.Expression(body=node.test)
        return eval(compile(expression, str(source_path), "eval"), {"__builtins__": {}}, scope)

    results = []
    with tempfile.TemporaryDirectory(prefix="skel-restore-policy-") as temporary:
        root = Path(temporary)
        (root / "sample.c").write_text("int f(void) { return 1; }\n", encoding="utf-8")
        edit = {
            "schema_version": "gbs_patch_suggest/edit-spec/v1",
            "patch_name": "offline-policy-probe",
            "edits": [{"file": "sample.c", "old": "return 1", "new": "return 0"}],
        }
        for kind in ("generated", "t1_cherry_pick", "suppress"):
            verdict = evaluate(edit, root, kind)
            scope = {
                "policy": {"edit_source_kind": kind},
                "verdict": verdict,
                "view": SimpleNamespace(reproduced=True),
            }
            results.append({
                "source_kind": kind,
                "policy_verdict": verdict.verdict,
                "fix_strategy_final": verdict.fix_strategy_final,
                "current_source_gate_rejects": rejected(source_gate[0], scope),
                "current_a2_rejects_if_reached": rejected(a2_gate[0], scope),
            })
        fixture_path = str(root)
    assert results[0]["current_source_gate_rejects"] is False
    assert results[0]["current_a2_rejects_if_reached"] is False
    assert results[1]["policy_verdict"] == "allowed"
    assert results[1]["fix_strategy_final"] == "cherry_pick"
    assert results[1]["current_source_gate_rejects"] is True
    assert results[1]["current_a2_rejects_if_reached"] is True
    assert results[2]["current_a2_rejects_if_reached"] is True
    print(json.dumps({
        "scope": "real guard/policy and unmodified AST predicates, not an end-to-end review run",
        "source": str(source_path.relative_to(repo)),
        "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "source_gate_line": source_gate[0].lineno,
        "source_gate_predicate": ast.unparse(source_gate[0].test),
        "a2_gate_line": a2_gate[0].lineno,
        "a2_gate_predicate": ast.unparse(a2_gate[0].test),
        "results": results,
        "temporary_fixture": fixture_path,
        "temporary_fixture_removed": not Path(fixture_path).exists(),
        "review_command_executed": False,
        "network_or_database_used": False,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
