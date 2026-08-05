# P0 Signature Audit: v1.5.14 to v1.5.16

This report records the per-signature audit required by change_39 A.5 before
P1 consumes `design.md` section 4.2. The old side was extracted from the local
v1.5.14 frozen snapshot. The new side was parsed from the final v1.5.16
`python` fence with `ast.parse`.

## Result

- Old contract inventory: 44 explicit pseudo-signatures plus one
  comment-embedded `cleanup_disposable_copy` contract.
- New contract inventory: 45 executable Python declarations.
- Missing or additional API identities: none.
- The four high-risk signatures retain their parameter order, keyword-only
  boundary, and return type.
- Changes called out below as notation normalization preserve the prose
  contract in the adjacent comments.

## High-Risk Signatures

```text
reconcile_pass_and_invocations(state_db, campaign_unit_key, *, round_index, arch_norm, failure_key, edit_spec_sha256) -> ReconcileResult
adopt_secondary_target_with_convergence(state_db, campaign_unit_key, *, arch_norm, expected_reproduce_event_id, convergence_payload) -> bool
consume_build_invocation(state_db, campaign_unit_key, *, round_index, arch_norm) -> InvocationReceipt
append_status(state_db, campaign_unit_key, status, reason=None, arch_norm=None) -> None
```

The old and new forms of all four lines are identical after removing the old
module-name prefix. In particular,
`adopt_secondary_target_with_convergence` contains exactly one
`convergence_payload` parameter.

## Complete Old/New Inventory

```text
01 build_campaign_unit_key
OLD submission_identity.build_campaign_unit_key(*, ci_system, source_build_id, project, branch, spec_name, base_commit) -> str
NEW build_campaign_unit_key(*, ci_system, source_build_id, project, branch, spec_name, base_commit) -> str

02 build_submission_identity_key
OLD submission_identity.build_submission_identity_key(*, ci_system, project, branch, spec_name, base_commit) -> str
NEW build_submission_identity_key(*, ci_system, project, branch, spec_name, base_commit) -> str

03 compute_submission_key
OLD submission_identity.compute_submission_key(submission_identity_key, verified_tree_sha) -> str
NEW compute_submission_key(submission_identity_key, verified_tree_sha) -> str

04 compute_change_id
OLD submission_identity.compute_change_id(submission_key) -> str
NEW compute_change_id(submission_key) -> str

05 ensure_schema
OLD campaign_state.ensure_schema(state_db) -> None
NEW ensure_schema(state_db) -> None

06 create_unit
OLD campaign_state.create_unit(state_db, *, campaign_unit_key, submission_identity_key, primary_arch, failed_arches, toolchain_profile, ci_evidence_ref, ci_evidence_sha256, max_rounds, max_build_invocations, **identity_fields) -> None
NEW create_unit(state_db, *, campaign_unit_key, submission_identity_key, primary_arch, failed_arches, toolchain_profile, ci_evidence_ref, ci_evidence_sha256, max_rounds, max_build_invocations, **identity_fields) -> None

07 create_arch_rejected_unit
OLD campaign_state.create_arch_rejected_unit(state_db, *, campaign_unit_key, submission_identity_key, failed_arches, reason, toolchain_profile, max_rounds, max_build_invocations, **identity_fields) -> None
NEW create_arch_rejected_unit(state_db, *, campaign_unit_key, submission_identity_key, failed_arches, reason, toolchain_profile, max_rounds, max_build_invocations, **identity_fields) -> None

08 get_unit
OLD campaign_state.get_unit(state_db, campaign_unit_key) -> Unit | None
NEW get_unit(state_db, campaign_unit_key) -> Unit | None

09 append_event
OLD campaign_state.append_event(state_db, campaign_unit_key, event_type, payload) -> int
NEW append_event(state_db, campaign_unit_key, event_type, payload) -> int

10 latest_event
OLD campaign_state.latest_event(state_db, campaign_unit_key, event_type) -> dict | None
NEW latest_event(state_db, campaign_unit_key, event_type) -> dict | None

11 adopt_secondary_target_with_convergence
OLD campaign_state.adopt_secondary_target_with_convergence(state_db, campaign_unit_key, *, arch_norm, expected_reproduce_event_id, convergence_payload) -> bool
NEW adopt_secondary_target_with_convergence(state_db, campaign_unit_key, *, arch_norm, expected_reproduce_event_id, convergence_payload) -> bool

12 latest_reproduce
OLD campaign_state.latest_reproduce(state_db, campaign_unit_key, *, arch_norm) -> dict | None
NEW latest_reproduce(state_db, campaign_unit_key, *, arch_norm) -> dict | None

13 find_unlinked_pass
OLD campaign_state.find_unlinked_pass(state_db, campaign_unit_key, *, arch_norm, failure_key) -> list[dict]
NEW find_unlinked_pass(state_db, campaign_unit_key, *, arch_norm, failure_key) -> list[dict]

14 ReconcileResult
OLD campaign_state.ReconcileResult
NEW class ReconcileResult:

15 reconcile_pass_and_invocations
OLD campaign_state.reconcile_pass_and_invocations(state_db, campaign_unit_key, *, round_index, arch_norm, failure_key, edit_spec_sha256) -> ReconcileResult
NEW reconcile_pass_and_invocations(state_db, campaign_unit_key, *, round_index, arch_norm, failure_key, edit_spec_sha256) -> ReconcileResult

16 append_status
OLD campaign_state.append_status(state_db, campaign_unit_key, status, reason=None, arch_norm=None) -> None
NEW append_status(state_db, campaign_unit_key, status, reason=None, arch_norm=None) -> None

17 latest_status
OLD campaign_state.latest_status(state_db, campaign_unit_key) -> str | None
NEW latest_status(state_db, campaign_unit_key) -> str | None

18 create_round
OLD campaign_state.create_round(state_db, campaign_unit_key, *, round_index, edit_spec_ref, edit_spec_sha256) -> None
NEW create_round(state_db, campaign_unit_key, *, round_index, edit_spec_ref, edit_spec_sha256) -> None

19 get_round
OLD campaign_state.get_round(state_db, campaign_unit_key, round_index) -> Round | None
NEW get_round(state_db, campaign_unit_key, round_index) -> Round | None

20 latest_round
OLD campaign_state.latest_round(state_db, campaign_unit_key) -> Round | None
NEW latest_round(state_db, campaign_unit_key) -> Round | None

21 invocations_used
OLD campaign_state.invocations_used(state_db, campaign_unit_key) -> int
NEW invocations_used(state_db, campaign_unit_key) -> int

22 InvocationReceipt
OLD campaign_state.InvocationReceipt
NEW class InvocationReceipt:

23 consume_build_invocation
OLD campaign_state.consume_build_invocation(state_db, campaign_unit_key, *, round_index, arch_norm) -> InvocationReceipt
NEW consume_build_invocation(state_db, campaign_unit_key, *, round_index, arch_norm) -> InvocationReceipt

24 link_verification_with_convergence
OLD campaign_state.link_verification_with_convergence(state_db, campaign_unit_key, *, convergence_payload, arch_raw, arch_norm, verification_id, round_index, edit_spec_sha256) -> None
NEW link_verification_with_convergence(state_db, campaign_unit_key, *, convergence_payload, arch_raw, arch_norm, verification_id, round_index, edit_spec_sha256) -> None

25 create_qb_request
OLD campaign_state.create_qb_request(state_db, campaign_unit_key, *, request_id, sbs_target) -> int
NEW create_qb_request(state_db, campaign_unit_key, *, request_id, sbs_target) -> int

26 append_qb_event
OLD campaign_state.append_qb_event(state_db, *, request_seq, event_type, qb_build_id=None, status=None, accepted=None, sbs_target_echo=None, per_arch_status_json=None, qb_result_sha256=None, qb_result_ref=None, degraded=False) -> int
NEW append_qb_event(state_db, *, request_seq, event_type, qb_build_id=None, status=None, accepted=None, sbs_target_echo=None, per_arch_status_json=None, qb_result_sha256=None, qb_result_ref=None, degraded=False) -> int

27 find_unit_by_request_id
OLD campaign_state.find_unit_by_request_id(state_db, request_id) -> str | None
NEW find_unit_by_request_id(state_db, request_id) -> str | None

28 find_unit_by_qb_build_id
OLD campaign_state.find_unit_by_qb_build_id(state_db, qb_build_id) -> str | None
NEW find_unit_by_qb_build_id(state_db, qb_build_id) -> str | None

29 latest_qb_result
OLD campaign_state.latest_qb_result(state_db, campaign_unit_key) -> dict | None
NEW latest_qb_result(state_db, campaign_unit_key) -> dict | None

30 release_superseded_partial_round
OLD campaign_lifecycle.release_superseded_partial_round(state_db, campaign_unit_key, *, round_index) -> list[str]
NEW release_superseded_partial_round(state_db, campaign_unit_key, *, round_index) -> list[str]

31 release_held_worktrees
OLD campaign_lifecycle.release_held_worktrees(state_db, campaign_unit_key, *, confirmed_by: str) -> list[str]
NEW release_held_worktrees(state_db, campaign_unit_key, *, confirmed_by: str) -> list[str]

32 release_terminal_worktrees
OLD campaign_lifecycle.release_terminal_worktrees(state_db, campaign_unit_key) -> list[str]
NEW release_terminal_worktrees(state_db, campaign_unit_key) -> list[str]

33 gate_view
OLD campaign_state.gate_view(state_db, campaign_unit_key) -> GateView
NEW gate_view(state_db, campaign_unit_key) -> GateView

34 aggregate_verifications
OLD aggregate.aggregate_verifications(ids, state_db) -> AggregateResult
NEW aggregate_verifications(ids, state_db) -> AggregateResult

35 derive
OLD derive_commit.derive(worktree: Path, tree_sha, parent_sha, message, author_identity, committer_identity, author_date, committer_date) -> str
NEW derive(worktree: Path, tree_sha, parent_sha, message, author_identity, committer_identity, author_date, committer_date) -> str

36 cleanup_disposable_copy
OLD comment-embedded contract: cleanup_disposable_copy(worktree_path: str, expected_workspace_root: str, *, reject_protected: bool = True) -> None
NEW cleanup_disposable_copy(worktree_path: str, expected_workspace_root: str, *, reject_protected: bool = True) -> None

37 toctou_recheck
OLD toctou_recheck(record, worktree) -> bool
NEW toctou_recheck(record, worktree) -> bool

38 check_push_ref
OLD check_push_ref(ref) -> RefClass{SANDBOX|REVIEW|FORBIDDEN}
NEW check_push_ref(ref) -> RefClass

39 reproduce.check
OLD reproduce.check(evidence_ci, evidence_local, *, package, arch_norm, toolchain_profile) -> ReproduceResult
NEW check(evidence_ci, evidence_local, *, package, arch_norm, toolchain_profile) -> ReproduceResult

40 suppress_policy.evaluate
OLD suppress_policy.evaluate(edit_spec, src_root, source_kind: {"t1_cherry_pick", "generated", "suppress"}) -> PolicyVerdict
NEW evaluate(edit_spec, src_root, source_kind: Literal["t1_cherry_pick", "generated", "suppress"]) -> PolicyVerdict

41 review_submit.validate_qb_gate
OLD review_submit.validate_qb_gate(state_db, campaign_unit_key, qb_result_path, *, allow_manual: bool = False) -> QbGateResult
NEW validate_qb_gate(state_db, campaign_unit_key, qb_result_path, *, allow_manual: bool = False) -> QbGateResult

42 diff2edit.convert
OLD diff2edit.convert(diff_path, src_root) -> list[EditSpecEntry] | raises UnsupportedDiff
NEW convert(diff_path, src_root) -> list[EditSpecEntry]

43 kb.query
OLD kb.query(db, *, diagnosed_flag, package=None, gerrit_path=None, category=None, warning_flags=None, toolchain_profile=None, error_signature=None, min_status="CI_VERIFIED", limit_t2=5) -> QueryResult{t1: list, t2: list}
NEW query(db, *, diagnosed_flag, package=None, gerrit_path=None, category=None, warning_flags=None, toolchain_profile=None, error_signature=None, min_status="CI_VERIFIED", limit_t2=5) -> QueryResult

44 kb.append
OLD kb.append(db, record) -> AppendResult{id, deduped: bool}
NEW append(db, record) -> AppendResult

45 kb.promote
OLD kb.promote(db, id, to_status) -> KbRecord
NEW promote(db, id, to_status) -> KbRecord
```

## Notation Normalization

The following changes make the skeleton valid Python without changing the
adjacent prose contract:

- Module prefixes moved to `# module:` headings; function names and argument
  contracts are unchanged.
- `check_push_ref` returns `RefClass`; the allowed enum members remain stated
  in its comment.
- `evaluate` now uses a valid `Literal[...]` annotation for the same three
  source kinds.
- `convert` returns `list[EditSpecEntry]`; `UnsupportedDiff` remains the
  documented exceptional outcome in its comment.
- `query` and `append` return their named result types; result fields remain
  documented next to the declarations.
- `cleanup_disposable_copy` moved from a comment-embedded signature into an
  executable declaration so P1 has one unambiguous API surface.

## Reproduction Commands

The first full-test invocation omitted the component script roots and failed
during collection because `ci_triage` was not importable. The successful,
reproducible rerun was:

```bash
PYTHONPATH=tizen-ci-triage/scripts:tizen-gbs-log-analysis/scripts:tizen-gbs-patch-suggest/scripts:tizen-gbs-build/scripts \
  .venv/bin/pytest -q
```

Result: `750 passed, 1 skipped`.

The type-check command was:

```bash
PYTHONPATH=tizen-ci-triage/scripts \
  .venv/bin/mypy tizen-ci-triage/scripts/ci_triage
```

Result: `Success: no issues found in 23 source files`.

Additional P0 gates:

```bash
.venv/bin/ruff check docs/clang-fix-campaign/tools/check_design_doc.py
python3 docs/clang-fix-campaign/tools/check_design_doc.py --self-test
python3 docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md
cmp docs/clang-fix-campaign/design.md docs/clang-fix-campaign/history/clang-fix-campaign-design-v1.5.16-FROZEN.md
sha256sum docs/clang-fix-campaign/p45-implementation-prompt-v1_5_15.md
```

Results: Ruff clean; checker self-test `33/33`; current design `OK: 0
problem`; snapshot byte-identical; prompt SHA-256
`e214d1fb8b806e1ebc12e6e8cfafc57d71cbffcf0340d94c26396ef87816a3fb`.
