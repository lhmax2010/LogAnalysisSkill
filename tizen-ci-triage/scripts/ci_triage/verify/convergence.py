"""Compatibility shim for the extracted convergence-judge skill."""

from tizen_convergence_judge.convergence import (
    ConvergenceResult as ConvergenceResult,
)
from tizen_convergence_judge.convergence import (
    _error_count as _error_count,
)
from tizen_convergence_judge.convergence import (
    _primary_fingerprint as _primary_fingerprint,
)
from tizen_convergence_judge.convergence import (
    check_convergence as check_convergence,
)
from tizen_convergence_judge.convergence import (
    error_count as error_count,
)
from tizen_convergence_judge.convergence import (
    primary_fingerprint as primary_fingerprint,
)
from tizen_convergence_judge.convergence import (
    touched_files_from_json as touched_files_from_json,
)
from tizen_convergence_judge.convergence import (
    write_convergence_result as write_convergence_result,
)

__all__ = [
    "ConvergenceResult",
    "check_convergence",
    "error_count",
    "primary_fingerprint",
    "touched_files_from_json",
    "write_convergence_result",
]
