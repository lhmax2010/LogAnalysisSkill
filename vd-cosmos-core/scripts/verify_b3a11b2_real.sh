#!/usr/bin/env bash
# Offline suite plus an anonymous source preflight. Never opens the live browser.
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd "$script_dir/../.." && pwd)"
actual_commit="$(nice -n 19 git -C "$repo_dir" rev-parse HEAD)"
nice -n 19 python3 --version >&2
printf '%s\n' "$actual_commit" >&2
if [[ $# -lt 1 || ! "$1" =~ ^[0-9a-fA-F]{40}$ || "$1" != "$actual_commit" ]]; then
    printf '%s\n' '{"exit_code":6,"error":"expected_commit_mismatch","verdict":"FAIL"}'
    exit 6
fi
shift
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$script_dir/../src"
exec nice -n 19 python3 -B "$script_dir/verify_b3a11b2_real.py" --verified-commit "$actual_commit" "$@"
