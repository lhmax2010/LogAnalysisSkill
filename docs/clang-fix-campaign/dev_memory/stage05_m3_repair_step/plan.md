# Stage 05 Plan: M3 Repair Step

## Goal

Expose the campaign repair step as the machine-consumable wrapper that executes
the frozen nine-step order and emits one deterministic JSON document.

## Order

1. Acquire unit/arch lock.
2. Validate source and unit identity.
3. Create or validate the round.
4. Reconcile prior PASS/invocation state.
5. Preflight previous evidence.
6. Consume one build invocation.
7. Run build-verify.
8. Record FAIL convergence or PASS link/convergence.
9. Release the lock.

## Exit Criteria

CLI routing, ordering, fail-closed exits, recovery short circuits, HELD
reachability, and stdout schema all need direct tests.
