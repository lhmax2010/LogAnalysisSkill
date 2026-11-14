# FatTank：Checkpoint B1 人工命令

本文件给 FatTank/Hao Lin 使用；人工命令不列在 ClineSR 的 SKILL.md。当前只有无浏览器读取与人工裁决，没有 `once`、点击、演练或提交实现。不要把“唯一候选”当成本请求身份的自动证明。内部名字可以回显，凭据永远不可回显或入库。

所有命令在本线独立工作树运行，`--config` 指向构建机原有配置。人工命令只能在独立控制终端执行，先输入 `yes`；管道/非终端退出 2，扩展宿主或 Cline 祖先拒绝（启发式防误操作，不是账号隔离边界）。

```bash
python3 vd-cosmos-submit/scripts/run.py attest --request R --build-id B --reason '核对依据' --config "$VD_CONFIG" --backend real
python3 vd-cosmos-submit/scripts/run.py bind --request R --build-id B --reason '核对依据' --config "$VD_CONFIG" --backend real
python3 vd-cosmos-submit/scripts/run.py rebind --request R --build-id B --reason '重跑后人工选择' --config "$VD_CONFIG" --backend real
python3 vd-cosmos-submit/scripts/run.py abandon --request R --reason '停止观察理由' --config "$VD_CONFIG"
python3 vd-cosmos-submit/scripts/run.py resolve --request R --build-id H --reason '提交端历史核对' --config "$VD_CONFIG"
python3 vd-cosmos-submit/scripts/run.py resolve --request R --manual-submit --build-id H --reason '确认曾人工提交' --config "$VD_CONFIG"
python3 vd-cosmos-submit/scripts/run.py resolve --request R --not-submitted --checked-at '2026-11-14T12:00:00Z' --reason '人工历史核对依据' --config "$VD_CONFIG"
python3 vd-cosmos-submit/scripts/run.py resolve --session S --manual-rerun --hub-id H --reason '人工重跑核对依据' --config "$VD_CONFIG"
```

`resolve --build-id` 的 H 是提交端编号；`attest` / `bind` / `rebind` 的 B 是构建管理端构建号。`--no-manual-submit` 是未提交裁决的另一入口。未定位不能用作未提交的依据。挂起的重跑记录需要额外输入 `rerun-records-unrelated`，不能通过换请求号清除。

认领先回显候选范围、锚点、当前保留记录中的覆盖、各字段比较、未核验字段、Hub Link、开始时间、待核对集合、H_pre 和范围内同账号的其它构建。按提示从 `/dev/tty` 输入构建号或确认词：

- `claim-unverified`：H_pre 或校时样本未知、覆盖不足、候选编号未大于 H_pre，或存在其它同账号的新构建。
- `claim-outside-candidates`：指定构建不在本次候选集合。它只能越过集合成员检查，不能越过身份、配置、已有归属、开始时间或已确认递增下的 H_pre 硬检查。两词独立，要求两个时必须都输入。

确认期间网络读取不持请求锁；回写前按最新请求版本及最新已落库扫描核对依据，依据变化要重新回显。绑定不是起轮授权，报告与输入核对仍需完成；不一致不得推进。改变绑定保留旧绑定记录并使旧映射产物过期。放弃观察不能清除已提交历次或未知提交状态。

观察续跑：

```bash
python3 vd-cosmos-submit/scripts/run.py watch --request R --config "$VD_CONFIG" --backend real
```

控制终端里可以确认候选；扫描与心跳在后台继续。不希望出现人工确认时加 `--read-only`。后台、管道运行只观察和写待办。观察运行锁与短暂的请求锁分开，另一个观察进程退出 6，人工命令最多等 `poll.lock_wait_s`。心跳空档超过三倍 `poll.watch_interval_s`（默认 300 秒）记中断。历史会清理，否定结论只能是“在已读取的保留记录中未发现”，不能称“从未重跑”。

B1 构建机只读验收（EXPECTED_COMMIT 必须是本批审核的完整提交号，不能现场直接取 HEAD 代替审定）：

```bash
nice -n 19 bash vd-cosmos-core/scripts/verify_b3a11b1_real.sh "$EXPECTED_COMMIT" --config "$VD_CONFIG"
```

使用现有 Python 3.10.12 验收 venv，已装开发工具 import-linter==2.3，并置于 PATH 首位。脚本先核对 HEAD/本线源码干净，所有写入位于原 data_root 下新建的 verification/b3a11b1-随机串目录；运行完整离线套件，然后 doctor --online 和两次无登录查号。37491096 应只得到 19270912；37491058 应只得到 19270877，后者只作误提交的只读查号核验，禁止绑定、分析或用作输入。没有自动安装、登录、浏览器、P4 或提交动作。


## B1.1：同一会话验收 A + B1

使用本次回报、经设计方审核的完整提交号填写 EXPECTED_COMMIT；将现有 Python 3.10.12 验收 venv 的 bin 放在 PATH 首位（import-linter==2.3）。VD_CONFIG 为构建机原配置绝对路径；B21_SAVED_DIR、B21_ROWS、B21_LINKS 为第 2.1 批已有独立基线的绝对路径（saved-dir 含 report_armv7l.html、report_x86_64.html、probe_3bed7e8c.html；links 为 arm-only）。同一干净检出、同一提交，依次执行：

```bash
nice -n 19 bash vd-cosmos-core/scripts/verify_b3a11_real.sh "$EXPECTED_COMMIT"   --config "$VD_CONFIG" --saved-dir "$B21_SAVED_DIR"   --rows "$B21_ROWS" --links "$B21_LINKS" &&
nice -n 19 bash vd-cosmos-core/scripts/verify_b3a11b1_real.sh "$EXPECTED_COMMIT"   --config "$VD_CONFIG"
```

A 非零退出就不运行 B1。两条命令各自核验完整 HEAD/本线源码洁净、执行同解释器完整离线套件，各自只写配置 data_root 下全新独立子目录。A 运行读取侧 A–F 和 19091860 七失败包的只读 P4 快照，未登录只打印登录命令并停止，不代登录；B1 做在线 doctor 和两次只读查号。两条均不打开浏览器、不提交构建、不安装软件。未取得构建机输出前，只能声称离线验证通过。

B1.1 的三个操作含义：①变量页首次值已冻结，出现“变量页已变化”不能通过重试覆盖原值；保留原输入和变化待办交设计方处理，本批不提供覆盖开关。②“重跑链”不等于证据冲突，逐项列出各构建的编号、开始时间和状态，仍由 FatTank 选择，工具不取最早/最新。③18 项映射提案只在 DELIVERY 中，默认配置仍未登记；recon25 后已登记的变量/编码可按 cmp-v1 比较，未登记仍未核验，旧 request_text_verified 不再作为文本比较开关。EMAIL_CC 变量页不列出。首读冻结只是防御规则，recon25 D3 未发现所核对历史清单变化。
