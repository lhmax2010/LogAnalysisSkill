#!/usr/bin/env python3
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(root / 'vd-cosmos-core/src'), str(root / 'vd-fix-analyze/src')]
from vd_fix_analyze.cli import main
raise SystemExit(main())
