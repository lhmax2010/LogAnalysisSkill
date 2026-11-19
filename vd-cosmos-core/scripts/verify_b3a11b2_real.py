#!/usr/bin/env python3
"""B2 build-machine acceptance with an anonymous source preflight."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from vd_cosmos_core.verify_b3a11b2 import main
raise SystemExit(main())
