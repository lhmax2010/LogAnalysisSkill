"""Synthetic pages reproducing recon15/16/17/18/21/22 structure, never live data."""
from html import escape
import copy
import time
from urllib.parse import urlsplit
from vd_cosmos_core.errors import FlowError

BASE = '//example/tree/product/[INT]/packages/foo/...@100\n'
STAMP = 1792216800.0
DATE = '2026-10-17 15:00:00'


def detail(b='900', h='500', *, state='failed', config='4362', hub_host='hub.example.invalid', pair=None,
           begin=DATE, duration='1 hour', variables=None):
    hub = '' if h is None else f'♦ Hub Link : <a href="https://{hub_host}/build/{h}">https://{hub_host}/build/{h}</a><br>'
    promotion = '' if pair is None else f'<span title="Promoted to build 700">UPDATE_BUILDINFO: [{pair}]</span>'
    page = (f'<div class="build-header"><a href="/overview/{config}">configuration</a>'
            f'<a href="/build/{b}" title="Build is {state}">{b}</a>{promotion}<br>{hub}</div>'
            '<h2>Summary</h2><table><tr><th>Id</th><th>Status</th><th>Begin Date</th><th>Duration</th><th>Triggered By</th></tr>'
            f'<tr><td>{b}</td><td>{state}</td><td>{begin}</td><td>{duration}</td><td>Build_Runner</td></tr></table>')
    if variables is not None:
        page += variable_table(variables)
    return page.encode()


def variable_table(values):
    return ('<table><thead><tr><th>Name</th><th>Display Name</th><th>Value</th></tr></thead><tbody>' +
            ''.join(f'<tr><td>{escape(k)}</td><td>Display label only</td><td><pre>{escape(v)}</pre></td></tr>'
                    for k, v in values.items()) + '</tbody></table>')


def history(ids, *, first=1, total=None, next_url=None, versions=None, begin=DATE, running=False):
    total = total if total is not None else len(ids)
    text = f'<span>Showing {first} to {first + len(ids) - 1} of {total}</span>'
    text += '<table><tr><th></th><th>Version</th><th>Master Node</th><th>Begin Date</th><th>Duration</th><th>Triggered By</th></tr>'
    for b in ids:
        version = (versions or {}).get(str(b), '[fixture-user] example-build')
        text += f'<tr><td><a href="/build/{b}">{b}</a></td><td>{version}{" 39%" if running else ""}</td><td>worker</td><td>{begin}</td><td>1 hour</td><td>Build_Runner</td></tr>'
    text += '</table>'
    if next_url: text += f'<a href="{escape(next_url)}">&gt;</a>'
    return text.encode()


def overview(rows=(), *, sample=False):
    text = '<table><tr>' + ''.join('<th>'+s+'</th>' for s in ('Id','Next Build Version','Schedule','Requested By','Schedule Date','Priority','Process Status','Build Version','Configuration Path','Hub ID','Requester')) + '</tr>'
    for b,h in rows:
        text += f'<tr><td><a href="/build/{b}">{b}</a></td><td></td><td></td><td>Build_Runner</td><td>{DATE}</td><td>7</td><td>RUNNING_BUILD</td><td>[fixture-user] build</td><td>PRODUCT/example/RELEASE</td><td>{h}</td><td>fixture-user</td></tr>'
    text += '</table>'
    if sample:
        text += '<table><tr><th>Id</th><th>Version</th><th>Begin Date</th><th>Duration</th></tr>'
        text += f'<tr><td>900</td><td>test 39%</td><td>{DATE}</td><td>1h:00m:00s</td></tr></table>'
    return text.encode()


class MemoryTransport:
    def __init__(self, pages, *, clock=None):
        self.pages = pages; self.reads = []; self.indices = {}
        self.clock = clock or {'valid': True, 'offset_s': 0, 'error_s': 0, 'server_time': STAMP,
                               'received_at': STAMP, 'sent_at': STAMP, 'rtt_s': .01}
    def read(self, url, *, history=False):
        p = urlsplit(url); path = p.path + ('?' + p.query if p.query else '')
        self.reads.append(path)
        value = self.pages.get(path)
        if isinstance(value, list):
            i = self.indices.get(path,0); self.indices[path] = i+1; value = value[min(i,len(value)-1)]
        if callable(value): value = value()
        if value is None: raise FlowError(5,'bm_http_status',status=404)
        if isinstance(value, FlowError): raise value
        return value, copy.deepcopy(self.clock)
    def reset(self): pass
    def close(self): pass


def pages(b='900', h='500', **kwargs):
    return {'/overview/4362': overview(), '/history/4362': history([b]),
            '/build/'+b: detail(b,h,**kwargs),
            '/build/'+b+'/variables': detail(b,h,variables={'PACKAGE_LIST':BASE,'SHELVE_LIST':''},**kwargs)}
