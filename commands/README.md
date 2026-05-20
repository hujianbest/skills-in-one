# DevFlow Commands

DevFlow 工作流阶段入口（slash-style commands）。每个 command 是一个 **阶段编排器**，对应 `AGENTS.md` 定义的 DevFlow 工作流主环节；内部组合多个 canonical `devflow-*` skill，但不替换或绕开它们。

Commands 与 `skills/` 的关系：

| 层 | 它是什么 | 例 | 编排角色 |
|---|---|---|---|
| Skill | 带步骤与退出准则的工作流 | `devflow-ar-design`、`devflow-spec-review` | *How*：在 command 或 persona 内部被严格遵循 |
| Persona（agent） | 带角色视角和输出格式的子代理 | `devflow-reviewer`、`devflow-implementer` | *Who*：被 router 或 tdd-implementation 派发 |
| Command | 用户视角的工作流阶段入口 | `/devflow-specify`、`/devflow-build` | *When*：组合多个 skill 推进一个阶段 |

Slash command **不复制** SKILL.md 的内容，只声明本阶段会跨过哪些 canonical 节点、需要派发哪些评审子代理，以及阶段开始与结束时如何形成 handoff。所有判据仍以 `skills/<name>/SKILL.md` 为唯一权威。

---

## 命令清单

| Command | 阶段 | 内部组合的 canonical skills | 评审派发（由 `devflow-router`）|
|---|---|---|---|
| [`/devflow`](devflow.md) | 入口 / 续作 | `using-devflow` → `devflow-router`（按需） | — |
| [`/devflow-specify`](devflow-specify.md) | 规格阶段 | `devflow-specify` → `devflow-router` | `devflow-spec-review` |
| [`/devflow-design`](devflow-design.md) | 设计阶段 | （组件影响时）`devflow-component-design` →（评审）→ `devflow-ar-design` →（评审）| `devflow-component-design-review`、`devflow-ar-design-review` |
| [`/devflow-build`](devflow-build.md) | 构建阶段 | `devflow-tdd-implementation` →（评审）→（评审）| `devflow-test-review`、`devflow-code-review` |
| [`/devflow-ship`](devflow-ship.md) | 收尾阶段 | `devflow-completion-gate` → `devflow-finalize` | — |
| [`/devflow-fix`](devflow-fix.md) | hotfix 子图 | `devflow-router`（升级 `hotfix`）→ `devflow-problem-fix` → 回到 `/devflow-build` → `/devflow-ship` | 继承 `devflow-test-review`、`devflow-code-review` |

---

## 通用规则（每个 command 都遵守）

1. **不写自由文本下一步**。`Next Action Or Recommended Skill` 字段必须是 13 个 canonical 节点之一；`using-devflow` 不得写入任何 handoff 字段。
2. **不内联评审**。所有 5 个评审节点（spec / component-design / ar-design / test / code）一律由 `devflow-router` 派发独立 `devflow-reviewer` 子代理，禁止父会话或作者节点自审。
3. **profile 单调升级**。一个 work item 内允许 `standard → component-impact`、`standard / component-impact → hotfix`；禁止反向降级，禁止 `requirement-analysis` 与任何实现 profile 互转。
4. **不替团队角色拍板**。涉及业务、需求方向、架构边界、接口契约的决策 → 停下，交还需求负责人 / 模块架构师 / 开发负责人。
5. **artifact-first**。任何下一步只来自磁盘工件（`features/<id>/progress.md`、`reviews/`、`evidence/`、`completion.md`、长期 `docs/`）；与聊天记忆冲突时以工件为准。
6. **`auto` execution mode** 不豁免任何评审、门禁或证据要求；只移除节点间人工确认。

---

## 不引入的命令（明确划线）

- ❌ `/ship` 并行 fan-out：与 DevFlow 顺序门禁链（test-review → code-review → completion-gate → finalize）冲突。
- ❌ `/code-simplify`：简化属于 `devflow-tdd-implementation` 的 REFACTOR 步骤，不另立节点。
- ❌ `/plan`：tasks 队列由 `devflow-tdd-implementation` 内部 preflight 管理，不另立 command。
- ❌ 任何 meta-orchestrator command：`devflow-router` 是唯一编排权威。
