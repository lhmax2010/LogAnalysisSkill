"""Compatibility alias for tizen_qb_verify.qb_evidence."""

import sys

from tizen_qb_verify import qb_evidence as _implementation

sys.modules[__name__] = _implementation
