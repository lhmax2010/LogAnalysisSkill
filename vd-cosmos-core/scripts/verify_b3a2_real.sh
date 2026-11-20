#!/usr/bin/env bash
# Verify immutable, already-downloaded data. No network, browser, P4 or AI.
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd "$script_dir/../.." && pwd)"
actual_commit="$(nice -n 19 git -C "$repo_dir" rev-parse HEAD)"
nice -n 19 python3 --version >&2
printf '%s\n' "$actual_commit" >&2
if [[ $# -lt 1 || ! "$1" =~ ^[0-9a-f]{40}$ || "$1" != "$actual_commit" ]]; then
    printf '%s\n' '{"exit_code":6,"error":"expected_commit_mismatch","verdict":"FAIL"}'
    exit 6
fi
shift
exec nice -n 19 python3 -I -B "$script_dir/verify_b3a2_real.py" --verified-commit "$actual_commit" "$@"
