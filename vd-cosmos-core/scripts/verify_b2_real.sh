#!/usr/bin/env bash
# Invoke with bash --noprofile --norc; source pages/baselines are read-only.
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd "$script_dir/../.." && pwd)"
actual_commit="$(git -C "$repo_dir" rev-parse HEAD)"
printf '%s\n' "$actual_commit"
if [[ $# -lt 1 || "$1" != "$actual_commit" ]]; then
    printf '%s\n' '{"exit_code":6,"error":"expected_commit_mismatch","verdict":"FAIL"}'
    exit 6
fi
shift
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$script_dir/../src"
exec python3 -B "$script_dir/verify_b2_real.py" --verified-commit "$actual_commit" "$@"
