# Decisions

| ID | Date | Decision | Source | Rationale | Impact |
| --- | --- | --- | --- | --- | --- |
| d001 | 2026-05-18 | Preserve both normalized `LogLine.text` and original `LogLine.raw_text`; add `gbs_seconds`. | Real ffmpeg smoke review H1. | Scanner regexes need normalized text, while trace/debugging needs the exact original line and timestamp. | Small `LogLine` schema expansion; no scan result schema change. |
| d002 | 2026-05-18 | Normalize only GBS timestamp prefixes and ANSI color escapes. | Real ffmpeg smoke review H1. | The real failure is caused by `[  213s] ` and color codes; stripping broader prefixes could change unrelated logs. | Minimal compatibility risk for existing fixtures. |
| d003 | 2026-05-18 | Support only `Executing(%prep|%build|%install|%check):` as RPM phase markers. | Real ffmpeg smoke review H2. | These are build phases required by the MVP flow; generic `Executing(%...):` would include RPM scriptlets outside build analysis scope. | Correctly sets `current_phase` for real GBS logs without expanding phase semantics. |
| d004 | 2026-05-18 | Trace scan events with both `text` and `raw_text` when a source line is available. | Real ffmpeg smoke review trace note. | Debugging real logs needs normalized matcher input and original raw line side by side. | Slight trace size increase; no public output schema change. |
