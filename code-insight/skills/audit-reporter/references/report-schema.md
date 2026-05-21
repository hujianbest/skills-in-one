# Report Schema - Excel Only

`audit-reporter` 只输出 Excel：`.garage/code-audit/runs/<run_id>/reports/report.xlsx`。HTML export 已移除。

## 模式

| 模式 | 触发时机 | 输入 | 说明 |
|---|---|---|---|
| `draft` | 每次 `audit-reviewer` 写出 `findings/<module>.json` 后 | `plan.json` + `findings/*.json` | 允许 `verifier: {}`，复核状态显示为 `待复核` |
| `final` | `audit-verifier` 写回 verifier 并生成 `confirmed.json` 后 | `plan.json` + `findings/*.json` + `confirmed.json` | 校验 `confirmed.json` 与 `findings/*.json` 的复核状态一致，然后刷新 Excel |
| `auto` | 重渲染 | 同上 | 有 `confirmed.json` 则 `final`，否则 `draft` |

## Workbook

### Sheet 1: `审查结果`

所有 finding 都在本 sheet 中展示。一审阶段展示草稿，复核后展示最终状态；被复核为非问题的记录不会丢失。

| 列 | 表头 | 来源 |
|---|---|---|
| A | 发现ID | `id` |
| B | 模块 | `module` |
| C | 文件 | `file` |
| D | 起始行 | `line_start` |
| E | 结束行 | `line_end` |
| F | 位置 | `<file>:<line_start>-<line_end>` |
| G | 标题 | `title` |
| H | 审查类别 | `category` |
| I | 审查类别说明 | `plan.review_checklist.categories[].description` |
| J | 严重级别 | `severity` |
| K | 严重级别说明 | `critical=严重 / high=高 / medium=中 / low=低 / info=提示` |
| L | 置信度 | `confidence` |
| M | 置信度说明 | `high=高 / medium=中 / low=低` |
| N | 复核状态 | `verifier.status`；草稿为 `draft` |
| O | 复核状态说明 | `待复核 / 已确认 / 非问题 / 已确认-严重级别上调 / 已确认-严重级别下调 / 证据不足` |
| P | 问题描述 | `description` |
| Q | 证据代码 | `evidence.code_snippet` 前 500 字符 |
| R | 审查推理 | `evidence.reasoning` |
| S | 触发条件 | `evidence.trigger_conditions` |
| T | 预期与实际 | `evidence.expected_vs_actual` |
| U | 建议修复 | `suggested_fix` |
| V | 一审Agent | `reviewer.agent` |
| W | 一审时间 | `reviewer.ts` |
| X | 复核理由 | `verifier.reason` |
| Y | 复核核验证据 | `verifier.evidence_check` |
| Z | 调整前严重级别 | `severity_before` |

格式要求：

- 第 1 行冻结并开启筛选
- 表头为中文
- `严重级别` 单元格按 severity 着色
- `复核状态` 单元格按 status 着色
- 长文本自动换行

### Sheet 2: `汇总`

包含以下统计块：

- 按复核状态统计：`draft` / `confirmed` / `rejected` / `upgrade` / `downgrade` / `needs_more_evidence`
- 按严重级别统计：`critical` / `high` / `medium` / `low` / `info`
- 按审查类别统计：动态来自 `plan.review_checklist.categories[].id`
- 按模块和严重级别统计：模块 × severity 透视表

### Sheet 3: `运行信息`

key-value 表，字段名使用中文：

| 字段 | 说明 |
|---|---|
| 报告模式 | `一审草稿` 或 `复核后最终结果` |
| run_id | 当前 run ID |
| 审查目标 | `plan.target` |
| 生成时间 | UTC ISO 8601 |
| pack_version | code-insight pack version |
| 项目语言 / 项目架构 / 框架 / 风险关注点 | 来自 `plan.profile` |
| 项目画像是否人工确认 | `plan.profile.user_confirmed` |
| 审查清单 preset | `plan.review_checklist.preset` |
| 审查类别数量 | `len(plan.review_checklist.categories)` |
| 审查清单是否人工确认 | `plan.review_checklist.user_confirmed` |
| 一审 finding 总数 | 所有 `findings/*.json` 的 finding 数 |
| 复核确认问题数 | `status ∈ {confirmed, upgrade, downgrade}` |
| 复核认为非问题数 | `status = rejected` |
| 仍需补证据数 | `status = needs_more_evidence` |
| 模块数量 | `len(plan.modules)` |

### Sheet 4: `非问题记录`

记录所有 `verifier.status = rejected` 的 finding。该 sheet 是审计完整性要求，不能省略。

| 表头 | 来源 |
|---|---|
| 发现ID | `id` |
| 模块 | `module` |
| 文件 | `file` |
| 位置 | `<file>:<line_start>-<line_end>` |
| 标题 | `title` |
| 审查类别 | `category` + 类别说明 |
| 严重级别 | `severity` |
| 复核状态 | 中文状态说明 |
| 复核理由 | `verifier.reason` |
| 复核核验证据 | `verifier.evidence_check` |
| 原问题描述 | `description` |

### Sheet 5: `待补证据`

记录所有 `verifier.status = needs_more_evidence` 的 finding，字段与 `非问题记录` 相同。

## 校验规则

### draft

- `findings/*.json` 必须是 JSON array
- 每条 finding 必须有完整一审字段
- `verifier` 必须存在且为 object，允许为空 `{}`
- `category` 必须属于当前 run 的 review checklist；旧 plan 缺失 checklist 时回退 base 11

### final

- 满足 draft 的所有规则
- 每条 finding 的 `verifier` 必须含 `status` / `reason` / `evidence_check` / `agent` / `ts`
- `confirmed.json` 必须存在且为 JSON array
- `confirmed.json` 的 ID 集合必须等于 `findings/*.json` 中 `status ∈ {confirmed, upgrade, downgrade}` 的 ID 集合
- `rejected` 和 `needs_more_evidence` 不进入 `confirmed.json`，但必须进入 Excel 的对应 sheet

## 行号文本协议

`位置` 使用 `<file>:<line_start>-<line_end>`，便于复制到 IDE 或命令行中定位。
