"""Render .spec toolchain flag compatibility patch context."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gbs_patch_suggest.formatter import EDIT_SPEC_SCHEMA
from gbs_patch_suggest.render import MANDATORY_INSTRUCTIONS
from gbs_patch_suggest.spec_toolchain_flag_resolver import SpecToolchainFlagResolution


def write_spec_toolchain_flag_outputs(
    resolved: SpecToolchainFlagResolution,
    output_dir: Path,
    *,
    evidence_path: Path | None = None,
    buildlog_path: Path | None = None,
) -> dict[str, Path]:
    """Write context, metadata, and optional edit spec for spec flag fixes."""

    output_dir.mkdir(parents=True, exist_ok=True)
    spec_dir = output_dir / "spec_toolchain_flag_context"
    spec_dir.mkdir(parents=True, exist_ok=True)
    edit_spec_path = spec_dir / "edit_spec_spec_toolchain_flags.json"
    if resolved.patch_ready:
        edit_spec_path.write_text(
            json.dumps(_render_edit_spec(resolved), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    readme_path = output_dir / "README.md"
    context_path = output_dir / "context.md"
    meta_path = output_dir / "meta.json"
    readme_path.write_text(_render_readme(resolved), encoding="utf-8")
    context_path.write_text(
        _render_context(resolved, edit_spec_path=edit_spec_path if resolved.patch_ready else None),
        encoding="utf-8",
    )
    meta_path.write_text(
        json.dumps(
            _render_meta(
                resolved,
                edit_spec_path=edit_spec_path if resolved.patch_ready else None,
                readme_path=readme_path,
                context_path=context_path,
                meta_path=meta_path,
                evidence_path=evidence_path,
                buildlog_path=buildlog_path,
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return {"readme_md": readme_path, "context_md": context_path, "meta_json": meta_path}


def _render_readme(resolved: SpecToolchainFlagResolution) -> str:
    return "\n".join(
        [
            "# Patch Suggestion Output",
            "",
            "This output handles Clang unknown warning options that originate from .spec "
            "CFLAGS/CXXFLAGS.",
            "",
            "## Summary",
            "",
            f"- Status: `{resolved.status}`",
            "- Mode: `spec_toolchain_flag`",
            "- Original CFLAGS/CXXFLAGS lines must remain unchanged for GCC safety.",
            "",
            "Read `context.md` next. The skill did not apply a patch or modify the source tree.",
            "",
        ]
    )


def _render_context(
    resolved: SpecToolchainFlagResolution,
    *,
    edit_spec_path: Path | None,
) -> str:
    lines = [
        "# Spec Toolchain Flag Compatibility Context",
        "",
        "This diagnostic is a Clang unknown warning-option failure. The safe repair is "
        "to preserve the original .spec CFLAGS/CXXFLAGS for GCC and strip only the "
        "unknown options inside a `%{toolchain_is clang}` branch.",
        "",
        "## Unknown Options",
        "",
    ]
    lines.extend(f"- `{option}`" for option in resolved.options)
    lines.append("")
    lines.extend(
        [
            "## Safety Rules",
            "",
            "- Do not delete options from the original CFLAGS/CXXFLAGS lines.",
            "- GCC must continue to see the original flags.",
            "- Clang strips only the options listed above.",
            "- Do not apply the patch; present it to the user for review.",
            "",
        ]
    )
    if resolved.patch_ready and edit_spec_path is not None:
        assert resolved.spec_relative_path is not None
        assert resolved.insert_after_line is not None
        edit_spec_rel = _relative(edit_spec_path, edit_spec_path.parents[1])
        lines.extend(
            [
                "## Generated Edit Spec",
                "",
                f"- Spec file: `{resolved.spec_relative_path}`",
                f"- Insert after line: `{resolved.insert_after_line}`",
                f"- Edit spec: `{_relative(edit_spec_path, edit_spec_path.parents[1])}`",
                "- The edit spec uses `operation: insert_after` with an anchor check. Keep "
                "`file`, `line`, `anchor`, and `insert` unchanged unless the formatter reports "
                "a specific mismatch.",
                "",
                "Run the formatter:",
                "",
                "```bash",
                "python3 -m gbs_patch_suggest format-patch \\",
                "    --src-root /path/to/source \\",
                f"    --edit-spec .gbs_patch_suggest/{edit_spec_rel} \\",
                "    --output .gbs_patch_suggest/candidate_spec_toolchain_flags.patch \\",
                "    --check",
                "```",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## Advisory",
                "",
                f"`{resolved.advisory or 'unable to prepare a safe spec patch'}`",
                "",
                "Do not guess a .spec patch. First confirm that the unknown options come from "
                ".spec CFLAGS/CXXFLAGS and identify a safe insertion point after final flag "
                "setup but before `%cmake`, `%configure`, or `make` consumes the flags.",
                "",
            ]
        )
    lines.extend([MANDATORY_INSTRUCTIONS.rstrip(), ""])
    return "\n".join(lines)


def _render_edit_spec(resolved: SpecToolchainFlagResolution) -> dict[str, Any]:
    assert resolved.spec_relative_path is not None
    assert resolved.insert_after_line is not None
    assert resolved.anchor is not None
    assert resolved.insert is not None
    return {
        "schema_version": EDIT_SPEC_SCHEMA,
        "patch_name": "candidate_spec_toolchain_flags.patch",
        "description": "Insert Clang-only stripping for warning options unsupported by Clang.",
        "edits": [
            {
                "operation": "insert_after",
                "file": resolved.spec_relative_path,
                "line": resolved.insert_after_line,
                "anchor": resolved.anchor,
                "insert": resolved.insert,
            }
        ],
    }


def _render_meta(
    resolved: SpecToolchainFlagResolution,
    *,
    edit_spec_path: Path | None,
    readme_path: Path,
    context_path: Path,
    meta_path: Path,
    evidence_path: Path | None,
    buildlog_path: Path | None,
) -> dict[str, Any]:
    return {
        "schema_version": "gbs_patch_suggest/meta/v1",
        "mode": "spec_toolchain_flag",
        "status": resolved.status,
        "options": list(resolved.options),
        "spec_file": resolved.spec_relative_path,
        "insert_after_line": resolved.insert_after_line,
        "advisory": resolved.advisory,
        "outputs": {
            "readme_md": str(readme_path),
            "context_md": str(context_path),
            "meta_json": str(meta_path),
            "edit_spec_json": None if edit_spec_path is None else str(edit_spec_path),
        },
        "inputs": {
            "evidence_json": None if evidence_path is None else str(evidence_path),
            "buildlog": None if buildlog_path is None else str(buildlog_path),
        },
    }


def _relative(path: Path, base: Path) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()
