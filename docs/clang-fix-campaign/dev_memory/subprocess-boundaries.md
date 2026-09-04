# P4.9 Subprocess Boundary Ledger

Static import contracts do not inspect dependencies crossed through process
execution. A green `lint-imports` result therefore does not prove that these
edges are absent or architecturally valid.

| Owner | Process edge | Source evidence | Closing point |
|---|---|---|---|
| `tizen_build_verify.build_verify` | `python -m gbs_analyzer analyze` | `_analyze_failure` builds the command at `tizen-build-verify/scripts/tizen_build_verify/build_verify.py:401-404` | Keep as an explicit runtime dependency; re-audit when analyzer ownership changes |
| `tizen_build_verify.build_verify` | `gbs build` | `_gbs_command` / `_run_gbs_build` in the same module | Build-verify runtime contract |
| `tizen_build_verify.build_verify` | `git` | `_git`, `_git_stdout`, diff and commit helpers in the same module | Build-verify runtime contract |
| `tizen_build_verify.workspace` | `cp -a` and `git` | `_copy_repository` and shared workspace git helpers | Build-verify workspace contract |

The precise in-process exception
`tizen_build_verify.build_verify -> gbs_patch_suggest.formatter` is separately
enforced by both root-layers and skill-independence. Its ignored edge also
removes any future transitive formatter dependency from import-linter's view;
that known limitation must be reconsidered if formatter gains new package
dependencies.
