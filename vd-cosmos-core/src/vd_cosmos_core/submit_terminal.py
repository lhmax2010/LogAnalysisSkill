"""Human-only confirmation from a controlling terminal; never accept pipe answers."""
import json
import os
from pathlib import Path
import sys

from .commands import Category, CommandContext
from .errors import FlowError


def ancestors_allowed():
    pid = os.getppid(); visited = set()
    while pid > 1 and pid not in visited:
        visited.add(pid)
        try:
            base = Path('/proc') / str(pid)
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


def human_context(command):
    if not available(): raise FlowError(2, 'terminal_required')
    ancestors_allowed()
    if ask('Confirm command (yes): ') != 'yes': raise FlowError(3, 'confirmation_required')
    return CommandContext(command, Category.HUMAN, True)


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
