"""OS locks, released on process death; never delete a lock inode."""
import fcntl
import os
import time
from .errors import FlowError
from .files import confined, digest


class OperationLock:
    def __init__(self, root, kind, identity, *, wait_s=0):
        if kind not in {"profile", "round", "loop", "request", "observation", "submit-target"}:
            raise FlowError(2, "invalid_lock_kind")
        self.path = confined(root, "locks/" + kind + "-" + digest(str(identity).encode()) + ".lock")
        self.wait_s = wait_s
        self.stream = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.stream = self.path.open("a+b")
        deadline = time.monotonic() + self.wait_s
        while True:
            try:
                fcntl.flock(self.stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    self.stream.seek(0)
                    holder = self.stream.read(32).decode('ascii', errors='ignore').strip()
                    self.stream.close()
                    self.stream = None
                    raise FlowError(6, "operation_locked", holder_pid=int(holder) if holder.isdecimal() else None) from None
                time.sleep(min(.05, max(0, deadline - time.monotonic())))
        if self.path.name.startswith('observation-'):
            self.stream.seek(0); self.stream.truncate()
            self.stream.write(str(os.getpid()).encode()); self.stream.flush()
        return self

    def __exit__(self, *args):
        if self.stream:
            fcntl.flock(self.stream.fileno(), fcntl.LOCK_UN)
            self.stream.close()
            self.stream = None
