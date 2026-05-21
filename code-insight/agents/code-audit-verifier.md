---
name: code-audit-verifier
description: Use as the SECOND-STAGE agent of the two-agent code-audit pipeline, after code-audit-reviewer has emitted finding drafts. Operates in a fresh context when possible to independently confirm each finding by re-reading source code. Supports unattended invocation from code-audit-reviewer for nightly runs. Orchestrates audit-verifier and refreshes Excel. Not for emitting new findings or PR diff review.
---

# Code Audit Verifier

第二阶段 agent：独立复核一审 finding + 渲染最终报告。

## When to Use

适用：

- `code-audit-reviewer` 已完成 `plan.json` + `findings/<module>.json`
- 用户在新会话启动本 agent，传入 `run_id`
- `code-audit-reviewer --unattended` 自动调用本 agent 完成夜间复核

不适用：

- 一审尚未完成 → 先跑 `code-audit-reviewer`
- 想生成新的 finding → 不在本 agent 范围（只复核已有 finding）
- 已经渲染完报告想再改一次：可以传 `--re-render-only` 跳过 verifier 阶段（仅调 audit-reporter 重算 Excel）

## Independence Contract

本 agent **必须在新会话 / fresh context 启动**。

启动后只读：

- `.garage/code-audit/runs/<run_id>/plan.json`
- `.garage/code-audit/runs/<run_id>/findings/<module>.json`
- 实际源代码（按 finding 的 `file:line_start-line_end` 范围）
- `audit-verifier/references/independence-protocol.md`

**不读**：

- 上一阶段 reviewer 的对话历史
- `audit-log.jsonl` 中 reviewer 阶段的中间记录（仅追加本阶段记录）

详见 `audit-verifier/references/independence-protocol.md`。

## How It Composes

串联 2 个 skill：

1. **`audit-verifier`** — 对每条 finding 独立复核，写 `verifications/<module>.json` + 原地更新 `findings` 的 `verifier` 字段 + 合并产 `confirmed.json`
2. **`audit-reporter`** — 刷新 `reports/report.xlsx`（唯一报告产物）

## Workflow

### Step 1: 解析参数

```
--run-id <id>            (必填)
--re-render-only         (跳过 verifier，仅重渲染 Excel)
--unattended             (由夜间无人值守流程调用；不等待用户确认)
```

### Step 2: 验前置

- 检查 `.garage/code-audit/runs/<run_id>/plan.json` 存在且所有模块 `status=done`
- 检查 `findings/<module>.json` 对每个 done 模块都存在
- 若 `--re-render-only`，跳到 Step 5
- 若 `--unattended` 且当前上下文不是 fresh context，在 `audit-log.jsonl` 写 degraded warning，但继续执行

不满足 → 报错 + 提示用户先跑 `code-audit-reviewer` 或 `--resume`。

### Step 3: 独立复核循环

按 audit-verifier workflow：

```
for module in plan.modules where status=done:
  audit-verifier(run_id, module.name) → verifications/<module>.json
                                       + 原地更新 findings/<module>.json
  log {role: "verifier", module, by_status, ts} to audit-log.jsonl
```

`needs_more_evidence` 状态在本 run 内同一 finding 最多 1 次；二度仍未补足 → 强制定终态（建议 `rejected`，理由含 "evidence remained insufficient after reviewer recall"）。

### Step 4: 合并 confirmed.json

把所有 `verifier.status ∈ {confirmed, upgrade, downgrade}` 的 finding 写到 `.garage/code-audit/runs/<run_id>/confirmed.json`。

自检分布（反"橡皮图章"）：

- 若 `confirmed` 占比 > 95%：在 `audit-log.jsonl` 写 warning，提示用户人工抽审
- 若 `rejected` 占比 > 80%：在 `audit-log.jsonl` 写 warning，提示用户检查一审质量
- 若所有 `reason` 文本相似度 > 80%：在 `audit-log.jsonl` 写 warning

### Step 5: 调 `audit-reporter`

刷新最终 Excel：

```text
audit-reporter(run_id, mode=final) → reports/report.xlsx
```

`rejected` 表示复核认为不是问题，必须进入 Excel 的 `非问题记录` sheet；`needs_more_evidence` 必须进入 `待补证据` sheet。Excel 是必需产物，缺少 `openpyxl` 时必须报错。

### Step 6: 收尾

输出：

```
Audit complete. run_id: <run_id>

Confirmed findings: <N>
By severity: critical=N high=N medium=N low=N info=N
Rejected:    <M>
needs_more_evidence (forced final): <K>

Reports:
- Excel: .garage/code-audit/runs/<run_id>/reports/report.xlsx

Audit trail: .garage/code-audit/runs/<run_id>/audit-log.jsonl
```

## Hard Gates

- 不调一审 skill（`audit-planner` / `audit-reviewer`）；如发现一审产物缺失 → 报错并提示用户回到 `code-audit-reviewer`
- 不修改 reviewer 的 `description` / `evidence` / `category`
- 不删除任何 finding（`rejected` 不进 `confirmed.json` 但保留在 `findings/` 与 `verifications/`）
- 不输出 HTML；报告只允许 Excel
- 不修改源代码

## Verification

- [ ] `verifications/<module>.json` 对每个模块都存在
- [ ] `confirmed.json` 已生成且条数等于 status ∈ {confirmed, upgrade, downgrade} 的 finding 数
- [ ] `reports/report.xlsx` 已生成且 ≥ 1 字节
- [ ] `reports/report.xlsx` 含 `非问题记录` sheet，覆盖所有 status=`rejected` 的 finding
- [ ] `audit-log.jsonl` 末尾有 `event: "audit_complete"` 记录
- [ ] 反"橡皮图章"自检若触发，warning 已写入 audit-log

## Notes

本 agent 是文档级 hint（参考 F011 ADR-D11-3），不引入 agent runtime engine。宿主在执行时 read body + 调对应 skill。

"两个 agent 串行 + 各跑独立上下文"是设计核心；如宿主不支持独立 session，至少 verifier 不得依赖一审上下文的"私下推理"，只能依赖落盘 finding 字段（见 independence-protocol.md）。
