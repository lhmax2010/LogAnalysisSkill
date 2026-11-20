# 第 3a-2 批 FatTank 手册

## 1. 核对部署与已有输入

在独立的构建机 clone 里核对完整提交号和 Python 版本。使用本线 `run/venv` 的解释器。LogAnalyzer 照旧使用该环境中已有的 PyYAML。

```bash
export PATH="/path/to/run/venv/bin:$PATH"
repo=/path/to/run/src
config=/path/to/data/config.json
expected='replace-with-deployed-full-commit'
nice -n 19 bash "$repo/vd-cosmos-core/scripts/verify_b3a2_real.sh" "$expected" --config "$config"
```

把 `expected` 填成已部署的完整提交号。默认验证 19270912。换构建时加 `--build <构建号>`。验证器只读已登记并核验的最终失败日志和快照，在数据根下独立的 `verification/b3a2-*/` 生成任务、验证全部分段清单，并用明确标为 fixture 的手写结果验证接收器。回贴 stdout 中的结论和证据路径即可。缺输入时先用既有读取与快照流程补齐并登记，再重新运行验证器。

## 2. 准备正式任务

workflow tick 在最终日志和可靠来源已登记时逐个组包。也可为单个失败包手工准备，`round` 是状态库中的 64 字符构建摘要，`build` 是构建号，`log` 和可选 `snapshot` 是回执登记的数据根内路径。

```bash
nice -n 19 python3 "$repo/vd-fix-analyze/scripts/run.py" prepare --config "$config" \
  --round "$round" --build-id "$build" --log "$log" --snapshot "$snapshot"
```

任务回执包含 task ID、input digest、attempt 和目录。默认复用相同输入的有效任务。明确重做时加 `--new-attempt`。原始日志或快照改变后按新摘要另建任务。老快照没有最终日志摘要关联时仅供诊断。

## 3. 人工核验 ClineSR 扩展工作区

1. 关掉命令执行、文件编辑和工作区外读取的自动批准。只给本轮新窗口打开数据根下的 `tasks/<轮次>/`。保持仓库目录和平时的工作区在该窗口外。
2. 批准前在平时的工作区及全局 skill 目录（如果存在）各放一个只有随机标记的金丝雀 skill。手工设置 `analyzer.cline_extension` 的 `normal_skills`、`global_skills`、`canary`（同一金丝雀目录名）。可在 `config_files` 中分别配置 `mcp`、`global_rules`、`global_workflows` 和 `auto_approval` 的实际配置文件路径。准备任务时，工具只记录这些配置的摘要及 skill 清单元数据摘要。
3. 通过扩展 UI 和生效配置核对当前窗口可见的 skills、MCP、规则和自动批准。确认只显示工作区中的分析 skill、两处金丝雀均不可见、无凭据访问工具并且自动批准关闭。用无操作标记核验工作区外读取会提出单独批准，拒绝该请求。别用模型自述作为证据。手工删除金丝雀。
4. 金丝雀、凭据类 capabilities 或配置检查未通过时，把结论记为“隔离未通过，人工监督模式”。只有 FatTank 可以决定继续人工监督。扩展和工具同账号运行，权限提示、文件模式和进程祖先守卫只减少误操作。

## 4. 运行扩展和接收结果

在 ClineSR 中选择唯一的 `vd-fix-analyze` skill，指明 attempt 路径。允许查看任务目录内的 inputs。只批准写该 attempt 的 `outputs/result.json` 和执行下列接收命令。分析者使用 `inputs/result-schema.md`、真实的 task/digest/attempt 和已登记的 evidence ID。

```bash
nice -n 19 python3 "$repo/vd-fix-analyze/scripts/run.py" accept --config "$config" \
  --round "$round" --task "$task" --attempt "$attempt"
```

核对 `rounds/<轮次>/reports/analysis-comparison.md` 和 workflow status 的分析投影。接收表示分析结果通过了结构与来源检查。批准方案、CL、验证和疑似真 bug 定性由后续人工流程处理。输入过期或只读 skill 变动后建立有效的新 attempt。日志中的操作指令不能执行或引用。

## 5. 录入诊断族

把与轮次相对应的 base primary repodata 放在数据根下 `rounds/<轮次>/inputs/base-repodata/primary.xml.gz`，或导入与准备时加 `--primary-repodata <数据根内路径>`。先确认 gbs root 与 base 的 Clang 完整版本-发布号相同。

只由 FatTank 在构建机控制终端运行下面的生成器。它经 sudo/chroot 在选定 root 内只执行只读的 RPM 查询与 diagtool tree，输出到数据根。

```bash
nice -n 19 python3 "$repo/vd-cosmos-core/scripts/generate_diagnosis_families.py" \
  --config "$config" --gbs-root "$gbs_root" --output diagnosis-family-candidate.json
nice -n 19 python3 "$repo/vd-fix-analyze/scripts/run.py" import-diagnosis-families \
  --config "$config" --round "$round" --family-file "$data_root/diagnosis-family-candidate.json"
```

核对生成的两档条目和本轮版本。导入版本不符时会拒绝，按待办继续保守升档。人工在同版本的 VD Clang 源码包中提取诊断分组也是可用来源，先按相同 JSON 结构构造清单再交给版本检查。
