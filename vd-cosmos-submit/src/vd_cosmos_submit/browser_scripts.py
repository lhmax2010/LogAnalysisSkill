"""Fixed, hashed scripts. No caller-supplied selector or source is accepted."""
from hashlib import sha256
from vd_cosmos_core.errors import FlowError

SCRIPT = r"""({operation,index,value,target,account}) => {
 const secret = document.querySelector('input[type="password"]');
 if(operation==='login_probe')return {manual_login:!!secret};
 if (secret) return {password_present:true,password_autofill:secret.matches(':-webkit-autofill')};
 const visible=e=>{const s=getComputedStyle(e);return e.getClientRects().length>0 &&
   e.checkVisibility({opacityProperty:true,visibilityProperty:true}) &&
   s.visibility==='visible' && e.getBoundingClientRect().width>0 && e.getBoundingClientRect().height>0;};
 if(operation==='dismiss_notice'||operation==='run_position'){
  const notices=[...document.querySelectorAll('#myNav.overlay')].filter(visible);
  if(notices.length>1)return {clear:false};
  if(operation==='dismiss_notice' && notices.length===1)notices[0].style.setProperty('display','none','important');
  const buttons=[...document.querySelectorAll('a,button,[role="button"],input[type="button"],input[type="submit"]')]
    .filter(e=>visible(e) && (e.tagName==='INPUT'?e.value:e.innerText).trim()==='Run the configuration');
  if(buttons.length!==1)return {clear:false};
  const button=buttons[0],r=button.getBoundingClientRect();
  const x=r.x+r.width/2,y=r.y+r.height/2,hit=document.elementFromPoint(x,y);
  return hit&&button.contains(hit)?{clear:true,x,y}:{clear:false};
 }
 if(operation==='account'){
  const matches=[...document.querySelectorAll('header *,nav *,[role="banner"] *,[role="navigation"] *')]
    .filter(e=>visible(e) && e.textContent.trim()===account &&
      ![...e.querySelectorAll('*')].some(c=>visible(c) && c.textContent.trim()===account));
  return {matched:matches.length===1, element:matches.length===1?
    {tag:matches[0].tagName.toLowerCase(),id:matches[0].id,class:matches[0].getAttribute('class')||''}:null};
 }
 const breadcrumbs=[...document.querySelectorAll('.breadcrumb,.breadcrumbs')];
 const segments=breadcrumbs.length===1 ? breadcrumbs[0].textContent.split(/[/»›>\r\n]+/).map(s=>s.trim()).filter(Boolean) : [];
 const expected=target.split('/');
 const same=(a,b)=>a.length===b.length && a.every((s,i)=>s===b[i]);
 if(!segments.length || !(same(segments,expected) || (expected[0]==='root' && same(segments,expected.slice(1)))))
   return {form_unrecognized:true,breadcrumb_segments:segments};
 const forms = [...document.forms].filter(f=>f.enctype==='multipart/form-data');
 if (forms.length!==1) throw Error('form'); const f=forms[0];
 const prefix='editor:content:basicProperties:';
 const all=[...f.elements];
 const known=all.filter(e=>e.name && e.name.startsWith(prefix));
 const names=new Set(); for(const e of known){if(names.has(e.name))throw Error('duplicate');names.add(e.name);}
 const groups=Array.from({length:18},(_,i)=>known.filter(e=>e.name.startsWith(prefix+i+':property:editor:editor:')));
 const labels=['BUILD_TYPE','BASE_REPOS','BUILD_CONF','PRODUCT_REPOS','ARCH','PACKAGE_LIST','GITURL','SHELVE_LIST','KS_LIST','Product Version (ks)','rpm Add & Delete','PACKAGE_LIST (DELETE)','PACKAGE_LIST (x86 arch)','Ignore package build failure?',"Keep 'Full' build type",'Image Skip?','EMAIL_CC','EXTRA_BUILD_PARAMETER'];
 const kinds=['select','text','text','text','select','textarea','select','textarea','ks','textarea','textarea','textarea','textarea','checkbox','checkbox','select','textarea','text'];
 const controls=groups.map((g,i)=>{
  const e=i===8?g.find(x=>x.type==='hidden'):g[0];
  if(!e || (i!==8 && g.length!==1) || (i===8 && (g.length!==3 || !g.some(x=>x.name.endsWith(':palette:choices')) || !g.some(x=>x.name.endsWith(':palette:selection')))))throw Error('control');
  if(i!==8 && (e.tagName==='SELECT'?'select':e.tagName==='TEXTAREA'?'textarea':e.type)!==kinds[i])throw Error('type');
  const row=e.closest('tr');const text=row?row.innerText:'';
  if(!text.includes(labels[i]))throw Error('label');
  const opts=e.tagName==='SELECT'?[...e.options].map(o=>({text:o.text,value:o.value})):[];
  const selected=i===8?[...g.filter(x=>x.tagName==='SELECT').slice(-1)[0]?.options||[]].map(o=>o.text):[];
  const v=i===8?selected.join(','):e.type==='checkbox'?String(e.checked):e.tagName==='SELECT'?e.selectedOptions[0]?.text||'':e.value;
  return {index:i,label:labels[i],kind:kinds[i],name:e.name,options:opts,selected,value:v,default:e.tagName==='SELECT'?v:e.type==='checkbox'?e.checked:e.value===''};
 });
 const hidden=all.filter(e=>e.type==='hidden' && e.name===f.id+'_hf_0');
 if(hidden.length!==1 || all.some(e=>e.name && !e.name.startsWith(prefix) && e!==hidden[0]))throw Error('extra');
 if(operation==='snapshot')return {target,controls,hidden:hidden[0].name,breadcrumb_segments:segments};
 if(operation==='serialize')return [...new FormData(f).entries()].map(([k,v])=>{if(typeof v!=='string')throw Error('file');return [k,v];});
 if(operation==='fill'){
  if(!Number.isInteger(index)||index<0||index>17||typeof value!=='string')throw Error('args');
  const g=groups[index], e=index===8?g.find(x=>x.type==='hidden'):g[0];
  if(index===8){if(controls[8].value!==value)throw Error('ks');return true;}
  if(e.tagName==='SELECT'){const options=[...e.options].filter(o=>o.text===value);if(options.length!==1)throw Error('option');e.value=options[0].value;}
  else if(e.type==='checkbox'){if(!['true','false'].includes(value))throw Error('boolean');e.checked=value==='true';}
  else e.value=value;
  e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));e.dispatchEvent(new Event('blur',{bubbles:true}));return true;
 }
 throw Error('operation');
}"""
DIGEST='eb47681d276779b8f2a4f14d6db6c117dd603bb6cd74c839e69ab5d2d1bbd322'

def arguments(operation,*,index=None,value=None,target=None,account=None,**unexpected):
    if unexpected or operation not in {'snapshot','serialize','fill','account','login_probe','dismiss_notice','run_position'} or not isinstance(target,str):raise FlowError(4,'fixed_script_arguments_rejected')
    if operation=='fill' and (type(index) is not int or not 0<=index<18 or not isinstance(value,str)):raise FlowError(4,'fixed_script_arguments_rejected')
    if operation!='fill' and (index is not None or value is not None):raise FlowError(4,'fixed_script_arguments_rejected')
    if operation=='account':
        if not isinstance(account,str) or not account or account!=account.strip():
            raise FlowError(4,'fixed_script_arguments_rejected')
    elif account is not None:raise FlowError(4,'fixed_script_arguments_rejected')
    return {'operation':operation,'index':index,'value':value,'target':target,'account':account}
