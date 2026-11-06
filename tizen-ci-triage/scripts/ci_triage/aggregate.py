"""Compatibility alias for tizen_campaign_core.aggregate."""

import sys

from tizen_campaign_core import aggregate as _implementation

sys.modules[__name__] = _implementation
