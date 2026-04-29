# devflow Profile And Route Map

> 配套 `devflow-router/SKILL.md`。展开 devflow 各 Workflow Profile 的合法节点集合、主链与支线，以及 hard stops 的具体表现。

devflow 当前覆盖两个子街区：

- **需求分析子街区**：profile = `requirement-analysis`；服务 SR 工作项；不进入实现节点
- **实现子街区**：profile = `standard` / `component-impact` / `hotfix` / `lightweight`；服务 AR / DTS / CHANGE 工作项

跨子街区切换 profile **一律禁止**——SR 拆出的候选 AR 必须新建 AR work item。

## Requirement-Analysis Route（需求分析子街区）

```text
using-devflow
  -> devflow-router
  -> devflow-specify                       (SR 子系统级需求澄清)
  -> devflow-spec-review
  -> (可选) devflow-component-design       (仅当 SR 触发组件实现设计修订)
  -> (可选) devflow-component-design-review
  -> devflow-finalize                      (analysis closeout)
```

合法节点集合：

```text
{ devflow-specify, devflow-spec-review,
  devflow-component-design, devflow-component-design-review,
  devflow-finalize }
```

非法节点（出现 → router hard stop，标 `reroute_via_router=true`）：

- `devflow-ar-design` / `devflow-ar-design-review` / `devflow-tdd-implementation` / `devflow-test-checker` / `devflow-code-review` / `devflow-completion-gate` / `devflow-problem-fix`
- 任何「升级」到 `standard` / `component-impact` / `hotfix` / `lightweight` 的尝试

触发条件：Work Item Type = `SR`。如果用户描述更像 AR / DTS（已分配给唯一组件、待实现），由 router 提示新建对应 work item，不在本 SR work item 内切换。

完成方式：`devflow-finalize` 写 **analysis closeout**，含：

- 子系统级需求规格（`requirement.md` 在分析子街区是终态文档，不是草稿）
- 可选的组件实现设计修订（promote 到 `docs/component-design.md`）
- AR Breakdown Candidates（候选 AR 列表 + 每条候选的范围 / 所属组件 / 优先级 / 上抛对象）
- 不要求实现 / 测试 / code-review evidence；不 promote 到 `docs/ar-designs/`

## Standard Route（实现子街区）

```text
using-devflow
  -> devflow-router
  -> devflow-specify
  -> devflow-spec-review
  -> devflow-ar-design
  -> devflow-ar-design-review
  -> devflow-tasks
  -> devflow-tasks-review
  -> devflow-tdd-implementation
  -> devflow-test-checker
  -> devflow-code-review
  -> devflow-completion-gate
  -> (next-ready task ? devflow-tdd-implementation : devflow-finalize)
```

合法节点集合：

```text
{ devflow-specify, devflow-spec-review, devflow-ar-design, devflow-ar-design-review,
  devflow-tasks, devflow-tasks-review,
  devflow-tdd-implementation, devflow-test-checker, devflow-code-review,
  devflow-completion-gate, devflow-finalize }
```

非法节点（出现需立即升级 / 改路）：

- 修改影响组件边界 / SOA 接口 / 组件依赖 → 升级 component-impact
- DTS / 紧急缺陷 → 改 hotfix
- Work Item Type = `SR` → 强制走 `requirement-analysis` profile，回 router

## Component-Impact Route

```text
using-devflow
  -> devflow-router
  -> devflow-specify
  -> devflow-spec-review
  -> devflow-component-design
  -> devflow-component-design-review
  -> devflow-ar-design
  -> devflow-ar-design-review
  -> devflow-tasks
  -> devflow-tasks-review
  -> devflow-tdd-implementation
  -> devflow-test-checker
  -> devflow-code-review
  -> devflow-completion-gate
  -> (next-ready task ? devflow-tdd-implementation : devflow-finalize)
```

触发条件（任一命中即升级）：

- 新增组件
- 修改 SOA 服务 / 接口 / 错误码 / 时序约束
- 修改组件职责、依赖方向、状态机或运行时机制
- AR 实现需要跨组件协调
- 现有组件实现设计缺失、过期或与代码明显不一致

注意：组件实现设计是 AR 实现设计的输入。AR 实现设计**不得**临时改写组件架构；必须先经过 `devflow-component-design`。

## Hotfix / Problem-Fix Route

```text
using-devflow
  -> devflow-router
  -> devflow-problem-fix
  -> (可选) devflow-ar-design -> devflow-ar-design-review
  -> (可选) devflow-tasks -> devflow-tasks-review
  -> devflow-tdd-implementation
  -> devflow-test-checker
  -> devflow-code-review
  -> devflow-completion-gate
  -> devflow-finalize
```

`devflow-problem-fix` 至少完成：复现路径或无法复现说明、根因、最小安全修复边界、是否需要补 AR 实现设计或组件实现设计、明确回流节点。

紧急 ≠ 绕过；hotfix 可以压缩文档量（例如不写完整 AR 实现设计，只写 fix-design.md），但**不能**跳过：

- `devflow-test-checker`
- `devflow-code-review`
- `devflow-completion-gate`

## Lightweight Route

```text
using-devflow
  -> devflow-router
  -> devflow-specify (极简)
  -> devflow-spec-review
  -> devflow-ar-design (极简，但必须含测试设计章节)
  -> devflow-ar-design-review
  -> devflow-tasks
  -> devflow-tasks-review
  -> devflow-tdd-implementation
  -> devflow-test-checker
  -> devflow-code-review
  -> devflow-completion-gate
  -> devflow-finalize
```

`lightweight` 仅在以下条件全部满足时使用：

- 修改局部、低风险（如 magic number、注释、日志措辞）
- 不影响 SOA 接口 / 组件依赖 / 状态机
- 测试覆盖已能直接锁定行为

`lightweight` **不允许**跳过 test-checker / code-review / completion-gate。允许压缩的是文档量（requirement.md 可数行、ar-design-draft.md 章节可合并），不是质量证据。

## Profile 升级规则（仅同子街区内升级，不允许降级，不允许跨子街区切换）

跨子街区切换 **一律禁止**：`requirement-analysis` ↔ 任意实现 profile 都不允许在同一 work item 内发生。SR 拆出的候选 AR 必须**新建** AR work item 走实现子街区。

需求分析子街区内：

| 当前 profile | 升级触发 | 升级后 |
|---|---|---|
| `requirement-analysis` | 仅本子街区使用 | 不存在升级路径 |

实现子街区内：

| 当前 profile | 升级触发 | 升级后 |
|---|---|---|
| `lightweight` | 发现影响 SOA / 组件依赖 / 状态机 | `component-impact` |
| `lightweight` | 发现是 DTS / 缺陷 | `hotfix` |
| `standard` | 发现影响 SOA / 组件依赖 / 状态机 | `component-impact` |
| `standard` | 发现是 DTS / 缺陷 | `hotfix` |
| `component-impact` | 发现是 DTS | 仍 `component-impact` 兼 hotfix 性质，启动 `devflow-problem-fix` 子线 |

降级（如发现 component-impact 不再成立）一律禁止。理由：profile 决定了证据要求，已经按更高 profile 准备的证据不会因为降级而消失，也避免因为「看起来简单了」就静默删减验证。

## Hard Stops

任一命中必须停下，标 `reroute_via_router=true`：

1. 需求输入不清且涉及方向 / 范围 / 验收 → 停在 `devflow-specify`，回需求负责人
2. IR / SR / AR 追溯关系冲突 → 阻塞，回需求负责人
3. AR 不属于唯一组件（实现子街区） → 阻塞
4. SR 缺所属子系统（需求分析子街区） → 阻塞
5. SR-flow 试图进入 `devflow-ar-design` / `devflow-tdd-implementation` / 任何实现节点 → router hard stop，提示新建 AR work item
6. SR analysis closeout 缺 AR Breakdown Candidates 且未声明「无可拆分 AR」 → 阻塞
7. 缺组件实现设计但当前修改影响组件边界（实现子街区） → 进 `devflow-component-design` 并升级 component-impact
8. AR 实现设计未含测试设计章节 → 回 `devflow-ar-design`
9. AR 设计通过后 tasks 未产出 / tasks-review 未通过 → 不得进 `devflow-tdd-implementation`
10. task-board 中 `Current Active Task` 不唯一、多个 `in_progress` 或依赖状态冲突 → 回 router
11. TDD 完成后测试用例未经 `devflow-test-checker` → 不得进 `devflow-code-review`
12. 代码修改破坏 SOA 边界或引入未解释跨组件依赖 → review 阻塞
13. 存在未解释的 critical 静态分析 / 编译告警 / 编码规范违反 → completion 阻塞
14. review / gate 结论无法唯一映射下一步 → router hard stop

## Reviewer Dispatch Anchor

review 节点必须派发独立 reviewer subagent，不内联：

| 来源节点 | 派发节点 |
|---|---|
| `devflow-specify` | `devflow-spec-review` |
| `devflow-component-design` | `devflow-component-design-review` |
| `devflow-ar-design` | `devflow-ar-design-review` |
| `devflow-tasks` | `devflow-tasks-review` |
| `devflow-tdd-implementation` | `devflow-test-checker` |
| `devflow-test-checker`（通过） | `devflow-code-review` |

reviewer subagent 返回 `阻塞`(workflow) 时，本节点必须 `reroute_via_router=true` 停下，由父会话决定是否升级 profile / 回上游。
