# B-0 fixed-tree baseline

All commands ran with cwd
`/home/linhao/Toolchain/development/LogAnalysisSkill-a0-43a6aa6`, detached at
`43a6aa625f27da46daba190657bf62256080c68e`, tree
`ca9331190e878af465e7968fe56e735585a5866e`.

The isolated Python 3.12.3 environment is
`/tmp/p49-a0-baseline-v12-43a6aa6`. It installs this worktree, not the main
worktree. Exact argv/cwd/environment/exit records are `*.command.json`; logs
retain original combined stdout/stderr. Only reproduction-relevant environment
values are recorded, not credentials. Dependency versions are in `packages.log`.

```bash
uv venv --python /usr/bin/python3 --seed /tmp/p49-a0-baseline-v12-43a6aa6
export PATH=/tmp/p49-a0-baseline-v12-43a6aa6/bin:$PATH
export VIRTUAL_ENV=/tmp/p49-a0-baseline-v12-43a6aa6
unset PYTHONPATH MYPYPATH PYTEST_ADDOPTS PYTEST_PLUGINS
python -m pip install -e '.[dev]' -r requirements-dev.txt
python -m pip freeze
pytest tests/ -vv --tb=short --junitxml=/absolute/evidence/path/pytest.xml
mypy
ruff check .
lint-imports
```

`nodeids.json` is extracted from the verbose pytest log and cross-checked with
the JUnit test count; it records every nodeid and result. This is B-0, not an OBS
claim run. No terminal-batch producer exists in this fixed tree. The new
comparator's artificial tests are separately recorded in `../predicates-v1.2/`.

Environment preparation notes: system `python3 -m venv` first failed because
`ensurepip` was unavailable. `uv` initially selected Python 3.13; before any
baseline command, the owned temporary venv was recreated with explicit
`--python /usr/bin/python3` (3.12.3). Neither event changed the fixed worktree.
