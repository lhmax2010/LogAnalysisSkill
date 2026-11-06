"""Atomic JSONL knowledge storage; audited instance and seed retrieval."""

from __future__ import annotations

import copy
import fcntl
import hashlib
import json
import math
import os
import re
import tempfile
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tizen_convergence_judge.convergence import primary_fingerprint

SCHEMA_VERSION = "clang_kb/v1"
NORMALIZER_VERSION = "campaign.v1(parity: convergence)"
STATUSES = ("NEW", "CI_VERIFIED", "MERGED")
_SHA = re.compile(r"[0-9a-fA-F]{40}")
_REF = re.compile(r"refs/changes/[0-9]{2}/[0-9]+/[0-9]+")
_WARNING = re.compile(r"-W[A-Za-z0-9_+=.-]+")
_STRATEGIES = ("fix_strategy_initial", "fix_strategy_final")
_PROVENANCE = (
    "reused_from", "quickbuild_id", "sandbox_branch", "gerrit_url", "change_ref", "change_id",
)
_IDENTITY = ("package", "gerrit_path", "baseline_commit", "verified_tree_sha")
_SIGNATURE = ("error_signature_raw", "error_signature_normalized")
_LISTS = ("files", "error_lines", "verified_archs")
_REQUIRED = frozenset(_STRATEGIES + _PROVENANCE + _IDENTITY + _SIGNATURE + _LISTS) | {
    "schema_version", "record_type", "origin", "status", "confidence", "normalizer_version",
    "diagnosed_flag", "root_cause_category", "toolchain_profile", "warning_flags",
    "fix_summary", "promoted_at",
}


class KbSchemaError(ValueError):
    """Invalid caller input, including an invalid monotone transition."""


KbError = KbSchemaError


class KbCorrupt(KbSchemaError):
    """An existing database is invalid; do not query or rewrite a partial prefix."""


@dataclass(frozen=True)
class AppendResult:
    id: str
    deduped: bool


@dataclass(frozen=True)
class QueryResult:
    t1: list[dict[str, Any]]
    t2: list[dict[str, Any]]


def normalize_signature(value: str) -> str:
    """Independent implementation of convergence message normalization."""
    value = re.sub(r"(:\d+){1,2}", ":#", value.lower())
    value = re.sub(r"\b\d+\b", "#", value)
    return re.sub(r"\s+", " ", value).strip()


def describe_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    primary = evidence.get("primary_error")
    if not isinstance(primary, dict) or not _text(primary.get("message")):
        raise KbSchemaError("missing_primary_message")
    fingerprint = primary_fingerprint(evidence, touched_files=None)
    if fingerprint is None:
        raise KbSchemaError("missing_primary_fingerprint")
    category = primary.get("semantic_class") or primary.get("kind")
    candidates = evidence.get("root_cause_candidates", [])
    if not isinstance(candidates, list):
        raise KbSchemaError("invalid_root_cause_candidates")
    for candidate in candidates:
        if (isinstance(candidate, dict) and primary.get("id") is not None
                and candidate.get("event_id") == primary["id"]
                and candidate.get("semantic_class")):
            category = candidate["semantic_class"]
            break
    if not _text(category):
        raise KbSchemaError("missing_root_cause_category")
    raw = primary["message"]
    flags = set(_WARNING.findall(raw))
    for value in (primary.get("warning_option"), fingerprint.diagnostic_code):
        if isinstance(value, str):
            flags.update(_WARNING.findall(value))
    return {
        "diagnosed_flag": fingerprint.diagnostic_code,
        "root_cause_category": category,
        "warning_flags": sorted(flags),
        "error_signature_raw": raw,
    }


def make_record(**metadata: Any) -> dict[str, Any]:
    """Complete schema defaults without inventing identity or policy decisions."""
    record: dict[str, Any] = dict.fromkeys(_PROVENANCE + ("origin", "promoted_at"))
    record.update({field: [] for field in _LISTS})
    record.update(schema_version=SCHEMA_VERSION, record_type="instance", status="NEW",
                  confidence=0, normalizer_version=NORMALIZER_VERSION, warning_flags=[])
    if metadata.get("record_type") == "seed":
        record.update(dict.fromkeys(_IDENTITY + _LISTS + _SIGNATURE + _STRATEGIES))
        record.update(diagnosed_flag=None, root_cause_category=None)
    elif metadata.get("origin") == "imported_shelve":
        record.update(dict.fromkeys(_STRATEGIES + ("verified_tree_sha",)))
    record.update(copy.deepcopy(metadata))
    if isinstance(record.get("error_signature_raw"), str):
        record.setdefault("error_signature_normalized",
                          normalize_signature(record["error_signature_raw"]))
    _validate(record, stored=False)
    return record


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _utc(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return stamp.tzinfo is not None and stamp.utcoffset() == timezone.utc.utcoffset(stamp)
    except ValueError:
        return False


def _validate(record: dict[str, Any], *, stored: bool) -> None:
    required = _REQUIRED | ({"id", "dedupe_key", "created_at"} if stored else set())
    if required - record.keys():
        raise KbSchemaError("missing_record_fields:" + ",".join(sorted(required - record.keys())))
    if record["schema_version"] != SCHEMA_VERSION:
        raise KbSchemaError("invalid_schema_version")
    if record["record_type"] not in ("instance", "seed"):
        raise KbSchemaError("invalid_record_type")
    if record["status"] not in STATUSES:
        raise KbSchemaError("invalid_status")
    if record["normalizer_version"] != NORMALIZER_VERSION:
        raise KbSchemaError("invalid_normalizer_version")
    for field in ("toolchain_profile", "fix_summary"):
        if not _text(record[field]):
            raise KbSchemaError("invalid_" + field)
    seed = record["record_type"] == "seed"
    imported = record["origin"] == "imported_shelve"
    if seed:
        for field in _IDENTITY + _LISTS + _SIGNATURE + _PROVENANCE:
            if record[field] is not None:
                raise KbSchemaError("seed_instance_field:" + field)
        for field in ("diagnosed_flag", "root_cause_category"):
            if record[field] is not None and not isinstance(record[field], str):
                raise KbSchemaError("invalid_" + field)
        if record["diagnosed_flag"] is None and record["root_cause_category"] is None:
            raise KbSchemaError("seed_without_match_key")
    else:
        for field in _IDENTITY + _SIGNATURE + ("diagnosed_flag", "root_cause_category"):
            if imported and field == "verified_tree_sha" and record[field] is None:
                continue
            if not _text(record[field]):
                raise KbSchemaError("invalid_" + field)
        for field in ("baseline_commit", "verified_tree_sha"):
            if record[field] is not None and not _SHA.fullmatch(record[field]):
                raise KbSchemaError("invalid_" + field)
        normalized = normalize_signature(record["error_signature_raw"])
        if record["error_signature_normalized"] != normalized:
            raise KbSchemaError("signature_normalization_mismatch")
        for field in _LISTS:
            value = record[field]
            if not isinstance(value, list):
                raise KbSchemaError("invalid_" + field)
            if field == "error_lines":
                if any(not ((type(item) is int and item > 0) or _text(item)) for item in value):
                    raise KbSchemaError("invalid_error_lines")
            elif any(not _text(item) for item in value):
                raise KbSchemaError("invalid_" + field)
    for field in _STRATEGIES:
        value = record[field]
        if value is None and (seed or imported):
            continue
        if value not in ("code", "cherry_pick", "suppress"):
            raise KbSchemaError("invalid_" + field)
    flags = record["warning_flags"]
    if not isinstance(flags, list) or any(not _text(flag) for flag in flags):
        raise KbSchemaError("invalid_warning_flags")
    for field in _PROVENANCE + ("origin",):
        value = record[field]
        if value is None:
            continue
        if field == "quickbuild_id":
            if type(value) is not int or value <= 0:
                raise KbSchemaError("invalid_quickbuild_id")
        elif not _text(value):
            raise KbSchemaError("invalid_" + field)
    confidence = record["confidence"]
    try:
        valid_confidence = (not isinstance(confidence, bool)
                            and isinstance(confidence, (int, float))
                            and math.isfinite(confidence))
    except OverflowError:
        valid_confidence = False
    if not valid_confidence:
        raise KbSchemaError("invalid_confidence")
    if record["change_ref"] is not None and not _REF.fullmatch(record["change_ref"]):
        raise KbSchemaError("invalid_change_ref")
    if imported:
        if seed or not _text(record.get("diff")):
            raise KbSchemaError("invalid_imported_diff")
        try:
            record["diff"].encode("utf-8", errors="strict")
        except UnicodeError as exc:
            raise KbSchemaError("invalid_diff_encoding") from exc
    if record["promoted_at"] is not None and not _utc(record["promoted_at"]):
        raise KbSchemaError("invalid_promoted_at")
    if "created_at" in record and not _utc(record["created_at"]):
        raise KbSchemaError("invalid_created_at")
    if stored:
        try:
            if str(uuid.UUID(record["id"])) != record["id"]:
                raise ValueError
        except (ValueError, TypeError, AttributeError) as exc:
            raise KbSchemaError("invalid_id") from exc
        if record["dedupe_key"] != dedupe_key(record):
            raise KbSchemaError("dedupe_key_mismatch")


def dedupe_key(record: dict[str, Any]) -> str:
    if record["record_type"] == "seed":
        summary = unicodedata.normalize("NFC", record["fix_summary"]).strip()
        if not summary:
            raise KbSchemaError("empty_seed_summary")
        parts = ["clang_kb/seed/v1", record["diagnosed_flag"], record["root_cause_category"],
                 record["toolchain_profile"], hashlib.sha256(summary.encode("utf-8")).hexdigest()]
        raw = json.dumps(parts, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    else:
        tree = record["verified_tree_sha"]
        if record.get("origin") == "imported_shelve":
            tree = "imported:" + hashlib.sha256(record["diff"].encode("utf-8")).hexdigest()
        parts = [record["package"], record["gerrit_path"], record["baseline_commit"], tree,
                 record["diagnosed_flag"], record["toolchain_profile"],
                 record["error_signature_normalized"]]
        raw = "".join(parts).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    record: dict[str, Any] = {}
    for key, value in pairs:
        if key in record:
            raise KbCorrupt("duplicate_json_key")
        record[key] = value
    return record


def _constant(value: str) -> Any:
    raise KbCorrupt("nonfinite_json_number")


def records(db: Path) -> list[dict[str, Any]]:
    """Validate a complete atomic snapshot; queries never repair damaged data."""
    try:
        data = db.read_bytes().decode("utf-8", errors="strict")
    except FileNotFoundError:
        return []
    except UnicodeError as exc:
        raise KbCorrupt("invalid_jsonl_encoding") from exc
    rows: list[dict[str, Any]] = []
    ids: set[str] = set()
    keys: set[str] = set()
    # JSONL is LF-delimited: Unicode line separators can occur inside JSON strings.
    lines = data.split("\n")
    if lines[-1] == "":
        lines.pop()
    for line in lines:
        try:
            row = json.loads(line, object_pairs_hook=_pairs, parse_constant=_constant)
            if not isinstance(row, dict):
                raise KbSchemaError("record_not_object")
            _validate(row, stored=True)
            if row["id"] in ids or row["dedupe_key"] in keys:
                raise KbSchemaError("duplicate_record")
            ids.add(row["id"])
            keys.add(row["dedupe_key"])
            rows.append(row)
        except (ValueError, TypeError, KeyError) as exc:
            raise KbCorrupt("invalid_jsonl_record") from exc
    return rows


def _write(db: Path, rows: list[dict[str, Any]]) -> None:
    try:
        payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False)
                          + "\n" for row in rows).encode("utf-8")
    except (ValueError, TypeError) as exc:
        raise KbSchemaError("record_not_json_utf8") from exc
    descriptor, name = tempfile.mkstemp(prefix="." + db.name + ".", dir=db.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, db)
        parent = os.open(db.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
    finally:
        temporary.unlink(missing_ok=True)


def append(db: Path, record: dict[str, Any]) -> AppendResult:
    candidate = make_record(**record)
    key = dedupe_key(candidate)
    db.parent.mkdir(parents=True, exist_ok=True)
    with (db.parent / ".lock").open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        rows = records(db)
        for row in rows:
            if row["dedupe_key"] == key:
                return AppendResult(id=row["id"], deduped=True)
        candidate.update(id=str(uuid.uuid4()), dedupe_key=key)
        candidate.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        _validate(candidate, stored=True)
        _write(db, rows + [candidate])
        return AppendResult(id=candidate["id"], deduped=False)


def promote(db: Path, id: str, to_status: str) -> dict[str, Any]:
    if to_status not in STATUSES:
        raise KbSchemaError("invalid_status")
    db.parent.mkdir(parents=True, exist_ok=True)
    with (db.parent / ".lock").open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        rows = records(db)
        for row in rows:
            if row["id"] != id:
                continue
            if STATUSES.index(to_status) < STATUSES.index(row["status"]):
                raise KbSchemaError("status_downgrade")
            if row["status"] != to_status:
                row.update(status=to_status, promoted_at=datetime.now(timezone.utc).isoformat())
                _write(db, rows)
            return row
        raise KbSchemaError("unknown_record_id")


def query(
    db: Path, *, diagnosed_flag: str, package: str | None = None,
    gerrit_path: str | None = None, category: str | None = None,
    warning_flags: list[str] | None = None, toolchain_profile: str | None = None,
    error_signature: str | None = None, min_status: str = "CI_VERIFIED", limit_t2: int = 5,
) -> QueryResult:
    if not _text(diagnosed_flag) or min_status not in STATUSES:
        raise KbSchemaError("invalid_query")
    if type(limit_t2) is not int or limit_t2 < 0:
        raise KbSchemaError("invalid_limit_t2")
    if warning_flags is not None and (
        not isinstance(warning_flags, list) or any(not _text(v) for v in warning_flags)
    ):
        raise KbSchemaError("invalid_warning_flags")
    for value in (package, gerrit_path, category, toolchain_profile, error_signature):
        if value is not None and not _text(value):
            raise KbSchemaError("invalid_query")
    rows = [row for row in records(db) if row["status"] != "NEW"
            and STATUSES.index(row["status"]) >= STATUSES.index(min_status)]
    complete = all(value is not None for value in (
        package, gerrit_path, category, warning_flags, toolchain_profile, error_signature,
    ))
    signature = normalize_signature(error_signature) if error_signature is not None else None
    t1 = [row for row in rows if complete and row["record_type"] == "instance"
          and row["package"] == package and row["gerrit_path"] == gerrit_path
          and row["diagnosed_flag"] == diagnosed_flag and row["root_cause_category"] == category
          and set(row["warning_flags"]) == set(warning_flags or [])
          and row["toolchain_profile"] == toolchain_profile
          and row["error_signature_normalized"] == signature]
    t2 = [row for row in rows if row["diagnosed_flag"] == diagnosed_flag
          or (category is not None and row["root_cause_category"] == category)]

    def rank(row: dict[str, Any]) -> tuple[int, float]:
        exact = category is not None and row["root_cause_category"] == category
        if row["record_type"] == "seed":
            priority = 0 if exact else 1
        else:
            priority = 2 if row["status"] == "MERGED" and exact else 3
        return priority, -float(row["confidence"])

    return QueryResult(t1=t1, t2=sorted(t2, key=rank)[:limit_t2])
