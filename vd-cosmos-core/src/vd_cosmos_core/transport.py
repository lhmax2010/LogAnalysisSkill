"""Bounded HTTP requests; no cookies, explicit proxy and pre-request redirects."""
from datetime import datetime, timezone
import http.client
import io
import ipaddress
import posixpath
import queue
import re
import socket
import ssl
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urljoin, urlsplit
from urllib.request import (Request, ProxyHandler, HTTPRedirectHandler, HTTPHandler,
                            HTTPSHandler, build_opener)
from .errors import FlowError
from .files import digest


def now():
    return datetime.now(timezone.utc).isoformat()


def origin(url):
    parsed = urlsplit(url)
    return parsed.scheme.lower(), parsed.hostname, parsed.port or (443 if parsed.scheme == 'https' else 80)


def normalized_path(path):
    return posixpath.normpath(unquote(path))


def log_allowed(url, report_url):
    target = urlsplit(url)
    directory = posixpath.dirname(normalized_path(urlsplit(report_url).path)).rstrip('/') + '/'
    return (origin(url) == origin(report_url) and not target.username and not target.password
            and normalized_path(target.path).startswith(directory))


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


class Deadline:
    def __init__(self, duration, idle):
        self.end = time.monotonic() + duration
        self.idle = idle
        self.network = {}

    def timeout(self):
        remaining = self.end - time.monotonic()
        if remaining <= 0:
            raise FlowError(5, 'deadline')
        return min(remaining, self.idle)


class TimedRaw(io.RawIOBase):
    def __init__(self, sock, deadline):
        self.sock, self.deadline = sock, deadline
        self.source = sock.makefile('rb', buffering=0)

    def readable(self):
        return True

    def readinto(self, buffer):
        self.sock.settimeout(self.deadline.timeout())
        return self.source.readinto(buffer)

    def close(self):
        self.source.close()
        super().close()


class TimedSocket:
    def __init__(self, sock, deadline):
        self.sock, self.deadline = sock, deadline

    def __getattr__(self, name):
        return getattr(self.sock, name)

    def makefile(self, mode, buffering=None):
        if mode != 'rb':
            raise ValueError('read-only HTTP stream')
        return io.BufferedReader(TimedRaw(self.sock, self.deadline))

    def sendall(self, data, flags=0):
        self.sock.settimeout(self.deadline.timeout())
        return self.sock.sendall(data, flags)


def connection(address, deadline, source_address=None):
    # DNS is also bounded. A stuck platform resolver cannot hold the caller's
    # round lock past deadline; its daemon thread owns no request/socket.
    result = queue.Queue(maxsize=1)
    def resolve():
        try:
            result.put(socket.getaddrinfo(*address, type=socket.SOCK_STREAM))
        except OSError as error:
            result.put(error)
    threading.Thread(target=resolve, daemon=True).start()
    try:
        addresses = result.get(timeout=deadline.timeout())
    except queue.Empty:
        raise FlowError(5, 'deadline' if time.monotonic() >= deadline.end else 'timeout') from None
    if isinstance(addresses, OSError):
        raise FlowError(5, 'dns') from None
    last = None
    for family, kind, proto, _, target in addresses:
        sock = socket.socket(family, kind, proto)
        try:
            sock.settimeout(deadline.timeout())
            if source_address:
                sock.bind(source_address)
            sock.connect(target)
            deadline.network = {'peer_ip': sock.getpeername()[0], 'local_ip': sock.getsockname()[0]}
            return TimedSocket(sock, deadline)
        except OSError as error:
            last = error
            sock.close()
        except FlowError:
            sock.close()
            raise
    if last:
        raise last
    raise FlowError(5, 'connect')


class StrictResponse(http.client.HTTPResponse):
    def _read_next_chunk_size(self):
        line = self.fp.readline(65537)
        if len(line) > 65536 or not re.fullmatch(rb'[0-9a-fA-F]+(?:;[^\r\n]*)?\r\n', line):
            raise http.client.IncompleteRead(b'')
        return int(line.split(b';', 1)[0].strip(), 16)

    def _read_and_discard_trailer(self):
        total = 0
        while True:
            line = self.fp.readline(65537)
            total += len(line)
            if line == b'\r\n':
                self.strict_complete = True
                return
            if total > 65536 or not re.fullmatch(rb"[!#$%&'*+.^_`|~0-9A-Za-z-]+:[^\r\n]*\r\n", line):
                raise http.client.IncompleteRead(b'')

    def _get_chunk_left(self):
        if self.chunk_left == 0:
            if self._safe_read(2) != b'\r\n':
                raise http.client.IncompleteRead(b'')
            self.chunk_left = None
        return super()._get_chunk_left()


def not_a_log(body, content_type=''):
    prefix = body[:16384].lstrip().lower()
    html = prefix.startswith((b'<!doctype html', b'<html', b'<head', b'<form'))
    if not html and not ('text/html' in content_type.lower() and prefix.startswith(b'<')):
        return False
    return bool(re.search(rb'<form\b|<input\b[^>]*type\s*=\s*[\x22\x27]?password|<title[^>]*>[^<]*(?:login|sign in|proxy|authentication|access denied)', prefix))


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None


class HTTPTransport:
    def __init__(self, config):
        self.config, self.network = config, config.raw.get('network', {})
        self.context = ssl.create_default_context()
        if self.network.get('ca_file'):
            try:
                self.context.load_verify_locations(cafile=str(config.source(self.network['ca_file'])))
            except (OSError, ssl.SSLError):
                raise FlowError(2, 'invalid_ca_file') from None
        self.requests = []

    def proxy_request(self, request):
        proxy = self.network.get('proxy')
        if proxy and not direct_host(urlsplit(request.full_url).hostname, self.network.get('no_proxy_hosts', [])):
            parsed = urlsplit(proxy)
            request.set_proxy(parsed.netloc, parsed.scheme)

    def opener(self, deadline):
        class HTTPConnection(http.client.HTTPConnection):
            response_class = StrictResponse
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._create_connection = lambda address, timeout=None, source_address=None: connection(address, deadline, source_address)

        class HTTPSConnection(http.client.HTTPSConnection):
            response_class = StrictResponse
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._create_connection = lambda address, timeout=None, source_address=None: connection(address, deadline, source_address)

            def connect(self):
                http.client.HTTPConnection.connect(self)
                self.sock.settimeout(deadline.timeout())
                target = self._tunnel_host or self.host
                self.sock = TimedSocket(self._context.wrap_socket(self.sock, server_hostname=target), deadline)

        class HTTP(HTTPHandler):
            def http_open(self, request):
                return self.do_open(HTTPConnection, request)

        class HTTPS(HTTPSHandler):
            def https_open(self, request):
                return self.do_open(HTTPSConnection, request, context=self._context)

        return build_opener(ProxyHandler({}), NoRedirect(), HTTP(), HTTPS(context=self.context))

    def get(self, url, limit, *, truncate=False, report_url=None):
        deadline = Deadline(self.config.raw['fetch']['deadline_s'], self.config.raw['fetch']['timeout_s'])
        redirects = 0
        chain = []
        while True:
            parsed = urlsplit(url)
            if parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username or parsed.password:
                raise FlowError(4, 'unsafe_url')
            evidence = {'http_status': None, 'Date': None, 'Last-Modified': None, 'ETag': None,
                        'Content-Length': None, 'actual_bytes': 0, 'sha256': digest(b''), 'started_at': now()}
            body = bytearray()
            response = None
            try:
                req = Request(url, headers={'Cache-Control': 'no-cache', 'Pragma': 'no-cache',
                                            'User-Agent': self.config.raw['fetch']['user_agent']})
                self.proxy_request(req)
                try:
                    response = self.opener(deadline).open(req, timeout=deadline.timeout())
                except HTTPError as error:
                    response = error
                evidence['http_status'] = response.code
                for key in ('Date', 'Last-Modified', 'ETag', 'Content-Length', 'Content-Type', 'Transfer-Encoding'):
                    evidence[key] = response.headers.get(key)
                if 300 <= response.code < 400:
                    next_url = urljoin(url, response.headers.get('Location', ''))
                    target = urlsplit(next_url)
                    evidence['location'] = {'host': target.hostname, 'path': target.path}
                    if report_url is None:
                        raise FlowError(5, 'redirect_refused')
                    if not response.headers.get('Location') or not log_allowed(next_url, report_url) or redirects >= 3:
                        raise FlowError(4, 'log_redirect_outside_build', todo={'reason': 'log_url_outside_build'})
                    redirects += 1
                    url = next_url
                    continue
                # read1 performs at most one raw read. TimedRaw adjusts the socket
                # before *each* receive, including chunk/header framing reads.
                while len(body) <= limit:
                    deadline.timeout()
                    chunk = response.read1(min(65536, limit + 1 - len(body)))
                    if not chunk:
                        break
                    body.extend(chunk)
                oversized = len(body) > limit
                if oversized and not truncate:
                    raise FlowError(5, 'page_size_limit')
                if not oversized:
                    length = evidence['Content-Length']
                    if length is not None and (not length.isdecimal() or int(length) != len(body)):
                        raise FlowError(5, 'incomplete_body')
                    if getattr(response, 'chunked', False) and not getattr(response, 'strict_complete', False):
                        raise FlowError(5, 'incomplete_body')
                verifiable = (evidence['Content-Length'] is not None or getattr(response, 'chunked', False))
                if not verifiable and not truncate:
                    raise FlowError(5, 'incomplete_body')
                if truncate and response.code == 200 and not_a_log(bytes(body), evidence.get('Content-Type') or ''):
                    raise FlowError(5, 'not_a_log')
                return {'body': bytes(body[:limit]), 'status': response.code, 'truncated': oversized,
                        'transfer_complete': not oversized and verifiable, 'final_url': url, 'observed_at': now(), 'response': evidence,
                        'responses': chain}
            except (FlowError, OSError, URLError, http.client.HTTPException, ValueError) as error:
                underlying = error.reason if isinstance(error, URLError) else error
                if isinstance(error, FlowError):
                    reason, code, details = error.reason, error.code, error.details
                else:
                    details, code = {}, 5
                    reason = ('tls_verify' if isinstance(underlying, ssl.SSLCertVerificationError) else
                              'dns' if isinstance(underlying, socket.gaierror) else
                              ('deadline' if time.monotonic() >= deadline.end else 'timeout') if isinstance(underlying, TimeoutError) else
                              'incomplete_body' if isinstance(underlying, http.client.HTTPException) or response is not None else 'connect')
                evidence['failure'] = reason
                raise FlowError(code, reason, **{**details, 'http_status': evidence['http_status'], 'response': evidence, 'responses': chain}) from None
            finally:
                evidence.update(deadline.network)
                evidence.update(actual_bytes=len(body), sha256=digest(body), finished_at=now())
                chain.append(evidence)
                self.requests.append(evidence)
                if response is not None:
                    response.close()
