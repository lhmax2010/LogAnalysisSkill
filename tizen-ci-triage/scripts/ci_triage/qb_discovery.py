"""Compatibility alias for tizen_qb_verify.qb_discovery."""

import sys

from tizen_qb_verify import qb_discovery as _implementation

sys.modules[__name__] = _implementation
