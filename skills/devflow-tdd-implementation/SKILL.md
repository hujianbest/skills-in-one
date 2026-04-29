---
name: devflow-tdd-implementation
description: 当 devflow-ar-design-review 已通过，需要把已批准的 AR 设计映射成任务队列并通过 C/C++ TDD 实现时使用；也用于继续 Current Active Task，或按 devflow-test-checker、devflow-code-review 的需修改结论回修实现，或接收 devflow-problem-fix 交接的复现与修复边界。不用于编写 AR 设计、修改组件设计、测试有效性评审、代码评审，或路由恢复。
---

# devflow TDD 实现

把已批准的 AR 设计转成 task queue，锁定唯一 `Current Active Task`，在实现上下文较大时派发聚焦的 implementer subagent，并记录 fresh evidence。任务规划现在是本 skill 的内部 preflight，不再是独立 workflow node。

本 skill 不写 AR 设计、不改变 AR 范围、不自审测试、不自审代码；这些职责分别属于 `devflow-ar-design`、`devflow-test-checker`、`devflow-code-review`。

## 适用场景

适用：

- `devflow-ar-design-review` 已通过，需要建立 task queue 并执行 TDD。
- `tasks.md` / `task-board.md` 已存在，work item 需要继续 `Current Active Task`。
- `devflow-test-checker` 或 `devflow-code-review` 对实现工作返回 `needs changes`。
- `devflow-problem-fix` 已交接复现、根因和安全修复边界。

不适用 → 改用：

- AR 设计缺失、未评审或缺测试设计：使用 `devflow-ar-design`。
- 变更影响组件边界、SOA 接口、依赖或状态机：使用 `devflow-router` / `devflow-component-design`。
- 测试需要独立有效性审查：使用 `devflow-test-checker`。
- 代码需要独立评审：使用 `devflow-code-review`。

## 硬性门禁

- `devflow-ar-design-review` 通过前不得开始。
- task queue preflight 通过前不得进入 RED。
- `Current Active Task` 必须唯一并与 `task-board.md` 一致。
- 每个 task 必须包含 Test Design Case IDs、Verify、Definition of Done。
- 不得发明已批准 AR 设计之外的测试或业务事实。
- 不得跳过 RED。
- GREEN 阶段不得做 cleanup。
- REFACTOR 必须留在当前 task 边界内。
- 不得自称测试有效或代码质量合格；下一步派发 `devflow-test-checker`。

## 对象契约

- Primary Object: task-scoped implementation slice（task 范围内实现切片）
- Frontend Input Object: 已批准的 `ar-design-draft.md`、`ar-design-review.md`、`requirement.md`、`traceability.md`、可选既有 `tasks.md` / `task-board.md`、component design、当前代码、`AGENTS.md`、`progress.md`。
- Backend Output Object: `tasks.md`、`task-board.md`、C/C++ 代码变更、测试代码变更、`implementation-log.md`、fresh evidence、traceability 更新、progress 更新。
- Boundaries: 不改组件边界、不改 AR 范围、不自审。

## 方法原则

- **Task Queue As Execution Index**: `tasks.md` 与 `task-board.md` 把已批准设计映射成可执行 TDD 切片。
- **Design-Case Mapping**: 每个 task 回指 requirement rows、AR design anchors、Test Design Case IDs。
- **Single Active Task**: 只能有一个 task 处于 active 或 in progress。
- **Embedded TDD**: RED -> GREEN -> REFACTOR。
- **Two Hats**: implementation 与 refactoring 必须分开。
- **Fresh Evidence**: RED / GREEN / REFACTOR evidence 必须由当前会话生成。
- **Fresh Implementer Context**: controller 只给 implementer subagent 当前 task context pack，不给整段会话历史。

## Subagent 执行模式

实现 `Current Active Task` 时默认使用此模式，尤其是读写代码会把大量上下文拉进 controller session 时。controller 仍负责 routing、task queue 状态、evidence 路径和最终 handoff。

不要让 implementer subagent 读取完整计划、历史聊天或大范围仓库上下文。先构建 context pack，把必要事实直接放进派发 prompt。

### Implementer Context Pack

派发 implementer subagent 前，基于已批准产物写出或组装以下 context pack：

```markdown
## Implementer Context Pack
- Work Item Type / ID:
- Owning Component:
- Current Active Task:
- Task Goal:
- Acceptance:
- Files allowed to inspect/edit:
- Files explicitly out of scope:
- Requirement Rows:
- AR Design Anchors:
- Test Design Case IDs:
- Existing Test Harness / Commands:
- Verify Commands:
- Evidence Paths To Write:
- Component Boundary Constraints:
- Hard Stops:
  - requirements、acceptance、approach 或 dependencies 不清楚时先问
  - task 需要 component-boundary 或 architecture 决策时停止
  - 不添加 approved AR design 中不存在的测试或行为
```

### Implementer 状态处理

implementer subagent 返回以下状态之一：

- `DONE`: 实现与 fresh evidence 已就绪；controller 记录报告并派发 `devflow-test-checker`。
- `DONE_WITH_CONCERNS`: 实现已完成但 subagent 标出不确定点；controller 在 test-checker 前先处理 concerns。
- `NEEDS_CONTEXT`: controller 补充缺失上下文，并用更收敛的 context pack 重新派发。
- `BLOCKED`: controller 判断路由到 `devflow-ar-design`、`devflow-router`，或继续拆分 task。

implementer 的 self-review 有价值，但永远不能替代 `devflow-test-checker` 或 `devflow-code-review`。

## 工作流

### 1. 对齐输入与 work item

读取已批准 AR 设计、AR design review、requirement、traceability、已有 task queue 产物（如存在）、component design、`AGENTS.md`、代码上下文和 `progress.md`。

如果 AR design review 未通过、测试设计缺失或 work item 身份不明确，立即停止。

### 2. 创建或校验 task queue

如果 `features/<id>/tasks.md` 或 `task-board.md` 缺失，按已批准 AR 设计和 `references/task-plan-template.md` / `references/task-board-template.md` 创建。若已存在，只对照当前已批准 AR 设计和 requirement 校验，避免无关重写。

每个 task 必须包含 Task ID、Goal、Acceptance、Files、Covers Requirement、AR Design Anchor、Test Design Case IDs、Dependencies、Verify、Definition of Done、Expected Evidence Paths、notes/assumptions。

Task queue preflight 检查：

- TR1 Executability：每个 task 可冷启动，且粒度不能过大。
- TR2 Contract：Acceptance、Files、Verify、DoD 完整。
- TR3 Verification Seeds：Verify 支持 fail-first RED/GREEN 工作。
- TR4 Dependency：依赖清晰且无环。
- TR5 Traceability：task 映射到 requirement row、AR design 和 test case。
- TR6 Router Readiness：task-board 能选择唯一 `Current Active Task` 或 next-ready task。

如果 preflight 因 AR 设计信息缺失而失败，路由到 `devflow-ar-design`；如果 queue 状态不明确，路由到 `devflow-router`。

### 3. 检查组件边界

把计划变更与 component design 对照。若 task 触及组件接口、依赖、状态机或 SOA boundary，停止并路由到 `devflow-router` 处理 component-impact。

### 4. 准备 Implementer Context Pack

为 `Current Active Task` 创建 Implementer Context Pack。派发前把路径或摘要记录到 `task-board.md`。若 pack 无法做到小而精确，说明 task 太宽，应先拆分或收敛。

### 5. 派发 Implementer Subagent

派发新的 implementer subagent，只提供 context pack、允许的文件范围和预期 evidence 路径。implementer 在受限上下文中执行下面步骤 6-10。若 subagent 提问，在 controller session 中回答，并用澄清后的 context pack 重新派发。

对极小的单文件修改，若上下文已经很小，controller 可直接实现，但仍必须遵守同一套 RED / GREEN / REFACTOR evidence 规则。

### 6. 从测试设计落地测试

识别既有 test harness、build scripts、CI 配置、邻近组件测试和团队 mock/fixture 风格。若目标没有可运行 harness，先搭建最小 smoke-tested harness 并记录 bootstrap evidence。Harness failure 不是业务 RED。

只实现 `Current Active Task` 对应 Test Design Case IDs 的测试。名称或注释中保留 Task ID 与 Case ID 锚点。

### 7. RED

运行新增测试，并在 `features/<id>/evidence/unit/` 或 `evidence/integration/` 下记录有效 RED evidence。Evidence 包含命令、退出码、失败摘要、失败为何匹配预期行为缺口，以及 freshness anchor。

### 8. GREEN

写最小实现让 RED 变 GREEN。记录 GREEN evidence，包含命令、退出码、通过摘要、关键结果和 freshness anchor。GREEN 阶段不得 refactor。

### 9. REFACTOR

只有测试已绿后，才按需做 task 范围内 cleanup。遵循 `references/red-green-refactor-discipline.md`。每次 cleanup 后重新运行测试；若发生 cleanup，记录 REFACTOR evidence。

### 10. 静态与动态证据

运行 build、static analysis 和相关 regression checks。遵循 `references/embedded-evidence-checklist.md`。未解释的 critical 问题阻塞 handoff。

### 11. Implementation Log 与 Traceability

把 `Current Active Task`、implementer status/report、changed files、decisions、RED/GREEN/REFACTOR evidence、test results 和 open risks 写入 `implementation-log.md`。用 Task ID、Code File、Test Code File、Verification Evidence 更新 traceability。

### 12. Progress 与 Handoff

更新 progress 字段：Current Stage、Task Plan Path、Task Board Path、Current Active Task、Pending Reviews And Gates、`Next Action Or Recommended Skill = devflow-test-checker`。同步 `task-board.md` 的 dispatch status、context pack location/summary、implementation report、evidence paths 和 blocked reason（如有）。

派发独立 reviewer subagent 执行 `devflow-test-checker`；不要内联执行测试评审。

## 输出契约

- `features/<id>/tasks.md` 与 `task-board.md` 已创建或已校验。
- 使用 subagent mode 时，已为 `Current Active Task` 记录 Implementer Context Pack。
- `Current Active Task` 对应的 C/C++ 代码与测试代码。
- `implementation-log.md` 含 handoff block。
- `evidence/{unit,integration,static-analysis,build}/` 下有 fresh evidence。
- traceability 与 progress 已更新。
- 下一步：`devflow-test-checker`。

## 风险信号

- task queue preflight 通过前就开始实现。
- 派发 implementer subagent 时给了大段聊天历史，而不是精选 context pack。
- 让 implementer 自己探索完整计划或不受限仓库上下文。
- 存在多个 active 或 in-progress tasks。
- 添加 AR 设计中不存在的测试。
- 把 harness setup failure 当成业务 RED。
- RED 前写实现。
- GREEN 阶段 refactor。
- 在实现中改变组件边界。
- 复用 stale evidence。
- 自行批准测试或代码。

## 验证清单

- [ ] Work item identity 稳定
- [ ] Task queue preflight 已通过
- [ ] Current Active Task 唯一且匹配 task-board
- [ ] 使用 subagent mode 时，Implementer Context Pack 小而明确且已记录
- [ ] Implementer status 为 DONE 或 DONE_WITH_CONCERNS，且 concerns 已在 review 前处理
- [ ] Test Design Case IDs 已驱动本轮工作
- [ ] RED、GREEN 和可选 REFACTOR evidence 都是 fresh
- [ ] Build / static / regression evidence 已记录
- [ ] `implementation-log.md` 已包含 handoff information
- [ ] `traceability.md` 已更新
- [ ] `progress.md` 已路由到 `devflow-test-checker`

## 本地测试设计契约摘录

本 skill 使用的每个 test design case 需要包含：case id、requirement row 或 design anchor、behavior under test、preconditions、inputs/stimuli、expected output 或 observable effect、mock/stub/simulation boundary、verification command 或 evidence path、embedded risk covered。DevFlow 不使用单独的 `test-design.md`；测试设计位于 AR design 中。

## 本地 DevFlow 约定

本节由当前 skill 自己维护。不要加载共享约定文件；项目 `AGENTS.md` 可以覆盖等价路径或模板。

### 产物布局

默认产物布局来自 `docs/principles/03 artifact-layout.md`。项目 `AGENTS.md` 可以覆盖等价路径；没有覆盖时，本 skill 必须使用以下组件仓库布局：

```text
<component-repo>/
  docs/
    component-design.md           # 长期组件实现设计
    ar-designs/                   # 长期 AR 实现设计
      AR<id>-<slug>.md
    interfaces.md                 # 可选；仅团队启用时读取 / 同步
    dependencies.md               # 可选；仅团队启用时读取 / 同步
    runtime-behavior.md           # 可选；仅团队启用时读取 / 同步

  features/
    AR<id>-<slug>/                # 单个 AR 的过程产物
    DTS<id>-<slug>/               # 单个缺陷 / 问题修复的过程产物
    CHANGE<id>-<slug>/            # 单个轻量变更的过程产物
```

`docs/` 存放随代码提交的长期组件资产。`features/<id>/` 存放单个 work item 的过程产物：按需包含 `README.md`、`progress.md`、`requirement.md`、`ar-design-draft.md`、`tasks.md`、`task-board.md`、`traceability.md`、`implementation-log.md`、`reviews/`、`evidence/`、`completion.md`、`closeout.md`。

Read-on-presence 规则：

- 必需长期资产缺失时阻塞：component-impact 工作需要 `docs/component-design.md`；implementation closeout 前需要 `docs/ar-designs/AR<id>-<slug>.md`。
- 可选资产（`docs/interfaces.md`、`docs/dependencies.md`、`docs/runtime-behavior.md`）仅在项目启用时读取 / 同步。缺失的可选资产记录为 `N/A (project optional asset not enabled)`，不视为阻塞。
- 过程目录保留在 `features/` 下；不要把已关闭 work item 移到 `features/archived/`，否则会破坏追溯链接。

### Progress 字段

本 skill 读写 `features/<id>/progress.md` 时使用 canonical progress 字段：

- Work Item Type
- Work Item ID
- Owning Component / Owning Subsystem
- Workflow Profile
- Execution Mode
- Current Stage
- Pending Reviews And Gates
- Task Plan Path
- Task Board Path
- Current Active Task
- Implementer Dispatch Status
- Implementer Context Pack
- Implementation Report
- Next Action Or Recommended Skill
- Blockers
- Last Updated

### Handoff 字段

返回 `current_node`、`work_item_id`、`owning_component`、`artifact_paths`、`evidence_summary`、`traceability_links`、`blockers`、`next_action_or_recommended_skill`、`reroute_via_router`。

不要把 `next_action_or_recommended_skill` 设为 `using-devflow` 或自由文本。

## 支撑参考

| 文件 | 用途 |
|---|---|
| `references/task-plan-template.md` | task queue plan 模板 |
| `references/task-board-template.md` | task-board 状态投影模板 |
| `references/red-green-refactor-discipline.md` | RED / GREEN / REFACTOR 纪律 |
| `references/embedded-evidence-checklist.md` | 证据采集检查清单 |
| 本地测试设计契约摘录 | 测试设计字段契约 |
