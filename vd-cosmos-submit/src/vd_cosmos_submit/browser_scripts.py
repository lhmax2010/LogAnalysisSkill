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
 if(['dismiss_notice','run_position','scroll_run'].includes(operation)){
  const notices=[...document.querySelectorAll('#myNav.overlay')].filter(visible);
  if(operation==='dismiss_notice' && notices.length===1)notices[0].style.setProperty('display','none','important');
  const buttons=[...document.querySelectorAll('a,button,[role="button"],input[type="button"],input[type="submit"]')]
    .filter(e=>visible(e) && (e.tagName==='INPUT'?e.value:(e.innerText||'')).trim()==='Run the configuration');
  const button=buttons.length===1?buttons[0]:null,r=button?.getBoundingClientRect();
  const facts={operation,notices_visible:notices.length,button_count:buttons.length,
    rect:r?{x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)}:null,
    viewport:{innerWidth,innerHeight},
    visibility_state:['visible','hidden','prerender','unloaded'].includes(document.visibilityState)?document.visibilityState:'unknown',
    hit:null};
  const blocked=reason=>({clear:false,reason,...facts});
  if(notices.length>1)return blocked('notices_multiple');
  if(!button)return blocked('button_count');
  const x=r.x+r.width/2,y=r.y+r.height/2;
  if(x<0 || y<0 || x>=innerWidth || y>=innerHeight){
   if(operation==='scroll_run')button.scrollIntoView({block:'center',behavior:'instant'});
   return blocked('hit_outside_viewport');
  }
  const hit=document.elementFromPoint(x,y);
  if(!hit)return blocked('hit_null');
  const safeAttribute=(text,pattern,limit)=>text && !pattern.test(text)?'<redacted>':text.slice(0,limit);
  facts.hit={tag:safeAttribute(hit.tagName.toLowerCase(),/^[a-z][a-z0-9-]*$/,32),
    id:safeAttribute(hit.getAttribute('id')||'',/^[a-zA-Z0-9_-]+$/,80),
    class:safeAttribute(hit.getAttribute('class')||'',/^[a-zA-Z0-9_ -]+$/,60)};
  if(!button.contains(hit))return blocked('hit_other_element');
  return {clear:true,x,y,click_rect:[r.x,r.y,r.width,r.height],...facts};
 }
 if(operation==='account'){
  const info=e=>({tag:e.tagName.toLowerCase(),id:e.id,class:e.getAttribute('class')||''});
  const matches=[...document.querySelectorAll('a,button,[role="link"],[role="button"],input[type="button"],input[type="submit"]')]
    .filter(e=>visible(e) && (e.tagName==='INPUT'?e.value:(e.innerText||'')).trim().toLowerCase()==='sign out');
  if(matches.length!==1)return {matched:false,element:null,container:null};
  const token=new RegExp('(^|[\\s(:!])'+account.replace(/[.*+?^$(){}|[\]\\]/g,'\\$&')+'($|[\\s),])');
  const element=info(matches[0]);
  let parent=matches[0].parentElement;
  for(let level=1;parent && level<=3;level++,parent=parent.parentElement){
   const text=(parent.innerText||'').replace(/\s+/g,' ').trim();
   if(token.test(text)){
    const result={matched:true,element,container:info(parent)};
    if([...text].length<=80)result.container_text=text;
    return result;
   }
  }
  return {matched:false,element,container:null};
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
DIGEST='ccb9ea5e3c53b0334c70c89610e7b5476029b4abaf7b52672776db827d7fd102'

def arguments(operation,*,index=None,value=None,target=None,account=None,**unexpected):
    if unexpected or operation not in {'snapshot','serialize','fill','account','login_probe','dismiss_notice','run_position','scroll_run'} or not isinstance(target,str):raise FlowError(4,'fixed_script_arguments_rejected')
    if operation=='fill' and (type(index) is not int or not 0<=index<18 or not isinstance(value,str)):raise FlowError(4,'fixed_script_arguments_rejected')
    if operation!='fill' and (index is not None or value is not None):raise FlowError(4,'fixed_script_arguments_rejected')
    if operation=='account':
        if not isinstance(account,str) or not account or account!=account.strip():
            raise FlowError(4,'fixed_script_arguments_rejected')
    elif account is not None:raise FlowError(4,'fixed_script_arguments_rejected')
    return {'operation':operation,'index':index,'value':value,'target':target,'account':account}
