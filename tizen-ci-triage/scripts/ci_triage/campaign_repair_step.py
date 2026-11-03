"""Compatibility alias for tizen_campaign_repair.campaign_repair_step."""

import sys

from tizen_campaign_repair import campaign_repair_step as _implementation

sys.modules[__name__] = _implementation
