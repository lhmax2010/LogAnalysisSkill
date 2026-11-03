# Campaign Kickoff Inputs

Fill every applicable field before starting. Do not place passwords, cookies or
session data here. Missing entries require a question, not a guessed default.

## Shared Inputs

- CONFIG: absolute campaign YAML path.
- STATE_DB: absolute campaign database path (new or explicitly approved resume).
- STATE_ROOT: one absolute evidence/trace/results root shared by ALL QuickBuild
  commands, including trigger, result fetch and later rereads.
- REPORT_PATH: report output path.
- Operator / CONFIRMED_BY: human identity for explicit release confirmations.
- Git author identity and Git committer identity: `Name <email>`, frozen in CONFIG.
- Authorization: current batch and permitted external actions; batch 3.5 forbids
  sandbox/review pushes and QuickBuild and retains its three linked PASS copies.

## Every Package

| Required input | Value |
|---|---|
| PROJECT (Gerrit project) | |
| BRANCH | |
| SPEC_NAME (package) | |
| BASE_COMMIT | |
| CI_LOG (local build log) | |
| SOURCE_BUILD_ID | |
| FAILED_ARCHES (registered raw names, comma-separated) | |
| TOOLCHAIN_PROFILE | |
| CLANG_CONF (must equal configured clang_conf_path) | |
| BASELINE_OUTPUT (separate output directory for each architecture) | |
| SANDBOX_BRANCH (sandbox/... name, not refs/heads/...) | |
| REVIEW_TARGET (refs/for/ followed by BRANCH) | |
| MESSAGE_BRIEF | |
| SOURCE_KIND (generated or suppress) | |
| MAX_ROUNDS and max_build_invocations | |

UNIT_KEY, SRC_CLEAN and primary architecture come from add-unit. ROUND_INDEX and
EDIT_SPEC describe the current repair; VERIFICATION_IDS come from the three linked
PASS outputs of the same final round. REQUEST_ID and QB_RESULT come from the
QuickBuild commands. Never invent these values or workspace/iter paths.

## Configuration Checklist

Startup requires gerrit_ssh_base (ssh://), gerrit_user, git_author_identity,
git_committer_identity, push_timeout_sec, push_retry, target_arches,
campaign_workspace and clang_conf_path. Intake also needs max_rounds and
max_build_invocations. Submission requires the approved commit-msg hook path
and its gerrit_commit_msg_hook_sha256. QuickBuild requires its existing validated
qb section (browser paths, timeout, enabled branch/project profile and form).
Retain the authority's existing configuration format; do not add a state_root
configuration key. STATE_ROOT above is passed explicitly on every QB command.
