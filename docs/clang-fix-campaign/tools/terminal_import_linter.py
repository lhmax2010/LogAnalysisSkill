"""E9 C7e module-slot detector, not a candidate enumerator or whole-tree seal.

INI semantics use ConfigParser, as import-linter 2.3 does. The small lexical
index only retains source locations. Caller-supplied name hits are classified
without manufacturing binding consumption from a module dependency.
"""

from __future__ import annotations

import argparse
import configparser
import json
import re
from pathlib import Path
from typing import Any

from terminal_scan import (
    ModuleIndex,
    ScanError,
    context_for,
    contexts,
    entry_kind,
    fixed_inputs,
    sha256,
    write_atomic,
)

GLOBAL_KEYS = frozenset({"root_package", "root_packages"})
CONTRACT_KEYS = frozenset(
    {"layers", "containers", "modules", "source_modules", "forbidden_modules", "ignore_imports"}
)


def contract(section: str) -> bool:
    return bool(re.fullmatch(r"importlinter:contract:[^:]+", section))


def source_rows(text: str) -> list[dict[str, Any]]:
    """Locate options/continuations without interpreting their values."""
    rows = []
    section = key = ""
    option_indent = -1
    parser = configparser.ConfigParser()
    for line, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()
        start = len(raw) - len(raw.lstrip())
        role = "OTHER"
        value = stripped
        if stripped.startswith(("#", ";")):
            role = "COMMENT"
        elif stripped:
            if key and start > option_indent:
                role = "VALUE"
            else:
                heading = parser.SECTCRE.match(stripped)
                option = re.match(r"([^:=]+?)\s*[:=]\s*(.*)$", stripped)
                if heading:
                    section, key = heading.group("header"), ""
                    option_indent = -1
                elif option:
                    key = parser.optionxform(option.group(1).strip())
                    value = option.group(2)
                    start += option.start(2)
                    option_indent = len(raw) - len(raw.lstrip())
                    role = "VALUE"
        rows.append(
            dict(line=line, raw=raw, section=section, key=key, role=role, value=value, start=start)
        )
    return rows


def value_tokens(key: str, value: str) -> list[tuple[str, int, int]]:
    if key == "layers":
        separators = list(re.finditer(r"[|:]", value))
    elif key == "ignore_imports":
        if value.count("->") != 1:
            raise ScanError("C7E_IGNORE_IMPORTS_ARITY")
        separators = list(re.finditer(r"->", value))
    else:
        separators = []
    result = []
    starts = [0, *(match.end() for match in separators)]
    ends = [*(match.start() for match in separators), len(value)]
    for start, end in zip(starts, ends, strict=True):
        raw = value[start:end]
        token = raw.strip()
        begin = start + len(raw) - len(raw.lstrip())
        if key == "layers" and token.startswith("(") and token.endswith(")"):
            token = token[1:-1].strip()
            begin = value.index(token, begin + 1) if token else begin + 1
        if not token:
            raise ScanError(
                "C7E_IGNORE_IMPORTS_ARITY" if key == "ignore_imports" else "C7E_EMPTY_TOKEN"
            )
        result.append((token, begin, begin + len(token)))
    if key == "ignore_imports" and len(result) != 2:
        raise ScanError("C7E_IGNORE_IMPORTS_ARITY")
    return result


def inspect(
    path: str,
    mode: str,
    data: bytes,
    index: ModuleIndex,
    name_hits: list[dict[str, Any]],
) -> dict[str, Any]:
    """Every supplied name hit gets a destination, including UNKNOWN_CAPABILITY.

    Hits carry line/column/name/candidate_id; columns are zero-based. Candidate
    enumeration and the four name forms belong to the caller, not this detector.
    """
    if entry_kind(path, mode, data) != "IMPORT_LINTER":
        raise ScanError("C7E_ENTRY_KIND")
    text = data.decode("utf-8")
    context = context_for(path, index.contexts).key
    rows = source_rows(text)
    parser = configparser.ConfigParser()
    errors: list[str] = []
    try:
        parser.read_string(text, source=path)
        # Force interpolation errors before any partial dependency result.
        for section in parser.sections():
            list(parser.items(section))
    except configparser.Error as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    participants: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    dynamic: list[dict[str, Any]] = []
    exclusions = []
    for row in rows:
        is_comment = row["role"] == "COMMENT"
        is_name = row["role"] == "VALUE" and contract(row["section"]) and row["key"] == "name"
        if is_comment or (not errors and is_name):
            exclusions.append(
                {
                    **row,
                    "class": 9,
                    "reason": "COMMENT" if is_comment else "CONTRACT_NAME",
                    "interpreter_line": False,
                }
            )
    if not errors:
        for section in parser.sections():
            keys = (
                GLOBAL_KEYS
                if section == "importlinter"
                else CONTRACT_KEYS
                if contract(section)
                else set()
            )
            for key in parser[section]:
                if key not in keys:
                    continue
                relevant = [
                    r
                    for r in rows
                    if r["role"] == "VALUE" and r["section"] == section and r["key"] == key
                ]
                # No guessed provenance for defaults or interpolated tokens.
                actual = [v.strip() for v in parser[section][key].splitlines() if v.strip()]
                located = [r["value"] for r in relevant if r["value"]]
                if actual != located:
                    raise ScanError(f"C7E_VALUE_PROVENANCE: {section}.{key}")
                containers = (
                    parser[section].get("containers", "").splitlines() if contract(section) else []
                )
                containers = [c.strip() for c in containers if c.strip()]
                for row in relevant:
                    if not row["value"]:
                        continue
                    for token, start, end in value_tokens(key, row["value"]):
                        point = {
                            "path": path,
                            "context": context,
                            "line": row["line"],
                            "column": row["start"] + start,
                            "end_column": row["start"] + end,
                            "section": section,
                            "key": key,
                            "token": token,
                            "form": "C7e",
                            "branch": "consumer.C7e",
                            "resolutions": [],
                        }
                        participants.append(point)
                        names = (
                            [f"{c}.{token}" for c in containers]
                            if key == "layers" and containers
                            else [token]
                        )
                        for name in names:
                            if "*" in name:
                                dynamic.append(
                                    {
                                        **point,
                                        "module": name,
                                        "kind": "DYNAMIC_UNRESOLVED",
                                        "reason": "MODULE_WILDCARD",
                                    }
                                )
                                continue
                            resolution = index.resolve(
                                context, name, f"{path}:{row['line']}:{point['column']}"
                            )
                            point["resolutions"].append(resolution)
                            if resolution["kind"] != "MODULE_IDENTITY_AMBIGUOUS":
                                for target in resolution["targets"]:
                                    edges.append(
                                        {
                                            "source": {
                                                "path": path,
                                                "context": context,
                                                "line": row["line"],
                                                "column": point["column"],
                                            },
                                            "target": {**target, "module": name},
                                            "granularity": "MODULE",
                                            "form": "C7e",
                                            "branch": "consumer.C7e",
                                        }
                                    )

    classified = []
    for hit in name_hits:
        line, column, name = hit["line"], hit["column"], hit["name"]
        if (
            line < 1
            or line > len(rows)
            or rows[line - 1]["raw"][column : column + len(name)] != name
        ):
            raise ScanError("NAME_HIT_SOURCE_MISMATCH")
        excluded = [
            e
            for e in exclusions
            if e["line"] == line and (e["reason"] == "COMMENT" or column >= e["start"])
        ]
        points = [
            p
            for p in participants
            if p["line"] == line and p["column"] <= column and column + len(name) <= p["end_column"]
        ]
        destinations = ["EXCLUDED_CLASS9"] * len(excluded) + ["C7e"] * len(points)
        classified.append(
            {
                **hit,
                "destinations": destinations,
                "status": destinations[0]
                if len(destinations) == 1
                else "UNKNOWN_CAPABILITY"
                if not destinations
                else "MULTIPLE_DESTINATIONS",
            }
        )
    return {
        "path": path,
        "context": context,
        "entry_kind": "IMPORT_LINTER",
        "parse_errors": errors,
        "participants": participants,
        "module_edges": edges,
        "binding_edges": [],
        "dynamic_unresolved": dynamic,
        "exclusions": exclusions,
        "name_hits": classified,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--rules-root", type=Path, required=True)
    parser.add_argument("--scan06-witness", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest, files = fixed_inputs(args.root, args.rules_root)
    index = ModuleIndex(files, contexts(files))
    witness_bytes = args.scan06_witness.read_bytes()
    witness = json.loads(witness_bytes)
    if (witness["head"], witness["tree"]) != (manifest["head"], manifest["tree"]):
        raise ScanError("WITNESS_TREE_MISMATCH")
    if sha256(files[witness["provider_entry"]["path"]]) != witness["provider_entry"]["sha256"]:
        raise ScanError("WITNESS_FILE_MISMATCH")
    results = []
    for entry in manifest["entries"]:
        if entry["entry_kind"] != "IMPORT_LINTER":
            continue
        hits = [
            {
                "line": h["line"],
                "column": h["column"],
                "name": h["module"],
                "name_form": h["name_form"],
                "candidate_id": witness["candidate_id"],
            }
            for h in witness["hits"]
            if h["file"] == entry["path"]
        ]
        results.append(inspect(entry["path"], entry["git_mode"], files[entry["path"]], index, hits))
    output = {
        "head": manifest["head"],
        "tree": manifest["tree"],
        "rules_sha256": manifest["rules_sha256"],
        "witness_sha256": sha256(witness_bytes),
        "scope": "all IMPORT_LINTER module slots; name-hit coverage limited to SCAN-06 witness",
        "non_python_full_preflight": "NOT_RUN_CANDIDATE_UNIVERSE_UNAVAILABLE",
        "scan_completion": "NOT_CREATED",
        "manifest": manifest,
        "results": results,
        "resolution_events": index.events,
    }
    write_atomic(args.output, output)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return int(
        any(
            r["parse_errors"]
            or any(
                h["status"] in {"UNKNOWN_CAPABILITY", "MULTIPLE_DESTINATIONS"}
                for h in r["name_hits"]
            )
            for r in results
        )
        or any(e["kind"] == "MODULE_IDENTITY_AMBIGUOUS" for e in index.events)
    )


if __name__ == "__main__":
    raise SystemExit(main())
