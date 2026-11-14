# Browser-free submission tracking (Checkpoint B1)

Entry point: `python3 vd-cosmos-submit/scripts/run.py <command> --config <config.json>`.
See SKILL.md for read-only usage; human decisions are documented only in `docs/enhance/batch3a-1.1/FATTANK-B1-MANUAL.md`.

The skill depends only on core. `bm_pages.py` parses registered management fields in memory; `bm_transport.py` owns an anonymous, same-host cookie jar that is discarded on close. `bm_reader.py` handles anchored paging and bounded detail reads. `submit_model.py`, `submit_claim.py` and `submit_watch.py` persist requests, candidates and observation tasks in the existing append-only SQLite journal. A separate observation lock spans the process lifetime; request locks protect state changes only, with version checks after network reads.

All 18 properties are present in `config.sample.json` under `submit.property_map`; `variable: null` and `encoding: null` mean unregistered. They do not license a guessed variable mapping or browser encoding. The verified recon25 follow-up (designer, 2026-11-14) enables cmp-v1 for registered variable/encoding pairs, including text. The legacy `request_text_verified` flag no longer gates text comparison; unregistered, absent or not-listed mappings stay unverified. PACKAGE_LIST is compared by parsed entries. EMAIL_CC is not listed on the observed variable pages and does not affect the build. New settings and defaults are documented in the core README and frozen HLD Appendix B.

Fixture manifests have `pages: {"https://bm.example.invalid/path": {"file": "relative.html", "clock": {"valid": true, "offset_s": 0, "error_s": 0, "server_time": 0, "sent_at": 0, "received_at": 0, "rtt_s": 0}}}`. Use a list of these entries to replay page changes. The test helpers reconstruct the observed recon15–22 structures with synthetic names and values; they are not saved authenticated pages.

B1.1 uses the shared header-based `variable_pages.py` parser: Name/Value are required, Display Name is optional and never contributes to a value. Selected values (including known absence) are frozen on first read under data_root/inputs/variable-first-read, separately from page HTML. Changes produce a durable “变量页已变化” todo and exit 3; originals remain authoritative. Same-Hub consistent builds are a “重跑链”, with every build listed and no automatic selection; inconsistent relationship evidence remains “冲突”.
