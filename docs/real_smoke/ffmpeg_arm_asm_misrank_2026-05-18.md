# Real Smoke: ffmpeg ARM assembler error mis-ranked behind source-export noise

## Summary

Real smoke run against a local Tizen `gbs` build of ffmpeg shows that MVP M8 runs
successfully, but the analyzer chooses the wrong Top-1 root cause.

The correct root cause is an ARM assembler error introduced in:

```text
libavcodec/arm/h264cmc_neon.S:43
```

The analyzer instead ranks an earlier `pristine-tar` export message as Top-1:

```text
fatal: path 'ffmpeg-8.0.1.tar.gz.delta' does not exist in 'refs/heads/pristine-tar'
```

That earlier message is not the build failure root cause because the log continues
through source export, dependency resolution, RPM `%prep`, `%build`, compilation, and
only then fails.

## Reproduction Command

Local command used by the user:

```bash
python3 -m gbs_analyzer analyze <ffmpeg-root>/ffmpeg.log \
    --src-root <ffmpeg-root> \
    --max-tokens 1800 \
    --trace \
    --output-dir <ffmpeg-root>/output/real_smoke_1
```

The actual `ffmpeg` checkout is outside this repository and must not be committed.

## Intentional Source Changes

The user intentionally modified ffmpeg to validate the skill. Local diff summary:

```diff
diff --git a/libavcodec/arm/h264cmc_neon.S b/libavcodec/arm/h264cmc_neon.S
@@
         vld1.16         {d22[],d23[]}, [r6,:16]
+        sasdd            r1, r1, r3

diff --git a/libavcodec/h264_slice.c b/libavcodec/h264_slice.c
@@
 }
-
+fsfs
 static int alloc_scratch_buffers(H264SliceContext *sl, int linesize)
```

The current build stops first on the ARM assembler error, so the `h264_slice.c` syntax
change does not become the final observed build failure in this log.

## Relevant Log Excerpts

Early source-export noise:

```text
info: Generating diff file HEAD..<commit>
fatal: path 'ffmpeg-8.0.1.tar.gz.delta' does not exist in 'refs/heads/pristine-tar'
pristine-tar: git show refs/heads/pristine-tar:ffmpeg-8.0.1.tar.gz.delta failed
error: Couldn't checkout "ffmpeg-8.0.1.tar.gz": it exited with 128
info: ffmpeg-8.0.1.tar.gz does not exist, creating from 'upstream/8.0.1'
```

The build then continues:

```text
info: package files have been exported to:
...
*** [1/1] building ffmpeg-8.0.1-0 armv7l tizen_unified_standard
...
[  194s] Executing(%prep): /bin/sh -e /var/tmp/rpm-tmp...
[  208s] Executing(%build): /bin/sh -e /var/tmp/rpm-tmp...
[  209s] + /bin/make -j40
```

Actual failure:

```text
[  213s] AS	libavcodec/arm/h264cmc_neon.o
[  213s] libavcodec/arm/h264cmc_neon.S: Assembler messages:
[  213s] libavcodec/arm/h264cmc_neon.S:43: Error: bad instruction `sasdd r1,r1,r3'
[  213s] libavcodec/arm/h264cmc_neon.S:455:  Info: macro invoked from here
[  213s] libavcodec/arm/h264cmc_neon.S:43: Error: bad instruction `sasdd r1,r1,r3'
[  213s] make: *** [ffbuild/common.mak:93: libavcodec/arm/h264cmc_neon.o] Error 1
[  217s] error: Bad exit status from /var/tmp/rpm-tmp... (%build)
```

## Observed Analyzer Output

M8 wrapper succeeds:

- exit code: `0`
- stdout: clean
- outputs: `evidence_packet.json`, `evidence_packet.md`, `perf_report.json`, `trace.jsonl`, `trace.log`

But the packet is wrong:

```json
{
  "verdict": "needs_llm",
  "via": "full_path",
  "matched_tier": null,
  "failed_phase": null,
  "primary_error": {
    "id": "E001",
    "kind": "raw_error",
    "message": "fatal: path 'ffmpeg-8.0.1.tar.gz.delta' does not exist in 'refs/heads/pristine-tar'",
    "line_no": 20,
    "phase": null,
    "command_id": null
  }
}
```

Trace summary from the run:

```text
scan_completed {"commands": 0, "events": 20, "failed_phase": null}
```

Key symptoms:

- `commands = 0`
- `failed_phase = null`
- all RPM phases are lost
- the assembler failure is classified as `raw_error`
- source file path is not extracted from the assembler diagnostic
- Top-1 is an early non-fatal source-export error
- `packet_tokens = 2367`, exceeding `--max-tokens 1800`

## Expected Analyzer Behavior

Expected Top-1 should be the assembler diagnostic:

```json
{
  "primary_error": {
    "kind": "compiler_or_assembler",
    "file": "libavcodec/arm/h264cmc_neon.S",
    "line": 43,
    "message": "bad instruction `sasdd r1,r1,r3'"
  },
  "failed_phase": "%build",
  "via": "full_path",
  "verdict": "needs_llm"
}
```

The packet should include:

- `%build` as the failed phase.
- command summary near `/bin/make -j40` or the closest build command available.
- source snippet around `libavcodec/arm/h264cmc_neon.S:43`.
- cascade summary linking `libavcodec/arm/h264cmc_neon.o` to the assembler diagnostic.
- packet token estimate within `--max-tokens 1800`.

## Root Causes in Analyzer

### 1. GBS/RPM timestamp prefix is not normalized

Real lines often begin with a prefix:

```text
[  208s] + /bin/make -j40
[  213s] libavcodec/arm/h264cmc_neon.S:43: Error: bad instruction ...
```

MVP scanners expect bare lines such as:

```text
+ /bin/make -j40
libavcodec/arm/h264cmc_neon.S:43: error: ...
```

This causes command detection, phase detection, and file/line extraction to fail.

### 2. RPM phase markers in real logs use `Executing(%build):`

The log contains:

```text
[  208s] Executing(%build): /bin/sh -e /var/tmp/rpm-tmp...
```

MVP only handles `+ %build` style markers. As a result `failed_phase` remains null.

### 3. Assembler diagnostics are not first-class

The actual error uses uppercase `Error:` and an assembly file:

```text
libavcodec/arm/h264cmc_neon.S:43: Error: bad instruction ...
```

MVP falls back to `raw_error`, losing `file`, `line`, and semantic meaning.

### 4. Early non-fatal source-export errors are not demoted

The `pristine-tar` error is followed by recovery:

```text
info: ffmpeg-8.0.1.tar.gz does not exist, creating from 'upstream/8.0.1'
```

Ranking currently ties generic errors and sorts by earlier line number, so source-export
noise wins over later build-failing diagnostics.

### 5. Fallback packet can exceed token budget

`perf_report.json` shows:

```json
{
  "tokens": {
    "packet_tokens": 2367,
    "budget": {
      "limit": 1800
    }
  }
}
```

This violates the wrapper contract expectation for `--max-tokens 1800`.

## Design Review Disposition

Claude's design review accepted the five root causes above, but narrowed the hotfix
scope so real-buildlog adaptation does not become a v0.6 mini-cycle.

Accepted hotfix sequence:

1. H1/H2 first: fix scanner normalization and real RPM `Executing(...)` phase markers.
2. H3/H6 second: recognize assembler diagnostics as existing `kind: compiler`, then
   enforce the final packet token cap.
3. H4/H5 stay deferred unless H1/H2/H3 still fail the ffmpeg acceptance check.

Key accepted constraints:

- Extend existing `LogLine` with `raw_text` and `gbs_seconds`; do not add a new
  normalization dataclass.
- Strip only GBS timestamp prefixes and ANSI color escapes.
- Support only `Executing(%prep|%build|%install|%check):`.
- Preserve trace/debug fidelity by recording both normalized and raw text in scan traces.
- Do not update `docs/DESIGN.md` for this hotfix; roll lessons into a future v0.6 design
  only after more real buildlog data.

After H1/H2 implementation on the user's real ffmpeg log:

```text
commands: 73
failed_phase: %build
primary after full wrapper: assembler line as raw_error in %build
packet_tokens: 3342
```

This confirms H1/H2 fixed the root scanner miss. H3 is still needed for structured
assembler classification and cascade linkage. H6 is still needed for the hard token cap.

## Initial Hotfix Questions Captured for Review

### H1. Normalize real GBS line prefixes in scanner

Add line normalization that strips ANSI escape codes and extracts an optional GBS
timestamp prefix while keeping original `raw_offset` and `line_no`.

Design review answer: keep both raw and normalized text on existing `LogLine`; do not
introduce a new dataclass.

Examples:

```text
[  213s] libavcodec/arm/h264cmc_neon.S:43: Error: bad instruction ...
=> libavcodec/arm/h264cmc_neon.S:43: Error: bad instruction ...

\x1b[32minfo:\x1b[0m prepare sources...
=> info: prepare sources...
```

Design review answer: keep both fields. `LogLine.text` is normalized matcher input;
`LogLine.raw_text` preserves the original line for trace/debug fidelity.

### H2. Detect real RPM phase markers

Add support for:

```text
Executing(%prep):
Executing(%build):
Executing(%install):
Executing(%check):
```

After prefix normalization, this should set `current_phase` exactly as `+ %build` does.

### H3. Recognize assembler diagnostics

Minimum hotfix option:

- Extend compiler diagnostic regex to accept `.S`.
- Accept uppercase/lowercase severities: `Error`, `error`, `Warning`, `warning`.
- Accept assembler-style message: `file:line: Error: bad instruction ...`.
- Classify as existing `kind: compiler` to avoid schema churn.

Alternative design option:

- Add `kind: assembler` and route it to CompileEvidenceCollector.

Design review answer: reuse `kind: compiler`; add `details.is_assembler` during H3.

### H4. Demote recovered pre-build source-export errors

Possible ranking/scanner rules:

- If a raw `fatal/error` occurs before any RPM phase/build start and later build phases
  exist, mark it as `details.recovered_prebuild_error = true` or lower its rank.
- Specifically demote `pristine-tar` checkout failures when followed by
  `does not exist, creating from 'upstream/...'`.
- Prefer diagnostics in `failed_phase` over diagnostics outside the failed phase.
- For equal-confidence generic errors, prefer later diagnostics inside the failed RPM
  phase over earlier pre-build diagnostics.

Design review answer: defer H4. If still needed after H1/H2/H3, prefer a ranker rule.

### H5. Link make cascade to assembler/source event

After assembler diagnostics carry `file = libavcodec/arm/h264cmc_neon.S`, existing
source-to-object mapping should be checked against:

```text
make: *** [ffbuild/common.mak:93: libavcodec/arm/h264cmc_neon.o] Error 1
```

Acceptance: cascade parent should point to the assembler diagnostic, not remain
`unlinked`.

### H6. Enforce `--max-tokens` on final packet/prompt

Short-term hotfix:

- Reduce fallback raw context when final packet estimate exceeds `max_tokens`.
- Recompute token estimate after truncation.
- Add a warning/degradation reason such as `packet_truncated_to_token_budget`.

Design review answer: enforce in `packet_assembler.py`.

## Final Hotfix Acceptance Criteria

Add a sanitized fixture derived from this case, not the full ffmpeg tree:

```text
tests/fixtures/real_smoke_ffmpeg_arm_asm/
├── buildlog
├── expected_packet.json
├── README.md
└── src/libavcodec/arm/h264cmc_neon.S
```

Expected core assertions:

- `commands > 0`
- `failed_phase == "%build"`
- Top-1 event points to `libavcodec/arm/h264cmc_neon.S:43`
- final `perf_report.tokens.packet_tokens <= 1800`

Regression gate:

- Existing 20 M8 E2E fixtures have zero regressions.
- Full suite passes.
- Overall coverage remains at or above 96%.

## Non-Goals for This Hotfix

- Do not implement full M9 collectors.
- Do not add a generic collector.
- Do not implement full `expand`.
- Do not commit the user's local ffmpeg tree, full build output, or generated
  `output/real_smoke_1` artifacts.
