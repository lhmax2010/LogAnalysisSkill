# Known Issues for build skill broken-root clean retry

- Real broken-root reproduction depends on local GBS scratch-root state. If it
  cannot be reproduced during validation, unit tests cover the retry behavior
  with fake GBS scripts and real validation should be recorded as not available.

