# SCAN-06:非入口配置中的候选名字无形态承接

状态:OPEN。E8-6 Python 全树预检已零阻塞;这是恢复第1块后发现的另一条停止项,
不是 SCAN-05 重报,不是 OBS claim 判红。未自行扩展消费者表或排除集合。

## 冻结输入

- HEAD: `43a6aa625f27da46daba190657bf62256080c68e`。
- tree: `ca9331190e878af465e7968fe56e735585a5866e`。
- 权威: `p49-terminal-batch-design-v1.31-FROZEN.md`,SHA-256
  `66b33ef6c365c3da835529756d60ee43626768a0d361eb47dbeea86177f6db3c`。
- 实跑: `scan06.command.json` / `scan06.log`,exit 1;原始事实 `scan06-witness.json`。
  该命令是单见证规范可满足性检查,不是全树名字兜底完成声明。

## 原文与事实

| 原文位置(当前批准字节) | 要求 | 机械见证 |
|---|---|---|
| §1.1c L1015 | 粒度②覆盖任一模块的 re-export binding,含 `__all__` | `tizen-convergence-judge/scripts/tizen_convergence_judge/__init__.py:3` 从实现模块导入 `check_convergence`,且 `__all__` 显式含它 |
| §1.1 L359–363 | 每个 candidate 生成模块名;binding 再加限定名字;全部文本文件词边界搜索 | 候选 `.../__init__.py#REEXPORT#check_convergence` 的模块名为 `tizen_convergence_judge` |
| E4-2 L2193 | `.importlinter` 明确属于 OTHER_TEXT,须跑名字兜底 | lstat/git mode=100644,entry_kind=OTHER_TEXT;上下文为 live(`.`) |
| §1.1 L368–371 | 非 Python 名字须有解释器消费边或文档排除,其余 UNKNOWN_CAPABILITY | `.importlinter:8/:22/:32/:57` 的四次命中处均无解释器命令,也非文档 |
| §1.1 原子表 L425–428 | C7a限打包入口表,C7b限CI,C7c限shell,C7d限具名构建文件 | `.importlinter` 不属于四类任一;不能把静态门禁配置归作 Python import |
| §1.1 L356 | UNKNOWN_CAPABILITY 唯一解除途径为勘误扩表 | 实现侧不能自行将该配置白名单化或排除候选 |

该包是保留入口,不意味着其 re-export binding 可从扫描输入提前删除:
§1.2a L1332–1334 排除的是 A 类整模块删除,不是粒度②发现;
admission/disposition 尚未运行。用“将来会保留”跳过本条会缩小发现面。

四条原文:

```text
.importlinter:8:     tizen_convergence_judge
.importlinter:22:    tizen_convergence_judge | tizen_qb_discover | tizen_gerrit_fetch | tizen_build_verify | tizen_gerrit_submit | tizen_triage_report | gbs_patch_suggest
.importlinter:32:    tizen_convergence_judge
.importlinter:57:    tizen_convergence_judge
```

## 待设计方裁决

1. 为此类静态工具配置补封闭形态、解析位置、消费边含义与正/反控制;
   同步原子表/registry/正控制目录和相关投影。
2. 若其语义不是消费者,由设计侧给出封闭排除规则及机械上界、反向控制;
   不能由实现侧凭文件名或预期处置自行排除。

以上仅为候选方向,没有实施任何一个。没有将“未发现更多”写成全树不存在。
第1块仍未完成,无 scan completion marker;第2–5块、全部新增 OBS、门禁改前实跑未执行。
E8-5 全消费边控制与23形态五方对账仍待完成,预检组件测试不替代它们。
