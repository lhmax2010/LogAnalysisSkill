#!/usr/bin/env python3
import sys
from pathlib import Path
sys.dont_write_bytecode = True
repo = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(repo / 'vd-cosmos-core/src'), str(repo / 'vd-cosmos-submit/src')]
from vd_cosmos_submit.cli import main
if __name__ == '__main__':
    raise SystemExit(main())
