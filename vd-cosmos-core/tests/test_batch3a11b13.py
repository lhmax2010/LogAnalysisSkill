"""B1.3 real received pages, architecture inputs, compact CLI and verifier errors."""
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import urlsplit
from test_batch3a11b1 import B1Case
from bm_helpers import detail,variable_table,pages,BASE
from helpers import CORE,REPO
from vd_cosmos_core import bm_pages,build_inputs,verify_b3a11
from vd_cosmos_core.observation import detail_state
from vd_cosmos_core.report import Document
from vd_cosmos_core.files import json_bytes,load_json
from vd_cosmos_submit.cli import lookup_summary

FIXTURES=CORE/'fixtures/real_pages'

class RealPagesTests(B1Case):
    def setUp(self):
        super().setUp()
        self.config.raw['cosmos'].update(bm_host='bm.example.invalid',hub_host='hub.example.invalid',variables_url_template='https://bm.example.invalid/build/{build_id}/variables')
    def page(self,b='19270912'):return (FIXTURES/('detail_'+b+'.html')).read_bytes()
    def hub_h3(self,data):return re.search(r'<h3[^>]*>\s*♦ Hub Link\s*:.*?</h3>'.encode(),data,re.S)[0]
    def test_real_details_states_hubs_configs_and_trusted_observation(self):
        for b,h,state,ended in [('19270912','37491096','failed',True),('19206687','37376237','successful',True),('19238877','37432138','failed',True),('19091860','37174546','failed',True),('19344434','37619264','running',False)]:
            d=bm_pages.detail(self.page(b),self.config,b)
            self.assertEqual((d['hub_id'],d['state'],d['ended'],d['config_id']),(h,state,ended,'4362'))
            source=load_json(CORE/'config.sample.json')['cosmos']['status_source'];source['url_template']='https://bm.example.invalid/build/{build_id}'
            observed=detail_state(self.page(b),source,b,'https://bm.example.invalid/build/'+b)
            self.assertEqual(observed['identity'],'strong');self.assertEqual(observed['state'],'已结束' if ended else '运行')
    def test_hub_h3_missing_duplicate_wrong_host_and_outside_ignored(self):
        data=self.page();h=self.hub_h3(data);without=data.replace(h,b'')
        self.assertIsNone(bm_pages.detail(without,self.config,'19270912')['hub_id'])
        self.assertIsNone(bm_pages.detail(without+h,self.config,'19270912')['hub_id'])
        for bad in [data.replace(h,h+h),data.replace(h,h.replace(self.config.raw['cosmos']['hub_host'].encode(),b'wrong.example.invalid')),data.replace(h,re.sub(rb'<a .*?</a>',b'',h,flags=re.S)),data.replace(h,h.replace(b'</h3>',b'<a href="https://hub.example.invalid/build/1">extra</a></h3>'))]:
            self.assertEqual(self.fails(5,bm_pages.detail,bad,self.config,'19270912').reason,'bm_page_unrecognized')
    def test_tab_and_config_identity_mutations_ignore_history_buttons(self):
        data=self.page();doc=Document(data.decode());tab=next(n for n in doc.nodes if n.tag=='a' and 'nav-link' in n.attrs.get('class','').split() and n.attrs.get('href','').endswith('/variables'))
        bad=data.replace(tab.attrs['href'].encode(),tab.attrs['href'].replace('19270912','999').encode())
        self.assertEqual(self.fails(5,bm_pages.detail,bad,self.config,'19270912').reason,'bm_identity_mismatch')
        configlink=next(n for n in doc.nodes if n.tag=='a' and 'nav-link' in n.attrs.get('class','').split() and n.attrs.get('href')=='/overview/4362')
        missing=data.replace(b'/overview/4362',b'/not-config/4362')
        for bad in [missing,data+b'<a class="nav-link" href="/overview/999">other</a>']:
            self.assertEqual(self.fails(5,bm_pages.detail,bad,self.config,'19270912').reason,'bm_config_unrecognized')
        # Same ID appears twice: exactly one DISTINCT ID remains, per designer.
        self.assertEqual(bm_pages.detail(data+b'<a class="nav-link" href="/overview/4362">same</a>',self.config,'19270912')['config_id'],'4362')
        self.assertEqual(bm_pages.detail(data,self.config,'19270912')['identity'],'strong')
    def test_archived_diag_hashes_and_exact_exemptions(self):
        from vd_cosmos_core.archive_precheck import check_file
        expected={'scripts/diag28.py':'9cb35b2540ddc193041871ff422f03158b6341f0ebd610538d7cd810a1a4e13d','scripts/diag29.py':'0e20d3586acb12161c15485eedb78a1ec0eb089e7bf0bc115ce99f45434a9df0','scripts/diag30b.py':'63f11711e972fd1b479e85f6dca1b911ca87af2fecc9239f8a238bd5ee4688be','diag29.txt':'357a32a2218401ffe7bd747b71d0fca6f1672eb29c3de20eed8ca5541b7b5a83'}
        for name,sha in expected.items():
            path=REPO/'docs/enhance/evidence'/name;self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),sha);self.assertTrue(check_file(path,self.config)['allowed'])
    def test_real_overview_history_rows_and_fixture_hash_manifest(self):
        overview=bm_pages.listing((FIXTURES/'overview_4362.html').read_bytes(),self.config,'overview');self.assertEqual(len(overview['rows']),39);self.assertTrue(all(r['hub_id'] for r in overview['rows']))
        history=bm_pages.listing((FIXTURES/'history_4362_p1.html').read_bytes(),self.config,'history');self.assertEqual(len(history['rows']),30);self.assertTrue(history['next'])
        for name,entry in load_json(FIXTURES/'manifest.json').items():
            data=(FIXTURES/name).read_bytes();self.assertEqual(hashlib.sha256(data).hexdigest(),entry['sha256']);self.assertEqual(hashlib.sha256(re.sub(r'\s+','',data.decode()).encode()).hexdigest(),entry['whitespace_free_sha256'])

class ArchInputsTests(B1Case):
    def inputs(self):
        root='//example/project/packages/'
        total=root+'common/...@100\n'
        x86=total+''.join(root+n+'/...@101\n' for n in ('erofs-utils','vd-integration','mic-bootstrap'))
        values={'PACKAGE_LIST':total,'SHELVE_LIST':'','PACKAGE_LIST_armv7l':total,'SHELVE_LIST_armv7l':'','PACKAGE_LIST_x86_64':x86,'SHELVE_LIST_x86_64':'','BASE_REPOS':'base','PRODUCT_REPOS':'product','BUILD_CONF':'conf'}
        reports={arch:{'input_rows':[{'path':v['path'],'cl':v['cl'],'shelve':False} for v in build_inputs.parse_list(values['PACKAGE_LIST_'+arch],[]).values()]} for arch in ('armv7l','x86_64')}
        return values,reports
    def test_diag28_arch_extras_reconcile_total_stays_submission_input(self):
        values,reports=self.inputs();result=build_inputs.freeze(self.config,'arch',values,reports,source='variables_page')
        self.assertEqual(len(result['base']),1);self.assertEqual(len(result['architectures']['x86_64']['base']),4)
        self.assertEqual(len(build_inputs.for_arch(result,'armv7l')['base']),1)
        self.assertIn('/example/project/packages/erofs-utils',build_inputs.for_arch(result,'x86_64')['base'])
        self.assertEqual(Path(result['files']['PACKAGE_LIST']['path']).read_text(),values['PACKAGE_LIST'])
    def test_arch_specific_shelve_cl_does_not_cross_arch_and_total_coverage_required(self):
        values,reports=self.inputs();path=reports['x86_64']['input_rows'][1]['path'];reports['x86_64']['input_rows'][1].update(shelve=True,cl='200');values['SHELVE_LIST_x86_64']=path+'@200'
        result=build_inputs.compare_arch_lists(values,reports,[]);self.assertEqual(len(result['architectures']['x86_64']['shelve']),1)
        values['SHELVE_LIST_x86_64']=path+'@201';self.fails(4,build_inputs.compare_arch_lists,values,reports,[])
        values,reports=self.inputs();values['PACKAGE_LIST']+='//example/project/packages/absent/...@100';self.fails(4,build_inputs.compare_arch_lists,values,reports,[])
        values,reports=self.inputs();values['PACKAGE_LIST']=values['PACKAGE_LIST'].replace('@100','@999');self.fails(4,build_inputs.compare_arch_lists,values,reports,[])
    def test_missing_arch_list_fallback_but_empty_or_wrong_list_not_fallback(self):
        values,reports=self.inputs();del values['PACKAGE_LIST_armv7l'];del values['SHELVE_LIST_armv7l']
        result=build_inputs.compare_arch_lists(values,reports,[]);self.assertEqual(result['architectures']['armv7l']['fallback_note'],'回退到总清单')
        values['PACKAGE_LIST_x86_64']='';self.fails(4,build_inputs.compare_arch_lists,values,reports,[])
    def test_snapshot_selects_arch_base_revision_not_total_revision(self):
        from test_batch3a1 import Snapshot3a1Tests
        f=Snapshot3a1Tests();f.setUp();self.addCleanup(f.doCleanups)
        correct=copy.deepcopy(f.lists)
        for entry in f.lists['base'].values():entry['cl']='999999'
        f.lists['architectures']={f.package['key']['arch']:correct}
        result,_=f.snap()
        self.assertEqual(result['mode'],'可分析');self.assertEqual(result['files'][0]['snapshot_provenance'],'原样叠加')
    def test_arch_whitelist_first_read_change_and_unselected_secret_not_stored(self):
        values,_=self.inputs();values['UNSELECTED_VALUE']='not-to-store';html=detail(variables=values)
        self.config.raw['cosmos']['status_source']=load_json(CORE/'config.sample.json')['cosmos']['status_source']
        first,_=build_inputs.variables(html,self.config,'900','https://bm.example.invalid/build/900/variables')
        self.assertEqual(first['PACKAGE_LIST_x86_64'],values['PACKAGE_LIST_x86_64']);self.assertNotIn('UNSELECTED_VALUE',first)
        selected=bm_pages.variables(html,self.config,'900',build_inputs.variable_names(self.config));self.assertIn('PACKAGE_LIST_x86_64',selected)
        self.assertNotIn('UNSELECTED_VALUE',selected)
        values['PACKAGE_LIST_x86_64']+='//example/project/packages/new/...@100'
        error=self.fails(3,bm_pages.variables,detail(variables=values),self.config,'900',build_inputs.variable_names(self.config));self.assertEqual(error.reason,'variable_page_changed')
        for p in self.config.data_root.rglob('*'):
            if p.is_file():self.assertNotIn(b'not-to-store',p.read_bytes())

class LookupOutputTests(B1Case):
    def test_scan_page_errors_first_failure_and_summary_excludes_rows(self):
        data=pages();data['/overview/4362']=b'<table>wrong</table>';data['/build/900']=b'wrong';result=self.reader(data).lookup('500')
        self.assertEqual(result['page_errors'][0],{'kind':'overview','build_id':None,'reason':'bm_table_unrecognized'})
        self.assertTrue(any(e['kind']=='detail' and e['build_id']=='900' for e in result['page_errors']))
        result['rows']={str(i):{'payload':'x'*10000} for i in range(150)}
        summary=lookup_summary(result);self.assertLess(len(json.dumps(summary)),3000);self.assertNotIn('rows',summary);self.assertEqual(summary['counts']['rows'],150)
    def test_lookup_cli_one_small_object_full_artifact(self):
        data=pages();manifest={'pages':{}}
        for i,(url,body) in enumerate(data.items()):
            path=self.root/('p'+str(i));path.write_bytes(body);manifest['pages']['https://bm.example.invalid'+url]={'file':path.name,'clock':{'valid':True,'offset_s':0,'received_at':1,'rtt_s':.1}}
        f=self.root/'fixture.json';f.write_text(json.dumps(manifest))
        run=subprocess.run([sys.executable,str(REPO/'vd-cosmos-submit/scripts/run.py'),'lookup','--config',str(self.path),'--backend','fixture','--fixture',str(f),'--hub-id','500'],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stdout);out=json.loads(run.stdout);self.assertLess(len(run.stdout),4000);full=load_json(out['artifact']);self.assertIn('rows',full);self.assertIn('details',full);self.assertNotIn('rows',out)
    def test_b1_verifier_persists_result_reason_artifact_without_error(self):
        from vd_cosmos_core import verify_b3a11b1 as verifier
        from vd_cosmos_core.errors import FlowError
        child=FlowError(5,'acceptance_skill_failed',child_error=None,child_result='未定位',child_reason='页面无法识别',child_artifact='/fixture/lookup.json')
        with patch.object(verifier.subprocess,'check_output',side_effect=['a'*40,b'']),patch.object(verifier,'contracts',return_value=[]),patch.object(verifier,'offline_tests',return_value='offline'),patch.object(verifier,'command',side_effect=[{'exit_code':0},child]):
            result=verifier.execute(SimpleNamespace(verified_commit='a'*40,config=str(self.path)),REPO)
        self.assertEqual(result['failed_command']['hub_id'],'37491096');self.assertEqual(result['failed_command']['details']['child_artifact'],'/fixture/lookup.json')
        self.assertEqual(load_json(result['result_file']['path'])['failed_command'],result['failed_command'])
    def test_verifier_nonzero_without_error_keeps_result_reason_artifact(self):
        child={'exit_code':5,'result':'未定位','reason':'页面无法识别','artifact':'/fixture/result.json'}
        with patch.object(verify_b3a11,'process',return_value=SimpleNamespace(returncode=5,stdout=json_bytes(child),stderr=b'')):
            e=self.fails(5,verify_b3a11.command,self.config,REPO,self.root,{},'vd-cosmos-submit',['lookup'])
        self.assertIsNone(e.details['child_error']);self.assertEqual(e.details['child_result'],'未定位');self.assertEqual(e.details['child_reason'],'页面无法识别');self.assertEqual(e.details['child_artifact'],'/fixture/result.json')
