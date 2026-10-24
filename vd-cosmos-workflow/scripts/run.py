#!/usr/bin/env python3
import sys
from pathlib import Path
sys.dont_write_bytecode = True
repo = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(repo / (name + '/src')) for name in ('vd-cosmos-core', 'vd-cosmos-watch', 'vd-cosmos-fetch', 'vd-cosmos-workflow')]
from vd_cosmos_workflow.cli import main
raise SystemExit(main())
