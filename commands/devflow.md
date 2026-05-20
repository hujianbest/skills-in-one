---
description: DevFlow public entry — discover where this session belongs and route to the right phase command or canonical skill
---

This command orchestrates the **DevFlow entry / resume** phase.

## Phase scope

- Skills involved (in推进顺序):
  1. `using-devflow` — public entry，分流意图为 `direct invoke` 或 `route-first`
  2. `devflow-router` — runtime routing（当 `using-devflow` 返回 `route-first`、或当前是评审/门禁后的恢复、或证据冲突时）
- Reviewers dispatched: 无（本 command 不直接派发评审；如路由到评审节点，由阶段 command 与 router 共同完成）

## When to use

- 新会话不确定从哪进入 DevFlow
- 用户说"继续 / 推进 / 开始做"但当前节点未确认
- 评审 / 门禁刚结束需要消费 verdict 决定下一步
- 不确定走 `/devflow-specify`、`/devflow-design`、`/devflow-build`、`/devflow-ship` 还是 `/devflow-fix`

不适用：

- 已在某个 leaf skill 内部继续执行 → 直接继续该 skill
- 已知阶段明确 → 直接用对应阶段 command

## Hard contract（节选自 AGENTS.md，不可绕开）

- `using-devflow` 是 public entry，**永远不能** 写入 `Next Action Or Recommended Skill` 或任何 handoff 字段
- 任何无法唯一映射到一个 leaf 的延续 / 恢复 / profile 决定 / 评审 verdict 消费 → 必须交 `devflow-router`
- 决策只来自磁盘工件，与聊天记忆冲突取工件

## Workflow（不复制 SKILL.md，只编排）

1. 载入 `using-devflow`，按其 `工作流` 章节做最小入口判定
2. `using-devflow` 输出二选一：
   - `direct invoke` + 唯一 canonical leaf + 工件证据稳定 → 进入对应阶段 command 或直接进入该 leaf skill
   - `route-first` → 立即载入 `devflow-router`，由其按工件证据决定唯一下一步
3. 阶段确定后，把控制交给对应阶段 command：`/devflow-specify`、`/devflow-design`、`/devflow-build`、`/devflow-ship`、`/devflow-fix`
4. 形成 canonical handoff 块；`next_action_or_recommended_skill` 仅限 13 个 canonical 节点之一

## Anti-rationalization quick refs

| 误判 | 反向行动 |
|---|---|
| "用户说继续就直接进 TDD" | 禁止；先 `using-devflow` 判分流，证据不足 → `devflow-router` |
| "看起来是评审刚过，我替它写下一步" | 禁止；评审后恢复一律 `devflow-router` 消费 verdict |
| "把 `using-devflow` 写进 handoff 表示入口" | 禁止；它是 public entry，不是 canonical 节点 |
