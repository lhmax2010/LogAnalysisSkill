"""Resolve source context for fix-all source candidates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from gbs_patch_suggest.cluster_ingest import LargeScaleCluster
from gbs_patch_suggest.cluster_resolver import ClusterFileContext, resolve_clusters
from gbs_patch_suggest.fix_all_ingest import FixAllIngestResult, SourceCandidateDiagnostic

FIX_ALL_CLUSTER_ID = "FIXALL"


@dataclass(frozen=True)
class ResolvedFixAllContext:
    """Resolved context for fix-all by file mode."""

    candidates: tuple[SourceCandidateDiagnostic, ...]
    patch_ready_candidates: tuple[SourceCandidateDiagnostic, ...]
    file_contexts: tuple[ClusterFileContext, ...]


def resolve_fix_all(
    ingest: FixAllIngestResult,
    *,
    src_root: Path | None,
) -> ResolvedFixAllContext:
    """Resolve patch-ready source candidates into per-file contexts."""

    patch_ready = ingest.patch_ready_candidates
    if not patch_ready:
        return ResolvedFixAllContext(
            candidates=ingest.candidates,
            patch_ready_candidates=(),
            file_contexts=(),
        )

    cluster = LargeScaleCluster(
        id=FIX_ALL_CLUSTER_ID,
        warning_option="source_candidates",
        diagnostic_kinds=tuple(
            sorted({candidate.kind for candidate in patch_ready if candidate.kind})
        ),
        truncated=False,
        locations=tuple(candidate.as_location() for candidate in patch_ready),
    )
    resolved = resolve_clusters((cluster,), src_root=src_root)
    file_contexts = resolved[0].file_contexts if resolved else ()
    return ResolvedFixAllContext(
        candidates=ingest.candidates,
        patch_ready_candidates=patch_ready,
        file_contexts=file_contexts,
    )
