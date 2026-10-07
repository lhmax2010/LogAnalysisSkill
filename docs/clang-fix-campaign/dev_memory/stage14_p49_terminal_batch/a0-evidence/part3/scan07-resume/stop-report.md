# SCAN-08:匿名 callable 的候选 ID 缺少唯一化规则

状态:OPEN,等待设计方裁决。不是 UNKNOWN_CAPABILITY 逐点放行申请。
SCAN-07 已关闭;本轮没有修改冻结稿,权威 SHA 仍为
`b5c2dce6568b722a70ceb92ed7860ecda4417ca8895310df4bdbf7ae9158cec3`。

## 规范位置

- 冻结稿 §1.1c:1022-1028:任一 callable 对单一外部模块纯委托须产出候选,
  无其它必要条件;不得用跨顶层包条件裁掉同包代理。
- §1.1c:1038-1048:PROXY ID 是 `<path>#PROXY#<callable lexical qualname>`,
  全局唯一、不含行号。
- §1.1c:1056-1062:N1 只合并同一逻辑 binding 的互斥 guard producer。
- §1.1d:1117:SEAL-7 要求 candidate ID 全局唯一。
- 勘误5 E5-3:release 仍入扫描,不能提前排除。

## 固定树见证

`anonymous-id-feasibility.command.json` 记录完整命令、脚本原文、工具 hash、
独立环境、HEAD/tree 和 exit;脚本只 AST 解析及 compile 取得 code object,
不 import/exec 被观测代码,不是 OBS producer。

```text
HEAD=43a6aa625f27da46daba190657bf62256080c68e
TREE=ca9331190e878af465e7968fe56e735585a5866e
python_entries=272
non_python_text_entries=570
contexts={'.':736,'release-v1.4.0':110}
lambda_sites=121
direct_import_call_id_collision_groups=5
EXIT=0
```

最小且不依赖复杂参数求值的见证:

```python
# tizen-gbs-log-analysis/scripts/gbs_analyzer/analyze.py:110
lambda: scan_buildlog(buildlog, cwd=src_root, trace_logger=trace_logger)
# 同文件:116
lambda: build_error_clusters(scan_result)
```

两者各自只有一次外部模块调用,实参全为 Name。导入分别在该文件:28 和:14,
指向 `gbs_analyzer.scan_and_extract.scan_buildlog` 与
`gbs_analyzer.error_clusters.build_error_clusters`。同属 gbs_analyzer 顶层包,
不能加跨包过滤。Python 编译器给出的 co_qualname 均为:

```text
analyze_buildlog.<locals>.<lambda>
```

因此按现有格式得到同一个 ID:

```text
tizen-gbs-log-analysis/scripts/gbs_analyzer/analyze.py#PROXY#analyze_buildlog.<locals>.<lambda>
```

这不是同一 binding 的互斥 producer:它们是两个独立的匿名 callable,
都在函数同一顺序执行块内,调用目标不同。直接 N1 合并会丢掉 callable 身份;
即便因宿主可变状态落 SCAN_UNRESOLVED,也仍需先有各自 candidate ID。
去掉 `<locals>` 也不会消除重名。冻结稿没有匿名 callable 的替代 ID 文法。

全部已取到的同类重名组(这是原始 direct-call 形状统计,不把每个复杂实参
lambda 都宣称为已裁定的纯代理):

| 上下文 | 文件 | lexical scope | 源行 |
|---|---|---|---|
| live | `tizen-gbs-log-analysis/scripts/gbs_analyzer/analyze.py` | `analyze_buildlog` | 110,116,121,123,142,168,198 |
| release | `release-v1.4.0/tizen-gbs-log-analysis/scripts/gbs_analyzer/analyze.py` | `analyze_buildlog` | 110,116,121,123,142,168,198 |
| live | `tests/unit/test_campaign_repair_step.py` | `test_round_budget_exhaustion_writes_exact_terminal_status` | 1219,1231 |
| live | 同上 | `test_invocation_budget_exhaustion_writes_exact_terminal_status` | 1243,1253 |
| live | 同上 | `test_orphan_reconciliation_uses_dedicated_error_code` | 1444,1458 |

完整121处源码、位置、上下文、导入事实、co_qualname 与五组重名见
`anonymous-callable-id.json`,SHA-256:
`3fe6bade0f09a43efa483d5825b9a387ec7bd427addf3e7a112cd0fb26bd384e`。

## 候选处置(均未实施)

1. 保留“任一 callable”的发现面,由设计方为匿名 callable 明定无行号的
   唯一 ID 后缀,例如词法宿主加 AST field/index 路径;同时明确相关名字形态
   与碰撞控制。实现方不自行挑后缀、哈希或编号。
2. 若设计方意图限定为具名 callable,须显式修订发现域并说明匿名纯委托的
   覆盖承担方;实现方不能把 lambda 自行当作 near-miss 排除。

## 停止边界

- 停止报告1项:SCAN-08。没有新增 predicate 或修改既有原始 OBS。
- 四级候选全集/三段台账尚未交付;不把可行性探查当作 shim_inventory。
- CTRL-INTRA-PKG-PROXY 仍 NOT_RUN,四级正控制和 near-miss 未声称完成。
- E9-5 的570条非Python文本预检仍 NOT_RUN。UNKNOWN_CAPABILITY、
  多去处、跨上下文回退边、MODULE_IDENTITY_AMBIGUOUS 和动态新增总数均 N/A,
  不用0冒充全量扫描结果;不能给出伪完整的按文件阻塞清单。
- 第3段后续8个claim和30场景 before_run 未运行,仍 PENDING_SEG3。
- 停止后仅完成已授权修复的回归、证据保全、登记和提交,不继续扫描实现。
