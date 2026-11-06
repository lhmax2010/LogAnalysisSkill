"""Compatibility alias for tizen_qb_verify.qb_result_html."""

import sys

from tizen_qb_verify import qb_result_html as _implementation

sys.modules[__name__] = _implementation
