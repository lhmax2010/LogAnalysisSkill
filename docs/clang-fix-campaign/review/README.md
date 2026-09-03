# Review Protocol

评审只读：发现问题报 finding，不得修改被审文件。

当前 skill-1 冻结契约：
`../p49-skill1-convergence-judge-design-v1.4-FROZEN.md`。

## P4.9 Skill 4-6 Review Template Checks

- For every byte-for-byte migrated copy, review whether inherited comments
  remain true at the new location, especially comments containing “shim,”
  “temporary,” “will be deleted,” or equivalent wording.
- Every numeric/count assertion must include a reproducible command scoped to
  the surface being asserted. A bare number or repository-wide count cannot
  stand in for a narrower conflict-surface claim.
