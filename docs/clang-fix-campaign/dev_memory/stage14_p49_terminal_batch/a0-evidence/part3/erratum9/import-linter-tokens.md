# E9 C7e fixed-tree module slots

HEAD `43a6aa625f27da46daba190657bf62256080c68e`; tree `ca9331190e878af465e7968fe56e735585a5866e`.
仅 `.importlinter` 全部模块位;名字命中输入仅为 SCAN-06 的四处见证,不是全候选预检。

| 行:列(列0起) | 节 / 键 | token | 解析 | MODULE 消费边 |
|---|---|---|---|---|
| 7:4 | importlinter / root_packages | `tizen_ci_shared` | LOCAL:tizen_ci_shared | `.:tizen-ci-shared/scripts/tizen_ci_shared/__init__.py` |
| 8:4 | importlinter / root_packages | `tizen_convergence_judge` | LOCAL:tizen_convergence_judge | `.:tizen-convergence-judge/scripts/tizen_convergence_judge/__init__.py` |
| 9:4 | importlinter / root_packages | `tizen_qb_discover` | LOCAL:tizen_qb_discover | `.:tizen-qb-discover/scripts/tizen_qb_discover/__init__.py` |
| 10:4 | importlinter / root_packages | `tizen_gerrit_fetch` | LOCAL:tizen_gerrit_fetch | `.:tizen-gerrit-fetch/scripts/tizen_gerrit_fetch/__init__.py` |
| 11:4 | importlinter / root_packages | `tizen_build_verify` | LOCAL:tizen_build_verify | `.:tizen-build-verify/scripts/tizen_build_verify/__init__.py` |
| 12:4 | importlinter / root_packages | `tizen_gerrit_submit` | LOCAL:tizen_gerrit_submit | `.:tizen-gerrit-submit/scripts/tizen_gerrit_submit/__init__.py` |
| 13:4 | importlinter / root_packages | `tizen_triage_report` | LOCAL:tizen_triage_report | `.:tizen-triage-report/scripts/tizen_triage_report/__init__.py` |
| 14:4 | importlinter / root_packages | `gbs_patch_suggest` | LOCAL:gbs_patch_suggest | `.:tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/__init__.py` |
| 15:4 | importlinter / root_packages | `ci_triage` | LOCAL:ci_triage | `.:tizen-ci-triage/scripts/ci_triage/__init__.py` |
| 21:4 | importlinter:contract:root-layers / layers | `ci_triage` | LOCAL:ci_triage | `.:tizen-ci-triage/scripts/ci_triage/__init__.py` |
| 22:4 | importlinter:contract:root-layers / layers | `tizen_convergence_judge` | LOCAL:tizen_convergence_judge | `.:tizen-convergence-judge/scripts/tizen_convergence_judge/__init__.py` |
| 22:30 | importlinter:contract:root-layers / layers | `tizen_qb_discover` | LOCAL:tizen_qb_discover | `.:tizen-qb-discover/scripts/tizen_qb_discover/__init__.py` |
| 22:50 | importlinter:contract:root-layers / layers | `tizen_gerrit_fetch` | LOCAL:tizen_gerrit_fetch | `.:tizen-gerrit-fetch/scripts/tizen_gerrit_fetch/__init__.py` |
| 22:71 | importlinter:contract:root-layers / layers | `tizen_build_verify` | LOCAL:tizen_build_verify | `.:tizen-build-verify/scripts/tizen_build_verify/__init__.py` |
| 22:92 | importlinter:contract:root-layers / layers | `tizen_gerrit_submit` | LOCAL:tizen_gerrit_submit | `.:tizen-gerrit-submit/scripts/tizen_gerrit_submit/__init__.py` |
| 22:114 | importlinter:contract:root-layers / layers | `tizen_triage_report` | LOCAL:tizen_triage_report | `.:tizen-triage-report/scripts/tizen_triage_report/__init__.py` |
| 22:136 | importlinter:contract:root-layers / layers | `gbs_patch_suggest` | LOCAL:gbs_patch_suggest | `.:tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/__init__.py` |
| 23:4 | importlinter:contract:root-layers / layers | `tizen_ci_shared` | LOCAL:tizen_ci_shared | `.:tizen-ci-shared/scripts/tizen_ci_shared/__init__.py` |
| 25:4 | importlinter:contract:root-layers / ignore_imports | `tizen_build_verify.build_verify` | LOCAL:tizen_build_verify.build_verify | `.:tizen-build-verify/scripts/tizen_build_verify/build_verify.py` |
| 25:39 | importlinter:contract:root-layers / ignore_imports | `gbs_patch_suggest.formatter` | LOCAL:gbs_patch_suggest.formatter | `.:tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py` |
| 32:4 | importlinter:contract:skill-independence / modules | `tizen_convergence_judge` | LOCAL:tizen_convergence_judge | `.:tizen-convergence-judge/scripts/tizen_convergence_judge/__init__.py` |
| 33:4 | importlinter:contract:skill-independence / modules | `tizen_qb_discover` | LOCAL:tizen_qb_discover | `.:tizen-qb-discover/scripts/tizen_qb_discover/__init__.py` |
| 34:4 | importlinter:contract:skill-independence / modules | `tizen_gerrit_fetch` | LOCAL:tizen_gerrit_fetch | `.:tizen-gerrit-fetch/scripts/tizen_gerrit_fetch/__init__.py` |
| 35:4 | importlinter:contract:skill-independence / modules | `tizen_build_verify` | LOCAL:tizen_build_verify | `.:tizen-build-verify/scripts/tizen_build_verify/__init__.py` |
| 36:4 | importlinter:contract:skill-independence / modules | `tizen_gerrit_submit` | LOCAL:tizen_gerrit_submit | `.:tizen-gerrit-submit/scripts/tizen_gerrit_submit/__init__.py` |
| 37:4 | importlinter:contract:skill-independence / modules | `tizen_triage_report` | LOCAL:tizen_triage_report | `.:tizen-triage-report/scripts/tizen_triage_report/__init__.py` |
| 38:4 | importlinter:contract:skill-independence / modules | `gbs_patch_suggest` | LOCAL:gbs_patch_suggest | `.:tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/__init__.py` |
| 40:4 | importlinter:contract:skill-independence / ignore_imports | `tizen_build_verify.build_verify` | LOCAL:tizen_build_verify.build_verify | `.:tizen-build-verify/scripts/tizen_build_verify/build_verify.py` |
| 40:39 | importlinter:contract:skill-independence / ignore_imports | `gbs_patch_suggest.formatter` | LOCAL:gbs_patch_suggest.formatter | `.:tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py` |
| 47:4 | importlinter:contract:shared-layers / layers | `state` | LOCAL:tizen_ci_shared.state | `.:tizen-ci-shared/scripts/tizen_ci_shared/state/__init__.py` |
| 47:12 | importlinter:contract:shared-layers / layers | `workspace` | LOCAL:tizen_ci_shared.workspace | `.:tizen-ci-shared/scripts/tizen_ci_shared/workspace/__init__.py` |
| 47:24 | importlinter:contract:shared-layers / layers | `classify` | LOCAL:tizen_ci_shared.classify | `.:tizen-ci-shared/scripts/tizen_ci_shared/classify.py` |
| 48:4 | importlinter:contract:shared-layers / layers | `quickbuild_http` | LOCAL:tizen_ci_shared.quickbuild_http | `.:tizen-ci-shared/scripts/tizen_ci_shared/quickbuild_http.py` |
| 48:22 | importlinter:contract:shared-layers / layers | `env` | LOCAL:tizen_ci_shared.env | `.:tizen-ci-shared/scripts/tizen_ci_shared/env.py` |
| 49:4 | importlinter:contract:shared-layers / layers | `types` | LOCAL:tizen_ci_shared.types | `.:tizen-ci-shared/scripts/tizen_ci_shared/types.py` |
| 50:13 | importlinter:contract:shared-layers / containers | `tizen_ci_shared` | LOCAL:tizen_ci_shared | `.:tizen-ci-shared/scripts/tizen_ci_shared/__init__.py` |
| 55:17 | importlinter:contract:shared-no-uplink / source_modules | `tizen_ci_shared` | LOCAL:tizen_ci_shared | `.:tizen-ci-shared/scripts/tizen_ci_shared/__init__.py` |
| 56:20 | importlinter:contract:shared-no-uplink / forbidden_modules | `ci_triage` | LOCAL:ci_triage | `.:tizen-ci-triage/scripts/ci_triage/__init__.py` |
| 57:4 | importlinter:contract:shared-no-uplink / forbidden_modules | `tizen_convergence_judge` | LOCAL:tizen_convergence_judge | `.:tizen-convergence-judge/scripts/tizen_convergence_judge/__init__.py` |
| 58:4 | importlinter:contract:shared-no-uplink / forbidden_modules | `tizen_qb_discover` | LOCAL:tizen_qb_discover | `.:tizen-qb-discover/scripts/tizen_qb_discover/__init__.py` |
| 59:4 | importlinter:contract:shared-no-uplink / forbidden_modules | `tizen_gerrit_fetch` | LOCAL:tizen_gerrit_fetch | `.:tizen-gerrit-fetch/scripts/tizen_gerrit_fetch/__init__.py` |
| 60:4 | importlinter:contract:shared-no-uplink / forbidden_modules | `tizen_build_verify` | LOCAL:tizen_build_verify | `.:tizen-build-verify/scripts/tizen_build_verify/__init__.py` |
| 61:4 | importlinter:contract:shared-no-uplink / forbidden_modules | `tizen_gerrit_submit` | LOCAL:tizen_gerrit_submit | `.:tizen-gerrit-submit/scripts/tizen_gerrit_submit/__init__.py` |
| 62:4 | importlinter:contract:shared-no-uplink / forbidden_modules | `tizen_triage_report` | LOCAL:tizen_triage_report | `.:tizen-triage-report/scripts/tizen_triage_report/__init__.py` |
| 68:4 | importlinter:contract:shared-l1-independence / modules | `tizen_ci_shared.state` | LOCAL:tizen_ci_shared.state | `.:tizen-ci-shared/scripts/tizen_ci_shared/state/__init__.py` |
| 69:4 | importlinter:contract:shared-l1-independence / modules | `tizen_ci_shared.workspace` | LOCAL:tizen_ci_shared.workspace | `.:tizen-ci-shared/scripts/tizen_ci_shared/workspace/__init__.py` |
| 70:4 | importlinter:contract:shared-l1-independence / modules | `tizen_ci_shared.classify` | LOCAL:tizen_ci_shared.classify | `.:tizen-ci-shared/scripts/tizen_ci_shared/classify.py` |
| 76:4 | importlinter:contract:shared-l0-independence / modules | `tizen_ci_shared.quickbuild_http` | LOCAL:tizen_ci_shared.quickbuild_http | `.:tizen-ci-shared/scripts/tizen_ci_shared/quickbuild_http.py` |
| 77:4 | importlinter:contract:shared-l0-independence / modules | `tizen_ci_shared.env` | LOCAL:tizen_ci_shared.env | `.:tizen-ci-shared/scripts/tizen_ci_shared/env.py` |

## 注释 / name 排除记账

| 行 | 原文 | 去处 | 解释器行 |
|---|---|---|---|
| 1 | `# Static import gates do not see subprocess dependencies. In particular,` | CLASS9/COMMENT | false |
| 2 | `# tizen_build_verify.build_verify invokes ``python -m gbs_analyzer`` and also` | CLASS9/COMMENT | false |
| 3 | `# runs gbs, git, and cp -a. See` | CLASS9/COMMENT | false |
| 4 | `# docs/clang-fix-campaign/dev_memory/subprocess-boundaries.md.` | CLASS9/COMMENT | false |
| 18 | `name = application layers: orchestration -> skills -> shared` | CLASS9/CONTRACT_NAME | false |
| 29 | `name = extracted skills are independent` | CLASS9/CONTRACT_NAME | false |
| 44 | `name = shared internal layers: L1 -> L0 -> types` | CLASS9/CONTRACT_NAME | false |
| 53 | `name = shared must not import orchestration` | CLASS9/CONTRACT_NAME | false |
| 65 | `name = shared L1 domains are independent` | CLASS9/CONTRACT_NAME | false |
| 73 | `name = shared L0 primitives are independent` | CLASS9/CONTRACT_NAME | false |

## SCAN-06 见证闭合

| 行 | candidate | 名字形态 | 去处 | binding 边 |
|---|---|---|---|---|
| 8 | `tizen-convergence-judge/scripts/tizen_convergence_judge/__init__.py#REEXPORT#check_convergence` | DOTTED_MODULE | C7e | 无 |
| 22 | `tizen-convergence-judge/scripts/tizen_convergence_judge/__init__.py#REEXPORT#check_convergence` | DOTTED_MODULE | C7e | 无 |
| 32 | `tizen-convergence-judge/scripts/tizen_convergence_judge/__init__.py#REEXPORT#check_convergence` | DOTTED_MODULE | C7e | 无 |
| 57 | `tizen-convergence-judge/scripts/tizen_convergence_judge/__init__.py#REEXPORT#check_convergence` | DOTTED_MODULE | C7e | 无 |
