# SKEL-B2-02: 本地克隆的 origin 与现有身份校验不兼容

状态:STOPPED,等待设计方裁定。基线:5b9ecea。日期:2026-11-03。
本报告不修改冻结稿,不实施候选方案,不放宽身份校验。

## 1. 互相冲突的要求

- 骨架冻结稿5.1第4步(第162行起):远端为
  `gerrit_ssh_base.rstrip('/') + '/' + project`;canonical已存在时
  **只用现有**`_validate_source_identity`,不覆盖、不修补。
- 同节第168行允许`gerrit_ssh_base`为绝对本地路径供测试;第6节要求本地裸仓库
  首次克隆与各崩溃点重跑成功。本轮任务也明确要求离线测试使用本地裸仓库。
- 当前`tizen-campaign-core/scripts/tizen_campaign_core/_campaign_workspace.py:47`
  要求`_normalize_project(origin) == unit.project`;第89-100行对本地路径只去掉
  首尾斜杠、可选的`git/`前缀和`.git`后缀,不会去掉本机remote根目录。
- 因此克隆`/tmp/<root>/remotes/platform/upstream/libtirpc`后,归一化结果为
  `tmp/<root>/remotes/platform/upstream/libtirpc`,不等于
  `platform/upstream/libtirpc`。即使首次发布另写核验,下一次建档重跑或
  baseline-reproduce/repair-step/sandbox-submit复用现有校验时仍会被拒。

## 2. 离线实测

命令(仓库根目录):

```sh
env PYTHONPATH=tizen-campaign-core/scripts:tizen-ci-shared/scripts .venv/bin/python docs/clang-fix-campaign/dev_memory/stage21_campaign_skeleton/evidence/batch2/probe-local-origin.py.txt
```

探针只用临时目录,通过真实git init、clone --bare、clone、checkout构造本地输入,
通过生产create_unit/get_unit创建并读取临时unit,写恰好三个键的marker,
直接调用生产`_validate_source_identity`。不使用生产状态库,不启动任何浏览器。
`GIT_ALLOW_PROTOCOL=file`,系统/全局Git配置禁用;没有任何网络访问或push。

| 核对项 | 实测 |
|---|---|
| 本地裸仓库clone与checkout | 成功 |
| HEAD == unit.base_commit | true |
| marker恰为unit_key/project/base_commit且值一致 | true |
| 本地origin原样保留时调用既有校验 | `_StepError`,exit 4,`REJECTED_IDENTITY_MISMATCH` |
| 错误原因 | `source HEAD or origin does not match campaign unit` |
| 对照:仅改临时仓库origin为ssh://example.invalid/platform/upstream/libtirpc | 校验通过,未连接该URL |
| 对照后 | 恢复临时origin,临时目录连同临时DB已清理 |

完整argv、结果、origin原文、归一化结果、UTC起止:
[probe-local-origin.json](probe-local-origin.json)。探针exit 0表示成功复现规格冲突,
**不是**campaign-add-unit验收通过;该命令尚未实现。
临时SSH origin只用于定位原因,不是实施方案或测试绕过。

现有测试为何未暴露:tests/unit/test_sandbox_submit.py:47手工设origin为
`ssh://unused.example/project`,同时第142-155行另配本地裸仓库用于传输。
它没有覆盖按同一绝对本地配置克隆出来的origin原文。

## 3. 候选处置(未实施)

建议设计方明确授权扩展共享身份校验的**本地远端分支**:

```diff
- canonical已存在时只用现有_validate_source_identity校验。
+ canonical已存在时用共享_validate_source_identity校验。保留HEAD与三键marker检查。
+ gerrit_ssh_base为绝对本地路径时,按受信配置中的base与unit.project构造预期远端,
+ 比较origin与该预期远端的规范化绝对路径;不以project后缀匹配或任意去前缀放行。
+ 现有SSH/网络远端分支保持原语义。调用方一致传入配置所确定的预期远端。
```

这是候选文字,尚需设计方确定本地路径、符号链接与file://的具体接受范围;
本轮不自行选择语义。副作用:共享校验API及intake/baseline/repair/sandbox
调用点需同步,触及身份判断边界,不能当作纯测试夹具机械调整。无需改安全核心。

所需验收至少包括:本地clone首建/同参数重跑/崩溃恢复;后续基线、修复、沙箱
身份检查一致;错误local base、同后缀但不同目录、错误origin/HEAD/marker拒绝;
原SSH项目归一化正负例不变;设计方明确的路径规范化边界分别有正负例。

不采用未授权替代:改unit.project为绝对路径、在正式建档里伪造SSH origin、
测试mock掉身份检查、只按路径后缀比较、改冻结稿。

## 4. 本轮停止范围

只登记SKEL-B2-01与本停止报告并运行上述离线探针。
生产代码、既有测试、CLI解析、放弃屏障、SKILL和新业务模块均未改。
sandbox-submit/qb-trigger屏障diff均0行;本批业务用例和CLI对照测试未实施。
全仓pytest、计时清单重跑、安全四组、mypy/ruff/import-linter未运行;
不得沿用第1批结果宣称第2批通过。设计检查器与完整性核对另见
`checks.json`。第3批未开始。
