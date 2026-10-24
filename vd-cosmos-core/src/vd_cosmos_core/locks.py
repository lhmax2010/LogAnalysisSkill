"""OS locks, released on process death; never delete a lock inode."""
import fcntl
from .errors import FlowError
from .files import confined, digest


class OperationLock:
    def __init__(self, root, kind, identity):
        if kind not in {"profile", "round", "loop"}:
            raise FlowError(2, "invalid_lock_kind")
        self.path = confined(root, "locks/" + kind + "-" + digest(str(identity).encode()) + ".lock")
        self.stream = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.stream = self.path.open("a+b")
        try:
            fcntl.flock(self.stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.stream.close()
            self.stream = None
            raise FlowError(6, "operation_locked") from None
        return self

    def __exit__(self, *args):
        if self.stream:
            fcntl.flock(self.stream.fileno(), fcntl.LOCK_UN)
            self.stream.close()
            self.stream = None
