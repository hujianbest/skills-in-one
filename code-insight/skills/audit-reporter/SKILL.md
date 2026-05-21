---
name: audit-reporter
description: Use when a code-audit run needs an Excel workbook after reviewer findings are written or after verifier results are available.
---

# Audit Reporter

把一审 finding 和二审复核结果汇总到 Excel。`audit-reporter` 是 `code-insight` 的唯一报告导出节点，不再生成 HTML。

## When to Use

适用：

- `audit-reviewer` 已写出至少一个 `findings/<module>.json`，需要生成一审草稿 Excel
- `audit-verifier` 已更新 `findings/*.json` 并写出 `confirmed.json`，需要刷新最终 Excel
- 用户要求重算某个 run 的 Excel 报告

不适用：

- 想新增 finding → 回到 `audit-reviewer`
- 想复核 finding 真伪 → 回到 `audit-verifier`
- 想导出 HTML → 本 pack 已移除 HTML export

## Hard Gates

- 只写 `reports/report.xlsx`，不写 `report.html`
- 不修改 `confirmed.json`、`findings/`、`verifications/`
- Excel 是必需产物；缺少 `openpyxl` 必须报错，不得静默跳过
- 一审草稿模式允许 `verifier: {}`，最终模式要求每条 finding 都有完整 `verifier`
- 复核认为不是问题的 finding 必须保留在 Excel 的 `非问题记录` sheet 中
- Excel 面向中文读者，sheet 名、表头、状态说明、统计字段必须使用中文

## Workflow

### 1. 读取输入

公共输入：

- `.garage/code-audit/runs/<run_id>/plan.json`：run meta、module 清单、`review_checklist.categories[]`
- `.garage/code-audit/runs/<run_id>/findings/<module>.json`：一审 finding 和二审原地写回的 `verifier`

最终模式额外输入：

- `.garage/code-audit/runs/<run_id>/confirmed.json`：只含 `confirmed` / `upgrade` / `downgrade` 的 finding

### 2. 选择模式

调用 `scripts/render_xlsx.py`：

```bash
python code-insight/skills/audit-reporter/scripts/render_xlsx.py --run-id <run_id> --mode draft
python code-insight/skills/audit-reporter/scripts/render_xlsx.py --run-id <run_id> --mode final
python code-insight/skills/audit-reporter/scripts/render_xlsx.py --run-id <run_id> --mode auto
```

- `draft`：一审后立即渲染，读取所有 `findings/*.json`，复核状态显示为 `待复核`
- `final`：复核后刷新，要求 `confirmed.json` 存在，并校验其 ID 集合与 `findings/*.json` 中 `verifier.status ∈ {confirmed, upgrade, downgrade}` 一致
- `auto`：有 `confirmed.json` 则走 `final`，否则走 `draft`

### 3. 数据校验

- `category` 必须属于 `plan.review_checklist.categories[].id`；旧 plan 缺失清单时回退 base 11
- `severity` / `confidence` / `verifier.status` 必须是合法 enum
- `line_start <= line_end`
- `evidence` 至少包含 `code_snippet` / `reasoning` / `trigger_conditions` / `expected_vs_actual`
- `reviewer` 至少包含 `agent` / `ts`
- `final` 模式下每条 finding 的 `verifier` 必须包含 `status` / `reason` / `evidence_check` / `agent` / `ts`

### 4. 渲染 Excel

输出固定为：

```text
.garage/code-audit/runs/<run_id>/reports/report.xlsx
```

Workbook sheets：

| Sheet | 内容 |
|---|---|
| `审查结果` | 所有 finding，一审草稿和复核结果都在这里；含中文表头、中文严重级别说明、中文复核状态说明、审查类别说明 |
| `汇总` | 按复核状态、严重级别、审查类别、模块 × 严重级别统计 |
| `运行信息` | run_id、target、profile、review_checklist、生成时间、总数和状态分布 |
| `非问题记录` | `verifier.status = rejected` 的 finding，记录复核理由与核验证据 |
| `待补证据` | `verifier.status = needs_more_evidence` 的 finding，记录还缺哪些证据 |

### 5. 返回结构化摘要

```yaml
run_id: <run_id>
report_path: .garage/code-audit/runs/<run_id>/reports/report.xlsx
mode: draft | final
finding_total: <int>
confirmed_count: <int>
non_issue_count: <int>
needs_more_evidence_count: <int>
by_severity: {critical: N, high: N, medium: N, low: N, info: N}
by_module: {runtime: N, adapter: N}
next_action: done
```

## Output Contract

- 写盘：`reports/report.xlsx`
- 不写：任何 HTML 报告
- 不修改：`confirmed.json` / `findings/` / `verifications/`
- 唯一下一步：`done`

## Red Flags

- 仍然调用旧 HTML 导出脚本或输出 `report.html`
- Excel 表头继续使用英文 key 作为展示名
- `rejected` finding 只保留在 JSON，Excel 里看不到
- 一审草稿因为 `verifier: {}` 被拒绝渲染
- `openpyxl` 缺失时仍声称报告生成成功
- `confirmed.json` 与 `findings/*.json` 的复核状态集合不一致却继续渲染最终 Excel

## Verification

- [ ] `reports/report.xlsx` 已生成且大于 0 字节
- [ ] 一审后调用使用 `--mode draft`，即使 `verifier: {}` 也能生成 Excel
- [ ] 复核后调用使用 `--mode final` 或 `--mode auto`，Excel 已刷新
- [ ] `非问题记录` sheet 包含所有 `verifier.status = rejected` 的 finding
- [ ] `待补证据` sheet 包含所有 `verifier.status = needs_more_evidence` 的 finding
- [ ] sheet 名、表头、状态说明、统计字段为中文

## Reference Guide

| 文件 | 用途 |
|---|---|
| `references/report-schema.md` | Excel 输出格式契约 |
| `scripts/render_xlsx.py` | findings / confirmed.json → report.xlsx |
