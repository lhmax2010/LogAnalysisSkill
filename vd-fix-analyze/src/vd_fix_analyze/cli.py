import json
import sys
from vd_cosmos_core.cli import Parser
from vd_cosmos_core.config import load_config
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.read_ops import make_reader
from .api import create_snapshot


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    try:
        if '--help' in argv:
            result = {'commands': ['snapshot'], 'exit_code': 0}
        else:
            parser = Parser(add_help=False)
            parser.add_argument('command', choices=['snapshot'])
            parser.add_argument('--config', required=True)
            parser.add_argument('--backend', choices=['fixture', 'real'], default='fixture')
            parser.add_argument('--build-id', required=True)
            parser.add_argument('--manifest')
            parser.add_argument('--package', required=True)
            parser.add_argument('--arch', required=True)
            parser.add_argument('--log', required=True)
            parser.add_argument('--expected-event', type=int)
            parser.add_argument('--tickets-override')
            args = parser.parse_args(argv)
            config = load_config(args.config)
            reader = make_reader(config, args.backend, build_id=args.build_id, manifest=args.manifest)
            if reader.build_ref.run_id != args.build_id:
                raise FlowError(6, 'build_identity_mismatch')
            result = create_snapshot(config, reader, args.package, args.arch, args.log, expected_event=args.expected_event, tickets_override=args.tickets_override)
    except FlowError as error:
        result = error.as_dict()
    except (OSError, ValueError, TypeError, KeyError):
        result = {'exit_code': 5, 'error': 'snapshot_processing_failed'}
    code = result.get('exit_code', 0)
    print(json.dumps({'ok': code == 0, **result}, ensure_ascii=False))
    return code
