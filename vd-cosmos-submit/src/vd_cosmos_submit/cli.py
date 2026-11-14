"""Browser-free command entry point. Human commands are documented only in the manual."""
from datetime import datetime
import json
import signal
import threading
import time
import sys
from zoneinfo import ZoneInfo

from vd_cosmos_core.cli import Parser
from vd_cosmos_core.config import load_config
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.bm_reader import Reader, FixtureTransport
from vd_cosmos_core.submit_doctor import doctor
from vd_cosmos_core.submit_model import read, resolve
from vd_cosmos_core import submit_claim, submit_terminal, submit_watch
from vd_cosmos_core.files import atomic_write, json_bytes
from vd_cosmos_core.export import check_content

COMMANDS = ['lookup', 'doctor', 'watch', 'attest', 'bind', 'rebind', 'abandon', 'resolve']


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        if '--help' in argv:
            result = {'commands': COMMANDS, 'exit_code': 0, 'checkpoint': 'B1; browser paths unavailable'}
        else:
            parser = Parser(add_help=False)
            parser.add_argument('command', choices=COMMANDS)
            parser.add_argument('--config', required=True)
            parser.add_argument('--backend', choices=['real', 'fixture'], default='fixture')
            parser.add_argument('--fixture')
            for name in ('hub-id', 'build-id', 'request', 'session', 'reason', 'checked-at', 'since'):
                parser.add_argument('--' + name)
            for name in ('via-hub', 'online', 'read-only', 'manual-submit', 'manual-rerun', 'not-submitted', 'no-manual-submit'):
                parser.add_argument('--' + name, action='store_true')
            parser.add_argument('--max-scans', type=int)
            args = parser.parse_args(argv)
            if args.via_hub: raise FlowError(6, 'requires_B2_browser')
            context = None
            if args.command in {'attest', 'bind', 'rebind', 'abandon', 'resolve'}:
                context = submit_terminal.human_context('round.abandon' if args.command == 'abandon' else args.command)
            config = load_config(args.config)
            def factory(cache=None):
                transport = None
                if args.backend == 'fixture':
                    if not args.fixture: raise FlowError(2, 'fixture_required')
                    transport = FixtureTransport(config.source(args.fixture))
                return Reader(config, transport=transport, cache=cache)
            reader = None
            try:
                if args.command == 'doctor':
                    reader = factory() if args.online else None
                    result = doctor(config, reader=reader)
                elif args.command == 'lookup':
                    if not args.hub_id or not args.hub_id.isdecimal(): raise FlowError(2, 'hub_id_required')
                    reader = factory(); since = None
                    if args.since:
                        try: since = datetime.strptime(args.since, '%Y-%m-%d').replace(tzinfo=ZoneInfo(config.raw['cosmos']['bm_display_tz'])).timestamp()
                        except ValueError: raise FlowError(2, 'invalid_since_date') from None
                    result = reader.lookup(args.hub_id, since=since)
                elif args.command in {'attest', 'bind', 'rebind'}:
                    if not args.request or not args.build_id or not args.reason: raise FlowError(2, 'decision_arguments_required')
                    reader = factory()
                    if args.command == 'rebind':
                        if submit_terminal.ask('Rebind to build ' + args.build_id + ' (type build number): ') != args.build_id:
                            raise FlowError(3, 'confirmation_required')
                        result = submit_claim.rebind(config, args.request, args.build_id, context, args.reason, reader)
                    else:
                        prepared = submit_claim.prepare_attest(config, args.request, args.build_id, reader)
                        words = submit_terminal.confirm(prepared)
                        result = submit_claim.attest(config, args.request, prepared, context, words, args.reason, reader)
                elif args.command == 'abandon':
                    result = submit_claim.abandon(config, args.request, context, args.reason or '')
                elif args.command == 'resolve':
                    flags = [mode for mode in ('manual-submit', 'manual-rerun', 'not-submitted', 'no-manual-submit') if getattr(args, mode.replace('-', '_'))]
                    if len(flags) > 1: raise FlowError(2, 'resolve_modes_exclusive')
                    mode = flags[0] if flags else 'build-id'
                    words = []
                    if mode in {'not-submitted', 'no-manual-submit'}:
                        # Show unresolved reruns through the model before asking for the extra word.
                        try:
                            result = resolve(config, context, request_id=args.request, mode=mode, reason=args.reason or '', checked_at=args.checked_at)
                        except FlowError as error:
                            if error.reason != 'rerun_records_confirmation_required': raise
                            words = submit_terminal.ask(json.dumps(error.details, ensure_ascii=False) + '\n输入 rerun-records-unrelated: ').split()
                        else:
                            mode = None
                    if mode:
                        result = resolve(config, context, request_id=args.request, session=args.session,
                            hub_id=args.hub_id if mode == 'manual-rerun' else args.build_id,
                            mode=mode, reason=args.reason or '', checked_at=args.checked_at, words=words)
                else:
                    if not args.request or args.max_scans is not None and args.max_scans < 1: raise FlowError(2, 'watch_arguments_required')
                    result = watch(config, args, factory)
            finally:
                if reader: reader.close()
            if not check_content(json_bytes(result), config)['allowed']: raise FlowError(4, 'output_credential_blocked')
            # Human-readable and full evidence go to a file; stdout remains one JSON object.
            output = 'submit/results/' + str(time.time_ns()) + '.json'
            atomic_write(config.data_root, output, json_bytes(result))
            result = dict(result, artifact=str(config.output(output)))
    except FlowError as error:
        result = error.as_dict()
    except (OSError, ValueError, TypeError, KeyError):
        result = {'exit_code': 5, 'error': 'submit_read_processing_failed'}
    code = result.get('exit_code', 0)
    print(json.dumps({'ok': code == 0, **result}, ensure_ascii=False))
    return code


def watch(config, args, factory):
    stop = threading.Event(); errors = []; result = []
    old_signals = {}
    for sig in (signal.SIGINT, signal.SIGTERM):
        old_signals[sig] = signal.signal(sig, lambda *_: stop.set())
    interactive = not args.read_only and submit_terminal.available()
    if interactive: submit_terminal.ancestors_allowed()
    def worker():
        try: result.append(submit_watch.run(config, args.request, factory, stop=stop, max_scans=args.max_scans))
        except FlowError as error: errors.append(error)
        finally: stop.set()
    thread = threading.Thread(target=worker, daemon=True); thread.start()
    shown = None
    try:
        while not stop.wait(.1):
            if not interactive: continue
            r = read(config, args.request)
            if r.get('binding') or not r.get('candidates'): continue
            ids = tuple(sorted(d['build_id'] for d in r['candidates']))
            if len(ids) != 1: continue
            basis_key = json.dumps(submit_claim.fingerprint(r, r['scan'], r['candidates'][0]), sort_keys=True)
            if shown == basis_key: continue
            retry_confirmation = False
            reader = factory()
            try:
                prepared = submit_claim.confirmation(config, r, r['scan'], r['candidates'][0])
                context = submit_terminal.human_context('attest')
                words = submit_terminal.confirm(prepared)
                submit_claim.attest(config, args.request, prepared, context, words, 'watch 候选确认', reader)
            except FlowError as error:
                if error.code not in (3, 6): raise
                sys.stderr.write(error.reason + '\n')
                retry_confirmation = error.reason in {'confirmation_basis_changed', 'request_version_changed'}
            finally: reader.close()
            shown = None if retry_confirmation else basis_key
        thread.join()
        if errors: raise errors[0]
        return result[-1] if result else read(config, args.request)
    finally:
        stop.set(); thread.join(timeout=5)
        for sig, handler in old_signals.items(): signal.signal(sig, handler)
