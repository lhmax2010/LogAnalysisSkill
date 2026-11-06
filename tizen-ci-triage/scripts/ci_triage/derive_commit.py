"""Compatibility module alias for campaign commit derivation."""

import sys

from tizen_campaign_core import derive_commit as _implementation

sys.modules[__name__] = _implementation
