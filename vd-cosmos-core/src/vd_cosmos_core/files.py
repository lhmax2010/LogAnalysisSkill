"""Confined output paths and atomic artifacts."""
import hashlib
import json
import os
from pathlib import Path
import tempfile

from .errors import FlowError


def digest(data):
    return hashlib.sha256(data).hexdigest()


def confined(root, path):
    root = Path(root).resolve()
    path = Path(path)
    target = (path if path.is_absolute() else root / path).resolve()
    if target == root or root not in target.parents:
        raise FlowError(4, "path_outside_owned_root")
    return target


def atomic_write(root, path, content):
    path = confined(root, path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path = confined(root, path)
    fd, temp = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    return {"path": str(path), "size": len(content), "sha256": digest(content)}


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def load_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique)
    except (OSError, ValueError, UnicodeError):
        raise FlowError(2, "invalid_json_file") from None
