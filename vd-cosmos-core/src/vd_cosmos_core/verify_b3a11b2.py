"""B2 build-machine acceptance: local tests only, never live once/rehearse."""
import json
from pathlib import Path
import re
import subprocess
import sys
import uuid
from .cli import Parser
from .config import load_config
from .browser_executable import resolve as resolve_browser
from .errors import FlowError
from .files import atomic_write,json_bytes,digest
from .verify_b3a11 import ROOTS,child_env,contracts,offline_tests,process,safe_bytes

def execute(args,repo):
    head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    if not re.fullmatch('[0-9a-f]{40}',args.verified_commit) or head!=args.verified_commit:raise FlowError(6,'expected_commit_mismatch')
    if subprocess.check_output(['git','-C',str(repo),'status','--porcelain=v1','--untracked-files=all','--',*ROOTS]):raise FlowError(6,'owned_source_tree_dirty')
    config=load_config(args.config)
    directory=config.output('verification/b3a11b2-'+uuid.uuid4().hex);directory.mkdir(parents=True,exist_ok=False)
    for name in ('tmp','cache'):(directory/name).mkdir()
    env=child_env(directory);env['VD_REQUIRE_HEADLESS']='1'
    executable=resolve_browser(args.chrome)
    if executable:env['VD_COSMOS_CHROME']=executable
    elif args.chrome:env['VD_COSMOS_CHROME']=str(Path(args.chrome).resolve())
    result={'commit':head,'python':sys.version.split()[0],'exit_code':0,'live_operations':False,'required_headless':True,'browser_executable':executable,'data_root':str(directory)}
    stage='contracts'
    try:
        result['contracts']=contracts(config,repo,directory,env)
        stage='static_scan'
        run=process([sys.executable,'-B',str(repo/'vd-cosmos-core/scripts/check_submit_boundary.py')],directory,env)
        path=atomic_write(config.data_root,directory/'static-scan.txt',safe_bytes(config,run.stdout+run.stderr));result['static_scan']=path
        if run.returncode:raise FlowError(4,'browser_static_scan_failed')
        stage='offline_suite_with_required_headless'
        result['test_output']=offline_tests(config,repo,directory,env)
        result['test_sha256']=digest(Path(result['test_output']['path']).read_bytes())
    except FlowError as e:result.update(e.as_dict(),failed_stage=stage)
    result['verdict']='PASS' if result['exit_code']==0 else 'FAIL'
    result_path=atomic_write(config.data_root,directory/'result.json',safe_bytes(config,json_bytes(result)))
    return {**result,'result_file':result_path}

def main(argv=None):
    try:
        parser=Parser(description=__doc__);parser.add_argument('--verified-commit',required=True);parser.add_argument('--config',required=True);parser.add_argument('--chrome')
        result=execute(parser.parse_args(argv),Path(__file__).resolve().parents[3])
    except FlowError as e:result=e.as_dict()
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError):result={'exit_code':5,'error':'b2_acceptance_processing_failed'}
    print(json.dumps(result,ensure_ascii=False));return result['exit_code']
