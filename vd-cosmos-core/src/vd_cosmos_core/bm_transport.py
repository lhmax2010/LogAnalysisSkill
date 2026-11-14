"""Anonymous management session, memory only, fixed GET paths and same-host paging."""
from email.utils import parsedate_to_datetime
from http.cookiejar import CookieJar, DefaultCookiePolicy
import http.client
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPCookieProcessor, Request
import re

from .errors import FlowError
from .transport import Deadline, HTTPTransport


class HostCookies(DefaultCookiePolicy):
    def __init__(self, host):
        super().__init__(); self.host = host

    def set_ok(self, cookie, request):
        return (urlsplit(request.full_url).netloc == self.host and
                cookie.domain.lstrip('.') == urlsplit('https://' + self.host).hostname and
                super().set_ok(cookie, request))

    def return_ok(self, cookie, request):
        return urlsplit(request.full_url).netloc == self.host and super().return_ok(cookie, request)


class AnonymousTransport(HTTPTransport):
    def __init__(self, config):
        super().__init__(config)
        self.host = config.raw['cosmos']['bm_host']
        self.jar = CookieJar(policy=HostCookies(self.host))

    def close(self):
        self.jar.clear()

    def read(self, url, *, history=False):
        path = '/history/' + self.config.raw['cosmos']['bm_config_id']
        deadline = Deadline(self.config.raw['fetch']['deadline_s'], self.config.raw['fetch']['timeout_s'])
        started, monotonic = time.time(), time.monotonic()
        for hop in range(5):
            u = urlsplit(url)
            if (u.scheme != 'https' or u.netloc != self.host or u.username or u.password or u.fragment
                    or not re.fullmatch(r'/(?:history|overview)/\d+|/build/\d+(?:/variables)?', u.path)
                    or (u.query and (not history or u.path != path))):
                raise FlowError(4, 'bm_url_refused')
            response = None
            try:
                req = Request(url, headers={'User-Agent': self.config.raw['fetch']['user_agent'], 'Cache-Control': 'no-cache'})
                # Management reads always use direct connections, never an authenticated proxy.
                opener = self.opener(deadline); opener.add_handler(HTTPCookieProcessor(self.jar))
                try: response = opener.open(req, timeout=deadline.timeout())
                except HTTPError as error: response = error
                if 300 <= response.code < 400:
                    target = urljoin(url, response.headers.get('Location', ''))
                    p = urlsplit(target)
                    if not history or p.scheme != 'https' or p.netloc != self.host or p.path != path or p.fragment or p.username or p.password:
                        raise FlowError(5, 'bm_redirect_refused')
                    url = target; continue
                if response.code != 200:
                    raise FlowError(5, 'bm_http_status', status=response.code)
                body = bytearray(); limit = self.config.raw['fetch']['max_page_bytes']
                while len(body) <= limit:
                    deadline.timeout()
                    chunk = response.read1(min(65536, limit + 1 - len(body)))
                    if not chunk: break
                    body.extend(chunk)
                length = response.headers.get('Content-Length')
                if len(body) > limit:
                    raise FlowError(5, 'bm_page_size_limit')
                if (length is not None and (not length.isdecimal() or int(length) != len(body))
                        or length is None and not response.chunked
                        or response.chunked and not getattr(response, 'strict_complete', False)):
                    raise FlowError(5, 'bm_incomplete_body')
                finished = time.time(); elapsed = time.monotonic() - monotonic
                date = response.headers.get('Date')
                sample = clock_sample(date, started, finished, elapsed)
                return bytes(body), sample
            except FlowError:
                raise
            except (OSError, URLError, http.client.HTTPException, ValueError):
                raise FlowError(5, 'bm_read_failed') from None
            finally:
                if response is not None: response.close()
        raise FlowError(5, 'bm_redirect_limit')


def clock_sample(date, started, finished, elapsed):
    sample = {'sent_at': started, 'received_at': finished, 'rtt_s': elapsed, 'valid': False}
    try:
        server = parsedate_to_datetime(date).timestamp()
    except (TypeError, ValueError, OverflowError):
        return sample
    sample.update(server_time=server, offset_s=server - (started + finished) / 2, error_s=elapsed / 2,
                  valid=0 <= elapsed <= 10 and abs(finished - started - elapsed) <= 60)
    return sample
