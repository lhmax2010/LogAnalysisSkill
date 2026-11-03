# Formal Repetition Results

All tests use local fixtures and a private virtual display.

## c8

| Run | Result | Seconds | DENY_TARGET_GONE | FETCH_CONTINUE_FAILED | Failure shape | Load before / after (1,5,15 min) |
|---|---|---:|---:|---:|---|---|
| c8-01 | PASS | 182.39 | 0 | 0 | none | 0.70/0.92/1.08 / 0.46/0.77/0.99 |
| c8-02 | PASS | 182.92 | 0 | 0 | none | 0.46/0.77/0.99 / 1.96/1.19/1.10 |
| c8-03 | PASS | 184.38 | 0 | 0 | none | 1.96/1.19/1.10 / 3.76/2.48/1.64 |
| c8-04 | FAIL | 203.52 | 2 | 0 | racing-wicket-navigation: {'class_name': 'TargetClosedError', 'agent_code': None, 'category': 'OTHER_FRAMEWORK_ERROR'} | 3.76/2.48/1.64 / 9.94/6.42/3.37 |

## late

| Run | Result | Seconds | DENY_TARGET_GONE | FETCH_CONTINUE_FAILED | Failure shape | Load before / after (1,5,15 min) |
|---|---|---:|---:|---:|---|---|
