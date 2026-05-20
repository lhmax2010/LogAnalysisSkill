"""Suggester registry for BW-M2 workflow."""

from __future__ import annotations

from gbs_workflow.suggesters.base import SuggesterBase
from gbs_workflow.suggesters.depsolve import DepsolveSuggester

DEFAULT_SUGGESTERS: list[SuggesterBase] = [DepsolveSuggester()]
