"""One isolated process per real-browser test, including setUp and cleanups."""
import json
import os
from pathlib import Path
import sys
import tempfile
from vd_cosmos_core.config import load_config
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.verification_process import process
from vd_cosmos_core import browser_temp
from helpers import config_data

WORKER = '''
import faulthandler,json,sys,unittest
faulthandler.enable()
faulthandler.dump_traceback_later(float(sys.argv[3]),repeat=False)
class Result(unittest.TextTestResult):
 def addError(self,*args):
  faulthandler.dump_traceback(all_threads=True);super().addError(*args)
 def addFailure(self,*args):
  faulthandler.dump_traceback(all_threads=True);super().addFailure(*args)
suite=unittest.defaultTestLoader.loadTestsFromName(sys.argv[1])
result=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(suite)
faulthandler.cancel_dump_traceback_later()
with open(sys.argv[2],'w') as f:json.dump({'ok':result.wasSuccessful(),'skipped':[reason for _,reason in result.skipped]},f)
sys.exit(0 if result.wasSuccessful() else 1)
'''


class HeadlessWatchdog:
    watchdog_seconds=90
    def run(self,result=None):
        if os.environ.get('VD_HEADLESS_CHILD')=='1':return super().run(result)
        result=result or self.defaultTestResult();result.startTest(self)
        try:
            with tempfile.TemporaryDirectory(prefix='headless-watchdog-') as name:
                root=Path(name);config_path=root/'config.json';config_path.write_text(json.dumps(config_data(root/'data')))
                config=load_config(config_path);env=dict(os.environ,VD_HEADLESS_CHILD='1',TMPDIR=str(root),VD_COSMOS_TEST_TMPDIR=str(root))
                transcript=root/'test-output.txt';outcome=root/'outcome.json'
                try:
                    run=process([sys.executable,'-B','-c',WORKER,self.id(),str(outcome),str(max(.1,self.watchdog_seconds-5))],root,env,
                        timeout=self.watchdog_seconds,config=config,artifact=transcript)
                    value=json.loads(outcome.read_text())
                    if run.returncode or not value['ok']:raise AssertionError('real-browser child test failed; see thread stacks and transcript above')
                    if value['skipped']:result.addSkip(self,'; '.join(value['skipped']))
                    else:result.addSuccess(self)
                except FlowError as error:
                    if error.reason=='acceptance_process_timeout':
                        raise AssertionError('real-browser watchdog expired after '+str(self.watchdog_seconds)+' s; process group/browser cleanup attempted; thread stacks follow') from None
                    raise
                finally:
                    if transcript.exists():sys.stderr.write(transcript.read_text());sys.stderr.flush()
                    # The child owns every profile below this fresh root. On a
                    # watchdog kill, the verifier already stopped its browsers.
                    for marker in root.rglob(browser_temp.MARKER):browser_temp.cleanup(marker.parent)
        except BaseException:
            result.addFailure(self,sys.exc_info())
        finally:result.stopTest(self)
        return result
