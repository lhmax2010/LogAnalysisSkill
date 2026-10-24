#!/usr/bin/env python3
"""Install-free bootstrap for the offline acceptance script."""
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from vd_cosmos_core.verify_b2 import main

raise SystemExit(main())
