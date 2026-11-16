"""Designer B1.3: page tab identity, independent of history navigation."""
import re
from urllib.parse import urlsplit,urljoin
from .errors import FlowError

def tab_identity(doc,build_id,page_url):
    links=[];origin=urlsplit(page_url)
    for node in doc.nodes:
        if node.tag!='a' or 'nav-link' not in node.attrs.get('class','').split():continue
        u=urlsplit(urljoin(page_url,node.attrs.get('href','')))
        m=re.fullmatch(r'/build/([^/]+)/(.+)',u.path)
        if not m:continue
        if m[1]!=str(build_id) or u.scheme!=origin.scheme or u.netloc!=origin.netloc or u.username or u.password or u.query or u.fragment:raise FlowError(5,'bm_identity_mismatch')
        if re.fullmatch(r'overview|log|variables|step_status|build_report_[A-Za-z0-9_-]+|profiling_report_[A-Za-z0-9_-]+',m[2]):links.append({'host':u.hostname,'path':u.path})
    if len(links)<2:raise FlowError(5,'bm_identity_mismatch')
    return links
