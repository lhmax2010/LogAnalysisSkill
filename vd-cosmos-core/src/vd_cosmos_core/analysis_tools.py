"""Run the existing analyzer and read-only context producer without passing ambient secrets."""
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from .errors import FlowError
from .files import load_json

ROOT = Path(__file__).resolve().parents[3]
DIAGNOSTIC = re.compile(
    rb'(?:^|[\r\n])([^\r\n]*?:\d+(?::\d+)?:\s*(?:fatal error|error|warning|note):[^\r\n]*)'
)
COMMAND = re.compile(rb'(?:^|\s)(?:make(?:\s+install)?|ninja|cmake|[^\s/]*(?:clang|gcc|g\+\+)[^\s]*)\b')
R08 = b'%if "%{?_toolchain}" == "clang"\n# Clang-only option, if justified\n%endif\n'


def run_tool(script, args, work, reason):
    env = {key: os.environ[key] for key in ('PATH', 'LANG', 'LC_ALL') if key in os.environ}
    env.update(HOME=str(work), TMPDIR=str(work), PYTHONNOUSERSITE='1',
               PYTHONDONTWRITEBYTECODE='1')
    try:
        subprocess.run([sys.executable, str(script), *map(str, args)], cwd=work,
                       env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=120, check=True)
    except (OSError, subprocess.SubprocessError):
        raise FlowError(5, reason) from None


def analyze_log(config, log, package, category):
    root = config.output('tmp/analysis-tools')
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='read-', dir=root) as directory:
        work = Path(directory)
        result = work / 'evidence_packet.json'
        run_tool(ROOT / 'tizen-gbs-log-analysis/scripts/run_analyzer.py',
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
            run_tool(ROOT / 'tizen-gbs-patch-suggest/scripts/run_patch_suggest.py',
                     ['--evidence', result, '--output-dir', patch_dir],
                     work, 'patch_context_failed')
            try:
                context = (patch_dir / 'context.md').read_bytes()
            except OSError:
                raise FlowError(5, 'patch_context_missing') from None
            if re.search(rb'%\{\s*\??toolchain_is\b', context, re.I):
                context = b''
        return reference, context
