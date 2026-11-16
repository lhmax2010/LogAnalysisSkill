# Anonymized real Cosmos pages

Source: designer-supplied pages30.md, captured/anonymized on the build machine by diag30b. Only the seven HTML blocks are fixtures; the terminal transcript is excluded. GitHub issue transport expanded tabs: original per-page byte SHA256 annotations are no longer valid. Incoming whitespace-free SHA256 is computed with `sha256(re.sub(r"\s+", "", page).encode("utf-8"))` and was verified against the designer values before editing.

B3a11-Q10 approved 2026-11-16: whole-token replacement of the remaining Hub/BM hosts with hub.example.invalid / bm.example.invalid, in every occurrence including href and Hub Link text. No other byte changes. Tests explicitly use both placeholder hosts. `manifest.json` records incoming and committed digests; archived diagnostic scripts are not executed.

| Page | Incoming whitespace-free SHA256 | Hub replacements | BM replacements | Committed SHA256 |
|---|---|---|---|---|
| history_4362_p1.html | 5d6bb9f0c5710ecc7f5c2b55e22e9c2125e10360f721895921a95d9f676565d5 | 0 | 1 | ebc786b0b9866707f9043cb509edd890cd4c107471757498953624cedd8ee70e |
| overview_4362.html | ca5d20b6dcff89cfa2c86fc51f0ea33a24be58aa7d4ea1d3ec016561fb4c4a5e | 0 | 1 | c090aa2307af20fc176cb8cd6140c5137f5fa6f64a3ca0a32b132afe23ba8007 |
| detail_19270912.html | 7f3d206a0e9d59ed35d8c56e3c04c516f13050597d66ca0913b4b2a69e101a2d | 2 | 0 | 6c5ac2f3f52366acf312ef4a3ecd276c47b665ef493ca62394b0322a04489bb4 |
| detail_19206687.html | 1644b82de070c5c4cf7663ea354b3f849bbef4f34fa615e44aef4d3d4defb2af | 2 | 0 | 4004534ced25b5e7d43c657a2525ce3cb3a6414e7fdcb9fafcedd369b0451966 |
| detail_19238877.html | 2b06d12049dc36c47c8cb078540acd03e46a6110202ccc089d580a4949753898 | 2 | 0 | 17716d8a9168584bba2beadd7bbda1e2b68c0602d54f7f995c2fff51f17227a6 |
| detail_19091860.html | 634405660e02c2fae6211a405262ab339b5bcd4e13ff22a6b6cfa346c4e6d041 | 2 | 0 | 6aca5dbace64d8e1a2f3e9dce60276c12cda2f59ff4674c303dc527f6d2f4419 |
| detail_19344434.html | c063c467d83ea03b83a7c1a61c3b6a30c06e452f77226d5c99b97a7f62f993e0 | 2 | 0 | a7d4b1b118a4efc489457e9829ec223c98d2cc4086dcd73e66c5e06d00486a18 |
