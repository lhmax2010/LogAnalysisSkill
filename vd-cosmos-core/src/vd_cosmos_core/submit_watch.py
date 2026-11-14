"""Request observation lifecycle: one runner, independent heartbeat, short merge locks."""
import threading
import time

from .commands import Category, CommandContext
from .errors import FlowError
from .locks import OperationLock
from .state import EventStore
from .submit_claim import collect, merge_scan
from .submit_model import read

CONTEXT = CommandContext('submit.watch', Category.OBSERVE)


def heartbeat(config, request_id, *, now=None):
    now = time.time() if now is None else now
    with EventStore(config.data_root) as store:
        for _ in range(4):
            head = store.head()
            previous = [e for e in store.events(kinds=['submit_heartbeat']) if e['request_id'] == request_id]
            last = previous[-1]['payload']['at'] if previous else None
            if last is None:
                last = read(config, request_id)['observation']['created_at']
            payload = {'at': now, 'interrupted': now - last > config.raw['poll']['watch_interval_s'] * 3,
                       'gap_from': last if now - last > config.raw['poll']['watch_interval_s'] * 3 else None}
            try:
                store.append(CONTEXT, 'submit_heartbeat', payload, head, request_id=request_id)
                return payload
            except FlowError as error:
                if error.reason not in {'state_busy', 'stale_head'}: raise
        raise FlowError(6, 'heartbeat_state_busy')


def step(config, request_id, reader, *, now=None):
    r = read(config, request_id)
    if not r.get('observation'): raise FlowError(6, 'observation_task_missing')
    if r.get('observation_complete') or r['status'] == 'abandoned': return r
    reader.cache.update(r.get('cache', {}))
    scan = collect(config, r, reader)
    try: return merge_scan(config, r, scan, CONTEXT, now=now)
    except FlowError as error:
        if error.reason == 'request_version_changed':
            return dict(read(config, request_id), scan_discarded=True)
        raise


def run(config, request_id, reader_factory, *, stop=None, max_scans=None, on_scan=None):
    stop = stop or threading.Event(); interval = config.raw['poll']['watch_interval_s']
    errors = []
    with OperationLock(config.data_root, 'observation', request_id):
        r = read(config, request_id)
        if not r.get('observation'): raise FlowError(6, 'observation_task_missing')
        heartbeat(config, request_id)
        def pulse():
            while not stop.wait(interval):
                try: heartbeat(config, request_id)
                except FlowError as error:
                    errors.append(error); stop.set(); return
        thread = threading.Thread(target=pulse, daemon=True); thread.start()
        count = 0
        try:
            while not stop.is_set():
                r = read(config, request_id)
                if r.get('observation_complete') or r['status'] == 'abandoned': break
                delay = max(0, r.get('next_scan_at', 0) - time.time())
                if stop.wait(delay): break
                reader = reader_factory(r.get('cache', {}))
                try: r = step(config, request_id, reader)
                finally: reader.close()
                count += 1
                if on_scan: on_scan(r)
                if max_scans and count >= max_scans: break
                # Version conflicts retry on the next step, never merge stale evidence.
                if r.get('scan_discarded'): continue
                if stop.wait(interval): break
            if errors: raise errors[0]
            return r
        finally:
            stop.set(); thread.join(timeout=min(interval + 1, 5))
