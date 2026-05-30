# Decisions for build skill broken-root clean retry

| ID | Decision | Source | Rationale | Impact |
| --- | --- | --- | --- | --- |
| d001 | Retry only after a normal non-timeout failure whose compiler log contains `Your build system is broken`. | User request and confirmation. | Timeout logs may be incomplete and represent a different failure class; ordinary build failures should preserve existing v0.2 behavior. | Normal incremental builds are unchanged, broken-root failures get one clean retry, and timeout handling remains independent. |
| d002 | Use official `--clean` retry instead of writing `y` to stdin. | User request. | `--clean` is the non-interactive GBS mechanism and avoids scripting an interactive destructive prompt. | The runner can work in subprocess/non-interactive AI environments without depending on prompt wording beyond detection. |
| d003 | Record the final command in `BuildResult.command`. | User confirmation. | The command field should describe the invocation that produced the final result. | If the clean retry runs, callers see a command ending in `--clean`; otherwise command semantics stay unchanged. |
| d004 | Set `stdin=subprocess.DEVNULL` for each GBS invocation. | User request and build-root prompt behavior. | Broken-root prompts should receive EOF/default behavior instead of hanging on inherited stdin. | Non-interactive runs avoid prompt stalls; tests verify stdin is EOF for fake GBS processes. |

