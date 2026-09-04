"""Compatibility shim for the extracted build-verify edit-spec guard."""

from tizen_build_verify.edit_spec_guard import EDIT_SPEC_SCHEMA as EDIT_SPEC_SCHEMA
from tizen_build_verify.edit_spec_guard import EditSpecViolation as EditSpecViolation
from tizen_build_verify.edit_spec_guard import _check_no_overlaps as _check_no_overlaps
from tizen_build_verify.edit_spec_guard import _find_old_from_line as _find_old_from_line
from tizen_build_verify.edit_spec_guard import _find_unique_old as _find_unique_old
from tizen_build_verify.edit_spec_guard import _is_relative_to as _is_relative_to
from tizen_build_verify.edit_spec_guard import _line_starts as _line_starts
from tizen_build_verify.edit_spec_guard import _locate_edit as _locate_edit
from tizen_build_verify.edit_spec_guard import _LocatedEdit as _LocatedEdit
from tizen_build_verify.edit_spec_guard import _validate_schema as _validate_schema
from tizen_build_verify.edit_spec_guard import _validate_target_path as _validate_target_path
from tizen_build_verify.edit_spec_guard import validate_edit_spec as validate_edit_spec

__all__ = ["EDIT_SPEC_SCHEMA", "EditSpecViolation", "validate_edit_spec"]
