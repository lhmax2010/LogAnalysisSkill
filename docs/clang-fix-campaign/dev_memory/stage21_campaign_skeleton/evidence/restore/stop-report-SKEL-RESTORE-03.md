# SKEL-RESTORE-03:恢复第2批输入与输出契约待裁定

## 1. 停点与范围

SKEL-RESTORE-02已关闭T1审核资格冲突。本报告不是重新质疑该裁定,
也不要求扩大其两处审核修改。恢复第1批独立验收,第2批在接口核对处停止;
未实现KB、propose-fix或审核改动,未进入第3批。等待设计方明确以下两项。

## 2. 事实与证据

### 2.1 propose-fix的固定输出字段

SKEL-RESTORE-01第二.4.c原文要求生成分支输出`needs_generation=true`;
同节4.d给出的固定JSON字段为:

```text
mode, edit_spec_path, source_kind, kb_precedent_ref,
context_dir, t2_records, downgrade_reason
```

固定表不含`needs_generation`。若“固定字段”指固定键集合,七键与显式布尔字段
不能同时满足;若只是最小字段集,需要明确允许第八键。本轮不自行把布尔字段
藏入context文件、不省略它,也不自行增加stdout键。

离线事实探针[probe-contract.py](batch2/probe-contract.py)枚举两种形状,
[contract-probe/stdout.log](batch2/contract-probe/stdout.log)记录各自满足哪一约束。
这是条文形状核对,不是生产功能测试,不能证明应选择哪一种解释。

### 2.2 imported_shelve的baseline_commit来源

design.md第807-820行把`baseline_commit`列入clang_kb/v1字段与去重七元;
第1051-1053行区分完整溯源instance与可将instance字段置null的seed。
SKEL-RESTORE-01第二.3.b新增的imported_shelve明确允许`verified_tree_sha`为空,
但没有规定`baseline_commit`是否也可为空。其CLI参数中既无baseline输入,
也无源仓库或manifest输入。

这不是可以从任意CI日志可靠补出的值。本机已有
`tests/fixtures/e2e_clang_compile/buildlog:1`只有3行编译命令/诊断;
真实`gbs_analyzer analyze`在该输入上exit0,结果的全部嵌套键已归档,
没有baseline_commit/base_commit/revision/commit_sha/verified_tree_sha。
见[analyzer原始产物](batch2/contract-facts/analyzer/evidence_packet.json)与
[命令、时刻、退出码](batch2/contract-probe/command.json)。
diff的Git index行即便存在也表示blob标识,不是源码commit;QuickBuild编号
也不能离线直接推出revision。未尝试真实网络、没有编造SHA或假设该字段可空。

## 3. 候选文字修订与影响(均未实施)

### 3.1 输出形状

推荐在第二.4.d增加一项:

```diff
- downgrade_reason。
+ downgrade_reason、needs_generation(布尔值;mode=generate时true,t1时false)。
```

副作用:固定键集合由7变8,新CLI与编排消费端需统一;尚无既有propose-fix协议需迁移。
替代方案:删除4.c中的`needs_generation=true`,明确`mode=generate`为唯一生成标识。
新增测试:两分支精确键集合、类型、mode与布尔值一致性;第四批剧本按同一契约消费。

### 3.2 历史基线来源

候选A(完整溯源优先):第二.3.b增加必填`--baseline-commit <完整commit>`;
规定SHA形态与原样入库,不能从diff的index猜测。不改变七元或其它来源schema。
副作用:历史修法导入前必须由人补齐revision,无revision的历史材料暂不能导入。
新增测试:缺失/非法参数零写入,有效值原样保存,不同baseline分开去重,相同七元幂等。

候选B(允许不完整历史导入):明确仅`origin=imported_shelve`同时允许
baseline_commit与verified_tree_sha为null,并明确null在七元哈希中的编码。
副作用:缺失两个溯源值时,同包/同failure的不同历史diff可能归到同一个七元,
必须同时裁定该情形是返回原id、拒绝冲突还是另行调整身份公式;不能擅自加第八元。
新增测试:仅此origin允许空值、null编码稳定、同七元不同diff的规定行为、其它origin拒绝。

## 4. 边界

仅做离线契约探针和记录;不写KB或state DB、不改审核/推送/代理/guard/身份判据。
SKEL-RESTORE-02的审核两处修改及测试仍随第2批提交,未提前混入第1批。
未把部分恢复写成全部完成;冻结稿与design.md本轮保持原字节。
