---
name: devflow-router
description: Use when the user says "继续/推进" and the canonical devflow node must be decided from artifact evidence, when a review/gate just finished and orchestration must resume, when route/stage/profile is unclear or artifact evidence conflicts, when deciding whether to enter component-impact / hotfix profile, or when dispatching reviewer subagents for spec/component-design/ar-design/test-check/code-review. Not for new-session family discovery (→ using-devflow), not for authoring/reviewing/implementing inside a leaf node (→ corresponding devflow-* skill).
---

# DevFlow Router

DevFlow workflow family 的 **runtime authority**。基于工件证据决定：Workflow Profile、Execution Mode、canonical `devflow-*` 节点、是否进入 component-impact 或 hotfix 支线、review subagent 派发，以及 review / gate 后的恢复编排。

`using-devflow` 负责 public entry 与意图分流；本 skill 负责 runtime routing 与恢复。

devflow 默认以单 AR / 单 DTS 为 work item 边界；实现子街区在 AR 设计通过后维护 work item 内部的 `tasks.md` / `task-board.md` 执行索引。本 skill 不替模块架构师、开发负责人、开发人员拍板任何专业判断；只负责把工件证据转化为唯一下一步。

## When to Use

适用：

- 用户说"继续 / 推进"，需依据工件判断当前节点
- review / gate 刚完成，需消费结论并决定下一步
- route / stage / profile 不清，或工件证据冲突
- 需判断本 work item 走 **需求分析子街区**（SR → `requirement-analysis`）还是 **实现子街区**（AR / DTS / CHANGE → `standard` / `component-impact` / `hotfix` / `lightweight`）
- 需判断是否进入 `devflow-component-design`（SR-analysis 可选 / AR component-impact 触发）或 `devflow-problem-fix`（hotfix）
- 需派发 reviewer subagent 执行 spec / component-design / ar-design / test-check / code-review
- reviewer subagent 返回 `reroute_via_router=true`

不适用 → 改用：

- 新会话 family discovery → `using-devflow`
- 节点内部 authoring / review / 实现 → 对应 `devflow-*` leaf skill

## Hard Gates

- 不替模块架构师 / 开发负责人 / 开发人员拍板专业判断
- 不在父会话内联做 review；review 节点必须派发独立 reviewer subagent
- Profile 一旦升级（standard → component-impact / hotfix），不允许在同一 work item 内静默降级
- **不允许跨子街区切换 profile**：同一 work item 不得在 `requirement-analysis` 与任何实现 profile 之间切换。SR 拆出的候选 AR 必须**新建** AR work item，由 router 重新分流
- `requirement-analysis` profile 下不得路由到 `devflow-ar-design` / `devflow-ar-design-review` / `devflow-tdd-implementation` / `devflow-test-checker` / `devflow-code-review` / `devflow-completion-gate` / `devflow-problem-fix`
- 缺组件实现设计但本次修改影响组件边界 → 必须升级到 `component-impact` profile（仅适用于 AR 工作项），路由到 `devflow-component-design`
- AR 实现设计未含测试设计章节 → 不得路由到 `devflow-tdd-implementation`，必须回 `devflow-ar-design`
- AR 设计通过后由 `devflow-tdd-implementation` 内部执行 task queue preflight；preflight 无法产出完整 task queue 或唯一 Current Active Task 时必须回 `devflow-router`
- task-board 无法唯一判断 `Current Active Task` / next-ready task → 标 `reroute_via_router=true`
- TDD 完成后未经 `devflow-test-checker` 审查 → 不得路由到 `devflow-code-review`
- review / gate 结论无法唯一映射下一步 → 标 `reroute_via_router=true`，停下让父会话重新评估

## Object Contract

- Primary Object: routing 决定（profile + execution mode + canonical 节点 + reviewer 派发）
- Frontend Input Object: `features/<id>/progress.md`、`reviews/`、`evidence/`、`completion.md`、用户最新请求
- Backend Output Object: 唯一下一步 + 必要的 reviewer 派发说明 + 状态字段同步
- Transformation: 把工件证据转化为唯一 canonical 节点
- Boundaries: 不写设计 / 不写代码 / 不替 reviewer 给出 verdict
- Invariants: profile / execution mode 一旦决定，不允许 leaf 节点自改；canonical 节点名严格使用 `devflow-*` 前缀

## Methodology

- **Finite State Machine Routing**: workflow 阶段建模为 FSM，每条转移由工件状态驱动
- **Evidence-Based Decision Making**: 所有路由判断基于磁盘证据，证据冲突时取保守策略（更上游节点 / 更高 profile）
- **Escalation Pattern**: 只允许向上升级 profile（standard → component-impact / hotfix），不允许降级
- **Role-Separated Review Dispatch**: review 必须派发独立 reviewer subagent，不内联，不让 author 自审
- **Fresh Implementer Dispatch**: implementation may dispatch a fresh implementer subagent from `devflow-tdd-implementation`; router only consumes its status, not its code context
- **Read-On-Presence**: 项目当前未启用的可选资产（如 `docs/runbooks/`）缺失不阻塞路由

## Workflow

### 1. 确认是否属于 runtime routing

如果是 public entry / family discovery → 回 `using-devflow`。否则（恢复编排、profile 判断、消费 review/gate 结论、evidence conflict、切支线）继续。

### 2. 读取最少必要证据

按 Read-On-Presence 原则只读路由所需的最少内容：项目 `AGENTS.md` 路径映射、用户请求、`features/<id>/progress.md`、`features/<id>/reviews/` 与 `features/<id>/completion.md`、`docs/component-design.md` / `docs/ar-designs/`（必要时）。不在路由阶段做大范围代码探索。证据冲突 → 选更上游节点 / 升级 profile，不擅自调和。

### 3. 子街区判定

先决定本 work item 走 **需求分析子街区** 还是 **实现子街区**——profile 集合不同、合法节点集不同、closeout 类型不同。

| Work Item Type | 子街区 | profile 候选集 |
|---|---|---|
| `SR` | 需求分析 | 仅 `requirement-analysis` |
| `AR` / `CHANGE` | 实现 | `standard` / `component-impact` / `lightweight` |
| `DTS` | 实现 | `hotfix`（默认）；判断为常规缺陷修改时也可走 `standard` |

**禁止跨子街区升级**：同一个 work item 的 profile 不允许在 `requirement-analysis` 与任何实现 profile 之间切换。如果用户提出 SR 拆出的某个候选 AR 应该立刻进入实现，由需求负责人**新建** AR work item，由 router 重新走一次步骤 1-7。

### 4. 检查支线信号（仅实现子街区）

实现子街区内，支线优先于普通主链：

| 信号 | 路由 |
|---|---|
| DTS / 紧急缺陷 / 已上线问题修复 | `devflow-problem-fix`，profile = `hotfix` |
| 新增组件 / 修改 SOA 接口 / 修改组件职责 / 修改组件依赖 / 组件设计缺失或过期 | profile 升级到 `component-impact`，下一步 `devflow-component-design` |
| AR 实现需要跨组件协调 | profile = `component-impact` |

命中支线 → 走对应路径，不再回主链。

需求分析子街区不存在「升级到 component-impact」的概念——SR-flow 内的组件设计修订是 `requirement-analysis` profile 自带的可选步，不切换 profile。

### 5. 决定 Workflow Profile

按 Escalation Pattern：先执行 `AGENTS.md` 强制规则 → 沿用已有 profile → 按证据选择 → 冲突选更重。**只允许在同一子街区内升级，不允许降级，也不允许跨子街区切换**。

需求分析子街区：

| Profile | 适用场景 |
|---|---|
| `requirement-analysis` | Work Item Type = `SR`；澄清子系统级需求 + 可选组件实现设计；不进入实现 |

实现子街区：

| Profile | 适用场景 |
|---|---|
| `standard` | 既有组件 AR 增量、组件设计稳定、纯组件内修改 |
| `component-impact` | 命中步骤 4 component-impact 信号 |
| `hotfix` | 命中步骤 4 hotfix 信号 |
| `lightweight` | 极小、低风险、纯局部修改（错别字 / magic number / 注释）；保留 specify → completion 全链，仅允许压缩文档量 |

详细规则见 `references/profile-and-route-map.md`。

### 6. 决定 Execution Mode

与 Profile 正交。归一化顺序：用户显式要求 → `AGENTS.md` 默认 → 已有值 → 默认 `interactive`。`auto` 不删除 review / gate / approval，也不让 leaf 节点静默降级。

### 7. 归一化显式 handoff

leaf skill 返回的 `next_action_or_recommended_skill` 是受控字段。检查它是否归一化、是否与最新 evidence 一致、是否在当前 profile 合法集合内（见 `references/profile-and-route-map.md`）。全部满足才采用；否则忽略，回退到迁移表。

特别注意：`requirement-analysis` profile 下，leaf 返回 `devflow-ar-design` / `devflow-tdd-implementation` / `devflow-test-checker` / `devflow-code-review` / `devflow-completion-gate` / `devflow-problem-fix` 一律视为非法 → `reroute_via_router=true`，由真人决定是否新建 AR work item。

### 8. 决定 canonical 节点

路由原则：支线优先于主链 → review / gate 恢复优先于实现 → 缺失上游优先于下游 → 冲突选更保守。

迁移意图（与 `references/profile-and-route-map.md` 的 profile 主链 / 支线表一致）：

| 当前节点 | profile | 成功后 | 需修改 / 阻塞 |
|---|---|---|---|
| `devflow-specify` | `requirement-analysis`（SR） | `devflow-spec-review` | 回需求负责人 / `devflow-router` |
| `devflow-spec-review` | `requirement-analysis` | `devflow-component-design`（本 SR 触发组件设计修订）/ `devflow-finalize`（仅澄清，无组件设计修订） | `devflow-specify` |
| `devflow-component-design` | `requirement-analysis` | `devflow-component-design-review` | 继续修订 |
| `devflow-component-design-review` | `requirement-analysis` | `devflow-finalize`（analysis closeout） | `devflow-component-design` |
| `devflow-finalize` | `requirement-analysis` | workflow closed（analysis closeout） | 回 router |
| `devflow-specify` | 实现 profile | `devflow-spec-review` | 回需求负责人 / `devflow-router` |
| `devflow-spec-review` | 实现 profile | `devflow-component-design`（component-impact）/ `devflow-ar-design`（standard / lightweight） | `devflow-specify` |
| `devflow-component-design` | `component-impact` | `devflow-component-design-review` | 继续修订 |
| `devflow-component-design-review` | `component-impact` | `devflow-ar-design` | `devflow-component-design` |
| `devflow-ar-design` | 实现 profile | `devflow-ar-design-review` | 继续修订 |
| `devflow-ar-design-review` | 实现 profile | `devflow-tdd-implementation`（含 task queue preflight） | `devflow-ar-design` |
| `devflow-tdd-implementation` | 实现 profile | `devflow-test-checker` | 继续实现 / `devflow-ar-design` / `devflow-router` |
| `devflow-test-checker` | 实现 profile | `devflow-code-review` | `devflow-tdd-implementation` |
| `devflow-code-review` | 实现 profile | `devflow-completion-gate` | `devflow-tdd-implementation` |
| `devflow-completion-gate` | 实现 profile | `devflow-tdd-implementation`（有唯一 next-ready task）/ `devflow-finalize`（无剩余 task） | 缺什么回什么 |
| `devflow-finalize` | 实现 profile | workflow closed | 回 router |
| `devflow-problem-fix` | `hotfix` | `devflow-ar-design` 或 `devflow-tdd-implementation` | 继续 hotfix 分析 |

若结论无法映射唯一节点 → 标 `reroute_via_router=true` 停下。

### 9. 处理 review / gate 恢复

读取最新 review record / completion record，按 verdict 与角色边界判定：

- `通过` → 进入迁移表的成功后节点；`needs_human_confirmation=true` 时按 Mode 处理（interactive 等真人，auto 写 approval record）
- `需修改` / `阻塞`（内容） → 回授权节点（如 `devflow-tdd-implementation` / `devflow-ar-design`）
- `阻塞`（workflow） → `reroute_via_router=true`，停下并写明阻塞原因

completion-gate 通过后先读取 `Task Board Path`。若存在唯一 `next-ready task`，更新 `Current Active Task` 并路由到 `devflow-tdd-implementation`；若不存在剩余 ready / pending task，才路由到 `devflow-finalize`；若候选不唯一或状态冲突，回 `devflow-router` hard stop。

Implementer subagent status is consumed only through `devflow-tdd-implementation` artifacts (`task-board.md`, `implementation-log.md`, evidence paths). `NEEDS_CONTEXT` stays in `devflow-tdd-implementation` with a tighter context pack; `BLOCKED` routes to `devflow-router` only when the blocker is route/profile/scope related.

### 10. 派发 reviewer subagent

review 节点不在父会话内联执行。构造最小 review request（`target_skill`、`work_item_id`、`owning_component`、`primary_artifact`、`supporting_context`、`agents_md_anchor`、`expected_return_contract`），派发独立 subagent，消费结构化 reviewer 返回。详见 `references/reviewer-dispatch-protocol.md`。

### 11. 连续执行与暂停点

路由结论不是独立用户交互：

- 非 hard stop → 同一轮进入目标 skill
- review 节点 → 立刻派发 subagent
- approval step → 按 Execution Mode 处理
- hard stop（缺组件设计、缺测试设计章节、TDD 后未经 test-checker、SR-flow 试图进入实现节点等）→ 必须停下等待

## Output Contract

最小输出：

- `Current Stage`
- `Workflow Profile`
- `Execution Mode`
- `Target Skill`（唯一 canonical `devflow-*` 节点）
- `Why`（1-2 条决定性证据）
- `reroute_via_router`：`false`（已唯一映射）或 `true`（无法唯一映射，等待父会话）

evidence 充足时使用紧凑格式；不回放未命中分支，不复述 authority 说明。

runtime canonical 字段统一：`devflow-router`、`reroute_via_router`，不出现自由文本下一步。

## Red Flags

- 没经过 router 就跨节点切换
- 因命令名 / 用户点名跳过 route / profile 判断
- 把 `using-devflow` 写进 runtime handoff
- 在 route 阶段做大范围代码探索
- 忽略证据冲突沿用旧印象推进
- 把 `auto` 解读为「不写 review record / 不要 approval」
- 父会话内联 review，没派发 reviewer subagent
- profile 不再成立却不升级（如修改影响 SOA 接口却仍走 standard）

## Common Mistakes

| 错误 | 修复 |
|---|---|
| TDD 完成后直接路由到 `devflow-code-review` | 必须先派发 `devflow-test-checker` |
| 看到 AR 设计修改了组件接口，仍走 standard | 升级到 component-impact，先 `devflow-component-design` |
| review 返回 `阻塞`(workflow) 还硬选下一节点 | 标 `reroute_via_router=true` 停下 |

## Verification

- [ ] 已确认是 runtime routing（非 family discovery）
- [ ] 已基于最新证据决定 Workflow Profile，并执行升级判断
- [ ] 已归一化 Execution Mode 且未违反 policy
- [ ] 已验证显式 handoff 合法性
- [ ] 推荐节点在当前 profile 合法集合内
- [ ] review 节点已派发独立 reviewer subagent
- [ ] hard stop 命中时已显式停下且写明原因
- [ ] 非 hard stop 时在同一轮继续执行
- [ ] 字段名严格使用 `devflow-router` 与 `reroute_via_router`

## Local DevFlow Conventions

This section is owned by this skill. Do not load a shared conventions file. Project AGENTS.md may override equivalent paths or templates.

### Progress Fields

Use canonical progress fields when this skill reads or writes features/<id>/progress.md:

- Work Item Type: SR / AR / DTS / CHANGE
- Work Item ID: SR1234, AR12345, DTS67890, or CHANGE id
- Owning Component: required for AR / DTS / CHANGE
- Owning Subsystem: required for SR
- Workflow Profile: requirement-analysis / standard / component-impact / hotfix / lightweight
- Execution Mode: interactive / auto
- Current Stage: current canonical devflow node
- Pending Reviews And Gates: pending review or gate list
- Next Action Or Recommended Skill: one canonical node only
- Blockers: open blockers
- Last Updated: timestamp

### Handoff Fields

Return a structured handoff with the fields this skill knows:

- current_node
- work_item_id
- owning_component or owning_subsystem
- result or verdict
- artifact_paths
- record_path, when a review / gate / verification record exists
- evidence_summary
- traceability_links
- blockers
- next_action_or_recommended_skill
- reroute_via_router

Do not set next_action_or_recommended_skill to using-devflow or free text.

### Router Authority

- devflow-router is the runtime authority for profile, execution mode, canonical next node, reviewer dispatch, and review / gate recovery.
- Legal profiles: requirement-analysis, standard, component-impact, hotfix, lightweight.
- If a leaf handoff conflicts with artifact evidence, ignore the handoff and route from evidence.

### Task Routing Fields

For implementation profiles also read Current Active Task, Task Plan Path, and Task Board Path. Multiple in_progress tasks or ambiguous next-ready tasks are workflow blockers.
## Supporting References

| 文件 | 用途 |
|---|---|
| `references/profile-and-route-map.md` | 各 profile 主链与支线、Hard Stops |
| `references/reviewer-dispatch-protocol.md` | reviewer subagent 派发协议与返回契约 |
