"""Suggester registry for BW-M2 workflow."""

from __future__ import annotations

from gbs_workflow.suggesters.base import SuggesterBase
from gbs_workflow.suggesters.compile_error import CompileErrorSuggester
from gbs_workflow.suggesters.depsolve import DepsolveSuggester
from gbs_workflow.suggesters.fallback import FallbackSuggester
from gbs_workflow.suggesters.linker_missing import LinkerMissingSuggester
from gbs_workflow.suggesters.linker_undef import LinkerUndefSuggester
from gbs_workflow.suggesters.patch_failed import PatchFailedSuggester
from gbs_workflow.suggesters.spec_script import SpecScriptSuggester

DEFAULT_SUGGESTERS: list[SuggesterBase] = [
    DepsolveSuggester(),
    LinkerMissingSuggester(),
    LinkerUndefSuggester(),
    PatchFailedSuggester(),
    SpecScriptSuggester(),
    CompileErrorSuggester(),
    FallbackSuggester(),
]
