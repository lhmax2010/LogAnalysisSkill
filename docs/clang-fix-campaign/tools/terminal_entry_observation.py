"""Enumerate documented repository entries and collect isolated help-smoke facts."""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

import tomllib
from terminal_predicates import EVIDENCE_PREFIX
from verify_anchors import TREE, digest, guard, write_json

CLAIM = "OBS-5.entry-consumers"
INVOCATION = re.compile(
    r"\bpython(?:3)?\s+(?:-m\s+(?P<module>[\w.]+)|"
    r"(?P<script>(?:/path/to/)?[\w./-]+\.py))(?P<command>\s+(?:analyze|format-patch)\b)?"
)
BARE_LAUNCHER = re.compile(r"`(?P<script>scripts/run_[\w]+\.py)`")


def tracked(root: Path) -> list[str]:
    return subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", "HEAD"], cwd=root, text=True
    ).splitlines()


def enumerate_entries(root: Path) -> dict[str, Any]:
    """Source-only enumeration, independent of smoke outcomes and claim records."""
    files = tracked(root)
    rows: dict[str, dict[str, Any]] = {}
    descriptors = {}
    documents = []
    for context in ("", "release-v1.4.0"):
        prefix = f"{context}/" if context else ""
        config = root / prefix / "pyproject.toml"
        parsed = tomllib.loads(config.read_text())
        where = parsed["tool"]["setuptools"]["packages"]["find"]["where"]
        descriptors[context] = dict(
            file=str(config.relative_to(root)),
            sha256=digest(config),
            roots=[str(Path(prefix) / p) for p in where],
            console_scripts=parsed["project"].get("scripts", {}),
        )

    def add(kind: str, context: str, target: str, argv: list[str], site: str) -> None:
        key = f"{context or 'live'}:{kind}:{target}"
        row = rows.setdefault(
            key,
            dict(
                entry_id=key, kind=kind, target=target, context=context, argv=argv, documented_in=[]
            ),
        )
        if site not in row["documented_in"]:
            row["documented_in"].append(site)

    for context, descriptor in descriptors.items():
        for name, target in descriptor["console_scripts"].items():
            add("CONSOLE_SCRIPT", context, target, [name, "--help"], descriptor["file"])
        for path in files:
            if not path.endswith("/__main__.py"):
                continue
            for source_root in descriptor["roots"]:
                if path.startswith(source_root + "/"):
                    module = (
                        path[len(source_root) + 1 :].removesuffix("/__main__.py").replace("/", ".")
                    )
                    add(
                        "PACKAGE_MAIN",
                        context,
                        module,
                        [sys.executable, "-m", module, "--help"],
                        path,
                    )
    for path in files:
        if Path(path).name != "SKILL.md":
            continue
        source = (root / path).read_text()
        context = "release-v1.4.0" if path.startswith("release-v1.4.0/") else ""
        matches = []
        for pattern in (INVOCATION, BARE_LAUNCHER):
            for match in pattern.finditer(source):
                values = match.groupdict()
                command = (values.get("command") or "").strip()
                if values.get("module"):
                    target = "-m " + values["module"]
                    argv = [sys.executable, "-m", values["module"]]
                else:
                    # Documented /path/to placeholders name the enclosing skill launcher.
                    script = Path(path).parent / "scripts" / Path(values["script"]).name
                    if script.as_posix() not in files:
                        raise ValueError(f"documented launcher not tracked: {path}: {script}")
                    target = script.as_posix()
                    argv = [sys.executable, str(root / script)]
                if command:
                    target += " " + command
                    argv.append(command)
                line = source.count("\n", 0, match.start()) + 1
                add("SKILL_MD_COMMAND", context, target, [*argv, "--help"], f"{path}:{line}")
                matches.append(dict(line=line, spelling=match.group(), target=target))
        documents.append(dict(path=path, sha256=digest(root / path), invocations=matches))
    return dict(
        independent_enumeration=sorted(rows),
        entries=[rows[k] for k in sorted(rows)],
        packaging=descriptors,
        skill_documents=documents,
        scope=(
            "Repository entry points, including both packaging contexts. External git/gbs "
            "commands are subprocess effects, not repository entries; never execute for smoke."
        ),
        smoke_policy=(
            "Retain launcher/module and named CLI subcommand, replace operational inputs "
            "with --help. Repeated documentation sites share one entry and all citations."
        ),
    )


def consumers(root: Path, target: str, context: str) -> list[str]:
    module = target.removeprefix("-m ").split(" ", 1)[0]
    found = []
    for path in tracked(root):
        if not path.endswith(".py") or path.startswith("tests/"):
            continue
        if path.startswith("release-v1.4.0/") != bool(context):
            continue
        for node in ast.walk(ast.parse((root / path).read_text())):
            if isinstance(node, ast.ImportFrom) and node.module == module:
                found.append(f"{path}:{node.lineno}")
            elif isinstance(node, ast.Import) and any(a.name == module for a in node.names):
                found.append(f"{path}:{node.lineno}")
    return sorted(set(found))


def produce(root: Path, rules_root: Path, out: Path, enumeration: Path) -> None:
    context = guard(root, rules_root)
    context["producer_sha256"] = digest(Path(__file__))
    inventory = json.loads(enumeration.read_text())
    # Re-read source descriptors; never infer coverage from successful commands.
    if inventory != enumerate_entries(root):
        raise ValueError("independent entry enumeration differs from fixed source")
    out.mkdir(parents=True, exist_ok=False)
    entries, runs = [], []
    for row in inventory["entries"]:
        env = dict(os.environ)
        for key in ("PYTHONPATH", "MYPYPATH", "PYTEST_ADDOPTS", "PYTEST_PLUGINS"):
            env.pop(key, None)
        env["PYTHONPATH"] = os.pathsep.join(
            str(root / p) for p in inventory["packaging"][row["context"]]["roots"]
        )
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        result = subprocess.run(
            row["argv"], cwd=root, env=env, capture_output=True, text=True, timeout=30
        )
        run = dict(
            entry_id=row["entry_id"],
            argv=row["argv"],
            cwd=str(root),
            context=row["context"],
            pythonpath=env["PYTHONPATH"],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
        )
        runs.append(run)
        entries.append(
            dict(
                entry_id=row["entry_id"],
                kind=row["kind"],
                target=row["target"],
                documented_in=row["documented_in"],
                consumers=consumers(root, row["target"], row["context"]),
                smoke_command=shlex.join(row["argv"]),
                smoke_exit=result.returncode,
            )
        )
        print(f"SMOKE {row['entry_id']} exit={result.returncode}", flush=True)
    write_json(out / "raw.json", dict(context=context, runs=runs))
    evidence = [
        dict(kind="FILE", path=str(p), sha256=digest(p), selector=selector)
        for p, selector in ((enumeration, "/independent_enumeration"), (out / "raw.json", "/runs"))
    ]
    write_json(
        out / "output.json",
        {CLAIM: dict(claim_id=CLAIM, snapshot=TREE, evidence=evidence, entries=entries)},
    )
    write_json(out / "context.json", dict(head=context["head"], tree=TREE, run_id=out.name))
    print(f"FACTS_WRITTEN claim={CLAIM} entries={len(entries)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("enumerate", "produce"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--rules-root", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    guard(args.root, args.rules_root)
    anchor = args.rules_root / EVIDENCE_PREFIX / "B-5-entries.json"
    if args.mode == "enumerate":
        if anchor.exists():
            raise ValueError("do not overwrite independent evidence")
        value = enumerate_entries(args.root)
        write_json(anchor, value)
        print(f"INDEPENDENT_ENUMERATION entries={len(value['entries'])} sha256={digest(anchor)}")
    else:
        if args.out is None:
            parser.error("produce requires --out")
        produce(args.root, args.rules_root, args.out, anchor)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
