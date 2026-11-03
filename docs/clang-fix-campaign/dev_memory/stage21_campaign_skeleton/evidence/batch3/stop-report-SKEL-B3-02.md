# SKEL-B3-02: 无 RESULT 时实际 state_root 没有输入来源

状态:STOPPED,待设计方裁定。基线:`1a4ed25`。

## 事实与影响

1. 骨架冻结稿5.3(第184行)要求无RESULT时返回固定message,
   其中`<state_root>`必须替换为实际路径;不得读取trace来判断错误分支。
2. 该节保留的`design.md`4.1签名(1847-1853行)只有
   `--verification-ids --state-db --config --qb-result --review-target`,
   外加本轮已删除的人工降级参数,没有`--state-root`。
3. `docs/clang-fix-campaign/campaign-kickoff-template.md:71`起的配置模板
   没有state_root键;该路径在会话输入中单列,不是campaign_workspace。
4. 生产`qb_trigger.py:64`与`qb_result_fetch.py:75`的options显式接收state_root;
   `_trace`(`qb_trigger.py:287`)直接使用传入根写`qb_traces/<unit_hash>.jsonl`。
   没有约束其等于数据库父目录或源码workspace。
5. `campaign_state.py:198`起的QB请求/事件表不保存根目录;
   profile冻结内容也未约定保存它。无RESULT分支尤其没有结果文件引用可反推。
   `--qb-result`只是输入JSON路径,没有要求它处于canonical state_root下;
   无RESULT时不能把不存在或外部路径的父目录当作实际trace根。

因此,实现固定message必须新增接口约定或改变提示。现有参数不够确定实际根,
从state-db.parent、workspace或任意qb-result路径猜测都不是冻结条文。
本报告不声称六道重校验本身不可实现;停止点是用户要求严格实现的无RESULT输出契约。

## 离线证据

运行:

```bash
.venv/bin/python docs/clang-fix-campaign/dev_memory/stage21_campaign_skeleton/evidence/batch3/probe-state-root.py
```

结果:`probe-state-root.json`,exit 0。一个临时unit/request、零RESULT;
相同库与request在两个独立state_root调用生产trace写入函数,产生两个不同路径,
库sha256保持相同。没有网络、浏览器或真实状态库访问。
该探针不执行完整QB命令,只验证实际trace函数与数据库载体,不冒充端到端测试。
初次编写探针时误对create_qb_request已自动创建的SUBMITTED再次调用append_qb_event,
导致TypeError;删除该冗余调用后成功,不是生产缺陷。

## 候选处理(未实施)

推荐A:给review-submit新增必填`--state-root <dir>`,仅用于固定提示与本命令trace,
由调用者传与QB命令相同的根;不改DB/schema、不扫描目录、不读取trace判断分支。
同步CLI示例、编排skill与启动模板。文案与返回码保持冻结要求。
副作用:新增一个必填参数;遗留review-submit命令示例需更新(当前尚无实现)。
新增测试:state_root与DB父目录/workspace分离时message仍准确;缺参数exit2且零外部动作;
两个不同显式根产生不同固定message,其它输出及库均不变。

候选B:设计方明确增加config.state_root必填键作为review-submit提示来源,
并规定与QB CLI显式根的一致性责任。副作用:新配置项与两种来源需同步;
相较A更容易出现配置与实际QB调用不一致。需同样的分离路径与缺键测试。

候选C:取消实际路径插值,把固定message改成“调用qb-result-fetch时所用的state_root”。
不增接口,但降低提示精度且改变冻结文案,须设计方明确批准。

## 本轮范围与验收

- 仅登记SKEL-B3-01、读取失败观测表、停止报告及离线探针。
- review-submit/start-check/编排skill/端到端均未实现,全仓门禁NOT_RUN。
- 原3028个nodeid与全部生产文件不改;未运行四组安全测试。
- 冻结稿、身份校验、安全核心、QB写入/schema、代理字节不变。
- 未联网,未运行真实gbs,未访问/推送真实Gerrit或QuickBuild;不进入第3.5批。
- 文档检查器与diff检查结果见`checks.json`。第2批结果不能作为本轮门禁结果。
