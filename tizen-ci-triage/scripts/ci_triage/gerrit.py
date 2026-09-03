"""Compatibility shim for the extracted Gerrit fetch skill."""

from tizen_ci_shared.types import GerritChange as GerritChange
from tizen_ci_shared.types import GerritPatchSet as GerritPatchSet
from tizen_ci_shared.types import SourceFetchResult as SourceFetchResult
from tizen_gerrit_fetch.gerrit import GERRIT_HOST as GERRIT_HOST
from tizen_gerrit_fetch.gerrit import GERRIT_PORT as GERRIT_PORT
from tizen_gerrit_fetch.gerrit import GerritError as GerritError
from tizen_gerrit_fetch.gerrit import SubprocessRunner as SubprocessRunner
from tizen_gerrit_fetch.gerrit import _optional_int as _optional_int
from tizen_gerrit_fetch.gerrit import _reset_generated_source_dir as _reset_generated_source_dir
from tizen_gerrit_fetch.gerrit import _run_git as _run_git
from tizen_gerrit_fetch.gerrit import change_from_query_obj as change_from_query_obj
from tizen_gerrit_fetch.gerrit import fetch_source_for_commit as fetch_source_for_commit
from tizen_gerrit_fetch.gerrit import find_patchset_by_revision as find_patchset_by_revision
from tizen_gerrit_fetch.gerrit import parse_gerrit_query_output as parse_gerrit_query_output
from tizen_gerrit_fetch.gerrit import query_change_for_commit as query_change_for_commit

__all__ = [
    "GERRIT_HOST",
    "GERRIT_PORT",
    "GerritChange",
    "GerritError",
    "GerritPatchSet",
    "SourceFetchResult",
    "SubprocessRunner",
    "change_from_query_obj",
    "fetch_source_for_commit",
    "find_patchset_by_revision",
    "parse_gerrit_query_output",
    "query_change_for_commit",
]
