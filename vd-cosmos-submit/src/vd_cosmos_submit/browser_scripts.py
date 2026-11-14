"""Fixed, hashed scripts. No caller-supplied selector or source is accepted."""
from hashlib import sha256
from vd_cosmos_core.errors import FlowError

SCRIPT = r"""({operation,index,value,target}) => {
 const secret = document.querySelector('input[type="password"]');
 if (secret) return {password_present:true,password_autofill:secret.matches(':-webkit-autofill')};
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
  if(!e || (i!==8 && g.length!==1))throw Error('control');
  if(i!==8 && (e.tagName==='SELECT'?'select':e.tagName==='TEXTAREA'?'textarea':e.type)!==kinds[i])throw Error('type');
  const row=e.closest('tr');const text=row?row.innerText:'';
  if(!text.includes(labels[i]))throw Error('label');
  const opts=e.tagName==='SELECT'?[...e.options].map(o=>({text:o.text,value:o.value})):[];
  const selected=i===8?[...g.filter(x=>x.tagName==='SELECT').slice(-1)[0]?.options||[]].map(o=>o.text):[];
  const v=i===8?selected.join(','):e.type==='checkbox'?String(e.checked):e.tagName==='SELECT'?e.selectedOptions[0]?.text||'':e.value;
  return {index:i,label:labels[i],kind:kinds[i],name:e.name,options:opts,selected,value:v,default:e.tagName==='SELECT'?v:e.type==='checkbox'?e.checked:e.value===''};
 });
 const breadcrumb=document.querySelector('.breadcrumb')||document.querySelector('.breadcrumbs');
 if(!breadcrumb || breadcrumb.textContent.trim()!==target)throw Error('target');
 const hidden=all.filter(e=>e.type==='hidden' && e.name===f.id+'_hf_0');
 if(hidden.length!==1 || all.some(e=>e.name && !e.name.startsWith(prefix) && e!==hidden[0]))throw Error('extra');
 if(operation==='snapshot')return {target,controls,hidden:hidden[0].name};
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
DIGEST=sha256(SCRIPT.encode()).hexdigest()

def arguments(operation,*,index=None,value=None,target=None,**unexpected):
    if unexpected or operation not in {'snapshot','serialize','fill'} or not isinstance(target,str):raise FlowError(4,'fixed_script_arguments_rejected')
    if operation=='fill' and (type(index) is not int or not 0<=index<18 or not isinstance(value,str)):raise FlowError(4,'fixed_script_arguments_rejected')
    if operation!='fill' and (index is not None or value is not None):raise FlowError(4,'fixed_script_arguments_rejected')
    return {'operation':operation,'index':index,'value':value,'target':target}
