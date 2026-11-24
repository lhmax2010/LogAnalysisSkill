#!/usr/bin/env python3
"""Launch only the configured existing browser; watch the owning CLI process."""
import json
import os
from pathlib import Path
import signal
import sys
import time

def identity(pid):
    try:return (Path('/proc')/str(pid)/'stat').read_text().rsplit(')',1)[1].split()[19]
    except (OSError,IndexError):return None

def main():
    try:
        import ctypes
    except ImportError:
        return 6

    owner=int(os.environ.pop('VD_BROWSER_OWNER'));start=os.environ.pop('VD_BROWSER_START');exe=os.environ.pop('VD_BROWSER_EXECUTABLE')
    if not Path(exe).is_file() or identity(owner)!=start:return 6
    profile=os.environ.pop('VD_BROWSER_PROFILE', None)
    args=sys.argv[1:]
    if profile:
        args=[arg for arg in args if not arg.startswith('--user-data-dir=')]
        args.append('--user-data-dir='+profile)
        marker=Path(profile)/'active-browser.json'
        descriptor=os.open(marker,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(descriptor,'w') as stream:
            json.dump({'pid':os.getpid(),'start_time':identity(os.getpid())},stream)
    if os.getpgrp()!=os.getpid():os.setsid()
    group=os.getpid()
    libc=ctypes.CDLL(None);libc.prctl(1,signal.SIGTERM)
    child=os.fork()
    if child==0:
        os.closerange(3,65536)
        while identity(owner)==start and identity(group) is not None:time.sleep(.2)
        try:os.killpg(group,signal.SIGTERM)
        except ProcessLookupError:pass
        os._exit(0)
    os.execv(exe,[exe,*args])
    return 6
if __name__=='__main__':raise SystemExit(main())
