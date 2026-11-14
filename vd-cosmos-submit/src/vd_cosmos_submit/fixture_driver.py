"""Scripted browser substitute; cannot target a real instance."""
import copy
import json
from vd_cosmos_core import submit_flow
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.submit_browser_contract import readback

class FixtureDriver:
    def __init__(self,config,session,path):
        if not config.raw['submit']['target_instance'].endswith('.invalid'):raise FlowError(4,'fixture_target_required')
        self.config=config;self.session=session;self.data=json.loads(config.source(path).read_text()).get('browser')
        if not isinstance(self.data,dict):raise FlowError(2,'browser_fixture_required')
        self.snap=copy.deepcopy(self.data['snapshot']);self.closed=False
    def operate(self,args,request,context,confirm,reader_factory):return submit_flow.execute(self.config,request,self.session,context,self,confirm,reader_factory,rehearse=args.rehearse)
    def open(self,expose,confirm):
        expose()
        if self.data.get('page') in {'login','unknown','crash'}:raise FlowError(5,'fixture_page_unavailable')
    def snapshot(self):return copy.deepcopy(self.snap)
    def fill(self,index,value):self.snap['controls'][index]['value']=value
    def serialize_check(self,snapshot,form,*,rehearse):readback(self.config,snapshot,form);return {'verified':False,'reason':'scripted_fixture'}
    def records(self):return []
    def release(self,expected,hidden):return self.data.get('result','uncertain')
    def close(self):self.closed=True
