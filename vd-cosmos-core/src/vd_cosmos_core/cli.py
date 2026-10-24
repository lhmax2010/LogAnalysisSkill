"""One JSON object on stdout, immutable attempt artifacts, and journaled outcomes."""
import argparse
import json
import sys
import uuid

from .backends import FixtureReportReader, SavedReportReader, timestamp
from .commands import COMMANDS, Category, command_context
from .config import load_config
from .errors import FlowError, unsupported
from .export import check_content, export_file
from .files import atomic_write, digest, json_bytes
from .groups import group_expansion
from .locks import OperationLock
from .state import EventStore


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise FlowError(2, "invalid_arguments")


PUBLIC = {"watch": ["observe"], "fetch": ["packages", "inputs", "groups", "logs"],
          "core": ["status", "export", "prepush"]}


def parser_for(skill):
    parser = Parser(add_help=False)
    choices = list(PUBLIC[skill])
    if skill == "core":
        choices += [k for k, v in COMMANDS.items() if v in {Category.HUMAN, Category.EXTERNAL}]
    parser.add_argument("command", choices=choices)
    parser.add_argument("--config", required=True)
    parser.add_argument("--backend", choices=["fixture", "real"], default="fixture")
    parser.add_argument("--manifest")
    parser.add_argument("--arch")
    parser.add_argument("--expected-event", type=int)
    parser.add_argument("--source")
    parser.add_argument("--type", dest="material_type")
    parser.add_argument("--name")
    parser.add_argument("--files", nargs="*")
    return parser


def _todos(store, context, expected, build_key, todos, config):
    seen = {e["payload"].get("todo_key") for e in store.events() if e["kind"] == "inbox_opened"}
    for todo in todos:
        todo_key = digest(json_bytes({"build": build_key, "todo": todo}))
        if todo_key not in seen:
            expected = store.append(context, "inbox_opened", {"todo_key": todo_key, "todo": todo,
                                    "build": build_key}, expected)
            seen.add(todo_key)
    lines = ["# 待办", ""] + ["- " + json.dumps(e["payload"]["todo"], ensure_ascii=False)
                                   for e in store.events() if e["kind"] == "inbox_opened"]
    atomic_write(config.data_root, "inbox.md", ("\n".join(lines) + "\n").encode())
    return expected


def _read_action(skill, args, reader):
    ref = reader.build_ref
    if skill == "watch":
        return reader.observe(ref)
    if args.command == "inputs":
        return reader.read_inputs(ref)
    if args.command == "packages":
        if not args.arch:
            raise FlowError(2, "architecture_required")
        return reader.read_packages(ref, args.arch)
    observed = reader.observe(ref)
    if observed["observation_failed"]:
        return observed
    packages = [p for r in observed["reports"].values() for p in r.get("packages", [])]
    if args.command == "groups":
        return {**group_expansion(packages, reader.provides()), "todos": observed["todos"]}
    reader.require("fetch_log")
    logs = []
    for package in packages:
        if package["category"] in {"build_error", "export_error"} and package["log_url"]:
            logs.append({"key": package["key"], **reader.fetch_log(ref, package["key"]["arch"], package)})
    return {"logs": logs, "todos": observed["todos"]}


def execute(skill, args):
    name = f"{skill}.{args.command}" if args.command in PUBLIC[skill] else args.command
    context = command_context(name)
    if context.category in {Category.HUMAN, Category.EXTERNAL}:
        unsupported(args.command)
    config = load_config(args.config)
    if skill == "core":
        if args.command == "prepush":
            if not args.files:
                raise FlowError(2, "files_required")
            checked = []
            for source in args.files:
                path = config.source(source)
                checks = check_content(path.read_bytes(), config, test_exemptions=True)
                checked.append({"path": str(path), **checks})
            return {"files": checked, "exit_code": 0 if all(c["allowed"] for c in checked) else 4}
        if args.command == "export":
            if not all((args.source, args.material_type, args.name)):
                raise FlowError(2, "export_arguments_required")
            with OperationLock(config.data_root, "round", "export"):
                return export_file(config, args.source, args.material_type, args.name)
        with EventStore(config.data_root) as store:
            return {"last_event_id": store.head(), "events": len(store.events())}
    if not args.manifest:
        raise FlowError(2, "manifest_required")
    reader_type = FixtureReportReader if args.backend == "fixture" else SavedReportReader
    reader = reader_type(config, args.manifest)
    build_key = digest(json_bytes(reader.build_ref.to_dict()))
    with OperationLock(config.data_root, "round", build_key), EventStore(config.data_root) as store:
        expected = args.expected_event if args.expected_event is not None else store.head()
        attempt = uuid.uuid4().hex
        current = store.append(context, "observation_started", {"attempt": attempt, "build": build_key}, expected)
        try:
            data = _read_action(skill, args, reader)
        except FlowError as error:
            store.append(context, "observation_failed", {"attempt": attempt, "build": build_key,
                         "reason": error.reason}, current)
            raise
        exit_code = data.get("exit_code", 0)
        path = f"rounds/{build_key}/attempt-{attempt}/{skill}-{args.command}.json"
        artifact = atomic_write(config.data_root, path, json_bytes(data))
        payload = {"build": build_key, "attempt": attempt, "artifact": artifact,
                   "report_state": data.get("report_state"), "result_state": data.get("result_state"),
                   "header_consistency": data.get("header_consistency"), "exit_code": exit_code}
        if skill == "watch":
            payload["content_fingerprint"] = digest(json_bytes({a: r.get("evidence", {}).get("sha256")
                                                              for a, r in data["reports"].items()}))
            payload["observed_at"] = data["observed_at"]
        current = store.append(context, "observation_failed" if exit_code else "observation_recorded", payload, current)
        todos = list(data.get("todos", []))
        if skill == "watch" and not exit_code and data.get("report_state") != "完整":
            history = [e["payload"] for e in store.events() if e["kind"] == "observation_recorded"
                       and e["command"] == "watch.observe" and e["payload"].get("build") == build_key]
            distinct = {p["observed_at"]: p for p in history if p.get("observed_at")}
            ordered = [distinct[k] for k in sorted(distinct)]
            count = config.raw["poll"].get("stall_polls", 6)
            recent = ordered[-count:]
            if len(recent) == count and all(p["content_fingerprint"] == payload["content_fingerprint"] for p in recent):
                if timestamp(recent[-1]["observed_at"]) - timestamp(recent[0]["observed_at"]) >= (count - 1) * config.raw["poll"]["interval_s"]:
                    todos.append({"reason": "report_stalled"})
            if ordered and data.get("observed_at") and timestamp(data["observed_at"]) - timestamp(ordered[0]["observed_at"]) > config.raw["poll"].get("expected_hours", 24) * 5400:
                todos.append({"reason": "expected_observation_duration_exceeded"})
        if exit_code == 5:
            outcomes = [e for e in store.events() if e["kind"] in {"observation_failed", "observation_recorded"}
                        and e["payload"].get("build") == build_key]
            todos = []
            if len(outcomes) >= 3 and all(e["kind"] == "observation_failed" for e in outcomes[-3:]):
                todos.append({"reason": "three_consecutive_observation_failures"})
        if config.filesystem["free_bytes"] < config.raw.get("budget", {}).get("disk_warning_bytes", 0):
            todos.append({"reason": "disk_low", "free_bytes": config.filesystem["free_bytes"]})
        current = _todos(store, context, current, build_key, todos, config)
        return {"artifact": artifact, "last_event_id": current, "exit_code": exit_code,
                **{key: data[key] for key in ("execution_state", "report_state", "result_state", "header_consistency") if key in data}}


def main(skill, argv=None):
    argv = sys.argv[1:] if argv is None else argv
    try:
        if "--help" in argv or "-h" in argv:
            output = {"ok": True, "skill": skill, "commands": PUBLIC[skill],
                      "usage": "python3 <skill>/scripts/run.py <command> --config <file> [--backend fixture|real] [--manifest <file>]"}
            code = 0
        else:
            args = parser_for(skill).parse_args(argv)
            output = execute(skill, args)
            code = output.get("exit_code", 0)
            output = {"ok": code == 0, **output, "exit_code": code}
    except FlowError as error:
        output, code = error.as_dict(), error.code
    except (OSError, ValueError, KeyError, TypeError, RuntimeError):
        output, code = {"ok": False, "exit_code": 5, "error": "local_processing_failed"}, 5
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    return code
