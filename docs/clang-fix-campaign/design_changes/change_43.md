# change_43: E6' cynara supplied input cannot establish a clean baseline

Status: **CLOSED - no design change; test-input issue**

Date: 2026-08-05

## Trigger

The RC scope required a newly constructed, realistic Clang/LLVM 22 C++ case in
`cynara`. Fault injection was permitted only after an unchanged checkout built
successfully, so that any later failure could be attributed to the injected
change.

## Observed facts

The supplied cynara checkout was clean at
`611ff2ecc979bbd9d269e2bc7eb227a895055667`. Before any source edit, real GBS
failed four translation units because `plugin/PluginCache.h` was missing:

```text
src/service/logic/Logic.h:38:10: fatal error: 'plugin/PluginCache.h' file not found
src/service/main/Cynara.h:35:10: fatal error: 'plugin/PluginCache.h' file not found
```

The accepted raw log is
`tmp/campaign-smoke/logs/E6-cynara-clean.log`, SHA-256
`a549babe112ed7d73813844c6d180042bde5ab6b31502e80efd7d6e568e4d17b`.
The repository had no matching header, plugin directory, submodule, or
generation step. The source remained clean. No synthetic fault was injected
on this invalid baseline.

## Decision

This is a source snapshot/input problem, not a campaign design or runtime
problem. Rejecting fault injection was the correct fail-closed behavior.
Developer adjudication authorized exactly one attempt to locate and build the
accepted Wave 1-era cynara snapshot before degrading E6 acceptance.

No explicit Wave 1 SHA ledger was present. The repository's concrete accepted
toolchain reference identified:

```text
commit: 9add176aefd99e9274e99f597a15c26e75067429
tag: accepted/tizen/unified/toolchain/20260725.092057
subject: Release 0.26.0
```

This commit predates `611ff2e` (`Adjust to new plugin management`) and does not
reference `PluginCache.h`. The single authorized clean-baseline retry passed:

```text
log: tmp/campaign-smoke/logs/E6-cynara-wave1-clean.log
sha256: cbdbe2079b89065bbdd6c7b8b9cf0a10b04a717ee135beace6b025c71addc256
result: Total succeeded built packages: (1)
```

## Closure evidence

The accepted snapshot then supported the full E6' exercise:

- a committed C++ template mismatch produced a real Clang candidate-list
  diagnostic;
- two independent GBS/analyzer runs produced identical fingerprints;
- a one-line guarded repair passed real GBS through `campaign-repair-step`;
- verification `ebb7960f-c7d0-4ec4-975f-daaa771b042f` was linked to round 1;
- the protected build copy remained clean and changed only
  `src/service/main/CmdlineParser.cpp`.

E6' therefore completed under option (a). Options (b) and (c) were not used.
There is no residual C++ rich-diagnostic TODO for the P5 gate from this
adjudication.

## Related non-blocking observation

The multi-assistant patch-suggest output uses formatter operation
`insert_after`, while frozen design section 3.4 binds campaign build
verification to the existing `edit_spec_guard` contract requiring
`file/old/new`. The direct edit spec was rejected fail-closed before GBS. The
same safe edit was represented as an exact `old/new` replacement and passed.
This remains an integration seam, not a request to change the frozen guard.
