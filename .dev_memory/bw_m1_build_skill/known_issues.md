# Known Issues for BW-M1: gbs_build_skill

## Watch Points

- Real gbs validation is environment-dependent. BW-M1 verified the local ffmpeg success and B
  depsolve failure paths with `gbs 2.0.6` and `/home/linhao/Toolchain/gbs.conf`.
- Running `python3 -m gbs_build_skill` from outside the repository with the system Python fails unless
  the package is installed into that interpreter. The validated command uses the repository `.venv`
  Python. Fresh CI installs via `pip install -e .`, so this is expected.

## Out of Scope

- No Suggester implementation.
- No analyzer invocation.
- No source patch application or build retry.
