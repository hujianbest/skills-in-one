# devflow 任务看板模板

使用说明：

- 默认保存路径：`features/<工作项ID>-<slug>/task-board.md`。
- `tasks.md` 定义任务拓扑、依赖与完成条件；task-board 只投影当前状态。
- `Current Active Task（当前活跃任务）` 以 `progress.md` 为权威；本文件最多一个 `in_progress`，且必须与 `progress.md` 保持一致。
- 若 task-board 与已批准 tasks.md 冲突，或无法唯一判断 next-ready task，停止自动推进并回 `devflow-router`。

## 元数据

- 工作项 ID:
- 来源任务计划:
- 看板路径:
- Owner:
- 最后更新:
- 看板模式: `artifact-first + board-assisted`
- 实现模式: controller-direct / implementer-subagent

## 选择规则

- 当前活跃任务:
- 选择规则:
  - 选择依赖已满足、状态为 `ready` 的唯一最高优先级任务
- 冲突策略:
  - 若存在多个同等候选，或依赖 / 状态冲突，则回 `devflow-router`
- Ready 语义:
- Done 语义:

## 状态词汇

- `pending`: 前置依赖或 ready 条件尚未满足
- `ready`: 可被 router 锁定为下一任务
- `in_progress`: 已被锁定为当前唯一活跃任务
- `done`: 当前任务已完成 TDD、test-check、code-review、completion-gate 的 task-level 质量链
- `blocked`: 任务当前无法推进，需要外部条件或上游修订
- `cancelled`: 任务已失效、被改范围覆盖或不再执行

## 实现派发状态词汇

- `not_dispatched`: controller 尚未将此任务派发给实现者
- `dispatched`: 新的实现者 subagent 已收到上下文包
- `needs_context`: 实现者请求补充信息
- `blocked`: 实现者无法安全继续
- `done`: 实现者报告 DONE
- `done_with_concerns`: 实现者报告 DONE_WITH_CONCERNS
- `review_ready`: controller 已处理 concerns，可派发 `devflow-test-checker`

## 队列快照

- Ready 任务:
- Pending 任务:
- Blocked 任务:
- Done 任务:
- 最近完成记录:
- 当前实现派发状态:
- 当前上下文包:
- 当前实现报告:
- 下一步 router 动作:

## 任务队列

| 任务 ID | 标题 | 状态 | 依赖 | 就绪条件 | 选择优先级 | 测试设计用例 ID | 派发状态 | 上下文包 | 实现报告 | 证据路径 | 阻塞原因 | 最近结果 / 记录 | 备注 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T1 | <任务标题> | ready | - | task queue preflight passed | P1 |  | not_dispatched |  |  |  |  | N/A |  |

## 实现上下文包索引

| 任务 ID | 上下文包路径 / 摘要 | 允许修改文件 | 验证命令 | 硬停止条件 |
|---|---|---|---|---|
| T1 |  |  |  |  |

## 状态变更日志

- 日期:
  - 变更:
  - 证据 / 记录:

## 备注

- 其他备注:
