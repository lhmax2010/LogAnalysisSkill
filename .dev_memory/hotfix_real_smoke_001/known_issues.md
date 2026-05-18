# Known Issues

## Resolved In PR2

- Assembler diagnostics with uppercase `Error:` and `.S` source files are now classified as `kind: compiler`.
- Packet token overflow is guarded in `assemble_packet()`.

## Deferred

- H4 pre-build recovered-error downranking is not implemented in this hotfix because the assembler diagnostic wins Top-1 after H1/H2/H3.
- H5 make cascade changes are not implemented in this hotfix because existing source-to-object suffix mapping links the make cascade to an assembler event.

## Real Smoke Status

The scanner-only PR proved:

- `commands == 73`
- `failed_phase == "%build"`
- Top-1 after the full wrapper moved from the early `pristine-tar` raw error to the
  assembler line, but remains `kind: raw_error`.

Full acceptance remains:

- Top-1 event file is `libavcodec/arm/h264cmc_neon.S`.
- Top-1 event line is `43`.
- Top-1 event kind is `compiler`.
- Cascade parent links to an assembler event with the same file/line root cause.
- `packet_tokens == 1674`, under the requested `1800` cap.
