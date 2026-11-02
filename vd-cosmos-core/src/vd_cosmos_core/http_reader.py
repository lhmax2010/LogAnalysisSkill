"""HTTP reader with instance-scoped storage, maturity and bounded evidence."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import posixpath
import re
from urllib.parse import urljoin, urlsplit
from .backends import ReportReader
from .errors import FlowError
from .export import check_content
from .files import atomic_write, digest, json_bytes, load_json
from .models import BuildRef
from .observation import detail_state, summarize
from .report import Document, parse_report
from .baselines import baseline_revision, apply_rows_coverage
from .stability import advance, maturity, execution_clock
from .receipts import manual_terminal, terminal_basis, log_binding
from .transport import HTTPTransport, direct_host, origin, normalized_path, log_allowed
from .versions import build_key, parsing_digest, PARSER_VERSION


def sanitized(value, config):
    if isinstance(value, dict):
        return {k: sanitized(v, config) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitized(v, config) for v in value]
    return value if check_content(json_bytes(value), config)['allowed'] else '未保留'


def index_fingerprint(data, regex):
    doc = Document(data.decode('utf-8'))
    forbidden = any(n.tag == 'form' or (n.tag == 'input' and (n.attrs.get('type') or '').casefold() == 'password') for n in doc.nodes)
    matched = sum(n.tag == 'a' and bool(re.fullmatch(regex, n.attrs.get('href') or '')) for n in doc.nodes)
    return {'verified': not forbidden and matched > 0, 'matched_links': matched, 'form_or_password': forbidden}


class HTTPReportReader(ReportReader):
    capabilities = frozenset({'observe', 'read_packages', 'read_inputs', 'fetch_log'})

    def __init__(self, config, build_id, expected_rows=None, *, clock=None):
        if not isinstance(build_id, str) or not re.fullmatch(r'[0-9]+', build_id):
            raise FlowError(2, 'invalid_build_id')
        self.config, self.build_id = config, build_id
        self.cosmos = config.raw['cosmos']
        if not self.cosmos.get('report_root') or not self.cosmos.get('report_path_template'):
            raise FlowError(2, 'http_report_configuration_required')
        if any(not re.fullmatch(r'[A-Za-z0-9_.-]+', arch) for arch in self.cosmos['archs']):
            raise FlowError(2, 'invalid_architecture')
        root = self.cosmos['report_root']; scheme, host, port = origin(root)
        identity = f'{scheme}://{host}:{port}' + normalized_path(urlsplit(root).path)
        self.build_ref = BuildRef('cosmos-http', identity, build_id, 'cosmos')
        self.folder = 'rounds/' + build_key(self)
        self.clock = clock or (lambda: datetime.now(timezone.utc).isoformat())
        self.transport = HTTPTransport(config)
        self.rows = None
        if expected_rows:
            try:
                self.rows = sorted(baseline_revision(line) for line in config.source(expected_rows).read_text().splitlines() if line.strip())
            except (OSError, UnicodeError):
                raise FlowError(2, 'invalid_expected_rows') from None
        self._observed = None

    def expected_digest(self):
        return digest(json_bytes(self.rows))

    def check_ref(self, ref):
        if ref != self.build_ref:
            raise FlowError(6, 'build_identity_mismatch')

    def report_url(self, arch):
        path = self.cosmos['report_path_template'].format(last3=self.build_id[-3:].zfill(3), build_id=self.build_id, arch=arch)
        return self.cosmos['report_root'].rstrip('/') + '/' + path.lstrip('/')

    def index(self):
        path = self.cosmos.get('bucket_path_template', 'b{last3}/').format(last3=self.build_id[-3:].zfill(3), build_id=self.build_id)
        response = self.transport.get(self.cosmos['report_root'].rstrip('/') + '/' + path.lstrip('/'), self.config.raw['fetch']['max_page_bytes'])
        try:
            fingerprint = index_fingerprint(response['body'], self.cosmos['index_link_regex'])
        except UnicodeError:
            fingerprint = {'verified': False, 'matched_links': 0}
        return response, fingerprint

    def record(self, arch, record, response, at, reset=False):
        path = self.config.output(f'{self.folder}/pages/{arch}/continuous.json')
        old = load_json(path) if path.exists() else {'continuous': None, 'history': []}
        value = {**old, 'continuous': None if reset else record,
                 'history': (old['history'] + [{'observed_at': at, 'response': sanitized(response, self.config),
                                              'continuous': record if not reset else None}])[-50:]}
        atomic_write(self.config.data_root, path, json_bytes(value))

    def _arch(self, arch, execution):
        url = self.report_url(arch)
        response = self.transport.get(url, self.config.raw['fetch']['max_page_bytes'])
        stamp, status = self.clock(), response['status']
        if status == 404:
            self.record(arch, None, response['response'], stamp, reset=True)
            try:
                index, fingerprint = self.index()
            except FlowError as error:
                if error.code != 5:
                    raise
                raise FlowError(5, 'index_unverified', http_status=404, response=error.details.get('response')) from None
            if index['status'] == 200 and fingerprint['verified']:
                return {'arch': arch, 'http_status': 404, 'index': fingerprint, 'response': response['response'],
                        'index_response': index['response'], 'observed_at': stamp, 'settled': False,
                        'report_state': '未发布', 'result_state': '未知', 'package_coverage': '未核',
                        'coverage_basis': 'manual_file' if arch == 'armv7l' and self.rows is not None else 'none', 'headers': {}, 'issues': []}
            raise FlowError(5, 'index_unverified', http_status=404, response=response['response'])
        if status != 200:
            raise FlowError(5, f'http_{status}', http_status=status, response=response['response'])
        data = response['body']
        try:
            allowed = check_content(data, self.config)['allowed']
            html = data.decode('utf-8')
        except (FlowError, UnicodeError):
            raise FlowError(5, 'not_a_report', http_status=status, response=response['response']) from None
        if not allowed:
            raise FlowError(5, 'credential_blocked', http_status=status, response=response['response'])
        folder = f'{self.folder}/pages/{arch}'
        history_path = self.config.output(folder + '/continuous.json')
        old = load_json(history_path).get('continuous') if history_path.exists() else None
        execution.update(execution_clock(execution, execution, stamp, report_success=True))
        record = advance(old, digest(data), stamp, parsing_digest(self.config), execution)
        stable, settled = maturity(record, self.config.raw['poll'], execution)
        try:
            report = parse_report(html, arch, self.cosmos, stable=stable, settled=settled, source_url=url)
        except FlowError as error:
            if error.code != 5:
                raise
            raise FlowError(5, 'not_a_report', http_status=status, response=response['response']) from None
        path = self.config.output(folder + '/' + digest(data) + '.html')
        if path.exists() and digest(path.read_bytes()) == digest(data):
            artifact = {'path': str(path), 'sha256': digest(data), 'size': len(data)}
        else:
            artifact = atomic_write(self.config.data_root, path, data)
        self.record(arch, record, response['response'], stamp)
        report.update(settled_basis=record['settled_basis'], observed_at=stamp, http_status=status, continuous=record, response=sanitized(response['response'], self.config), evidence=artifact)
        return apply_rows_coverage(report, self.rows if arch == 'armv7l' else None)

    def detail(self):
        source = self.cosmos.get('status_source')
        execution = {'state': '未知', 'trust': 'unknown', 'basis': 'title_not_matched'}
        if not source:
            path = self.config.output(self.folder + '/detail.json')
            previous = load_json(path) if path.exists() else {}
            return {**execution, **execution_clock(previous, execution, self.clock()), 'invalid_manual_events': previous.get('invalid_manual_events', [])}
        try:
            response = self.transport.get(source['url_template'].format(build_id=self.build_id), self.config.raw['fetch']['max_page_bytes'])
            if response['status'] != 200:
                raise FlowError(5, 'http_' + str(response['status']), http_status=response['status'], response=response['response'])
            data = response['body']
            execution = detail_state(data, source, self.build_id)
            execution.update(sha256=digest(data), response=response['response'], http_status=response['status'],
                             raw_retained=False, retention_note='原文未保留（命中凭据模式）' if not check_content(data, self.config)['allowed'] else '原文未保留')
        except FlowError as error:
            if error.code != 5:
                raise
            execution = {'state': '未知', 'trust': 'unknown', 'basis': 'detail_fetch_failed', 'failure': error.reason,
                         'http_status': error.details.get('http_status'), 'response': error.details.get('response')}
        except UnicodeError:
            execution = {'state': '未知', 'trust': 'unknown', 'basis': 'title_not_matched'}
        path = self.config.output(self.folder + '/detail.json')
        previous = load_json(path) if path.exists() else {'count': 0}
        failed = execution.get('identity') != 'strong' or execution['state'] == '未知'
        count = previous.get('count', 0) + 1 if failed else 0
        at = previous.get('first_seen_at') if failed and previous.get('count') else self.clock()
        execution.update(execution_clock(previous, execution, self.clock()))
        execution['invalid_manual_events'] = previous.get('invalid_manual_events', [])
        execution.setdefault('identity_match', None)
        execution.setdefault('candidates', [])
        execution.update(failure_count=count, failure_started_at=at if failed else None,
                         rule_version=PARSER_VERSION, detail_attempted=True)
        execution = sanitized(execution, self.config)
        atomic_write(self.config.data_root, path, json_bytes({**execution, 'count': count, 'first_seen_at': at, 'evidence': execution}))
        return execution

    def observe(self, build_ref):
        self.check_ref(build_ref)
        if self._observed is not None:
            return self._observed
        execution = self.detail()
        reports = {}
        for arch in self.cosmos['archs']:
            try:
                reports[arch] = self._arch(arch, execution)
            except FlowError as error:
                if error.code != 5:
                    raise
                stamp = self.clock()
                evidence = sanitized(error.details.get('response', {}), self.config)
                self.record(arch, None, evidence, stamp, reset=True)
                reports[arch] = {'arch': arch, 'observation_failed': True, 'headers': {}, 'settled': False,
                                 'error': error.reason, 'http_status': error.details.get('http_status'),
                                 'response': evidence, 'observed_at': stamp}
        invalidated = execution.setdefault('invalid_manual_events', [])
        manual = manual_terminal(self.config, build_key(self), reports, invalidated)
        execution['terminal_basis'] = terminal_basis(execution, manual)
        execution['manual_conflict'] = bool(manual and execution.get('effective_state') in {'运行', '排队'})
        for arch, report in list(reports.items()):
            if not report.get('continuous'):
                continue
            record = report['continuous']
            stable, settled = maturity(record, self.config.raw['poll'], execution, manual)
            parsed = parse_report(self.config.output(report['evidence']['path']).read_text(), arch, self.cosmos,
                                  stable=stable, settled=settled, source_url=self.report_url(arch))
            parsed.update({k: report[k] for k in ('observed_at', 'http_status', 'continuous', 'response', 'evidence')})
            parsed['settled_basis'] = record['settled_basis']
            reports[arch] = apply_rows_coverage(parsed, self.rows if arch == 'armv7l' else None)
        for arch, report in reports.items():
            history_path = self.config.output(f'{self.folder}/pages/{arch}/continuous.json')
            history = load_json(history_path) if history_path.exists() else {}
            stamp = report.get('observed_at', self.clock())
            if report.get('report_state') == '未发布':
                history['unpublished_since'] = history.get('unpublished_since') or stamp
            else:
                history['unpublished_since'] = None
            if report.get('continuous') and not report.get('settled'):
                history['unsettled_since'] = history.get('unsettled_since') or stamp
                audit = history.get('history', [])
                previous = audit[-2].get('continuous') if len(audit) >= 2 else None
                changed = bool(previous and previous['sha256'] != report['continuous']['sha256'])
                history['change_count'] = history.get('change_count', 0) + int(changed)
            else:
                history['unsettled_since'], history['change_count'] = None, 0
            report.update({k: history.get(k) for k in ('unpublished_since', 'unsettled_since', 'change_count')})
            first_failures = history.setdefault('first_failures', {})
            for package in report.get('packages', []):
                if package['category'] in {'build_error', 'export_error'}:
                    identity = digest(json_bytes(package['key']))
                    package['first_failure_observed_at'] = first_failures.setdefault(identity, stamp)
            atomic_write(self.config.data_root, history_path, json_bytes(history))
        atomic_write(self.config.data_root, self.folder + '/detail.json', json_bytes({**execution,
            'count': execution.get('failure_count', 0), 'first_seen_at': execution.get('failure_started_at')}))
        self._observed = summarize(build_ref, self.cosmos, reports, execution, backend=self.__class__.__name__)
        for arch, report in reports.items():
            if report.get('error') == 'credential_blocked':
                self._observed['todos'].append({'reason': 'report_credential_pattern_blocked', 'arch': arch,
                    'basis_version': report.get('response', {}).get('sha256')})
        if execution.get('failure_count', 0) >= 3:
            self._observed['todos'].append({'reason': 'detail_page_unavailable', 'basis_version': execution['failure_started_at']})
        return self._observed

    def read_packages(self, build_ref, arch):
        if arch not in self.cosmos['archs']:
            raise FlowError(2, 'unexpected_architecture')
        return self.observe(build_ref)['reports'][arch]

    def read_inputs(self, build_ref):
        observed = self.observe(build_ref)
        return {'reports': {a: {'headers': r.get('headers', {}), 'rows': r.get('input_rows', [])} for a, r in observed['reports'].items()},
                'header_consistency': observed['header_consistency'], 'package_coverage': observed['package_coverage'],
                'todos': observed['todos'], 'exit_code': observed['exit_code']}

    def provides(self):
        return []

    def fetch_log(self, build_ref, arch, package):
        self.check_ref(build_ref)
        if arch not in self.cosmos['archs'] or package['key']['arch'] != arch:
            raise FlowError(2, 'unexpected_architecture')
        report_url = self.report_url(arch)
        url = urljoin(report_url, package.get('log_url') or '')
        if not package.get('log_url') or not log_allowed(url, report_url):
            raise FlowError(4, 'log_url_outside_build', todo={'reason': 'log_url_outside_build', 'arch': arch, 'key': package['key']})
        nvr = posixpath.basename(posixpath.dirname(normalized_path(urlsplit(url).path)))
        if not re.fullmatch(r'[A-Za-z0-9_+.-]+', nvr) or nvr in {'.', '..'}:
            raise FlowError(4, 'unsafe_log_name')
        relative = f'{self.folder}/logs/{arch}/{nvr}/log.txt'
        destination, meta = self.config.output(relative), self.config.output(relative + '.json')
        report_sha = self.observe(build_ref)['reports'][arch].get('evidence', {}).get('sha256')
        binding = log_binding(self.observe(build_ref), arch, self.config.raw['fetch']['max_log_bytes'], url)
        if meta.exists():
            record = load_json(meta)
            destination = self.config.output(record['path'])
            if record.get('key') == package['key'] and record.get('binding') == binding and record.get('final') and destination.is_file() and destination.stat().st_size == record.get('size') and digest(destination.read_bytes()) == record.get('sha256'):
                return {**record, 'skipped': True}
        try:
            response = self.transport.get(url, self.config.raw['fetch']['max_log_bytes'], truncate=True, report_url=report_url)
            if response['status'] != 200:
                raise FlowError(5, 'http_' + str(response['status']), http_status=response['status'],
                                response=response['response'], responses=response['responses'])
        except FlowError as error:
            if error.code == 4:
                error.details['todo'] = {'reason': 'log_url_outside_build', 'arch': arch, 'key': package['key'], 'basis_version': report_sha}
            error.details = sanitized(error.details, self.config)
            # Failure evidence contains metadata only, never the incomplete body;
            # it is separate from the successful log/cache metadata.
            error.details['request_evidence'] = atomic_write(self.config.data_root, relative + '.failure.json',
                json_bytes({'reason': error.reason, 'binding': binding, **error.details}))
            raise
        try:
            allowed = check_content(response['body'], self.config)['allowed']
        except FlowError:
            allowed = False
        revision = digest(json_bytes({'body': digest(response['body']), 'binding': binding}))
        artifact = atomic_write(self.config.data_root, relative + '.revisions/' + revision + '/log.txt', response['body'])
        record = {**artifact, 'key': package['key'], 'first_failure_observed_at': package.get('first_failure_observed_at'), 'final': bool(binding['final_stage'] and response['transfer_complete']), 'settled_basis': binding['settled_basis'], 'terminal_basis': binding['terminal_basis'], 'truncated': response['truncated'], 'transfer_complete': response['transfer_complete'],
                  'export_allowed': allowed, 'export_note': '可导出' if allowed else '禁止导出', 'binding': binding,
                  'response': sanitized(response['response'], self.config),
                  'responses': sanitized(response['responses'], self.config)}
        atomic_write(self.config.data_root, meta, json_bytes(record))
        atomic_write(self.config.data_root, artifact['path'] + '.json', json_bytes(record))
        return {**record, 'skipped': False}

    def fetch_logs(self, packages):
        self.observe(self.build_ref)
        def fetch(package):
            return {'key': package['key'], **self.fetch_log(self.build_ref, package['key']['arch'], package)}
        with ThreadPoolExecutor(max_workers=self.config.raw['fetch']['log_concurrency']) as executor:
            return list(executor.map(fetch, packages))
