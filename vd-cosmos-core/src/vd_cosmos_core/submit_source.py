"""Source determination reads only explicit variables and report headers; no rounds."""
import time
from urllib.parse import urlsplit
from . import submit_model as model
from .bm_pages import base_digest
from .build_inputs import parse_list
from .errors import FlowError
from .files import digest, json_bytes
from .report import Document, report_headers
from .state import EventStore
from .submit_config import SECRET_NAME, PROPERTIES
from .submit_terminal import confirmation_error
from .transport import HTTPTransport

COPY_DEFAULT = ['PACKAGE_LIST','BASE_REPOS','BUILD_CONF','PRODUCT_REPOS','ARCH','BUILD_TYPE','KS_LIST','EXTRA_BUILD_PARAMETER']


REQUIRED_HEADERS = {'arch', 'start_time', 'base', 'product', 'build_conf'}


def headers_only(data):
    try:
        headers, conflicts = report_headers(Document(data.decode('utf-8')))
    except (UnicodeError, ValueError, RecursionError):
        raise FlowError(5, 'source_header_unrecognized') from None
    if conflicts:
        raise FlowError(5, 'source_header_conflict', keys=sorted(conflicts), found=sorted(headers))
    missing = sorted(key for key in REQUIRED_HEADERS if not headers.get(key))
    if missing:
        raise FlowError(5, 'source_header_missing', keys=missing, found=sorted(headers))
    return headers


def read_headers(config, build, arch, reader):
    c=config.raw['cosmos']
    if not c.get('report_path_template') or not c.get('report_root'):
        raise FlowError(2, 'source_report_config_required')
    path=c['report_path_template'].format(build_id=build,last3=build[-3:].zfill(3),arch=arch)
    url=c['report_root'].rstrip('/')+'/'+path.lstrip('/')
    if urlsplit(url).scheme!='https':raise FlowError(4,'source_report_requires_https')
    from .bm_reader import FixtureTransport
    if isinstance(reader.transport,FixtureTransport):body,_=reader.transport.read(url)
    else:
        response=HTTPTransport(config).get(url,config.raw['fetch']['max_page_bytes'])
        if response['status']!=200:raise FlowError(5,'source_report_unavailable')
        body=response['body']
    return headers_only(body)


def prepare_source(config, hub, build, reader, header_reader=read_headers, *, write=True, evidence=None):
    """Run the same pre-confirmation checks for once and the read-only verifier."""
    evidence = {} if evidence is None else evidence
    if not str(hub).isdecimal() or build is not None and not str(build).isdecimal():raise FlowError(2,'source_identity_required')
    if build=='19270877':raise FlowError(4,'erroneous_build_forbidden')
    scan=None
    if build:
        d=reader.detail(build,fresh=True);coverage='未查找（--bm-build 直接指定）';version=None
    else:
        # scan, not lookup: lookup would also read SHELVE_LIST.
        scan=reader.scan(hub_id=hub)
        candidates=scan['candidates']
        if len(candidates)!=1 or scan['conflicts']:
            raise FlowError(3,'source_not_unique',todo={'reason':'source_not_unique','message':'来源未定位或重跑链；请明确 --bm-build'})
        d=candidates[0];build=d['build_id'];coverage=scan['coverage'];version=scan['rows'].get(build,{}).get('version')
    evidence['detail_keys'] = sorted(d)
    if build=='19270877' or d.get('conflict') or d.get('hub_id')!=str(hub):raise FlowError(4,'source_hub_mismatch')
    if d['config_id']!=config.raw['cosmos']['bm_config_id']:raise FlowError(4,'source_config_mismatch')
    copy_names=config.raw['submit'].get('copy_from_source_vars',COPY_DEFAULT)
    compare_names=config.raw['analyzer'].get('source_compare_vars',['BASE_REPOS','PRODUCT_REPOS','BUILD_CONF'])
    if any(not isinstance(names,list) or not all(isinstance(n,str) for n in names) or len(set(names))!=len(names) for names in (copy_names,compare_names)):
        raise FlowError(2,'source_variable_names_required')
    names=set(copy_names)|set(compare_names)
    if 'PACKAGE_LIST' not in copy_names or any(n in {'SHELVE_LIST','EMAIL_CC'} or SECRET_NAME.search(n) for n in names):raise FlowError(4,'source_variable_forbidden')
    values=reader.variables(build,names) if write else reader.variables(build,names,write=False)
    evidence['variable_keys'] = sorted(values)
    if set(values)!=names:raise FlowError(5,'source_variable_missing',todo={'reason':'source_variable_missing'})
    frozen={n:values[n]['value'] for n in sorted(names)}
    headers = {}
    evidence['report_header_keys'] = {}
    for arch in config.raw['cosmos']['archs']:
        try:
            headers[arch] = header_reader(config,build,arch,reader)
        except FlowError as error:
            evidence['report_header_keys'][arch] = error.details.get('found', [])
            raise FlowError(error.code, error.reason, **{**error.details, 'arch': arch}) from None
        evidence['report_header_keys'][arch] = sorted(headers[arch])
        if headers[arch]['arch'] != arch:
            raise FlowError(4, 'source_header_arch_mismatch', arch=arch)
    model.ensure_safe(config,headers)
    form=dict(config.raw['submit']['form'])
    if set(form)!=set(PROPERTIES):raise FlowError(2,'all_18_properties_required')
    props=config.raw['submit']['property_map'];copied=[]
    for name in PROPERTIES:
        variable=props[name]['variable'] or (name if name in COPY_DEFAULT else None)
        if variable in copy_names:form[name]=frozen[variable];copied.append(name)
    form['PACKAGE_LIST']=frozen['PACKAGE_LIST'];form['SHELVE_LIST']=''
    basis={'hub_instance':config.raw['cosmos']['hub_host'],'hub_id':str(hub),'bm_instance':config.raw['cosmos']['bm_host'],
           'build_id':build,'config_id':d['config_id'],'variables_sha256':digest(json_bytes(frozen)),
           'conditions_sha256':digest(json_bytes({'variables':{n:frozen[n] for n in compare_names},'headers':headers}))}
    display={**basis,'start_time':d['start_time'],'coverage':coverage,'version':version,'requester':d['requester'],
             'package_count':len(parse_list(frozen['PACKAGE_LIST'],config.raw['cosmos']['branch_markers'])),
             'package_digest':base_digest(frozen['PACKAGE_LIST'],config),'variables':frozen,'from_form':[n for n in PROPERTIES if n not in copied],'headers':headers}
    model.ensure_safe(config,display)
    return form, basis, display


def determine(config, hub, build, reader, confirm, context, header_reader=read_headers):
    form, basis, display = prepare_source(config, hub, build, reader, header_reader)
    expected=basis['build_id']
    if confirm(dict(display,confirmation='source',target=model.target(config)))!=expected:
        raise confirmation_error('source',expected)
    with EventStore(config.data_root) as store, store.transaction():
        store.append(context,'base_source_attest',{'basis':basis,'frozen':display['variables'],'headers':display['headers'],'at':time.time(),'reason':'once --base-from-hub 回显核对'},store.head())
    return form,basis
