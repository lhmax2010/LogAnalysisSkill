"""Compatibility alias for tizen_qb_verify.qb_result_fetch."""

import sys

from tizen_qb_verify import qb_result_fetch as _implementation

sys.modules[__name__] = _implementation
