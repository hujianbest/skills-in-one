---
name: devflow-tasks-review
description: Use when devflow-tasks has produced tasks.md and task-board.md and an independent verdict is needed before TDD, when task planning needs re-review after revision, or when Current Active Task / next-ready task selection must be audited. Not for writing tasks (→ devflow-tasks), not for implementation (→ devflow-tdd-implementation), not for stage confusion (→ devflow-router).
---

# devflow 任务计划评审

独立评审 `features/<id>/tasks.md` 与 `features/<id>/task-board.md`，判断它们是否能作为 `devflow-tdd-implementation` 的执行索引。reviewer 不补任务、不设计测试、不写代码，只产出 verdict + findings + 唯一下一步。

## When to Use

适用：

- `devflow-tasks` 已产出 tasks.md / task-board.md
- reviewer subagent 被派发执行 tasks review
- tasks 修订后需要复审

不适用 → 改用：

- 继续编写任务计划 → `devflow-tasks`
- 开始当前 active task 的 TDD → `devflow-tdd-implementation`
- 阶段 / profile / task queue 冲突 → `devflow-router`

## Hard Gates

- tasks-review 通过前不得进入 `devflow-tdd-implementation`
- reviewer 不补任务、不新增测试用例、不改 task board
- 每个关键任务缺 Acceptance / Files / Verify / DoD → 不得通过
- 任务未回指 requirement row、AR 设计章节、Test Design Case ID → 不得通过
- next-ready task 不唯一、依赖循环或多个 `in_progress` → `阻塞`(workflow)，回 `devflow-router`

## Object Contract

- Primary Object: task plan review finding set + verdict
- Frontend Input Object: `tasks.md`、`task-board.md`、`ar-design-draft.md`、`requirement.md`、`traceability.md`、`progress.md`
- Backend Output Object: `features/<id>/reviews/tasks-review.md` + 结构化 reviewer 返回摘要
- Object Boundaries: 不修改任务计划 / 不设计测试 / 不写代码
- Object Invariants: verdict ∈ {`通过`, `需修改`, `阻塞`}

## Workflow

### 1. 建立证据基线

读取 tasks.md、task-board.md、ar-design-draft.md（含测试设计章节）、requirement.md、traceability.md、progress.md。缺 tasks.md 或 task-board.md → blocked-content，下一步 `devflow-tasks`。

### 2. Precheck

- AR 设计 review 未通过 → blocked-workflow，`reroute_via_router=true`
- tasks 中出现 AR 设计没有的测试用例 / 设计事实 → blocked-content，下一步 `devflow-tasks`
- 多个 `in_progress` task 或 next-ready task 不唯一 → blocked-workflow，`reroute_via_router=true`
- 否则进入评分

### 3. 多维评分

按 `references/tasks-review-rubric.md` 的 TR1-TR6 做 0-10 评分：

| 维度 | 关注 |
|---|---|
| TR1 Executability | 关键任务可冷启动，无大任务 |
| TR2 Task Contract Completeness | Acceptance / Files / Verify / DoD 完整 |
| TR3 Verification Seeds | Verify 足以支持 fail-first / RED-GREEN |
| TR4 Dependency & Order | 依赖 / 关键路径清晰、无循环 |
| TR5 Traceability Coverage | 任务可回指规格 / 设计 / Test Case |
| TR6 Router Readiness | Current Active Task / next-ready task 选择规则唯一 |

任一关键维度 < 6 不得 `通过`。

### 4. Checklist 审查

每条 finding 记录 `severity` / `classification` / `rule_id` / `anchor` / 描述 / 建议修复。缺少业务事实或优先级拍板 → `USER-INPUT`；可补字段 / 调整粒度 → `LLM-FIXABLE`；涉及组件边界 / 测试策略缺口 → `TEAM-EXPERT` 或回上游。

### 5. 形成 verdict

| 条件 | conclusion | `next_action_or_recommended_skill` | reroute_via_router | needs_human_confirmation |
|---|---|---|---|---|
| TR1-TR6 均 ≥ 6、任务合同完整、next-ready task 唯一、无新增测试设计事实 | `通过` | `devflow-tdd-implementation` | `false` | `true`（开发负责人确认开始执行） |
| 任务粒度 / 字段 / 追溯可 1-2 轮定向修订 | `需修改` | `devflow-tasks` | `false` | `false` |
| 缺设计输入 / 测试设计缺 Case ID / task 无法映射设计 | `阻塞`（内容） | `devflow-tasks` 或 `devflow-ar-design` | `false` | `false` |
| next-ready task 不唯一 / 依赖冲突 / route 或 profile 冲突 | `阻塞`（workflow） | `devflow-router` | `true` | `false` |

### 6. 写 review 记录并回传

按 `references/devflow-review-record-template.md` 写 `features/<id>/reviews/tasks-review.md`，并回传结构化摘要。

## Output Contract

- Review record：`features/<id>/reviews/tasks-review.md`
- 结构化 reviewer 返回摘要含 record_path、conclusion、key_findings、finding_breakdown、`next_action_or_recommended_skill`、needs_human_confirmation、reroute_via_router

## Red Flags

- 任务没有 Verify，却给通过
- 任务和测试设计 Case ID 脱节
- task-board 有多个 `in_progress`
- reviewer 顺手改 tasks.md
- 把 tasks-review 当成测试设计评审

## Verification

- [ ] review record 已落盘
- [ ] TR1-TR6 评分完整
- [ ] 每个 finding 已分类
- [ ] verdict 唯一、下一步唯一
- [ ] `通过` 时 next_action 为 `devflow-tdd-implementation`

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

### Tasks Review Record

Write features/<id>/reviews/tasks-review.md unless AGENTS.md overrides it.

### Review Boundary

Review task granularity, dependencies, Test Design Case IDs, verification commands, DoD, active/ready state, and next-ready uniqueness. Ambiguous queue state routes to devflow-router.
## Supporting References

| 文件 | 用途 |
|---|---|
| `references/tasks-review-rubric.md` | TR1-TR6 rubric |
| `references/devflow-review-record-template.md` | review record 模板 |
