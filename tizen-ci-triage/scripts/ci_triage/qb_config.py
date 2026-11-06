"""Compatibility alias for tizen_qb_verify.qb_config."""

import sys

from tizen_qb_verify import qb_config as _implementation

sys.modules[__name__] = _implementation
