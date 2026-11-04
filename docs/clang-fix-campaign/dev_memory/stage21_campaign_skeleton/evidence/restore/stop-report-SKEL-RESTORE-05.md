# SKEL-RESTORE-05:seed 的七元去重编码未定义

## 1. 停点

SKEL-RESTORE-04已关闭第03号报告的两处接口问题。本报告不重开它们,
也不改变SKEL-RESTORE-02的T1审核资格裁定。

恢复第2批实现核对到seed写入时停止:design.md允许seed的实例字段为null,
但七元去重公式需要拼接其中四个字段,没有定义null的字节编码。
本轮不自行以空串、字面量null、虚构commit或新增seed专用公式代替。
拒绝全部seed也不能作为交付:这会使第3.5节的人工策略入库与Phase8不完整。

## 2. 原文与离线证据

- `docs/clang-fix-campaign/design.md:818`:
  `sha256(package + gerrit_path + baseline_commit + verified_tree_sha + diagnosed_flag + toolchain_profile + error_signature_normalized)`。
- `docs/clang-fix-campaign/design.md:1053`:seed为人工审定的类别策略,只参与T2,
  instance必填字段置null。
- `docs/clang-fix-campaign/design.md:2000`:append进行schema校验、七元命中返回既有id。
- `docs/clang-fix-campaign/design.md:3229`:Phase8包含人工审定seed初始数据。
- SKEL-RESTORE-04第一.②只规定`instance/origin=imported_shelve`的tree槽位为
  `imported:`加原始diff的SHA256,没有覆盖`record_type=seed`。

[probe-seed-dedupe.py](batch2/probe-seed-dedupe.py)不导入未验收KB实现,
只构造四个实例槽位为null的七元,直接拼接得到TypeError;
分别试算三种候选编码得到三个不同hash。普通instance的全字符串公式不变。
[stdout](batch2/seed-contract-probe/stdout.log)与
[argv/UTC/exit](batch2/seed-contract-probe/command.json)保留实测,exit0。
探针只说明编码会改变持久化身份,不是证明Python异常本身属于生产缺陷,
也不证明某个候选更符合设计。未写KB、state DB或发起网络请求。

检索范围:design.md的schema、T1/T2、CLI、Phase8条款;
campaign core、相关测试与原有实现。没有可复用的KB seed/null哈希约定。
草稿自行要求历史initial/final非空的校验不作为本报告依据:
没有找到该非空约束的明确条文,这属于草稿待修项,不是设计冲突。

## 3. 候选文字diff(均未采用)

### A. seed的null槽位按空串计算

```diff
 七元:同包同tree下多个failure pattern各存一条。
+ 仅record_type=seed:七元中的null槽位在计算dedupe_key时编码为空字符串;
+ JSONL中仍保存null,不伪造package、仓库路径、baseline_commit或tree。
+ 其它槽位与普通instance公式不变;imported_shelve仍按SKEL-RESTORE-04。
```

副作用:同一flag/profile/归一化signature的seed会命中同一id,
即使fix_summary或root_cause_category不同也不另建记录,因为它们不在七元内。
需设计方明确接受这一去重粒度。实例非空校验不能因seed例外而放宽。

### B. 为seed另定义有域标识的去重公式

```diff
+ record_type=seed使用另行规定的seed专用公式;instance继续使用原七元。
+ 公式必须明确字段、顺序、null编码、UTF-8序列化与域标识。
```

副作用:这是显式改变现有七元契约,需裁定完整公式,不能只授权“自行处理null”。
可以区分不同类别的人工策略,但需要单独的黄金向量与兼容性说明。

两种候选均需新增:seed append成功/重复返回既有id/并发幂等;
seed只出现在T2且排序正确;空实例仍拒绝;普通instance七元逐字节不变;
imported_shelve原始diff槽位不变;固定hash黄金向量;同键不同摘要的明确行为。

## 4. 本轮草稿与局部检查

未验收草稿已保存于
[implementation-wip.patch](batch2/seed-stop/implementation-wip.patch),
[文件与hash清单](batch2/seed-stop/wip-manifest.json)。9个既有文件的本轮改动已撤回,
12个新增实现/测试文件已从源码树移出;仅保留patch用于定位,不得直接恢复当作交付。
恢复后验证见[rollback-integrity.json](batch2/seed-stop/rollback-integrity.json)。

停止前局部运行记录(不作本批门禁):

| 范围 | 当时观察 | 限制 |
| --- | --- | --- |
| D2E补修 | 99 passed,含35新增 | 协作任务报告,没有全仓验收 |
| T1审核 | 33 passed,含7新增 | 原26例加新7例,未改原断言 |
| propose-fix | 32 passed | 未完成seed持久化闭环 |
| sync/状态/生命周期 | 较早一轮106 passed | 后增用例运行在48 passed处主动中断,exit2,不能算通过 |
| KB CLI新用例 | 12 passed,3 failed | 草稿错误地拒绝历史策略空值,待修;不是本次停止依据 |

SKEL-RESTORE-04要求D2E补修与第二批同一轮全仓门禁,所以本次不单独交付补修或
两处审核改动。没有运行本轮全仓pytest/mypy/import门禁,不声称第二批完成。
design.md尚未登记实现落地,其原字节保留;第三批URL取证尚未开始。
没有更改冻结稿、代理、安全核心、共享身份规则或真实状态库;无真机操作。
