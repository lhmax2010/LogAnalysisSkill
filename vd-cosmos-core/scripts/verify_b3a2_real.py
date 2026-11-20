#!/usr/bin/env python3
"""Entry point for the build machine's read-only 3a-2 analysis check."""
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from vd_cosmos_core.verify_b3a2 import main

if __name__ == '__main__':
    raise SystemExit(main())
