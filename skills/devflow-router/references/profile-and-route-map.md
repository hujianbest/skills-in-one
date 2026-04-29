# DevFlow Profile 与路由表

本 reference 属于 `devflow-router`，定义合法 profile 路径、route upgrades 和 hard stops。

DevFlow 有两个子街区：

- `requirement-analysis`：SR work item；不包含实现节点。
- `implementation`：AR / DTS / CHANGE work item 使用 `standard` / `component-impact` / `hotfix` / `lightweight` profiles。

同一个 work item 内不得在 SR analysis 与 implementation 之间切换。SR closeout 可以列出 AR candidates；由需求负责人另行创建新的 AR work items。

## Requirement-Analysis 路由

```text
using-devflow
  -> devflow-router
  -> devflow-specify
  -> devflow-spec-review
  -> (optional) devflow-component-design
  -> (optional) devflow-component-design-review
  -> devflow-finalize
```

合法节点：`devflow-specify`、`devflow-spec-review`、`devflow-component-design`、`devflow-component-design-review`、`devflow-finalize`。

此 profile 下实现节点均非法。

## Standard 路由

```text
using-devflow
  -> devflow-router
  -> devflow-specify
  -> devflow-spec-review
  -> devflow-ar-design
  -> devflow-ar-design-review
  -> devflow-tdd-implementation        # 包含 task queue setup/preflight
  -> devflow-test-checker
  -> devflow-code-review
  -> devflow-completion-gate
  -> (next-ready task ? devflow-tdd-implementation : devflow-finalize)
```

## Component-Impact 路由

```text
using-devflow
  -> devflow-router
  -> devflow-specify
  -> devflow-spec-review
  -> devflow-component-design
  -> devflow-component-design-review
  -> devflow-ar-design
  -> devflow-ar-design-review
  -> devflow-tdd-implementation        # 包含 task queue setup/preflight
  -> devflow-test-checker
  -> devflow-code-review
  -> devflow-completion-gate
  -> (next-ready task ? devflow-tdd-implementation : devflow-finalize)
```

新增组件、SOA / interface / error-code / timing 变化、依赖或状态机变化、跨组件协调、组件设计缺失或过期时，使用 `component-impact`。

## Hotfix / Problem-Fix 路由

```text
using-devflow
  -> devflow-router
  -> devflow-problem-fix
  -> (optional) devflow-ar-design -> devflow-ar-design-review
  -> devflow-tdd-implementation        # 按需包含 task queue setup/preflight
  -> devflow-test-checker
  -> devflow-code-review
  -> devflow-completion-gate
  -> devflow-finalize
```

Hotfix 可以压缩文档量，但不能跳过 test-checker、code-review 或 completion-gate。

## Lightweight 路由

```text
using-devflow
  -> devflow-router
  -> devflow-specify (minimal)
  -> devflow-spec-review
  -> devflow-ar-design (minimal，仍包含 test design section)
  -> devflow-ar-design-review
  -> devflow-tdd-implementation        # 包含最小 task queue setup/preflight
  -> devflow-test-checker
  -> devflow-code-review
  -> devflow-completion-gate
  -> devflow-finalize
```

Lightweight 只压缩文档量，不移除质量门禁。

## Hard Stops（硬停止）

命中任一项必须停止，并设置 `reroute_via_router=true`：

1. Requirement input 在 scope / acceptance / direction 上不清楚。
2. IR / SR / AR traceability 冲突。
3. AR / DTS / CHANGE 缺唯一 owning component。
4. SR 缺 owning subsystem。
5. SR work item 试图进入实现节点。
6. 变更影响组件边界，但 component design 缺失或过期。
7. AR design 缺 embedded test design。
8. Task queue preflight 无法产出完整 tasks 或唯一 `Current Active Task`。
9. `task-board.md` 存在多个 in_progress tasks、next-ready tasks 不明确，或与 `progress.md` 冲突。
10. TDD 已完成但测试尚未通过 `devflow-test-checker`。
11. 代码变更破坏 SOA boundary，或新增未解释的跨组件依赖。
12. critical static-analysis / build / coding-standard 问题未解释。
13. review / gate verdict 无法映射到唯一 next action。

## Reviewer 派发锚点

Review 节点必须派发为独立 reviewer subagents：

| 来源节点 | 派发节点 |
|---|---|
| `devflow-specify` | `devflow-spec-review` |
| `devflow-component-design` | `devflow-component-design-review` |
| `devflow-ar-design` | `devflow-ar-design-review` |
| `devflow-tdd-implementation` | `devflow-test-checker` |
| `devflow-test-checker` pass | `devflow-code-review` |

Task queue preflight 是 `devflow-tdd-implementation` 的内部步骤，不是派发式 review 节点。
