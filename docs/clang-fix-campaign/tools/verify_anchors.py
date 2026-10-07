"""Collect only OBS-1.item3/item4 facts; verdicts belong to terminal_predicates.

Code is loaded from the fixed clean worktree. Rules are loaded separately from
the admitted erratum. Fake subprocess runners never contact Gerrit or execute
git; filesystem effects under observation are the production Python effects.
Signal probes run in child processes with normal SIGINT/SIGTERM dispositions.
"""

from __future__ import annotations

import argparse
import ast
import dataclasses
import hashlib
import importlib
import json
import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

from terminal_authority import E1_COMMIT, read_authority
from terminal_predicates import check_frozen_hashes, load_json

HEAD = "43a6aa625f27da46daba190657bf62256080c68e"
TREE = "ca9331190e878af465e7968fe56e735585a5866e"
RULES_PATH = "docs/clang-fix-campaign/p49-terminal-batch-design-v1.31-FROZEN.md"
RULES_HASH = "d44584592b54bfaf1406c13369da5f2f6a5894fc3dd8de04b3905eadd6213c3f"
TABLE_PATH = "docs/clang-fix-campaign/p49-skill5-gerrit-submit-design-v1.3.2-FROZEN.md"
FETCH = "tizen-gerrit-fetch/scripts/tizen_gerrit_fetch/gerrit.py"
SUBMIT = "tizen-gerrit-submit/scripts/tizen_gerrit_submit/gerrit_submit.py"
WORKSPACE = "tizen-ci-shared/scripts/tizen_ci_shared/workspace/__init__.py"
DATA = Path(__file__).with_name("p49_terminal_data")
CLAIMS = {"item3": "OBS-1.item3-predicate", "item4": "OBS-1.item4-anchors"}
COMMIT = "a" * 40


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def serial(value: Any) -> Any:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return serial(dataclasses.asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, subprocess.CompletedProcess):
        return {
            key: serial(getattr(value, key)) for key in ("args", "returncode", "stdout", "stderr")
        }
    if isinstance(value, dict):
        return {key: serial(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [serial(item) for item in value]
    return value


def value_state(value: Any) -> dict[str, Any]:
    return {"state": "VALUE", "value": serial(value)}


def marker_state(path: Path) -> dict[str, Any]:
    return {"state": "PRESENT", "sha256": digest(path)} if path.is_file() else {"state": "ABSENT"}


def path_state(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        return {"kind": "SYMLINK", "target": os.readlink(path), "target_exists": path.exists()}
    if path.is_dir():
        return {
            "kind": "DIRECTORY",
            "files": {
                str(item.relative_to(path)): digest(item)
                for item in sorted(path.rglob("*"))
                if item.is_file() and not item.is_symlink()
            },
        }
    if path.is_file():
        return {"kind": "FILE", "sha256": digest(path)}
    return {"kind": "ABSENT"}


def guard(root: Path, rules_root: Path) -> dict[str, Any]:
    def git(*args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=root, text=True).strip()

    if git("rev-parse", "HEAD") != HEAD or git("rev-parse", "HEAD^{tree}") != TREE:
        raise ValueError("observation HEAD/tree differs")
    if git("status", "--porcelain=v1"):
        raise ValueError("observation worktree is not clean")
    if Path.cwd().resolve() != root.resolve():
        raise ValueError("producer must run in observation worktree")
    read_authority(rules_root, E1_COMMIT, RULES_HASH)
    check_frozen_hashes(
        load_json(DATA / "predicates.json"), load_json(DATA / "measurement_exemptions.json")
    )
    return {
        "head": HEAD,
        "tree": TREE,
        "code_root": str(root),
        "rules": {
            "path": str(rules_root / RULES_PATH),
            "sha256": digest(rules_root / RULES_PATH),
            "source_commit": E1_COMMIT,
            "source_sha256": RULES_HASH,
        },
        "producer_sha256": digest(Path(__file__)),
    }


def modules(root: Path) -> tuple[Any, Any, Any]:
    loaded = tuple(
        importlib.import_module(name)
        for name in (
            "tizen_gerrit_fetch.gerrit",
            "tizen_gerrit_submit.gerrit_submit",
            "tizen_ci_shared.workspace",
        )
    )
    for module, source in zip(loaded, (FETCH, SUBMIT, WORKSPACE), strict=True):
        if module.__file__ is None or Path(module.__file__).resolve() != (root / source).resolve():
            raise ValueError(f"wrong import provenance: {module.__file__}")
    return loaded[0], loaded[1], loaded[2]


def item3_anchor(source: str) -> dict[str, Any]:
    matches = []
    for function in ast.parse(source).body:
        if not isinstance(function, ast.FunctionDef):
            continue
        for node in ast.walk(function):
            if not isinstance(node, ast.BoolOp) or not isinstance(node.op, ast.And):
                continue
            calls = [
                child.func
                for child in node.values
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute)
            ]
            names = [child.attr for child in calls]
            if {"exists", "is_symlink"} <= set(names):
                matches.append((function, node, calls, names))
    result = {
        "file": FETCH,
        "function": "",
        "selector": "FunctionDef//BoolOp.And[direct operand calls include exists,is_symlink]",
        "matched_count": len(matches),
        "expr_kind": "",
        "operand_calls": [],
        "same_receiver": False,
        "span_sha256": "",
    }
    if len(matches) == 1:
        function, node, calls, names = matches[0]
        segment = ast.get_source_segment(source, node)
        assert segment is not None
        result.update(
            function=function.name,
            expr_kind="BoolOp.And",
            operand_calls=names,
            same_receiver=len({ast.dump(child.value) for child in calls}) == 1,
            span_sha256=hashlib.sha256(segment.encode()).hexdigest(),
        )
    return result


def call_anchor(
    root: Path, number: int, file: str, function: str, callee: str
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source = (root / file).read_text()
    matches = [
        node
        for fn in ast.parse(source).body
        if isinstance(fn, ast.FunctionDef) and fn.name == function
        for node in ast.walk(fn)
        if isinstance(node, ast.Call) and ast.unparse(node.func) == callee
    ]
    selector = f"FunctionDef[name={function}]//Call[func={callee}]"
    return (
        {
            "anchor_no": number,
            "file": file,
            "function": function,
            "selector": selector,
            "matched_count": len(matches),
        },
        [
            {
                "lineno": node.lineno,
                "end_lineno": node.end_lineno,
                "source": ast.get_source_segment(source, node),
            }
            for node in matches
        ],
    )


def table(root: Path) -> tuple[dict[str, Any], list[dict[str, str]]]:
    text = (root / TABLE_PATH).read_text()
    lines = text.splitlines()
    headings = [line for line in lines if line.startswith("### 3.2 ")]
    if len(headings) != 1:
        raise ValueError("mapping heading is not unique")
    section = text.split(headings[0], 1)[1].split("\n##", 1)[0]
    rows = []
    active = False
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("| 调用面 | 超时"):
            active = True
            continue
        if active and stripped.startswith("|---"):
            continue
        if active and stripped.startswith("|"):
            cells = [cell.strip() for cell in stripped[1:-1].split("|")]
            if len(cells) != 4:
                raise ValueError("mapping table is not four-column")
            rows.append(
                dict(
                    zip(
                        ("surface", "timeout_cell", "interrupt_cell", "residual_cell"),
                        cells,
                        strict=True,
                    )
                )
            )
        elif active:
            break
    return {"path": TABLE_PATH, "sha256": digest(root / TABLE_PATH), "heading": headings[0]}, rows


def probe(root: Path, directory: Path, surface: str, fault: str) -> None:
    fetch, submit, workspace = modules(root)
    directory.mkdir(parents=True, exist_ok=False)
    destination = directory / "destination"
    if surface.startswith("symlink:"):
        case = surface.split(":")[1]
        if case in {"DANGLING_SYMLINK", "LIVE_SYMLINK_TO_DIR"}:
            target = directory / "target"
            if case == "LIVE_SYMLINK_TO_DIR":
                target.mkdir()
                (target / "sentinel").write_bytes(b"existing target\n")
            destination.symlink_to(target, target_is_directory=True)
        elif case == "REAL_DIR":
            destination.mkdir()
            (destination / "sentinel").write_bytes(b"existing destination\n")
    else:
        destination.mkdir()
        (destination / "sentinel").write_bytes(b"existing destination\n")
    workdir_marker = destination / workspace.MARKER_FILENAME
    exclude = destination / ".git/info/exclude"
    handle = None
    if surface.startswith("shared"):
        # A fixed valid initial marker is fixture data, not a claimed observation.
        write_json(
            workdir_marker,
            {
                "workspace_root": str(directory),
                "baseline_repo": str(directory / "baseline"),
                "base_commit": COMMIT,
                "iter_index": 1,
                "created_at": "2026-09-29T00:00:00+00:00",
            },
        )
        handle = workspace.DisposableWorktree(
            str(destination),
            str(directory / "baseline"),
            COMMIT,
            str(directory),
            1,
            str(workdir_marker),
        )
    write_json(directory / "before.json", path_state(destination))
    trace: list[dict[str, Any]] = []
    query = (
        json.dumps(
            {"project": "fixture/project", "branch": "fixture", "status": "MERGED", "number": 1}
        )
        + "\n"
    )

    def runner(argv: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        trace.append({"argv": list(argv), "kwargs": serial(kwargs)})
        write_json(directory / "trace.json", trace)
        selected = (
            (surface == "fetch-query" and argv[0] == "ssh")
            or (
                surface.startswith("fetch-full-")
                and (
                    (surface == "fetch-full-query" and argv[0] == "ssh")
                    or (argv[0] == "git" and surface.removeprefix("fetch-full-") in argv)
                )
            )
            or surface
            in {"fetch-git", "submit-git", "submit-remote", "shared-git", "shared-exclude"}
        )
        if selected and fault == "timeout":
            exc = subprocess.TimeoutExpired(list(argv), 0.125)
            write_json(
                directory / "injection.json",
                {
                    "type": type(exc).__name__,
                    "cmd": exc.cmd,
                    "timeout": exc.timeout,
                    "message": str(exc),
                },
            )
            raise exc
        if selected and fault in {"SIGINT", "SIGTERM"}:
            write_json(
                directory / "injection.json",
                {"signal": fault, "pid": os.getpid(), "argv": list(argv)},
            )
            os.kill(os.getpid(), getattr(signal, fault))
            raise RuntimeError("signal unexpectedly returned")
        stdout = query if argv[0] == "ssh" else ""
        if "ls-remote" in argv:
            stdout = COMMIT + "\trefs/heads/fixture\n"
        if "--git-path" in argv:
            stdout = str(exclude) + "\n"
        return subprocess.CompletedProcess(argv, 0, stdout, "")

    outcome: dict[str, Any]
    try:
        if surface.startswith(("symlink:", "fetch-full-")):
            result = fetch.fetch_source_for_commit(
                "fixture/project", COMMIT, destination, subprocess_runner=runner
            )
        elif surface == "fetch-query":
            result = fetch.query_change_for_commit(COMMIT, subprocess_runner=runner)
        elif surface == "fetch-git":
            result = fetch._run_git(["git", "-C", str(destination), "status"], runner, env={})
        elif surface == "submit-git":
            result = submit._run_git(destination, ["status"], runner)
        elif surface == "submit-remote":
            # Only the attributes read by this isolated surface are supplied.
            record = SimpleNamespace(project="fixture/project", base_commit=COMMIT)
            options = SimpleNamespace(
                submit_target="refs/for/fixture",
                gerrit_user="fixture-user",
                gerrit_host="fixture.invalid",
                gerrit_port="29418",
                git_ssh_command=None,
            )
            result = submit._target_warnings(record, options, runner)
        elif surface == "shared-git":
            with patch.object(workspace.subprocess, "run", runner):
                result = workspace._run_git(["-C", str(destination), "status"])
        elif surface == "shared-exclude":
            with patch.object(workspace.subprocess, "run", runner):
                result = workspace.mark_worktree_protected(
                    handle, verification_id="fixture-v", failure_key="fixture-f"
                )
        else:
            raise ValueError(f"unsupported surface: {surface}")
        outcome = {"return_value": value_state(result), "exception": {"state": "ABSENT"}}
    except BaseException as exc:
        outcome = {
            "return_value": {"state": "ABSENT"},
            "exception": value_state(
                {
                    "type": type(exc).__name__,
                    "module": type(exc).__module__,
                    "message": str(exc),
                    "code": value_state(exc.code) if hasattr(exc, "code") else {"state": "ABSENT"},
                }
            ),
        }
        write_json(directory / "outcome.json", outcome)
        if not isinstance(exc, Exception):
            raise
    write_json(directory / "outcome.json", outcome)


def run_probe(
    root: Path, rules_root: Path, fixtures: Path, name: str, surface: str, fault: str
) -> dict[str, Any]:
    directory = fixtures / name
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--root",
        str(root),
        "--rules-root",
        str(rules_root),
        "--probe",
        surface,
        "--fault",
        fault,
        "--fixture",
        str(directory),
    ]
    # Exact controlled environment, no inherited credentials in argv/kwargs evidence.
    env = {
        key: os.environ[key] for key in ("PATH", "HOME", "LANG", "VIRTUAL_ENV") if key in os.environ
    }
    completed = subprocess.run(
        command, cwd=root, env=env, capture_output=True, text=True, timeout=30
    )
    before = load_json(directory / "before.json")
    after = path_state(directory / "destination")
    outcome_path = directory / "outcome.json"
    outcome = load_json(outcome_path) if outcome_path.exists() else None
    injection_path = directory / "injection.json"
    trace_path = directory / "trace.json"
    exclusion = directory / "destination/.git/info/exclude"
    raw = {
        "scenario_id": name,
        "surface": surface,
        "fault": fault,
        "command": command,
        "fixture": str(directory),
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "before": before,
        "after": after,
        "destination_unchanged": before == after,
        "trace": load_json(trace_path) if trace_path.exists() else [],
        "outcome": outcome,
        "injection": load_json(injection_path) if injection_path.exists() else None,
        "workdir_marker": marker_state(directory / "destination/.ci_triage_workdir"),
        "protected_marker": marker_state(directory / "destination/.ci_triage_protected"),
        "exclude_completed": exclusion.is_file()
        and {".ci_triage_workdir", ".ci_triage_protected"}
        <= set(exclusion.read_text().splitlines()),
    }
    write_json(fixtures / f"{name}.observation.json", raw)
    if completed.returncode and fault not in {"SIGINT", "SIGTERM"}:
        raise ValueError(
            f"probe infrastructure error, see {fixtures / (name + '.observation.json')}"
        )
    return raw


def produce(kind: str, root: Path, rules_root: Path, out: Path) -> None:
    context = guard(root, rules_root)
    out.mkdir(parents=True, exist_ok=False)
    fixtures = Path(tempfile.mkdtemp(prefix=f"p49-{kind}-"))
    raw: dict[str, Any] = {"context": context, "fixture_root": str(fixtures), "observations": []}
    if kind == "item3":
        rows = []
        anchor = item3_anchor((root / FETCH).read_text())
        for name in ("DANGLING_SYMLINK", "LIVE_SYMLINK_TO_DIR", "REAL_DIR", "ABSENT"):
            obs = run_probe(root, rules_root, fixtures, name, f"symlink:{name}", "none")
            raw["observations"].append(obs)
            exception = obs["outcome"]["exception"]
            row = {
                "scenario_id": name,
                "exception_code": {"state": "ABSENT"},
                "destination_after": json.dumps(obs["after"], ensure_ascii=False, sort_keys=True),
            }
            if exception["state"] == "VALUE":
                row.update(
                    exception_type=exception["value"]["type"],
                    exception_code=exception["value"]["code"],
                )
            rows.append(row)
        claim = {"anchor": anchor, "scenarios": rows}
        source_files = [FETCH]
    else:
        table_source, table_rows = table(root)
        definitions = [
            (FETCH, "query_change_for_commit", "subprocess_runner"),
            (FETCH, "_run_git", "subprocess_runner"),
            (SUBMIT, "_run_git", "subprocess_runner"),
            (SUBMIT, "_target_warnings", "subprocess_runner"),
            (WORKSPACE, "_run_git", "subprocess.run"),
            (WORKSPACE, "_exclude_private_files", "subprocess.run"),
        ]
        calls, spans = [], []
        for number, (file, function, callee) in enumerate(definitions, 1):
            call, matched = call_anchor(root, number, file, function, callee)
            calls.append(call)
            spans.append({"anchor_no": number, "matches": matched})
        raw["call_spans"] = spans
        residual = []
        surfaces = (
            "fetch-query",
            "fetch-git",
            "submit-git",
            "submit-remote",
            "shared-git",
            "shared-exclude",
        )
        for number, surface in enumerate(surfaces, 1):
            for fault in ("none", "timeout", "SIGINT", "SIGTERM"):
                obs = run_probe(
                    root, rules_root, fixtures, f"surface{number}-{fault}", surface, fault
                )
                raw["observations"].append(obs)
                if number == 6 and fault != "none":
                    residual.append(
                        {
                            "anchor_no": 6,
                            "injected_at": f"_exclude_private_files/subprocess.run/{fault}",
                            "workdir_marker": obs["workdir_marker"],
                            "protected_marker": obs["protected_marker"],
                            "exclude_completed": obs["exclude_completed"],
                        }
                    )
        for stage in ("query", "init", "fetch", "checkout"):
            for fault in ("timeout", "SIGINT", "SIGTERM"):
                obs = run_probe(
                    root,
                    rules_root,
                    fixtures,
                    f"fetch-{stage}-{fault}",
                    f"fetch-full-{stage}",
                    fault,
                )
                raw["observations"].append(obs)
                residual.append(
                    {
                        "anchor_no": 1 if stage == "query" else 2,
                        "injected_at": f"fetch_source_for_commit/{stage}/{fault}",
                        "destination_unchanged": obs["destination_unchanged"],
                    }
                )
        claim = {
            "table_source": table_source,
            "rows": table_rows,
            "call_sites": calls,
            "residual_obs": residual,
        }
        source_files = [FETCH, SUBMIT, WORKSPACE, TABLE_PATH]
    raw_path = out / "raw.json"
    write_json(raw_path, raw)
    evidence = [
        {
            "kind": "FILE",
            "path": str(root / file),
            "sha256": digest(root / file),
            "selector": "module source",
        }
        for file in source_files
    ]
    evidence += [
        {
            "kind": "FILE",
            "path": str(raw_path),
            "sha256": digest(raw_path),
            "selector": "/observations",
        },
        {
            "kind": "FILE",
            "path": str(rules_root / RULES_PATH),
            "sha256": digest(rules_root / RULES_PATH),
            "selector": "Appendix C/E1-1/E1-2",
        },
    ]
    claim.update(claim_id=CLAIMS[kind], snapshot=TREE, evidence=evidence)
    write_json(out / "output.json", {CLAIMS[kind]: claim})
    write_json(out / "context.json", {"tree": TREE, "head": HEAD, "run_id": out.name})
    print(f"FACTS_WRITTEN claim={CLAIMS[kind]} output={out / 'output.json'} raw={raw_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--rules-root", type=Path, required=True)
    parser.add_argument("--claim", choices=CLAIMS)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--probe")
    parser.add_argument("--fault", choices=("none", "timeout", "SIGINT", "SIGTERM"))
    parser.add_argument("--fixture", type=Path)
    args = parser.parse_args()
    guard(args.root, args.rules_root)
    if args.probe:
        if args.fixture is None or args.fault is None:
            parser.error("probe requires fixture and fault")
        probe(args.root, args.fixture, args.probe, args.fault)
    else:
        if not args.claim or args.out is None:
            parser.error("claim and out required")
        produce(args.claim, args.root, args.rules_root, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
