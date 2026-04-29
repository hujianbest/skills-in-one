# devflow Task Board

使用说明：

- 这是 `devflow-tdd-implementation` 用于 task-to-task 推进的队列投影模板，默认保存为 `features/<Work Item Id>-<slug>/task-board.md`。
- `tasks.md` 定义任务拓扑、依赖与完成条件；task board 只投影当前状态。
- `Current Active Task` 以 `progress.md` 为权威；本文件最多一个 `in_progress`，且必须与 `progress.md` 保持一致。
- 若 task board 与已批准 tasks.md 冲突，或无法唯一判断 next-ready task，停止自动推进并回 `devflow-router`。

## Metadata

- Work Item ID:
- Source Task Plan:
- Board Path:
- Owner:
- Last Updated:
- Board Mode: `artifact-first + board-assisted`
- Implementation Mode: controller-direct / implementer-subagent

## Selection Rules

- Current Active Task:
- Selection Rule:
  - 选择依赖已满足、状态为 `ready` 的唯一最高优先级任务
- Conflict Policy:
  - 若存在多个同等候选，或依赖 / 状态冲突，则回 `devflow-router`
- Ready Semantics:
- Done Semantics:

## Status Vocabulary

- `pending`: 前置依赖或 ready 条件尚未满足
- `ready`: 可被 router 锁定为下一任务
- `in_progress`: 已被锁定为当前唯一活跃任务
- `done`: 当前任务已完成 TDD、test-check、code-review、completion-gate 的 task-level 质量链
- `blocked`: 任务当前无法推进，需要外部条件或上游修订
- `cancelled`: 任务已失效、被改范围覆盖或不再执行

## Implementer Dispatch Vocabulary

- `not_dispatched`: controller has not sent this task to an implementer
- `dispatched`: fresh implementer subagent has received the context pack
- `needs_context`: implementer asked for missing information
- `blocked`: implementer cannot continue safely
- `done`: implementer reported DONE
- `done_with_concerns`: implementer reported DONE_WITH_CONCERNS
- `review_ready`: controller resolved concerns and can dispatch `devflow-test-checker`

## Queue Snapshot

- Ready Tasks:
- Pending Tasks:
- Blocked Tasks:
- Done Tasks:
- Last Completion Record:
- Current Implementer Dispatch:
- Current Context Pack:
- Current Implementation Report:
- Next Router Action:

## Task Queue

| Task ID | Title | Status | Depends On | Ready When | Selection Priority | Test Design Case IDs | Dispatch Status | Context Pack | Implementation Report | Evidence Paths | Blocked Reason | Last Outcome / Record | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T1 | <task title> | ready | - | task queue preflight passed | P1 |  | not_dispatched |  |  |  |  | N/A |  |

## Implementer Context Pack Index

| Task ID | Context Pack Path / Summary | Allowed Files | Verify Commands | Hard Stops |
|---|---|---|---|---|
| T1 |  |  |  |  |

## State Change Log

- Date:
  - Change:
  - Evidence / Record:

## Notes

- Additional Notes:
