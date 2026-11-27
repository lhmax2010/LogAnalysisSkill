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
EMPTY_CONTROLS = tuple(PROPERTIES[i] for i in (6, 9, 10, 11, 12))
DEFAULT_CONTROLS = PROPERTIES[13:16]
SEED = [{'index':i,'label':name,'kind':KINDS[i], 'name':'editor:content:basicProperties:'+str(i)+':property:editor:editor:'+('palette:recorder' if i==8 else 'checkbox' if i in (13,14) else 'wrapper:select' if KINDS[i]=='select' else 'wrapper:input')} for i,name in enumerate(PROPERTIES)]
CALLBACK_SEED=[{'method':'POST','path':'/wicket/page','listener':'IBehaviorListener','behavior':'0','component':'form-editor-content-basicProperties-'+str(i)+'-property-editor-editor-wrapper-input'} for i in (1,2,3,5,7,17)]

def policy_error(field, rule):
    reason = 'first_release_submit_policy'
    return FlowError(4, reason, todo={'reason': reason, 'field': field, 'rule': rule,
        'message': {'must_be_empty': '首版只允许该控件为空。',
                    'must_keep_default': '首版必须保留表单当前默认值；请核对请求和表单。'}[rule]})


def enforce_policy(form, *, defaults=None, actual=None):
    if set(form) != set(PROPERTIES):
        raise FlowError(2, 'all_18_properties_required')
    if any(not isinstance(value, str) for value in form.values()):
        raise FlowError(2, 'business_values_must_be_strings')
    for field in EMPTY_CONTROLS:
        if form[field] != '' or (actual is not None and actual[field] != ''):
            raise policy_error(field, 'must_be_empty')
    for field, allowed in zip(DEFAULT_CONTROLS, ({'true'}, {'true'}, {'yes', 'no'})):
        requested = form[field]
        if (requested not in allowed or (defaults is not None and defaults[field] != requested)
                or (actual is not None and actual[field] != requested)):
            raise policy_error(field, 'must_keep_default')


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

def readback(config,snapshot,form, *, defaults=None):
    structure(config,snapshot)
    actual={c['label']:c.get('value') for c in snapshot['controls']}
    enforce_policy(form, defaults=defaults, actual=actual)
    if any(not isinstance(actual.get(p),str) or normalized(actual[p])!=normalized(form[p]) for p in PROPERTIES):raise FlowError(5,'form_readback_mismatch')
    return actual

def multipart_line_endings(value):
    return re.sub(r'\r\n|\r|\n', '\r\n', value)


def ks_recorder_evidence(snapshot):
    palette = snapshot.get('ks_palette', {})
    if 'recorder' not in palette:
        return None
    raw = palette['recorder'].encode()
    return {'length': len(raw), 'sha256': digest(raw)}


def _ks_wire(snapshot, value, entry, *, rehearsal):
    palette = snapshot.get('ks_palette')
    if palette is None:
        raise FlowError(4, 'ks_mapping_unregistered')
    choices, selection = palette['choices'], palette['selection']
    wanted = value.split(',') if value else []
    candidates = {}
    for option in choices + selection:
        candidates.setdefault(option['text'], []).append(option['value'])
    details = {'recorder': ks_recorder_evidence(snapshot), 'choices_count': len(choices),
               'selection_count': len(selection)}
    if [option['text'] for option in selection] != wanted or any(len(candidates[text]) != 1 for text in wanted):
        raise FlowError(4, 'ks_mapping_unregistered', **details)

    derived = {'ids': ','.join(candidates[text][0] for text in wanted), 'texts': ','.join(wanted)}
    for encoding, encoded in derived.items():
        if palette['recorder'] == encoded:
            if not rehearsal and entry.get('encoding') != encoding:
                raise FlowError(4, 'property_encoding_unregistered', property='KS_LIST', ks_encoding=encoding)
            return encoded, encoding
    shapes = {kind: re.sub(r'[0-9]+', 'N', encoded)[:80] if re.fullmatch(r'[\w. ,()+-]*', encoded)
              else '<redacted>' for kind, encoded in derived.items()}
    raise FlowError(4, 'ks_mapping_unregistered', candidate_shapes=shapes, **details)


def wire_values(config,snapshot,form, *, rehearsal=False, evidence=None):
    """Explicitly decode encodings; unregistered fields can be observed, never sent."""
    readback(config,snapshot,form)
    result = {}
    props = config.raw['submit']['property_map']
    ks_wire, ks_encoding = _ks_wire(snapshot, form['KS_LIST'], props['KS_LIST'], rehearsal=rehearsal)
    if evidence is not None:
        evidence['ks_encoding'] = ks_encoding
    for c in snapshot['controls']:
        p=c['label'];entry=props[p];value=form[p]
        if c['kind'] != 'ks' and not rehearsal and entry.get('encoding') is None:
            raise FlowError(4, 'property_encoding_unregistered')
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
            wire = ks_wire
        else:
            wire = multipart_line_endings(value)
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
