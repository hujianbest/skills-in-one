# mdc-bug-patterns — 使用说明

> C/C++ 嵌入式代码 Bug 模式审计 skill，用 LLM 做单元级别深度复核 + 子代理独立复核 + 中文 Excel 报告 + 长跑可恢复。

本 README 面向**人类用户**。给 agent 看的版本是 [`SKILL.md`](SKILL.md)（agent 在匹配到 skill 时自动读入）。

---

## 简介

| 它能做 | 它不能做 |
|---|---|
| 对 C/C++（含嵌入式 / 裸机 / RTOS）代码做内存安全 / 锁使用 / 并发 ISR / 资源外设 / 整数逻辑 / 硬件硬域的 bug 模式审计 | 替代真正的静态分析（clang-tidy / cppcheck / coverity）—— 它和这些是互补的 |
| 在大仓库 / 大量代码上跑数小时（甚至过夜），失败可恢复 | 修复 bug —— 只输出发现 + 修复建议 + 子代理复核 + 人工确认下拉 |
| 给评审者一份中文 Excel：`严重程度` 色码、`文件 + 行号 + 问题说明` 三联列、`子代理复核结论`（独立 AI 二次复核）、`人工确认` 下拉 | 跑 C/C++ 之外的语言（templates 是 C/C++ 嵌入式视角） |

**典型用户流程**：

1. 启动 cloud agent / 本地 agent，告诉它"用 mdc-bug-patterns 审 src/io/ 的锁使用和并发"。
2. agent 跑 5-pass 流程；如果是长跑，自动用 `scripts/run_audit.py` 做 checkpoint。
3. 跑完得到 `audit/bug_report.xlsx`。打开看 `发现明细` 表，逐行复核，在 `人工确认` 列填 ✓/✗/?，在 `备注` 写理由。
4. 跟开发者讨论修复。

---

## 前置依赖

| 工具 | 用途 | 是否必需 | 安装 |
|---|---|---|---|
| Python ≥ 3.10 | 跑所有 `scripts/*.py` | 必需 | 系统自带 / `pyenv` |
| ripgrep (`rg`) | Pass 2 候选扫描 | 必需 | `apt install ripgrep` |
| `openpyxl` | 生成 Excel | 必需 | `pip install openpyxl` |
| `tokei` 或 `cloc` | Pass 1 LoC 统计 | 可选（fallback `find ... | wc -l`） | `apt install tokei` |
| `tmux` | 长跑 conductor 的 SSH-drop 防护 | 长跑时强烈推荐 | `apt install tmux` |
| `git` | 可选 `--auto-commit` checkpoint | 可选 | 系统自带 |
| LibreOffice | 验证 Excel（人手开 Excel/Calc 也行） | 可选 | `apt install libreoffice-calc` |

---

## 快速开始（5 分钟）

适合**几十到几百 LoC 的小范围 / PR 级审计**。长跑请直接看下面的"长跑过夜审计"。

```bash
# 0. 进入 skill 目录
cd skills/mdc-bug-patterns

# 1. 看看有哪些专项 + 模板
scripts/scan_candidates.py --list          # 列出 6 个专项 / 61 个模板

# 2. 决定审什么 —— 比如「锁使用」
SCOPE=/path/to/repo/src/io
SPECIALTY=lock-usage
mkdir -p /tmp/audit-demo

# 3. Pass 2: 跑 rg 候选 + 排序成单元工作队列
scripts/scan_candidates.py --specialty $SPECIALTY --path $SCOPE --out /tmp/audit-demo/candidates.jsonl
scripts/list_units.py --candidates /tmp/audit-demo/candidates.jsonl --path $SCOPE --format table | head -30

# 4. Pass 3: 由 LLM agent 逐个单元深读 + 应用 specialty 模板
#    (这一步 cloud agent 自动做; 手工跑时, 评审者按 list_units 输出顺序读单元 + 写 findings JSON)

# 5. Pass 3.5: 子代理独立复核
#    (派发 Task 子代理; 见 references/second-pass-review.md)

# 6. Pass 4: 渲染 Excel
scripts/excel_helper.py \
    --bugs-file findings_with_review.json \
    --coverage  coverage.json \
    --repo "myorg/myrepo" --scope "src/io/" --reviewer "alice" \
    --output bug_report.xlsx

# 7. 用 LibreOffice / Excel 打开 bug_report.xlsx, 在「发现明细」页逐条复核
```

---

## 5-pass workflow

```
Pass 1   Map + Specialty selection      读 references/templates.md 决策树
                                        选 1-2 个专项文件加载
Pass 2   Prioritise units               scan_candidates → list_units
                                        rg 候选 → 按 suspicion score 排序
Pass 3   Unit-by-unit deep review       LLM 端到端读每个单元, 应用专项 templates
                                        作为 checklist (tokens-for-quality)
Pass 3.5 Second-pass subagent review    独立 Task subagent 重读源码、re-derive
                                        verdict (agree / disagree / uncertain)
Pass 4   Report                         中文 4-sheet Excel, 17 列, 人工确认下拉
```

详细方法论：[`references/methodology.md`](references/methodology.md)。

---

## 文件结构

```
skills/mdc-bug-patterns/
├── README.md                     ← 本文档 (面向人类)
├── SKILL.md                      ← 给 agent 读的 skill 定义 (frontmatter + 5-pass)
├── references/
│   ├── methodology.md            ← 5-pass 操作细则 (Map / Prioritise / Unit Review / Concurrency Deep Dive)
│   ├── templates.md              ← 6 专项的索引 + 决策树 + 锁使用速查表
│   ├── templates/
│   │   ├── memory-safety.md      ← 16 模板: heap/stack/buffer/pointer/DMA
│   │   ├── lock-usage.md         ← 11 模板: mutex/lock_guard/critical-section
│   │   ├── concurrency-and-isr.md← 8 模板:  非锁同步/atomic/volatile/ISR/RTOS API
│   │   ├── resource-management.md← 7 模板:  fd/外设时钟/RTOS task/HW timer/NVIC
│   │   ├── logic-and-numeric.md  ← 13 模板: int/移位/字节序/位域/packed struct
│   │   └── embedded-hardware.md  ← 6 模板:  watchdog/低功耗/MMIO RMW/Flash
│   ├── false-positive-filters.md ← 跨专项 fp.* 过滤器 (fp.ownership.smart-pointer 等)
│   ├── second-pass-review.md     ← Pass 3.5 子代理 prompt 模板 + verdict schema
│   ├── reporting.md              ← finding JSON schema + 17 列 Chinese Excel 详解
│   ├── long-running-audits.md    ← 长跑可恢复协议 (read me before any multi-hour run)
│   └── opencode-integration.md   ← 在 opencode 中跑 (装 skill + tmux + serve + driver) ★
└── scripts/
    ├── scan_candidates.py        ← Pass 2: rg 候选 → JSONL
    ├── list_units.py             ← Pass 2: 候选聚合到 unit (function/file) + 排序
    ├── coverage_tracker.py       ← Pass 2/3/4: per-candidate 状态簿记
    ├── merge_second_pass.py      ← Pass 3.5: 合并子代理 verdicts 到 findings.json
    ├── excel_helper.py           ← Pass 4: 渲染中文 4-sheet Excel
    ├── run_audit.py              ← 长跑 conductor: init/next/record/.../finalize
    └── audit-overnight-opencode.sh ← 一行启动 opencode 过夜审计 (tmux + serve + driver) ★
```

---

## 4 个常用使用场景

### 场景 1: PR-level 快速审 (单文件 / 几十 LoC)

```bash
# 直接让 agent 自由跑, 不用 run_audit.py
# agent 内部执行: scan → 自己写 findings → 子代理复核 → excel_helper 渲染
```

或者评审者手工：

```bash
SPEC=memory-safety SCOPE=path/to/changed_file.cc
scripts/scan_candidates.py --specialty $SPEC --path $SCOPE --out /tmp/c.jsonl
scripts/list_units.py --candidates /tmp/c.jsonl --path $SCOPE --format table
# 人按顺序读单元, 手写 findings JSON (按 references/reporting.md 的 schema)
scripts/excel_helper.py --bugs-file findings.json --output bug_report.xlsx
```

### 场景 2: 长跑过夜审计 (大仓库, 数小时)

**用 `scripts/run_audit.py`**，可恢复，挂了不丢已审单元。详细协议在 [`references/long-running-audits.md`](references/long-running-audits.md)；如果你用的是 [opencode](https://opencode.ai)，可以直接用现成的 `scripts/audit-overnight-opencode.sh` 启动整夜跑（详见 [`references/opencode-integration.md`](references/opencode-integration.md)）。

```bash
# 1) 初始化 (一次性)
scripts/run_audit.py init \
    --scope src/ \
    --specialty lock-usage --specialty concurrency-and-isr \
    --repo "myorg/myrepo" --reviewer "auto-overnight" \
    --out audit/

# 2) 在 tmux 中跑 cloud agent 主循环 (snippet 在 long-running-audits.md)
tmux new-session -d -s mdc-audit -- bash -lc '
    while true; do
        # cloud agent 内部:
        #   while True:
        #       unit = run_audit.py next --out audit/
        #       if no unit: break
        #       findings = LLM_review(unit)
        #       run_audit.py record --unit-id <id> --findings <path> --out audit/
        #   while True:
        #       finding = run_audit.py next-verdict --out audit/
        #       if no finding: break
        #       verdict = subagent_review(finding)
        #       run_audit.py record-verdict --finding-id <id> --verdict <path> --out audit/
        sleep 60
    done | tee -a audit/runner.log
'

# 3) 随时检查进度
scripts/run_audit.py status --out audit/
# audit/  (started 2026-05-14 22:13)
#   units:    pending=183 / in-progress=1 / done=412 / failed=4 / total=600
#   verdicts: pending= 87 / done=329 / total=416
#   duration: 6h 47m
#   ETA:      ~2h 30m
#   partial:  audit/partial_reports/bug_report-2026-05-15T03-12-44Z.xlsx (12 min ago)

# 4) 中途想看现在的中间结果? 直接打开最新 partial:
ls -lt audit/partial_reports/ | head -3

# 5) 跑完, 渲染最终报告
scripts/run_audit.py finalize --out audit/
# → audit/bug_report.xlsx
```

**用 opencode 整夜跑的极简方式** (一行启动 + 关电脑去睡):

```bash
# 0) 一次性
scripts/run_audit.py init --scope src/ \
    --specialty lock-usage --specialty concurrency-and-isr \
    --repo "myorg/myrepo" --reviewer "auto-overnight" \
    --out audit/

# 1) 启 tmux + opencode serve + Pass 3 / Pass 3.5 driver loop + finalize
scripts/audit-overnight-opencode.sh audit/

# 早上回来:
scripts/run_audit.py status --out audit/        # 看进度
ls -t audit/partial_reports/ | head -3           # 最新部分 Excel
# 如果跑完了, audit/bug_report.xlsx 就是终稿
```

详见 [`references/opencode-integration.md`](references/opencode-integration.md) — 包含安装到 opencode、tmux + serve 架构、prompt 模板、retry/timeout、model 选择 (e.g. Pass 3 用 sonnet, Pass 3.5 用 haiku)、opencode 非交互权限规则等 gotchas。

**Cloud agent 重启 / 上下文爆掉时**：新 agent 看到 `audit/HOWTO_RESUME.md` 就**绝不再 init**，先 `status` → 然后从 `next` 继续。任何 `audit/findings/<unit-id>.json` 已存在的单元就是已审完，不重复审。

### 场景 3: 单专项审计 (只查一类问题)

例如"只审锁使用"：

```bash
scripts/scan_candidates.py --specialty lock-usage --path src/ --out cand.jsonl
# 11 模板的候选都带 specialty=lock-usage 字段
```

LLM 只加载 `references/templates/lock-usage.md`（~12 KB）+ 索引（~16 KB）= ~28 KB，远低于全量加载。

### 场景 4: 综合审计 (load 全部 6 专项)

```bash
scripts/run_audit.py init --scope src/ --out audit/      # 不传 --specialty
# = 加载全部 6 专项 / 61 模板
# token 消耗较高, 仅在没有明确范围 / 需要广撒网时使用
```

---

## CLI 速查

| 脚本 | 子命令 | 用途 | 例子 |
|---|---|---|---|
| `scan_candidates.py` | (default) | rg 候选 → JSONL | `--path src/ --out c.jsonl` |
| | `--list` | 列出全部模板（按专项分组） | `--list` |
| | `--specialty NAME` | 只跑某专项的模板 | `--specialty lock-usage` |
| | `--template ID` | 只跑某一个模板 | `--template con-try-lock-no-check` |
| | `--dry-run` | 只打印 rg 命令不执行 | |
| `list_units.py` | (default) | 候选聚合到单元 + 按 suspicion 排序 | `--candidates c.jsonl --path src/` |
| | `--format table` | 人读表格输出 | |
| | `--top N` | 只输出前 N 单元 | `--top 50` |
| `coverage_tracker.py` | `register --candidates F` | 把候选注册到 coverage.json | |
| | `mark --id ID --status STATUS` | 标记 confirmed/suppressed/inconclusive | `--filter fp.ownership.smart-pointer` |
| | `summary` | 按模板的覆盖率表 | |
| | `audit-gaps` | 列出 inconclusive + 未标记 | |
| | `findings --out F` | 导出已确认 findings | |
| `merge_second_pass.py` | (default) | 合并 verdicts 到 findings.json | `--findings F --verdicts V --out OUT` |
| `excel_helper.py` | (default) | 渲染中文 4-sheet Excel | `--bugs-file F --output report.xlsx` |
| | `--coverage F` | 用 coverage.json 填覆盖率页 | |
| | `--repo / --scope / --reviewer` | 元数据写到「审查总览」 | |
| `run_audit.py` | `init` | 一次性建审计目录 (Pass 1+2) | `--scope src/ --specialty NAME --out audit/` |
| | `status` | 进度 + ETA | |
| | `next` | 下一个 pending unit (JSON) | |
| | `record --unit-id ID --findings F` | 原子记录该单元的 findings | |
| | `next-verdict` / `record-verdict` | Pass 3.5 同形 | |
| | `partial` | 立即生成部分 Excel | |
| | `finalize` | 生成最终 Excel | |
| | `mark --unit-id ID --status STATUS` | 手动改单元状态 | |
| | `reset-unit --unit-id ID` | 把某单元重新放回 pending | |
| `audit-overnight-opencode.sh` | (default) | 一键启动 opencode 过夜审计 (tmux + serve + driver loop + finalize) | `audit-overnight-opencode.sh audit/ --port 4096 --model anthropic/claude-sonnet-4` |

所有脚本都支持 `--help`。

---

## 专项文件速查

| 加载场景 | 专项文件 | 模板数 | 大小 |
|---|---|---|---|
| 内存/堆/栈/buffer/指针/DMA | `templates/memory-safety.md` | 16 | 20 KB |
| **锁/mutex/lock_guard/临界区** | `templates/lock-usage.md` | 11 | 12 KB |
| 非锁并发/atomic/volatile/ISR/RTOS | `templates/concurrency-and-isr.md` | 8 | 12 KB |
| 资源/外设生命周期 (非 mutex) | `templates/resource-management.md` | 7 | 8 KB |
| 整数/字节序/位域/可移植性 | `templates/logic-and-numeric.md` | 13 | 12 KB |
| 看门狗/低功耗/MMIO RMW/Flash | `templates/embedded-hardware.md` | 6 | 8 KB |
| **索引** (始终首先读入) | `templates.md` | — | 16 KB |

**典型加载量**：索引 + 1 专项 ≈ 24-32 KB。最常见 pairing「锁 + 并发」≈ 44 KB。全量 ≈ 90 KB。

完整决策树见 [`references/templates.md`](references/templates.md) 顶部的 "How to choose a specialty"。

---

## 输出产物

### Excel 报告（核心交付物）

`audit/bug_report.xlsx`，4 个 sheet，全中文表头：

| Sheet | 内容 |
|---|---|
| `审查总览` | 仓库 / 范围 / 审计人 / 时间 / 模板数 + 按严重程度的发现统计 + 子代理复核统计 + 8 步阅读指引 |
| `发现明细` | 高/中可信发现，**17 列**，行高自适应。冻结 `编号 + 严重程度` 两列，所有列 autofilter |
| `审计盲区` | 低可信 / 不确定 / 未复核项，同样 17 列，备注预填原因 |
| `覆盖率明细` | 按模板（候选 / 已确认 / 已抑制 / 不确定 / 覆盖率）+ 按文件（高/中/低/总）双表 |

**`发现明细` 的 17 列**：
```
编号 → 严重程度 → 可信度 → 类别 → 模板ID
     → 文件 → 行号 → 问题说明 (具体问题是什么) → 所在函数
     → 证据 (file:line + 代码) → 已排除的误报模式 → 修复建议 → 代码上下文
     → 子代理复核结论 → 子代理复核依据
     → 人工确认 → 备注
```

`文件 + 行号 + 问题说明` 是视觉相邻三联列：评审者看到位置后立即看到问题描述。`人工确认` 是下拉（✓ 同意 / ✗ 误报 / ? 待定），`子代理复核结论` 用绿/红/黄/灰独立色码（与严重色码独立）。

详见 [`references/reporting.md`](references/reporting.md)。

### 长跑产物（`audit/`）

```
audit/
├── meta.json              # 不变: 审计元数据
├── candidates.jsonl       # Pass 2 原始候选
├── units.jsonl            # Pass 2 排序的单元工作队列
├── state.json             # 状态簿记 (原子写, 每 unit / verdict 更新)
├── findings/<unit>.json   # 每单元的 findings (原子写)
├── verdicts/<id>.json     # 每条 finding 的子代理复核 (原子写)
├── heartbeat.txt          # <pid> <iso-ts> <last-action>
├── runner.log             # 追加式日志
├── partial_reports/       # 滚动 Excel 快照 (每 50 单元 / 30 分钟)
├── bug_report.xlsx        # 最终报告 (finalize 产出)
└── HOWTO_RESUME.md        # init 自动生成, 给"被替换的新 agent"读
```

---

## FAQ

**Q: 跑了一半 cloud agent 重启了 / 网断了 / 上下文爆了, 怎么办?**

A: 进 workspace, `cd` 到 audit 目录, 跑 `scripts/run_audit.py status --out audit/` 看进度。然后让新的 agent 实例从 `next` 继续。任何已经写到 `audit/findings/<unit>.json` 的单元都不会被重审。详见 [`references/long-running-audits.md`](references/long-running-audits.md)。

**Q: 我想中途看一下现在的中间结果**

A: `ls -lt audit/partial_reports/` 找最近的 `bug_report-<ts>.xlsx`，直接开。每 50 单元 / 30 分钟自动滚动一份。

**Q: 子代理复核结论有几个 finding 是 `反对 (误报)`，要怎么处理?**

A: 这是 Pass 3.5 设计的核心价值——独立 AI 抓出主 agent 没排除掉的 FP filter (例如忘了 `fp.test-code`、`fp.generated-code`)。打开 `子代理复核依据` 列看它的反对理由 + supporting_evidence，再决定是否在 `人工确认` 填 `✗ 误报`。

**Q: 模板太详细了, 我能不能更简化?**

A: 模板已经是 Option B 瘦身后的「discipline contract」格式 —— 没有 pattern teaching 和示例代码，只剩 `id + severity + what + detection_query + fp_filters + verification + required_evidence + confidence + fix`。如果还想更激进，删掉 `verification` 步骤和 `required_evidence` 是可以的，但你会失去「auditable findings」的保证。

**Q: 我的代码不是 C/C++ 嵌入式怎么办?**

A: 当前所有 templates 都假设 C/C++ 语义（`new`/`delete`、`std::mutex`、CMSIS 头文件等）。其它语言需要新写 specialty 文件 + 适配 detection_query。Linux 内核 / 普通 Linux 应用大部分模板仍适用（去掉 `isr-*` / `rtos-*` / `emb-*` 前缀的）。

**Q: 我能不能只跑 rg 候选, 不跑 LLM 复核, 当个 fancy grep 用?**

A: 可以。`scripts/scan_candidates.py --specialty <NAME> --path <SCOPE>` 直接输出 JSONL 候选；不要 Pass 3 / Pass 3.5。但你只会得到「rg 找到的 file:line 列表」，没有 LLM 判断、没有 FP 排除、没有证据收集。本 skill 的核心价值是 LLM 单元复核 + 子代理二次复核，跳过这两步等于退化成 grep。

**Q: `--auto-commit` 是什么时候用?**

A: 默认关。当你担心 cloud agent 的 workspace 整个被擦（不只是 VM 重启而是 workspace 重置）时打开。每完成 K 单元自动 `git commit` 到当前分支，最坏情况下从 git remote 都能恢复。代价是 git 历史会被 audit checkpoint 污染。

**Q: 报告里 `人工确认` 列下拉为啥是 `✓ 同意 (确认是bug)` / `✗ 误报 (附理由)` / `? 待定` 三个值?**

A: 这是 `excel_helper.py` 用 `openpyxl.DataValidation` 内嵌进 Excel 的，不是宏。在 Excel / LibreOffice Calc 里直接是下拉框；填别的值会被拒绝。

**Q: 我自己改了模板格式，现在 `scan_candidates.py --list` 看不到我的模板**

A: 解析器只识别两个东西：`### \`<id>\`` 形式的标题、`**detection_query:**` 后跟 ```bash 块。其它字段格式可以随便改。如果你的标题是 `### \`my-template\` (critical)` 这样有尾巴的，把括号去掉，把 severity 放到下一行 `- **severity:** critical`。

---

## 延伸阅读

| 想了解 | 读 |
|---|---|
| 5-pass 工作流的操作细则 | [`references/methodology.md`](references/methodology.md) |
| 6 个专项的决策树 + 锁使用速查 | [`references/templates.md`](references/templates.md) |
| 单个模板的契约 schema | 任意 `references/templates/*.md` |
| 跨专项的 false-positive 过滤器 | [`references/false-positive-filters.md`](references/false-positive-filters.md) |
| Pass 3.5 子代理的 prompt 模板 + verdict schema | [`references/second-pass-review.md`](references/second-pass-review.md) |
| Excel 报告的 finding JSON schema + 17 列详解 | [`references/reporting.md`](references/reporting.md) |
| 长跑 / 过夜 / 可恢复审计的运行手册 | [`references/long-running-audits.md`](references/long-running-audits.md) |
| 在 opencode 中跑 (装 skill + tmux + serve + driver) | [`references/opencode-integration.md`](references/opencode-integration.md) |
| Skill 本身的 frontmatter / 哲学 / Iron Rule | [`SKILL.md`](SKILL.md) |
