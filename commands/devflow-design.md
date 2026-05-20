---
description: Authoring + independent review of component design (when component-impact) and AR design with embedded test design
---

This command orchestrates the **DevFlow design (设计)** phase.

## Phase scope

- Skills involved (in推进顺序):
  1. `devflow-component-design` — 仅在 `component-impact` 子街区或 SR-analysis 触发组件设计时
  2. `devflow-router` — 派发组件设计评审 + 消费 verdict
  3. `devflow-ar-design` — 实现子街区下写或修 `features/<id>/ar-design-draft.md`，**必须** 含测试设计章节
  4. `devflow-router` — 派发 AR 设计评审 + 消费 verdict
- Reviewers dispatched (via `devflow-router`, system prompt = `agents/devflow-reviewer.md`):
  - `devflow-component-design-review`（仅当组件设计存在）
  - `devflow-ar-design-review`

## When to use

- 规格已通过 spec-review，进入实现子街区做 AR 级设计
- AR 触及 SOA 接口 / 依赖 / 状态机 / 运行机制 → router 升级到 `component-impact`，先做组件设计
- SR-analysis 触发组件设计修订
- 上一轮设计评审返回 `REQUEST_CHANGES`，需要回修后重审

不适用：

- 规格尚未通过 → 改用 `/devflow-specify`
- 设计已通过，进入 TDD → 改用 `/devflow-build`
- 紧急修复 → 改用 `/devflow-fix`

## Hard contract（节选自 AGENTS.md，不可绕开）

- 是否进入 `devflow-component-design` 由 `devflow-router` 决定（基于工件 + AR 范围）；leaf **不允许** 自行升级 profile
- profile 单调升级：`standard → component-impact` 允许；反向降级禁止
- 组件影响型 work item 缺 `docs/component-design.md` → 必须先完成 `devflow-component-design`
- **AR 设计未含测试设计章节 → 不得进入 `devflow-tdd-implementation`**；评审若发现缺测试设计章节，必须 `REQUEST_CHANGES` 回 `devflow-ar-design`
- 作者不自审：两个评审节点都必须由 `devflow-router` 派发独立 `devflow-reviewer` 子代理
- `requirement-analysis` 子街区不得路由到 `devflow-ar-design` / `devflow-ar-design-review`

## Workflow（不复制 SKILL.md，只编排）

1. 读 `features/<id>/progress.md` 与最近评审记录：
   - profile 未定 / 证据冲突 → 回 `/devflow` 走 router
   - profile = `component-impact` 且 `docs/component-design.md` 缺失或过时 → 走步骤 2；否则跳到步骤 5
2. 进入 `devflow-component-design`，严格遵循其 SKILL.md `工作流`，产出或修订 `features/<id>/component-design-draft.md`
3. handoff 给 `devflow-router`，派发 `devflow-component-design-review`（`target_skill = devflow-component-design-review`）
4. 消费组件设计评审 verdict：
   - `APPROVE` → 步骤 5
   - `REQUEST_CHANGES` → 回步骤 2
   - `REJECT` → 停下，交模块架构师裁决
5. 进入 `devflow-ar-design`，严格遵循其 SKILL.md `工作流`，产出或修订 `features/<id>/ar-design-draft.md`，**确保测试设计章节完整**（数据点、边界、错误路径、最低测试金字塔比例等按 SKILL.md）
6. handoff 给 `devflow-router`，派发 `devflow-ar-design-review`（`target_skill = devflow-ar-design-review`）
7. 消费 AR 设计评审 verdict：
   - `APPROVE` / `APPROVE_WITH_FOLLOWUPS` → `next_action_or_recommended_skill = devflow-tdd-implementation`，进入 `/devflow-build`
   - `REQUEST_CHANGES` → 回 `devflow-ar-design`
   - `REJECT` → 停下，交开发负责人裁决

## Anti-rationalization quick refs

| 误判 | 反向行动 |
|---|---|
| "改动看起来不影响组件边界，跳过组件设计" | 由 router 判，不由 leaf 自判；任何 SOA 接口 / 依赖 / 状态机 / 运行机制变化都触发 `component-impact` |
| "测试设计章节先空着，TDD 时再补" | 禁止；缺章节直接被 ar-design-review 打回 |
| "ar-design 我改完顺手 review 一下" | 禁止；必须 router 派发独立子代理 |
| "把 SR 的组件设计当成 AR 的 AR 设计用" | 禁止跨子图，组件设计与 AR 设计是不同 canonical 节点 |
