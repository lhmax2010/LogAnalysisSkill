"""Explicit timestamp formats supported equally by Python 3.10 and 3.12."""
from datetime import datetime
import re


def parse_datetime(value):
    if not isinstance(value, str):
        raise ValueError('timestamp must be text')
    value = value.strip().replace('/', '-')
    # Report and P4 timestamps use compact numeric offsets, optionally separated
    # from the time by a space. Normalize before the 3.10 ISO parser.
    value = re.sub(r'\s*([+-]\d{2})(\d{2})$', r'\1:\2', value)
    if value.endswith('Z'):
        value = value[:-1] + '+00:00'
    return datetime.fromisoformat(value)
