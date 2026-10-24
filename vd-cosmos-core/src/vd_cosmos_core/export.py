"""Two-level content check and byte-exact UTF-8 export bundles."""
import os
from pathlib import Path
import re
import shutil
import tempfile

from .errors import FlowError
from .files import atomic_write, digest, json_bytes


def check_content(content, config, *, test_exemptions=False):
    try:
        text = content.decode("utf-8")
    except UnicodeError:
        raise FlowError(4, "non_utf8_export") from None
    hits, warnings = [], []
    for index, pattern in enumerate(config.raw["prepush"]["credential_patterns"]):
        for match in re.finditer(pattern, text, re.I | re.M):
            line_start = text.rfind("\n", 0, match.start()) + 1
            line_end = text.find("\n", match.end())
            line_end = len(text) if line_end < 0 else line_end
            if test_exemptions and "\n" not in match.group() and "# credential-test-sample" in text[line_start:line_end]:
                continue
            hits.append({"pattern_index": index, "line": text.count("\n", 0, match.start()) + 1})
    words_file = config.raw["prepush"].get("words_file")
    if words_file:
        try:
            words = config.source(words_file).read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError):
            raise FlowError(2, "wordlist_unreadable") from None
        for index, word in enumerate(words):
            if word.strip() and word.casefold() in text.casefold():
                warnings.append({"word_index": index})
    return {"allowed": not hits, "credential_hits": hits, "warnings": warnings}


def utf8_chunks(content, limit):
    if limit < 4:
        raise FlowError(2, "chunk_limit_too_small")
    try:
        content.decode("utf-8")
    except UnicodeError:
        raise FlowError(4, "non_utf8_export") from None
    offset = 0
    while offset < len(content):
        end = min(offset + limit, len(content))
        while end < len(content) and content[end] & 0xC0 == 0x80:
            end -= 1
        newline = content.rfind(b"\n", offset, end)
        if newline >= offset:
            end = newline + 1
        yield content[offset:end]
        offset = end


def export_file(config, source, material_type, name):
    if material_type not in config.raw["export"]["allow_types"]:
        raise FlowError(4, "material_type_not_exportable")
    path = config.output(source)
    relative = path.relative_to(config.data_root)
    if relative.parts[0] in {"browser", "browser-bin", "state", "locks", "run", "tmp", "venv", "settings"}:
        raise FlowError(4, "sensitive_asset_not_exportable")
    if path == config.output(config.raw["p4"]["config_file"]) or path.name == "config.json":
        raise FlowError(4, "configuration_not_exportable")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        raise FlowError(2, "invalid_export_name")
    try:
        content = path.read_bytes()
    except OSError:
        raise FlowError(5, "export_source_unreadable") from None
    checks = check_content(content, config)
    if not checks["allowed"]:
        # No directory or chunk is created, even when a late line contains a credential.
        raise FlowError(4, "credential_pattern_blocked", hits=checks["credential_hits"])
    # An authentication page remains non-exportable even with empty credential fields.
    if re.search(r'(?is)<input\b[^>]*\btype\s*=\s*["\x27]?password', content.decode("utf-8")):
        raise FlowError(4, "authentication_page_not_exportable")
    destination = config.output("export/" + name)
    if destination.exists():
        raise FlowError(6, "export_already_exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".pending-export-", dir=destination.parent))
    try:
        blocks = []
        for index, block in enumerate(utf8_chunks(content, config.raw["export"]["chunk_bytes"]), 1):
            filename = f"part-{index:05d}.txt"
            atomic_write(temporary, filename, block)
            blocks.append({"order": index, "file": filename, "size": len(block), "sha256": digest(block)})
        manifest = {"schema_version": 1, "material_type": material_type,
                    "total_blocks": len(blocks), "source_size": len(content),
                    "source_sha256": digest(content), "blocks": blocks, "warnings": checks["warnings"]}
        atomic_write(temporary, "manifest.json", json_bytes(manifest))
        # Operation locks in the CLI serialize bundles under this data root.
        os.rename(temporary, destination)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return {"path": str(destination / "manifest.json"), **manifest}
