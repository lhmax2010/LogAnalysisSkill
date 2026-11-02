import json
import sys
from vd_cosmos_core.cli import Parser
from vd_cosmos_core.commands import command_context
from vd_cosmos_core.config import load_config
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.read_ops import make_reader
from .api import decide


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:2] == ['inbox', 'done']:
        argv[:2] = ['inbox.done']
    try:
        if '--help' in argv:
            result = {'commands': ['confirm-terminal', 'confirm-input', 'bind-base-list', 'inbox done'], 'exit_code': 0}
        else:
            parser = Parser(add_help=False)
            parser.add_argument('command', choices=['confirm-terminal', 'confirm-input', 'bind-base-list', 'inbox.done'])
            parser.add_argument('--config', required=True)
            parser.add_argument('--backend', choices=['fixture', 'real'], default='fixture')
            parser.add_argument('--round', required=True)
            parser.add_argument('--manifest')
            parser.add_argument('--reason', required=True)
            parser.add_argument('--expected-event', type=int)
            parser.add_argument('--report-digests', type=json.loads)
            parser.add_argument('--override-running', action='store_true')
            parser.add_argument('--withdraw', action='store_true')
            parser.add_argument('--package', type=json.loads)
            parser.add_argument('--shelve-digest')
            parser.add_argument('--file')
            parser.add_argument('--shelve-file')
            parser.add_argument('--todo-key')
            args = parser.parse_args(argv)
            context = command_context(args.command)
            config = load_config(args.config)
            reader = make_reader(config, args.backend, build_id=args.round, manifest=args.manifest)
            if reader.build_ref.run_id != args.round:
                raise FlowError(6, 'build_identity_mismatch')
            result = decide(config, reader, args.command, context=context, expected_event=args.expected_event,
                reason=args.reason, report_bindings=args.report_digests, override_running=args.override_running,
                withdraw=args.withdraw, package=args.package, shelve_digest=args.shelve_digest,
                base_file=args.file, shelve_file=args.shelve_file, todo_key=args.todo_key)
    except FlowError as error:
        result = error.as_dict()
    except (OSError, ValueError, TypeError, KeyError):
        result = {'exit_code': 5, 'error': 'register_processing_failed'}
    code = result.get('exit_code', 0)
    print(json.dumps({'ok': code == 0, **result}, ensure_ascii=False))
    return code
