"""Designer B1.1 regressions: real columns, frozen values and rerun chains."""
import copy
import json
from pathlib import Path
import threading
import unittest

from bm_helpers import BASE, detail, history, pages, variable_table
from helpers import CORE
from test_batch3a11b1 import B1Case, OBSERVE, HUMAN
from vd_cosmos_core import bm_pages, build_inputs, submit_claim, variable_pages
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.files import digest, json_bytes
from vd_cosmos_core.state import EventStore
from vd_cosmos_core.submit_config import PROPERTIES
from vd_cosmos_core.report import parse_report
from helpers import report_html, pkg


class VariablePageTests(B1Case):
    def setUp(self):
        super().setUp()
        source=json.loads((CORE/'config.sample.json').read_text())['cosmos']['status_source']
        source['url_template']='https://bm.example.invalid/build/{build_id}'
        self.config.raw['cosmos']['status_source']=source
        self.values={'PACKAGE_LIST':BASE,'SHELVE_LIST':'','BASE_REPOS':'https://example.invalid/base',
                     'BUILD_CONF':'//example/conf@123','PRODUCT_REPOS':'https://example.invalid/product'}
        self.url='https://bm.example.invalid/build/900/variables'

    def stored(self):
        return {p.name:p.read_bytes() for p in (self.config.data_root/'inputs/variable-first-read').glob('*/*.json')}

    def test_three_columns_nonempty_display_pre_shared_callers_exact_value(self):
        body=detail(variables=dict(self.values,BART_PASSWD='DO_NOT_STORE_THIS'))
        body=body.replace(b'</td><td></td><td>',b'</td><td>Display label only</td><td>')
        a,note=build_inputs.variables(body,self.config,'900',self.url)
        b=bm_pages.variables(body,self.config,'900',set(self.values))
        self.assertEqual(a,self.values)
        self.assertEqual({name:value['value'] for name,value in b.items()},self.values)
        self.assertEqual(b['PACKAGE_LIST']['value_column'],2)
        self.assertEqual(b['PACKAGE_LIST']['table_columns'],3)
        self.assertEqual(len(build_inputs.parse_list(a['PACKAGE_LIST'],['[INT]'])),1)
        for path in self.config.data_root.rglob('*'):
            if path.is_file():
                for forbidden in (b'Display label only',b'BART_PASSWD',b'DO_NOT_STORE_THIS',b'<table',b'<pre'):
                    self.assertNotIn(forbidden,path.read_bytes())
        # Both callers have one shared first-read record per actual value.
        self.assertEqual(len(self.stored()),5)

    def test_header_mapping_reorder_legacy_two_columns_and_bad_headers(self):
        legacy=b'<table><tr><th>Name</th><th>Value</th></tr><tr><td>PACKAGE_LIST</td><td><pre>original</pre></td></tr></table>'
        self.assertEqual(variable_pages.parse(legacy,{'PACKAGE_LIST'})['PACKAGE_LIST']['value'],'original')
        reordered=b'<table><tr><th>Value</th><th>Display Name</th><th>Name</th></tr><tr><td><pre>original</pre></td><td>decoy</td><td>PACKAGE_LIST</td></tr></table>'
        self.assertEqual(variable_pages.parse(reordered,{'PACKAGE_LIST'})['PACKAGE_LIST']['value'],'original')
        bads=[legacy.replace(b'<tr><th>Name</th><th>Value</th></tr>',b''),
              legacy.replace(b'<th>Value</th>',b'<th>Content</th>'),
              legacy.replace(b'<th>Value</th>',b'<th>Value</th><th>Value</th>'),
              legacy+legacy,legacy.replace(b'<td><pre>',b'<td colspan="2"><pre>')]
        for bad in bads:
            with self.subTest(bad=bad):
                e=self.fails(5,variable_pages.parse,bad,{'PACKAGE_LIST'})
                self.assertEqual(e.details['todo']['message'],'变量页无法识别')
        page=detail(variables=self.values).replace(b'<th>Value</th>',b'<th>Content</th>')
        for call,args in [(build_inputs.variables,(page,self.config,'900',self.url)),
                          (bm_pages.variables,(page,self.config,'900',set(self.values)))]:
            self.assertEqual(self.fails(5,call,*args).reason,'variables_page_unrecognized')
        self.assertEqual(self.stored(),{})

    def test_first_read_before_report_validation_and_changes_preserve_authority(self):
        body=detail(variables=self.values)
        first,_=build_inputs.variables(body,self.config,'900',self.url)
        before=self.stored()
        self.fails(4,build_inputs.freeze,self.config,'no-report',first,{},source='variables_page')
        changed=dict(self.values,PACKAGE_LIST=BASE.replace('@100','@101'))
        error=self.fails(3,bm_pages.variables,detail(variables=changed),self.config,'900',set(self.values))
        self.assertEqual(error.reason,'variable_page_changed')
        self.assertEqual(error.details['todo']['message'],'变量页已变化')
        self.assertEqual(self.stored(),before)
        self.assertEqual(build_inputs.variables(body,self.config,'900',self.url)[0],first)
        issues=list((self.config.data_root/'inputs/variable-first-read').glob('*/issues/*.json'))
        self.assertEqual(len(issues),1)
        self.assertNotIn('@101',issues[0].read_text())

    def test_claim_first_read_restart_absence_new_names_and_digest_tampering(self):
        reader=self.reader()
        value=reader.variables('900',{'PACKAGE_LIST','EXTRA_BUILD_PARAMETER'})
        before=self.stored()
        self.assertEqual(self.reader().variables('900',{'PACKAGE_LIST'})['PACKAGE_LIST'],value['PACKAGE_LIST'])
        self.assertEqual(self.stored(),before)
        html=detail(variables={'PACKAGE_LIST':BASE,'EXTRA_BUILD_PARAMETER':'new'})
        self.fails(3,bm_pages.variables,html,self.config,'900',{'PACKAGE_LIST','EXTRA_BUILD_PARAMETER'})
        self.assertEqual(self.stored(),before)
        # New, previously unrequested fields are frozen only when actually used.
        bm_pages.variables(detail(variables={'PACKAGE_LIST':BASE,'ARCH':'armv7l'}),self.config,'900',{'ARCH'})
        self.assertEqual(len(self.stored()),3)
        path=next(p for p in (self.config.data_root/'inputs/variable-first-read').glob('*/*.json')
                  if json.loads(p.read_text())['name']=='PACKAGE_LIST')
        data=json.loads(path.read_text());data['value']='changed on disk';path.write_text(json.dumps(data))
        self.fails(4,self.reader().variables,'900',{'PACKAGE_LIST'})

    def test_simultaneous_first_reads_cannot_overwrite_and_secret_blocks_before_store(self):
        barrier=threading.Barrier(2);out=[]
        def work(text):
            barrier.wait(timeout=5)
            try:
                variable_pages.remember(self.config,'900',self.url,{'PACKAGE_LIST':text},{'PACKAGE_LIST'})
                out.append('stored')
            except FlowError as e:out.append(e.reason)
        threads=[threading.Thread(target=work,args=(BASE.replace('@100',cl),)) for cl in ('@100','@101')]
        for t in threads:t.start()
        for t in threads:t.join(5);self.assertFalse(t.is_alive())
        self.assertCountEqual(out,['stored','variable_page_changed'])
        self.assertEqual(len(self.stored()),1)
        before=self.stored()
        bad=dict(self.values,PACKAGE_LIST='Cookie: synthetic-b11-value') # credential-test-sample
        self.fails(4,bm_pages.variables,detail(b='901',variables=bad),self.config,'901',set(bad))
        self.assertEqual(self.stored(),before)

    def test_lookup_and_watch_propagate_changed_variable_todo(self):
        r=self.accepted();rid=r['request_id'];reader=self.reader()
        scan=submit_claim.collect(self.config,r,reader)
        submit_claim.merge_scan(self.config,r,scan,OBSERVE,now=self.start)
        data=pages();data['/build/900/variables']=detail(variables={'PACKAGE_LIST':BASE.replace('@100','@101'),'SHELVE_LIST':''})
        lookup=self.reader(data).lookup('500')
        self.assertEqual(lookup['exit_code'],3)
        self.assertEqual(lookup['todos'][0]['message'],'变量页已变化')
        from vd_cosmos_core.submit_model import read
        r=read(self.config,rid);scan=submit_claim.collect(self.config,r,self.reader(data))
        self.assertFalse(scan['candidates'])
        r=submit_claim.merge_scan(self.config,r,scan,OBSERVE,now=self.start+1)
        self.assertIn('变量页已变化',r['todos'])
        self.assertIsNone(r['binding'])

    def test_registered_text_compares_and_shipped_map_stays_unregistered(self):
        for entry in self.config.raw['submit']['property_map'].values():
            self.assertIsNone(entry['variable']);self.assertIsNone(entry['encoding'])
        p=self.config.raw['submit']['property_map']['EXTRA_BUILD_PARAMETER']
        p.update(variable='EXTRA_BUILD_PARAMETER',encoding='text',request_text_verified=True)
        result=bm_pages.compare({'form':dict.fromkeys(PROPERTIES,'')|{'PACKAGE_LIST':BASE}},
            {'PACKAGE_LIST':{'value':BASE},'EXTRA_BUILD_PARAMETER':{'value':'a different value'}},self.config)
        self.assertEqual(result['fields']['EXTRA_BUILD_PARAMETER'],'不一致')
        self.assertFalse(result['matches'])

    def test_recon25_empty_display_column_four_builds_and_exact_shapes(self):
        # recon25 confirms header/empty labels and these public vocabulary values.
        values=dict(self.values,BUILD_TYPE='Full',ARCH='armv7l',EXTRA_BUILD_PARAMETER='--threads 32')
        for build in ('19206687','19270912','19091860','19287341'):
            body=detail(b=build,variables=values)
            self.assertIn(b'<th>Name</th><th>Display Name</th><th>Value</th>',body)
            self.assertNotIn(b'Display label only',body)
            parsed=bm_pages.variables(body,self.config,build,set(values))
            for name in ('BUILD_TYPE','ARCH','EXTRA_BUILD_PARAMETER'):
                item=parsed[name]
                self.assertEqual(item['value'],values[name])
                self.assertEqual((item['leading_blank_lines'],item['trailing_blank_lines'],item['indented_lines']),(0,0,0))
            again=bm_pages.variables(body,self.config,build,set(values))
            self.assertEqual(parsed,again)
        self.assertFalse(list((self.config.data_root/'inputs/variable-first-read').glob('*/issues/*')))

    def test_recon25_registered_cmp_v1_without_old_flag_and_unregistered(self):
        form=self.form();form['EXTRA_BUILD_PARAMETER']='--threads 32'
        vals={'PACKAGE_LIST':{'value':BASE},'EXTRA_BUILD_PARAMETER':{'value':'--threads 32 \r\n'}}
        prop=self.config.raw['submit']['property_map']['EXTRA_BUILD_PARAMETER']
        self.assertEqual(bm_pages.compare({'form':form},vals,self.config)['fields']['EXTRA_BUILD_PARAMETER'],'未核验')
        prop.update(variable='EXTRA_BUILD_PARAMETER',encoding=None)
        self.assertEqual(bm_pages.compare({'form':form},vals,self.config)['fields']['EXTRA_BUILD_PARAMETER'],'未核验')
        prop['encoding']='text'
        for legacy_flag in (False,True):
            prop['request_text_verified']=legacy_flag
            self.assertEqual(bm_pages.compare({'form':form},vals,self.config)['fields']['EXTRA_BUILD_PARAMETER'],'一致')
        for changed in ('--threads=32',' --threads 32','--threads  32','--threads\n\n32'):
            vals['EXTRA_BUILD_PARAMETER']['value']=changed
            result=bm_pages.compare({'form':form},vals,self.config)
            self.assertEqual(result['fields']['EXTRA_BUILD_PARAMETER'],'不一致')
            self.assertFalse(result['matches'])
        prop['variable']='not_listed'
        self.assertEqual(bm_pages.compare({'form':form},vals,self.config)['fields']['EXTRA_BUILD_PARAMETER'],'未核验')

    def test_other_report_fixed_schema_rejects_added_display_column(self):
        html=report_html('armv7l',[pkg('foo')])
        html=html.replace('<th>Package</th><th>Path</th>','<th>Package</th><th>Display Name</th><th>Path</th>')
        html=html.replace('<td>foo</td><td>//example','<td>foo</td><td>not a path</td><td>//example')
        result=parse_report(html,'armv7l',self.config.raw['cosmos'],stable=True)
        self.assertIn('malformed_detail_row',result['issues'])
        self.assertEqual(result['report_state'],'结构未知')


class RerunChainTests(B1Case):
    def chain(self):
        data=pages()
        data['/history/4362']=history(['901','900'])
        data['/build/901']=detail('901','500',state='running')
        data['/build/901/variables']=detail('901','500',variables={'PACKAGE_LIST':BASE,'SHELVE_LIST':''})
        return data

    def test_same_hub_multiple_consistent_builds_chain_never_select_or_bind(self):
        result=self.reader(self.chain()).lookup('500')
        self.assertEqual(result['result'],'重跑链')
        self.assertIsNone(result['auto_selected'])
        self.assertEqual(result['conflicts'],[])
        chain=result['rerun_chains'][0]
        self.assertEqual(chain['hub_id'],'500')
        self.assertEqual([x['build_id'] for x in chain['builds']],['900','901'])
        self.assertEqual({x['status'] for x in chain['builds']},{'failed','running'})
        self.assertTrue(all(x['start_time'] for x in chain['builds']))
        with EventStore(self.config.data_root) as store:self.assertEqual(store.events(kinds=['bind']),[])

    def test_genuine_inconsistency_still_conflict_and_claim_chain_is_manual(self):
        data=self.chain();data['/build/901']=detail('901','500',pair='501:901:FAILED')
        self.assertEqual(self.reader(data).lookup('500')['result'],'冲突')
        r=self.accepted();scan=submit_claim.collect(self.config,r,self.reader(self.chain()))
        self.assertEqual(scan['result'],'重跑链')
        r=submit_claim.merge_scan(self.config,r,scan,OBSERVE,now=self.start)
        self.assertIsNone(r['binding']);self.assertIn('重跑链待人工选择',r['todos'])
        reader=self.reader(self.chain())
        prepared=submit_claim.prepare_attest(self.config,r['request_id'],'901',reader)
        chosen=submit_claim.attest(self.config,r['request_id'],prepared,HUMAN,prepared['required_words'],'FatTank explicitly chose 901',reader)
        self.assertEqual(chosen['binding']['build_id'],'901')

    def test_recon26_same_hub_two_real_ids_and_start_times_no_auto_selection(self):
        # IDs/times from recon26; statuses and package contents are synthetic.
        ids=('19238877','19241462');times=('2026-11-05 12:05:41','2026-11-05 15:42:50')
        data=pages(b=ids[0],h='37432138',begin=times[0])
        data['/history/4362']=history(list(reversed(ids)),begin=times[1])
        data['/build/'+ids[1]]=detail(ids[1],'37432138',begin=times[1])
        data['/build/'+ids[1]+'/variables']=detail(ids[1],'37432138',begin=times[1],variables={'PACKAGE_LIST':BASE,'SHELVE_LIST':''})
        result=self.reader(data).lookup('37432138')
        self.assertEqual(result['result'],'重跑链')
        self.assertEqual(result['conflicts'],[])
        self.assertIsNone(result['auto_selected'])
        builds=result['rerun_chains'][0]['builds']
        self.assertEqual([b['build_id'] for b in builds],list(ids))
        self.assertEqual([b['start_time'] for b in builds],[bm_pages.page_time(t,'Asia/Seoul') for t in times])
