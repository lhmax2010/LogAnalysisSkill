import assert from 'node:assert/strict';

// Existing exact facts remain exact; the newly authorized timestamp is checked separately.
export function withoutElapsed(rows) {
  return rows.map(({ elapsed_ms, ...facts }) => {
    assert.ok(Number.isInteger(elapsed_ms) && elapsed_ms >= 0);
    return facts;
  });
}
