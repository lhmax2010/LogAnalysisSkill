"""Simulate a pyenv build without either optional compression extension."""
import sys

for name in ('_lzma', '_bz2'):
    sys.modules[name] = None
