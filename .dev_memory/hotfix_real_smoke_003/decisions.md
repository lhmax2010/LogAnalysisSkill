# Decisions for Hotfix Real Smoke 003

| ID | Date | Decision | Source | Rationale | Impact |
| --- | --- | --- | --- | --- | --- |
| d001 | 2026-05-20 | Pattern data must live inside the `gbs_analyzer` package. | Real workflow failure from ffmpeg cwd. | Repo-root relative paths work only when cwd is the repository root and fail for real users or pip installs. | Runtime default paths become independent of caller cwd. |
| d002 | 2026-05-20 | Default pattern paths are anchored with `Path(__file__)`. | User hotfix instruction. | The existing API expects concrete `Path` values and explicit file overrides; anchoring to the module file is the smallest compatible fix. | Default loaders work from arbitrary cwd, and temp-file tests still pass custom paths. |
| d003 | 2026-05-20 | Use setuptools package data for packaged patterns. | Pip-install validation requirement. | Moving files under the package is not enough for wheel/install workflows unless package data includes the non-Python files. | Installed packages include `README.md`, `error_semantics.yaml`, `gbs_errors.yaml`, and `schema.json`. |
| d004 | 2026-05-20 | Do not use `importlib.resources` for this hotfix. | User hotfix constraint. | Editable/local installs and existing `Path`-based cache comparisons are simpler and safer with concrete package-relative paths. | No resource-loader abstraction added; cache behavior remains familiar. |
| d005 | 2026-05-20 | Leave `templates/` unchanged. | `rg` found no `templates` runtime references under `gbs_analyzer/`. | The bug affects runtime pattern/semantic YAML loading only; moving unused templates would increase scope. | Templates stay repo-root documentation/template material. |
