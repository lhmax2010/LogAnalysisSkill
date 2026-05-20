"""Suggestion generators for GbsBuildWorkflow."""

from __future__ import annotations

from gbs_workflow.suggesters.base import Suggestion, SuggesterBase
from gbs_workflow.suggesters.depsolve import DepsolveSuggester
from gbs_workflow.suggesters.registry import DEFAULT_SUGGESTERS

__all__ = ["DEFAULT_SUGGESTERS", "DepsolveSuggester", "Suggestion", "SuggesterBase"]
