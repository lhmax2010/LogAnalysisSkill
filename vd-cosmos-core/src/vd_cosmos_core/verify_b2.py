"""Isolated A-F acceptance, with provenance and strict per-stage verdicts."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import ipaddress
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from types import SimpleNamespace
from urllib.parse import urlsplit
import uuid
from .config import load_config
from .errors import FlowError
from .export import export_file
from .files import atomic_write, digest, json_bytes, load_json
from .http_reader import HTTPReportReader, sanitized
from .read_ops import fetch_logs
from .state import EventStore
from .versions import build_key
from .verify import REAL_COUNTS, read_baselines, evaluate, run as verify_saved

ROOTS = ['vd-cosmos-core', 'vd-cosmos-watch', 'vd-cosmos-fetch', 'vd-cosmos-workflow']


def utc():
    return datetime.now(timezone.utc).isoformat()


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    for name in ['verified-commit', 'config', 'build-id', 'saved-dir', 'rows', 'links']:
        result.add_argument('--' + name, required=True)
    result.add_argument('--live-build-id')
    result.add_argument('--mode', choices=['real', 'fixture'], default='real')
    result.add_argument('--fixture-counts')
    return result


def endpoint(url):
    p = urlsplit(url)
    return {'scheme': p.scheme, 'host': p.hostname, 'port': p.port or (443 if p.scheme == 'https' else 80), 'path': p.path}


def check_source(args, config, repo):
    head = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    if not re.fullmatch('[0-9a-fA-F]{40}', args.verified_commit) or head != args.verified_commit:
        raise FlowError(6, 'expected_commit_mismatch')
    dirty = subprocess.check_output(['git', '-C', str(repo), 'status', '--porcelain=v1', '--untracked-files=all', '--', *ROOTS])
    if dirty:
        raise FlowError(6, 'owned_source_tree_dirty')
    cosmos = config.raw['cosmos']
    urls = [cosmos['report_root'], cosmos['status_source']['url_template']]
    if args.mode == 'real':
        for url in urls:
            host = urlsplit(url).hostname.lower().rstrip('.')
            try:
                invalid = ipaddress.ip_address(host).is_loopback
            except ValueError:
                invalid = False
            if invalid or host == 'localhost' or host.endswith('.localhost') or host.endswith('.invalid'):
                raise FlowError(2, 'real_backend_requires_non_loopback_instance')
    tree = subprocess.check_output(['git', '-C', str(repo), 'ls-tree', '-rz', 'HEAD', '--', *ROOTS])
    return {'commit': head, 'source_tree_sha256': digest(tree), 'script_sha256': digest((repo / 'vd-cosmos-core/scripts/verify_b2_real.sh').read_bytes()),
            'instances': [endpoint(url) for url in urls], 'backend': 'http-fixture' if args.mode == 'fixture' else 'cosmos-http'}


def verdict(passed, **values):
    return {**values, 'verdict': 'PASS' if passed else 'FAIL', 'exit_code': 0 if passed else 6}


def html_log(data):
    text = data[:65536].decode('utf-8', errors='replace')
    return bool(re.search(r'<(?:!doctype\s+html|html|head|body|form|input)\b', text, re.I))


def run(args, config, directory, result, repo, config_path):
    saved = Path(args.saved_dir)
    rows, links = read_baselines(Path(args.rows).read_bytes(), Path(args.links).read_bytes())
    counts = REAL_COUNTS
    if args.mode == 'fixture':
        if not args.fixture_counts:
            raise FlowError(2, 'fixture_counts_required')
        counts = load_json(args.fixture_counts)
    elif args.fixture_counts:
        raise FlowError(2, 'real_counts_cannot_be_overridden')
    reader = HTTPReportReader(config, args.build_id, args.rows)
    first = reader.observe(reader.build_ref)
    atomic_write(config.data_root, directory / 'A-first.json', json_bytes(first))
    time.sleep(config.raw['poll']['interval_s'])
    reader = HTTPReportReader(config, args.build_id, args.rows)
    second = reader.observe(reader.build_ref)
    target = config.output(directory / 'A');target.mkdir()
    part = {'stability_simulated': False}
    try:
        if second['observation_failed']:
            raise FlowError(5, 'A_observation_failed')
        evaluate(reader, rows, links, counts, config, target, part)
        part['saved_page_comparison'] = {}
        for arch, report in second['reports'].items():
            saved_sha = digest((saved / ('report_' + arch + '.html')).read_bytes())
            actual_sha = report.get('evidence', {}).get('sha256')
            part['saved_page_comparison'][arch] = {'saved_sha256': saved_sha, 'http_sha256': actual_sha,
                                                  'result': '相同' if saved_sha == actual_sha else '不同'}
        if any(r['result'] != '相同' for r in part['saved_page_comparison'].values()):
            part.update(verdict(False))
    except (FlowError, KeyError) as error:
        part.update(verdict(False), error=error.reason if isinstance(error, FlowError) else 'A_missing_report')
    result['A'] = part
    logs = []
    try:
        data = fetch_logs(reader, second)
        if data.get('exit_code'):
            raise FlowError(data['exit_code'], 'B_report_unavailable')
        logs = data['logs']
        actual_counts = {arch: sum(log['key']['arch'] == arch for log in logs) for arch in counts}
        expected_counts = {arch: c['build_error'] + c['export_error'] for arch, c in counts.items()}
        checks = []
        for log in logs:
            content = Path(log['path']).read_bytes()
            checks.append(not log.get('skipped') and log.get('transfer_complete') and not log['truncated']
                          and not html_log(content) and digest(content) == log['sha256'])
        result['B'] = verdict(all(checks) and actual_counts == expected_counts,
                              counts=actual_counts, expected_counts=expected_counts, logs=logs, log_checks=checks)
    except FlowError as error:
        result['B'] = verdict(False, error=error.reason)
    target = config.output(directory / 'C');target.mkdir()
    saved_args = SimpleNamespace(mode=args.mode, fixture_counts=args.fixture_counts, run_id=args.build_id,
        arm_report=str(saved / 'report_armv7l.html'), x86_report=str(saved / 'report_x86_64.html'),
        detail_page=str(saved / 'probe_3bed7e8c.html'), rows=args.rows, links=args.links)
    result['C'] = {}
    try:
        verify_saved(saved_args, config, target, result['C'])
    except FlowError as error:
        result['C'] = verdict(False, error=error.reason)
    if args.live_build_id:
        live = HTTPReportReader(config, args.live_build_id)
        observed = live.observe(live.build_ref)
        result['D'] = {'evaluated_for_pass': False, 'observation_exit_code': observed['exit_code'],
                       'reports': {a: {'http_status': r.get('http_status'), 'report_state': r.get('report_state')}
                                   for a, r in observed['reports'].items()},
                       'execution_state': observed['execution_state'], 'execution_evidence': observed['execution_evidence']}
    else:
        result['D'] = {'skipped': True, 'evaluated_for_pass': False}
    # The root was created for this acceptance run. Nothing from an earlier run
    # is visible. B and E intentionally share this run's freshly downloaded logs.
    script = repo / 'vd-cosmos-workflow/scripts/run.py'
    command = [sys.executable, '-B', str(script), 'loop', '--config', str(config_path), '--backend', 'real',
               '--build-id', args.build_id, '--expected-rows', args.rows]
    if result['A']['verdict'] == 'PASS' and result['B']['verdict'] == 'PASS':
        try:
            budget = 3 * (len(counts) + 1) * config.raw['fetch']['deadline_s'] + 3 * config.raw['poll']['interval_s']
            process = subprocess.run(command, cwd=config.data_root, capture_output=True, text=True, timeout=budget)
            loop_result = json.loads(process.stdout)
        except subprocess.TimeoutExpired:
            process = SimpleNamespace(returncode=5)
            loop_result = {'exit_code': 5, 'error': 'acceptance_loop_deadline'}
    else:
        process = SimpleNamespace(returncode=6)
        loop_result = {'exit_code': 6, 'error': 'acceptance_loop_prerequisite_failed'}
    atomic_write(config.data_root, directory / 'E-loop.json', json_bytes(loop_result))
    with EventStore(config.data_root) as store:
        events = store.events(build_key(reader))
    todos = [e['payload']['todo'] for e in events if e['kind'] == 'inbox_opened' and e['payload']['todo'].get('reason') == 'analysis_pending']
    actions = {e['payload'].get('step') for e in events if e['kind'] == 'workflow_result' and not e['payload']['exit_code']}
    log_events = [e for e in events if e['kind'] == 'workflow_result' and e['payload'].get('step') == 'logs' and not e['payload']['exit_code']]
    recorded = load_json(log_events[-1]['payload']['artifact']['path'])['logs'] if log_events else []
    log_map = lambda entries: {json.dumps(e['key'], sort_keys=True): e['sha256'] for e in entries}
    same = bool(logs) and log_map(recorded) == log_map(logs)
    no_download = bool(recorded) and all(log.get('skipped') for log in recorded)
    failed_count = sum(c['build_error'] + c['export_error'] for c in counts.values())
    result['E'] = verdict(process.returncode == 0 and loop_result.get('phase') == '结果已拉取' and same and no_download
        and {'observe', 'logs', 'notify'} <= actions and len(todos) == 1 and todos[0]['count'] == failed_count,
        phase=loop_result.get('phase'), actions=sorted(actions), log_sha256_matches_B=same,
        no_repeated_downloads=no_download, analysis_todos=todos, command=command)
    try:
        index, fingerprint = reader.index()
        index_result = {'http_status': index['status'], 'fingerprint': fingerprint, 'response': index['response']}
    except FlowError as error:
        index_result = {'error': error.reason, 'response': error.details.get('response')}
    result['F'] = sanitized({'evaluated_for_pass': False, 'index': index_result,
        'detail_identity_match': second['execution_evidence'].get('identity_match', False),
        'redirect_responses': [r for r in reader.transport.requests if r.get('http_status') and 300 <= r['http_status'] < 400]}, config)
    result.update(verdict(all(result[part]['verdict'] == 'PASS' for part in ['A', 'B', 'C', 'E'])))


def main(argv=None):
    args = parser().parse_args(argv)
    repo = Path(__file__).resolve().parents[3]
    started = utc()
    try:
        head = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
        if not re.fullmatch('[0-9a-fA-F]{40}', args.verified_commit) or args.verified_commit != head:
            raise FlowError(6, 'expected_commit_mismatch')
        original = load_config(args.config)
        provenance = check_source(args, original, repo)
        for name in ['saved_dir', 'rows', 'links']:
            setattr(args, name, str(original.source(getattr(args, name))))
        if args.fixture_counts:
            args.fixture_counts = str(original.source(args.fixture_counts))
        run_id = 'b21-' + uuid.uuid4().hex
        outer = original.output('verification/' + run_id)
        raw = deepcopy(original.raw)
        raw['data_root'] = str(outer / 'data')
        raw['p4']['config_file'] = str(original.output(raw['p4']['config_file']).relative_to(original.data_root))
        for section, key in [('network', 'ca_file'), ('prepush', 'words_file')]:
            if raw.get(section, {}).get(key):
                raw[section][key] = str(original.source(raw[section][key]))
        config_path = outer / 'config.json'
        atomic_write(original.data_root, config_path, json_bytes(raw))
        config = load_config(config_path)
        directory = config.output('verification/results');directory.mkdir(parents=True)
        provenance.update(run_id=run_id, started_at=started, original_config_sha256=digest(Path(args.config).read_bytes()),
            command=[sys.executable, *sys.argv] if argv is None else list(argv),
            baselines={name: digest(Path(getattr(args, name)).read_bytes()) for name in ['rows', 'links']},
            saved_pages={p.name: digest(p.read_bytes()) for p in Path(args.saved_dir).iterdir() if p.name in {'report_armv7l.html','report_x86_64.html','probe_3bed7e8c.html'}})
        result = {'schema_version': 2, 'provenance': provenance, 'mode': args.mode,
                  'note': '本地 HTTP 夹具模拟，非真实验收' if args.mode == 'fixture' else '构建机真实读取验收', **verdict(False)}
        try:
            run(args, config, directory, result, repo, config_path)
        except FlowError as error:
            result.update(verdict(False), error=error.reason, exit_code=error.code)
        except (OSError, ValueError, KeyError, TypeError):
            result.update(verdict(False), error='acceptance_processing_failed', exit_code=5)
        provenance['finished_at'] = utc()
        provenance['exit_code'] = result['exit_code']
        provenance['artifacts'] = [{'path': str(p.relative_to(config.data_root)),
                                   'sha256': digest(p.read_bytes()), 'size': p.stat().st_size}
                                  for p in sorted(directory.rglob('*')) if p.is_file()]
        artifact = atomic_write(config.data_root, directory / 'result.json', json_bytes(result))
        bundle = export_file(config, artifact['path'], 'verification', run_id)
        output = {'verdict': result['verdict'], 'exit_code': result['exit_code'], 'result_file': artifact,
                  'export': bundle, 'two_block_target_met': bundle['total_blocks'] <= 2}
    except FlowError as error:
        output = error.as_dict()
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        output = {'exit_code': 5, 'error': 'acceptance_preflight_failed'}
    print(json.dumps(output, ensure_ascii=False))
    return output['exit_code']
