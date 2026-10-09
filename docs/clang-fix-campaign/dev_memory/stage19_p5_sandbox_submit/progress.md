# Stage19 P5 sandbox-submit

日期:2026-10-09。状态:**C1_VALIDATED**,C0已推送且远端CI成功;C1本地门禁无新增失败,待推送后远端CI核验。

## 1. 权威、批准与基线

- FatTank已批准P5 v1.2冻结,本轮按用户授权实施C0-C5。
- 输入文件:`docs/clang-fix-campaign/p5-sandbox-submit-design-v1.2.md`。
- 输入SHA256:`e7103cefbf279fb21d7b6fd10218be1653ca791192d95f11f400b01a8f54e420`,实测一致。
- 冻结文件:`docs/clang-fix-campaign/p5-sandbox-submit-design-v1.2-FROZEN.md`。
- 仅改标题后的SHA256:`120bb6fa86b9e475df576c174059769caeda02493edb552face29f73a7c15ca7`。
- P5-C0-01六处引用裁定后的SHA256:`2f800aa4b391af3f53949cf5cc9db5af743e15f97475be68f67958f7c9d2a4de`。
- 两次改动分别为标题冻结、附录A六处外部章节记号;反向还原分别与前一版本hash相等。
- `git fetch origin clang-fix-campaign` exit 0后,HEAD与origin/clang-fix-campaign
  均为`cd7f8ddac8c05af0eaa99714ef171668d905f983`。
- 不访问真实Gerrit,不做真实sandbox推送。未来测试仅使用本地仓库和本地裸仓库。
- C0未修改生产代码、测试或检查器。C1仅实施§5四项加固,见§7;C2-C5未开展。

## 2. 计划与进度

| 提交 | 范围 | 状态 |
|---|---|---|
| C0 | 文件名与标题冻结;附录A照录同步design.md v1.5.20;检查器与通用门禁 | `38c076f`;本地94命令无新增失败;远端CI SUCCESS |
| C1 | §5四项加固与§6.4,真实hook本机passed | 本地1527 passed/1 skipped;94命令无新增失败;本提交外部锚定,远端CI待推送 |
| C2 | suppress_policy、CLI、§6.1 | NOT_STARTED |
| C3 | gate_view、latest_policy_for_round、lookup_change_id、§6.2 | NOT_STARTED |
| C4 | 共用unit hash/src_clean、Git安全环境、sandbox_submit、CLI、§6.3 | NOT_STARTED |
| C5 | READY_FOR_REVIEW收口、规则与用例双向表、已知限制、真实hook原文 | NOT_STARTED |

每个提交均须通过§6.5,相对cd7f8dd无新增设计门禁失败,独立推送并核验远端CI。
三条既有checker遗留不伪称已修;本次新增失败不能算作历史遗留。

## 3. C0已完成的文档工作与证据

- design.md附录A.1新增§4.4,逐字照录,包括原有`v1.x`路径字面。
- A.2仅插入指引行/新增错误码,不改旧签名或旧契约正文;头尾版本同步为v1.5.20。
- 新建本进度文件并登记INDEX。工作树已有.gitignore修改和四份docs删除保持原样,
  其它untracked历史稿不纳入本批。

SHA命令与实际输出(exit 0):

```text
$ sha256sum docs/clang-fix-campaign/p5-sandbox-submit-design-v1.2.md
e7103cefbf279fb21d7b6fd10218be1653ca791192d95f11f400b01a8f54e420  docs/clang-fix-campaign/p5-sandbox-submit-design-v1.2.md
$ sha256sum docs/clang-fix-campaign/p5-sandbox-submit-design-v1.2-FROZEN.md
120bb6fa86b9e475df576c174059769caeda02493edb552face29f73a7c15ca7  docs/clang-fix-campaign/p5-sandbox-submit-design-v1.2-FROZEN.md
```

标题与A.1照录断言实跑(exit 0):从冻结稿提取A.1的Markdown引用块,仅去掉
引用前缀,断言完整块出现在design.md;恢复标题字面后断言输入hash。

```text
title_only_change=PASS
appendix_A1_verbatim=PASS
```

首次C0检查命令及实际输出(exit 1,裁定前历史记录):

```text
$ .venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md
== check_design_doc: docs/clang-fix-campaign/design.md ==
[CK-XREF-01][DEADLINK] §0.1 无对应章节
-- 1 problem(s) --
```

基线复核:读取`git show HEAD:docs/clang-fix-campaign/design.md`,调用相同
checker.check,传相同权威prompt且`require_python_fence=True`。实际输出(exit 0):

```text
baseline=cd7f8dd
-- OK: 0 problem --
```

首次在C0检查失败即停止,当时未跑其余门禁或推送;裁定后复跑见§6。

## 4. 停止报告与人工裁决前提

### P5-C0-01 CLOSED:跨文档章节引用与既有检查器不兼容

- 原文位置:P5冻结稿:911、923-927。A.2要求照录两行“P5设计文件§0.1”,
  且C0检查器零问题方可继续。
- 落盘位置:`design.md:2834`与`:3071`。此处引用的是P5文档的§0.1,
  不是design.md自身的章节。
- 工具位置:`tools/check_design_doc.py:408-412`。它枚举全文所有§数字引用,
  只与当前文档标题比较,没有外部文档引用解析;相同§0.1被集合去重为一个错误。
- 影响:按A.2照录后C0门禁无法达到零问题,相对cd7f8dd为新增失败。
  未自行改写附录、添加假章节或豁免该检查。
- 候选1:由设计方批准将这两处外部引用改为明确的Markdown文件锚链接,
  替代裸§0.1引用,保留含义;这是对“照录”要求的具名例外。
- 候选2:授权检查器识别明确的外部文档引用并校验目标文件/章节,缺文件或
  缺章节仍红,补正反控制;不采用对§0.1的无条件放行。
- 在裁决前保留中间态,不提交C0,不进入任何生产实现。
- 现按§6设计方裁定关闭,不修改检查器。

## 5. 挂账

- P5-C0-01已关闭,当前未闭合停止报告条目数0。
- P4移交的两项加固已由C1实现并实跑;P2移交的已有DERIVE删缓存拒绝推送
  仍待C4,不把计划登记记作完成。

## 6. P5-C0-01设计方裁定与落实

### 裁定原文

> P5-C0-01 裁定(设计方,轻量流程,不出勘误,记入 stage19 progress):
> 原因:附录 A 中指向 P5 设计文件章节的引用使用了"§",与 design.md 内部章节引用的记号冲突。
>
> 1. 在冻结稿 p5-sandbox-submit-design-v1.2-FROZEN.md 的附录 A 中,把以下 6 处"P5 设计文件 §x"统一改为"P5 设计文件第 x 节"(只删"§"并加"第…节",其余文字不变):
>    - A.1 第 13 条:"P5 设计文件 §4.2" → "P5 设计文件第 4.2 节"
>    - A.1 第 14 条:"P5 设计文件 §4.4" → "P5 设计文件第 4.4 节"
>    - A.2 §3.7 行:"P5 设计文件 §2" → "P5 设计文件第 2 节"
>    - A.2 §4.1 sandbox-submit 行:"P5 设计文件 §4" → "P5 设计文件第 4 节"
>    - A.2 §7 Phase 4.5 行与 §7 Phase 5 行:"P5 设计文件 §0.1" → "P5 设计文件第 0.1 节"
>    指向 design.md 自身的"§4.4 第 N 条"等引用不改。
> 2. design.md 中照录的对应 6 处同样修改,使其与冻结稿逐字一致。
> 3. progress 记录:裁定原文、冻结稿改前(120bb6fa…)与改后的 sha256、6 处位置清单。检查器不改。
> 4. 重跑设计文档检查器须 0 problem;另用 grep 确认 design.md 中已无"设计文件 §"字样。之后按原计划完成 C0 并继续 C1。

### 位置与实测

| 条目 | 冻结稿行 | design.md行 | 新引用 |
|---|---|---|---|
| A.1第13条 | 899 | 2685 | P5 设计文件第 4.2 节 |
| A.1第14条 | 902 | 2688 | P5 设计文件第 4.4 节 |
| A.2 §3.7 | 917 | 1152 | P5 设计文件第 2 节 |
| A.2 sandbox-submit | 918 | 1174 | P5 设计文件第 4 节 |
| A.2 Phase 4.5 | 923 | 2834 | P5 设计文件第 0.1 节 |
| A.2 Phase 5 | 924 | 3071 | P5 设计文件第 0.1 节 |

改前hash为`120bb6fa86b9e475df576c174059769caeda02493edb552face29f73a7c15ca7`,
改后hash为`2f800aa4b391af3f53949cf5cc9db5af743e15f97475be68f67958f7c9d2a4de`。
反向恢复这六处替换后hash与改前一致,其它冻结稿字节未动;A.1引用块去掉
Markdown引用前缀后与design.md新增§4.4完整逐字匹配。

```text
ruling_replacements=6; other_frozen_changes=0; appendix_A1_verbatim=PASS
exit=0
$ .venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md
== check_design_doc: docs/clang-fix-campaign/design.md ==
-- OK: 0 problem --
exit=0
$ grep -n '设计文件 §' docs/clang-fix-campaign/design.md
(空输出)
exit=1 (无匹配)
```

### 通用门禁

基线干净工作树`/tmp/p5-baseline-cd7f8dd`,C0干净验证树`/tmp/p5-c0-cd7f8dd`。
复用stage16的`evidence/review-minors/run_validation.py`,运行全仓pytest(逐用例JUnit)、
mypy、ruff、lint-imports及已登记90条设计checker/控制,总计94条。
输出与环境逐项保存在本stage `evidence/baseline/`和`evidence/C0/`。
不运行真实Gerrit或QuickBuild业务请求。

运行命令(两次均exit 0):

```bash
.venv/bin/python docs/clang-fix-campaign/dev_memory/stage16_p2_submission_identity/evidence/review-minors/run_validation.py /tmp/p5-baseline-cd7f8dd docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/baseline
.venv/bin/python docs/clang-fix-campaign/dev_memory/stage16_p2_submission_identity/evidence/review-minors/run_validation.py /tmp/p5-c0-cd7f8dd docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/C0
```

两树实测均为`1496 passed, 1 skipped`,新增测试0。四项exit全部0,
90条设计门禁/控制的exit逐条相等。原始结果摘要:

```text
pytest: exit=0 expected=0
mypy: exit=0 expected=0
ruff: exit=0 expected=0
lint-imports: exit=0 expected=0
design-doc: exit=0 expected=0
completed=94 unexpected=3
```

unexpected三条与基线一致:design-doc-controls=1、
symbol-negative-duplicate-spec-root-mismatch=0、symbol-key-twin-both-binary-key=1。
其余负控制按预期exit 1,不是回归失败。
`evidence/C0-comparison.json`逐nodeid比较:exit_changes={}、missing_nodeids=[]、
changed_outcomes=[]、added_nodeids=[];同时钉定实际受验两份设计文档hash。
设计Python签名代码未改变,无需变更签名夹具;checker、生产和测试diff均为空。
远端CI在提交推送后核验,其run以GitHub外部锚定,回报并在下一提交记入。

## 7. C1四项加固与§6.4实测

C0远端核验命令与输出(exit 0):

```text
$ gh run view 37899082560 --json status,conclusion,url,headSha
{"conclusion":"success","headSha":"38c076fa0c1da4b18a83b66bb258fd59c28f7bc3","status":"completed","url":"https://github.com/lhmax2010/LogAnalysisSkill/actions/runs/37899082560"}
```

C1变更边界为三个生产模块与四个测试文件,无其它API扩展,冻结稿与design.md
不变。实现细节:共享日期校验函数留在已有依赖方向的derive_commit模块;
首次写入的DERIVE字段集合提为campaign_state内部常量,供后续gate_view复用。
这些放置选择不增加行为或安全规则。

| 设计规则 | 实现 | 验收用例(相对tests/) |
|---|---|---|
| §5日期加固/§6.4① | `COMMIT_DATE_RE`加re.ASCII;统一`validate_commit_date`先正则再fromisoformat;Z在解析时转换+00:00;derive/state共用 | `unit/test_derive_commit.py::test_non_ascii_or_impossible_dates_refuse_before_git_and_payload`(两个字段各四反例);`test_real_dates_with_timezone_can_derive`(Z/+08:00) |
| §5真实hook/§6.4② | hash不符pytest.fail;缺配置/文件仍skip | `integration/test_derive_commit_real_hook.py::test_real_hook_digest_mismatch_is_failure`;`test_missing_real_hook_inputs_remain_skip`;`test_registered_real_hook_then_derive`本机PASSED |
| §5目录fsync/§6.4③ | 新建/预存/竞争三成功路径校验hash后fsync父目录;link与目录fsync失败为WORKSPACE_FS_UNSUPPORTED、exit 5 | `unit/test_campaign_repair_step.py::test_edit_spec_all_success_paths_fsync_parent`;`test_conflicting_edit_spec_never_fsyncs_parent`;`test_edit_spec_filesystem_failure_is_uncounted_and_retryable`(canonical/build两份×EPERM/EXDEV/ENOTSUP/fsync四故障) |
| §5身份不可变/§6.4④ | 首次写入不可变集合加入committer_identity,其余四项保持 | `unit/test_campaign_change_ids.py::test_all_derive_identity_fields_are_immutable`(五字段独立负例,拒绝后仍一条DERIVE) |

目录故障用例断言:失败两次均没有BUILD_INVOCATION、builder零调用;canonical
失败没有round,build副本失败保留既有round但不计构建;清除故障可重试PASS;
成功后三份原字节相同、临时文件无残留。既有publication-failure用例原来
预期OSError,按本次明文新契约改断言为WORKSPACE_FS_UNSUPPORTED/exit 5,
nodeid不变,未删除用例。

开发中新增immutable测试曾误把latest_event的事件信封当payload,导致五个
新增用例失败;改为读取`original["payload"]`后通过。未修改生产API迁就测试,
与设计冲突无关。定向复跑命令及实际输出(exit 0):

```text
$ .venv/bin/python -m pytest tests/unit/test_derive_commit.py tests/unit/test_campaign_change_ids.py tests/unit/test_campaign_repair_step.py tests/integration/test_derive_commit_real_hook.py -q
148 passed in 5.28s
```

干净验证树`/tmp/p5-c1-38c076f`基于C0,只应用本次七份源码/测试diff。
命令、环境、exit与原始输出在`evidence/C1/commands.json`及各同名log;
`evidence/C1/pytest.xml`记录逐nodeid结果。实跑命令(exit 0):

```bash
.venv/bin/python docs/clang-fix-campaign/dev_memory/stage16_p2_submission_identity/evidence/review-minors/run_validation.py /tmp/p5-c1-38c076f docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/C1
```

实际输出摘录:

```text
======================= 1527 passed, 1 skipped in 35.08s =======================
Success: no issues found in 106 source files
All checks passed!
Contracts: 6 kept, 0 broken.
pytest: exit=0 expected=0
mypy: exit=0 expected=0
ruff: exit=0 expected=0
lint-imports: exit=0 expected=0
completed=94 unexpected=3
```

相对cd7f8dd的三条既有设计门禁异常与§6完全一致,没有新增失败。比较命令
与输出(exit 0;结构化结果在`evidence/C1-comparison.json`):

```text
$ .venv/bin/python docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/compare_validation.py docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/C1 /tmp/p5-c1-38c076f
{
  "baseline_commit": "cd7f8dd",
  "command_count": 94,
  "exit_changes": {},
  "baseline_tests": {
    "passed": 1496,
    "skipped": 1
  },
  "current_tests": {
    "passed": 1527,
    "skipped": 1
  },
  "missing_nodeids": [],
  "changed_outcomes": {}
}
added_nodeids=31; identical_tested_sources=7
baseline_comparison=PASS
```

比较器只比较已保存结果,不重设任何期望;七文件主树/验证树逐字相等并记录
hash。新增31个用例均passed,原1497个nodeid无缺失/状态改变。
真实hook配置沿用P2,本机文件与P2登记sha256一致,没有访问Gerrit:

```text
$ sha256sum /home/linhao/gerrit-hook/commit-msg
3c7e9b5fbe0b7ed945abd74248913c912ee0464abb416c18278bc5811dbb6f50  /home/linhao/gerrit-hook/commit-msg
$ rg -n 'test_registered_real_hook_then_derive' docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/C1/pytest.log
72:tests/integration/test_derive_commit_real_hook.py::test_registered_real_hook_then_derive PASSED [  4%]
```

两命令exit 0。远端CI仍按提交后的外部run核验,不能以本地结果替代;
远端缺hook时skip不充当真实hook通过证据,上面的本机PASSED才是该项验收。
