#!/usr/bin/env bash
set -euo pipefail
core_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_dir="$(dirname "$core_dir")"
mkdir -p "$core_dir/.runtime"
export TMPDIR="$core_dir/.runtime"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$core_dir/src:$repo_dir/vd-cosmos-watch/src:$repo_dir/vd-cosmos-fetch/src:$repo_dir/vd-cosmos-workflow/src:$core_dir/tests:$core_dir/.devtools"
cd "$core_dir"
python3 --version
python3 scripts/check_imports.py
if command -v lint-imports >/dev/null 2>&1; then
    lint_command="$(command -v lint-imports)"
elif [[ -f "$core_dir/.devtools/bin/lint-imports" ]]; then
    lint_command="$core_dir/.devtools/bin/lint-imports"
else
    echo 'Missing repository dev tool import-linter==2.3; see README.md.' >&2
    exit 6
fi
"$lint_command" --config "$core_dir/.importlinter" --no-cache
python3 -m unittest discover -s tests -p 'test_*.py' -v
