"""Layer 3 evidence collectors."""

from gbs_analyzer.evidence.base import Evidence, EvidenceCollector
from gbs_analyzer.evidence.compile import CompileEvidenceCollector
from gbs_analyzer.evidence.deps import DepsEvidenceCollector
from gbs_analyzer.evidence.link import LinkEvidenceCollector
from gbs_analyzer.evidence.spec import SpecEvidenceCollector

__all__ = [
    "CompileEvidenceCollector",
    "DepsEvidenceCollector",
    "Evidence",
    "EvidenceCollector",
    "LinkEvidenceCollector",
    "SpecEvidenceCollector",
]
