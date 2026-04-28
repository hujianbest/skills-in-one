# Profile Node And Transition Map

这份参考文档集中保存 `using-mdc-workflow` 的 profile 合法节点集合、canonical route map、结果驱动迁移表与恢复编排协议。

当你已经在 workflow 主文件（`using-mdc-workflow/SKILL.md`）中确认：

- 当前请求属于 workflow 场景
- 当前 profile 已确定
- 需要查合法节点、默认链路或结论后的默认下一步

再来这里读取细节。

## 合法状态集合

### full profile 主链推荐节点

- `mdc-specify`
- `mdc-review` (review_type=spec)
- `规格真人确认`
- `mdc-arch-design` (条件：涉及新增组件时执行)
- `mdc-review` (review_type=arch-design)
- `架构设计真人确认`
- `mdc-ar-design`
- `mdc-review` (review_type=ar-design)
- `AR设计真人确认`
- `mdc-tasks`
- `mdc-review` (review_type=tasks)
- `任务真人确认`
- `mdc-test-driven-dev`
- `mdc-test-checker`
- `mdc-code-review`
- `mdc-finalize`

### standard profile 主链推荐节点

- `mdc-specify` (如果规格未批准)
- `mdc-review` (review_type=spec) (如果规格未批准)
- `规格真人确认` (如果规格未批准)
- `mdc-ar-design`
- `mdc-review` (review_type=ar-design)
- `AR设计真人确认`
- `mdc-tasks`
- `mdc-review` (review_type=tasks)
- `任务真人确认`
- `mdc-test-driven-dev`
- `mdc-test-checker`
- `mdc-code-review`
- `mdc-finalize`

### lightweight profile 主链推荐节点

- `mdc-ar-design`
- `mdc-review` (review_type=ar-design)
- `AR设计真人确认`
- `mdc-tasks`
- `mdc-test-driven-dev`
- `mdc-test-checker`
- `mdc-code-review`
- `mdc-finalize`

如果某个用户请求、口头描述或局部记录暗示跳到当前 profile 合法集合之外，按无效迁移处理，回到最近一个有证据支撑的上游节点，或触发 profile 升级。

## Execution Mode Does Not Change The Route Map

`Execution Mode` 只影响 approval step 的解决方式，不改变 profile 的合法节点集合：

- `interactive`：`规格真人确认` 表现为等待用户输入的 approval node
- `auto`：同样保留这个 approval node，但要求先写 approval record，再解锁下游节点
- 不允许把 `mdc-review(spec) -> mdc-ar-design` 直接折叠成"跳过确认节点"

## Canonical Route Map

把下列主骨架视为默认路由图；任何实际迁移都必须同时满足 profile 合法集合、批准证据和迁移表规则：

```text
full:
  mdc-specify -> mdc-review(review_type=spec) -> 规格真人确认 -> 
  [判断: 是否涉及新增组件?] 
    -> 是: mdc-arch-design -> mdc-review(review_type=arch-design) -> 架构设计真人确认 -> mdc-ar-design
    -> 否: mdc-ar-design
  ]
  -> mdc-review(review_type=ar-design) -> AR设计真人确认
  -> mdc-tasks -> mdc-review(review_type=tasks) -> 任务真人确认
  -> mdc-test-driven-dev -> mdc-test-checker -> mdc-code-review
  -> mdc-finalize
  -> [判断: 有唯一 next-ready task? 
    -> 是: using-mdc-workflow (lock next task) -> mdc-test-driven-dev (新任务循环)
    -> 否: workflow 收尾（内嵌 finalize）]

standard:
  (如果规格未批准: mdc-specify -> mdc-review(review_type=spec) -> 规格真人确认)
  -> mdc-ar-design -> mdc-review(review_type=ar-design) -> AR设计真人确认
  -> mdc-tasks -> mdc-review(review_type=tasks) -> 任务真人确认
  -> mdc-test-driven-dev -> mdc-test-checker -> mdc-code-review
  -> mdc-finalize
  -> [判断: 有唯一 next-ready task? 
    -> 是: using-mdc-workflow (lock next task) -> mdc-test-driven-dev (新任务循环)
    -> 否: workflow 收尾（内嵌 finalize）]

lightweight:
  mdc-ar-design -> mdc-review(review_type=ar-design) -> AR设计真人确认
  -> mdc-tasks -> mdc-test-driven-dev -> mdc-test-checker -> mdc-code-review
  -> mdc-finalize
  -> [判断: 有唯一 next-ready task? 
    -> 是: using-mdc-workflow (lock next task) -> mdc-test-driven-dev (新任务循环)
    -> 否: workflow 收尾（内嵌 finalize）]
```

说明：

- `mdc-test-driven-dev` 到 `mdc-finalize` 描述的是"单个 `Current Active Task` 的实现与质量闭环"
- 完成后不默认等于"整个 workflow 已完成"；父会话必须先判断是否仍有 approved 且 dependency-ready 的剩余任务
- 若存在唯一 `next-ready task`，先回到 `using-mdc-workflow` 锁定新的 `Current Active Task`，再重新进入 `mdc-test-driven-dev`
- 只有在没有剩余任务时，`mdc-finalize` 执行内嵌的 finalize 步骤完成收尾

## 结果驱动迁移表

### full profile 迁移表

| 当前节点 | 结论 | 下一推荐节点 |
|---|---|---|
| `mdc-review`(spec) | `通过` | 规格真人确认 |
| `mdc-review`(spec) | `需修改` / `阻塞` | `mdc-specify` |
| `mdc-review`(spec) | `阻塞`（需重编排） | `using-mdc-workflow` |
| 规格真人确认 | approval step 完成 | `[判断: 是否涉及新增组件?] → 是:mdc-arch-design / 否:mdc-ar-design` |
| 规格真人确认 | 要求修改 | `mdc-specify` |
| `mdc-arch-design` | 设计完成 | `mdc-review`(arch-design) |
| `mdc-review`(arch-design) | `通过` | 架构设计真人确认 |
| `mdc-review`(arch-design) | `需修改` / `阻塞` | `mdc-arch-design` |
| `mdc-review`(arch-design) | `阻塞`（需重编排） | `using-mdc-workflow` |
| 架构设计真人确认 | approval step 完成 | `mdc-ar-design` |
| 架构设计真人确认 | 要求修改 | `mdc-arch-design` |
| `mdc-ar-design` | AR 设计完成 | `mdc-review`(ar-design) |
| `mdc-review`(ar-design) | `通过` | AR设计真人确认 |
| `mdc-review`(ar-design) | `需修改` / `阻塞` | `mdc-ar-design` |
| `mdc-review`(ar-design) | `阻塞`（需重编排） | `using-mdc-workflow` |
| AR设计真人确认 | approval step 完成 | `mdc-tasks` |
| AR设计真人确认 | 要求修改 | `mdc-ar-design` |
| `mdc-tasks` | 任务计划完成 | `mdc-review`(tasks) |
| `mdc-review`(tasks) | `通过` | 任务真人确认 |
| `mdc-review`(tasks) | `需修改` / `阻塞` | `mdc-tasks` |
| `mdc-review`(tasks) | `阻塞`（需重编排） | `using-mdc-workflow` |
| 任务真人确认 | approval step 完成 | `mdc-test-driven-dev` |
| 任务真人确认 | 要求修改 | `mdc-tasks` |
| `mdc-test-driven-dev` | 实现完成 | `mdc-test-checker` |
| `mdc-test-checker` | `通过` | `mdc-code-review` |
| `mdc-test-checker` | `需修改` / `阻塞` | `mdc-test-driven-dev` |
| `mdc-code-review` | `通过` | `mdc-finalize` |
| `mdc-code-review` | `需修改` / `阻塞` | `mdc-test-driven-dev` |
| `mdc-finalize` | 追溯链不通过 | `mdc-test-driven-dev` |
| `mdc-finalize` | 回归不通过 | `mdc-test-driven-dev` |
| `mdc-finalize` | 完成通过 + 有唯一 next-ready task | `using-mdc-workflow` |
| `mdc-finalize` | 完成通过 + 无剩余任务 | workflow 收尾（内嵌 finalize） |
| `mdc-finalize` | 完成通过 + 有剩余任务但 next-ready 不唯一 | `using-mdc-workflow` |
| `mdc-finalize` | `阻塞`（环境） | `mdc-finalize`（重试） |
| `mdc-finalize` | `阻塞`（上游） | `using-mdc-workflow` |
| `mdc-finalize` | task closeout | `using-mdc-workflow` |
| `mdc-finalize` | workflow closeout | workflow 结束（不写回 router） |
| `mdc-finalize` | `blocked` | `using-mdc-workflow` |

### standard profile 迁移表

| 当前节点 | 结论 | 下一推荐节点 |
|---|---|---|
| `mdc-ar-design` | AR 设计完成 | `mdc-review`(ar-design) |
| `mdc-review`(ar-design) | `通过` | AR设计真人确认 |
| `mdc-review`(ar-design) | `需修改` / `阻塞` | `mdc-ar-design` |
| AR设计真人确认 | approval step 完成 | `mdc-tasks` |
| AR设计真人确认 | 要求修改 | `mdc-ar-design` |
| `mdc-tasks` | 任务计划完成 | `mdc-review`(tasks) |
| `mdc-review`(tasks) | `通过` | 任务真人确认 |
| `mdc-review`(tasks) | `需修改` / `阻塞` | `mdc-tasks` |
| 任务真人确认 | approval step 完成 | `mdc-test-driven-dev` |
| `mdc-test-driven-dev` | 实现完成 | `mdc-test-checker` |
| `mdc-test-checker` | `通过` | `mdc-code-review` |
| `mdc-code-review` | `通过` | `mdc-finalize` |
| `mdc-finalize` | 完成 | 同 full profile finalize 行为 |

### lightweight profile 迁移表

| 当前节点 | 结论 | 下一推荐节点 |
|---|---|---|
| `mdc-ar-design` | AR 设计完成 | `mdc-review`(ar-design) |
| `mdc-review`(ar-design) | `通过` | AR设计真人确认 |
| `mdc-review`(ar-design) | `需修改` / `阻塞` | `mdc-ar-design` |
| AR设计真人确认 | approval step 完成 | `mdc-tasks` |
| AR设计真人确认 | 要求修改 | `mdc-ar-design` |
| `mdc-tasks` | 任务计划完成 | `mdc-test-driven-dev` |
| `mdc-test-driven-dev` | 实现完成 | `mdc-test-checker` |
| `mdc-test-checker` | `通过` | `mdc-code-review` |
| `mdc-code-review` | `通过` | `mdc-finalize` |
| `mdc-finalize` | 完成 | 同 full profile finalize 行为 |

如果某个下游 skill 给出的结论无法映射到当前 profile 迁移表中的唯一下一推荐节点，则说明编排信息还不完整，应回到 `using-mdc-workflow` 重新判断，而不是自行补脑推进。

上表主要描述"内容回修型"默认迁移。若 reviewer 返回摘要显式要求 `reroute_via_router=true`，或把 `next_action_or_recommended_skill` 指向 `using-mdc-workflow`，该显式重编排信号优先于表内默认下一步。

## 恢复编排协议

当某个节点完成后，按以下顺序恢复状态机：

1. 读取该节点的最新结论
2. 确认当前 workflow profile（从 `task-progress.md` 读取）
3. 若 `task-progress.md` 或等价工件已经写入合法或可归一化的 `Next Action Or Recommended Skill`，且它来自上一个已完成节点并与最新证据不冲突，优先采用这个显式下一步
4. 否则检查该结论对应的上游 / 下游迁移是否在当前 profile 迁移表中有明确规则
5. 若当前结论是完成检查通过，优先检查已批准任务计划或 `Task Board Path` 指向的等价工件：
   - 若存在唯一 `next-ready task`，先把 `Current Active Task` 切换到该任务，并把显式下一步锁定为 `mdc-test-driven-dev`
   - 若不存在剩余 ready / pending task，才把下一步视为 `mdc-finalize`（内嵌 finalize 收尾）
   - 若剩余任务候选不唯一、依赖状态冲突或 ready 判定不稳定，回到 `using-mdc-workflow` 作为 hard stop
6. 根据当前会话上下文判断用户是否已经提出了新范围、新问题或新阻塞（基于已有信息判断，不主动询问用户）
7. 若没有新的支线信号，则按当前 profile 迁移表进入唯一下一推荐节点

### 最小示例：T1 完成后切到 T2

前提工件：

```markdown
# task-progress.md

- Current Stage: mdc-code-review
- Workflow Profile: standard
- Execution Mode: auto
- Current Active Task: T1
- Next Action Or Recommended Skill: mdc-code-review
- Task Board Path: `docs/tasks/2026-04-09-parser-task-board.md`
```

```markdown
# docs/tasks/2026-04-09-parser-task-board.md

## Task Queue

| Task ID | Status | Depends On | Ready When | Selection Priority |
|---|---|---|---|---|
| T1 | in_progress | - | tasks approval 已完成 | P1 |
| T2 | pending | T1 | T1=`done` | P2 |
```

当 T1 的 `mdc-code-review` 返回 `PASS` 后，父会话 / workflow 恢复顺序应为：

1. 读取 code review 结论，确认当前 task 完成为 `T1`
2. 读取 task board，先把 T1 投影为 `done`
3. 根据 `Depends On` + `Ready When` 判断，T2 成为唯一 `next-ready task`
4. 更新 `Current Active Task: T2`
5. 将 `Next Action Or Recommended Skill` 锁定为 `mdc-test-driven-dev`
6. 因为这不是 approval node，也不是 hard stop，所以在同一轮继续进入 `mdc-test-driven-dev`

### 最小示例：最后一个任务完成后进入 finalize

若同样的恢复编排发生在最后一个任务：

```markdown
## Task Queue

| Task ID | Status | Depends On | Ready When | Selection Priority |
|---|---|---|---|---|
| T1 | done | - | tasks approval 已完成 | P1 |
| T2 | done | T1 | T1=`done` | P2 |
```

此时 workflow 读取 queue 后发现不存在剩余 `ready` / `pending` task，才把下一步收敛为 `mdc-finalize`（内嵌 finalize 收尾），而不是再回到实现节点。

不要跳过第 2 步、第 3 步和第 4 步。

恢复编排完成后：

- 若下一推荐节点是 `interactive` 下的 approval node，等待用户确认
- 若下一推荐节点是 `auto` 下的 approval node，先写 approval record，再进入该节点解锁后的下游节点
- 若下一推荐节点不是 approval node，也不是 hard stop，立刻在同一轮中进入该节点，不等待用户确认

若该下一推荐节点是 review 节点，则"进入该节点"的含义是：按 `references/review-dispatch-protocol.md` 派发 reviewer subagent，并按 `references/reviewer-return-contract.md` 消费返回摘要，而不是在父会话内联执行 review。
