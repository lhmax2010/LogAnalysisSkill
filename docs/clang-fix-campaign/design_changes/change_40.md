# change_40:CK-API-01 解析层修正(→ v1.5.16-FROZEN)【v2】

**v2 修订(Codex 第三次停止-报告,两处硬冲突全采)**:①prompt ⑤
的 SHA 断言仍指 change_39 旧值(照文执行必立即失败)——改为指向
"编号最大的含落盘校验值的 change";②P0-2 权威顺序仍写"冲突以
change_39 为准"(会把 compile 裁决翻回 ast.parse)——改为"以编号
最大的相关 change 为准,当前 = change_40";③未来编号升 change_41+;
④SHA 已按修订后 prompt 重算并更新 B.4(本文件旧值作废)。
**结构性修正**:prompt 不再钉死具体 change 编号,统一指向裁决链头
——本元环三次同型失误(P0-2 口径、版本标签、SHA/优先级)的共同
根因是"固定指针指向移动目标",链头引用使 change_41+ 出现时 prompt
无需回改。

**触发**:Codex P0 停止-报告(协议 2 第二次正常触发,工作树保留
中间态、零擅自判定)。
**性质**:仅改 checker 规则的解析原语与其在 design.md §7.13 7g /
权威 prompt P0-2 的表述;**零运行时契约变更**。应用后 design.md
升 **v1.5.16-FROZEN**。

---

## A. 矛盾实锤与裁决

**矛盾**:change_39 要求 CK-API-01 用 `ast.parse` **且**重复形参
fixture 必须 FAIL。实测(Codex 报告 + 本轮独立复现):

```
ast.parse("def f(a, a): ...")                       → 通过
compile("def f(a, a): ...", "<x>", "exec")          → SyntaxError: duplicate argument 'a'
compile("def adopt(..., *, convergence_payload, arch_norm,
         convergence_payload): ...", "<b4>", "exec") → SyntaxError: duplicate argument 'convergence_payload'
```

重复形参检测发生在编译符号表阶段、不在语法树阶段——**CK-API-01
按 change_39 原文抓不住自己的立规事故(B4)**,change_39 中"B4 的
重复形参必须被裸解析抓住"系事实错误(裁决方笔误,记账)。

**裁决(采 Codex 推荐项)**:CK-API-01 的解析原语改为
`compile(block, "<design.md:块定位>", "exec")`:
- compile **只编译不执行、不解析名字**——skeleton 无 import、
  装饰器/注解名未定义均不报错(本轮探针以含 dataclass / PEP604 /
  `tuple[...,...]` / kw-only / `...` 体的代表性块验证通过);
- compile 语法阶段**包含**解析,故 ast.parse 的全部检出被子集覆盖;
- **不采备选项**(ast.parse + 显式遍历查重复形参):自写遍历规则
  复杂、易漂移,且 compile 已由解释器保证语义。
裸签名起始行扫描、CK-IDX/XREF/MMD 各规则不变。

## B. 应用步骤(接续 Codex 当前工作树)

1. design.md:§7.13 7g 行的 "ast.parse" 表述改为
   "compile(...,'exec')";版本行升 **v1.5.16-FROZEN**、状态行追加
   change_40;已完成的 §4.2 skeleton 转换、change_31 回写**保留**;
2. checker:CK-API-01 按 compile 原语实现;fixture ①(重复形参)
   与 B4 精确形态 fixture 必须 FAIL——**本条即⑦的首次执行**
   (见 D);
3. 权威 prompt:P0-2 的 CK-API 表述同步(修订件已随本 change
   交付),设计版本引用升 v1.5.16;
4. **落盘断言值更新(supersede change_39 附记 SHA)**:目标机
   `p45-implementation-prompt-v1_5_15.md` sha256 必须等于
   `e214d1fb8b806e1ebc12e6e8cfafc57d71cbffcf0340d94c26396ef87816a3fb`
   (change_39 附记旧值 `22d217a2...2432c5` 作废);
5. 生成 `history/clang-fix-campaign-design-v1.5.16-FROZEN.md` 快照
   并 `cmp` 断言(v1.5.15 快照若已生成则一并保留为历史);
6. 其余 P0 项(prompt 归档、Ruff、自测)按 change_39 继续。

## C. 验收

compile 对 §4.2 全部围栏块通过 + 两个重复形参 fixture(通用 +
B4 精确形态)FAIL + 裸签名扫描归零 + 其余 change_39 验收项不变 +
prompt SHA 新值一致。

## D. 方法论记账

**⑦立规事故必须在规则冻结前被规则实测复现**:⑥要求规则试跑,
但 change_39 的试跑只覆盖了两条**新写的**正则,没有覆盖**继承的**
核心断言(ast.parse 能抓重复形参)——选择性试跑等于没试跑。自本
change 起:每条 guard 类规则的 change 文档必须附"立规事故 fixture
在该规则下 FAIL"的实测输出,缺失即退回;规则抓不住自己的立规
事故 = 该规则不存在。
