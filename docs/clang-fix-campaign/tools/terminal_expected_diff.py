"""Section 6 exact-difference gate. No OBS producers or production imports.

Collectors are injected by the caller; readers must come from the verified
OBS-1.item5-order universe. Segment 2 exercises artificial objects only.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import unicodedata
from collections.abc import Callable
from pathlib import Path
from typing import Any

from historical_inputs import read_pinned
from terminal_authority import assert_contained, read_authority
from terminal_predicates import canonical, check_frozen_hashes, load_json

DATA = Path(__file__).with_name("p49_terminal_data")
DOC = "docs/clang-fix-campaign/p49-terminal-batch-design-v1.31-FROZEN.md"
DOC_HASH = "7b8531fdd9bcb4b2ecf8f3576eab6285f09f4b22fb1b212775939dbe72d19200"
DOC_COMMIT = "cbd3a22ae6fdb6454ecc5a55254304f72a17ecd1"
TABLE = "docs/clang-fix-campaign/p49-skill5-gerrit-submit-design-v1.3.2-FROZEN.md"
TABLE_HASH = "0e2de5ff80c7f36940e455ec75f4f6872caa4fd93be360ad0fcfd0e59c755f27"
OBS = "docs/clang-fix-campaign/dev_memory/stage14_p49_terminal_batch/a0-evidence/part2/"
OBS_HASHES = {
    OBS + "e1-item3/raw.json": "cdd0c1065c458ae80d7a0a7440c4bdf6c1df4ff15ad77bb9ded760ccb7071bd5",
    OBS + "e1-item4/raw.json": "7a8b93b5ffe31511c9e93da06441f41c817be4b341e079ac29aad2f7529cdfe2",
    OBS
    + "e1-item3/output.json": "117484f68d517b7ba032a0438841a0c6bef4933f8476ae43d1b3f9414d27078a",
}
SURFACES = (
    "fetch-query",
    "fetch-git",
    "submit-git",
    "submit-remote",
    "shared-git",
    "shared-exclude",
)
ABSENT: dict[str, Any] = {"state": "ABSENT"}
MISSING = object()


class GateError(ValueError):
    """Fail-closed schema, source, registration or comparison failure."""


def require(condition: Any, message: str) -> None:
    if not condition:
        raise GateError(message)


def fields(obj: Any, names: set[str], where: str) -> None:
    require(isinstance(obj, dict) and set(obj) == names, f"CLOSED_FIELDS: {where}")


def value(item: Any) -> dict[str, Any]:
    return {"state": "VALUE", "value": item}


def equal(a: Any, b: Any) -> bool:
    return canonical(a) == canonical(b)


def pointer(obj: Any, path: str) -> Any:
    require(path == "" or path.startswith("/"), f"JSON_POINTER: {path}")
    for token in path.split("/")[1:]:
        require(not re.search(r"~(?![01])", token), f"JSON_POINTER: {path}")
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(obj, dict) and token in obj:
            obj = obj[token]
        elif isinstance(obj, list) and re.fullmatch(r"0|[1-9][0-9]*", token):
            require(int(token) < len(obj), f"MISSING_POINTER: {path}")
            obj = obj[int(token)]
        else:
            raise GateError(f"MISSING_POINTER: {path}")
    return obj


def escaped(key: str) -> str:
    return key.replace("~", "~0").replace("/", "~1")


class Sources:
    def __init__(self, root: Path):
        self.root = root
        self.cache: dict[str, bytes] = {}
        self.current_document: str | None = None

    def current_authority(self) -> str:
        if self.current_document is None:
            text = (self.root / DOC).read_text()
            check_later_errata(text)
            self.current_document = text
        return self.current_document

    def read(self, file: str, sha256: str) -> bytes:
        allowed = {DOC: DOC_HASH, TABLE: TABLE_HASH, **OBS_HASHES}
        require(allowed.get(file) == sha256, f"SOURCE_NOT_APPROVED: {file}")
        if file not in self.cache:
            if file == DOC:
                self.current_authority()
                self.cache[file] = read_authority(self.root, DOC_COMMIT, sha256)
            elif file == TABLE:
                self.cache[file] = read_pinned(self.root, TABLE, sha256)
                assert_contained(self.cache[file], (self.root / TABLE).read_bytes())
            else:
                self.cache[file] = (self.root / file).read_bytes()
        content = self.cache[file]
        require(hashlib.sha256(content).hexdigest() == sha256, f"SOURCE_HASH: {file}")
        return content

    def fact(self, ref: dict[str, Any]) -> Any:
        fields(ref, {"file", "sha256", "pointer"}, "observation reference")
        require(ref["file"] in OBS_HASHES, "NOT_AN_OBS_SOURCE")
        return pointer(json.loads(self.read(ref["file"], ref["sha256"])), ref["pointer"])

    def timeout_cells(self) -> list[str]:
        text = self.read(TABLE, TABLE_HASH).decode()
        rows = [
            line.strip()
            for line in text.splitlines()
            if line.strip().startswith("| ")
            and line.count("|") == 5
            and any(
                key in line
                for key in ("FETCH_TIMEOUT", "GIT_TIMEOUT", "target_head_unknown:timeout")
            )
        ]
        require(len(rows) == len(SURFACES), "MAPPING_TABLE_ROWS")
        return rows

    def cite(self, ref: dict[str, Any]) -> None:
        fields(ref, {"file", "sha256", "section", "quote"}, "authority reference")
        require(ref["file"] in {DOC, TABLE}, "NOT_AN_AUTHORITY")
        text = self.read(ref["file"], ref["sha256"]).decode()
        require(isinstance(ref["quote"], str) and ref["quote"] in text, "SOURCE_QUOTE")
        require(bool(ref["quote"].strip()) and bool(ref["section"].strip()), "EMPTY_SOURCE")
        bounds = {
            "§3 预期差异": ("## §3 ", "## §4 "),
            "§4 验收口径": ("## §4 ", "## §5 "),
            "§6": ("## §6 ", "## §7 "),
            "附录C/E1-2": ("**E1-2 ·", "**生效范围**"),
            "附录C/E2-1": ("**E2-1 ·", "**E2-2 ·"),
            "附录C/E2-2": ("**E2-2 ·", "**生效范围**"),
            "附录C/E3-1": ("**E3-1 ·", "**E3-2 ·"),
        }
        if ref["file"] == DOC:
            require(ref["quote"] in self.current_authority(), "CURRENT_SOURCE_QUOTE")
            require(ref["section"] in bounds, "UNAPPROVED_SOURCE_SECTION")
            start, end = bounds[ref["section"]]
            body = start + text.split(start, 1)[1].split(end, 1)[0]
        else:
            require(ref["section"] == "§3.2⑥ timeout 单元格", "UNAPPROVED_TABLE_SECTION")
            body = text.split("⑥**结果映射表", 1)[1].split("**protected marker 写入顺序议题", 1)[0]
        require(ref["quote"] in body, "SOURCE_QUOTE_OUTSIDE_SECTION")


def check_later_errata(text: str) -> list[dict[str, Any]]:
    """SCAN-07: immutable E3 sources are valid only while later scopes exclude them."""
    marker = "## 附录 C:冻结后勘误"
    require(text.count(marker) == 1, "ERRATA_APPENDIX")
    appendix = text.split(marker, 1)[1]
    headings = list(re.finditer(r"^### 勘误 (\d+)\(", appendix, re.MULTILINE))
    numbers = [int(h.group(1)) for h in headings]
    require(numbers and numbers == list(range(1, len(numbers) + 1)), "ERRATA_SEQUENCE")
    scopes = []
    for i, heading in enumerate(headings):
        number = int(heading.group(1))
        if number < 4:
            continue
        end = headings[i + 1].start() if i + 1 < len(headings) else len(appendix)
        block = appendix[heading.end() : end]
        matches = re.findall(
            r"^\*\*生效范围\*\*[:：]([^\n]*(?:\n(?!\s*\n|#)[^\n]+)*)", block, re.MULTILINE
        )
        require(len(matches) == 1 and matches[0].strip(), f"ERRATUM_SCOPE_MISSING: {number}")
        scope = matches[0]
        normalized = re.sub(r"[\s*`]", "", unicodedata.normalize("NFKC", scope))
        forbidden = re.search(
            r"§[3456](?!\d)|勘误(?:[123](?!\d)|[一二三])|预期差异门禁", normalized
        )
        require(forbidden is None, f"LATER_ERRATUM_AFFECTS_DIFF: E{number}: {scope}")
        scopes.append({"erratum": number, "scope": scope})
    return scopes


def tagged(item: Any) -> dict[str, Any]:
    if item is MISSING:
        return dict(ABSENT)
    if isinstance(item, dict) and item.get("state") in {"VALUE", "ABSENT"}:
        return dict(item)
    return value(item)


def changes(before: Any, after: Any, path: str = "") -> dict[str, Any]:
    """Compare every field; tagged absence/value is an atomic result value."""
    if before is not MISSING and after is not MISSING and equal(before, after):
        return {}
    if before is MISSING or after is MISSING:
        return {path: {"old": tagged(before), "new": tagged(after)}}

    def is_state(obj: Any) -> bool:
        return isinstance(obj, dict) and "state" in obj

    if (
        isinstance(before, dict)
        and isinstance(after, dict)
        and not (is_state(before) or is_state(after))
    ):
        result = {}
        for key in sorted(before.keys() | after.keys()):
            result.update(
                changes(
                    before.get(key, MISSING), after.get(key, MISSING), path + "/" + escaped(key)
                )
            )
        return result
    if isinstance(before, list) and isinstance(after, list):
        result = {}
        for i in range(max(len(before), len(after))):
            result.update(
                changes(
                    before[i] if i < len(before) else MISSING,
                    after[i] if i < len(after) else MISSING,
                    path + f"/{i}",
                )
            )
        return result
    return {path: {"old": tagged(before), "new": tagged(after)}}


def validate_value(obj: Any, schema: Any, where: str = "result") -> None:
    """Small closed schema vocabulary; JSON payloads are explicit map values.

    Heterogeneous return values, argv kwargs and reader returns remain fully
    compared by changes(), including any nested member, never normalized.
    """
    if isinstance(schema, str):
        types: dict[str, tuple[type, ...]] = {
            "str": (str,),
            "bool": (bool,),
            "int": (int,),
            "number": (int, float),
            "null": (type(None),),
        }
        if schema == "json":
            canonical(obj)
            return
        require(schema in types and type(obj) in types[schema], f"TYPE: {where}")
        return
    kind = schema.get("kind")
    if kind == "record":
        required, optional = schema["required"], schema.get("optional", {})
        require(
            isinstance(obj, dict)
            and set(required) <= set(obj)
            and set(obj) <= set(required) | set(optional),
            f"CLOSED_FIELDS: {where}",
        )
        for key, child in obj.items():
            validate_value(child, (required | optional)[key], where + "/" + key)
    elif kind == "enum":
        require(any(equal(obj, option) for option in schema["values"]), f"ENUM: {where}")
    elif kind == "array":
        require(isinstance(obj, list), f"ARRAY: {where}")
        for i, child in enumerate(obj):
            validate_value(child, schema["items"], where + f"/{i}")
    elif kind == "map":
        require(isinstance(obj, dict), f"MAP: {where}")
        for key, child in obj.items():
            validate_value(child, schema["values"], where + "/" + key)
    elif kind == "state":
        require(isinstance(obj, dict), f"STATE: {where}")
        if obj.get("state") == "ABSENT":
            fields(obj, {"state"}, where)
        else:
            fields(obj, {"state", "value"}, where)
            require(obj["state"] == "VALUE", f"STATE: {where}")
            validate_value(obj["value"], schema["value"], where + "/value")
    elif kind == "one_of":
        for choice in schema["choices"]:
            try:
                validate_value(obj, choice, where)
                return
            except GateError:
                pass
        raise GateError(f"ONE_OF: {where}")
    else:
        raise GateError(f"UNKNOWN_SCHEMA: {kind}")


def reader_names(readers: Any) -> list[str]:
    require(isinstance(readers, list) and readers, "READERS_EMPTY_OR_MISSING")
    require(all(isinstance(r, str) and r.strip() for r in readers), "READER_ID")
    require(len(readers) == len(set(readers)), "DUPLICATE_READER")
    return sorted(readers)


def readers_from_item5(output: dict[str, Any]) -> list[str]:
    """Extract membership only; caller must have verified the frozen claim."""
    require("OBS-1.item5-order" in output, "ITEM5_REQUIRED")
    scenarios = output["OBS-1.item5-order"]["scenarios"]
    require(
        {s["scenario_id"] for s in scenarios} == {"EXCLUDE_INTERRUPTED", "MARKER_WRITE_INTERRUPTED"}
        and len(scenarios) == 2,
        "ITEM5_SCENARIOS",
    )
    names = [reader_names([r["reader"] for r in s["readers"]]) for s in scenarios]
    require(names[0] == names[1], "ITEM5_READER_UNIVERSES_DIFFER")
    return names[0]


def resolve_old(recipe: dict[str, Any], sources: Sources) -> dict[str, Any]:
    kind = recipe.get("kind")
    fields(recipe, {"kind", "ref"}, "old")
    fact = sources.fact(recipe["ref"])
    if kind == "OBS_ABSENT_TIMEOUT":
        require(isinstance(fact, dict) and "timeout" not in fact, "OBS_TIMEOUT_NOT_ABSENT")
        return dict(ABSENT)
    require(kind in {"OBS_VALUE", "OBS_STATE"}, "OLD_SOURCE_KIND")
    return value(fact) if kind == "OBS_VALUE" else tagged(fact)


def resolve_new(recipe: dict[str, Any], scenario: dict[str, Any], sources: Sources) -> Any:
    kind = recipe.get("kind")
    if kind == "LITERAL":
        fields(recipe, {"kind", "value", "source"}, "new")
        sources.cite(recipe["source"])
        require(
            recipe["source"]["section"] in {"§3 预期差异", "§3.2⑥ timeout 单元格"},
            "LITERAL_AUTHORITY",
        )
        quoted = recipe["value"]
        require(
            isinstance(quoted, str) and quoted in recipe["source"]["quote"], "LITERAL_NOT_IN_SOURCE"
        )
        return value(quoted)
    if kind == "TIMEOUT_KWARG":
        fields(recipe, {"kind", "source"}, "new")
        sources.cite(recipe["source"])
        require(recipe["source"]["section"] == "附录C/E2-2", "KWARG_AUTHORITY")
        return value(scenario["timeout"])
    if kind == "TIMEOUT_WARNING":
        fields(recipe, {"kind", "source"}, "new")
        sources.cite(recipe["source"])
        require(recipe["source"]["section"] == "附录C/E1-2", "WARNING_AUTHORITY")
        require('"target_head_unknown:timeout"' in recipe["source"]["quote"], "WARNING_QUOTE")
        return value(["target_head_unknown:timeout"])
    fields(recipe, {"kind", "rule", "source", "inputs"}, "derived new")
    require(kind == "DERIVED", "NEW_SOURCE_KIND")
    sources.cite(recipe["source"])
    rule, inputs = recipe["rule"], recipe["inputs"]
    if rule in {"TIMEOUT_MESSAGE_FROM_EXC", "GIT_TIMEOUT_PREFIX_PLUS_EXC"}:
        require(recipe["source"]["section"] == "附录C/E1-2", "MESSAGE_AUTHORITY")
        fields(inputs, {"injection"}, "timeout inputs")
        exc = sources.fact(inputs["injection"])
        require(
            exc["type"] == "TimeoutExpired" and exc["timeout"] == scenario["timeout"],
            "TIMEOUT_FIXTURE",
        )
        message = str(subprocess.TimeoutExpired(exc["cmd"], exc["timeout"]))
        require(message == exc["message"], "TIMEOUT_OBS_MESSAGE")
        return value(("GIT_TIMEOUT: " if rule == "GIT_TIMEOUT_PREFIX_PLUS_EXC" else "") + message)
    require(
        rule == "EXISTING_BRANCH_OUTPUT" and scenario["id"] == "DANGLING_SYMLINK",
        "EXISTING_BRANCH_SCOPE",
    )
    require(recipe["source"]["section"] == "附录C/E2-1", "BRANCH_AUTHORITY")
    fields(inputs, {"anchor", "adjacent", "destination"}, "branch inputs")
    anchor = sources.fact(inputs["anchor"])
    require(
        anchor["matched_count"] == 1
        and anchor["function"] == "_reset_generated_source_dir"
        and anchor["selector"]
        == "FunctionDef//BoolOp.And[direct operand calls include exists,is_symlink]",
        "ANCHOR3",
    )
    adjacent = sources.fact(inputs["adjacent"])
    require(adjacent["scenario_id"] == "LIVE_SYMLINK_TO_DIR", "ADJACENT_SCENARIO")
    require(
        adjacent["outcome"]["exception"]["value"]["message"]
        == "source directory is a symlink: " + adjacent["fixture"] + "/destination",
        "E2-1_LIVE_MESSAGE_MISMATCH",
    )
    destination = sources.fact(inputs["destination"]) + "/destination"
    require(destination == scenario["fixture"]["destination"], "BRANCH_FIXTURE")
    return value("source directory is a symlink: " + destination)


def check_mode(entry: Any) -> None:
    require(isinstance(entry, dict), "MODE_OBJECT")
    mode = entry.get("mode")
    if mode == "NO_DIFF":
        fields(entry, {"mode", "reason"}, "NO_DIFF")
        require(isinstance(entry["reason"], str) and entry["reason"].strip(), "EMPTY_REASON")
    elif mode == "DIFF_SET":
        fields(entry, {"mode", "differences"}, "DIFF_SET")
        require(isinstance(entry["differences"], dict) and entry["differences"], "EMPTY_DIFF_SET")
        for path, change in entry["differences"].items():
            require(isinstance(path, str) and path.startswith("/"), "DIFF_POINTER")
            fields(change, {"old", "new", "reason"}, path)
            require(isinstance(change["reason"], str) and change["reason"].strip(), "EMPTY_REASON")
    else:
        raise GateError("MODE_MISSING_OR_UNKNOWN")


def compare_one(before: Any, after: Any, entry: dict[str, Any], resolved: dict[str, Any]) -> None:
    check_mode(entry)
    actual = changes(before, after)
    require(
        set(actual) == set(resolved),
        f"DIFF_PATHS: extra={sorted(actual.keys() - resolved.keys())} "
        f"missing={sorted(resolved.keys() - actual.keys())}",
    )
    for path in actual:
        require(equal(actual[path], resolved[path]), f"DIFF_VALUE: {path}")


def timeout_outcome(observed: dict[str, Any]) -> dict[str, Any]:
    """E3-2: project the archived outcome, including unchanged result fields."""
    outcome = observed["outcome"]
    exc = outcome["exception"].get("value", {})
    return {
        "return_value": outcome["return_value"],
        "exception_type": value(exc["type"]) if "type" in exc else dict(ABSENT),
        "exception_code": exc.get("code", dict(ABSENT)),
        "exception_message": value(exc["message"]) if "message" in exc else dict(ABSENT),
        "warnings": outcome["return_value"]
        if observed["surface"] == "submit-remote"
        else dict(ABSENT),
    }


class Gate:
    def __init__(self, manifest: Any, schema: Any, expected: Any, sources: Sources):
        self.manifest, self.schema, self.expected, self.sources = (
            manifest,
            schema,
            expected,
            sources,
        )

    def validate(self) -> dict[str, Any]:
        fields(self.manifest, {"version", "rules", "before_run", "scenarios"}, "manifest")
        require(self.manifest["version"] == 1, "MANIFEST_VERSION")
        require(self.manifest["before_run"] == "PENDING_SEG3", "SEGMENT2_SCOPE")
        self.sources.cite(self.manifest["rules"])
        fields(self.expected, {"version", "scenarios"}, "expected_diff")
        require(self.expected["version"] == 1, "REGISTRY_VERSION")
        fields(self.schema, {"version", "result", "readers_source"}, "result_schema")
        require(
            self.schema["version"] == 1 and self.schema["readers_source"] == "OBS-1.item5-order",
            "READER_AUTHORITY",
        )
        rows = self.manifest["scenarios"]
        ids = [r["id"] for r in rows]
        required = {
            "DANGLING_SYMLINK",
            "LIVE_SYMLINK_TO_DIR",
            "REAL_DIR",
            "ABSENT",
            "EXCLUDE_INTERRUPTED",
            "MARKER_WRITE_INTERRUPTED",
        }
        required.update(
            f"surface{i}-{fault}"
            for i in range(1, 7)
            for fault in ("none", "timeout", "SIGINT", "SIGTERM")
        )
        require(len(ids) == len(set(ids)) and set(ids) == required, "SCENARIO_CLOSED_SET")
        require(set(self.expected["scenarios"]) == set(ids), "SCENARIO_REGISTRATION")
        resolved = {}
        for row in rows:
            row_fields = {
                "id",
                "section",
                "surface",
                "fault",
                "timeout",
                "fixture",
                "calls",
                "obs_ref",
            }
            if row.get("fault") == "timeout":
                row_fields.add("before_run")
            fields(
                row,
                row_fields,
                "scenario",
            )
            fields(row["fixture"], {"destination"}, "fixture")
            require(Path(row["fixture"]["destination"]).is_absolute(), "FIXTURE_PATH")
            require(row["fault"] in {"none", "timeout", "SIGINT", "SIGTERM"}, "FAULT")
            require(row["timeout"] is None or type(row["timeout"]) in {int, float}, "TIMEOUT")
            require((row["fault"] == "timeout") == (row["timeout"] is not None), "TIMEOUT_INPUT")
            observed = self.sources.fact(row["obs_ref"])
            sid = row["id"]
            if sid.startswith("surface"):
                number, fault = sid.removeprefix("surface").split("-", 1)
                require(
                    (row["section"], row["surface"], row["fault"])
                    == ("§4", SURFACES[int(number) - 1], fault),
                    "SCENARIO_COORDINATES",
                )
                require(observed["scenario_id"] == sid, "OBS_SCENARIO_BINDING")
                if fault == "timeout":
                    require(row["obs_ref"]["file"] == OBS + "e1-item4/raw.json", "TIMEOUT_OBS_FILE")
                    plan = row["before_run"]
                    fields(
                        plan, {"method", "pass_timeout", "injection_ref", "source"}, "before_run"
                    )
                    self.sources.cite(plan["source"])
                    require(plan["source"]["section"] == "附录C/E3-1", "TIMEOUT_BEFORE_AUTHORITY")
                    injection_ref = dict(row["obs_ref"])
                    injection_ref["pointer"] += "/injection"
                    require(
                        plan["method"]
                        == (
                            "同一 fixture、同一调用处注入 subprocess.TimeoutExpired，"
                            "不传 timeout 参数"
                        )
                        and plan["pass_timeout"] is False
                        and plan["injection_ref"] == injection_ref,
                        "TIMEOUT_BEFORE_PLAN",
                    )
                    injection = self.sources.fact(injection_ref)
                    require(
                        injection["type"] == "TimeoutExpired"
                        and injection["timeout"] == row["timeout"]
                        and any(
                            equal(call["argv"], injection["cmd"]) for call in observed["trace"]
                        ),
                        "TIMEOUT_INJECTION_BINDING",
                    )
            elif sid in {"EXCLUDE_INTERRUPTED", "MARKER_WRITE_INTERRUPTED"}:
                section = "§5(i)" if sid == "EXCLUDE_INTERRUPTED" else "§5(ii)"
                require(
                    (row["section"], row["surface"], row["fault"])
                    == (section, "shared-exclude", "SIGINT"),
                    "SCENARIO_COORDINATES",
                )
                require(observed["surface"] == "shared-exclude", "MARKER_KWARG_SURFACE")
            else:
                require(
                    (row["section"], row["surface"], row["fault"]) == ("§3", "fetch-full", "none"),
                    "SCENARIO_COORDINATES",
                )
                require(observed["scenario_id"] == sid, "OBS_SCENARIO_BINDING")
            require(
                row["fixture"]["destination"] == observed["fixture"] + "/destination",
                "FIXTURE_SOURCE",
            )
            require(len(row["calls"]) == len(observed["trace"]), "CALL_COUNT")
            for i, call in enumerate(row["calls"]):
                fields(call, {"surface", "trace_ref"}, "call")
                require(call["surface"] in SURFACES, "CALL_SURFACE")
                require(
                    equal(self.sources.fact(call["trace_ref"]), observed["trace"][i]), "CALL_SOURCE"
                )
            entry = self.expected["scenarios"][row["id"]]
            check_mode(entry)
            if row["fault"] == "timeout" and row["surface"] in SURFACES[:3]:
                require(
                    "/exception_message" not in entry.get("differences", {}),
                    "UNCHANGED_TIMEOUT_MESSAGE_REGISTERED",
                )
            deltas = {}
            for path, change in entry.get("differences", {}).items():
                old = resolve_old(change["old"], self.sources)
                new = resolve_new(change["new"], row, self.sources)
                require(not equal(old, new), f"IMPOSSIBLE_NO_CHANGE: {path}")
                deltas[path] = {"old": old, "new": new}
            # Every observed call traverses one of the new optional signatures.
            kwpaths = {f"/calls/{i}/kwargs/timeout" for i in range(len(row["calls"]))}
            require(kwpaths <= set(deltas), f"TIMEOUT_REGISTRATION_MISSING: {row['id']}")
            for path in kwpaths:
                change = entry["differences"][path]
                require(
                    change["new"]["kind"] == "TIMEOUT_KWARG"
                    and change["old"]["kind"] == "OBS_ABSENT_TIMEOUT",
                    "KWARG_SOURCES",
                )
                index = int(path.split("/")[2])
                ref = dict(row["calls"][index]["trace_ref"])
                ref["pointer"] += "/kwargs"
                require(change["old"]["ref"] == ref, "KWARG_OLD_CALL_BINDING")
            allowed_results = set()
            if row["id"] == "DANGLING_SYMLINK":
                allowed_results = {"/exception_type", "/exception_code", "/exception_message"}
            elif row["fault"] == "timeout":
                if row["surface"] == "submit-remote":
                    allowed_results = {"/warnings", "/return_value"}
                else:
                    allowed_results = {"/exception_type"}
                    if row["surface"] in {"fetch-query", "fetch-git", "submit-git"}:
                        allowed_results.add("/exception_code")
                    else:
                        allowed_results.add("/exception_message")
            require(set(deltas) == kwpaths | allowed_results, "REGISTRATION_PATH_CLOSED_SET")
            for path in allowed_results:
                delta = entry["differences"][path]
                new = delta["new"]
                if row["fault"] == "timeout":
                    expected_ref = dict(row["obs_ref"])
                    if path in {"/warnings", "/return_value"}:
                        suffix, old_kind = "/outcome/return_value", "OBS_STATE"
                    else:
                        field = path.removeprefix("/exception_")
                        suffix = "/outcome/exception/value/" + field
                        old_kind = "OBS_STATE" if field == "code" else "OBS_VALUE"
                    expected_ref["pointer"] += suffix
                    require(
                        delta["old"] == {"kind": old_kind, "ref": expected_ref},
                        "TIMEOUT_RESULT_OLD_SOURCE_BINDING",
                    )
                    if row["surface"] == "submit-remote":
                        require(new["kind"] == "TIMEOUT_WARNING", "WARNING_SOURCE_KIND")
                    elif path == "/exception_message":
                        rule = (
                            "GIT_TIMEOUT_PREFIX_PLUS_EXC"
                            if row["surface"].startswith("shared-")
                            else "TIMEOUT_MESSAGE_FROM_EXC"
                        )
                        require(new.get("rule") == rule, "MESSAGE_RULE_BINDING")
                        injection = dict(row["obs_ref"])
                        injection["pointer"] += "/injection"
                        require(new["inputs"]["injection"] == injection, "INJECTION_SOURCE_BINDING")
                    else:
                        quote = new["source"]["quote"]
                        require(
                            new["source"]["file"] == TABLE
                            and quote
                            == self.sources.timeout_cells()[SURFACES.index(row["surface"])],
                            "MAPPING_SURFACE_BINDING",
                        )
                        column = quote.split("|")[2]
                        pattern = (
                            r"(GerritError|GerritSubmitError|WorkspaceViolation)\("
                            if path == "/exception_type"
                            else r'\("([A-Z_]+)"'
                        )
                        match = re.search(pattern, column)
                        require(
                            new["kind"] == "LITERAL" and match and new["value"] == match.group(1),
                            "MAPPING_CELL_EXTRACTION",
                        )
                else:
                    field = path.removeprefix("/exception_")
                    expected_ref = dict(row["obs_ref"])
                    expected_ref["pointer"] += "/outcome/exception/value/" + field
                    require(delta["old"].get("ref") == expected_ref, "SYMLINK_OLD_SOURCE_BINDING")
                    if field == "message":
                        require(new.get("rule") == "EXISTING_BRANCH_OUTPUT", "SYMLINK_MESSAGE_RULE")
                    else:
                        require(
                            new["kind"] == "LITERAL" and new["source"]["section"] == "§3 预期差异",
                            "SYMLINK_NEW_SOURCE_BINDING",
                        )
            resolved[row["id"]] = deltas
        return resolved

    def validate_results(self, results: Any, readers: Any) -> None:
        names = reader_names(readers)
        require(
            isinstance(results, dict)
            and set(results) == {s["id"] for s in self.manifest["scenarios"]},
            "RESULT_SCENARIOS",
        )
        for scenario in self.manifest["scenarios"]:
            obj = results[scenario["id"]]
            validate_value(obj, self.schema["result"], scenario["id"])
            require(len(obj["calls"]) == len(scenario["calls"]), "RESULT_CALL_COUNT")
            marker = obj["protected_marker"]
            observed = [r["reader"] for r in marker["readers"]]
            require(reader_names(observed) == names, "RESULT_READER_MEMBERSHIP")
            for field in ("workdir_marker", "protected_marker"):
                m = obj[field]
                require((m["sha256"]["state"] == "VALUE") == m["exists"], "MARKER_HASH_STATE")
                if m["exists"]:
                    require(re.fullmatch(r"[0-9a-f]{64}", m["sha256"]["value"]), "MARKER_HASH")

    def item3_projection(self) -> list[dict[str, Any]]:
        """PHASE1-03: derive postponed fields from registered sources, never results."""
        self.validate()
        excluded = []
        for sid, entry in self.expected["scenarios"].items():
            for path, delta in entry.get("differences", {}).items():
                source = delta["new"]["source"]
                if source["file"] == DOC and (
                    re.fullmatch(r"§3(?:\s.*)?", source["section"])
                    or source["section"] == "附录C/E2-1"
                ):
                    excluded.append({"scenario": sid, "path": path, "source": source})
        return excluded

    def compare(self, before: Any, after: Any, readers: Any, *, phase: str = "FULL") -> None:
        require(phase in {"A", "FULL"}, "UNKNOWN_PHASE")
        resolved = self.validate()
        excluded = (
            {(row["scenario"], row["path"]) for row in self.item3_projection()}
            if phase == "A"
            else set()
        )
        self.validate_results(before, readers)
        self.validate_results(after, readers)
        for row in self.manifest["scenarios"]:
            if row["fault"] == "timeout":
                for field, old in timeout_outcome(self.sources.fact(row["obs_ref"])).items():
                    require(
                        equal(before[row["id"]][field], old),
                        f"TIMEOUT_BEFORE_OUTCOME: {row['id']}/{field}",
                    )
        for sid, entry in self.expected["scenarios"].items():
            if phase == "A" and entry["mode"] == "DIFF_SET":
                active = {
                    path: delta
                    for path, delta in entry["differences"].items()
                    if (sid, path) not in excluded
                }
                projected_entry = (
                    {"mode": "DIFF_SET", "differences": active}
                    if active
                    else {"mode": "NO_DIFF", "reason": "PHASE1-03: item3 remains before"}
                )
                compare_one(
                    before[sid],
                    after[sid],
                    projected_entry,
                    {path: resolved[sid][path] for path in active},
                )
            else:
                compare_one(before[sid], after[sid], entry, resolved[sid])

    def collect(
        self, runner: Callable[[dict[str, Any], list[str]], dict[str, Any]], readers: Any
    ) -> dict[str, Any]:
        """The caller supplies an isolated before OR after collector, never an OBS producer."""
        self.validate()
        names = reader_names(readers)
        result = {
            row["id"]: copy.deepcopy(runner(copy.deepcopy(row), names[:]))
            for row in self.manifest["scenarios"]
        }
        self.validate_results(result, names)
        return result

    def dual_run(
        self, before_runner: Callable[..., Any], after_runner: Callable[..., Any], readers: Any
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        before = self.collect(before_runner, readers)
        after = self.collect(after_runner, readers)
        self.compare(before, after, readers)
        return before, after


def load_gate(root: Path, data: Path = DATA) -> Gate:
    check_frozen_hashes(
        load_json(DATA / "predicates.json"), load_json(DATA / "measurement_exemptions.json")
    )
    return Gate(
        load_json(data / "scenario_manifest.json"),
        load_json(data / "result_schema.json"),
        load_json(data / "expected_diff.json"),
        Sources(root),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check", "compare"])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--data", type=Path, default=DATA)
    parser.add_argument("--before", type=Path)
    parser.add_argument("--after", type=Path)
    parser.add_argument("--item5-output", type=Path)
    parser.add_argument("--phase", choices=["A", "FULL"], default="FULL")
    parser.add_argument("--projection-output", type=Path)
    args = parser.parse_args()
    try:
        gate = load_gate(args.root, args.data)
        resolved = gate.validate()
        if args.projection_output:
            with args.projection_output.open("x", encoding="utf-8") as handle:
                json.dump(gate.item3_projection(), handle, ensure_ascii=False, indent=2)
                handle.write("\n")
        if args.command == "compare":
            require(
                args.before and args.after and args.item5_output, "BOTH_RUNS_AND_ITEM5_REQUIRED"
            )
            readers = readers_from_item5(load_json(args.item5_output))
            gate.compare(load_json(args.before), load_json(args.after), readers, phase=args.phase)
        entries = list(gate.expected["scenarios"].values())
        print(
            f"STRUCTURE_SOURCES=PASS scenarios={len(entries)} "
            f"NO_DIFF={sum(e['mode'] == 'NO_DIFF' for e in entries)} "
            f"DIFF_SET={sum(e['mode'] == 'DIFF_SET' for e in entries)} "
            f"registrations={sum(map(len, resolved.values()))}"
        )
        print("REAL_BEFORE=PENDING_SEG3" if args.command == "check" else "EXACT_DIFF=PASS")
        return 0
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f"GATE_REJECTED: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
