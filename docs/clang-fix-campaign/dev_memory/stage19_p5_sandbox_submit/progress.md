# Stage19 P5 sandbox-submit

日期:2026-10-09。状态:**C0_VALIDATED**,P5-C0-01已关闭,本地门禁通过,待本提交推送后远端CI核验。

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
- 本轮未修改生产代码、测试或检查器。未开展C1-C5。

## 2. 计划与进度

| 提交 | 范围 | 状态 |
|---|---|---|
| C0 | 文件名与标题冻结;附录A照录同步design.md v1.5.20;检查器与通用门禁 | 本地94命令无新增失败;本提交外部锚定,远端CI待推送 |
| C1 | §5四项加固与§6.4,真实hook本机passed | NOT_STARTED |
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
- P2移交的已有DERIVE删缓存拒绝推送以及P4两项加固均待后续对应提交,
  不把计划登记记作完成。

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
