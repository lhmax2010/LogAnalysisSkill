import copy
from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from helpers import config_data, REPO
from bm_helpers import BASE, DATE, STAMP, detail, history, overview, pages, MemoryTransport
from vd_cosmos_core.config import load_config
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.commands import Category, CommandContext
from vd_cosmos_core.state import EventStore
from vd_cosmos_core.locks import OperationLock
from vd_cosmos_core.bm_reader import Reader
from vd_cosmos_core import bm_pages, submit_claim, submit_model, submit_watch
from vd_cosmos_core.bm_transport import clock_sample
from vd_cosmos_core.submit_config import PROPERTIES
from vd_cosmos_core.submit_doctor import doctor

HUMAN=CommandContext('attest',Category.HUMAN,True)
RESOLVE=CommandContext('resolve',Category.HUMAN,True)
EXTERNAL=CommandContext('submit',Category.EXTERNAL,True)
OBSERVE=CommandContext('submit.watch',Category.OBSERVE)


class B1Case(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name); raw=config_data(self.root/'data')
        raw['cosmos'].update(bm_host='bm.example.invalid',hub_host='hub.example.invalid',bm_config_id='4362',bm_scan_interval_s=0,hub_id_slack=10)
        raw['submit']={'account':'fixture-user'}; raw['poll'].update(lock_wait_s=.3,watch_interval_s=.05)
        self.path=self.root/'config.json'; self.path.write_text(json.dumps(raw)); self.config=load_config(self.path)
        self.start=bm_pages.page_time(DATE,'Asia/Seoul')
    def reader(self, data=None): return Reader(self.config,transport=MemoryTransport(data or pages()),sleep=lambda _:None)
    def form(self): return dict.fromkeys(PROPERTIES,'') | {'PACKAGE_LIST':BASE}
    def accepted(self, *, H_pre=490, click=True, form=None):
        r=submit_model.create_request(self.config,EXTERNAL,form or self.form(),'fixture',now=self.start)
        return submit_model.record_outcome(self.config,r['request_id'],EXTERNAL,'accepted',now=self.start,
            click_time=self.start if click else None,H_pre=H_pre,
            click_clock={'valid':True,'offset_s':0,'error_s':0} if click else {})
    def fails(self, code, fn, *args, **kwargs):
        with self.assertRaises(FlowError) as raised: fn(*args,**kwargs)
        self.assertEqual(raised.exception.code,code); return raised.exception


class RelationAndComparisonTests(B1Case):
    def test_hub_identity_and_side_evidence_closed_shapes(self):
        d=bm_pages.detail(detail(pair='500:900:SUCCESSFUL'),self.config,'900')
        self.assertEqual(d['hub_id'],'500'); self.assertFalse(d['conflict'])
        self.assertTrue(bm_pages.detail(detail(pair='501:900:FAILED'),self.config,'900')['conflict'])
        self.assertFalse(bm_pages.detail(detail(pair='501:899:FAILED'),self.config,'900')['conflict'])
        self.assertIsNone(bm_pages.detail(detail(h=None,pair='500:900:FAILED'),self.config,'900')['hub_id'])
        for bad in (detail(hub_host='other.invalid'),detail().replace(b'/build/500',b'/build/500.latest'),
                    detail().replace(b'/build/500',b'/build/500?q=x'),detail().replace(b'Hub Link :',b'Hub Link : Hub Link :'),
                    detail().replace(b'Hub Link :',b'unregistered Hub Link :'),
                    detail().replace(b'class="build-header"',b'class="fake-build-header"'),detail(b='901')):
            self.fails(5,bm_pages.detail,bad,self.config,'900')
        description=detail(h=None)+b'<p>Hub Link : <a href="https://hub.example.invalid/build/500">500</a></p>'
        self.assertIsNone(bm_pages.detail(description,self.config,'900')['hub_id'])
    def test_multiple_links_reference_and_overview_conflict(self):
        bad=detail().replace(b'</a><br></div>',b'</a><a href="https://hub.example.invalid/build/501">501</a><br></div>')
        self.fails(5,bm_pages.detail,bad,self.config,'900')
        data=pages();data['/overview/4362']=overview([('900','501')])
        self.assertEqual(self.reader(data).lookup('500')['result'],'冲突')
    def test_cmp_v1_and_unregistered_text_and_parsed_base(self):
        self.assertEqual(bm_pages.cmp_v1('a \r\nb\t\r\n \r\n'), 'a\nb')
        self.assertNotEqual(bm_pages.cmp_v1(' a'),bm_pages.cmp_v1('a'))
        self.assertNotEqual(bm_pages.cmp_v1('a\n\nb'),bm_pages.cmp_v1('a\nb'))
        self.assertEqual(bm_pages.cmp_v1('a \r\nb\t'),bm_pages.cmp_v1('a\nb'))
        base=BASE+'//example/tree/product/packages/bar/...@101\n'
        self.assertEqual(bm_pages.base_digest(base,self.config),bm_pages.base_digest('\n'+''.join(reversed(base.splitlines(True))),self.config))
        form=self.form();form['EXTRA_BUILD_PARAMETER']='--threads 32'
        vals={'PACKAGE_LIST':{'value':BASE},'EXTRA_BUILD_PARAMETER':{'value':'--threads=32'}}
        prop=self.config.raw['submit']['property_map']['EXTRA_BUILD_PARAMETER']
        prop.update(variable='EXTRA_BUILD_PARAMETER',encoding='text')
        result=bm_pages.compare({'form':form},vals,self.config)
        self.assertIn('比较规则未确认',result['fields']['EXTRA_BUILD_PARAMETER'])
        prop['request_text_verified']=True
        self.assertIn('比较规则未确认',bm_pages.compare({'form':form},vals,self.config)['fields']['EXTRA_BUILD_PARAMETER'])
        vals['EXTRA_BUILD_PARAMETER']['value']='--threads 32';vals['SHELVE_LIST']={'value':'//x@903'}
        self.assertFalse(bm_pages.compare({'form':form},vals,self.config)['matches'])
        vals['SHELVE_LIST']['value']='';vals['EMAIL_CC']={'value':'different'}
        self.assertTrue(bm_pages.compare({'form':form},vals,self.config)['matches'])
        for name in ('Image Skip?',):
            self.config.raw['submit']['property_map'][name].update(variable=name,encoding='text',request_text_verified=True)
            vals[name]={'value':'different'}
            self.assertFalse(bm_pages.compare({'form':form},vals,self.config)['matches']);del vals[name]
    def test_variable_raw_shape_preserves_template_layout(self):
        html=detail(variables={'EXTRA_BUILD_PARAMETER':'PLACEHOLDER'})
        html=html.replace(b'PLACEHOLDER',b'  <pre>\n  first\n\nsecond\n</pre><li>end</li>\n')
        value=bm_pages.variables(html,self.config,'900',{'EXTRA_BUILD_PARAMETER'})['EXTRA_BUILD_PARAMETER']
        self.assertEqual(value['value'],'  \n  first\n\nsecond\nend\n\n')
        self.assertEqual(value['leading_blank_lines'],1)
        self.assertEqual(value['trailing_blank_lines'],2)
        self.assertEqual(value['indented_lines'],2)
        self.assertEqual(value['first_line_indent'],2)
        self.assertEqual(bm_pages.cmp_v1(value['value']),'\n  first\n\nsecond\nend')
    def test_variable_two_cells_and_fixed_enum_original_case(self):
        html=detail(variables={'BUILD_TYPE':'True'})
        value=bm_pages.variables(html,self.config,'900',{'BUILD_TYPE'})['BUILD_TYPE']
        self.assertEqual(value['enum_display'],'True')
        html=detail(b='901',variables={'BUILD_TYPE':'Full'})
        value=bm_pages.variables(html,self.config,'901',{'BUILD_TYPE'})['BUILD_TYPE']
        self.assertEqual(value['cells'],2)
        self.assertEqual(value['enum_display'],'Full')
    def test_enum_unobserved_and_variable_whitelist_never_returns_secret(self):
        prop=self.config.raw['submit']['property_map']['Image Skip?'];prop.update(variable='IMAGE_SKIP',encoding='enum',observed_values=['no'])
        form=self.form();form['Image Skip?']='yes'
        result=bm_pages.compare({'form':form},{'PACKAGE_LIST':{'value':BASE},'IMAGE_SKIP':{'value':'yes'}},self.config)
        self.assertEqual(result['fields']['Image Skip?'],'未核验')
        html=detail(variables={'PACKAGE_LIST':BASE,'BART_PASSWD':'PRIVATE_FIXTURE_VALUE','EXTRA_BUILD_PARAMETER':'\n  --threads 32\n'})
        values=bm_pages.variables(html,self.config,'900',{'PACKAGE_LIST','EXTRA_BUILD_PARAMETER'})
        self.assertNotIn('PRIVATE_FIXTURE_VALUE',json.dumps(values));self.assertNotIn('BART_PASSWD',json.dumps(values))
        self.assertEqual(values['EXTRA_BUILD_PARAMETER']['value'],'\n  --threads 32\n')
        self.fails(4,bm_pages.variables,html,self.config,'900',{'BART_PASSWD'})
        duplicate=html.replace(b'</tbody>',b'<tr><td>PACKAGE_LIST</td><td>display</td><td><pre>x</pre></td></tr></tbody>')
        self.fails(5,bm_pages.variables,duplicate,self.config,'900',{'PACKAGE_LIST'})


class LookupTests(B1Case):
    def test_unique_conflict_missing_and_no_negative_cache(self):
        reader=self.reader(); r=reader.lookup('500');self.assertEqual(r['result'],'唯一');self.assertFalse(r['uniqueness_proven'])
        self.assertEqual(r['candidates'][0]['package_list_count'],1)
        self.assertIn('900',reader.cache)
        data=pages(h=None);reader=self.reader(data);self.assertEqual(reader.lookup('500')['result'],'未定位');self.assertEqual(reader.cache,{})
        data['/build/900']=detail(h='500');data['/build/900/variables']=detail(variables={'PACKAGE_LIST':BASE})
        self.assertEqual(reader.lookup('500')['result'],'唯一')
        data=pages();data['/history/4362']=history(['900','899']);data['/build/899']=detail('899','500');data['/build/899/variables']=detail('899','500',variables={'PACKAGE_LIST':BASE})
        self.assertEqual(self.reader(data).lookup('500')['result'],'重跑链')
    def test_history_overlap_topup_anchor_and_retention_wording(self):
        data=pages();data['/history/4362']=[history(['110','109','108'],total=6,next_url='/history/4362?p=2'),history(['111','110','109'],total=7,next_url='/history/4362?p=2')]
        data['/history/4362?p=2']=history(['108','106','105'],first=4,total=7,next_url='/history/4362?p=3')
        data['/history/4362?p=3']=history(['104'],first=7,total=7)
        for b in ('111','110','109','108','106','105','104'):data['/build/'+b]=detail(b,'500')
        r=self.reader(data).scan(since=self.start-100)
        self.assertEqual(r['anchor']['build_id'],'111');self.assertIn('111',r['details'])
        self.assertNotIn('history_gap',r['issues']);self.assertEqual(r['history_retention'],'未核验')
        self.assertEqual(r['coverage_scope'],'当前保留记录中')
    def test_history_gap_repeated_page_reorder_anchor_lost_limits(self):
        for second,issue in [(history(['107','106'],first=4,total=5),'history_gap'),
                             (history(['110','109','108'],total=6),'history_page_repeated'),
                             (history(['107','111','106'],first=4,total=6),'history_reordered')]:
            data=pages();data['/history/4362']=history(['110','109','108'],total=6,next_url='/history/4362?p=2');data['/history/4362?p=2']=second
            for b in ('110','109','108','107','106','111'):data['/build/'+b]=detail(b,'500')
            r=self.reader(data).scan(since=self.start-1);self.assertFalse(r['coverage']);self.assertIn(issue,r['issues'])
        data=pages();data['/history/4362']=[history(['900']),history(['899'])];data['/build/899']=detail('899')
        self.assertIn('anchor_not_reached',self.reader(data).scan()['issues'])
    def test_locate_three_pass_snapshot_prioritizes_late_group_and_budget(self):
        data={'/overview/4362':overview()};groups=[]
        for i in range(45):
            ids=[str(10000-i*30-j) for j in range(30)];groups.append(ids)
            next_url=f'/history/4362?p={i+2}' if i<44 else None
            data['/history/4362' if i==0 else f'/history/4362?p={i+1}']=history(ids,first=i*30+1,total=1350,next_url=next_url)
            for j,b in enumerate(ids):data['/build/'+b]=detail(b,str(510 if i==41 else 490 if i==44 else 2000))
        target=groups[41][5];data['/build/'+target]=detail(target,'500');data['/build/'+target+'/variables']=detail(target,'500',variables={'PACKAGE_LIST':BASE})
        self.config.raw['cosmos']['bm_lookup_detail_max']=1000
        reader=self.reader(data);r=reader.lookup('500')
        self.assertEqual([c['build_id'] for c in r['candidates']],[target]);self.assertFalse(r['coverage'])
        self.assertLess(r['detail_read_order'].index(target),100)
        self.assertIn('bm_detail_budget',r['issues'])
    def test_cache_only_ended_hub_and_unread_pending_not_dropped(self):
        data=pages(state='running');reader=self.reader(data);reader.scan();self.assertEqual(reader.cache,{})
        self.config.raw['cosmos']['bm_lookup_detail_max']=1;self.config.raw['cosmos']['bm_pending_max']=1
        data['/history/4362']=history(['900','899','898'])
        r=self.reader(data).scan();self.assertTrue({'899','898'}<=set(r['pending']));self.assertIn('pending_limit',r['issues'])
    def test_reader_budget_spans_pre_scan_and_transport_failure_is_error(self):
        reader=self.reader(pages(state='running'))
        self.config.raw['cosmos']['bm_lookup_detail_max']=1
        reader.detail('900',fresh=True)
        result=reader.scan()
        self.assertEqual(result['exit_code'],6)
        self.assertIn('bm_detail_budget',result['issues'])
        failed=self.reader()
        with patch.object(failed.transport,'read',side_effect=FlowError(5,'http_status_error')):
            result=failed.lookup('500')
        self.assertEqual(result['exit_code'],5)
        self.assertEqual(result['result'],'未定位')
        self.assertFalse(result['coverage'])
    def test_candidates_filter_detail_reads_reruns_use_live_overview(self):
        data=pages()
        data['/history/4362']=history(['900','899'],versions={'899':'[other-user] build'})
        data['/build/899']=detail('899','500')
        reader=self.reader(data)
        reader.scan(since=self.start-1,account_only=True)
        self.assertNotIn('/build/899',reader.transport.reads)
        data['/overview/4362']=overview([('899','500')])
        reader=self.reader(data)
        result=reader.scan(since=self.start-1,rerun=True)
        self.assertEqual(result['details']['899']['identity'],'overview_only')
        self.assertNotIn('/build/899',reader.transport.reads)
        self.assertNotIn('899',reader.cache)
        data['/overview/4362']=overview()
        reader=self.reader(data);result=reader.scan(since=self.start-1,rerun=True)
        self.assertIn('/build/899',reader.transport.reads)
        self.assertTrue(result['details']['899']['ended'])
    def test_clock_skew_timezones_and_duration_samples(self):
        self.assertEqual(bm_pages.duration('1h:14m:28s'),4468)
        self.assertEqual(bm_pages.duration('1 hour 49 minutes 40 seconds'),6580)
        self.assertEqual(bm_pages.duration('31 seconds'),31)
        for date,elapsed,ok in [('Sat, 17 Oct 2026 06:00:00 GMT',1,True),(None,1,False),('Sat, 17 Oct 2026 06:00:00 GMT',11,False)]:
            self.assertEqual(clock_sample(date,self.start,self.start+elapsed,elapsed)['valid'],ok)
        self.assertFalse(clock_sample('Sat, 17 Oct 2026 06:00:00 GMT',self.start,self.start+100,1)['valid'])
        reader=self.reader({'/overview/4362':overview(sample=True)})
        reader.transport.clock['server_time']=self.start+3600
        self.assertEqual(doctor(self.config,reader=reader,package_probe=lambda:{'verified':True,'count':0})['timezone_check'],'通过')
        self.config.raw['cosmos']['bm_display_tz']='Asia/Shanghai'
        self.assertEqual(doctor(self.config,reader=reader,package_probe=lambda:{'verified':True,'count':0})['exit_code'],3)
        result=doctor(self.config,reader=self.reader(),package_probe=lambda:{'verified':True,'count':0})
        self.assertEqual(result['timezone_check'],'页面时区未验证')
    def test_lookup_readonly_does_not_resolve_uncertain(self):
        r=submit_model.create_request(self.config,EXTERNAL,self.form(),'fixture');submit_model.record_outcome(self.config,r['request_id'],EXTERNAL,'uncertain')
        with EventStore(self.config.data_root) as store:head=store.head()
        self.assertEqual(self.reader().lookup('500')['result'],'唯一')
        with EventStore(self.config.data_root) as store:self.assertEqual(head,store.head())


class RequestAndClaimTests(B1Case):
    def test_digest_reuse_duplicate_round_and_uncertainty_cross_request(self):
        form=self.form();form['PACKAGE_LIST']+= '//example/tree/product/packages/bar/...@101\n'
        r=submit_model.create_request(self.config,EXTERNAL,form,'reason');form['PACKAGE_LIST']='\n'+''.join(reversed(form['PACKAGE_LIST'].splitlines(True)))
        self.assertEqual(submit_model.create_request(self.config,EXTERNAL,form,'other reason')['request_id'],r['request_id'])
        submit_model.record_outcome(self.config,r['request_id'],EXTERNAL,'accepted')
        self.fails(6,submit_model.create_request,self.config,EXTERNAL,form,'again',now=time.time()+25*3600)
        r2=submit_model.create_request(self.config,EXTERNAL,form,'new round',resubmit_of=r['request_id']);submit_model.record_outcome(self.config,r2['request_id'],EXTERNAL,'accepted')
        self.fails(6,submit_model.create_request,self.config,EXTERNAL,form,'older',resubmit_of=r['request_id'])
        form['PACKAGE_LIST']=BASE.replace('@100','@999');r3=submit_model.create_request(self.config,EXTERNAL,form,'changed')
        submit_model.record_outcome(self.config,r3['request_id'],EXTERNAL,'uncertain')
        form['PACKAGE_LIST']=BASE.replace('@100','@888');self.fails(6,submit_model.create_request,self.config,EXTERNAL,form,'bypass')
    def test_resolve_atomic_tasks_manual_time_and_pending_rerun(self):
        r=submit_model.create_request(self.config,EXTERNAL,self.form(),'fixture')
        submit_model.record_outcome(self.config,r['request_id'],EXTERNAL,'uncertain')
        submit_model.resolve(self.config,RESOLVE,session='s1',hub_id='500',mode='manual-rerun',reason='checked',now=self.start)
        self.fails(3,submit_model.resolve,self.config,RESOLVE,request_id=r['request_id'],mode='not-submitted',reason='history checked',checked_at='2026-11-14')
        resolved=submit_model.resolve(self.config,RESOLVE,request_id=r['request_id'],hub_id='500',mode='manual-submit',reason='history checked',now=self.start)
        self.assertIsNone(resolved['click_time']);self.assertEqual(resolved['observation']['supplementary_start'],self.start)
        self.assertEqual(len(resolved['manual_reruns']),1)
        again=submit_model.resolve(self.config,RESOLVE,request_id=r['request_id'],hub_id='500',mode='build-id',reason='again',now=self.start+100)
        self.assertEqual(resolved['version'],again['version']);self.assertEqual(resolved['observation'],again['observation'])
    def test_not_submitted_no_observation_and_lookup_absence_refused(self):
        r=submit_model.create_request(self.config,EXTERNAL,self.form(),'fixture')
        submit_model.record_outcome(self.config,r['request_id'],EXTERNAL,'uncertain')
        self.fails(4,submit_model.resolve,self.config,RESOLVE,request_id=r['request_id'],mode='not-submitted',reason='未定位',checked_at='today')
        resolved=submit_model.resolve(self.config,RESOLVE,request_id=r['request_id'],mode='not-submitted',reason='manual history checked',checked_at='today')
        self.assertIsNone(resolved['observation'])
    def test_candidate_only_and_both_words_hpre_unknown_and_hard_checks(self):
        r=self.accepted(H_pre=None,click=False);rid=r['request_id'];reader=self.reader()
        prepared=submit_claim.prepare_attest(self.config,rid,'900',reader)
        self.assertIsNone(submit_model.read(self.config,rid)['binding'])
        self.assertIn('claim-unverified',prepared['required_words'])
        self.fails(3,submit_claim.attest,self.config,rid,prepared,HUMAN,['900'],'checked',reader)
        bound=submit_claim.attest(self.config,rid,prepared,HUMAN,['claim-unverified'],'checked',reader)
        self.assertEqual(bound['binding']['build_id'],'900');self.assertIsNone(bound['H_pre'])
        self.assertEqual(submit_claim.attest(self.config,rid,prepared,HUMAN,['claim-unverified'],'repeat',reader)['already_confirmed'],True)
    def test_attest_outside_candidates_hard_guards_and_words_independent(self):
        r=self.accepted(H_pre=None,click=False);rid=r['request_id'];data=pages();data['/history/4362']=history(['899']);data['/build/899']=detail('899','499');data['/build/899/variables']=detail('899','499',variables={'PACKAGE_LIST':BASE})
        prepared=submit_claim.prepare_attest(self.config,rid,'900',self.reader(data))
        self.assertEqual(set(prepared['required_words']),{'claim-unverified','claim-outside-candidates'})
        for words in (['900'],['claim-unverified'],['claim-outside-candidates']):
            self.fails(3,submit_claim.attest,self.config,rid,prepared,HUMAN,words,'checked',self.reader(data))
        self.config.raw['submit']['hub_id_monotonic_confirmed']=True
        old=copy.deepcopy(r);old['H_pre']=500
        self.fails(4,submit_claim.hard_checks,self.config,old,bm_pages.detail(detail(),self.config,'900'),{})
        self.fails(4,submit_claim.hard_checks,self.config,r,bm_pages.detail(detail(config='4359'),self.config,'900'),{})
        old=copy.deepcopy(r);old.update(click_time=self.start+2*86400,click_clock={'valid':True,'offset_s':0,'error_s':0})
        self.fails(4,submit_claim.hard_checks,self.config,old,bm_pages.detail(detail(),self.config,'900'),{})
        d=bm_pages.detail(detail(),self.config,'900')
        self.fails(4,submit_claim.hard_checks,self.config,r,d,{'other':{'request_id':'other','hub_id':'500'}})
    def test_confirmation_basis_changes_but_not_anchor_and_version_race(self):
        r=self.accepted();rid=r['request_id'];reader=self.reader();p=submit_claim.prepare_attest(self.config,rid,'900',reader)
        current=submit_model.read(self.config,rid);scan=copy.deepcopy(current['scan']);scan['anchor']['build_id']='99999'
        submit_model.mutate(self.config,rid,current['version'],OBSERVE,{'scan':scan},kind='submit_observation')
        bound=submit_claim.attest(self.config,rid,p,HUMAN,p['required_words'] or ['900'],'checked',reader)
        self.assertIsNotNone(bound['binding'])
        self.fails(6,submit_model.mutate,self.config,rid,current['version'],OBSERVE,{'scan':scan},kind='submit_observation')
    def test_network_outside_lock_version_change_discards_scan(self):
        r=self.accepted();rid=r['request_id'];entered=threading.Event();release=threading.Event()
        data=pages();orig=data['/history/4362']
        def blocked(): entered.set();self.assertTrue(release.wait(5));return orig
        data['/history/4362']=blocked;results=[]
        thread=threading.Thread(target=lambda:results.append(submit_watch.step(self.config,rid,self.reader(data))))
        thread.start();self.assertTrue(entered.wait(3))
        current=submit_model.read(self.config,rid)
        submit_model.mutate(self.config,rid,current['version'],HUMAN,{'resolution_reason':'concurrent human update'})
        release.set();thread.join(5);self.assertFalse(thread.is_alive());self.assertTrue(results[0]['scan_discarded'])
    def test_heartbeat_not_scan_duration_and_resume_gap(self):
        r=self.accepted(click=False);rid=r['request_id'];interval=self.config.raw['poll']['watch_interval_s']
        self.assertFalse(submit_watch.heartbeat(self.config,rid,now=self.start)['interrupted'])
        for i in range(1,11):self.assertFalse(submit_watch.heartbeat(self.config,rid,now=self.start+i*interval)['interrupted'])
        self.assertTrue(submit_watch.heartbeat(self.config,rid,now=self.start+30*interval)['interrupted'])
        with OperationLock(self.config.data_root,'observation',rid):
            self.fails(6,submit_watch.run,self.config,rid,lambda cache:self.reader(),max_scans=1)
            # Manual state changes require only the request lock.
            submit_model.mutate(self.config,rid,r['version'],HUMAN,{'resolution_reason':'not blocked by observation'})
    def test_rerun_pending_retention_and_supplementary_bound(self):
        r=self.accepted(click=False);rid=r['request_id'];reader=self.reader();p=submit_claim.prepare_attest(self.config,rid,'900',reader)
        bound=submit_claim.attest(self.config,rid,p,HUMAN,p['required_words'],'checked',reader)
        data=pages();data['/history/4362']=history(['901','900']);data['/build/901']=detail('901','500');data['/build/901/variables']=detail('901','500',variables={'PACKAGE_LIST':BASE})
        updated=submit_watch.step(self.config,rid,self.reader(data),now=self.start+4000)
        self.assertIn('发现重跑',updated['todos']);self.assertEqual(updated['binding']['build_id'],'900')
        data['/build/901']=FlowError(5,'bm_http_status',status=404)
        updated=submit_watch.step(self.config,rid,self.reader(data),now=self.start+4100)
        self.assertIn('901',updated['seen']);self.assertFalse(updated['observation_complete'])
        self.assertLessEqual(updated['lower_bound'],self.start)
    def test_observation_cannot_authorize_and_task_persists_restart(self):
        r=self.accepted();rid=r['request_id']
        self.fails(4,submit_model.mutate,self.config,rid,r['version'],OBSERVE,{'binding':{'build_id':'900'}},kind='submit_observation')
        self.assertEqual(submit_model.read(self.config,rid)['observation'],r['observation'])
    def test_known_Hpre_confirmation_matrix_and_no_replacement(self):
        r=self.accepted();d=bm_pages.detail(detail(),self.config,'900')
        scan={'candidates':[d],'coverage':True,'account_rows':[d]}
        self.assertEqual(submit_claim.confirmation(self.config,r,scan,d)['required_words'],[])
        scan['account_rows'].append(dict(d,build_id='901',hub_id='501'))
        self.assertEqual(submit_claim.confirmation(self.config,r,scan,d)['required_words'],['claim-unverified'])
        scan['account_rows']=[d];r['H_pre']=501
        self.assertIn('claim-unverified',submit_claim.confirmation(self.config,r,scan,d)['required_words'])
        self.config.raw['submit']['hub_id_monotonic_confirmed']=True
        self.fails(4,submit_claim.hard_checks,self.config,r,d,{})
        r['H_pre']=None
        submit_claim.hard_checks(self.config,r,d,{})
        self.assertIn('claim-unverified',submit_claim.confirmation(self.config,r,scan,d)['required_words'])
    def test_manual_start_lower_bound_and_observation_deadline_running(self):
        r=self.accepted(click=False);rid=r['request_id'];reader=self.reader()
        p=submit_claim.prepare_attest(self.config,rid,'900',reader)
        bound=submit_claim.attest(self.config,rid,p,HUMAN,p['required_words'],'manual',reader)
        bound['observation']['supplementary_start']=self.start+4*3600
        self.assertEqual(submit_claim.lower_bound(self.config,bound),self.start-900)
        data=pages(state='running');result=submit_watch.step(self.config,rid,self.reader(data),now=self.start+10*86400)
        self.assertFalse(result['observation_complete'])
        # A prior ended cache must not be used to test a running build: clear it explicitly in the fixture state.
        current=submit_model.read(self.config,rid)
        submit_model.mutate(self.config,rid,current['version'],OBSERVE,{'cache':{}},kind='submit_observation')
        result=submit_watch.step(self.config,rid,self.reader(data),now=self.start+10*86400)
        self.assertIsNone(result['deadline']);self.assertFalse(result['observation_complete'])
    def test_time_skew_margin_preserves_utc_and_clock_unknown(self):
        r=self.accepted();r['click_time']=10000;r['click_clock']={'valid':True,'offset_s':-360,'error_s':2}
        self.assertEqual(submit_claim.lower_bound(self.config,r),8740)
        d=bm_pages.detail(detail(),self.config,'900');d['start_time']=9000
        submit_claim.hard_checks(self.config,r,d,{})
        d['start_time']=6000;self.fails(4,submit_claim.hard_checks,self.config,r,d,{})
        r['click_clock']={};submit_claim.hard_checks(self.config,r,d,{})
        self.assertIn('claim-unverified',submit_claim.confirmation(self.config,r,{'candidates':[d],'coverage':True},d)['required_words'])

    def test_binding_uses_reader_identity_report_mismatch_blocks_workflow(self):
        from vd_cosmos_core.http_reader import HTTPReportReader
        from vd_cosmos_core.versions import build_key
        from vd_cosmos_core.submit_projection import apply
        from vd_cosmos_core.observation import stopped
        r=self.accepted();rid=r['request_id'];p=submit_claim.prepare_attest(self.config,rid,'900',self.reader())
        submit_claim.attest(self.config,rid,p,HUMAN,p['required_words'] or ['900'],'checked',self.reader())
        key=build_key(HTTPReportReader(self.config,'900'))
        observation={'report_state':'完整','reports':{'armv7l':{'input_rows':[{'path':BASE.strip().split('@')[0],'cl':'100','shelve':False}]}},'terminal_prerequisite_met':True}
        with EventStore(self.config.data_root) as store:
            self.assertEqual(len(store.events(key,kinds=['bind'])),1)
            self.assertEqual(apply(self.config,store,key,copy.deepcopy(observation))['binding_input_check'],'一致')
            bad=copy.deepcopy(observation);bad['reports']['armv7l']['input_rows'][0]['cl']='101'
            checked=apply(self.config,store,key,bad)
            self.assertEqual(checked['binding_input_check'],'绑定不一致');self.assertTrue(stopped(checked));self.assertFalse(checked['terminal_prerequisite_met'])
        current=submit_model.read(self.config,rid)
        submit_model.mutate(self.config,rid,current['version'],OBSERVE,{'result_caution':'可能不是最终构建'},kind='submit_observation')
        with EventStore(self.config.data_root) as store:
            checked=apply(self.config,store,key,observation)
            self.assertFalse(checked['terminal_prerequisite_met']);self.assertEqual(checked['result_caution'],'可能不是最终构建')
    def test_unresolved_raw_click_cannot_be_bypassed_and_config_invalid(self):
        r=submit_model.create_request(self.config,EXTERNAL,self.form(),'fixture')
        with EventStore(self.config.data_root) as store:
            h=store.append(EXTERNAL,'submit_session_started',{'target':r['target']},store.head(),request_id=r['request_id'],operation_id='s')
            store.append(EXTERNAL,'click_intent',{},h,request_id=r['request_id'],operation_id='s')
        form=self.form();form['PACKAGE_LIST']=BASE.replace('@100','@200')
        self.fails(6,submit_model.create_request,self.config,EXTERNAL,form,'bypass raw intent')
        raw=json.loads(self.path.read_text());raw['submit']['form']=[];self.path.write_text(json.dumps(raw))
        self.fails(2,load_config,self.path)

    def test_doctor_offline_cli_non_tty_and_via_hub_B2_error(self):
        with patch('vd_cosmos_core.bm_transport.AnonymousTransport.read',side_effect=AssertionError('network forbidden')):
            result=doctor(self.config,package_probe=lambda:{'verified':True,'count':0});self.assertFalse(result['online'])
        self.assertEqual(doctor(self.config,package_probe=lambda:{'verified':True,'count':1})['exit_code'],6)
        for command in ('attest','resolve','bind','rebind','abandon'):
            run=subprocess.run([sys.executable,str(REPO/'vd-cosmos-submit/scripts/run.py'),command,'--config',str(self.path)],capture_output=True,text=True)
            self.assertEqual(run.returncode,2,run.stdout);json.loads(run.stdout)
        run=subprocess.run([sys.executable,str(REPO/'vd-cosmos-submit/scripts/run.py'),'lookup','--config',str(self.path),'--hub-id','500','--via-hub'],capture_output=True,text=True)
        self.assertEqual(run.returncode,6);self.assertIn('requires_B2_browser',run.stdout)

if __name__=='__main__':unittest.main()
