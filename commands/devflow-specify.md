---
description: Authoring + independent review of the requirement spec (SR analysis or AR/DTS/CHANGE implementation context)
---

This command orchestrates the **DevFlow specify (规格)** phase.

## Phase scope

- Skills involved (in推进顺序):
  1. `devflow-specify` — 写或修 `features/<id>/requirement.md`
  2. `devflow-router` — 派发评审子代理 + 消费 verdict + 决定下一步
- Reviewers dispatched (via `devflow-router`, system prompt = `agents/devflow-reviewer.md`):
  - `devflow-spec-review`，`target_skill = devflow-spec-review`

## When to use

- SR 接受后进入 `requirement-analysis` 子街区做需求澄清
- AR / DTS / CHANGE 进入实现子街区前的规格澄清
- 上一轮 spec review 返回 `REQUEST_CHANGES`，需要回修后重审

不适用：

- 仍在做产品发现 / 决定要不要做这个 SR / AR → 交回需求负责人
- 规格已通过，准备进入设计 → 改用 `/devflow-design`
- 紧急修复 → 改用 `/devflow-fix`

## Hard contract（节选自 AGENTS.md，不可绕开）

- 作者不自审：`devflow-specify` 完成后 **不允许** 在父会话内联评审；必须交 `devflow-router` 派发独立 `devflow-reviewer` 子代理
- SR 拆出的候选 AR **必须新建** AR work item，由 router 重新分流，不允许在同一 work item 内跨子图
- 规格未通过 spec-review 不得进入 `devflow-component-design` / `devflow-ar-design` / `devflow-tdd-implementation`
- `auto` execution mode 不豁免 spec-review

## Workflow（不复制 SKILL.md，只编排）

1. 读 `features/<id>/progress.md`：
   - 不存在 / 工件证据不稳定 → 退回 `/devflow` 走 `using-devflow → devflow-router`
   - 存在且当前节点就是 `devflow-specify` → 继续本阶段
2. 进入 `devflow-specify`，严格遵循其 SKILL.md `工作流` 章节，产出或修订 `requirement.md`，写齐 traceability、约束、可设计性所需的信息
3. authoring 完成 → 形成 handoff：`current_node = devflow-specify`，`next_action_or_recommended_skill = devflow-spec-review`，`reroute_via_router = true`
4. 控制交回 `devflow-router`：
   - 构造 Review Request Pack（`target_skill = devflow-spec-review`、`primary_artifact = features/<id>/requirement.md`、`agents_md_anchor`、`expected_return_contract`）
   - 派发独立子代理（system prompt = `agents/devflow-reviewer.md`）
5. 消费 reviewer verdict：
   - `APPROVE` / `APPROVE_WITH_FOLLOWUPS` → `next_action_or_recommended_skill` 由 router 决定（SR 子街区可能是 `devflow-component-design` 或 `devflow-finalize`；实现子街区一般是 `devflow-ar-design`，必要时升级 `component-impact` 走 `devflow-component-design`）
   - `REQUEST_CHANGES` → 回 `devflow-specify` 修订
   - `REJECT` → 停下，交团队角色（需求负责人）裁决；写 `Blockers`
   - `reroute_via_router = true` → 由 router 重新评估

## Anti-rationalization quick refs

| 误判 | 反向行动 |
|---|---|
| "规格我看一遍就行，跳过 spec-review" | 禁止；评审必须由 router 派发独立子代理 |
| "SR 顺手把候选 AR 一起做了" | 禁止跨子图；候选 AR 必须新建 work item |
| "auto 模式可以跳过评审" | `auto` 只移除人工确认，不豁免评审 |
| "规格不清的地方我替需求负责人定" | 禁止；写进 `Blockers`，交需求负责人 |
