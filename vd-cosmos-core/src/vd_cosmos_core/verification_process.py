"""Bounded verifier children, process-group cleanup and checked live transcripts."""
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import time
from .errors import FlowError
from .export import check_content
from .files import digest


def identity(pid):
    try:
        fields=(Path('/proc')/str(pid)/'stat').read_text().rsplit(')',1)[1].split()
        return None if fields[0]=='Z' else fields[19]
    except (OSError,IndexError):return None


def owned_processes(directory):
    """Only inspect ownership/path markers; never return or persist environments."""
    root=str(Path(directory).resolve());roots={root}
    for marker in Path(directory).rglob('browser-temp.json'):
        try:
            value=json.loads(marker.read_text())['path']
            if Path(value).name.startswith('vdc-'):roots.add(value)
        except (OSError,ValueError,KeyError,TypeError):pass
    def matches(value):
        return any(value==p or value.startswith(p+'/') for p in roots)
    result=[]
    for item in Path('/proc').iterdir():
        if not item.name.isdecimal() or int(item.name)==os.getpid():continue
        try:
            if item.stat().st_uid!=os.getuid():continue
            start=identity(int(item.name))
            if start is None:continue
            args=(item/'cmdline').read_bytes().split(b'\0')
            env=(item/'environ').read_bytes().split(b'\0')
            values=[v.decode('utf-8','replace').split('=',1)[-1] for v in args+env]
            if any(matches(v) for v in values):result.append((int(item.name),start))
        except (OSError,ValueError):continue
    return result


def signal_owned(items,sig):
    for pid,start in items:
        if identity(pid)==start:
            try:os.kill(pid,sig)
            except ProcessLookupError:pass


def terminate(child,directory,grace=10):
    # Browser wrappers may setsid(); also catch those via inherited verification
    # marker or profile/temp paths, including processes surviving a prior child.
    try:os.killpg(child.pid,signal.SIGTERM)
    except ProcessLookupError:pass
    seen=set(owned_processes(directory));signal_owned(seen,signal.SIGTERM)
    deadline=time.monotonic()+grace
    while time.monotonic()<deadline:
        current=set(owned_processes(directory));signal_owned(current-seen,signal.SIGTERM);seen|=current
        try:os.killpg(child.pid,0);group_alive=True
        except ProcessLookupError:group_alive=False
        if not group_alive and not current:break
        time.sleep(.05)
    try:os.killpg(child.pid,signal.SIGKILL)
    except ProcessLookupError:pass
    signal_owned(seen|set(owned_processes(directory)),signal.SIGKILL)
    child.wait(timeout=10)


def process(argv,directory,env,timeout=1800,*,config=None,artifact=None,terminate_grace=10):
    directory=Path(directory);path=Path(artifact) if artifact else None
    if path is not None and config is None:raise FlowError(2,'checked_output_config_required')
    transcript=bytearray();buffers={};pending={};child=None;output=None;cleaned=False
    def publish(data):
        if not data:return
        candidate=bytes(transcript)+data
        if config is not None and not check_content(candidate,config)['allowed']:
            raise FlowError(4,'acceptance_credential_blocked')
        transcript.extend(data)
        if output is not None:output.write(data);output.flush()
    def receipt():
        return {'path':str(path),'size':len(transcript),'sha256':digest(bytes(transcript))} if path else None
    try:
        if path:
            path.parent.mkdir(parents=True,exist_ok=True)
            output=path.open('wb')
        child=subprocess.Popen(argv,cwd=directory,env={**env,'VD_VERIFY_ROOT':str(directory.resolve()),'PYTHONUNBUFFERED':'1'},
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
        deadline=time.monotonic()+timeout
        with selectors.DefaultSelector() as selector:
            for stream in (child.stdout,child.stderr):
                os.set_blocking(stream.fileno(),False);selector.register(stream,selectors.EVENT_READ)
                buffers[stream]=bytearray();pending[stream]=bytearray()
            while selector.get_map() or child.poll() is None:
                if time.monotonic()>=deadline:
                    terminate(child,directory,terminate_grace);cleaned=True
                    for stream in buffers:
                        while True:
                            try:data=os.read(stream.fileno(),65536)
                            except BlockingIOError:break
                            if not data:break
                            buffers[stream].extend(data);pending[stream].extend(data)
                        publish(bytes(pending[stream]));pending[stream].clear()
                    raise FlowError(5,'acceptance_process_timeout',**({'output_artifact':receipt()} if path else {}))
                for key,_ in selector.select(min(.1,max(0,deadline-time.monotonic()))):
                    stream=key.fileobj;data=os.read(stream.fileno(),65536)
                    if not data:
                        selector.unregister(stream);publish(bytes(pending[stream]));pending[stream].clear();continue
                    buffers[stream].extend(data);pending[stream].extend(data)
                    end=pending[stream].rfind(b'\n')+1
                    if end:publish(bytes(pending[stream][:end]));del pending[stream][:end]
            return subprocess.CompletedProcess(argv,child.wait(),bytes(buffers[child.stdout]),bytes(buffers[child.stderr]))
    except FlowError:
        if child is not None and not cleaned:terminate(child,directory,terminate_grace)
        raise
    except OSError:
        if child is not None:terminate(child,directory,terminate_grace)
        raise FlowError(5,'acceptance_process_start_failed') from None
    finally:
        if child is not None:
            for stream in (child.stdout,child.stderr):
                if stream is not None:stream.close()
        if output is not None:output.close()
