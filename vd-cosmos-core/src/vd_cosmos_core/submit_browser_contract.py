"""Pure business-form contract. No browser APIs or authentication data."""
from email import policy
from email.parser import BytesParser
import re
from urllib.parse import urlsplit, urljoin
from .errors import FlowError
from .files import digest, json_bytes
from .submit_config import PROPERTIES
from . import submit_model as model

KINDS = ['select','text','text','text','select','textarea','select','textarea','ks',
         'textarea','textarea','textarea','textarea','checkbox','checkbox','select','textarea','text']
SEED = [{'index':i,'label':name,'kind':KINDS[i]} for i,name in enumerate(PROPERTIES)]

def normalized(value):
    return '\n'.join(line.rstrip() for line in value.replace('\r\n','\n').replace('\r','\n').split('\n')).rstrip()

def structure(config, snapshot):
    model.ensure_safe(config,snapshot)
    if snapshot.get('password_autofill') or snapshot.get('password_present'):raise FlowError(4,'sensitive_form_present')
    controls=snapshot.get('controls',[])
    if snapshot.get('target')!=config.raw['submit']['target_config'] or len(controls)!=18:raise FlowError(5,'form_unrecognized')
    expected=config.raw['submit'].get('form_fingerprint',{}).get('controls',SEED)
    for i,c in enumerate(controls):
        if any(c.get(k)!=SEED[i][k] for k in ('index','label','kind')):raise FlowError(5,'form_unrecognized')
        if not re.fullmatch(r'editor:content:basicProperties:'+str(i)+r':property:editor:editor:[A-Za-z0-9:_-]+',c.get('name','')):raise FlowError(5,'control_name_unrecognized')
        if any(c.get(k)!=v for k,v in expected[i].items() if k not in {'default'}):raise FlowError(5,'form_fingerprint_changed')
    fingerprint={'target':snapshot['target'],'controls':[{k:v for k,v in c.items() if k!='value'} for c in controls]}
    return fingerprint

def readback(config,snapshot,form):
    structure(config,snapshot)
    actual={c['label']:c.get('value') for c in snapshot['controls']}
    if any(not isinstance(actual.get(p),str) or normalized(actual[p])!=normalized(form[p]) for p in PROPERTIES):raise FlowError(5,'form_readback_mismatch')
    return actual

def wire_values(config,snapshot,form, *, rehearsal=False):
    """Explicitly decode encodings; unregistered fields can be observed, never sent."""
    readback(config,snapshot,form);result={};props=config.raw['submit']['property_map']
    for c in snapshot['controls']:
        p=c['label'];entry=props[p];value=form[p]
        if not rehearsal and entry.get('encoding') is None:raise FlowError(4,'property_encoding_unregistered')
        if c['kind']=='checkbox':
            if value not in {'true','false'}:raise FlowError(4,'checkbox_encoding_unregistered')
            if value=='false':continue
            wire=entry.get('checked_value')
            if not isinstance(wire,str):raise FlowError(4,'checkbox_encoding_unregistered')
        elif c['kind']=='select':
            pairs=[o for o in c.get('options',[]) if o['text']==value]
            if len(pairs)!=1:raise FlowError(4,'enum_encoding_unregistered')
            wire=pairs[0]['value']
            if not rehearsal and entry.get('option_values',{}).get(value)!=wire:raise FlowError(4,'enum_encoding_unregistered')
        elif c['kind']=='ks':
            if value!=','.join(c.get('selected',[])):raise FlowError(4,'ks_mapping_unregistered')
            wire=entry.get('record_value')
            if not isinstance(wire,str):raise FlowError(4,'ks_mapping_unregistered')
        else:wire=value.replace('\r\n','\n').replace('\r','\n').replace('\n','\r\n')
        result[c['name']]=wire
    return result

def multipart(body,content_type):
    if not isinstance(body,bytes) or len(body)>16*1024*1024:raise FlowError(4,'submit_body_invalid')
    if '\r' in content_type or '\n' in content_type:raise FlowError(4,'submit_body_invalid')
    message=BytesParser(policy=policy.default).parsebytes(('Content-Type: '+content_type+'\r\nMIME-Version: 1.0\r\n\r\n').encode()+body)
    if message.get_content_type()!='multipart/form-data' or not message.is_multipart() or message.defects:raise FlowError(4,'submit_body_invalid')
    result={}
    for part in message.iter_parts():
        name=part.get_param('name',header='content-disposition')
        if not name or name in result or part.get_content_disposition()!='form-data' or part.get_filename() is not None or part.defects or part.is_multipart() or part.get('Content-Transfer-Encoding'):raise FlowError(4,'submit_parts_invalid')
        try:result[name]=part.get_payload(decode=True).decode('utf-8',errors='strict')
        except (UnicodeError,AttributeError):raise FlowError(4,'submit_encoding_invalid') from None
    return result

def verify_parts(config,parts,expected,hidden, *, rehearsal=False):
    model.ensure_safe(config,parts)
    if set(parts)!=set(expected)|{hidden}:raise FlowError(4,'submit_parts_mismatch')
    if any(parts[k]!=v for k,v in expected.items()):raise FlowError(4,'submit_values_mismatch')
    if not rehearsal and parts[hidden] not in ('',config.raw['submit'].get('hidden_registered_value','')):
        raise FlowError(4,'hidden_value_unregistered',length=len(parts[hidden]),sha256=digest(parts[hidden].encode()))
    return [{'name':k,'length':len(v.encode()),'sha256':digest(v.encode())} for k,v in sorted(parts.items())]

def accepted_location(config,request_url,location):
    u=urlsplit(urljoin(request_url,location))
    return u.scheme=='https' and u.netloc==config.raw['cosmos']['hub_host'] and u.path=='/overview/'+config.raw['submit']['target_config_id'] and not (u.query or u.fragment or u.username or u.password)
