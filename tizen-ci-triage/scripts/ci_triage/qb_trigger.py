"""Compatibility alias for tizen_qb_verify.qb_trigger."""

import sys

from tizen_qb_verify import qb_trigger as _implementation

sys.modules[__name__] = _implementation
