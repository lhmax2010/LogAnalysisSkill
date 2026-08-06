# Stage 06 Result: RC Real E2E Smoke

## Result

RC completed E1-E6 against real GBS 2.0.6 and Clang/LLVM 22.1.8. No runtime or
frozen-design change was needed during execution. The authoritative evidence
and command transcript are in `../../review/e2e-smoke-report-v1.md`.

## Covered paths

- Synthetic zlib: real analyzer evidence, `advance`, PASS, and invocation
  accounting.
- Crash recovery: unlinked PASS was reconciled without rebuild or extra charge.
- Edge guards: lock loser, round exhaustion, and HELD reachability.
- Historical multi-assistant: stable historical/fresh fingerprint and
  dual-compiler-safe spec repair PASS.
- C++ rich diagnostics: two independent cynara template/candidate-list failures
  yielded an identical normalized fingerprint, followed by a one-round real
  repair PASS.

## Input adjudications

- change_41: raw logs are audit inputs; analyzer JSON is fingerprint evidence.
- change_42: `standard-armv7l` is the public raw architecture identity;
  `armv7l` is normalized internally.
- change_43: the supplied cynara HEAD was not buildable; this was a test-input
  issue. The single accepted-snapshot retry at `9add176` passed and completed
  E6'. All three changes closed without design or runtime modification.

## Plan-external validations

1. Fingerprint consistency was demonstrated across separate GBS and analyzer
   runs for both unknown-warning-option and C++ template candidate-list
   diagnostics.
2. The full real repair chain reached a protected PASS verification record and
   campaign link for both the historical packaging case and the constructed
   source case.

## Final status

COMPLETE. E1-E6 and E5 reporting are closed. The formatter-valid
`insert_after` versus campaign old/new guard mismatch remains a named,
non-blocking integration seam; the guard was not weakened. C++ rich-diagnostic
fingerprint stability was directly covered by E6'. RD close-out evidence is
recorded separately; PR human review is the only remaining project-level gate.
