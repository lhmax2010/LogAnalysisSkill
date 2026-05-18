# Real Smoke Cases

This directory records real buildlog validation cases discovered after MVP.

Rules:

- Do not commit large proprietary or local build trees.
- Do not copy full real buildlogs unless they are explicitly sanitized.
- Prefer short excerpts, observed analyzer outputs, expected root cause, and design questions.
- Hotfix branches may reference the local reproduction path, but committed docs should use
  redacted placeholders such as `<ffmpeg-root>`.
