# SKEL-R-05: New Stop Rule Conflicts With Immutable Existing Assertions

Status: **STOPPED BEFORE IMPLEMENTATION**. Baseline `46db465`.
SKEL-R-04 is registered verbatim in stage21 progress section 21.
SKEL-R-02 diagnostics are accepted by SKEL-R-04(1); this report does not reopen
that review or reject the newly authorized failRequest exception.

## Conflict

SKEL-R-04(3) requires zero onStop calls for
`Fetch.failRequest + REQUEST_ID_INVALID`, every time. Step 2(3) also requires
all existing agent tests unchanged and passing. Three existing assertions in
`tests/node/test_qb_read_failure_diagnostics.mjs` cannot satisfy both:

| Node test | Line | Existing expectation | Required by new rule |
|---|---:|---|---|
| `rejected Fetch.failRequest still stops and records fixed metadata` | 40 | One FETCH_CONTINUE_FAILED stop | Zero stops; DENY_TARGET_GONE |
| `capture scheduling phase and generation, keep first rejection only` | 60 | Two stops: target closed, then invalid request ID | One stop for target closed; invalid ID only DENY_TARGET_GONE |
| `read navigation cancellation concurrent with a rejected Fetch keeps initiating failure` | 96 | One stop for invalid-ID failRequest | Zero Fetch stops; navigation error still follows its original path |

The Python wrapper is the existing nodeid
`tests/unit/test_qb_read_failure_diagnostics.py::test_node_read_failure_diagnostics`.
No new test can make the contradictory old assertions pass. Branching on test
names, bypassing assertions or changing the failure's classification would
violate the rule; none was attempted.

## Read-Only Verification

`probe-existing-contract.py.txt` runs the original Node test file and compares
all tracked skill/test/frozen/design files against `46db465`. It does not
change the source or construct an alternative implementation.

- `baseline-node.stdout.log`: 17 passed / 0 failed / 0 skipped, Node exit 0.
- `baseline-facts.json`: exact three assertion texts and source lines;
  protected_files_changed is empty.
- No browser, server or network is started by this EventEmitter-based suite.
- 20 CPUs; before/after loadavg `0.58 0.89 1.04`.
- Agent full SHA256 before and after:
  `d0e99f7e4caf11104920ddfe7a569a75e100c5a1dc44a3a916d73ef2bacbf823`.
- Agent prefix SHA256 before and after:
  `3bb1c0cc2fbfcb20aef324c8b8a703f06f40a438211317e0e96f2ba30f2be4c2`.
- Production diff: 0 lines. No new behavior has been tested or delivered.

## Candidate Ruling, Not Applied

Permit changes only to the three directly conflicting expectations and add
DENY_TARGET_GONE assertions. Retain all parameters and pytest nodeids; the two
continue operations and every other failure category must still stop.
All other existing assertions and the allow/deny matrix stay unchanged.

Illustrative assertion-only diff, for design approval:

```diff
@@ rejected ${method} still stops and records fixed metadata
-    assert.deepEqual(stops, ['FETCH_CONTINUE_FAILED']);
+    assert.deepEqual(stops, method === 'Fetch.failRequest' ? [] : ['FETCH_CONTINUE_FAILED']);
+    assert.deepEqual(trace.filter(row => row.action === 'DENY_TARGET_GONE'),
+      method === 'Fetch.failRequest' ? [{ action: 'DENY_TARGET_GONE', phase: 'login',
+        stage: 'request', path: '<other>', generation: 1 }] : []);
@@ capture scheduling phase and generation, keep first rejection only
-  assert.deepEqual(stops, ['FETCH_CONTINUE_FAILED', 'FETCH_CONTINUE_FAILED']);
+  assert.deepEqual(stops, ['FETCH_CONTINUE_FAILED']);
+  assert.deepEqual(trace.filter(row => row.action === 'DENY_TARGET_GONE'),
+    [{ action: 'DENY_TARGET_GONE', phase: 'read', stage: 'request', path: '<other>', generation: 2 }]);
@@ read navigation cancellation concurrent with a rejected Fetch keeps initiating failure
-  assert.deepEqual(stops, ['FETCH_CONTINUE_FAILED']);
+  assert.deepEqual(stops, []);
+  assert.deepEqual(trace.filter(row => row.action === 'DENY_TARGET_GONE'),
+    [{ action: 'DENY_TARGET_GONE', phase: 'read', stage: 'request', path: '<other>', generation: 0 }]);
```

The first OPERATION_FAILED assertion remains intact, including the second
case's original TARGET_OR_SESSION_CLOSED first cause. The third case retains
its original QB_BROWSER_UNAVAILABLE navigation result assertion. This proposal
does not authorize any further production exception or rewrite any request
allow/deny test.

## Pending Work

Implementation, design.md appendix note, new exception-specific tests, four
safety groups, C8 20 runs, C5a 20 runs, and the complete regression/static gates
remain unstarted. The baseline 17 passes are not substituted for those gates.
No full-regression run used `-x`; there was no full-regression run this turn.
No true QuickBuild, Gerrit, gbs or push to Gerrit was performed. Wait for the
test-change allowance before implementation; do not silently choose one of
the contradictory requirements.
