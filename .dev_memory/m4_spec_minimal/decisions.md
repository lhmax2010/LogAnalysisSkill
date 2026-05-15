# Decisions for M4: spec_minimal

| ID | Date | Decision | Source | Rationale | Impact |
| --- | --- | --- | --- | --- | --- |
| d001 | 2026-05-15 | Start M4 from merge commit `b600505` after M3 review approval and merge. | v0.5 §7, §8 | Keeps the handoff pointer aligned with reviewed `main`. | M4 branch starts from latest merged baseline. |
| d002 | 2026-05-15 | `find_spec_file` uses exact `<package>.spec`, falls back to a sole spec file, and raises on ambiguity. | v0.5 §6.1 | The design requires finding the spec file but does not define ambiguity behavior; deterministic failure is safer than guessing. | Callers get a clear error when source roots contain multiple non-matching spec files. |
| d003 | 2026-05-15 | BuildRequires, Patch, and Source values are returned as raw declarations with only comment/continuation cleanup. | v0.5 §6.1 | v0.5 explicitly defers macro expansion and version-constraint semantic comparison to v0.6. | M4 exposes useful raw metadata without pretending conditions/macros were evaluated. |
| d004 | 2026-05-15 | Buildlog phase markers are limited to top-level spec sections; `+ %configure` remains a shell command. | v0.5 §6.1 | Functional fixtures showed RPM macros can look like phase markers. Treating all `+ %...` lines as phases would lose the real last command. | Failure context can correctly report macro commands such as `%configure`. |
| d005 | 2026-05-15 | Store the spec parse uncertainty prompt text in `templates/spec_parse_uncertainty.md` for M7 use. | M4 startup instruction, v0.4.1 P0-3 | M4 owns parse-status uncertainty, while M7 owns packet assembly. | Prompt text is available without implementing packet assembly early. |
