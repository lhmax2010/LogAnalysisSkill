"""Compatibility alias for tizen_campaign_core.suppress_policy."""

import sys

from tizen_campaign_core import suppress_policy as _implementation

sys.modules[__name__] = _implementation
