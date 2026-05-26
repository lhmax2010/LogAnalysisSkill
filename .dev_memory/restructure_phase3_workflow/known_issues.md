# Known Issues for Restructure Phase 3

- Phase 3 leaves broad documentation and integration cleanup to Phase 4.
- `pyproject.toml` still includes `"."` in package discovery because Phase 4 is responsible for final package-discovery cleanup after all code has moved.
- Direct skill-folder mode depends on the Python interpreter having runtime third-party dependencies such as PyYAML available; this matches the existing local environment assumptions and does not vendor dependencies.
