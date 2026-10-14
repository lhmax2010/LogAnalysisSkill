# P5Q 原始正文与活动文档比对

本脚本不在生产包。C5a只在本地HTTPS假服务器验证,以下命令留给C5b审批后执行。
复用生产createRuntime/Agent/read与installGuards;不传测试证书或DNS覆盖。
只允许只读集合中的精确路径,无查询、无动作链接。登录由人在浏览器内完成,
无终端输入、无自动填写。配置1917已由live-12登记。

在仓库根执行。唯一待FatTank指定的是`<TARGET_BUILD_ID>`(可对父、子分别执行,
每次使用新的目录;下面目录首次执行时必须不存在)。固定样本1193467/1193469与
配置1917同轮比较;成功父子样本不足时继续挂账,不得把本地夹具当真机证据。

```bash
mkdir -p docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C5b
/home/linhao/.local/bin/node docs/clang-fix-campaign/spikes/p5q_compare_raw_active.mjs --path /build/1193467/overview --path /build/1193467/variables --path /build/1193469/overview --path /build/1193469/variables --path /build/1193469/step_status --path /overview/1917 --path /build/<TARGET_BUILD_ID>/overview --path /build/<TARGET_BUILD_ID>/variables --output docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C5b/raw-active-01
```

同一次生产read导航捕获原始响应字节并按charset严格解码;随后从隔离环境取活动
文档序列化文本。两份都在惰性文档内脱敏后保存,**不保存未脱敏原字节**。
文件分别为NN.raw-redacted.html、NN.active-redacted.html,逐字段结论在
NN.comparison.json,总索引run.json。登记位置之外身份计数分别记录。
JS写前检查+Python qb_redact写前/写后原字节自检,失败删除该文件并停止。

出现仅活动文档有值或值不同,保存这一页证据后停止后续页;不改变生产read,
不从活动文档回退取得业务结论。构建号核对失败允许保存比对事实,不视为核对通过。
其它读取失败/WORKER_BLOCKED/NEW_PAGE/runtime.failure立即停止;不自动重试。
没有submit/Accept/Ready to Accept路径,不写state DB。
