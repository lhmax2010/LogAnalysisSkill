"""Compatibility alias for tizen_campaign_core._campaign_workspace."""

import sys

from tizen_campaign_core import _campaign_workspace as _implementation

sys.modules[__name__] = _implementation
