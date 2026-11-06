"""Compatibility alias for tizen_qb_verify.qb_browser."""

import sys

from tizen_qb_verify import qb_browser as _implementation

sys.modules[__name__] = _implementation
