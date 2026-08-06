# Clang Fix Campaign Checkpoints

| Tag | Commit | Coverage | Rollback command | State after rollback |
|---|---|---|---|---|
| `checkpoint/p45_code_ready` | `269321820abe0eddb7db345dcb26ffaedc7127c6` | P0 contract gates; M1 state; M2 reconciliation; M3 repair-step and tests | `git reset --hard checkpoint/p45_code_ready` | Code-ready P4.5 implementation with no RA/RB documentation or RC smoke results |

The rollback command is destructive to uncommitted work. Inspect and preserve
the worktree before using it.
