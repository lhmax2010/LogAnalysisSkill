"""Compatibility alias for tizen_campaign_core.campaign_state."""

import sys

from tizen_campaign_core import campaign_state as _implementation

sys.modules[__name__] = _implementation
