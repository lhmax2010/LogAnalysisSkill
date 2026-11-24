import json
import sys
from vd_cosmos_core.cli import Parser
from vd_cosmos_core.config import load_config
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.diagnosis import import_family
from vd_cosmos_core.submit_terminal import ancestors_allowed
from vd_cosmos_core.read_ops import make_reader
from vd_cosmos_core.analysis_result import accept_result
from vd_cosmos_core.task_package import prepare
from vd_cosmos_core.export import check_content
from vd_cosmos_core.files import json_bytes
from .api import create_snapshot
from .real_inputs import prepare_real_inputs

COMMANDS = ['snapshot', 'prepare', 'accept', 'import-diagnosis-families', 'prepare-inputs']


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    try:
        if '--help' in argv:
            result = {'commands': COMMANDS, 'exit_code': 0}
        else:
            parser = Parser(add_help=False)
            parser.add_argument('command', choices=COMMANDS)
            parser.add_argument('--config', required=True)
            parser.add_argument('--backend', choices=['fixture', 'real'], default=None)
            parser.add_argument('--build-id', '--build')
            parser.add_argument('--hub-id')
            parser.add_argument('--task')
            parser.add_argument('--attempt', type=int)
            parser.add_argument('--round')
            parser.add_argument('--snapshot')
            parser.add_argument('--family-file')
            parser.add_argument('--primary-repodata')
            parser.add_argument('--new-attempt', action='store_true')
            parser.add_argument('--manifest')
            parser.add_argument('--package')
            parser.add_argument('--arch')
            parser.add_argument('--log')
            parser.add_argument('--expected-event', type=int)
            parser.add_argument('--tickets-override')
            args = parser.parse_args(argv)
            config = load_config(args.config)
            if args.command == 'prepare-inputs':
                if not args.build_id or args.backend == 'fixture' or args.manifest or args.tickets_override:
                    raise FlowError(2, 'prepare_inputs_real_build_required')
                result = prepare_real_inputs(config, args.build_id, args.hub_id)
            elif args.command == 'import-diagnosis-families':
                ancestors_allowed()
                if not args.round or not args.family_file:
                    raise FlowError(2, 'diagnosis_import_identity_required')
                result = {'artifact': import_family(config, args.round, args.family_file, args.primary_repodata)}
            elif args.command == 'accept':
                if not args.round or not args.task or args.attempt is None:
                    raise FlowError(2, 'analysis_result_identity_required')
                result = accept_result(config, args.round, args.task, args.attempt)
            elif not args.build_id or not args.log:
                raise FlowError(2, 'analysis_build_and_log_required')
            elif args.command == 'prepare':
                if not args.round:
                    raise FlowError(2, 'analysis_round_required')
                task = prepare(config, args.round, args.build_id, args.log,
                               snapshot_path=args.snapshot, force_new=args.new_attempt, primary=args.primary_repodata)
                result = {field: task[field] for field in ('task_id', 'attempt', 'directory', 'task_input_digest')}
            else:
                if not args.package or not args.arch:
                    raise FlowError(2, 'package_and_architecture_required')
                reader = make_reader(config, args.backend or 'fixture', build_id=args.build_id, manifest=args.manifest)
                if reader.build_ref.run_id != args.build_id:
                    raise FlowError(6, 'build_identity_mismatch')
                result = create_snapshot(config, reader, args.package, args.arch, args.log, expected_event=args.expected_event, tickets_override=args.tickets_override)
    except FlowError as error:
        result = error.as_dict()
        if 'config' in locals() and args.command == 'prepare-inputs':
            try:
                allowed = check_content(json_bytes(result), config)['allowed']
            except FlowError:
                allowed = False
            if not allowed:
                result = FlowError(4, 'prepare_inputs_summary_credential_blocked').as_dict()
    except (OSError, ValueError, TypeError, KeyError):
        result = {'exit_code': 5, 'error': 'snapshot_processing_failed'}
    code = result.get('exit_code', 0)
    print(json.dumps({'ok': code == 0, **result}, ensure_ascii=False))
    return code
