"""Baseline reproduction identity, reusing convergence fingerprint semantics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tizen_convergence_judge.convergence import error_count, primary_fingerprint


@dataclass(frozen=True)
class ReproduceResult:
    reproduced: bool
    basis: dict[str, Any]


def check(
    evidence_ci: dict[str, Any],
    evidence_local: dict[str, Any],
    *,
    package: str,
    arch_norm: str,
    toolchain_profile: str,
) -> ReproduceResult:
    ci = primary_fingerprint(evidence_ci, touched_files=None)
    local = primary_fingerprint(evidence_local, touched_files=None)
    phase_ci = (evidence_ci.get("primary_error") or {}).get("phase")
    phase_local = (evidence_local.get("primary_error") or {}).get("phase")
    ci_count, local_count = error_count(evidence_ci), error_count(evidence_local)
    fields = dict(
        package=package,
        arch=arch_norm,
        toolchain_profile=toolchain_profile,
        phase=phase_ci == phase_local,
        fingerprint=ci is not None and local is not None and ci.identity == local.identity,
    )
    return ReproduceResult(
        bool(fields["phase"] and fields["fingerprint"]),
        dict(
            matched_fields=fields,
            ci_fp=ci.to_dict() if ci else None,
            local_fp=local.to_dict() if local else None,
            error_count_ci=ci_count,
            error_count_local=local_count,
            error_count_drift=ci_count != local_count,
        ),
    )
