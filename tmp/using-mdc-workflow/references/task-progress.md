# Task Progress

使用说明：

- 这是 `mdc` 中的通用任务进度模板。
- 适合记录当前目标、workflow 状态、证据和下一步；可与 `mdc-*` workflow skills 配合使用（runtime 编排以 `using-mdc-workflow` 为准）。
- 建议保存在仓库根目录或 `docs/` 下的合适位置。
- 若当前项目采用 `mdc-*` workflow，优先使用下面的 canonical 字段名。
- 该模板定义的是 minimal canonical core；项目可按需追加附加工件区块，但不应改写核心字段名。
- 若 workflow 需要 task-to-task 自动推进，建议额外提供 `Task Board Path` 或等价队列投影视图；`Current Active Task` 只记录当前锁定任务，不承担整个任务队列状态。

## Goal

- Goal:
- Owner:
- Status:
- Last Updated:

## Current Workflow State

- Current Stage:
- Workflow Profile:
- Execution Mode:
- Current Active Task:
- Pending Reviews And Gates:
- Relevant Files:
- Constraints:

## Progress Notes

- What Changed:
- Evidence Paths:
- Session Log:
- Open Risks:

## Optional Coordination Fields

- Task Board Path:
- Task Queue Notes:
- Workspace Isolation:
- Worktree Path:
- Worktree Branch:

## Next Step

- Next Action Or Recommended Skill:
- Blockers:
- Notes:
