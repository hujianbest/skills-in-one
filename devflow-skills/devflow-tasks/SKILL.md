---
name: devflow-tasks
description: Use when devflow-ar-design-review has passed and the approved AR implementation design must be mapped into an executable task plan / task board before TDD, when task planning was rejected and needs revision, or when progress visibility requires Current Active Task tracking. Not for designing tests (→ devflow-ar-design), not for implementing code (→ devflow-tdd-implementation), not for stage confusion (→ devflow-router).
---

# devflow 任务执行索引

把已批准的 AR 实现设计（含测试设计章节）映射成可执行任务计划和 task board。`devflow-tasks` 不重新设计测试，不新增业务事实；它只把已批准设计中的功能点、Case ID、文件、依赖、验证方式和完成定义组织成 TDD 可逐项执行的队列。

## When to Use

适用：

- `devflow-ar-design-review` verdict = `通过`，且开发负责人确认可以进入执行计划
- `devflow-tasks-review` 返回 `需修改` / `阻塞`，需修订任务计划
- 当前 work item 需要通过 `Current Active Task` / `task-board.md` 感知开发进度

不适用 → 改用：

- AR 设计或测试设计仍不充分 → `devflow-ar-design`
- 直接实现当前 active task → `devflow-tdd-implementation`
- task queue 与 profile / route 冲突 → `devflow-router`

## Hard Gates

- AR 设计未通过 `devflow-ar-design-review` 前不得开始
- tasks 不得新增测试用例；只能引用 AR 设计中的 Test Design Case ID
- tasks 不得补写设计事实；缺功能点、缺 Case ID、缺接口 / 文件范围 → 回 `devflow-ar-design`
- 每个可执行任务必须包含 Acceptance、Files、Verify、DoD、需求 / 设计 / 测试追溯
- 不允许多个 `in_progress` task；无法唯一选出 `Current Active Task` → 回 `devflow-router`
- tasks 未通过 `devflow-tasks-review` 前不得进入 `devflow-tdd-implementation`

## Object Contract

- Primary Object: task execution index（`tasks.md` + `task-board.md`）
- Frontend Input Object: `features/<id>/ar-design-draft.md`（已通过 review，含测试设计章节）、`features/<id>/requirement.md`、`features/<id>/traceability.md`、`features/<id>/reviews/ar-design-review.md`、`docs/component-design.md`
- Backend Output Object:
  - `features/<id>/tasks.md`
  - `features/<id>/task-board.md`
  - `features/<id>/traceability.md` task 列补充
  - `features/<id>/progress.md` canonical 同步
- Object Transformation: 把设计中的功能点 / Test Case / 文件 / 验证映射为可执行任务队列
- Object Boundaries: 不设计测试 / 不写代码 / 不改组件设计 / 不决定业务优先级

## Methodology

- **Task As Execution Index**: tasks 是设计到执行的索引层，不是测试设计层
- **Design-Case Mapping**: 每个任务必须引用 AR 设计章节和 Test Design Case ID
- **Single Active Task**: task board 中最多一个 `in_progress`
- **Dependency-Driven Queue**: 用依赖、ready 条件和优先级选择唯一 next-ready task
- **TDD Slice Discipline**: 任务粒度要足以完成 RED → GREEN → REFACTOR，并可被 test-check / code-review 独立审查

## Workflow

### 1. 读取已批准设计

读取 `ar-design-draft.md`、`reviews/ar-design-review.md`、`requirement.md`、`traceability.md`、`docs/component-design.md` 和 `progress.md`。确认 AR 设计 review = `通过`，且测试设计章节包含 Case ID、覆盖要求、Mock / Stub / Sim、RED / GREEN 证据计划。

缺任一关键输入 → blocked-content，回 `devflow-ar-design` 或 `devflow-router`。

### 2. 判断是否具备拆解条件

只有在以下条件都满足时才写完整 tasks：

- 功能点可回指 requirement row
- 测试设计 Case ID 可回指功能点和 requirement row
- 受影响文件 / 模块 / 类 / 接口足以判断任务边界
- 关键依赖和执行顺序可判断
- 验证方式可从测试设计章节和组件约束中得到

若不满足，写出阻塞项并回 `devflow-ar-design`，不要伪造任务计划。

### 3. 编写 `tasks.md`

按 `references/devflow-tasks-template.md` 写 `features/<id>/tasks.md`。每个任务至少包含：

- Task ID
- Goal
- Acceptance
- Files
- Covers Requirement
- AR Design Anchor
- Test Design Case IDs
- Dependencies
- Verify
- Definition of Done
- Expected Evidence Paths
- Notes / Assumptions

任务粒度应能让 `devflow-tdd-implementation` 对单个 task 执行完整 RED → GREEN → REFACTOR；不得把“完成整个模块 / 后面再验证”作为任务。

### 4. 编写 `task-board.md`

按 `references/devflow-task-board-template.md` 写 `features/<id>/task-board.md`。初始化 queue：

- 无前置依赖且优先级最高的唯一任务 → `ready`
- 依赖未满足 → `pending`
- 若无法唯一选出首个 ready task → 标 `blocked`，回 `devflow-router`

### 5. 同步 traceability 与 progress

在 `traceability.md` 补 Task ID / Test Design Case ID / planned evidence 列。

把 `progress.md` 写为：

- `Current Stage = devflow-tasks`
- `Task Plan Path = features/<id>/tasks.md`
- `Task Board Path = features/<id>/task-board.md`
- `Current Active Task = <唯一 ready task 或空>`
- `Pending Reviews And Gates` 含 `tasks-review`
- `Next Action Or Recommended Skill = devflow-tasks-review`

### 6. 自检与 handoff

自检：每个关键需求有 task；每个 task 有 Acceptance / Files / Verify / DoD；每个 task 引用 AR 设计章节和 Test Design Case ID；依赖无环；只有一个 next-ready task；没有新增测试设计事实。通过后派发 `devflow-tasks-review`。

## Output Contract

- `features/<id>/tasks.md`
- `features/<id>/task-board.md`
- `traceability.md` 补 task 追溯
- `progress.md` canonical 同步，下一步 `devflow-tasks-review`
- handoff 摘要按 Local DevFlow Conventions

## Red Flags

- 在 tasks 中新增 AR 设计没有的测试用例
- 任务缺 Verify 或 DoD
- 一个任务覆盖多个无关功能点，无法单独验证
- 多个 task 同时 `in_progress`
- task 依赖循环或 next-ready task 不唯一
- 把 tasks 写成设计摘要，而不是执行索引

## Verification

- [ ] `tasks.md` 已落盘
- [ ] `task-board.md` 已落盘，最多一个 `in_progress`
- [ ] 每个 task 都有 Acceptance / Files / Verify / DoD
- [ ] 每个 task 都回指 requirement row、AR 设计章节、Test Design Case ID
- [ ] 依赖关系无环，next-ready task 唯一或明确 blocked
- [ ] progress.md 下一步为 `devflow-tasks-review`

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

### Task Planning Fields

Maintain Current Active Task, Task Plan Path, and Task Board Path after task planning. There must be at most one in_progress task.

### Tasks.md Minimum Content

Include metadata, plan boundary, milestones, task breakdown, dependency map, traceability, verification strategy, risks, and open items. Each task needs Task ID, goal, acceptance, files, requirement coverage, AR design anchor, Test Design Case IDs, dependencies, verify command, DoD, and expected evidence paths.
## Supporting References

| 文件 | 用途 |
|---|---|
| `references/devflow-tasks-template.md` | tasks.md 模板 |
| `references/devflow-task-board-template.md` | task-board.md 模板 |
