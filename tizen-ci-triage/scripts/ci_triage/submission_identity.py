"""Compatibility alias for tizen_campaign_core.submission_identity."""

import sys

from tizen_campaign_core import submission_identity as _implementation

sys.modules[__name__] = _implementation
