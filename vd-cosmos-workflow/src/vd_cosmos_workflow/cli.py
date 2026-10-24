import argparse
import json
import sys
from vd_cosmos_core.config import load_config
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.read_ops import make_reader
from .api import tick, loop, status, inbox


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise FlowError(2, 'invalid_arguments')


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    try:
        if '--help' in argv or '-h' in argv:
            result = {'commands': ['tick', 'loop', 'status', 'inbox'], 'exit_code': 0}
        else:
            parser = Parser(add_help=False)
            parser.add_argument('command', choices=['tick', 'loop', 'status', 'inbox'])
            parser.add_argument('--config', required=True)
            parser.add_argument('--backend', choices=['fixture', 'real'], default='real')
            parser.add_argument('--build-id')
            parser.add_argument('--manifest')
            parser.add_argument('--expected-rows')
            parser.add_argument('--expected-event', type=int)
            parser.add_argument('--max-ticks', type=int)
            args = parser.parse_args(argv)
            config = load_config(args.config)
            factory = lambda: make_reader(config, args.backend, build_id=args.build_id,
                                         manifest=args.manifest, expected_rows=args.expected_rows)
            if args.command == 'tick':
                result = tick(config, factory, expected_event=args.expected_event)
            elif args.command == 'loop':
                result = loop(config, factory, max_ticks=args.max_ticks)
            elif args.command == 'inbox':
                result = inbox(config)
            else:
                result = status(config, factory() if args.build_id or args.manifest else None)
    except FlowError as error:
        result = error.as_dict()
    except (OSError, ValueError, TypeError, KeyError):
        result = {'exit_code': 5, 'error': 'workflow_processing_failed'}
    code = result.get('exit_code', 0)
    print(json.dumps({'ok': code == 0, **result, 'exit_code': code}, ensure_ascii=False))
    return code
