# edf Tasks Review Rubric

> 配套 `edf-tasks-review/SKILL.md`。tasks 是 AR 设计到 TDD 执行的索引层，不是二次测试设计。

## 6 维度评分

| 维度 | 关键检查 |
|---|---|
| **TR1 Executability** | 关键任务可冷启动，粒度可完成一个 RED → GREEN → REFACTOR 闭环，无“大任务” |
| **TR2 Task Contract Completeness** | 每个关键任务有 Acceptance、Files、Verify、Definition of Done、Expected Evidence |
| **TR3 Verification Seeds** | Verify 字段足以支持 fail-first；引用 AR 测试设计 Case ID，不新增测试设计事实 |
| **TR4 Dependency & Order** | 依赖、关键路径、串并行关系清晰，无循环依赖 |
| **TR5 Traceability Coverage** | 任务可回指 requirement row、AR 设计章节、Test Design Case ID |
| **TR6 Router Readiness** | task-board 能唯一选择 Current Active Task / next-ready task |

任一关键维度 < 6 不得 `通过`。

## Rule IDs

### Group TR1 - Executability

- `TR1.1` 任务可由开发者冷启动
- `TR1.2` 任务粒度足以独立验证
- `TR1.3` 任务不是设计摘要或大块“完成模块”

### Group TR2 - Contract

- `TR2.1` Acceptance 明确
- `TR2.2` Files 列出预计触碰工件或明确待确认理由
- `TR2.3` Verify 是可运行命令 / 明确检查步骤
- `TR2.4` DoD 不依赖“后面统一验证”
- `TR2.5` Expected Evidence Paths 明确

### Group TR3 - Verification Seeds

- `TR3.1` 任务引用 AR 设计 Test Design Case ID
- `TR3.2` Verify 足以驱动 RED / GREEN
- `TR3.3` 未在 tasks 中新增 AR 设计没有的测试用例

### Group TR4 - Dependency

- `TR4.1` Depends On 清晰
- `TR4.2` Ready When 可判定
- `TR4.3` 无循环依赖
- `TR4.4` 串行 / 并行关系明确

### Group TR5 - Traceability

- `TR5.1` 每个任务回指 requirement row
- `TR5.2` 每个任务回指 AR 设计章节
- `TR5.3` 每个任务回指 Test Design Case ID
- `TR5.4` 核心 requirement row 均被至少一个任务覆盖

### Group TR6 - Router Readiness

- `TR6.1` task-board 最多一个 `in_progress`
- `TR6.2` next-ready task 唯一
- `TR6.3` Selection Rule 与依赖状态一致
- `TR6.4` 无法唯一选择时明确回 `edf-workflow-router`

## Severity 分级

- `critical`：next-ready task 不唯一、任务缺 Verify、任务与测试设计 Case ID 脱节、依赖循环
- `important`：Files / DoD / Evidence 字段不完整、任务粒度过大、追溯缺单个字段
- `minor`：命名、排版、说明文字可读性问题

## Verdict 决策

| 评分 / findings 状态 | verdict |
|---|---|
| TR1-TR6 均 ≥ 6、无 critical、next-ready task 唯一 | `通过` |
| 字段缺口或粒度问题可定向修订 | `需修改` |
| 缺上游设计 / 测试设计 Case ID，或任务计划无法建立执行队列 | `阻塞`（内容） |
| next-ready task 不唯一 / route 冲突 / 依赖状态冲突 | `阻塞`（workflow） + `reroute_via_router=true` |
