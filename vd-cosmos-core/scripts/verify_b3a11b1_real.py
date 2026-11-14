#!/usr/bin/env python3
"""Batch 3a-1.1 read-only build-machine acceptance launcher."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from vd_cosmos_core.verify_b3a11b1 import main
raise SystemExit(main())
