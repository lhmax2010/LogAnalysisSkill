# Stage19 P5 sandbox-submit

日期:2026-10-10。状态:**REVIEW_FIXES_IN_PROGRESS**。C0-C5已推送;本轮按v1.3.1修订,见§18。未自行标CLOSED。

## 1. 权威、批准与基线

- FatTank已批准P5 v1.2冻结,本轮按用户授权实施C0-C5。
- 输入文件:`docs/clang-fix-campaign/p5-sandbox-submit-design-v1.2.md`。
- 输入SHA256:`e7103cefbf279fb21d7b6fd10218be1653ca791192d95f11f400b01a8f54e420`,实测一致。
- 冻结文件:`docs/clang-fix-campaign/p5-sandbox-submit-design-v1.2-FROZEN.md`。
- 仅改标题后的SHA256:`120bb6fa86b9e475df576c174059769caeda02493edb552face29f73a7c15ca7`。
- P5-C0-01六处引用裁定后的SHA256:`2f800aa4b391af3f53949cf5cc9db5af743e15f97475be68f67958f7c9d2a4de`。
- P5-C2-01一处用例期望裁定后的SHA256:`81dca7748666ba61198316f1cda5812d1202f088b6b53e3cb1bf7cf11f6b55ec`。
- P5-C2-02输出形状裁定后的SHA256:`a6177cbd2426dec2d42404277bd68b63f758d8b6d78fab827fa9b49259b91f3e`。
- 两次改动分别为标题冻结、附录A六处外部章节记号;反向还原分别与前一版本hash相等。
- `git fetch origin clang-fix-campaign` exit 0后,HEAD与origin/clang-fix-campaign
  均为`cd7f8ddac8c05af0eaa99714ef171668d905f983`。
- 不访问真实Gerrit,不做真实sandbox推送。未来测试仅使用本地仓库和本地裸仓库。
- C0未修改生产代码、测试或检查器。C1实施§5四项加固,见§7;C2见§11/12;C3见§13;C4见§15/16,C5随后进行。

## 2. 计划与进度

| 提交 | 范围 | 状态 |
|---|---|---|
| C0 | 文件名与标题冻结;附录A照录同步design.md v1.5.20;检查器与通用门禁 | `38c076f`;本地94命令无新增失败;远端CI SUCCESS |
| C1 | §5四项加固与§6.4,真实hook本机passed | `8c89de4`;本地1527 passed/1 skipped;94命令无新增失败;远端CI SUCCESS(§8) |
| C2 | suppress_policy、CLI、§6.1 | `1f3141e`;定向174 passed;全量1701 passed/1 skipped;94命令无新增失败;远端CI SUCCESS |
| C3 | gate_view、latest_policy_for_round、lookup_change_id、§6.2 | `68338dc`;定向23 passed;全量1724 passed/1 skipped;94命令无新增失败;远端CI SUCCESS |
| C4 | 共用unit hash/src_clean、Git安全环境、sandbox_submit、CLI、§6.3 | `33fcf68`;新增121例,1845 passed/1 skipped;94命令无新增失败;远端CI SUCCESS |
| C5 | READY_FOR_REVIEW收口、规则与用例双向表、已知限制、真实hook原文 | 本提交外部锚定;状态READY_FOR_REVIEW,最终门禁见§17 |

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

- P5-C0-01、P5-C2-01与P5-C2-02已关闭,当前未闭合停止报告条目数0。
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

## 8. P5-C2-01停止报告:CLOSED,计数公式与allowed用例冲突

本节为C1推送后开工核对记录,等待设计方裁定,暂不提交C2。冻结稿未改,
C2实现、测试均未创建。

- 权威位置:`p5-sandbox-submit-design-v1.2-FROZEN.md:234`以
  `(kind, token, scope)`为键;`:243`要求非全局减少总数大于全局增加数时
  `werror_removed → forbidden`。
- 冲突位置:同文件`:722`(§6.1第5项)要求“从target A移到全局、同时删掉
  target B的,allowed”。两处无法在同一组输入同时满足,不是实现细节。
- 最小输入:同一CMakeLists.txt,以单个非空的全文件edit替换如下两行,
  避免额外触发pure_deletion:

```cmake
target_compile_options(A PRIVATE -Werror)
target_compile_options(B PRIVATE -Werror)
```

替换为:

```cmake
add_compile_options(-Werror)
```

按冻结公式代入的命令与实际输出(exit 0;只作规则算术核验,不是新增evaluate):

```bash
.venv/bin/python - <<'PY'
from collections import Counter
before = Counter({('werror', '-Werror', 'target_private'): 2})
after = Counter({('werror', '-Werror', 'global_or_ambiguous'): 1})
token = '-Werror'
global_key = ('werror', token, 'global_or_ambiguous')
removed = sum(max(count - after[key], 0) for key, count in before.items()
              if key[1] == token and key[2] != 'global_or_ambiguous')
increase = max(after[global_key] - before[global_key], 0)
forbidden = after[global_key] < before[global_key] or removed > increase
print(f'non_global_decrease={removed}; global_increase={increase}')
print(f'section_2_6={"forbidden" if forbidden else "allowed"}; section_6_1_5=allowed')
assert forbidden
print('CONTRACT_CONFLICT=CONFIRMED (rule arithmetic only, not evaluate implementation)')
PY
```

```text
non_global_decrease=2; global_increase=1
section_2_6=forbidden; section_6_1_5=allowed
CONTRACT_CONFLICT=CONFIRMED (rule arithmetic only, not evaluate implementation)
```

候选处置(均须设计方决定,本轮未选):

1. 保留§2.6数量判据,将§6.1该例期望改为forbidden;实现严格按现公式。
2. 保留该例allowed,由设计方明确修订§2.6抵消公式/例外及其边界与反例。
   这会改变放行范围,不能由实现方把“一个全局实例”自行当作可无限抵消。

C1远端CI实跑命令与输出(exit 0):

```text
$ gh run view 37899857536 --json status,conclusion,url,headSha
{"conclusion":"success","headSha":"8c89de44adcd87e80876f736b6534166010bafb5","status":"completed","url":"https://github.com/lhmax2010/LogAnalysisSkill/actions/runs/37899857536"}
```

本节停止报告与C1远端结果保留在工作树,未提交C2或额外改动冻结稿;
待裁定后随下一次获准提交登记。C0与C1代码、测试和本地证据均已推送。

## 9. P5-C2-01裁定与单行落实

上节为裁定前记录。现按以下设计方原文关闭P5-C2-01,只修正指定的用例子句,
不改§2.6公式,不改“减1加1allowed”用例。冻结稿、progress、INDEX按要求
保留至C2一起提交,本次未单独提交。

> P5-C2-01 裁定(设计方,轻量流程,不出勘误,记入 stage19 progress):
> §2.6 的 werror_removed 公式保持不变;§6.1 第 5 条中"从 target A 移到全局、同时删掉 target B 的,allowed"属设计用例写错,改为 forbidden。
> 理由:add_compile_options 只对其后定义的 target 生效,"全局覆盖全部 target"的前提不成立;非全局减少 2、全局增加 1 时按公式判 forbidden 是正确的从严结果。"单 target 移到同文件全局(减 1 加 1)allowed"一例不变。
>
> 1. 冻结稿 p5-sandbox-submit-design-v1.2-FROZEN.md 第 722 行附近,把该子句改为:"从 target A 移到全局、同时删掉 target B 的,forbidden(非全局减少 2 大于全局增加 1)";其余文字不变。progress 记录裁定原文、冻结稿改前(2f800aa4…)与改后的 sha256。
> 2. 该文件变更与 progress、INDEX 一并随 C2 提交,不单独提交。
> 3. 按冻结稿继续实施 C2,完成后照原格式回报;后续 C3–C5 照原计划进行。

改前SHA256:`2f800aa4b391af3f53949cf5cc9db5af743e15f97475be68f67958f7c9d2a4de`。
改后SHA256:`81dca7748666ba61198316f1cda5812d1202f088b6b53e3cb1bf7cf11f6b55ec`。
机械断言确认:HEAD正文仅该子句出现一次,对它进行一次替换后的全部字节与
工作树正文相等。命令与输出见§10,未改其它字节。

## 10. P5-C2-02停止报告:CLOSED,纯删除hit缺少合法kind

### 原文位置与冲突

- 冻结稿`:74`(§2.1)明确`PolicyHit.kind`取“2.4的kind枚举”;`:77`限定
  `rule`为`forbidden | suppress`,不能用rule字段临时承载另一形态名。
- `:167-177`(§2.4)列出的kind没有`pure_deletion`,也没有一般删除/其它形态。
- `:246`(§2.6)要求每个new去空白为空的edit判`pure_deletion`、forbidden;
  `:268`要求其hit的edit_index为该edit下标;`:727`要求正反验收。
- 删除普通`int unused;`的edit可通过既有guard,却没有选项/pragma/target
  实例可作为kind。不能假称pragma_unparsed、无法省略hit,也不能自行扩展
  冻结的输出枚举。此缺口影响evaluate/CLI/POLICY中可观察的hit结构。

### 真实输入与文档枚举核验

以下实跑仅用临时本地git仓库和既有guard,没有新增C2实现、没有远端业务请求。
命令(exit 0):

```bash
.venv/bin/python - <<'PY'
import hashlib
import re
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from tizen_build_verify.edit_spec_guard import validate_edit_spec
path = 'docs/clang-fix-campaign/p5-sandbox-submit-design-v1.2-FROZEN.md'
before = subprocess.check_output(['git', 'show', 'HEAD:' + path])
after = Path(path).read_bytes()
old = '从 target A 移到全局、同时删掉 target B 的,allowed'
new = '从 target A 移到全局、同时删掉 target B 的,forbidden(非全局减少 2 大于全局增加 1)'
assert before.count(old.encode()) == 1
assert before.replace(old.encode(), new.encode()) == after
print('ruling_replacements=1; other_frozen_changes=0')
print('before_sha256=' + hashlib.sha256(before).hexdigest())
print('after_sha256=' + hashlib.sha256(after).hexdigest())
body = after.decode()
section = body.split('### 2.4 ', 1)[1].split('### 2.5 ', 1)[0]
kinds = re.findall(r'^\| `([^`]+)` \|', section, re.M)
with TemporaryDirectory(prefix='p5-c2-schema-') as directory:
    root = Path(directory)
    subprocess.run(['git', 'init', '-q', directory], check=True)
    (root / 'unit.c').write_text('int unused;\n')
    spec = {'schema_version': 'gbs_patch_suggest/edit-spec/v1', 'patch_name': 'remove-unused',
            'edits': [{'file': 'unit.c', 'old': 'int unused;\n', 'new': ''}]}
    validate_edit_spec(spec, str(root))
    print('pure_deletion_input=VALID (existing edit_spec_guard)')
print('section_2_4_kinds=' + ','.join(kinds))
print('pure_deletion_in_kind_enum=' + str('pure_deletion' in kinds))
PY
```

实际输出:

```text
ruling_replacements=1; other_frozen_changes=0
before_sha256=2f800aa4b391af3f53949cf5cc9db5af743e15f97475be68f67958f7c9d2a4de
after_sha256=81dca7748666ba61198316f1cda5812d1202f088b6b53e3cb1bf7cf11f6b55ec
pure_deletion_input=VALID (existing edit_spec_guard)
section_2_4_kinds=wno_flag,wno_error_flag,wno_error_all,wno_wholesale,w_all_off,werror,pragma_suppress,pragma_wholesale,pragma_unparsed,pragma_pop,target_decl
pure_deletion_in_kind_enum=False
```

### 候选处置(未实施)

1. 最小补正:批准增加结构性kind=`pure_deletion`,明确其token=None、
   scope=`n/a`、count=1、rule=`forbidden`、edit_index为原edit下标。
   移除类hit沿用被移除实例的kind(`werror`/`pragma_pop`/`target_decl`),
   另请明确是否同意此映射,避免同类命名歧义。
2. 统一输出分类:批准将三个移除规则名及`pure_deletion`作为独立hit kind,
   同时修正§2.1的枚举引用及§2.4表,明确各字段映射。此方案触及面更大。

未自行选择方案。当前只改冻结稿获准的一行与progress/INDEX;未创建生产模块
或测试,未运行全仓回归/远端CI,没有新的提交或推送。C2-C5等待本项裁定后续行。

## 11. P5-C2-02裁定与落实

§10为裁定前记录,现由下述裁定关闭,随C2提交,不单独提交文档。

> P5-C2-02 裁定(设计方,轻量流程,不出勘误,只补 hit 的输出形状,判定结果不变,记入 stage19 progress):
> §2.1 PolicyHit.kind 的取值 = §2.4 的 kind 枚举 + 以下 4 个规则名。移除类 hit 的 kind 用规则名,不沿用被移除实例的 kind(§6.1 第 4、5 条的用例以规则名书写)。各字段固定如下:
>
> 1. pure_deletion:token=None;scope="n/a";count=1;rule="forbidden";edit_index=该 edit 下标;file=该 edit 的文件。
> 2. werror_removed:每个文件、每个 werror token(-Werror 或某个 -Werror=<name>)至多一条。
>    token=该 werror token;scope="n/a";rule="forbidden"。
>    count 计算:记 g = 编辑后全局实例数 - 编辑前全局实例数,n = 编辑前非全局实例数 - 编辑后非全局实例数,
>    count = max(0, -g) + max(0, n - max(g, 0))。count 必为正,因为只有 g<0 或 n>g 时才命中。
> 3. pragma_pop_removed:每个文件至多一条。
>    token="pop";scope="n/a";rule="forbidden";count = pop 的减少数 - 全部 pragma_suppress 键减少数之和。
> 4. target_removed:每个文件、每个 target_decl 键一条。
>    token="<命令名小写> <名称值>"(与 §2.1 注释一致);scope="n/a";rule="forbidden";count=该键的减少数。
> 5. 移除类 hit 的 edit_index 按 §2.7 的旧区间规则确定。
> 6. 冻结稿 §2.1 中 PolicyHit.kind 的注释改为"2.4 的 kind 枚举,或移除类规则名 werror_removed / pragma_pop_removed / target_removed / pure_deletion(字段取值见 progress P5-C2-02)";其余文字不变。progress 记录改前(81dca774…)与改后的 sha256。
> 7. §6.1 增加断言:上述 4 类 hit 的 kind、token、scope、count 逐字段符合本裁定,其中 werror_removed 的 count 至少覆盖 g<0、n>g≥0 两种情形。
> 8. 文档变更随 C2 一并提交。继续实施 C2,完成后照原格式回报。

改前:`81dca7748666ba61198316f1cda5812d1202f088b6b53e3cb1bf7cf11f6b55ec`。
改后:`a6177cbd2426dec2d42404277bd68b63f758d8b6d78fab827fa9b49259b91f3e`。
只改kind注释与§6.1新增第11项字段断言;此前C2-01单行修正保留。

```text
$ sha256sum docs/clang-fix-campaign/p5-sandbox-submit-design-v1.2-FROZEN.md
a6177cbd2426dec2d42404277bd68b63f758d8b6d78fab827fa9b49259b91f3e  docs/clang-fix-campaign/p5-sandbox-submit-design-v1.2-FROZEN.md
exit=0
```

## 12. C2实现与验证

- 新增`ci_triage/suppress_policy.py`,只读、无state DB或网络调用;先复用既有
  guard校验,再按同一定位规则在内存中产生整文件after,不落盘。
- CLI只增加`suppress-policy check`分发;原有子命令行为不变。
- 实现细节登记(不改变判定或安全边界):直接复用guard私有定位/路径函数,
  不复制一套定位规则;CLI成功/forbidden的stdout严格为asdict结果,
  `REJECTED_SUPPRESS_POLICY`诊断放stderr,不向冻结的stdout形状添加字段;
  参数或输入错误为exit 2与INVALID_ARGS JSON。
- 审计机械同步:首次symbol_audit exit 1,仅四个`undeclared consumer
  ci_triage.suppress_policy`:EditSpecViolation、validate_edit_spec、
  _validate_target_path、_locate_edit。将该真实消费方加入四项SPECS,
  owner/definition/判据不变,guard生产文件零改动。

§6.1用例映射(文件统一为`tests/unit/test_suppress_policy.py`):

| 条文 | 测试函数(参数化覆盖见源码) |
|---|---|
| 1 token边界 | test_token_boundaries |
| 2 每kind、pragma及near-miss | test_option_kinds; test_pragma_kinds; test_source_near_misses |
| 3 作用域、文件类别、注释 | test_cmake_scopes; test_cmake_comments; test_automake_assignment; test_file_category_precedence; test_quoted_cmake_continuation_and_unchanged_targets |
| 4 整文件退化守卫 | test_whole_file_migration_and_activation; test_scope_keyword_only_edit_uses_entire_command_span; test_fragment_replacement_and_adjacent_edits; test_same_scope_reorder_and_unchanged_suppression |
| 5 移除/纯删除、跨文件不抵消 | test_werror_removed_count_and_fixed_fields; test_no_cross_file_offset_for_werror_or_targets; test_target_removed_fixed_fields; test_pop_removal_fixed_fields_and_suppression_removal_offset; test_pure_deletion_fixed_fields |
| 6 原样保留 | test_same_scope_reorder_and_unchanged_suppression; test_option_kinds |
| 7 来源与判定优先级 | test_source_kind_strategy_precedence |
| 8 输入错误 | test_policy_input_errors |
| 9 CLI stdout/退出码 | test_cli_stdout_exactly_matches_evaluate; test_cli_subprocess_exit_codes; test_cli_invalid_input_has_exit_two |
| 10 确定性/区间映射 | test_determinism_reordering_length_changes_and_no_mutation; test_new_span_mapping_continuations_line_anchor_and_doc_mixture; test_sort_order_and_minimal_touching_edit |
| 11/C2-02四类hit字段 | test_werror_removed_count_and_fixed_fields; test_werror_removed_once_per_token_with_both_count_terms; test_target_removed_fixed_fields; test_pop_removal_fixed_fields_and_suppression_removal_offset; test_pure_deletion_fixed_fields; test_multiple_removals_use_declared_output_shape; test_removed_instance_old_interval_not_new_interval |

定向实跑命令与原始尾部(exit 0):

```text
$ .venv/bin/python -m pytest tests/unit/test_suppress_policy.py -q
169 passed in 1.03s
$ .venv/bin/ruff check tizen-ci-triage/scripts/ci_triage/suppress_policy.py tizen-ci-triage/scripts/ci_triage/cli.py tests/unit/test_suppress_policy.py docs/clang-fix-campaign/tools/symbol_audit.py
All checks passed!
$ .venv/bin/mypy tizen-ci-triage/scripts/ci_triage
Success: no issues found in 15 source files
```

上面的169例为首轮定向记录。最终自检按§2.5限定三类作用域选项,
整类选项的scope用n/a;automake非空prefix不额外限定为字母数字。
补5例回归,没有修改冻结稿或判据。最终定向实跑:

```text
$ .venv/bin/python -m pytest tests/unit/test_suppress_policy.py -q
174 passed in 1.15s
exit=0
```

§6.5最终验收在干净工作树`/tmp/p5-c2-final-8c89de4`完成。基于C1,
应用本次暂存补丁;生产/测试文件哈希与待提交版本一致。全部命令、环境、
exit、输出hash见[evidence/C2/commands.json](evidence/C2/commands.json),
原文为同目录每项`.log`,逐用例结果为`pytest.xml`。

```text
$ .venv/bin/python docs/clang-fix-campaign/dev_memory/stage16_p2_submission_identity/evidence/review-minors/run_validation.py /tmp/p5-c2-final-8c89de4 docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/C2
pytest: exit=0 expected=0
mypy: exit=0 expected=0
ruff: exit=0 expected=0
lint-imports: exit=0 expected=0
symbol: exit=0 expected=0
bridge: exit=0 expected=0
design-doc: exit=0 expected=0
completed=94 unexpected=3
exit=0

======================= 1701 passed, 1 skipped in 35.91s =======================
Success: no issues found in 107 source files
All checks passed!
Contracts: 6 kept, 0 broken.
```

`unexpected=3`均为固定基线已登记的三项(design-doc-controls、
symbol-negative-duplicate-spec-root-mismatch、symbol-key-twin-both-binary-key),
不是新增失败;未放宽期望值。机械比较命令与输出:

```text
$ .venv/bin/python docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/compare_validation.py docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/C2 /tmp/p5-c2-final-8c89de4
{
  "baseline_commit": "cd7f8dd",
  "command_count": 94,
  "exit_changes": {},
  "baseline_tests": {
    "passed": 1496,
    "skipped": 1
  },
  "current_tests": {
    "passed": 1701,
    "skipped": 1
  },
  "missing_nodeids": [],
  "changed_outcomes": {}
}
added_nodeids=205; identical_tested_sources=3
baseline_comparison=PASS
exit=0
```

另按`C1/pytest.xml`与`C2/pytest.xml`中的(classname,name)及结果逐项比较,
断言旧集合包含于新集合、旧结果不变、所有新增为passed。实际输出(exit 0):
`C1_retained=1528 missing=0 outcome_changes=0 C2_added=174`。
本轮无待裁决问题,未访问真实Gerrit。远端CI结果随后续进度记录补锚,
不能以本地验收代称远端已通过。

C2推送后远端核验原文:

```text
$ gh run view 37907289971 --json headSha,status,conclusion,url
{"conclusion":"success","headSha":"1f3141ea43255afa34f2dc8118e92405998e189c","status":"completed","url":"https://github.com/lhmax2010/LogAnalysisSkill/actions/runs/37907289971"}
exit=0
```

## 13. C3只读门禁视图

- 新增GateView、gate_view、latest_policy_for_round、lookup_change_id。
- 实现细节:新接口以SQLite只读URI连接已有state DB,不执行schema初始化或生成
  Change-Id;gate_view显式BEGIN,所有unit/event/QB查询在同一连接、同一事务。
  无事件的reproduce_by_arch用空mapping,其余可空payload为None。
- 抽出原latest_qb_result的SQL与行转换为连接级内部原语,公共API行为不变;
  DERIVE读取侧使用C1同一不可变字段集合,没有另立枚举。
- §6.2映射(测试文件`tests/unit/test_campaign_gate_view.py`):
  1 reproduced六组合与最新primary覆盖;2各事件event_id排序/PUSH分ref_class;
  3 QB两级最新不回退;4五字段独立冲突与写入侧committer拒绝;
  5第二连接在查询原语间写入且快照不变;6空unit/不存在unit;
  7按round筛POLICY、缓存命中/未命中只读。

```text
$ .venv/bin/python -m pytest tests/unit/test_campaign_gate_view.py -q
23 passed in 0.46s
exit=0
$ .venv/bin/ruff check tizen-ci-triage/scripts/ci_triage/campaign_state.py tests/unit/test_campaign_gate_view.py
All checks passed!
exit=0
$ .venv/bin/mypy tizen-ci-triage/scripts/ci_triage
Success: no issues found in 15 source files
exit=0
```

全量证据:[evidence/C3/commands.json](evidence/C3/commands.json)(命令、环境、exit、
原输出hash)、同目录原始log及pytest.xml。代码测试与干净工作树字节相同。

```text
$ .venv/bin/python docs/clang-fix-campaign/dev_memory/stage16_p2_submission_identity/evidence/review-minors/run_validation.py /tmp/p5-c3-1f3141e docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/C3
pytest: exit=0 expected=0
mypy: exit=0 expected=0
ruff: exit=0 expected=0
lint-imports: exit=0 expected=0
symbol: exit=0 expected=0
bridge: exit=0 expected=0
design-doc: exit=0 expected=0
completed=94 unexpected=3
exit=0
======================= 1724 passed, 1 skipped in 36.77s =======================

$ .venv/bin/python docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/compare_validation.py docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/C3 /tmp/p5-c3-1f3141e
{
  "baseline_commit": "cd7f8dd",
  "command_count": 94,
  "exit_changes": {},
  "baseline_tests": {
    "passed": 1496,
    "skipped": 1
  },
  "current_tests": {
    "passed": 1724,
    "skipped": 1
  },
  "missing_nodeids": [],
  "changed_outcomes": {}
}
added_nodeids=228; identical_tested_sources=2
baseline_comparison=PASS
exit=0
```

三项历史门禁问题与C2及固定基线相同,未修改期望值。C3新增23例,既有API测试
保留;远端CI于本提交推送后核验,回报结果不冒充提交前已取得。

## 14. P5-C4-01停止报告:配置安全检查命中自身覆盖

**状态:CLOSED,设计方P5-C4-01裁定见§15。** 以下保留停止时的事实。C3实现与验收已完成;
C4只做冻结后真实输入的规格可满足性检验,未改生产代码、未改冻结稿、未豁免任何键。

### 原文位置与冲突

权威文件`p5-sandbox-submit-design-v1.2-FROZEN.md`:

- `:584`与`:595-603`要求每次git调用(包含config)均带全部`-c`覆盖,
  其中含`core.fsmonitor=false`、`core.askPass=`、`credential.helper=`。
- `:607-613`要求`git config --get-regexp`出现禁用键即拒绝,名单恰含上面三键,
  没有排除命令注入的配置来源。
- 真实git会把命令行`-c`配置一同输出;全新仓库也必命中,正常路径不能通过。
  若实现自行跳过这三键,又会漏掉仓库内真正的危险配置,不能自行放行。

### 实测(无网络,仅临时本地git仓库)

可复现脚本完整记录环境、八个覆盖与键模式:
[evidence/C4-config-preflight.py](evidence/C4-config-preflight.py)。
对照只移除命令行覆盖,使用同一个仓库和同一环境。

```text
$ .venv/bin/python docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/C4-config-preflight.py
fresh_local_repository=True
git_config_with_section_4_4_overrides: exit=0
stdout='core.fsmonitor false\ncore.askpass \ncredential.helper \n'
stderr=''
same_repository_without_command_overrides: exit=1
stdout=''
exit=0

$ .venv/bin/ruff check docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/C4-config-preflight.py
All checks passed!
exit=0
```

脚本exit 0表示复现实验完成,不是配置门禁绿;设计要求下前三行必导致拒绝。

### 候选处置(均未实施)

1. 配置查询加来源/作用域输出,机械排除本工具注入的command-scope安全覆盖;
   对仓库自身(含include/worktree配置)的同名键仍拒绝。须由设计明确精确过滤规则,
   并补“干净仓库通过/仓库同名键即使值与覆盖相同仍拒绝/不可借来源隐藏”的控制。
2. 只读配置枚举命令不带这三条重叠覆盖,其余命令仍全带;须设计方明确批准该例外,
   并验证配置枚举本身不执行危险配置对应的程序。

未自行选择,未开始C4/C5。C2-01/02裁定继续有效,没有以本问题改回任何判定。

## 15. P5-C4-01裁定与实施

设计方轻量裁定(不出勘误),原文:

1. 配置安全检查改为执行 git config --show-scope --get-regexp <键模式>(仍带 §4.4 的统一环境与 -c 覆盖)。只统计 scope 不是 "command" 的条目:命令行 -c 注入的覆盖不计,local、worktree 及经 include 引入的条目照常判定。名单与"无命中返回 1 视为通过"的规则不变。
2. 运行前检查 git 版本,低于 2.26(不支持 --show-scope)时 fail-closed:exit 4 REJECTED_UNSAFE_GIT_CONFIG,reason 注明 git 版本过低。
3. 冻结稿 §4.4"配置安全检查"一段,在"执行 git config --get-regexp <键模式>"处改为"执行 git config --show-scope --get-regexp <键模式>,只统计来源不是命令行(scope=command)的条目;git 低于 2.26 时按不通过处理";其余文字不变。progress 记录改前与改后的 sha256。
4. §6.3 补用例:全新仓库在带全部 -c 覆盖时通过检查;仓库本地设置 core.fsmonitor 或 credential.helper 时仍被拒;经 include.path 引入、含 core.sshCommand 的文件被拒;用包装把 git 版本模拟为 2.25 时被拒。
5. 另记一项供收口评审:suppress_policy 引用了 tizen_build_verify.edit_spec_guard 的私有函数 _validate_target_path 与 _locate_edit,并在 symbol_audit 中登记。C5 收口文档的"已知事项"中单独列出,写明引用原因与可选替代(提为公开接口或在本模块内实现同一定位规则),本轮不改。
6. 文档变更随 C4 一并提交。继续实施 C4,完成后照原格式回报;之后进行 C5。

冻结稿改前SHA256:`a6177cbd2426dec2d42404277bd68b63f758d8b6d78fab827fa9b49259b91f3e`。
改后SHA256:`432f0e62b1f836622012559c3c35e3cd57021423786d18da337d096c0d2de95b`。
修改范围:§4.4查询句、§6.3第27项配置来源用例。无其它设计改动。

C3远端CI:commit `68338dc6c631bd3954f53939a38d11b4993b9e33`,
[run 37907980980](https://github.com/lhmax2010/LogAnalysisSkill/actions/runs/37907980980),SUCCESS。
C5须登记私有接口已知事项,本轮保留C2的调用关系和审计登记。

## 16. C4实现与验证记录

### 实现细节(不改行为或安全边界)

- 共用私有模块`ci_triage/_campaign_workspace.py`:从repair-step移入五个定义,
  `_StepError`、`_unit_hash`、`_validate_source_identity`、`_git_stdout`、
  `_normalize_project`;旧调用点直接导入。`test_repair_primitives_moved_without_source_changes`
  对`68338dc`旧源与新模块逐定义AST source segment逐字比较,不是仅比较AST语义。
- gate_view与round policy查询抽出连接级内部原语;原公共API仍保持原连接/事务行为。
  TOCTOU通过同一只读连接的StateDatabase适配器再次调用aggregate_verifications,
  不另开快照。SubmitSnapshot增加git配置和已经解析的edit_spec作为运行载荷,
  不增加状态库字段或重新读取未绑定内容。
- Git配置查询使用`--null --name-only`承载scope/key成对结果;不读取/回显配置值,
  其余P5-C4-01判定不变。真实Git实跑确认NUL交替scope/key形态,多行值反例、
  worktree作用域与include均有测试。无命中返回1、版本不足/查询失败朝闭拒绝。
- 按既定消费关系补`symbol_audit`中is_protected的`ci_triage.sandbox_submit`
  declared consumer;无owner、判据或期望值变更。单靠新增调用未同步时审计实报
  `MISMATCH: undeclared consumer ci_triage.sandbox_submit`,已按实测补登记。
- §6.3第21项同名远端夹具使用本地仓库中的`remote.ssh://unused.example/project.url`
  配置,目标仍为本地裸仓库,在枚举拒绝前不会建立SSH连接。绝对路径作为remote名
  被Git警告并忽略,不能用来构造该拒绝分支。两形式独立复现实验:
  [C4-remote-name-preflight.py](evidence/C4-remote-name-preflight.py),exit 0;
  absolute: listed_same_name=false; ssh: listed_same_name=true。无需修改设计。
- 真实不可写远端用本地裸仓库objects目录去掉写权限验证,恢复权限后重跑;
  timeout、TOCTOU与崩溃窗口才使用相应桩。只访问本地Git,未触及真实Gerrit。
- 开发过程中3个夹具外键构造失败已改为显式带外SQL,子模块夹具补检出对应提交,
  一个测试的Path导入缺失已补齐。未修改生产契约或既有断言来消除失败。

### 定向与覆盖

测试文件`tests/unit/test_sandbox_submit.py`、`tests/unit/test_sandbox_git.py`。
§6.3逐项规则与测试对应关系在C5收口表登记。覆盖正常/幂等/补账、缓存丢失、
参数/选定/四锁、聚合/重绑定/policy、副本现场与src、TOCTOU同快照、A12、
hook、推送失败恢复、隐式路径、九个崩溃窗口、环境隔离、HELD锁内落库、
全部action逐字段快照、P5-C4-01及共用化等价。

首轮干净工作树回归(配置值NUL封装及两条附加控制之前):
`1843 passed, 1 skipped`;94条命令仅三项历史期望不符,与cd7f8dd相同。
保留原始输出于[evidence/C4-initial/commands.json](evidence/C4-initial/commands.json)。
最终版本须以[evidence/C4/commands.json](evidence/C4/commands.json)及后续比较为准,
不以首轮结果代替最后改动后的全量实测。

### C4最终门禁

完整命令、环境、exit与原始输出hash:
[evidence/C4/commands.json](evidence/C4/commands.json)。源码/测试与干净工作树
逐字节一致,比较输出含8个改动文件hash。

```text
$ .venv/bin/python -m pytest tests/unit/test_sandbox_submit.py tests/unit/test_sandbox_git.py -q
121 passed in 19.01s
exit=0
$ .venv/bin/python docs/clang-fix-campaign/dev_memory/stage16_p2_submission_identity/evidence/review-minors/run_validation.py /tmp/p5-c4-68338dc docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/C4
pytest: exit=0 expected=0
mypy: exit=0 expected=0
ruff: exit=0 expected=0
lint-imports: exit=0 expected=0
symbol: exit=0 expected=0
bridge: exit=0 expected=0
design-doc: exit=0 expected=0
completed=94 unexpected=3
exit=0
======================= 1845 passed, 1 skipped in 57.28s =======================

$ .venv/bin/python docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/compare_validation.py docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/C4 /tmp/p5-c4-68338dc
{
  "baseline_commit": "cd7f8dd",
  "command_count": 94,
  "exit_changes": {},
  "baseline_tests": {"passed": 1496, "skipped": 1},
  "current_tests": {"passed": 1845, "skipped": 1},
  "missing_nodeids": [],
  "changed_outcomes": {}
}
added_nodeids=349; identical_tested_sources=8
baseline_comparison=PASS
exit=0

C3_retained=1725 missing=0 outcome_changes=0 C4_added=121
exit=0
SUMMARY | 198 SYMBOL OK | 4 MODULE-SCOPE OK (48 SYMBOLS COVERED) | 0 MISMATCH | 0 INCOMPLETE
SUMMARY | 198 SYMBOL OK | 4 MODULE-SCOPE OK | 0 MISSING_FROM_INVENTORY | 0 MISSING_FROM_BODY | 0 OWNER_MISMATCH | 0 PARSE_ERROR
```

逐nodeid证据为C3/C4各自`pytest.xml`,集合比较未删除、未改旧用例结果。
三条历史期望不符仍为design-doc-controls、symbol-negative-duplicate-spec-root-mismatch、
symbol-key-twin-both-binary-key;基线exit分别1/0/1,当前相同,不重设期望。
真实hook原文(`C4/pytest.log:72`):

```text
tests/integration/test_derive_commit_real_hook.py::test_registered_real_hook_then_derive PASSED [  3%]
```

本轮停止报告条目数0;P5-C4-01已闭合。远端CI不以本地结果冒充,推送后另补锚。

C4推送与远端核验原文:

```text
$ git push origin clang-fix-campaign
68338dc..33fcf68  clang-fix-campaign -> clang-fix-campaign
exit=0
$ gh run view 37912146491 --json headSha,status,conclusion,url
{"conclusion":"success","headSha":"33fcf68241b4ada6fcfd8b03df8d026ef14d82a8","status":"completed","url":"https://github.com/lhmax2010/LogAnalysisSkill/actions/runs/37912146491"}
exit=0
```

## 17. C5收口

[p5-sandbox-submit-closeout.md](../../review/p5-sandbox-submit-closeout.md)
状态READY_FOR_REVIEW,含§6.1/6.2/6.3/6.4规则与真实用例名映射、§2.5/2.8
已知限制、P5-C4-01私有接口事项、真实hook PASSED原文与各阶段证据。
原有3项checker遗留未改。本次无新行为/安全边界裁决请求;§16非语义实现细节
已逐项登记。C5只改文档与证据,无生产/测试代码变化。

映射检查使用ast枚举四文件(test_suppress_policy/test_campaign_gate_view/
test_sandbox_submit/test_sandbox_git)的test函数,与收口表中的反引号用例名集合
相减;再对tests/所有测试函数检查表内名字存在性。命令实跑输出:

```text
new_module_test_functions=83 missing_from_mapping=[] unknown_test_names=[]
exit=0
```

最终独立复跑(完整原文见[evidence/C5/commands.json](evidence/C5/commands.json)
及同目录log,比较见[evidence/C5-comparison.json](evidence/C5-comparison.json)):

```text
$ .venv/bin/python docs/clang-fix-campaign/dev_memory/stage16_p2_submission_identity/evidence/review-minors/run_validation.py /tmp/p5-c5-33fcf68 docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/C5
pytest: exit=0 expected=0
mypy: exit=0 expected=0
ruff: exit=0 expected=0
lint-imports: exit=0 expected=0
symbol: exit=0 expected=0
bridge: exit=0 expected=0
design-doc: exit=0 expected=0
completed=94 unexpected=3
exit=0
======================= 1845 passed, 1 skipped in 57.36s =======================

$ .venv/bin/python docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/compare_validation.py docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/C5 /tmp/p5-c5-33fcf68
exit_changes={}; missing_nodeids=[]; changed_outcomes={}
added_nodeids=349; identical_tested_sources=0
baseline_comparison=PASS
exit=0
C4_to_C5 nodeids=1846 added=0 missing=0 outcome_changes=0
exit=0

tests/integration/test_derive_commit_real_hook.py::test_registered_real_hook_then_derive PASSED [  3%]
```

C5新增测试0;真实hook本机passed,不是skip。C0-C4远端均SUCCESS,
C5推送后的远端结果由交付回报外部锚定,不在尚未产生的本提交中预填成功。
状态保持READY_FOR_REVIEW,等待设计方核验/评审,不自行CLOSED。

## 18. 代码评审修订

2026-10-10:Claude Code、ChatGPT代码评审结论均为需修改。FatTank提供
`p5-sandbox-submit-design-v1.3.1.md`,取代v1.2冻结稿;v1.3草稿保持不动、不入库。
上一轮因v1.3.1文件未到位停止,本轮实测文件已到位,批准SHA完全一致:

```text
$ sha256sum docs/clang-fix-campaign/p5-sandbox-submit-design-v1.3.1.md
f027f8b4057d4d617f9265968765f01940ce1396e588a65b28e95326e89258e6  docs/clang-fix-campaign/p5-sandbox-submit-design-v1.3.1.md
exit=0
```

文档原字节不改;附录A.3四条与错误码照录至design.md v1.5.21。
修复前HEAD=72a5806,全量1845 passed/1 skipped;门禁对照基线仍为cd7f8dd。
提交顺序:文档同步 → 代码与测试 → READY_FOR_REVIEW收口,逐个推送。

| 附录D事项 | 对应契约 | 落实状态 |
|---|---|---|
| 数字分隔符与游离单引号 | §2.3、§6.1.13 | 待实现与变异验证 |
| BOM、二合字母、垂直空白pragma | §2.3/2.4、§6.1.13 | 待实现 |
| CMake值解码/列表/括号参数 | §2.3、§6.1.12 | 待实现与旧逻辑变异验证 |
| 生成器表达式整体/递归/闭集 | v1.3.1补充、§2.3 | 待实现 |
| 真实文件归组分类/alias_overlap | §2.2、§6.1.14 | 待实现 |
| 隔离传输与git版本无关对象库路径 | §4.4、§6.3.28 | 待实现 |
| CLI意外异常统一出口 | §4.1、§6.3.30 | 待实现 |
| TOCTOU路径/架构变异守卫 | §6.3.29 | 待实现与变异验证 |
| 读事务仅1/2/3/6、PolicyInputError归因 | §4.3第12步 | 待实现 |
| 定位跨模块等价/已知限制/规则v2 | §2.8、§6.1.15/16 | 待实现与收口登记 |

测试仅使用本地Git与裸仓库;不访问真实Gerrit。所有变异在隔离工作树做,
保存失败原文后恢复,不拿错误实现作为交付。

文档同步验证:

```text
$ .venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md
== check_design_doc: docs/clang-fix-campaign/design.md ==
-- OK: 0 problem --
exit=0
```

首次调用漏传路径得到usage/exit 2,补齐显式路径后如上通过,未改检查器。
