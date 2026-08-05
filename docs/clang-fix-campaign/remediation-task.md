# P4.5 补救与收尾总任务(REMEDIATION,顺序执行 RA→RB→RC→RD)

## 0. 协议与环境事实

协议不变:停止-报告(矛盾立案 change_41+)、实测验证不脑补(全部
断言贴命令+输出原文+sha256)、fail-closed、零修改名单不碰、禁止
直写 SQL(状态操作只走冻结公开 API)。

**环境事实(开发者提供)**:
- `tmp/gbs_llvm.conf`:GBS 编译配置文件(smoke 一律用它);
- `tmp/`:临时测试信息与数据目录,smoke 的 state.db/ws/日志全放
  `tmp/campaign-smoke/` 下,不碰生产状态;
- `tmp/Verification/log/`:开发者历史真实解过的 bug 错误日志;
- `tmp/Verification/codes/`:对应源码(**patch 已删除**,源码应处
  于故障态——这使它们成为真实修复用例:你需要自己写出修复);
- 开发者将另行下载:zlib(合成弧主力)、cynara(C++ 指纹验证)、
  libtpl-egl(备用)。

## RA. dev_memory 补档(R3,第一优先)

1. 建 `docs/clang-fix-campaign/dev_memory/`:
   - `INDEX.md`(全 stage 状态/commit/结论一览);
   - `stage01_design_convergence/`、`stage02_p0_gates/`、
     `stage03_m1_state_layer/`、`stage04_m2_reconcile/`、
     `stage05_m3_repair_step/`,每个含 `plan.md`(该 stage 目标与
     输入)/`progress.md`(过程与决策依据)/`result.md`(结论、
     commit、测试数、遗留 TODO);
2. 原始材料:`claude-review-ledger.md`(随本任务交付,先落盘到
   `docs/clang-fix-campaign/review/`)+ change_32–40 + design 台账 +
   commit message + p0-signature-audit;**冲突以机上落盘文档为准**,
   台账与文档不一致处不要调和,列入 result.md 的"记录差异"节;
3. 方法论账本 ①–⑦ 单列 `dev_memory/methodology.md`;
4. 打 checkpoint:`git tag checkpoint/p45_code_ready` 于当前 HEAD,
   在 `docs/clang-fix-campaign/checkpoints.md` 登记(tag/commit/
   覆盖范围/回退指令/回退后状态一句话);
5. 以上单独一个 commit:`docs(clang-fix-campaign): backfill R3 dev
   memory and checkpoint`。

## RB. 三方 review 包生成(第二优先,生成后交开发者分发)

在 `docs/clang-fix-campaign/review/three-way/` 生成两个自足包
(评审方拿到包即可审,不需要访问仓库):
1. **设计终版包** `design-v1.5.16-final-review.md`:冻结全文引用
   路径 + 版本史一页摘要 + "评审请求:对最终文本整体 PASS/列
   finding,重点 §3.4 契约表、§4.1 九步与分支表、§4.2 冻结 API";
2. **代码包** `code-review-package.md`:`git diff 85310ef..HEAD`
   全文(附 --stat)+ 契约→代码定位摘要 + DoD→测试函数映射表 +
   "评审请求:按 [BLOCKER]/[MAJOR]/[MINOR]/[NIT] 分级,重点
   事务边界/唯一性/崩溃恢复/append-only";
3. 包内注明:finding 回收后按 R14 闭环(BLOCKER 必修、MAJOR 修或
   开发者显式放行、MINOR 进 dev_memory 遗留 TODO);
4. 单独 commit。生成完毕即报告,**不等评审结果,继续 RC**(外部
   评审与 smoke 并行,合并主干前两者都须闭环)。

## RC. E2E smoke(真实环境验收,按已交付 runbook 执行,含本地化修订)

基础流程照 `e2e-smoke-runbook.md`(E0–E5),本地化修订如下:
1. **E0 修订**:GBS 配置一律 `tmp/gbs_llvm.conf`(记录其 sha256);
   smoke 目录 = `tmp/campaign-smoke/`;
2. **E1/E2(合成弧)**:用 zlib 走受控全弧(注错→R1 修一半→R2
   修好),断言按 runbook E2 逐条;
3. **E3(崩溃恢复)**:照 runbook,watcher + kill -9 打
   "PASS 已写、link 前"窗口,重入断言 relinked/不重复计费/不重复
   build;
4. **E4(边角三件)**:并发锁 / 预算终态 / HELD 可达,照 runbook;
5. **新增 E6(真实历史用例)**:遍历 `tmp/Verification/` 的每个
   case:
   a. 核对 codes 是否带 packaging(.spec 等),缺则列清单报告、
      跳过该 case,**不许自造 packaging 冒充**;
   b. 用 GBS 实际构建确认故障可复现,且报错与 log/ 中历史日志
      **同根因**(报错主体一致;行号/路径漂移可接受,写入报告);
      复现不了 → 记录环境漂移,跳过不硬怼;
   c. 以历史日志为 ci_evidence 种 unit(种子脚本只用冻结 API),
      baseline-reproduce 用**新鲜构建日志**——这里专门验证:
      `_primary_fingerprint` 对历史日志与新构建日志是否给出可
      比对的指纹(这是 Claude 押注最可能出偏差的点,任何不一致
      如实报,不调参迁就);
   d. **自行编写修复** edit_spec(patch 已删,这是真实修复练习),
      经 campaign-repair-step 走到 PASS;一轮修不好就多轮,预算内
      收敛;修不出来 → 记录为"人类难度用例",不硬怼;
   e. 每 case 独立小节入报告:根因/指纹比对/轮数/最终状态。
6. cynara 用例:在其一个 C++ 源里注一个模板/重载类错误走一遍
   R1-FAIL→6a,专验 C++ 报错的指纹稳定性;
7. 报告:`docs/clang-fix-campaign/review/e2e-smoke-report-v1.md`
   按 runbook E5 格式,含全部妥协项与偏差清单;偏差 = 停止报告的
   候选,不许静默吸收。

## RD. close-out 与收尾(RC 全绿或偏差被裁决后)

1. P4.5 close-out 报告(按权威 prompt P4:P2 自查表逐条打勾+代码
   定位、DoD→测试映射含反向验证双态输出、
   `git diff 85310ef..HEAD --stat` 证零修改名单未触碰、裁量记录);
2. dev_memory 各 stage result.md 补终态、INDEX 更新;
3. **提 PR**(标题 `[P4.5] clang-fix-campaign repair step`,描述含
   测试数/覆盖/关联 design 章节/已知风险),然后**停止,等开发者
   人工 review**——三方 review finding 闭环 + smoke 全绿 + PR 人工
   放行,三者齐备才允许 merge,merge 由你执行。

## 完成定义

RA/RB 两个 commit 落盘 → RC 报告(含 E6 每 case 小节)→ RD PR
挂起等人工。任何一步现实与设计冲突:停在那里,立案 change_41+。
