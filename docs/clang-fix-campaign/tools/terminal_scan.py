"""Fixed-tree inputs, E4 entry kinds and E5 context-aware module identities.

This module never imports observed code and never emits OBS verdicts. A manifest
is input evidence, not a completed detector matrix or a SEAL result.
The isolated A0 tooling environment requires Python 3.11+ (stdlib tomllib).
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import shlex
import stat
import subprocess
import tempfile
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import tomllib
from terminal_predicates import canonical_hash, check_frozen_hashes, load_json

HEAD = "43a6aa625f27da46daba190657bf62256080c68e"
TREE = "ca9331190e878af465e7968fe56e735585a5866e"
RULES = "docs/clang-fix-campaign/p49-terminal-batch-design-v1.31-FROZEN.md"
RULES_SHA = "d6496250c3f9ba80990785edab0e972c9b077fd4965a045cea31e3201bd7c032"
DATA = Path(__file__).with_name("p49_terminal_data")
ENTRY_KINDS = (
    "GITLINK",
    "SYMLINK",
    "IMPORTABLE_BINARY",
    "PTH",
    "BINARY",
    "PY_SOURCE",
    "PACKAGING",
    "CI_CONFIG",
    "SHELL",
    "BUILD",
    "DOC",
    "OTHER_TEXT",
)
PROVIDER_KINDS = ("PY_SOURCE", "PACKAGE", "NAMESPACE_PORTION")


class ScanError(ValueError):
    """A closed rule or fixed input cannot be satisfied."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=root)


def shebang(data: bytes) -> str | None:
    first = data.split(b"\n", 1)[0]
    if not first.startswith(b"#!"):
        return None
    try:
        words = shlex.split(first[2:].decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None
    if not words:
        return None
    executable = PurePosixPath(words[0]).name
    if executable == "env":
        words = words[1:]
        if words and words[0] == "-S":
            words = words[1:]
        if not words:
            return None
        executable = PurePosixPath(words[0]).name
    return executable


def entry_kind(path: str, mode: str, data: bytes) -> str:
    """E4-2: first match wins; no unknown-mode/text exemption."""
    if mode not in {"100644", "100755", "120000", "160000"}:
        raise ScanError(f"UNKNOWN_PROVIDER_KIND: {path} mode={mode}")
    if mode == "160000":
        return "GITLINK"
    if mode == "120000":
        return "SYMLINK"
    file = PurePosixPath(path)
    if file.suffix in {".so", ".pyd", ".pyc", ".pyo"}:
        return "IMPORTABLE_BINARY"
    if file.suffix == ".pth":
        return "PTH"
    try:
        data.decode("utf-8")
        binary = b"\0" in data
    except UnicodeDecodeError:
        binary = True
    if binary:
        return "BINARY"
    interpreter = shebang(data)
    is_python = (
        interpreter is not None
        and interpreter.startswith("python")
        and all(char in "0123456789." for char in interpreter[len("python") :])
    )
    if file.suffix == ".py" or is_python:
        return "PY_SOURCE"
    if file.name in {"pyproject.toml", "setup.cfg"}:
        return "PACKAGING"
    if path in {".gitlab-ci.yml", "Jenkinsfile", ".travis.yml"} or any(
        fnmatch.fnmatchcase(path, pattern)
        for pattern in (".github/workflows/*.yml", ".github/workflows/*.yaml")
    ):
        return "CI_CONFIG"
    if file.suffix == ".sh" or interpreter in {"sh", "bash"}:
        return "SHELL"
    if file.name in {"Makefile", "GNUmakefile", "Dockerfile", "tox.ini"} or file.suffix in {
        ".mk",
        ".spec",
        ".service",
    }:
        return "BUILD"
    if file.suffix in {".md", ".rst"} or (
        path.startswith("docs/") and mode != "100755" and not data.startswith(b"#!")
    ):
        return "DOC"
    return "OTHER_TEXT"


def registry() -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    entries = load_json(DATA / "entry_registry.json")
    providers = load_json(DATA / "provider_registry.json")
    if tuple(entries) != ENTRY_KINDS or set(providers) != set(PROVIDER_KINDS):
        raise ScanError("REGISTRY_CLOSED_DOMAIN")
    for key, detectors in [*entries.items(), *providers.items()]:
        if not detectors or len(detectors) != len(set(detectors)):
            raise ScanError(f"REGISTRY_REQUIRED_DETECTORS: {key}")
    return entries, providers


@dataclass(frozen=True)
class Context:
    key: str
    descriptor: str
    descriptor_sha256: str
    where: tuple[str, ...]
    include: tuple[str, ...]
    exclude: tuple[str, ...]


def contexts(files: dict[str, bytes]) -> list[Context]:
    result: list[Context] = []
    for path, data in sorted(files.items()):
        file = PurePosixPath(path)
        if file.name not in {"pyproject.toml", "setup.cfg"}:
            continue
        if file.name == "setup.cfg":
            raise ScanError(f"PACKAGING_DESCRIPTION_REQUIRES_RULE: {path}")
        config = tomllib.loads(data.decode("utf-8"))
        try:
            find = config["tool"]["setuptools"]["packages"]["find"]
            where, include = find["where"], find["include"]
        except (KeyError, TypeError) as exc:
            raise ScanError(f"PACKAGING_DESCRIPTION_REQUIRES_RULE: {path}") from exc
        exclude = find.get("exclude", [])
        for values in (where, include, exclude):
            if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
                raise ScanError(f"PACKAGING_DESCRIPTION_REQUIRES_RULE: {path}")
        key = file.parent.as_posix()
        if any(item.key == key for item in result):
            raise ScanError(f"CONTEXT_NOT_UNIQUE: {key}")
        result.append(
            Context(key, path, sha256(data), tuple(where), tuple(include), tuple(exclude))
        )
    return result


def context_for(path: str, declarations: list[Context]) -> Context:
    matches = [
        context
        for context in declarations
        if context.key == "." or path.startswith(context.key + "/")
    ]
    if not matches:
        raise ScanError(f"CONTEXT_NOT_FOUND: {path}")
    return max(matches, key=lambda context: len(PurePosixPath(context.key).parts))


class ModuleIndex:
    def __init__(self, files: dict[str, bytes], declarations: list[Context]):
        self.contexts = declarations
        self.files = files
        self.by_name: dict[tuple[str, str], list[str]] = defaultdict(list)
        self.by_path: dict[str, list[tuple[str, str]]] = defaultdict(list)
        self.events: list[dict[str, Any]] = []
        for path in sorted(files):
            context = context_for(path, declarations)
            for where in context.where:
                base = PurePosixPath(context.key) / where
                file = PurePosixPath(path)
                if not file.is_relative_to(base) or file.suffix != ".py":
                    continue
                relative = file.relative_to(base).with_suffix("")
                parts = relative.parts[:-1] if relative.name == "__init__" else relative.parts
                module = ".".join(parts)
                if not any(fnmatch.fnmatchcase(module, p) for p in context.include):
                    continue
                if any(fnmatch.fnmatchcase(module, p) for p in context.exclude):
                    continue
                identity = context.key, module
                if path not in self.by_name[identity]:
                    self.by_name[identity].append(path)
                if identity not in self.by_path[path]:
                    self.by_path[path].append(identity)
        for (context_key, name), paths in sorted(self.by_name.items()):
            if len(paths) != 1:
                self.events.append(
                    {
                        "kind": "MODULE_IDENTITY_AMBIGUOUS",
                        "context": context_key,
                        "module": name,
                        "paths": paths,
                    }
                )

    def resolve(self, context: str, module: str, origin: str) -> dict[str, Any]:
        local = self.by_name.get((context, module), [])
        targets = [(context, path) for path in local]
        route = "LOCAL"
        if not targets:
            route = "CROSS_CONTEXT_FALLBACK"
            targets = [
                (ctx, path)
                for (ctx, name), paths in self.by_name.items()
                if ctx != context and name == module
                for path in paths
            ]
        result: dict[str, Any] = {
            "origin": origin,
            "source_context": context,
            "module": module,
            "targets": [{"context": ctx, "path": path} for ctx, path in targets],
        }
        if not targets:
            result["kind"] = "NON_CANDIDATE_NAME"
        elif len(targets) != 1:
            result["kind"] = "MODULE_IDENTITY_AMBIGUOUS"
        else:
            result["kind"] = route
        self.events.append(result)
        return result

    def resolve_path(self, context: str, path: str, origin: str) -> dict[str, Any]:
        result: dict[str, Any] = {"origin": origin, "source_context": context, "path": path}
        if path not in self.files:
            result.update(kind="NON_CANDIDATE_NAME", targets=[])
        else:
            target_context = context_for(path, self.contexts).key
            result.update(kind="PATH", targets=[{"context": target_context, "path": path}])
        self.events.append(result)
        return result


def fixed_inputs(root: Path, rules_root: Path) -> tuple[dict[str, Any], dict[str, bytes]]:
    if root.resolve() != Path.cwd().resolve():
        raise ScanError("FIXED_WORKTREE_CWD_REQUIRED")
    if git(root, "rev-parse", "HEAD").decode().strip() != HEAD:
        raise ScanError("FIXED_HEAD_REQUIRED")
    if git(root, "rev-parse", "HEAD^{tree}").decode().strip() != TREE:
        raise ScanError("FIXED_TREE_REQUIRED")
    if git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise ScanError("CLEAN_WORKTREE_REQUIRED")
    if sha256((rules_root / RULES).read_bytes()) != RULES_SHA:
        raise ScanError("RULES_HASH")
    check_frozen_hashes(
        load_json(DATA / "predicates.json"), load_json(DATA / "measurement_exemptions.json")
    )
    entries: list[dict[str, Any]] = []
    files = {}
    for row in git(root, "ls-tree", "-rz", "--full-tree", TREE).split(b"\0"):
        if not row:
            continue
        metadata, encoded_path = row.split(b"\t", 1)
        mode, git_type, oid = metadata.decode().split()
        path = os.fsdecode(encoded_path)
        info = (root / path).lstat()
        if mode == "120000":
            data = os.fsencode(os.readlink(root / path))
            if not stat.S_ISLNK(info.st_mode):
                raise ScanError(f"LSTAT_GIT_MODE: {path}")
        elif mode == "160000":
            data = b""
        else:
            if not stat.S_ISREG(info.st_mode):
                raise ScanError(f"LSTAT_GIT_MODE: {path}")
            data = (root / path).read_bytes()
        if git_type == "blob":
            blob = b"blob " + str(len(data)).encode() + b"\0" + data
            if hashlib.sha1(blob).hexdigest() != oid:
                raise ScanError(f"TREE_BYTES_DIFFER: {path}")
        kind = entry_kind(path, mode, data)
        entries.append(
            {
                "path": path,
                "git_mode": mode,
                "git_type": git_type,
                "oid": oid,
                "lstat_mode": info.st_mode,
                "size": info.st_size,
                "sha256": sha256(data),
                "entry_kind": kind,
            }
        )
        files[path] = data
    declarations = contexts(files)
    for entry in entries:
        entry["context"] = context_for(entry["path"], declarations).key
    return {
        "head": HEAD,
        "tree": TREE,
        "rules_sha256": RULES_SHA,
        "entries": entries,
        "contexts": [asdict(context) for context in declarations],
    }, files


def write_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--rules-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    registry()
    manifest, files = fixed_inputs(args.root, args.rules_root)
    index = ModuleIndex(files, contexts(files))
    manifest["context_counts"] = dict(Counter(entry["context"] for entry in manifest["entries"]))
    manifest["entry_kind_counts"] = dict(
        Counter(entry["entry_kind"] for entry in manifest["entries"])
    )
    manifest["module_identities"] = [
        {"context": ctx, "module": name, "paths": paths}
        for (ctx, name), paths in sorted(index.by_name.items())
    ]
    manifest["identity_events"] = index.events
    write_atomic(args.output, manifest)
    print(f"MANIFEST_INPUT entries={len(manifest['entries'])} canonical={canonical_hash(manifest)}")
    print(json.dumps(manifest["context_counts"], sort_keys=True))
    print("SCAN_COMPLETION=NOT_CREATED (detector matrix not yet run)")
    return int(bool(index.events))


if __name__ == "__main__":
    raise SystemExit(main())
