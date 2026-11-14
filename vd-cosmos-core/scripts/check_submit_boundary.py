#!/usr/bin/env python3
"""Static guard for the single optional adapter; never installs a browser/PHP."""
import ast
from pathlib import Path

BANNED={'cookies','add_cookies','storage_state','screenshot','content','inner_html','outer_html','start_tracing','tracing','new_browser_cdp_session','connect_over_cdp','connect','get_attribute','input_value'}
CDP={'Fetch.enable','Fetch.continueRequest','Fetch.failRequest','Page.getFrameTree','Browser.getWindowForTarget','Browser.setWindowBounds'}

def validate(text,adapter=False):
    tree=ast.parse(text,feature_version=10)
    for node in ast.walk(tree):
        if isinstance(node,ast.Import) or isinstance(node,ast.ImportFrom) and not node.level:
            names=[n.name for n in node.names] if isinstance(node,ast.Import) else [node.module or '']
            if any(n.startswith(('playwright','selenium')) and not(adapter and n=='playwright.sync_api') for n in names):raise ValueError('browser import')
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute):
            attr=node.func.attr
            if attr in BANNED:raise ValueError('forbidden browser API')
            if attr=='new_cdp_session' and not adapter:raise ValueError('CDP outside adapter')
            if attr=='evaluate' and (not adapter or not node.args or not isinstance(node.args[0],ast.Name) or node.args[0].id!='SCRIPT'):raise ValueError('unregistered script')
            if attr=='send' and isinstance(node.func.value,ast.Attribute) and node.func.value.attr=='_cdp':
                if not node.args:raise ValueError('CDP method')
                first=node.args[0];values=[first.body,first.orelse] if isinstance(first,ast.IfExp) else [first]
                if any(not isinstance(v,ast.Constant) or v.value not in CDP for v in values):raise ValueError('CDP method')
        if isinstance(node,ast.keyword) and node.arg in {'record_har_path','record_video_dir','storage_state','record_har_content'}:raise ValueError('capture option')
        if isinstance(node,ast.List) and node.elts and isinstance(node.elts[0],ast.Constant) and node.elts[0].value in {'php','php-cli'}:raise ValueError('PHP')
        if isinstance(node,ast.Constant) and isinstance(node.value,str) and 'playwright'+' install' in node.value:raise ValueError('browser install')

def main():
    repo=Path(__file__).resolve().parents[2];paths=list((repo/'vd-cosmos-submit').rglob('*.py'))
    core=repo/'vd-cosmos-core/src/vd_cosmos_core';paths+=list(core.glob('bm_*.py'))+list(core.glob('submit_*.py'))+list(core.glob('verify_b3a11b*.py'))
    for path in paths:validate(path.read_text(),adapter=path.name=='playwright_driver.py')
    print('Checkpoint B2 browser/PHP/static boundary: PASS ('+str(len(paths))+' files)')
if __name__=='__main__':main()
