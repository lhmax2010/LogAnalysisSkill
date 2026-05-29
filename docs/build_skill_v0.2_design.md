# gbs_build_skill v0.2 重构设计

**版本**: v0.2(从 v0.1 升级)
**触发源**: v0.1 只捕获 gbs 终端输出(A),失败分析时真正错误常被 gbs wrapper 总结淹没;BW-M4 时 workflow 临时加 `select_analysis_log` 从 A 提取结构化日志(B)路径属权宜之计且职责错位
**目标**: 让 build skill 成为编译日志获取的唯一负责人,产出可直接用于分析的日志
**范围**: 本设计覆盖 Phase A(build skill 自身升级);Phase B(workflow 切换)单独 PR 实施

## 1. 设计哲学

> build skill 的目的是"获取编译错误日志,提供给 analyzer 分析"。它跑编译 + 拿到所有相关日志 + 明确告诉调用方哪份适合分析。不分析、不修复、不编排。

## 2. 职责变化(v0.1 → v0.2)

| 维度 | v0.1(现状) | v0.2(目标) |
|------|-----------|-----------|
| 跑 gbs | ✅ | ✅ |
| 抓 A(终端输出) | ✅ | ✅(机制不变) |
| 找 B(结构化失败日志) | ❌ | ✅ 新增 |
| 输出"分析用哪份" | ❌(只有 log_path) | ✅ 新增 `analysis_log_path` |
| 工作目录控制 | 已有 `BuildOptions.cwd`,但 CLI 无对应参数 | CLI 新增 `--src-dir`,语义=传给 `cwd` |

`select_analysis_log` 从 workflow 移除是 **Phase B** 的事,本设计 Phase A 不动 workflow。

## 3. 两个日志来源(参考)

| | A: 终端输出 | B: 结构化失败日志 |
|---|---|---|
| 内容 | gbs 全过程输出 | 当前失败包的详细日志 |
| 路径 | 用户指定 `--output-log`(BuildOptions.output_log) | `<GBS-ROOT>/local/repos/<profile>/<arch>/logs/fail/<包名>/log.txt` |
| 何时有 | 总有 | 仅失败时 |
| 适合分析 | 横向全但被 wrapper 信息淹没 | 失败包纯净详情,**分析首选** |

## 4. 接口设计

### 4.1 CLI 参数

```bash
python -m gbs_build_skill \
    --conf <gbs.conf 路径>          # 必填(v0.1 已有)
    --arch <架构>                    # 必填(v0.1 已有)
    --include-all                    # 可选(v0.1 已有)
    --output-log <A 路径>            # 可选(v0.1 已有)
    --timeout <秒>                   # 可选(v0.1 已有)
    --src-dir <代码目录>             # 新增,可选,语义=传给 BuildOptions.cwd,不传则 cwd=None(用当前 cwd)
```

**只新增 `--src-dir` 一个参数**。其他 5 个保持 v0.1 行为。

`--src-dir` 的实现:
```python
parser.add_argument("--src-dir", type=Path, default=None, help="Source directory to run gbs in. Defaults to current working directory.")
# 传给 BuildOptions
BuildOptions(..., cwd=args.src_dir)  # cwd 字段 v0.1 已有
```

### 4.2 Python API: BuildResult

**v0.1 字段全部保留**(向后兼容,workflow 现在的 import 仍工作):

```python
@dataclass(frozen=True)
class BuildResult:
    # v0.1 已有(保留,不改名)
    exit_code: int
    log_path: Path                        # ← v0.1 字段名,workflow 已用,保留
    command: tuple[str, ...]
    duration_seconds: float
    timed_out: bool = False
    
    # v0.2 新增
    failure_log_path: Path | None = None  # B 路径(失败且找到才有)
    analysis_log_path: Path | None = None # 推荐分析日志(成功=log_path,失败找到B=B,失败找不到=log_path)
    package_name: str | None = None       # 当前编译包名(从 B 路径提取)
```

**默认值都给 None,确保所有现有调用代码继续工作**(workflow 不知道新字段就忽略)。

`analysis_log_path` 在初始化后填值,不是 default None 永远 None。

### 4.3 Python API: BuildOptions

**v0.1 字段全部保留,不新增字段**。`--src-dir` 通过现有的 `cwd` 字段实现。

```python
@dataclass(frozen=True)
class BuildOptions:
    # v0.1 已有,全部保留
    conf: Path
    arch: str
    output_log: Path
    include_all: bool = False
    timeout: int = DEFAULT_TIMEOUT_SECONDS
    gbs_binary: str = "gbs"
    cwd: Path | None = None  # ← v0.1 已有,CLI 新增 --src-dir 给它传值
```

## 5. 行为流程

```
1. 验证 --conf 文件存在、--arch 非空
2. 确定工作目录:
   - --src-dir 给了 → 传 cwd=Path(src_dir).resolve(),验证目录存在
   - 否则 cwd=None(subprocess.Popen 用当前 cwd)
3. 构造 gbs 命令: gbs -c <conf> build -A <arch> [--include-all]
4. 流式捕获 stdout/stderr → output_log(A,v0.1 机制不变)
5. 编译结束,看 exit code:
   - 0(成功):
     * failure_log_path = None
     * analysis_log_path = log_path (即 A)
     * package_name = None(成功不需要)
   - 非 0(失败):
     * 调用 _extract_failure_log_path(log_path)
     * 提取成功 + 文件存在:
       failure_log_path = 那个路径
       analysis_log_path = failure_log_path
       package_name = 从路径提取(如 "ffmpeg-8.0.1-0")
     * 提取失败 / 文件不存在:
       failure_log_path = None
       analysis_log_path = log_path (退回 A)
       package_name = None
6. 返回 BuildResult(v0.1 字段 + v0.2 新字段填值)
```

## 6. B 路径定位(主路径,不做 gbs.conf 兜底)

### 6.1 正则

```python
GBS_FAILURE_LOG_PATTERN = re.compile(
    r"Leaving the logs in (?P<path>/\S+/logs/fail/(?P<pkg>[^/]+)/log\.txt)"
)
```

匹配 gbs 失败时打印的 `warning: build failed, Leaving the logs in /.../logs/fail/ffmpeg-8.0.1-0/log.txt`。

### 6.2 实现

```python
def _extract_failure_log_path(compiler_log: Path) -> tuple[Path | None, str | None]:
    """从 compiler.log 提取结构化失败日志路径 + 包名。"""
    try:
        text = compiler_log.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None, None
    
    matches = list(GBS_FAILURE_LOG_PATTERN.finditer(text))
    if not matches:
        return None, None
    
    # 多包构建按构建顺序打印,取最后一次匹配(当前真正失败包)
    last = matches[-1]
    candidate = Path(last.group("path"))
    if not candidate.is_file():
        return None, None
    
    return candidate, last.group("pkg")
```

### 6.3 不做兜底

不解析 gbs.conf 推断路径。正则失败 / 文件不存在直接退回 A。

### 6.4 多失败包: 取最后一次匹配

`finditer` 取最后一次。单包构建只有一次,多包构建最后一次是当前真失败包(GBS 按构建顺序输出)。

## 7. CLI stderr 摘要

build skill 单独 CLI 用时,stderr 打印结构化摘要(stdout 仍干净,符合 v0.1 约定):

成功:
```
gbs_build_skill: build succeeded (exit 0)
gbs_build_skill: compiler log written to ./compiler.log
```

失败且找到 B:
```
gbs_build_skill: build failed (exit 1)
gbs_build_skill: compiler log written to ./compiler.log
gbs_build_skill: failure log: /home/.../logs/fail/ffmpeg-8.0.1-0/log.txt
gbs_build_skill: recommended for analysis: /home/.../logs/fail/ffmpeg-8.0.1-0/log.txt
gbs_build_skill: package: ffmpeg-8.0.1-0
```

失败但没找到 B:
```
gbs_build_skill: build failed (exit 1)
gbs_build_skill: compiler log written to ./compiler.log
gbs_build_skill: failure log: not found in compiler log
gbs_build_skill: recommended for analysis: ./compiler.log (compiler log only)
```

格式风格沿用 v0.1 stderr 摘要(每行 `gbs_build_skill: <内容>`)。

## 8. 退出码(完全沿用 v0.1)

- `0`: build 成功
- 非 0: build 失败(透传 gbs 真实退出码,通常 1)
- `124`: 超时
- `127`: gbs 命令未找到

**找不到 B 不影响 exit code**——只是日志降级到 A。

## 9. SKILL.md 更新(tizen-gbs-build/SKILL.md)

需更新内容:

- **description**: 加触发词"获取编译日志/获取失败日志/获取结构化失败日志"
- **Required Workflow**: 加 `--src-dir` 参数说明
- **Output Contract**: 新增段落说明 `failure_log_path` / `analysis_log_path` / `package_name` 字段
- **Examples**: 加一个"在 ffmpeg 目录跑 build,失败后拿到 B 日志路径"的例子
- frontmatter 其他字段不变

## 10. 不做的事(Phase A 明确边界)

- 不解析 gbs.conf
- 不收集多个失败包
- 不分析任何日志
- **不修改 workflow / analyzer / suggester(Phase B 才动 workflow)**
- 不动其他 SKILL.md(只动 build 的)
- 不改 pattern 内容 / pyproject
- 不改流式捕获机制(v0.1 subprocess + reader 线程 + stderr 合并保持)
- **不重命名 v0.1 已有字段**(exit_code / log_path / command / duration_seconds / timed_out 保留)
- 不改 BuildOptions 字段(只通过 CLI `--src-dir` 给现有 cwd 字段传值)

## 11. 验证

### 11.1 单元测试

- `_extract_failure_log_path` 4 个 case:
  * 标准失败输出含 "Leaving the logs in ..." → 返回正确路径 + 包名
  * 多次匹配 → 返回最后一次
  * 无匹配 → 返回 (None, None)
  * 路径存在 vs 不存在
- BuildResult 三场景:成功 / 失败找到 B / 失败找不到 B 三种 analysis_log_path 正确
- `--src-dir` 处理:存在 / 不存在 / 相对路径
- **现有 7 个 build skill 测试 0 退化**(v0.1 字段不改名,旧测试都该过)

### 11.2 真实场景

- ffmpeg tizen 分支(成功):exit 0,analysis_log_path=log_path,failure_log_path=None
- ffmpeg real_smoke/E(av_temp_lss):
  * exit 非 0
  * failure_log_path 正确指向 `<GBS-ROOT>/.../logs/fail/ffmpeg-8.0.1-0/log.txt`
  * 该文件确实存在
  * analysis_log_path = failure_log_path
  * package_name = "ffmpeg-8.0.1-0"
- 故意构造 compiler.log 不含 "Leaving the logs":验证退回用 log_path,failure_log_path=None
- `--src-dir` 测试: 在仓库根跑,`--src-dir` 指向 ffmpeg

### 11.3 不退化 gate

- 整体测试 401 → 应保持或增加(本次会加新测试)
- **workflow 现有调用不破坏**: workflow 还在用 `BuildOptions(output_log=..., cwd=...)` + `result.log_path`,Phase A 必须保留这些 API。验证方式:workflow 现有测试全过。

## 12. 向后兼容(Phase A 关键)

Phase A 只升级 build skill,workflow 不动。所以 build skill API 必须**向后兼容**:

| API | v0.1 | v0.2 Phase A | 变化 |
|-----|------|-------------|------|
| BuildOptions 字段 | conf/arch/output_log/include_all/timeout/gbs_binary/cwd | 同 v0.1 | **不变** |
| BuildResult v0.1 字段 | exit_code/log_path/command/duration_seconds/timed_out | 全保留 | **不变** |
| BuildResult 新字段 | — | failure_log_path/analysis_log_path/package_name(都 default None) | **新增,default None 不破坏现有调用** |
| run_gbs_build 签名 | (options: BuildOptions) -> BuildResult | 同 v0.1 | **不变** |

workflow 现在:
```python
options = BuildOptions(conf=..., arch=..., output_log=compiler_log, cwd=options.src_root, ...)
result = run_gbs_build(options)
result.exit_code  # 仍工作
result.log_path   # 仍工作
```

Phase A 后这些都不变。Phase B 才把 workflow 改成用 `result.analysis_log_path`。

## 13. Phase B 预告(本次不做,但定义清楚)

Phase A merge 后启动 Phase B:

- workflow 调 build skill 后,从 `result.analysis_log_path` 拿日志(代替自己跑 `select_analysis_log`)
- 移除 workflow 的 `select_analysis_log` 函数(BW-M4 d002 引入的)
- A/B/C/D/E 五类真实场景仍正确路由
- 单独 PR + dev_memory

Phase A 实施时遇到任何"顺手优化 workflow"的冲动,**停下**——那是 Phase B。

## 14. 风险

| 风险 | 缓解 |
|------|------|
| gbs 版本差异导致 "Leaving the logs in" 措辞不同 | 正则保守,不匹配则降级用 A(不阻塞 build skill 工作) |
| `--src-dir` 相对路径解析错 | Path(src_dir).resolve() + 验证目录存在 |
| 多 failure log 路径选错 | 取 finditer 最后一次(GBS 构建顺序最后是真失败) |
| 新字段破坏 workflow 调用 | v0.1 字段不改名,新字段 default None,workflow 不感知就忽略 |
| 流式捕获机制改坏 | 不动 v0.1 subprocess + reader,只在 main 末尾加 B 提取 |
