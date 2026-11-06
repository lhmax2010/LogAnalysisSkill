"""JSON command adapter for strict diff conversion."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import TextIO

from tizen_campaign_core._campaign_io import JsonParser, fsync_parent
from tizen_campaign_core.diff_to_edit_spec import DiffUnsupported, convert


def main(argv: list[str], *, stdout: TextIO) -> int:
    parser = JsonParser(prog="diff-to-edit-spec")
    parser.add_argument("--diff", type=Path, required=True)
    parser.add_argument("--src-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--patch-name", required=True)
    try:
        args = parser.parse_args(argv)
        try:
            raw = args.diff.read_bytes().decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DiffUnsupported("unsupported_encoding") from exc
        result = convert(raw, args.src_root, args.patch_name)
        inputs = [args.diff.resolve(), *[
            (args.src_root / edit["file"]).resolve() for edit in result["edits"]
        ]]
        if args.output.resolve() in inputs:
            raise ValueError("output must not overwrite an input file")
        descriptor, name = tempfile.mkstemp(dir=args.output.parent, prefix=".edit-spec-")
        temporary = Path(name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(result, stream, ensure_ascii=True, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, args.output)
            fsync_parent(args.output)
        finally:
            temporary.unlink(missing_ok=True)
    except DiffUnsupported as exc:
        print(json.dumps({"error_code": "DIFF_CONVERT_UNSUPPORTED", "reason": str(exc)}),
              file=stdout)
        return 4
    except (ValueError, OSError) as exc:
        print(json.dumps({"error_code": "INVALID_ARGS", "reason": str(exc)}), file=stdout)
        return 2
    print(json.dumps({"edit_spec_path": str(args.output), "edits": len(result["edits"])}),
          file=stdout)
    return 0
