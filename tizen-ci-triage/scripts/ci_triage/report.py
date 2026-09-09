"""Compatibility shim for the extracted triage-report skill."""

from tizen_triage_report.report import TriageReportData, _primary_location, render_report

__all__ = ["TriageReportData", "_primary_location", "render_report"]
