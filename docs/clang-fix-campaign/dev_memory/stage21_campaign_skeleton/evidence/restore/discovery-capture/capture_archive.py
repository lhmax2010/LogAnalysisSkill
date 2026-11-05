"""Private capture spool and offline archive; never exposes source or exceptions."""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

from tizen_qb_verify.qb_redact import SessionPageRedactor

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]
STAGES = {"IDENTITY_REGISTER", "IDENTITY_EMPTY", "REDACT", "PRECHECK", "WRITE", "POSTCHECK"}


def private_write(path: Path, raw: bytes) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def encoded(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def check(redactor: SessionPageRedactor, raw: bytes, mode: str) -> None:
    redactor.check_bytes(html.escape(raw.decode()).encode() if mode != "html" else raw)


def scan_tree(root: Path, redactor: SessionPageRedactor) -> int:
    count = 0
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError
        if path.is_file():
            text = path.read_bytes().decode("utf-8", errors="replace")
            # This directory also contains fixtures/source with synthetic secrets. The
            # directory-wide contract is identity-only; each new archive has full checks.
            if redactor._edits(text if path.suffix == ".html" else html.escape(text)):
                raise ValueError
            count += 1
    return count


class Archive:
    def __init__(self, output: Path, *, replay: str | None = None) -> None:
        self.output = output.resolve()
        self.scan_root = HERE if self.output.is_relative_to(HERE) else self.output.parent
        base = Path.home() / ".local/state/campaign-capture-private"
        if any(p.is_symlink() for p in (base, *base.parents)):
            raise ValueError
        if base.resolve().is_relative_to(ROOT) or base.resolve().is_relative_to(self.scan_root):
            raise ValueError
        base.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(base, 0o700)
        if replay is None:
            self.private = Path(tempfile.mkdtemp(prefix="capture-", dir=base))
            self.items: list[dict[str, str]] = []
        else:
            if not re.fullmatch(r"capture-[A-Za-z0-9_-]+", replay):
                raise ValueError
            self.private = base / replay
            if self.private.is_symlink() or self.private.stat().st_mode & 0o077:
                raise ValueError
            self.items = json.loads((self.private / "manifest.json").read_text())
        self.redactor = SessionPageRedactor()
        self.stage = "WRITE"
        self.welcome_count = 0
        self.replacements = 0
        self.created: list[Path] = []

    def store(self, name: str, mode: str, raw: bytes, text: str) -> dict[str, Any]:
        if mode not in {"html", "text"} or not re.fullmatch(r"\d{2}\.response\.(html|txt)", name):
            raise ValueError
        private_write(self.private / (name + ".raw"), raw)
        private_write(self.private / (name + ".utf8"), text.encode())
        self.items.append({"name": name, "mode": mode})
        return {"ok": True, "file": name, "private_pending": True}

    def counts(self) -> dict[str, int]:
        return {"welcome_regions": self.welcome_count,
                "registered_identities": len(self.redactor.identities),
                "identity_replacement_count": self.replacements}

    def safe(self, source: str, mode: str) -> bytes:
        self.stage = "REDACT"
        value = self.redactor.redact_registered(html.escape(source) if mode != "html" else source)
        self.replacements += self.redactor.identity_replacement_count
        return (html.unescape(value) if mode != "html" else value).encode()

    def publish(self, name: str, raw: bytes, mode: str) -> None:
        self.stage = "PRECHECK"
        check(self.redactor, raw, mode)
        self.stage = "WRITE"
        path = self.output / name
        with path.open("xb") as stream:
            self.created.append(path)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        self.stage = "POSTCHECK"
        written = path.read_bytes()
        check(self.redactor, written, mode)
        if written != raw:
            raise ValueError

    def finish(self, record: dict[str, Any], *, replay: bool = False) -> dict[str, Any]:
        try:
            self.stage = "WRITE"
            if not replay:
                private_write(self.private / "manifest.json", encoded(self.items))
                private_write(self.private / "record.json", encoded(record))
            if not record.get("browser_closed") or not record.get("profile_removed"):
                raise ValueError
            self.stage = "IDENTITY_REGISTER"
            sources = [
                (item, (self.private / (item["name"] + ".utf8")).read_bytes().decode("utf-8"))
                for item in self.items
            ]
            for item, source in sources:
                if item["mode"] == "html":
                    self.redactor.register(source)
                    self.welcome_count += self.redactor.welcome_count
            self.stage = "IDENTITY_EMPTY"
            if not self.welcome_count or not self.redactor.session_identity_complete:
                raise ValueError
            self.stage = "IDENTITY_REGISTER"
            for item, source in sources:
                if item["mode"] == "html":
                    self.redactor.register(source)
            for item, source in sources:
                before = self.replacements
                raw = self.safe(source, item["mode"])
                self.publish(item["name"], raw, item["mode"])
                body = {"file": item["name"], "sha256": hashlib.sha256(raw).hexdigest(),
                        "bytes": len(raw), "identity_replacement_count": self.replacements - before,
                        "identity_remaining_count": 0}
                for page in record.get("pages", []):
                    if page.get("body", {}).get("file") == item["name"]:
                        page["body"] = body
            record["archive"] = {**self.counts(), "identity_remaining_count": 0,
                                 "private_run": self.private.name, "private_removed": True}
            raw_record = self.safe(encoded(record).decode(), "json")
            self.publish("run.json", raw_record, "json")
            self.stage = "POSTCHECK"
            for item, _ in sources:
                check(self.redactor, (self.output / item["name"]).read_bytes(), item["mode"])
            scan_tree(self.scan_root, self.redactor)
            self.stage = "WRITE"
            shutil.rmtree(self.private)
            return {"ok": True, "record": json.loads(raw_record)}
        except Exception:
            for path in self.created:
                path.unlink(missing_ok=True)
            failure = {"ok": False, "error": "QB_EVIDENCE_REDACTION_FAILED",
                       "stage": self.stage, **self.counts(), "private_run": self.private.name,
                       "private_removed": not self.private.exists()}
            stopped = {"status": "STOPPED", "failure": failure["error"], "archive": failure,
                       "page_count": len(record.get("pages", [])),
                       "browser_closed": record.get("browser_closed") is True,
                       "profile_removed": record.get("profile_removed") is True}
            try:
                (self.output / "run.json").write_bytes(encoded(stopped))
            except Exception:
                pass
            return {**failure, "record": stopped}
