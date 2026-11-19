"""Offline checks of the Hub gate and the private browser settings importer."""
import json
import stat
import subprocess
import sys

from helpers import REPO
from test_batch3a11b1 import B1Case
from vd_cosmos_core.submit_gate import Gate


class HubGateTests(B1Case):
    hub = 'http://127.0.0.1:8000'
    sso = 'https://sso.example.invalid'
    port = 'https://sso.example.invalid:443'

    def gate(self, **settings):
        self.config.raw['submit'].update(settings)
        return Gate(self.config, rehearse=True, local_origin=self.hub)

    def test_root_sso_chain_literal_host_port_query_and_method(self):
        g = self.gate(auth_paths=[
            {'host':'127.0.0.1:8000','path':path,'method':method}
            for path,method in (('/dashboard','GET'),('/signin','GET'),('/sso-initiate','GET'),('/sso-login','POST'))
        ] + [
            {'host':'sso.example.invalid','path':'/adfs/ls/','method':method} for method in ('GET','POST')
        ] + [{'host':'sso.example.invalid:443','path':'/adfs/ls/','method':'GET'}])
        chain = [(self.hub+'/', 'GET'), (self.hub+'/dashboard','GET'),
                 (self.hub+'/signin?redirect-url-after-sign-in','GET'),(self.hub+'/sso-initiate','GET'),
                 (self.sso+'/adfs/ls/?entry=one','GET'), (self.sso+'/adfs/ls/?entry=one','POST'),
                 (self.port+'/adfs/ls/?entry=two','GET'),(self.hub+'/sso-login','POST'),
                 (self.hub+'/dashboard','GET')]
        g.navigation(chain[0][0],login_entry=True)
        for i,(url,method) in enumerate(chain):
            self.assertTrue(g.request(url,method),url)
            if i+1<len(chain):self.assertTrue(g.response(url,302,chain[i+1][0]))
        self.assertFalse(g.request(self.port+'/adfs/ls/', 'POST'))
        self.assertFalse(g.request(self.port+'/adfs/ls/','GET',main_frame=False))
        self.assertFalse(g.request('https://sso.example.invalid:444/adfs/ls/', 'GET'))
        self.assertTrue(g.response(chain[-1][0],200));self.assertEqual(g.phase,'account')

    def test_manual_login_and_wicket_queries_cannot_use_auth_allowlist(self):
        entries=[{'host':'127.0.0.1:8000','path':path,'method':method}
                 for path,method in (('/signin','GET'),('/signin','POST'),('/dashboard','GET'))]
        g=self.gate(auth_paths=entries)
        self.assertTrue(g.request(self.hub+'/signin?redirect-url-after-sign-in','GET'))
        self.assertFalse(g.request(self.hub+'/signin?1-2.IFormSubmitListener-form','POST'))
        self.assertFalse(g.request(self.hub+'/dashboard?5-4.IBehaviorListener.0-widget','GET'))
        self.assertFalse(g.request(self.hub+'/dashboard?%35-4.IBehaviorListener.0-widget','GET'))
        self.assertFalse(g.response(self.hub+'/sso-login',302,'/signin?x=1&manual-login'))
        self.assertTrue(g.manual_login)
        self.assertFalse(g.request(self.hub+'/signin?manual-login','GET'))

    def test_versioned_static_paths_and_only_exact_query_shapes(self):
        g=self.gate(static_paths=['/assets/script-ver-*.js','/wicket/resource/theme-ver-123.css','/assets/icons.woff2'])
        for path,resource in (('/assets/script-ver-1700000000000.js','Script'),
                              ('/wicket/resource/theme-ver-9.css?v=01.A_b-2','Stylesheet'),
                              ('/assets/icons.woff2?'+'a'*32,'Font')):
            self.assertTrue(g.request(self.hub+path,'GET',resource=resource))
        for query in ('?v=','?v=a&v=b','?v=a&','?v=%32','?v='+'a'*65,
                      '?'+'A'*32,'?'+'a'*31,'?x=abc'):
            self.assertFalse(g.request(self.hub+'/assets/icons.woff2'+query,'GET',resource='Font'))
        self.assertFalse(g.request(self.hub+'/assets/icons.woff2?v=a','GET',resource='Other'))
        self.assertFalse(g.request(self.hub+'/assets/icons.woff2?v=a','POST',resource='Font'))
        self.assertFalse(g.request(self.sso+'/assets/icons.woff2?v=a','GET',resource='Font'))
        self.assertIsNone(g.fatal)

    def test_run_is_exact_single_main_document_get_and_numeric_editor_redirect(self):
        g=self.gate()
        g.phase='business'
        entry=self.hub+g.overview
        run=entry+'?7-1.ILinkListener-run'
        g.capture_run=True
        for url,kwargs in ((run,{'main_frame':False}), (run,{'resource':'XHR'}), (run,{'ajax':True}),
                           (entry+'?7-2.ILinkListener-run',{}), (entry+'?7-1.ILinkListener-other',{})):
            self.assertFalse(g.request(url,'GET',**kwargs))
        self.assertEqual(g.run_candidates,[])
        self.assertFalse(g.request(run,'GET'))
        self.assertEqual(g.run_candidates,[run])
        g.capture_run=False
        g.allow_run(run)
        self.assertFalse(g.request(entry+'?8-1.ILinkListener-run','GET'))
        self.assertTrue(g.request(run,'GET'))
        self.assertFalse(g.request(run,'GET'))
        self.assertTrue(g.response(run,302,'/wicket/page?99'))
        self.assertFalse(g.request(self.hub+'/wicket/page?98','GET'))
        self.assertTrue(g.request(self.hub+'/wicket/page?99','GET'))
        self.assertFalse(g.request(self.hub+'/wicket/page?99','GET'))
        for status, location in ((307,'/wicket/page?99'),(302,'/wicket/page?9&extra=1'),(302,self.sso+'/wicket/page?9')):
            g.run_response=run
            self.assertFalse(g.response(run,status,location))
            self.assertIsNone(g.run_response)

    def test_dismissal_blocks_even_allowlisted_request_and_sets_fatal(self):
        g=self.gate(static_paths=['/assets/site.css']);g.phase='business';g.dismissing=True
        self.assertFalse(g.request(self.hub+'/assets/site.css','GET',resource='Stylesheet'))
        self.assertEqual(g.fatal,'request_during_notice_dismissal')


class WriterTests(B1Case):
    def run_writer(self, values):
        path=self.root/'browser.json'
        path.write_text(json.dumps(values))
        result=subprocess.run([sys.executable,str(REPO/'vd-cosmos-core/scripts/apply_property_map.py'),
                               '--config',str(self.path),'--browser-input',str(path)],
                              check=False,capture_output=True,text=True,timeout=30)
        return result, json.loads(result.stdout)

    def test_only_browser_fields_change_and_output_has_only_names(self):
        values={'auth_paths':[{'host':'one.example.invalid:443','path':'/signin','method':'GET'}],
                'static_paths':['/wicket/resource/test-ver-*.js'],'target_config':'root/Family/Release',
                'target_config_id':'123456','account':'private-fixture-user'}
        original=self.path.read_bytes();before=json.loads(original)
        result,value=self.run_writer(values)
        self.assertEqual(result.returncode,0)
        self.assertEqual(set(value['submit']['added']+value['submit']['changed']),set(values))
        for private in ('private-fixture-user','one.example.invalid','root/Family/Release','123456'):
            self.assertNotIn(private,result.stdout+result.stderr)
        after=json.loads(self.path.read_bytes())
        before['submit'].update(values)
        self.assertEqual(before,after)
        backup,=self.root.glob('config.json.bak-*')
        self.assertEqual((backup.read_bytes(),stat.S_IMODE(backup.stat().st_mode)),(original,0o600))
        self.assertEqual(self.run_writer(values)[1]['submit'],{'added':[],'changed':[]})
        self.assertEqual(list(self.root.glob('config.json.bak-*')),[backup])

    def test_shape_allowlists_and_either_confirmation_block_the_write(self):
        invalid=[{'unrelated':'secret-fixture'}, {'auth_paths':[{'host':'x.invalid:99999','path':'/','method':'GET'}]},
                 {'auth_paths':[{'host':'x.invalid','path':'/login?v=x','method':'GET'}]},
                 {'static_paths':['/assets/*.js']},{'target_config':'root//branch'},
                 {'account':'  someone'},{'target_config_id':14}]
        for data in invalid:
            before=self.path.read_bytes()
            result,_=self.run_writer(data)
            self.assertEqual(result.returncode,2,data)
            self.assertEqual(self.path.read_bytes(),before)
        for field in ('property_map_confirmed','gate_patterns_confirmed'):
            config=json.loads(self.path.read_bytes())
            config['submit'].update(property_map_confirmed=False,gate_patterns_confirmed=False)
            config['submit'][field]=True
            self.path.write_text(json.dumps(config))
            before=self.path.read_bytes()
            self.assertEqual(self.run_writer({'account':'changed'})[0].returncode,4)
            self.assertEqual(self.path.read_bytes(),before)
        self.assertFalse(list(self.root.glob('config.json.bak-*')))
