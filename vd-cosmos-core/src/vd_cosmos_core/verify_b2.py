"""A-E acceptance; shared B1 reconciliation, no imports from skill packages."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace
import uuid

from .config import load_config
from .errors import FlowError
from .export import export_file
from .files import atomic_write, digest, json_bytes, load_json
from .http_reader import HTTPReportReader
from .locks import OperationLock
from .read_ops import fetch_logs
from .state import EventStore
from .verify import REAL_COUNTS, read_baselines, evaluate, run as verify_saved


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['verified-commit', 'config', 'build-id', 'saved-dir', 'rows', 'links']:
        p.add_argument('--' + name, required=True)
    p.add_argument('--live-build-id')
    p.add_argument('--mode', choices=['real', 'fixture'], default='real')
    p.add_argument('--fixture-counts')
    return p


def run(args, config, directory, result):
    saved = config.source(args.saved_dir)
    row_path, link_path = config.source(args.rows), config.source(args.links)
    rows, links = read_baselines(row_path.read_bytes(), link_path.read_bytes())
    counts = REAL_COUNTS
    if args.mode == 'fixture':
        if not args.fixture_counts:
            raise FlowError(2, 'fixture_counts_required')
        counts = load_json(args.fixture_counts)
    elif args.fixture_counts:
        raise FlowError(2, 'real_counts_cannot_be_overridden')
    reader = HTTPReportReader(config, args.build_id, row_path)
    key = digest(json_bytes(reader.build_ref.to_dict()))
    with OperationLock(config.data_root, 'round', key):
        first = reader.observe(reader.build_ref)
        atomic_write(config.data_root, directory / 'A-first.json', json_bytes(first))
    time.sleep(config.raw['poll']['interval_s'])
    reader = HTTPReportReader(config, args.build_id, row_path)
    with OperationLock(config.data_root, 'round', key):
        second = reader.observe(reader.build_ref)
        target = config.output(directory / 'A');target.mkdir()
        part = {'stability_simulated': False}
        if second['observation_failed']:
            raise FlowError(5, 'A_observation_failed')
        evaluate(reader, rows, links, counts, config, target, part)
        part['saved_page_comparison'] = {}
        for arch, report in second['reports'].items():
            saved_sha = digest((saved / ('report_' + arch + '.html')).read_bytes())
            actual_sha = report['evidence']['sha256']
            part['saved_page_comparison'][arch] = {'saved_sha256': saved_sha, 'http_sha256': actual_sha,
                                                  'result': '相同' if saved_sha == actual_sha else '不同'}
        result['A'] = part
        logs = fetch_logs(reader, second)['logs']
        actual_counts = {arch: sum(log['key']['arch'] == arch for log in logs) for arch in counts}
        expected_counts = {arch: c['build_error'] + c['export_error'] for arch, c in counts.items()}
        result['B'] = {'verdict': 'PASS' if actual_counts == expected_counts else 'FAIL',
                       'counts': actual_counts, 'expected_counts': expected_counts, 'logs': logs}
    target = config.output(directory / 'C');target.mkdir()
    saved_args = SimpleNamespace(mode=args.mode, fixture_counts=args.fixture_counts, run_id=args.build_id,
        arm_report=str(saved / 'report_armv7l.html'), x86_report=str(saved / 'report_x86_64.html'),
        detail_page=str(saved / 'probe_3bed7e8c.html'), rows=str(row_path), links=str(link_path))
    result['C'] = {}
    verify_saved(saved_args, config, target, result['C'])
    if args.live_build_id:
        live = HTTPReportReader(config, args.live_build_id)
        with OperationLock(config.data_root, 'round', digest(json_bytes(live.build_ref.to_dict()))):
            observed = live.observe(live.build_ref)
        result['D'] = {'evaluated_for_pass': False, 'exit_code': observed['exit_code'],
                       'reports': {a: {'http_status': r.get('http_status'), 'report_state': r.get('report_state')}
                                   for a, r in observed['reports'].items()},
                       'execution_state': observed['execution_state'], 'execution_evidence': observed['execution_evidence']}
    else:
        result['D'] = {'skipped': True, 'evaluated_for_pass': False}
    script = Path(__file__).resolve().parents[3] / 'vd-cosmos-workflow/scripts/run.py'
    process = subprocess.run([sys.executable, '-B', str(script), 'loop', '--config', str(Path(args.config).resolve()),
        '--backend', 'real', '--build-id', args.build_id, '--expected-rows', str(row_path), '--max-ticks', '4'],
        cwd=config.data_root, capture_output=True, text=True)
    loop_result = json.loads(process.stdout)
    atomic_write(config.data_root, directory / 'E-loop.json', json_bytes(loop_result))
    with EventStore(config.data_root) as store:
        events = [e for e in store.events() if e['payload'].get('build') == key]
    todos = [e['payload']['todo'] for e in events if e['kind'] == 'inbox_opened' and e['payload']['todo'].get('reason') == 'analysis_pending']
    log_events = [e for e in events if e['kind'] == 'workflow_result' and e['payload'].get('step') == 'logs' and not e['payload']['exit_code']]
    recorded = load_json(log_events[-1]['payload']['artifact']['path'])['logs'] if log_events else []
    log_map = lambda entries: {json.dumps(e['key'], sort_keys=True): e['sha256'] for e in entries}
    same = log_map(recorded) == log_map(logs)
    no_download = bool(recorded) and all(log.get('skipped') for log in recorded)
    expected_failed = sum(expected_counts.values())
    passed = (process.returncode == 0 and loop_result.get('phase') == '结果已拉取' and same and no_download
              and len(todos) == 1 and todos[0]['count'] == expected_failed)
    result['E'] = {'verdict': 'PASS' if passed else 'FAIL', 'phase': loop_result.get('phase'),
                   'ticks': loop_result.get('ticks'), 'log_sha256_matches_B': same,
                   'no_repeated_downloads': no_download, 'analysis_todos': todos}
    result['verdict'] = 'PASS' if all(result[part]['verdict'] == 'PASS' for part in ['A', 'B', 'C', 'E']) else 'FAIL'
    result['exit_code'] = 0 if result['verdict'] == 'PASS' else 6


def main(argv=None):
    args = parser().parse_args(argv)
    result = {'schema_version': 1, 'git_commit': args.verified_commit, 'mode': args.mode, 'verdict': 'FAIL',
              'note': '本地 HTTP 夹具模拟' if args.mode == 'fixture' else '构建机真实读取验收'}
    try:
        config = load_config(args.config)
        identifier = 'b2-real-' + uuid.uuid4().hex
        directory = config.output('verification/' + identifier);directory.mkdir(parents=True)
        try:
            run(args, config, directory, result)
        except FlowError as error:
            result.update(exit_code=error.code, error=error.reason)
        except (OSError, ValueError, KeyError, TypeError):
            result.update(exit_code=5, error='acceptance_processing_failed')
        artifact = atomic_write(config.data_root, directory / 'result.json', json_bytes(result))
        bundle = export_file(config, artifact['path'], 'verification', identifier)
        output = {'verdict': result['verdict'], 'exit_code': result['exit_code'], 'result_file': artifact,
                  'export': bundle, 'two_block_target_met': bundle['total_blocks'] <= 2}
    except FlowError as error:
        output = error.as_dict()
    print(json.dumps(output, ensure_ascii=False))
    return output['exit_code']
