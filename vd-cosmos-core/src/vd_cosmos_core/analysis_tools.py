"""Run the existing analyzer and read-only context producer without passing ambient secrets."""
import os
from pathlib import Path
import re
import selectors
import signal
import subprocess
import sys
import tempfile
import time

from .errors import FlowError
from .export import check_content
from .files import load_json

ROOT = Path(__file__).resolve().parents[3]
DIAGNOSTIC = re.compile(
    rb'(?:^|[\r\n])([^\r\n]*?:\d+(?::\d+)?:\s*(?:fatal error|error|warning|note):[^\r\n]*)'
)
COMMAND = re.compile(rb'(?:^|\s)(?:make(?:\s+install)?|ninja|cmake|[^\s/]*(?:clang|gcc|g\+\+)[^\s]*)\b')
R08 = b'%if "%{?_toolchain}" == "clang"\n# Clang-only option, if justified\n%endif\n'


STDERR_LIMIT = 4096
ANALYZER_DEPENDENCIES = {'yaml': 'PyYAML==6.0.2'}
IMPORT_PROBE = """import importlib
import sys
try:
    importlib.import_module(sys.argv[1])
except ImportError:
    sys.exit(6)
"""


def checked_last_line(config, tail):
    truncated = len(tail) > STDERR_LIMIT
    raw = bytes(tail[-STDERR_LIMIT:])
    try:
        if not check_content(raw, config)['allowed']:
            return None
    except FlowError:
        return None
    # Never disclose a fragment of a line whose leading context was discarded.
    if truncated and tail[0] != ord('\n'):
        raw = raw.partition(b'\n')[2]
    return next((line.strip() for line in reversed(raw.decode().splitlines()) if line.strip()), None)


def run_tool(config, script, args, work, reason, *, timeout=120):
    env = {key: os.environ[key] for key in ('PATH', 'LANG', 'LC_ALL') if key in os.environ}
    env.update(HOME=str(work), TMPDIR=str(work), PYTHONNOUSERSITE='1',
               PYTHONDONTWRITEBYTECODE='1')
    python = config.raw.get('analyzer', {}).get('python') or sys.executable
    command = [python, str(script), *map(str, args)]
    deadline = time.monotonic() + timeout
    tail = bytearray()
    child = None
    timed_out = False
    try:
        with subprocess.Popen(command, cwd=work, env=env, stdin=subprocess.DEVNULL,
                              stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                              start_new_session=True) as child:
            try:
                with selectors.DefaultSelector() as selector:
                    selector.register(child.stderr, selectors.EVENT_READ)
                    while True:
                        remaining = deadline - time.monotonic()
                        if remaining <= 0 or not selector.select(remaining):
                            raise subprocess.TimeoutExpired(command, timeout)
                        chunk = os.read(child.stderr.fileno(), 8192)
                        if not chunk:
                            break
                        tail.extend(chunk)
                        del tail[:-STDERR_LIMIT - 1]
                child.wait(timeout=max(0, deadline - time.monotonic()))
            except BaseException:
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                raise
    except subprocess.TimeoutExpired:
        timed_out = True
    except OSError:
        pass
    else:
        if child.returncode == 0:
            return
    details = {'exit_code': child.returncode if child is not None else None}
    if timed_out:
        details['timed_out'] = True
    line = checked_last_line(config, tail)
    if line is not None:
        details['stderr_last_line'] = line
    raise FlowError(5, reason, **details) from None


def check_analysis_dependencies(config, work):
    for module, package in ANALYZER_DEPENDENCIES.items():
        try:
            run_tool(config, '-c', [IMPORT_PROBE, module], work,
                     'log_analyzer_dependency_probe_failed', timeout=10)
        except FlowError as error:
            if error.details['exit_code'] == 6:
                reason = 'log_analyzer_dependency_missing'
                raise FlowError(6, reason, module=module, todo={
                    'reason': reason, 'message': f'install {package} in the analysis venv',
                }) from None
            raise FlowError(error.code, error.reason, module=module, **error.details) from None


def analyze_log(config, log, package, category):
    root = config.output('tmp/analysis-tools')
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='read-', dir=root) as directory:
        work = Path(directory)
        result = work / 'evidence_packet.json'
        check_analysis_dependencies(config, work)
        run_tool(config, ROOT / 'tizen-gbs-log-analysis/scripts/run_analyzer.py',
                 ['analyze', log, '--src-root', work, '--output-dir', work,
                  '--output-format', 'json', '--no-tiktoken', '--package', package['name'],
                  '--arch', package['arch']], work, 'log_analyzer_failed')
        try:
            packet = load_json(result)
            if packet['schema_version'] != 'evidence_packet/v1':
                raise ValueError
        except (FlowError, KeyError, TypeError, ValueError):
            raise FlowError(5, 'log_analyzer_evidence_invalid') from None
        primary = packet.get('primary_error') or {}
        clusters = packet.get('error_clusters') or {}
        evidence = packet.get('evidence') or {}
        reference = {
            'failed_phase_as_reported': packet.get('failed_phase'),
            'primary_error': primary,
            'error_clusters': {k: v for k, v in clusters.items() if k != 'full_locations_path'},
            'command_summary': evidence.get('command_summary') or evidence.get('current_command_summary'),
        }
        context = b''
        if category == 'build_error' and primary.get('kind') in {'compiler', 'werror'}:
            patch_dir = work / 'patch'
            run_tool(config, ROOT / 'tizen-gbs-patch-suggest/scripts/run_patch_suggest.py',
                     ['--evidence', result, '--output-dir', patch_dir],
                     work, 'patch_context_failed')
            try:
                context = (patch_dir / 'context.md').read_bytes()
            except OSError:
                raise FlowError(5, 'patch_context_missing') from None
            if re.search(rb'%\{\s*\??toolchain_is\b', context, re.I):
                context = b''
        return reference, context
