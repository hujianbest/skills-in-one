# Task Progress

## Goal

- Goal: 在 HF 主链上正式立项并落地 `hf-doc-freshness-gate`，把"用户可见行为变化必须对应可冷读的对外文档同步证据"从隐性 self-check 升级为带 verdict 的 gate；以 sync-on-presence + profile 分级 + 与 `hf-completion-gate` / `hf-finalize` 显式分工三条纪律保证不退化为模板填空、不让 lightweight 变重、不抢 finalize 同步动作。
- Owner: Cursor Cloud Agent (HF self-application)
- Status: spec-review 通过 + 4 LLM-FIXABLE 已回修；当前停在 规格真人确认 checkpoint（auto mode 仍不可跳）
- Last Updated: 2026-04-23

## Current Workflow State

- Current Stage: 规格真人确认（pending）
- Workflow Profile: standard
- Execution Mode: auto
- Current Active Feature: `features/001-hf-doc-freshness-gate/`
- Current Active Task: N/A（spec 阶段尚未拆任务）
- Pending Reviews And Gates: **规格真人确认（next，需真人）** → hf-design / hf-design-review → 设计真人确认 → hf-tasks / hf-tasks-review → 任务真人确认 → hf-test-driven-dev → test / code / traceability review → regression-gate / completion-gate → hf-finalize
- Relevant Files:
  - `features/001-hf-doc-freshness-gate/spec.md`
  - `docs/insights/2026-04-23-hf-doc-freshness-gate-discovery.md`（上游 discovery，已通过 review）
  - `docs/reviews/discovery-review-hf-doc-freshness-gate.md`（discovery review 通过记录）
  - `docs/experiments/2026-04-23-hf-doc-freshness-gate-hyp-001/`（HYP-001 probe，Pass）
- Constraints:
  - 不得动 `skills/hf-doc-freshness-gate/` 直至 design / tasks / TDD 主链通过 + 真人确认
  - 不得跳过 `规格真人确认` / `设计真人确认` / `任务真人确认`（auto mode 仅是 Execution Mode 偏好）
  - U2（责任边界稳定）必须在 spec 内通过显式责任矩阵 + reviewer 判定关闭

## Progress Notes

- What Changed:
  - 2026-04-23: hf-product-discovery 完成草稿（commit c4ca0db）
  - 2026-04-23: hf-discovery-review 通过 + 3 条 LLM-FIXABLE 已修订（commit 8143fa2）
  - 2026-04-23: hf-experiment HYP-001 probe Pass（commit 370e48c）；HYP-001 confidence medium → high，Blocking 是 → 否
  - 2026-04-23: hf-specify 创建 features/001-hf-doc-freshness-gate/ 骨架并起草 spec.md
  - 2026-04-23: hf-spec-review 通过 + 4 LLM-FIXABLE finding 已回修；HYP-002 (U2) 由 reviewer 冷读 §6.2 责任矩阵关闭（confidence medium → high，Blocking 是 → 否）；reviewer subagent ID: 1fb2f95f-bad4-48c0-b0be-7932b3d093eb；review record: `reviews/spec-review-2026-04-23.md`
- Evidence Paths:
  - `docs/reviews/discovery-review-hf-doc-freshness-gate.md`（discovery review verdict）
  - `docs/experiments/2026-04-23-hf-doc-freshness-gate-hyp-001/probe-result.md`
  - `docs/experiments/2026-04-23-hf-doc-freshness-gate-hyp-001/artifacts/desk-research-evidence.md`
  - `features/001-hf-doc-freshness-gate/reviews/spec-review-2026-04-23.md`（spec review 通过 + 4 LLM-FIXABLE 已回修；HYP-002 (U2) closed）
- Session Log: 父会话按 hf-product-discovery → hf-discovery-review (subagent ID: 4d5926b5-e6ec-4dcd-9ec9-11561cb7dec0) → hf-experiment (HYP-001 Pass) → hf-specify → hf-spec-review (subagent ID: 1fb2f95f-bad4-48c0-b0be-7932b3d093eb, 通过 + 4 LLM-FIXABLE 已回修) → 当前停在 规格真人确认 checkpoint
- Open Risks:
  - HYP-001 desk-research 证据强但仍是单方法 probe；future Phase 1+ 真实用户访谈如有反向证据，应通过 hf-increment 修订
  - HYP-003（router FSM 复杂度）+ HYP-004（lightweight ≤ 5 行 / ≤ 5 分钟）将在 design 阶段做 dry run；不阻塞 spec 但阻塞 design 通过
  - 真人确认前 spec 已落盘但未批准；不允许 hf-design 启动

## Optional Coordination Fields

- Task Board Path: N/A（spec 阶段尚未拆任务）
- Task Queue Notes: N/A
- Workspace Isolation: in-place
- Worktree Path: N/A
- Worktree Branch: cursor/discovery-doc-freshness-gate-d0e2

## Next Step

- Next Action Or Recommended Skill: **规格真人确认**（HUMAN approval checkpoint，需真人）
- Blockers:
  - 真人未确认前不允许进入 hf-design（hf-spec-review Hard Gate）
  - auto mode 仅是 Execution Mode 偏好，按 using-hf-workflow Step 3 + hf-specify Hard Gates 不能跳此 approval
- Notes:
  - 真人确认应写入 `approvals/spec-approval-YYYY-MM-DD.md`，包含决议（approve / request-changes / reject）+ 关键决策记录
  - 真人 approve 后下一节点 = hf-design（同时 hf-ui-design 不激活，因本 spec 无 UI surface）
  - 真人 request-changes → 回 hf-specify 修订（按 review 的 [USER-INPUT] 项处理；本评审 USER-INPUT 数 = 0，不预期 request-changes）
  - 真人 reject → 回 hf-product-discovery 修订 wedge（与 hf-specify Hard Gates 一致）
  - LLM-FIXABLE 已全部回修；不向真人转嫁
