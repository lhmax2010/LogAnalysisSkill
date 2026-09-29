# Erratum 1: First Authorized Observations

Status: item3/item4 PASS; expected-diff registration stopped on DIFF-03.
This is not an A0 completion certificate. No item5 or other producer ran.

## Provenance

- Approved rules: intake commit `32b7f432bdeed0b7f6aeeb26c9e37bd1d13486e1`,
  SHA-256 `d44584592b54bfaf1406c13369da5f2f6a5894fc3dd8de04b3905eadd6213c3f`.
- Predicate freeze: `6601cfc60fcbed8d2f8fa91301f7693d52723d94`; bytes unchanged.
- Observation HEAD: `43a6aa625f27da46daba190657bf62256080c68e`.
- Observation tree: `ca9331190e878af465e7968fe56e735585a5866e`.
- cwd: `/home/linhao/Toolchain/development/LogAnalysisSkill-a0-43a6aa6`.
- Python: `/tmp/p49-a0-baseline-v12-43a6aa6/bin/python`.
- Scripts are loaded by absolute main-tree path, not misreported as old-tree code.
  Each command record pins tool hashes; each raw output records the producer hash
  and the separate rules/code roots. Production imports are checked against cwd.

## Artifacts

`e1-item{3,4}/output.json` are raw claim-schema facts. `raw.json` contains the
unabridged fixture observations, source call spans, argv/kwargs, process exits,
exception fields, and before/after disk hashes. There are no policy verdicts in
either producer output. `e1-item{3,4}-verifier.log` contains the independent CLI
verdict, with command/environment/exit in the corresponding `.command.json`.

All external git/ssh calls use fake runners, so there is no network access or
remote repository mutation. Production Python filesystem operations execute in
isolated temporary directories. Signal probes use real child-process SIGINT or
SIGTERM; parent observations are made after the child exits. SIGINT exits -2,
SIGTERM exits -15. The fixture locations remain recorded for inspection.

`e1-observation-summary.log` is a jq projection of raw facts, not an oracle.
`e1-dangling-message-evidence.log` plus `e1-source-dir-message.log` and
`e1-message-rule-scope.log` establish the DIFF-03 stop. No producer output was
edited to satisfy its predicate. The failed initial mypy output is retained;
it preceded production observation and the final rerun is green.

## Reproduction

Every `e1-*.command.json` contains the exact argv, cwd, environment and exit.
Use that independent venv, unset PYTHONPATH/MYPYPATH, and run from the recorded
clean cwd. For a new producer run choose a fresh `--out` directory: the producer
refuses to overwrite evidence. Verify its output with the recorded full registry
hash, generated renderer block, context, and explicit `--claim`.

Replaying observations is distinct from proving post-change parity: no production
change exists yet and the full scenario/result schemas are not frozen. In
particular, marker reader enumeration and the two item5 interruption scenarios
are NOT collected here. Do not substitute empty readers or inferred results.

The current blocker and proposed (not adopted) resolution are in progress §15.3.
Expected-diff schema/mode checks and the seven admission controls remain NOT_RUN.
