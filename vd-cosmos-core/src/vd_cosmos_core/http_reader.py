"""Bounded, cookie-free urllib reader. All persistence is under data_root."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import ipaddress
import posixpath
import re
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urljoin, urlsplit
from urllib.request import Request, ProxyHandler, HTTPRedirectHandler, HTTPSHandler, build_opener

from .backends import ReportReader, timestamp
from .errors import FlowError
from .export import check_content
from .files import atomic_write, digest, json_bytes, load_json
from .models import BuildRef
from .observation import detail_state, summarize
from .report import parse_report
from .baselines import baseline_revision, apply_rows_coverage


def direct_host(host, rules):
    host = host.lower().rstrip('.')
    for rule in rules:
        rule = rule.lower().strip()
        if '/' in rule:
            try:
                if ipaddress.ip_address(host) in ipaddress.ip_network(rule, strict=False):
                    return True
            except ValueError:
                continue
        else:
            suffix = rule.removeprefix('*.').lstrip('.').rstrip('.')
            if host == suffix or host.endswith('.' + suffix):
                return True
    return False


class Redirects(HTTPRedirectHandler):
    def __init__(self, transport):
        self.transport = transport

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        old, new = urlsplit(req.full_url), urlsplit(newurl)
        if new.hostname != old.hostname:
            raise FlowError(5, 'cross_host_redirect_login_page')
        if new.scheme not in {'http', 'https'} or new.username or new.password:
            raise FlowError(5, 'unsafe_redirect')
        count = getattr(req, '_redirect_count', 0) + 1
        if count > 3:
            raise FlowError(5, 'redirect_limit')
        result = super().redirect_request(req, fp, code, msg, headers, newurl)
        result._redirect_count = count
        self.transport.proxy_request(result)
        return result


class HTTPTransport:
    def __init__(self, config):
        self.config = config
        self.network = config.raw.get('network', {})
        self.context = ssl.create_default_context()
        if self.network.get('ca_file'):
            try:
                self.context.load_verify_locations(cafile=str(config.source(self.network['ca_file'])))
            except (OSError, ssl.SSLError):
                raise FlowError(2, 'invalid_ca_file') from None

    def proxy_request(self, req):
        proxy = self.network.get('proxy')
        if proxy and not direct_host(urlsplit(req.full_url).hostname, self.network.get('no_proxy_hosts', [])):
            parsed = urlsplit(proxy)
            # Request.set_proxy avoids urllib ProxyHandler's environment-based
            # no_proxy bypass even when an explicit proxy was supplied.
            req.set_proxy(parsed.netloc, parsed.scheme)

    def get(self, url, limit, *, truncate=False):
        parsed = urlsplit(url)
        if parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username or parsed.password:
            raise FlowError(4, 'unsafe_url')
        req = Request(url, headers={'Cache-Control': 'no-cache', 'Pragma': 'no-cache',
                                   'User-Agent': self.config.raw['fetch']['user_agent']})
        self.proxy_request(req)
        opener = build_opener(ProxyHandler({}), Redirects(self), HTTPSHandler(context=self.context))
        try:
            try:
                response = opener.open(req, timeout=self.config.raw['fetch']['timeout_s'])
            except HTTPError as error:
                response = error
            with response:
                body = response.read(limit + 1)
                oversized = len(body) > limit
                if oversized and not truncate:
                    raise FlowError(5, 'page_size_limit')
                return {'body': body[:limit], 'status': response.code,
                        'truncated': oversized, 'final_url': response.geturl(),
                        'observed_at': datetime.now(timezone.utc).isoformat()}
        except (OSError, URLError, ValueError):
            raise FlowError(5, 'http_request_failed') from None



class HTTPReportReader(ReportReader):
    capabilities = frozenset({'observe', 'read_packages', 'read_inputs', 'fetch_log'})

    def __init__(self, config, build_id, expected_rows=None):
        if not isinstance(build_id, str) or not re.fullmatch(r'[0-9]+', build_id):
            raise FlowError(2, 'invalid_build_id')
        self.config, self.build_id = config, build_id
        self.cosmos = config.raw['cosmos']
        if not self.cosmos.get('report_root') or not self.cosmos.get('report_path_template'):
            raise FlowError(2, 'http_report_configuration_required')
        if any(not re.fullmatch(r'[A-Za-z0-9_.-]+', arch) for arch in self.cosmos['archs']):
            raise FlowError(2, 'invalid_architecture')
        self.build_ref = BuildRef('cosmos-http', urlsplit(self.cosmos['report_root']).hostname, build_id, 'cosmos')
        self.transport = HTTPTransport(config)
        self.rows = None
        if expected_rows:
            try:
                self.rows = [baseline_revision(line) for line in config.source(expected_rows).read_text().splitlines() if line.strip()]
            except (OSError, UnicodeError):
                raise FlowError(2, 'invalid_expected_rows') from None
            if len(self.rows) != len(set(self.rows)):
                raise FlowError(2, 'invalid_expected_package_set')
        self._observed = None

    def check_ref(self, ref):
        if ref != self.build_ref:
            raise FlowError(6, 'build_identity_mismatch')

    def report_url(self, arch):
        path = self.cosmos['report_path_template'].format(last3=self.build_id[-3:].zfill(3), build_id=self.build_id, arch=arch)
        return self.cosmos['report_root'].rstrip('/') + '/' + path.lstrip('/')

    def _arch(self, arch):
        url = self.report_url(arch)
        response = self.transport.get(url, self.config.raw['fetch']['max_page_bytes'])
        stamp, status = response['observed_at'], response['status']
        if status == 404:
            path = self.cosmos.get('bucket_path_template', 'b{last3}/').format(last3=self.build_id[-3:].zfill(3), build_id=self.build_id)
            index = self.transport.get(self.cosmos['report_root'].rstrip('/') + '/' + path.lstrip('/'), self.config.raw['fetch']['max_page_bytes'])
            if index['status'] == 200:
                return {'arch': arch, 'http_status': 404, 'index_http_status': 200, 'observed_at': stamp,
                        'report_state': '未发布', 'result_state': '未知', 'package_coverage': '未核', 'headers': {}, 'issues': []}
            raise FlowError(5, 'index_unreadable', http_status=404, index_http_status=index['status'])
        if status != 200:
            raise FlowError(5, 'report_http_error', http_status=status)
        data = response['body']
        if not check_content(data, self.config)['allowed']:
            raise FlowError(5, 'credential_pattern_blocked', http_status=status)
        sha = digest(data)
        folder = f'rounds/{self.build_id}/pages/{arch}'
        history_path = self.config.output(folder + '/history.json')
        history = load_json(history_path) if history_path.exists() else []
        stable = bool(history and history[-1]['sha256'] == sha and timestamp(stamp) - timestamp(history[-1]['observed_at']) >= self.config.raw['poll']['interval_s'])
        try:
            report = parse_report(data.decode('utf-8'), arch, self.cosmos, None, stable=stable, source_url=url)
        except UnicodeError:
            raise FlowError(5, 'report_parse_failed', http_status=status) from None
        filename = datetime.fromisoformat(stamp).strftime('%Y%m%dT%H%M%S%fZ') + '-' + sha[:12] + '.html'
        artifact = atomic_write(self.config.data_root, folder + '/' + filename, data)
        record = {'observed_at': stamp, 'sha256': sha, 'path': artifact['path'], 'http_status': status}
        atomic_write(self.config.data_root, history_path, json_bytes((history + [record])[-2:]))
        report.update(observed_at=stamp, http_status=status,
                      evidence={**artifact, 'previous_sha256': history[-1]['sha256'] if history else None})
        if arch == 'armv7l':
            apply_rows_coverage(report, self.rows)
        return report

    def observe(self, build_ref):
        self.check_ref(build_ref)
        if self._observed is not None:
            return self._observed
        reports = {}
        for arch in self.cosmos['archs']:
            try:
                reports[arch] = self._arch(arch)
            except FlowError as error:
                if error.code not in {4, 5}:
                    raise
                reports[arch] = {'arch': arch, 'observation_failed': True, 'headers': {},
                                 'error': error.reason, 'http_status': error.details.get('http_status'),
                                 'observed_at': datetime.now(timezone.utc).isoformat()}
        source = self.cosmos.get('status_source')
        execution, detail_failed = {'state': '未知', 'trust': 'unknown'}, False
        if source:
            try:
                response = self.transport.get(source['url_template'].format(build_id=self.build_id), self.config.raw['fetch']['max_page_bytes'])
                if response['status'] != 200:
                    raise FlowError(5, 'detail_http_error')
                data = response['body']
                blocked = not check_content(data, self.config)['allowed']
                execution = detail_state(data, source)
                if not check_content(json_bytes(execution), self.config)['allowed']:
                    execution = {'state': '未知', 'trust': 'unknown', 'basis': 'sensitive_status_element_redacted'}
                execution.update(sha256=digest(data), observed_at=response['observed_at'], http_status=response['status'],
                                 raw_retained=False, retention_note='原文未保留（命中凭据模式）' if blocked else '原文未保留')
            except (FlowError, UnicodeError, ValueError):
                detail_failed = True
        self._observed = summarize(build_ref, self.cosmos, reports, execution, backend=self.__class__.__name__, detail_failed=detail_failed)
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
        root, target = urlsplit(report_url), urlsplit(url)
        directory = posixpath.dirname(unquote(root.path)).rstrip('/') + '/'
        path = posixpath.normpath(unquote(target.path))
        if ((root.scheme, root.hostname, root.port) != (target.scheme, target.hostname, target.port)
                or not path.startswith(directory) or not package.get('log_url') or target.username or target.password):
            raise FlowError(4, 'log_url_outside_build', todo={'reason': 'log_url_outside_build', 'key': package['key']})
        nvr = posixpath.basename(posixpath.dirname(path))
        if not re.fullmatch(r'[A-Za-z0-9_+.-]+', nvr) or nvr in {'.', '..'}:
            raise FlowError(4, 'unsafe_log_name', todo={'reason': 'unsafe_log_name', 'key': package['key']})
        relative = f'rounds/{self.build_id}/logs/{arch}/{nvr}/log.txt'
        destination, meta = self.config.output(relative), self.config.output(relative + '.json')
        if destination.exists() and meta.exists():
            record = load_json(meta)
            if record.get('url_sha256') == digest(url.encode()) and digest(destination.read_bytes()) == record['sha256']:
                return {**record, 'skipped': True}
        try:
            response = self.transport.get(url, self.config.raw['fetch']['max_log_bytes'], truncate=True)
        except FlowError as error:
            if error.reason in {'cross_host_redirect_login_page', 'unsafe_redirect'}:
                raise FlowError(4, 'log_redirect_outside_build',
                                todo={'reason': 'log_redirect_outside_build', 'key': package['key']}) from None
            raise
        if response['status'] != 200:
            raise FlowError(5, 'log_http_error')
        final = urlsplit(response['final_url'])
        if ((final.scheme, final.hostname, final.port) != (root.scheme, root.hostname, root.port)
                or not posixpath.normpath(unquote(final.path)).startswith(directory)):
            raise FlowError(4, 'log_redirect_outside_build', todo={'reason': 'log_redirect_outside_build', 'key': package['key']})
        try:
            allowed = check_content(response['body'], self.config)['allowed']
        except FlowError:
            allowed = False
        artifact = atomic_write(self.config.data_root, relative, response['body'])
        record = {**artifact, 'truncated': response['truncated'], 'export_allowed': allowed,
                  'export_note': '可导出' if allowed else '禁止导出', 'url_sha256': digest(url.encode())}
        atomic_write(self.config.data_root, meta, json_bytes(record))
        return {**record, 'skipped': False}

    def fetch_logs(self, packages):
        def fetch(package):
            return {'key': package['key'], **self.fetch_log(self.build_ref, package['key']['arch'], package)}
        with ThreadPoolExecutor(max_workers=self.config.raw['fetch']['log_concurrency']) as executor:
            return list(executor.map(fetch, packages))
