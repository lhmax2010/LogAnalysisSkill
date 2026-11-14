"""Bounded no-login lookup with snapshot ordering and anchored coverage evidence."""
import copy
import json
import time
from pathlib import Path

from . import bm_pages
from .bm_transport import AnonymousTransport
from .errors import FlowError
from .export import check_content
from .files import confined, json_bytes


class FixtureTransport:
    """Disk fixtures are inputs, never captured server bodies or sessions."""
    def __init__(self, path):
        self.path = Path(path).resolve(); self.data = json.loads(self.path.read_text())
        self.counts = {}

    def read(self, url, *, history=False):
        entries = self.data['pages'].get(url)
        if not entries: raise FlowError(5, 'fixture_page_missing')
        if not isinstance(entries, list): entries = [entries]
        n = self.counts.get(url, 0); self.counts[url] = n + 1
        entry = entries[min(n, len(entries) - 1)]
        if 'error' in entry: raise FlowError(5, entry['error'])
        return confined(self.path.parent, entry['file']).read_bytes(), copy.deepcopy(entry['clock'])

    def reset(self): pass
    def close(self): pass


class Reader:
    def __init__(self, config, *, transport=None, cache=None, sleep=time.sleep):
        self.config = config; self.c = config.raw['cosmos']
        self.transport = transport or AnonymousTransport(config)
        self.cache = copy.deepcopy(cache or {})
        self.sleep = sleep; self.samples = []; self.detail_count = 0
        self.current_details = {}

    def close(self): self.transport.close()

    def url(self, path): return 'https://' + self.c['bm_host'] + path

    def get(self, path, *, history=False):
        url = path if path.startswith('https://') else self.url(path)
        body, sample = self.transport.read(url, history=history)
        self.samples.append(sample)
        return body

    def safe(self, value):
        if not check_content(json_bytes(value), self.config)['allowed']:
            raise FlowError(4, 'bm_parsed_credential_blocked')
        return value

    def overview(self):
        return self.safe(bm_pages.listing(self.get('/overview/' + self.c['bm_config_id']), self.config, 'overview'))

    def detail(self, build, *, fresh=False):
        b = str(build)
        if not fresh and b in self.current_details: return self.current_details[b]
        if not fresh and b in self.cache: return copy.deepcopy(self.cache[b])
        if self.detail_count >= self.c['bm_lookup_detail_max']:
            raise FlowError(6, 'bm_detail_budget')
        self.sleep(self.c['bm_scan_interval_s']); self.detail_count += 1
        value = self.safe(bm_pages.detail(self.get('/build/' + b), self.config, b))
        self.current_details[b] = value
        if value['ended'] and value['hub_id'] and not value['conflict']:
            self.cache[b] = copy.deepcopy(value)
        return value

    def variables(self, build, names):
        return self.safe(bm_pages.variables(self.get('/build/' + str(build) + '/variables'), self.config, str(build), names))

    def clock_valid(self):
        return bool(self.samples and all(s.get('valid') for s in self.samples)
                    and max(s['offset_s'] for s in self.samples) - min(s['offset_s'] for s in self.samples) <= 60)

    def scan(self, *, hub_id=None, since=None, previous_anchor=None, account_only=False, rerun=False):
        """All network I/O happens here, with no state-store lock held."""
        self.current_details = {}
        hub_id = str(hub_id) if hub_id is not None else None
        issues = []; failures = []; details = {}; rows = {}; groups = []; reads = []; page_evidence = []
        try: overview = self.overview()
        except FlowError as e:
            if e.code == 4: raise
            overview = {'rows': []}; issues.append(e.reason); failures.append(e.code)
        overview_rows = {r['build_id']: r for r in overview['rows']}
        overview_hubs = {r['build_id']: r['hub_id'] for r in overview['rows'] if r.get('hub_id')}
        for r in overview['rows']: rows[r['build_id']] = r

        def read_detail(b):
            if b in details: return details[b]
            quick = overview_rows.get(b)
            if (rerun and quick and quick.get('hub_id')
                    and quick.get('process_status') in {'RUNNING_BUILD', 'QUEUED', 'WAITING'}):
                # List evidence is sufficient to keep watching a live run. It never
                # supplies strong identity for a claim and is never cached.
                value = {'build_id': b, 'hub_id': quick['hub_id'], 'identity': 'overview_only',
                         'config_id': self.c['bm_config_id'], 'ended': False,
                         'state': 'running_or_queued', 'start_time': rows[b].get('start_time'),
                         'end_time': None, 'conflict': False, 'relation': 'overview'}
                details[b] = value
                return value
            try:
                d = self.detail(b); reads.append(b)
                if b in overview_hubs and d['hub_id'] != overview_hubs[b]: d = dict(d, conflict=True, relation='冲突')
                details[b] = d
                return d
            except FlowError as e:
                if e.code == 4: raise
                issues.append(e.reason); failures.append(e.code)
                return None

        def pages(stop_anchor=None):
            url = '/history/' + self.c['bm_config_id']; seen = set(); previous = None
            anchor = None; reached = False; reason = None; snapshots = []; chronological = None
            for _ in range(self.c['bm_history_max_pages']):
                try: page = bm_pages.listing(self.get(url, history=True), self.config, 'history')
                except FlowError as e:
                    if e.code == 4: raise
                    issues.append(e.reason); failures.append(e.code); reason = '扫描覆盖不足'; break
                page_evidence.append({'first': page['first'], 'last': page['last'], 'total': page['total'],
                                      'read_at': self.samples[-1]['received_at'], 'topup_to': stop_anchor})
                ids = [r['build_id'] for r in page['rows']]
                if not ids: issues.append('empty_history'); break
                if anchor is None:
                    anchor = {'build_id': ids[0], 'read_at': self.samples[-1]['received_at']}
                    if page['first'] != 1: issues.append('history_not_first_page')
                if any(int(a) <= int(b) for a, b in zip(ids, ids[1:])):
                    issues.append('history_reordered')
                overlap = seen.intersection(ids)
                new = [b for b in ids if b not in seen]
                if previous:
                    if page['first'] <= previous['first']: issues.append('history_page_repeated')
                    if not overlap and page['total'] < previous['total']: issues.append('history_gap')
                    if new and seen and int(new[0]) >= min(map(int, seen)): issues.append('history_reordered')
                for r in page['rows']:
                    if r['start_time'] is not None:
                        if chronological is not None and r['build_id'] not in seen and r['start_time'] > chronological:
                            issues.append('history_time_reordered')
                        if r['build_id'] not in seen: chronological = r['start_time']
                    if r['build_id'] not in rows: rows[r['build_id']] = r
                    elif rows[r['build_id']]['start_time'] is None:
                        rows[r['build_id']] = dict(rows[r['build_id']], start_time=r['start_time'])
                seen.update(ids); previous = page
                first = read_detail(ids[0]) if hub_id else None
                snapshots.append({'rows': page['rows'], 'first_hub': first.get('hub_id') if first else None})
                if stop_anchor and str(stop_anchor) in seen:
                    reached = True; break
                if not stop_anchor:
                    if hub_id and first and first['hub_id'] and int(first['hub_id']) < int(hub_id) - self.c['hub_id_slack']:
                        reached = True; break
                    if since is not None and page['rows'][-1]['start_time'] is not None and page['rows'][-1]['start_time'] < since:
                        reached = True; break
                if not page['next']:
                    reason = '窗口外（列表已到底，早期构建可能已被清理）'; break
                url = page['next']
            else: reason = '窗口外（翻页上限）'
            if stop_anchor and not reached: issues.append('anchor_not_reached')
            return snapshots, anchor, reached, reason

        groups, anchor, reached, reason = pages()
        if anchor:
            if hasattr(self.transport, 'reset'): self.transport.reset()
            else: self.transport.close()  # discard anonymous session; restart at first page
            top, new_anchor, connected, _ = pages(anchor['build_id'])
            groups = top + groups
            if connected and new_anchor: anchor = new_anchor
        if previous_anchor and str(previous_anchor['build_id']) not in rows:
            # Resume needs the old anchor, even when the time/number stop was reached earlier.
            if hasattr(self.transport, 'reset'): self.transport.reset()
            else: self.transport.close()
            extra, _, connected, _ = pages(previous_anchor['build_id'])
            groups += extra
            if not connected: issues.append('previous_anchor_lost')
        # Three passes share this exact snapshot: first rows already read during paging,
        # then groups in the H window, then all remaining groups. Never navigate backwards.
        if hub_id:
            groups.sort(key=lambda g: not (g['first_hub'] is not None and abs(int(g['first_hub']) - int(hub_id)) <= self.c['hub_id_slack']))
        ordered = [r for g in groups for r in g['rows']]
        quick = sorted(overview['rows'], key=lambda r: r.get('hub_id') != hub_id) if hub_id else overview['rows']
        ordered = quick + ordered
        visited = set()
        for row in ordered:
            b = row['build_id']
            if b in visited: continue
            visited.add(b)
            if since is not None and row['start_time'] is not None and row['start_time'] < since: continue
            if account_only and not row['version'].startswith('[' + self.config.raw['submit']['account'] + ']'): continue
            read_detail(b)
        if not self.clock_valid(): issues.append('clock_unverified')
        pending = sorted(b for b, r in rows.items() if
                         (since is None or r['start_time'] is None or r['start_time'] >= since)
                         and (not account_only or r['version'].startswith('[' + self.config.raw['submit']['account'] + ']'))
                         and (b not in details or not details[b].get('hub_id')))
        if len(pending) > self.c['bm_pending_max']: issues.append('pending_limit')
        relation_conflicts = [d['build_id'] for d in details.values() if d['conflict']]
        candidates = [d for d in details.values() if d.get('hub_id') == hub_id and d['config_id'] == self.c['bm_config_id'] and not d['conflict']] if hub_id else []
        status = '冲突' if relation_conflicts or len(candidates) > 1 else '唯一' if candidates else '未定位'
        coverage = bool(reached and not issues and not pending)
        if hub_id:
            result_reason = ('页面无法识别' if any(x in issues for x in ('bm_page_unrecognized', 'bm_identity_mismatch', 'bm_table_unrecognized', 'bm_summary_unrecognized')) else
                             '扫描覆盖不足' if issues else '可能排队过久、已被清理或超出翻页上限') if not candidates else None
        else:
            result_reason = '当前保留记录中尚未出现' if coverage else reason or '扫描覆盖不足'
        exit_code = (5 if 5 in failures else 6) if failures and not details else 0
        return self.safe({'exit_code': exit_code, 'result': status, 'reason': result_reason, 'candidates': candidates,
            'candidate_only': True, 'coverage': coverage, 'coverage_scope': '当前保留记录中',
            'history_retention': '未核验', 'uniqueness_proven': False if hub_id else coverage,
            'uniqueness_note': '唯一性未覆盖' if hub_id or not coverage else '当前范围内',
            'anchor': anchor, 'rows': rows, 'details': details, 'pending': pending,
            'issues': sorted(set(issues)), 'conflicts': relation_conflicts, 'detail_read_order': reads,
            'clock': self.samples[-1] if self.samples else None, 'cache': self.cache, 'pages': page_evidence,
            'limitation': '历史清理可能造成漏观测'} )

    def lookup(self, hub_id, *, since=None):
        scan = self.scan(hub_id=hub_id, since=since)
        for candidate in scan['candidates']:
            try:
                values = self.variables(candidate['build_id'], {'PACKAGE_LIST'})
                text = values['PACKAGE_LIST']['value']
                candidate.update(package_list_count=len(bm_pages.parse_list(text, self.c['branch_markers'])),
                                 package_list_sha256=bm_pages.base_digest(text, self.config),
                                 version=scan['rows'].get(candidate['build_id'], {}).get('version'))
            except (FlowError, KeyError):
                candidate['inputs'] = '未核验'; scan['coverage'] = False
        return scan
