"""Compatibility alias for tizen_qb_verify.qb_binding."""

import sys

from tizen_qb_verify import qb_binding as _implementation

sys.modules[__name__] = _implementation
