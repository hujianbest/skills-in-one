---
description: Sequential completion gate then finalize — promote artifacts to long-term docs/ and close out the work item
---

This command orchestrates the **DevFlow ship (收尾)** phase.

## Phase scope

- Skills involved (in推进顺序):
  1. `devflow-completion-gate` — 独立确认实现工作项是否满足 devflow 完成定义
  2. `devflow-finalize` — 实现 / 分析两种语境闭环：promote `docs/ar-specs/`、`docs/ar-designs/`、可选长期资产；SR 候选 AR 交还需求负责人
- Reviewers dispatched: 无（评审在 `/devflow-build` 阶段已经完成；本阶段只做门禁与闭环）

## When to use

- 实现子街区下 `devflow-code-review` 已 `APPROVE`，准备过完成门禁
- 门禁返工后复检
- SR 在 `devflow-spec-review` 通过或组件设计评审通过后做分析子街区的闭环
- 用户明确要求收口某个 SR / AR

不适用：

- 代码评审未通过 → `/devflow-build`
- 新实现 → `/devflow-build`
- 缺陷 / 紧急修复 → `/devflow-fix`

## Hard contract（节选自 AGENTS.md，不可绕开）

- **顺序门禁链不可跳序**：`devflow-test-review` → `devflow-code-review` → `devflow-completion-gate` → `devflow-finalize`
- `devflow-completion-gate` 未通过 → **不得** 进入 `devflow-finalize`（实现闭环）
- `devflow-finalize` 必须保证 `docs/ar-specs/AR<id>-<slug>.md` 与 `docs/ar-designs/AR<id>-<slug>.md` 存在或本次 promote；缺失即阻塞
- `requirement-analysis` 子街区不进 `devflow-completion-gate`；SR 直接走 `devflow-finalize`（分析闭环）
- 闭环不把 work item 移到 `features/archived/`；保留在 `features/<id>/` 以保 traceability
- 不替团队角色拍板：完成定义的灰区由开发负责人裁决，本阶段只汇总证据

## Workflow（不复制 SKILL.md，只编排）

1. 读 `features/<id>/progress.md`、`reviews/`、`evidence/`、`completion.md`（如有）
   - 实现子街区且 `devflow-code-review` 未通过 → 回 `/devflow-build`
   - 工件证据冲突 → 回 `/devflow` 走 router
2. 实现子街区路径：
   - a. 进入 `devflow-completion-gate`，严格遵循其 SKILL.md `工作流`，输出 `PASS` / `HOLD` / `FAIL`
   - b. `PASS` → 进入 `devflow-finalize`
   - c. `HOLD` → 写 `Blockers`，下一步指向 SKILL.md 指定的回修节点（通常是 `devflow-tdd-implementation` 或某个评审节点），由 `/devflow-build` 继续
   - d. `FAIL` → 停下，交开发负责人裁决
3. 分析子街区路径（SR）：
   - 直接进入 `devflow-finalize`（按 SKILL.md 的 SR 分析闭环工作流执行）
4. 在 `devflow-finalize` 内：
   - promote `features/<id>/requirement.md` → `docs/ar-specs/AR<id>-<slug>.md`（适用时）
   - promote `features/<id>/ar-design-draft.md` → `docs/ar-designs/AR<id>-<slug>.md`（适用时）
   - 处理可选长期资产（`docs/interfaces.md` / `docs/dependencies.md` / `docs/runtime-behavior.md`）按 read-on-presence
   - SR：把 AR Breakdown Candidates 交还需求负责人，候选 AR 必须新建 work item
5. 输出 canonical handoff 块；闭环完成后 `Current Stage = devflow-finalize`，`Pending Reviews And Gates` 清空，`Blockers` 清空或留 follow-up

## Anti-rationalization quick refs

| 误判 | 反向行动 |
|---|---|
| "code-review 大致 OK，跳过 completion-gate 直接 finalize" | 禁止跳序；门禁链必须顺序 |
| "完成定义有点灰，我替开发负责人定一下" | 禁止；写 `Blockers`，交开发负责人 |
| "把 work item 移到 archived 整洁一点" | 禁止；保留 `features/<id>/`，否则 traceability 链断 |
| "AR 设计草稿就放 features 下不 promote 到 docs/ar-designs/" | 禁止；finalize 必须 promote，否则后续 AR 失去长期 anchor |
