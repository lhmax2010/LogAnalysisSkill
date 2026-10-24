"""Loopback-only HTTP fixtures; never uses real services."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import threading
import time
from urllib.parse import urlsplit
from helpers import CORE


class FixtureServer:
    def __init__(self, root):
        self.root = Path(root)
        self.fixture = self.root / 'saved';shutil.copytree(CORE / 'fixtures/real_format', self.fixture)
        shutil.copyfile(self.fixture / 'detail.html', self.fixture / 'probe_3bed7e8c.html')
        self.routes, self.requests = {}, []
        self.active_logs = self.max_active_logs = 0
        self.lock = threading.Lock()
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_GET(self):
                path = urlsplit(self.path).path
                with owner.lock:
                    owner.requests.append({'path': path, 'request_target': self.path, 'headers': dict(self.headers)})
                route = owner.routes.get(path)
                if route is None:
                    if path.endswith('/log.txt'):
                        route = (200, b'fixture compiler log\n', {}, 0)
                    elif path.endswith('/'):
                        route = (200, b'<html>directory</html>', {}, 0)
                    elif path.startswith('/build/'):
                        route = (200, (owner.fixture / 'detail.html').read_bytes(), {}, 0)
                    else:
                        route = (404, b'not published', {}, 0)
                if callable(route):
                    route = route()
                status, body, headers, delay = route
                if path.endswith('/log.txt'):
                    with owner.lock:
                        owner.active_logs += 1
                        owner.max_active_logs = max(owner.max_active_logs, owner.active_logs)
                try:
                    if delay:time.sleep(delay)
                    self.send_response(status)
                    for key, value in headers.items():self.send_header(key, value)
                    self.send_header('Content-Length', str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError):
                    pass
                finally:
                    if path.endswith('/log.txt'):
                        with owner.lock:owner.active_logs -= 1

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.server.daemon_threads = True
        self.url = 'http://127.0.0.1:' + str(self.server.server_port)
        self.thread = threading.Thread(target=lambda: self.server.serve_forever(poll_interval=.01), daemon=True)
        self.thread.start()
        self.build_id = '19091860'
        for arch in ['armv7l', 'x86_64']:
            self.routes[self.report_path(arch)] = (200, (self.fixture / ('report_' + arch + '.html')).read_bytes(), {}, 0)
        config = json.loads((CORE / 'config.sample.json').read_text())
        config['data_root'] = str(self.root / 'owned')
        config['cosmos']['report_root'] = self.url + '/reports/'
        config['cosmos']['status_source']['url_template'] = self.url + '/build/{build_id}'
        config['poll']['interval_s'] = .03
        config['fetch']['timeout_s'] = .2
        config['fetch']['max_log_bytes'] = 100
        config['fetch']['log_concurrency'] = 2
        config['budget']['disk_warning_bytes'] = 0
        self.config_path = self.root / 'config.json'
        self.config_path.write_text(json.dumps(config))

    def report_path(self, arch):
        return '/reports/b860/19091860/html/Build_Report_' + arch + '/index.html'

    def close(self):
        self.server.shutdown();self.server.server_close();self.thread.join(2)
