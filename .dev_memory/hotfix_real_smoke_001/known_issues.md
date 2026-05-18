# Known Issues

## Deferred Until H3/H6

- Assembler diagnostics with uppercase `Error:` and `.S` source files may still be classified as `raw_error` until H3 extends the compiler diagnostic matcher.
- Packet token overflow remains possible until H6 adds a final packet size guard.

## Deferred Unless Still Needed

- H4 pre-build recovered-error downranking is not implemented in this hotfix. If H1/H2/H3 make the assembler diagnostic the Top-1 event, H4 stays deferred to v0.6.
- H5 make cascade changes are not implemented in this hotfix. Existing source-to-object suffix mapping should handle `.S -> .o` after H3 extracts the assembler source path.

## Real Smoke Status

The scanner-only PR proved:

- `commands == 73`
- `failed_phase == "%build"`
- Top-1 after the full wrapper moved from the early `pristine-tar` raw error to the
  assembler line, but remains `kind: raw_error`.

Full acceptance remains:

- Top-1 event file is `libavcodec/arm/h264cmc_neon.S`
- Top-1 event line is `43`
- Cascade parent links to the assembler event or a decision explains why it remains deferred
- `packet_tokens <= 1800`
