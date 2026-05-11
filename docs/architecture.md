# Architecture Overview

This document is a short implementation companion to `docs/DESIGN.md` v0.5. The
design document remains the frozen source of truth.

The analyzer is organized as a single-entry pipeline:

1. `analyze.py` owns the wrapper contract, tracing setup, output paths, and exit codes.
2. `scan_and_extract.py` streams the buildlog once, records phase and command structure,
   and emits diagnostic events.
3. `quick_filter.py` checks tier1 fast-path patterns before evidence collection.
4. `rank_causes.py` ranks root-cause candidates and keeps Top-K summaries.
5. `evidence/` collectors gather targeted context under `BudgetPool` control.
6. `full_match.py` evaluates direct-answer tier2 eligibility.
7. `packet_assembler.py` assembles JSON and Markdown Evidence Packets, applies redaction,
   records token use, and emits performance reports.

M0 only creates this documentation and the package skeleton. Implementation begins in M1
with `scan_and_extract.py` and the tracing foundation.
