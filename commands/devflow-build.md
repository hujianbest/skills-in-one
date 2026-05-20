---
description: TDD implementation followed by sequential test-effectiveness review and C/C++ code review
---

This command orchestrates the **DevFlow build (构建)** phase.

## Phase scope

- Skills involved (in推进顺序):
  1. `devflow-tdd-implementation` — task queue preflight + 派发 `devflow-implementer` 子代理执行 RED-GREEN-REFACTOR
  2. `devflow-router` — 派发测试有效性评审
  3. `devflow-router` — 派发 C/C++ 代码检视
- Reviewers dispatched (via `devflow-router`, system prompt = `agents/devflow-reviewer.md`):
  - `devflow-test-review`（`target_skill = devflow-test-review`）
  - `devflow-code-review`（`target_skill = devflow-code-review`）
- Implementer dispatched (via `devflow-tdd-implementation`, system prompt = `agents/devflow-implementer.md`):
  - 每次 next-ready task 一次新派发；接收 Implementer Context Pack

## When to use

- `devflow-ar-design-review` 已 `APPROVE`，进入 TDD
- `devflow-test-review` 或 `devflow-code-review` 返回需修改，回修后再次推进
- `devflow-problem-fix` 给出复现与最小修复边界后进入 TDD

不适用：

- AR 设计未通过 → `/devflow-design`
- 完成判断 / 收口 → `/devflow-ship`
- `requirement-analysis` 子街区（SR）→ 严禁进入本阶段

## Hard contract（节选自 AGENTS.md，不可绕开）

- AR 设计无测试设计章节 → **不得** 进入 `devflow-tdd-implementation`，回 `devflow-ar-design`
- 多个 `in_progress` task 或 next-ready 不唯一 → `reroute_via_router = true`，停下交 router
- TDD 完成后 **未经** `devflow-test-review` → 不得进入 `devflow-code-review`
- `devflow-code-review` 未通过 → 不得进入 `devflow-completion-gate`
- 实现子代理只能 `devflow-tdd-implementation` 派发；必须传 Implementer Context Pack，禁止裸传聊天历史
- 实现子代理 **不修改** task 计划 / AR 设计 / task-board 顺序
- 评审子代理 **不修改** 生产代码 / 测试

## Workflow（不复制 SKILL.md，只编排）

1. 读 `features/<id>/progress.md`、`Task Plan Path`、`Task Board Path`：
   - 工件证据不稳定 / next-ready 不唯一 → 回 `/devflow` 走 router
2. 进入 `devflow-tdd-implementation`，按其 SKILL.md `工作流` 做 task queue preflight 与 `Current Active Task` 决定
3. 派发 `devflow-implementer` 子代理（system prompt = `agents/devflow-implementer.md`，输入 = Implementer Context Pack）；按 task 逐个推进
4. 子代理返回：
   - `DONE` → 更新 task-board，继续下一 task 直到本批结束
   - `DONE_WITH_CONCERNS` → 记录 concerns，由 `devflow-tdd-implementation` 决定继续 / 升级
   - `NEEDS_CONTEXT` → 留在 `devflow-tdd-implementation` 内部重新打包再试，不外溢
   - `BLOCKED` + `reroute_via_router = true` → 交 `devflow-router`
5. 所有 next-ready task 完成 → handoff 给 `devflow-router`，派发 `devflow-test-review`
6. 消费 test-review verdict：
   - `APPROVE` / `APPROVE_WITH_FOLLOWUPS` → 步骤 7
   - `REQUEST_CHANGES` → 回 `devflow-tdd-implementation` 修测试 / 修实现
   - `REJECT` → 停下，交开发负责人裁决
7. handoff 给 `devflow-router`，派发 `devflow-code-review`
8. 消费 code-review verdict：
   - `APPROVE` / `APPROVE_WITH_FOLLOWUPS` → `next_action_or_recommended_skill = devflow-completion-gate`，进入 `/devflow-ship`
   - `REQUEST_CHANGES` → 回 `devflow-tdd-implementation` 按 findings 修
   - `REJECT` → 停下，交开发负责人裁决

## Anti-rationalization quick refs

| 误判 | 反向行动 |
|---|---|
| "测试都跑过了，跳过 test-review" | 禁止；test-review 评的是测试 **有效性** 与覆盖度，不是是否跑过 |
| "把全部 task 一起做" | 禁止；一次 next-ready task，一次新派发 |
| "implementer 顺手调一下 AR 设计" | 禁止；越界改 AR 设计或 task 计划必须 `BLOCKED + reroute` |
| "code-review 我自己读一遍代码就行" | 禁止；必须 router 派发独立子代理 |
| "evidence 写差不多就行" | 必须按 SKILL.md 写齐 evidence 路径，否则后续完成门禁会被卡 |
