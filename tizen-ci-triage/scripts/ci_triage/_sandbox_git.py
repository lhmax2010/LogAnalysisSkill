"""Compatibility alias for tizen_campaign_core._sandbox_git."""

import sys

from tizen_campaign_core import _sandbox_git as _implementation

sys.modules[__name__] = _implementation
