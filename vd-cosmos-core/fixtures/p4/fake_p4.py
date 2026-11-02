#!/usr/bin/env python3
"""Offline marshal-speaking P4. Reads only ./fake-p4.json; never opens a socket."""
import base64
import fnmatch
import hashlib
import json
import marshal
import os
from pathlib import Path
import signal
import sys
from urllib.parse import unquote

config = json.loads(Path('fake-p4.json').read_text())
args = sys.argv[1:]
if args[:1] != ['-G'] or args[1:2] != ['-p'] or args[3:4] != ['-u'] or args[5:6] != ['-c']:
    raise SystemExit(97)
if set(k for k in os.environ if k.startswith('P4')) != {'P4CONFIG', 'P4ENVIRO', 'P4TICKETS'} or os.environ['P4ENVIRO'] != '/dev/null':
    raise SystemExit(98)
command = args[7:]
with Path('fake-p4-calls.jsonl').open('a') as audit:
    audit.write(json.dumps({'args': args, 'p4_env': {k: v for k, v in os.environ.items() if k.startswith('P4')}})+'\n')
mode = config.get('mode')
if mode == 'killed':
    os.kill(os.getpid(), signal.SIGKILL)
if mode == 'truncated':
    sys.stdout.buffer.write(marshal.dumps({b'code': b'stat'})[:-1]); raise SystemExit(0)

def emit(record):
    marshal.dump({k.encode(): v.encode() if isinstance(v, str) else v for k, v in record.items()}, sys.stdout.buffer)

def error(number, severity, status):
    emit({'code': 'error', 'code0': str(number), 'fmt0': 'fixture structured message', 'severity': str(severity), 'generic': '17', 'data': b'fixture error'})
    raise SystemExit(status)

if mode == 'unknown': error(99999, 3, 1)
if mode == 'not_logged_in': error(807672853, 3, 1)
files = config.get('files', {})
if command == ['info']:
    emit({'code': 'stat', 'userName': args[4], 'serverAddress': config.get('server', args[2]),
          'clientName': config.get('client', '*unknown*'), 'serverDate': '2026/11/02 12:00:00 +0900 JST'})
elif command == ['login', '-s']:
    emit({'code': 'stat', 'TicketExpiration': str(config.get('ticket_seconds', 7200))})
elif command[0] in {'describe', 'change'}:
    shelf = config.get('shelves', {}).get(command[-1])
    if shelf is None: error(822220826 if command[0]=='change' else 554768749, 3 if command[0]=='change' else 2, 1 if command[0]=='change' else 0)
    if command[0] == 'change':
        emit({'code': 'stat', 'Change': command[-1], 'shelveUpdate': shelf.get('updated', '2026/10/01 10:00:00'),
              'shelveAccess': '2026/11/02 12:00:00', 'Date': '2026/09/01 10:00:00'})
    else:
        record = {'code': 'stat', 'change': command[-1], 'status': shelf.get('status', 'pending'), 'time': '1750000000'}
        if shelf.get('status', 'pending') == 'pending' and shelf.get('shelved', True): record['shelved'] = ''
        for i, item in enumerate(shelf.get('files', [])):
            raw = base64.b64decode(item.get('content', ''))
            fields = {'depotFile': item['path'], 'action': item.get('action', 'edit'), 'type': item.get('type', 'text'),
                      'rev': str(item.get('rev', 1)), 'digest': hashlib.md5(raw).hexdigest().upper(), 'fileSize': str(len(raw))}
            if item.get('movedFile'): fields['movedFile'] = item['movedFile']
            record.update({k+str(i): v for k, v in fields.items()})
        emit(record)
else:
    value = command[-1]
    mark = '#' if '#' in value else '@'
    escaped, _, revision = value.rpartition(mark)
    path, revision = unquote(escaped), mark+revision
    if command[0] == 'dirs':
        prefix = path[:-1]
        dirs = sorted({p[:p.find('/',len(prefix))] for p in files if p.startswith(prefix) and '/' in p[len(prefix):]})
        if not dirs: error(554768759, 2, 0)
        for directory in dirs: emit({'code': 'stat', 'dir': directory})
    elif command[0] in {'files', 'fstat'}:
        selected = []
        for p, versions in files.items():
            if (p == path or (path.endswith('/*') and p.startswith(path[:-1]) and '/' not in p[len(path)-1:])) and revision in versions:
                selected.append((p, versions[revision]))
        if not selected: error(554768759, 2, 0)
        for p, item in selected:
            emit({'code': 'stat', 'depotFile': p, 'rev': str(item.get('rev', 1)), 'type': item.get('type', 'text'),
                  'action': item.get('action', 'edit'), 'fileSize': str(len(base64.b64decode(item.get('content',''))))})
    elif command[0] == 'print':
        item = files.get(path, {}).get(revision)
        if revision.startswith('@='):
            item = next((x for x in config.get('shelves', {}).get(revision[2:], {}).get('files', []) if x['path']==path), None)
        if item is None: error(554768759, 2, 0)
        raw = base64.b64decode(item.get('expanded' if '-k' not in command and 'expanded' in item else 'content',''))
        emit({'code': 'text', 'data': raw})
    else: error(99999, 3, 1)
