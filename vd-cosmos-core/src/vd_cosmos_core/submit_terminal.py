"""Human-only confirmation from a controlling terminal; never accept pipe answers."""
import json
import os
from pathlib import Path
import re
import sys
import uuid

from .commands import Category, CommandContext
from .errors import FlowError
from .export import check_content
from .files import atomic_write, digest, json_bytes


CONFIRM_PROMPT_BYTES = 4096
_CONFIRM_REASONS = {'source': 'source_confirmation_required', 'run': 'run_confirmation_required',
                    'digest': 'digest_confirmation_required', 'resubmit': 'resubmit_confirmation_required'}


def _instruction(kind, expected):
    return {
        'source': f'输入构建号 {expected} 以确认 / type {expected} to confirm',
        'run': f'type {expected} to confirm',
        'digest': f'type the 12-character digest prefix {expected} to confirm',
        'resubmit': f'type {expected} to confirm',
    }[kind]


def confirmation_error(kind, expected):
    reason = _CONFIRM_REASONS[kind]
    return FlowError(3, reason, todo={'reason': reason, 'expected': expected,
                                     'message': _instruction(kind, expected)})


def _cell(value):
    if value is None:
        return '-'
    raw = str(value)
    if len(raw.encode()) > 120 or '\n' in raw or '\r' in raw:
        return f'{len(raw.splitlines())} lines; sha256={digest(raw.encode())}'
    return ''.join(c if c.isprintable() else '?' for c in raw)


def _lists(values):
    out = []
    for key in ('PACKAGE_LIST', 'SHELVE_LIST', 'BASE_REPOS', 'PRODUCT_REPOS', 'KS_LIST'):
        if key in values:
            raw = values[key]
            out.append(f'{key}: {sum(bool(line.strip()) for line in raw.splitlines())} nonblank lines; sha256={digest(raw.encode())}')
    return out


def _target(data):
    return 'Target config: ' + _cell(data.get('target', {}).get('config'))


def _summary(kind, data):
    if kind == 'source':
        lines = [f'Source: Hub {_cell(data["hub_id"])} / BM build {_cell(data["build_id"])} (BM config {_cell(data["config_id"])})',
                 _target(data), f'Packages: {_cell(data["package_count"])}; parsed sha256={_cell(data["package_digest"])}',
                 f'Source variables: sha256={_cell(data["variables_sha256"])}; conditions sha256={_cell(data["conditions_sha256"])}']
        lines += _lists(data['variables'])
        headers = data['headers']
        for arch, values in sorted(headers.items())[:2]:
            fields = ('arch', 'start_time', 'base', 'product', 'build_conf', 'profile', 'gbs_version')
            lines.append(f'Report headers [{_cell(arch)}]: ' + '; '.join(
                f'{k}={_cell(values[k])}' for k in fields if k in values))
        if len(headers) > 2:
            lines.append(f'All report headers: {len(headers)} architectures; sha256={digest(json_bytes(headers))}')
        return lines, str(data['build_id'])
    if kind == 'run':
        pattern = data['run_pattern']
        return [_target(data), 'Run pattern: ' + ' '.join(_cell(pattern[k]) for k in ('method', 'path', 'listener', 'component'))], 'allow-run'
    if kind == 'digest':
        prefix = data['digest_prefix']
        lines = [_target(data), f'Request: {_cell(data["request"])}; mode: {"rehearsal" if data["rehearse"] else "submit"}',
                 f'Request sha256={_cell(data["digest"])}; prefix={prefix}; {len(data["values"])} form fields']
        encoding = data['serialization'].get('ks_encoding')
        if data['rehearse']:
            if encoding in ('ids', 'texts'):
                lines.append(f'KS_LIST encoding observed: {encoding}')
            lines.append(f"callbacks sent: {data['serialization'].get('callbacks_sent', 0)}")
        return lines + _lists(data['values']), prefix
    previous = data['submissions']
    return [_target(data), f'Resubmit of: {_cell(data["resubmit_of"])}; next round: {_cell(data["next_round"])}',
            f'Request sha256={_cell(data["digest"])}',
            f'Prior submissions: {len(previous)}; sha256={digest(json_bytes(previous))}'], 'resubmit'


def confirm_once(config, payload):
    """Print bounded terminal text; retain the complete, checked JSON separately."""
    kind = payload.get('confirmation')
    if kind not in _CONFIRM_REASONS:
        raise FlowError(2, 'unknown_confirmation_kind')
    content = json_bytes(payload)
    if not check_content(content, config)['allowed']:
        raise FlowError(4, 'output_credential_blocked')
    lines, expected = _summary(kind, payload)
    if ((kind == 'source' and not re.fullmatch(r'[0-9]{1,32}', expected))
            or (kind == 'digest' and not re.fullmatch(r'[0-9a-f]{12}', expected))):
        raise FlowError(4, 'invalid_confirmation_expected')
    relative = f'submit/confirmations/{uuid.uuid4().hex}-{kind}.json'
    path = str(config.output(relative))
    shown = path if path.isprintable() and len(path.encode()) <= 512 else f'data_root/{relative}'
    footer = f'Full JSON: {shown}\n{_instruction(kind, expected)}\n> '
    prompt = '\n'.join(lines) + '\n' + footer
    if len(prompt.encode()) > CONFIRM_PROMPT_BYTES:
        kept = []
        omitted = 'Other details: see full JSON.\n'
        for line in lines:
            if len(('\n'.join(kept + [line]) + '\n' + omitted + footer).encode()) > CONFIRM_PROMPT_BYTES:
                break
            kept.append(line)
        prompt = '\n'.join(kept) + '\n' + omitted + footer
    if not check_content(prompt.encode(), config)['allowed']:
        raise FlowError(4, 'output_credential_blocked')
    try:
        atomic_write(config.data_root, relative, content)
    except OSError:
        raise FlowError(5, 'confirmation_artifact_write_failed') from None
    return ask(prompt)


def ancestors_allowed(proc_root=Path("/proc"), parent_pid=None):
    pid = os.getppid() if parent_pid is None else parent_pid; visited = set()
    while pid > 1 and pid not in visited:
        visited.add(pid)
        try:
            base = Path(proc_root) / str(pid)
            command = (base / 'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace').casefold()
            if 'cline' in command or 'extensionhost' in command or 'extension-host' in command:
                raise FlowError(4, 'ai_process_ancestor_refused')
            stat = (base / 'stat').read_text(); pid = int(stat[stat.rfind(')') + 2:].split()[1])
        except (OSError, ValueError):
            raise FlowError(4, 'ancestor_unverified') from None


def available():
    if not sys.stdin.isatty(): return False
    try:
        with open('/dev/tty') as stream: return stream.isatty()
    except OSError: return False


def human_context(command, category=Category.HUMAN):
    if not available(): raise FlowError(2, 'terminal_required')
    ancestors_allowed()
    if ask('Confirm command (yes): ') != 'yes': raise FlowError(3, 'confirmation_required')
    return CommandContext(command, category, True)


def ask(prompt):
    try:
        with open('/dev/tty', 'r', encoding='utf-8') as stream, open('/dev/tty', 'w', encoding='utf-8') as out:
            if not stream.isatty(): raise FlowError(2, 'terminal_required')
            out.write(prompt); out.flush()
            return stream.readline().strip()
    except OSError:
        raise FlowError(2, 'terminal_required') from None


def confirm(prepared):
    return ask(json.dumps(prepared, ensure_ascii=False, indent=2) + '\n输入构建号及所需确认词（空格分隔）： ').split()
