# Known Issues for Restructure Phase 4

- Historical files intentionally keep old path references. This includes `.dev_memory/`,
  `docs/archive/`, historical real-smoke design docs, and status reports.
- `integrations/cline/*.json` use installed mode only. Direct folder mode is documented
  in `integrations/cline/README.md` rather than encoded as a second JSON contract.

