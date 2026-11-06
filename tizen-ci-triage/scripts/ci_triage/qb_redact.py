"""Compatibility alias for tizen_qb_verify.qb_redact."""

import sys

from tizen_qb_verify import qb_redact as _implementation

sys.modules[__name__] = _implementation
