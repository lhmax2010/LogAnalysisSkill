"""Derive Section 6 registration files from approved documents and archived JSON.

This is a registration generator, not an OBS producer or a before-run collector.
It never imports or executes production code, and never overwrites OBS artifacts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from terminal_expected_diff import (
    DATA,
    DOC,
    DOC_HASH,
    OBS,
    OBS_HASHES,
    SURFACES,
    TABLE,
    TABLE_HASH,
    Gate,
    Sources,
    require,
)


def record(required: dict[str, Any], optional: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"kind": "record", "required": required, "optional": optional or {}}


def array(items: Any) -> dict[str, Any]:
    return {"kind": "array", "items": items}


def state(items: Any) -> dict[str, Any]:
    return {"kind": "state", "value": items}


def schema() -> dict[str, Any]:
    outcome = {
        "return_value": state("json"),
        "exception_type": state("str"),
        "exception_code": state("str"),
        "exception_message": state("str"),
    }
    reader = record({"reader": "str", **outcome})
    marker = {"exists": "bool", "sha256": state("str")}
    path_state = state(
        record(
            {
                "exists": "bool",
                "kind": {"kind": "enum", "values": ["ABSENT", "DIRECTORY", "FILE", "SYMLINK"]},
                "symlink_target": state("str"),
                "files": {"kind": "map", "values": "str"},
            }
        )
    )
    kwargs = record(
        {},
        {
            "check": "bool",
            "capture_output": "bool",
            "text": "bool",
            "env": {"kind": "one_of", "choices": ["null", {"kind": "map", "values": "str"}]},
            "timeout": {"kind": "one_of", "choices": ["null", "number"]},
        },
    )
    return {
        "version": 1,
        "readers_source": "OBS-1.item5-order",
        "result": record(
            {
                **outcome,
                "warnings": state(array("str")),
                "action": state("str"),
                "calls": array(record({"argv": array("str"), "kwargs": kwargs})),
                "destination": path_state,
                "worktree": path_state,
                "workdir_marker": record(marker),
                "protected_marker": record({**marker, "readers": array(reader)}),
                "exclude_completed": state("bool"),
                "exit_code": state("int"),
            }
        ),
    }


def ref(file: str, path: str) -> dict[str, Any]:
    return {"file": file, "sha256": OBS_HASHES[file], "pointer": path}


def cite(file: str, section: str, quote: str) -> dict[str, Any]:
    return {
        "file": file,
        "sha256": DOC_HASH if file == DOC else TABLE_HASH,
        "section": section,
        "quote": quote,
    }


def derive(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    sources = Sources(root)
    text = sources.read(DOC, DOC_HASH).decode()
    # Anchored rows remain byte-for-byte authority quotes, not a second mapping table.
    rows = sources.timeout_cells()
    timeout_before = cite(DOC, "附录C/E3-1", text.split("**E3-1 ·", 1)[1].split("**E3-2 ·", 1)[0])
    symlink_source = cite(
        DOC,
        "§3 预期差异",
        text.split("- **预期差异**(§6 登记", 1)[1].split("- 须更新 skill-3", 1)[0],
    )
    e1 = cite(DOC, "附录C/E1-2", text.split("**E1-2 ·", 1)[1].split("**生效范围**", 1)[0])
    e2 = cite(DOC, "附录C/E2-1", text.split("**E2-1 ·", 1)[1].split("**E2-2 ·", 1)[0])
    kwargs_source = cite(
        DOC, "附录C/E2-2", text.split("**E2-2 ·", 1)[1].split("**生效范围**", 1)[0]
    )
    manifest: dict[str, Any] = {
        "version": 1,
        "before_run": "PENDING_SEG3",
        "rules": cite(DOC, "§6", "## §6 [本批核心机制] 预期差异门禁"),
        "scenarios": [],
    }
    expected: dict[str, Any] = {"version": 1, "scenarios": {}}

    def add(sid: str, section: str, surface: str, fault: str, file: str, index: int) -> None:
        base = f"/observations/{index}"
        observed = sources.fact(ref(file, base))
        timeout = observed["injection"]["timeout"] if fault == "timeout" else None
        calls = []
        for i, call in enumerate(observed["trace"]):
            call_surface = surface
            if section == "§3":
                call_surface = "fetch-query" if call["argv"][0] == "ssh" else "fetch-git"
            calls.append({"surface": call_surface, "trace_ref": ref(file, base + f"/trace/{i}")})
        row = {
            "id": sid,
            "section": section,
            "surface": surface,
            "fault": fault,
            "timeout": timeout,
            "fixture": {"destination": observed["fixture"] + "/destination"},
            "calls": calls,
            "obs_ref": ref(file, base),
        }
        if fault == "timeout":
            row["before_run"] = {
                "method": (
                    "同一 fixture、同一调用处注入 subprocess.TimeoutExpired，"
                    "不传 timeout 参数"
                ),
                "pass_timeout": False,
                "injection_ref": ref(file, base + "/injection"),
                "source": timeout_before,
            }
        manifest["scenarios"].append(row)
        differences: dict[str, Any] = {}
        for i, _ in enumerate(calls):
            differences[f"/calls/{i}/kwargs/timeout"] = {
                "old": {
                    "kind": "OBS_ABSENT_TIMEOUT",
                    "ref": ref(file, base + f"/trace/{i}/kwargs"),
                },
                "new": {"kind": "TIMEOUT_KWARG", "source": kwargs_source},
                "reason": "E2-2:逐调用登记新增timeout关键字;其它调用参数逐字比较。",
            }
        if sid == "DANGLING_SYMLINK":
            for name, literal in (("type", "GerritError"), ("code", "SOURCE_DIR_UNSAFE")):
                differences["/exception_" + name] = {
                    "old": {
                        "kind": "OBS_STATE" if name == "code" else "OBS_VALUE",
                        "ref": ref(file, base + "/outcome/exception/value/" + name),
                    },
                    "new": {"kind": "LITERAL", "value": literal, "source": symlink_source},
                    "reason": "§3:悬空链接改走SOURCE_DIR_UNSAFE既有分支。",
                }
            differences["/exception_message"] = {
                "old": {
                    "kind": "OBS_VALUE",
                    "ref": ref(file, base + "/outcome/exception/value/message"),
                },
                "new": {
                    "kind": "DERIVED",
                    "rule": "EXISTING_BRANCH_OUTPUT",
                    "source": e2,
                    "inputs": {
                        "anchor": ref(
                            OBS + "e1-item3/output.json", "/OBS-1.item3-predicate/anchor"
                        ),
                        "adjacent": ref(file, "/observations/1"),
                        "destination": ref(file, base + "/fixture"),
                    },
                },
                "reason": "E2-1:用LIVE相邻观测验证消息形式,代入本场景destination。",
            }
        if fault == "timeout":
            cell = cite(TABLE, "§3.2⑥ timeout 单元格", rows[SURFACES.index(surface)])
            if surface == "submit-remote":
                for path in ("/warnings", "/return_value"):
                    differences[path] = {
                        "old": {
                            "kind": "OBS_STATE",
                            "ref": ref(file, base + "/outcome/return_value"),
                        },
                        "new": {"kind": "TIMEOUT_WARNING", "source": e1},
                        "reason": "映射表ls-remote告警单元格与E1-2:保留告警返回形状,统一码值。",
                    }
            else:
                exc_type = (
                    "GerritError"
                    if surface.startswith("fetch-")
                    else "GerritSubmitError"
                    if surface == "submit-git"
                    else "WorkspaceViolation"
                )
                differences["/exception_type"] = {
                    "old": {
                        "kind": "OBS_VALUE",
                        "ref": ref(file, base + "/outcome/exception/value/type"),
                    },
                    "new": {"kind": "LITERAL", "value": exc_type, "source": cell},
                    "reason": "E3-2:旧TimeoutExpired来自同场景outcome,新类型取映射表该调用面。",
                }
                if surface in {"fetch-query", "fetch-git", "submit-git"}:
                    differences["/exception_code"] = {
                        "old": {
                            "kind": "OBS_STATE",
                            "ref": ref(file, base + "/outcome/exception/value/code"),
                        },
                        "new": {
                            "kind": "LITERAL",
                            "value": "GIT_TIMEOUT" if surface == "submit-git" else "FETCH_TIMEOUT",
                            "source": cell,
                        },
                        "reason": "映射表该调用面的具名异常code字段。",
                    }
                if surface.startswith("shared-"):
                    differences["/exception_message"] = {
                        "old": {
                            "kind": "OBS_VALUE",
                            "ref": ref(file, base + "/outcome/exception/value/message"),
                        },
                        "new": {
                            "kind": "DERIVED",
                            "rule": "GIT_TIMEOUT_PREFIX_PLUS_EXC",
                            "source": e1,
                            "inputs": {"injection": ref(file, base + "/injection")},
                        },
                        "reason": "E3-2/E1-2:同场景旧消息增加GIT_TIMEOUT:前缀,逐字比较。",
                    }
        expected["scenarios"][sid] = (
            {"mode": "DIFF_SET", "differences": differences}
            if differences
            else {"mode": "NO_DIFF", "reason": "未经过新签名,且本场景无授权的结果变化。"}
        )

    item3 = OBS + "e1-item3/raw.json"
    for i, sid in enumerate(("DANGLING_SYMLINK", "LIVE_SYMLINK_TO_DIR", "REAL_DIR", "ABSENT")):
        add(sid, "§3", "fetch-full", "none", item3, i)
    item4 = OBS + "e1-item4/raw.json"
    for i, surface in enumerate(SURFACES):
        for j, fault in enumerate(("none", "timeout", "SIGINT", "SIGTERM")):
            add(f"surface{i + 1}-{fault}", "§4", surface, fault, item4, i * 4 + j)
    # These references prove ONLY the old absence of the kwarg on that call.
    # They are not claimed to be Section 5 before-run or reader observations.
    add("EXCLUDE_INTERRUPTED", "§5(i)", "shared-exclude", "SIGINT", item4, 22)
    add("MARKER_WRITE_INTERRUPTED", "§5(ii)", "shared-exclude", "SIGINT", item4, 20)
    result = schema()
    Gate(manifest, result, expected, sources).validate()
    return manifest, result, expected


def source_report(manifest: dict[str, Any], expected: dict[str, Any]) -> str:
    lines = [
        "# Section 6 Registration Sources",
        "",
        "Generated from the registration JSON, not a second authority. Before-run: PENDING_SEG3.",
        "Every listed path changes; every unlisted field must compare exactly equal.",
        "",
        "| Scenario | Field | Old Source | New Source |",
        "|---|---|---|---|",
    ]
    for row in manifest["scenarios"]:
        for path, delta in expected["scenarios"][row["id"]].get("differences", {}).items():
            old, new = delta["old"], delta["new"]
            r = old["ref"]
            origin = r["file"].split("/part2/")[1] + "#" + r["pointer"]
            target = new["source"]["section"]
            if new["kind"] == "DERIVED":
                target += ": " + new["rule"]
            elif new["kind"] == "LITERAL":
                target += ": " + new["value"]
            elif new["kind"] == "TIMEOUT_KWARG":
                target += ": timeout=" + json.dumps(row["timeout"])
            else:
                target += ": target_head_unknown:timeout"
            lines.append(f"| {row['id']} | `{path}` | `{old['kind']}`: {origin} | {target} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--output", type=Path, default=DATA)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    manifest, result, expected = derive(args.root)
    outputs = {
        name: (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode()
        for name, obj in zip(
            ("scenario_manifest.json", "result_schema.json", "expected_diff.json"),
            (manifest, result, expected),
            strict=True,
        )
    }
    outputs["expected_diff_sources.md"] = source_report(manifest, expected).encode()
    for name, content in outputs.items():
        path = args.output / name
        if args.check:
            require(path.read_bytes() == content, f"GENERATED_DATA_DRIFT: {name}")
        else:
            require(not path.exists(), f"REFUSE_OVERWRITE: {path}")
            path.write_bytes(content)
    print(
        f"REGISTRATION_DATA={'MATCH' if args.check else 'CREATED'} "
        f"scenarios={len(manifest['scenarios'])}"
    )


if __name__ == "__main__":
    main()
