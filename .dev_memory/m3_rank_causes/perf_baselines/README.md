# M3 Perf Baselines

Recorded baselines:

- `rank_5_fixtures.json`: 5 M3 rank fixtures, 200 iterations, Top-1 accuracy and runtime.
- `rank_5_fixtures_cold.json`: same fixtures with `SemanticClassifier.from_file` cache cleared before every rank call.
