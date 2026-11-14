"""Isolated read-only P4 access, fixed marshal protocol and structured failures."""
from dataclasses import dataclass
import io
import marshal
import os
from pathlib import Path
import re
import shlex
import subprocess
import uuid
from .errors import FlowError
from .files import digest, json_bytes
from .build_inputs import validate_root
from .export import check_content


@dataclass
class P4Plan:
    argv: list[str]
    env: dict[str, str]
    cwd: str


def depot_path(path):
    if not isinstance(path, str) or not path.startswith('//') or '...' in path or any(c in path for c in '\0\r\n') or any(p in {'.', '..'} for p in path[2:].split('/')):
        raise FlowError(4, 'unsafe_depot_path')
    return ''.join({'@': '%40', '#': '%23', '%': '%25', '*': '%2A'}.get(c, c) for c in path)


def decode(record):
    return {(k.decode('utf-8') if isinstance(k, bytes) else k):
            (v.decode('utf-8', errors='surrogateescape') if isinstance(v, bytes) and k not in {b'data', 'data'} else v)
            for k, v in record.items()}


class P4Adapter:
    def __init__(self, config, *, tickets_override=None, fixture=False):
        self.config, self.p4 = config, config.raw['p4']
        self.tickets_override = tickets_override
        self.executable = str(Path(__file__).resolve().parents[2] / "fixtures/p4/fake_p4.py") if fixture else self.p4["executable"]
        self.config_name = self.p4.get('read_config_name') or '.vd-cosmos-noconfig-' + uuid.uuid4().hex
        self.audit = []
        self.returned_paths = set()

    def plan(self, args, *, _listing=False):
        if not args or not isinstance(args, list) or not all(isinstance(x, str) and '\0' not in x for x in args):
            raise FlowError(2, 'invalid_p4_arguments')
        if args[0].startswith('-'):
            raise FlowError(4, 'p4_connection_options_forbidden')
        if args[0] in {'set', 'submit', 'client', 'logout'} or (args[0] == 'login' and args != ['login', '-s']):
            raise FlowError(4, 'p4_command_forbidden')
        if args[0] not in {'info', 'login', 'files', 'dirs', 'describe', 'change', 'print', 'fstat'}:
            raise FlowError(4, 'p4_command_not_in_read_allowlist')
        if args[0] == 'change' and (len(args) != 3 or args[1] != '-o' or not args[2].isdigit()):
            raise FlowError(4, 'p4_command_forbidden')
        if any(a in {'-p', '-u', '-c', '-i', '-d'} for a in args[1:]):
            raise FlowError(4, 'p4_connection_options_forbidden')
        if any('...' in a for a in args[1:]):
            valid_listing = (_listing and len(args) == 4 and args[:2] == ['files', '-m']
                and args[2] == str(self.config.raw['analyzer']['root_list_max_files'])
                and re.fullmatch(r'//[^*#@]+/\.\.\.@[0-9]+', args[3])
                and args[3].count('...') == 1)
            if not valid_listing:
                raise FlowError(4, 'unsafe_depot_path')
        root = self.config.data_root
        for parent in (root, *root.parents):
            if (parent / self.config_name).exists() or (parent / self.config_name).is_symlink():
                raise FlowError(6, 'p4_config_name_exists')
        env = {k: os.environ[k] for k in ('PATH', 'LANG', 'LC_ALL', 'TZ', 'SYSTEMROOT') if k in os.environ}
        env.update(P4CONFIG=self.config_name, P4ENVIRO='/dev/null',
                   P4TICKETS=str(Path(self.tickets_override or self.p4['tickets_file']).expanduser()),
                   TMPDIR=str(self.config.output('tmp/p4')), XDG_CACHE_HOME=str(self.config.output('tmp/p4-cache')))
        argv = [self.executable, '-G', '-p', self.p4['port'], '-u', self.p4['user'],
                '-c', self.p4['no_client_name'], *args]
        return P4Plan(argv, env, str(root))

    def login_todo(self):
        if self.tickets_override:
            return {'reason': 'p4_login_required', 'message': '撤掉票据覆盖后继续；覆盖模式不提供登录命令'}
        command = [self.p4['executable'], '-p', self.p4['port'], '-u', self.p4['user'], 'login']
        prefix = ''
        if Path(self.p4['tickets_file']).expanduser() != Path.home() / '.p4tickets':
            prefix = 'P4TICKETS=' + shlex.quote(str(Path(self.p4['tickets_file']).expanduser())) + ' '
        rendered = prefix + shlex.join(command)
        if not check_content(rendered.encode(), self.config)['allowed']:
            raise FlowError(4, 'p4_login_command_credential_blocked')
        return {'reason': 'p4_login_required', 'message': '登录后继续', 'command': rendered}

    def execute(self, args, *, _listing=False):
        plan = self.plan(args, _listing=_listing)
        for path in (self.config.data_root, self.config.output('tmp/p4'), self.config.output('tmp/p4-cache')):
            path.mkdir(parents=True, exist_ok=True)
        try:
            process = subprocess.run(plan.argv, env=plan.env, cwd=plan.cwd, capture_output=True, timeout=self.p4['timeout_s'])
        except subprocess.TimeoutExpired:
            raise FlowError(5, 'p4_timeout') from None
        except OSError:
            raise FlowError(5, 'p4_process_start_failed') from None
        if process.returncode < 0:
            raise FlowError(5, 'p4_process_signal')
        stream = io.BytesIO(process.stdout)
        records = []
        try:
            while stream.tell() < len(process.stdout):
                record = marshal.load(stream)
                if not isinstance(record, dict) or not (b'code' in record or 'code' in record):
                    raise ValueError()
                records.append(decode(record))
        except (EOFError, ValueError, TypeError, UnicodeError):
            raise FlowError(5, 'p4_incomplete_output') from None
        if not records:
            raise FlowError(5, 'p4_incomplete_output')
        category = 'ok'
        table = self.p4['code0_table'].get(self.p4['version'], {})
        for record in records:
            if record['code'] == 'error':
                if not {'code0', 'fmt0', 'severity', 'generic'} <= set(record):
                    raise FlowError(5, 'p4_incomplete_output')
                entry = table.get(str(record['code0']))
                if not entry or str(entry['severity']) != str(record['severity']) or entry['exit_code'] != process.returncode:
                    raise FlowError(5, 'p4_unclassified', message={'code0': str(record.get('code0')), 'severity': str(record.get('severity')), 'generic': str(record.get('generic'))})
                if category not in {'ok', entry['category']}:
                    raise FlowError(5, 'p4_unclassified')
                category = entry['category']
        if category == 'ok' and process.returncode != 0:
            raise FlowError(5, 'p4_unclassified')
        self.audit.append({'command': args[0], 'exit_code': process.returncode, 'category': category,
                           'output_sha256': digest(process.stdout), 'records': len(records)})
        if category == 'not_logged_in':
            raise FlowError(3, 'p4_not_logged_in', todo=self.login_todo())
        if category not in {'ok', 'file_missing', 'history_missing'}:
            raise FlowError(5, 'p4_' + category)
        for record in records:
            for name, value in record.items():
                if re.fullmatch(r'(?:depotFile|movedFile)[0-9]*', name) and isinstance(value, str):
                    self.returned_paths.add(value)
        return {'category': category, 'records': records}

    def stat(self, args, required, *, _listing=False):
        result = self.execute(args, _listing=_listing)
        if result['category'] != 'ok':
            return result
        records = [r for r in result['records'] if r['code'] == 'stat']
        if not records or any(not set(required) <= set(r) for r in records):
            raise FlowError(5, 'p4_incomplete_output')
        return {**result, 'records': records}

    def info(self):
        record = self.stat(['info'], ['userName', 'serverAddress', 'clientName', 'serverDate'])['records'][0]
        if (record['userName'] != self.p4['user'] or record['serverAddress'] != self.p4['expected_server_address']
                or record['clientName'] != self.p4['unknown_client_marker'] or 'clientRoot' in record):
            raise FlowError(6, 'p4_context_mismatch', todo={'reason': 'p4_context_mismatch'})
        return record

    def login_status(self, *, require_minimum=True):
        record = self.stat(['login', '-s'], ['TicketExpiration'])['records'][0]
        try:
            remaining = int(record['TicketExpiration'])
        except (ValueError, TypeError):
            raise FlowError(5, 'p4_incomplete_output') from None
        if remaining < 0 or (require_minimum and remaining < self.p4['min_ticket_minutes'] * 60):
            raise FlowError(3, 'p4_ticket_expiring', todo=self.login_todo())
        return remaining

    def files(self, path, revision, *, encoded=False):
        return self.stat(['files', self.path_argument(path, encoded=encoded) + revision], ['depotFile', 'rev', 'type', 'action'])

    def list_files(self, root, revision):
        validate_root(root, self.p4['min_root_depth'])
        if not re.fullmatch(r'@[0-9]+', revision):
            raise FlowError(4, 'invalid_listing_revision')
        limit = self.config.raw['analyzer']['root_list_max_files']
        query = depot_path(root) + '/...' + revision
        result = self.stat(['files', '-m', str(limit), query],
                           ['depotFile', 'rev', 'type', 'action'], _listing=True)
        if result['category'] != 'ok':
            return []
        records = result['records']
        if len(records) >= limit:
            raise FlowError(5, 'p4_listing_limit')
        if any(not r['depotFile'].startswith(depot_path(root) + '/') for r in records):
            raise FlowError(5, 'p4_listing_outside_package')
        return [r for r in records if r['action'] not in {'delete', 'move/delete'}]

    def path_argument(self, path, *, encoded=False):
        # Origin is explicit: a literal external name may itself contain %40.
        if encoded:
            if path not in self.returned_paths:
                raise FlowError(4, 'unrecognized_p4_returned_path')
            return path
        return depot_path(path)

    def describe(self, scl):
        if not str(scl).isdigit():
            raise FlowError(2, 'invalid_changelist')
        result = self.stat(['describe', '-S', '-s', str(scl)], ['change', 'status'])
        if result['category'] != 'ok':
            return {'historical_missing': True, 'files': []}
        record = result['records'][0]
        if record['status'] != 'pending' or 'shelved' not in record:
            return {'historical_missing': True, 'files': [], 'status': record['status']}
        files = []
        indexes = sorted(int(k[9:]) for k in record if re.fullmatch(r'depotFile[0-9]+', k))
        if not indexes or indexes != list(range(len(indexes))):
            raise FlowError(5, 'p4_incomplete_output')
        for index in indexes:
            fields = {k: record.get(k + str(index)) for k in ('depotFile', 'rev', 'action', 'type', 'digest', 'fileSize', 'movedFile')}
            required = ['depotFile', 'rev', 'action', 'type']
            if fields['action'] not in {'delete', 'move/delete'}:
                required += ['digest', 'fileSize']
            if any(fields[k] is None for k in required):
                raise FlowError(5, 'p4_incomplete_output')
            files.append(fields)
        return {'historical_missing': False, 'files': files, 'digest': digest(json_bytes(files))}

    def change(self, scl):
        return self.stat(['change', '-o', str(scl)], ['Change', 'shelveUpdate'])

    def file_size(self, path, revision, *, encoded=False):
        result = self.stat(['fstat', '-Ol', self.path_argument(path, encoded=encoded) + revision], ['depotFile', 'fileSize'])
        if result['category'] != 'ok':
            return None
        try:
            value = int(result['records'][0]['fileSize'])
            if value < 0:
                raise ValueError()
            return value
        except (ValueError, TypeError):
            raise FlowError(5, 'p4_incomplete_output') from None

    def print_file(self, path, revision, *, keywords=False, encoded=False):
        result = self.execute(['print', *([] if keywords else ['-k']), '-q', self.path_argument(path, encoded=encoded) + revision])
        if result['category'] != 'ok':
            raise FlowError(5, 'p4_' + result['category'])
        pieces = [r.get('data') for r in result['records'] if r['code'] in {'text', 'binary'}]
        if not pieces or not all(isinstance(p, bytes) for p in pieces):
            raise FlowError(5, 'p4_incomplete_output')
        return b''.join(pieces)
