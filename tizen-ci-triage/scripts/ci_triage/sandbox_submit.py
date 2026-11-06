"""Compatibility alias for tizen_sandbox_submit.sandbox_submit."""

import sys

from tizen_sandbox_submit import sandbox_submit as _implementation

sys.modules[__name__] = _implementation
