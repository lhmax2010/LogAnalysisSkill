#!/usr/bin/env python3
"""Launch only the configured existing browser; watch the owning CLI process."""
import ctypes
import os
from pathlib import Path
import signal
import sys
import time

def identity(pid):
    try:return (Path('/proc')/str(pid)/'stat').read_text().rsplit(')',1)[1].split()[19]
    except (OSError,IndexError):return None

def main():
    owner=int(os.environ.pop('VD_BROWSER_OWNER'));start=os.environ.pop('VD_BROWSER_START');exe=os.environ.pop('VD_BROWSER_EXECUTABLE')
    if not Path(exe).is_file() or identity(owner)!=start:return 6
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
    os.execv(exe,[exe,*sys.argv[1:]])
    return 6
if __name__=='__main__':raise SystemExit(main())
