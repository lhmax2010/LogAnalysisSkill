"""One JSON object on stdout, immutable attempt artifacts, and journaled outcomes."""
import argparse
import json
import sys
from pathlib import Path

from .read_ops import make_reader, register_read
from .commands import COMMANDS, Category, command_context
from .config import load_config
from .errors import FlowError, unsupported
from .export import export_file
from .archive_precheck import check_file as repository_precheck
from .locks import OperationLock
from .state import EventStore


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise FlowError(2, "invalid_arguments")


PUBLIC = {"watch": ["observe"], "fetch": ["packages", "inputs", "groups", "logs", "base-list"],
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
    parser.add_argument("--build-id")
    parser.add_argument("--expected-rows")
    parser.add_argument("--arch")
    parser.add_argument("--expected-event", type=int)
    parser.add_argument("--source")
    parser.add_argument("--type", dest="material_type")
    parser.add_argument("--name")
    parser.add_argument("--files", nargs="*")
    return parser



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
                requested = Path(source).expanduser()
                requested = requested if requested.is_absolute() else config.source_dir / requested
                checks = repository_precheck(requested, config)
                checked.append({"path": str(path), **checks})
            return {"files": checked, "exit_code": 0 if all(c["allowed"] for c in checked) else 4}
        if args.command == "export":
            if not all((args.source, args.material_type, args.name)):
                raise FlowError(2, "export_arguments_required")
            with OperationLock(config.data_root, "round", "export"):
                return export_file(config, args.source, args.material_type, args.name)
        with EventStore(config.data_root) as store:
            return {"last_event_id": store.head(), "events": len(store.events())}
    reader = make_reader(config, args.backend, build_id=args.build_id, manifest=args.manifest, expected_rows=args.expected_rows)
    result, _ = register_read(config, reader, skill, args.command, arch=args.arch,
                              expected_event=args.expected_event)
    return result

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
