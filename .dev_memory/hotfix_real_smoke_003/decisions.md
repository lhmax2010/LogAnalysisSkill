# Decisions for Hotfix Real Smoke 003

| ID | Date | Decision | Source | Rationale | Impact |
| --- | --- | --- | --- | --- | --- |
| d001 | 2026-05-20 | Pattern data must live inside the `gbs_analyzer` package. | Real workflow failure from ffmpeg cwd. | Repo-root relative paths work only when cwd is the repository root and fail for real users or pip installs. | Runtime default paths become independent of caller cwd. |
