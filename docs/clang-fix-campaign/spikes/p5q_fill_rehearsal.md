# P5Q 十二字段填表演练

C5a只运行假服务器;以下C5b命令需FatTank确认后执行,目标行与计划实际提交的
目标行相同。唯一待指定参数是`<TARGET_LINE>`(git_path@40位小写commit)。
配置固定1917/Base RBS/TRIGGER;Full、ALL、Ref. Snapshot、SNAPSHOT_NUM=@freeze、
tizen_base、Immediate Stop With Error=true、三架构组合、TARGET_IMAGE空列表、
Add/Remove空串。BUILD NOTES使用独立rehearsal-UUID标记,不写任何state DB。

```bash
mkdir -p docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C5b
/home/linhao/.local/bin/node docs/clang-fix-campaign/spikes/p5q_fill_rehearsal.mjs --target '<TARGET_LINE>' --output docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C5b/fill-rehearsal-01
```

弹出窗口后只由人在窗口内登录,600秒时限;不读stdin,不自动操作登录表单。
仅调用生产login、open_form、fill、close。源码静态断言排除提交命令、Ok点击和
提交URL登记;没有Accept/Ready to Accept代码。

只观察生产快照及协议适配器已筛出的元数据,不读取请求头/请求体。run.json记录
12字段原始回调形态、action/版本、初值与是否已相等、每窗口回调POST获准/拒绝数、
响应状态与random值、最终action、读回与指纹。表单action放行次数来自实际事件,
须为0;policy.released也须为false。后台刷新GET的拒绝另列,不算字段POST失败。
配置页与各次表单快照另记登记位置外身份计数;使用隔离环境序列化及生产惰性
脱敏,不增加请求。计数同时进入生产trace,不会改变表单判定。
写前写后均使用生产qb_redact自检。输出目录必须是新目录,不覆盖旧证据。

不修改Policy/installGuards,未增加任何生产trace字段。失败不重开/重试表单,
关闭浏览器并留存已取得的记录;成功也直接close,不会创建构建。
