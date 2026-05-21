# Code Insight 存量代码审查

`code-insight` 是一套面向存量代码的两阶段审查 skill / agent 包。目标是先按模块发现潜在 bug，再由独立复核 agent 逐条确认，最后输出一份中文 Excel 审查工作簿。

本包只做审查与记录，不修改业务代码。

## 目录结构

```text
code-insight/
  agents/
    code-audit-reviewer.md    # 一审编排：画像、清单、切模块、逐模块审查
    code-audit-verifier.md    # 二审编排：独立复核、刷新最终 Excel
  skills/
    audit-planner/                  # 识别项目画像并生成 plan.json
    audit-reviewer/                 # 单模块一审，写 findings/<module>.json
    audit-verifier/                 # 独立复核，写 verifier、verifications、confirmed.json
    audit-reporter/                 # 生成 reports/report.xlsx
```

## 工作流

### 1. 一审：生成 finding 草稿

首次运行 `code-audit-reviewer` 时，它会：

1. 识别项目语言、架构、框架和风险关注点。
2. 与用户确认审查清单 `review_checklist`。
3. 按目录树切分模块，写入 `plan.json` 和 `task.md`。
4. 每个新会话只审一个模块，写入 `findings/<module>.json`。
5. 模块审完后立即刷新草稿 Excel：`reports/report.xlsx`。

示例：

```text
请用 code-audit-reviewer 审查 src/
请用 code-audit-reviewer --resume run <run_id> 处理下一个模块
```

### 2. 二审：独立复核并刷新最终 Excel

所有模块一审完成后，在新会话启动 `code-audit-verifier`：

```text
请用 code-audit-verifier 复核 run <run_id>，刷新 Excel 报告
```

二审会：

1. 重新读取源代码和 finding 证据。
2. 为每条 finding 写入 `verifier.status`、`reason`、`evidence_check`。
3. 写入 `verifications/<module>.json`。
4. 原地更新 `findings/<module>.json`。
5. 将确认成立的问题合并到 `confirmed.json`。
6. 刷新最终 Excel：`reports/report.xlsx`。

## 产物路径

所有产物位于：

```text
.garage/code-audit/runs/<run_id>/
  plan.json
  task.md
  findings/
    <module>.json
  verifications/
    <module>.json
  confirmed.json
  reports/
    report.xlsx
  audit-log.jsonl
```

## Excel 报告

HTML export 已移除，唯一报告产物是：

```text
.garage/code-audit/runs/<run_id>/reports/report.xlsx
```

Excel 分两次刷新：

- 一审后：`audit-reporter --mode draft`，展示所有 finding 草稿，复核状态为 `待复核`。
- 复核后：`audit-reporter --mode final`，展示最终复核状态，并记录非问题和待补证据。

工作簿包含：

| Sheet | 内容 |
|---|---|
| `审查结果` | 所有 finding，含中文表头、审查类别说明、严重级别说明、复核状态说明 |
| `问题总结` | 对发现的问题做独立汇总：总数、按严重级别/模块/类别统计、重点问题列表 |
| `汇总` | 按复核状态、严重级别、审查类别、模块统计 |
| `运行信息` | run_id、target、profile、review_checklist、数量分布 |
| `非问题记录` | 复核认为不是问题的 finding，即 `verifier.status = rejected` |
| `待补证据` | 复核认为证据不足的 finding，即 `verifier.status = needs_more_evidence` |

## 复核状态

| status | 中文含义 | 是否进入 `confirmed.json` | Excel 记录位置 |
|---|---|---|---|
| `confirmed` | 已确认 | 是 | `审查结果` |
| `upgrade` | 已确认，严重级别上调 | 是 | `审查结果` |
| `downgrade` | 已确认，严重级别下调 | 是 | `审查结果` |
| `rejected` | 非问题 / 误报 | 否 | `审查结果` + `非问题记录` |
| `needs_more_evidence` | 证据不足 | 否 | `审查结果` + `待补证据` |

## 手动重渲染 Excel

```bash
python code-insight/skills/audit-reporter/scripts/render_xlsx.py --run-id <run_id> --mode draft
python code-insight/skills/audit-reporter/scripts/render_xlsx.py --run-id <run_id> --mode final
python code-insight/skills/audit-reporter/scripts/render_xlsx.py --run-id <run_id> --mode auto
```

`openpyxl` 是必需依赖。缺失时 Excel 不会被视为成功生成。

## 关键约束

- 一审和二审必须使用新会话隔离上下文。
- 一审每次只处理一个模块，不在同一会话连续扫多个模块。
- 二审不新增 finding，不修改 reviewer 的 `description`、`evidence`、`category`。
- `rejected` 不代表删除记录，必须保留在 JSON 和 Excel 中。
- finding JSON 中面向人工阅读的自然语言字段必须使用中文，包括问题标题、问题描述、证据推理、触发条件、预期与实际、建议修复、复核理由和复核核验证据。
- Excel 中面向人工阅读的描述、表头和状态说明必须使用中文。
