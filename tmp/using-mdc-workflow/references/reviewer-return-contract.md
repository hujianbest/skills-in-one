# Reviewer Return Contract

## 目的

这份协议定义 reviewer subagent 评审完成后，回传给父会话的最小结构化摘要。

## 最小返回格式

```json
{
  "conclusion": "PASS|REVISE|BLOCKED",
  "next_action_or_recommended_skill": "推荐下一步 canonical 节点",
  "record_path": "实际写入的 review 记录路径",
  "key_findings": [
    "关键发现 1",
    "关键发现 2"
  ],
  "needs_human_confirmation": false,
  "reroute_via_router": false
}
```

兼容说明：

- `needs_human_confirmation` 这个字段名为兼容现有 live contract 保留
- 它的运行时语义已扩大为"当前 review 通过后，还需要父会话完成 approval step"
- 父会话最终是等待真人确认，还是在 `Execution Mode=auto` 下自动落盘批准，由运行时编排决定

## 字段说明

| 字段 | 说明 |
| --- | --- |
| `conclusion` | 当前 review 的正式结论 |
| `next_action_or_recommended_skill` | reviewer 基于当前结果建议的下一步 canonical handoff |
| `record_path` | 已写入的 review 记录路径 |
| `key_findings` | 父会话需要向用户展示或用于回修的关键发现 |
| `needs_human_confirmation` | 是否必须由父会话继续完成 approval step（字段名保留兼容） |
| `reroute_via_router` | 若为 `true`，父会话应先回到 `using-mdc-workflow` 重编排 |

## 使用规则

### `conclusion`

只能使用：

- `PASS`
- `REVISE`
- `阻塞`（兼容旧写法）
- `BLOCKED`

### `next_action_or_recommended_skill`

优先返回 canonical `mdc-*` skill ID，或保留节点：

- `mdc-specify`
- `mdc-review`
- `mdc-arch-design`
- `mdc-ar-design`
- `mdc-tasks`
- `mdc-test-driven-dev`
- `mdc-test-checker`
- `mdc-code-review`
- `mdc-finalize`
- `规格真人确认`
- `架构设计真人确认`
- `AR设计真人确认`
- `任务真人确认`
- `using-mdc-workflow`

这个字段是 reviewer 摘要层对仓库 canonical 字段 `Next Action Or Recommended Skill` 的结构化映射。

它必须是一个唯一的 canonical 值，不得把多个候选动作拼成一个字符串。

命名规则：

- live reviewer skills 与相关文档统一使用 `next_action_or_recommended_skill`
- reviewer 摘要必须直接返回该字段，不再使用旧字段别名

### `needs_human_confirmation`

只在 `conclusion=PASS` 且当前 review 节点要求 approval step 时，才把这个字段设为 `true`。

若 `conclusion=REVISE` 或 `BLOCKED`，默认返回 `false`，并由 `next_action_or_recommended_skill` 指向回修或重编排节点。

`conclusion=PASS` 时，通常按以下约定：

| review skill | `conclusion=PASS` 时默认值 |
| --- | --- |
| `mdc-review`(spec) | `true` |
| `mdc-review`(arch-design) | `true` |
| `mdc-review`(ar-design) | `true` |
| `mdc-review`(tasks) | `true` |
| `mdc-code-review` | `false` |
| `mdc-test-checker` | `false` |

### `reroute_via_router`

以下情况建议返回 `true`：

- 当前 review 暴露出缺少上游已批准工件
- 当前输入证据与 profile / stage 明显冲突
- 当前问题本质上需要回到 `using-mdc-workflow` 重新决定分支

## 父会话消费规则

父会话收到该摘要后，先检查暂停点与"先向用户展示"的义务，再按以下顺序处理：

1. 若 `reroute_via_router=true`，先经 `using-mdc-workflow` 重编排。
2. 否则若 `conclusion=PASS` 且 `needs_human_confirmation=true`：
   - `Execution Mode=interactive`：进入真人确认 / approval step
   - `Execution Mode=auto`：先写 approval record，再继续进入该 approval step 解锁后的下游节点
3. 否则若 `conclusion=PASS` 且无需额外 approval step，进入 `next_action_or_recommended_skill`。
4. 否则若 `conclusion=REVISE` 或 `BLOCKED`，按 `next_action_or_recommended_skill` 回修或补条件。

补充理解：

- 对 `mdc-review`(spec/design/tasks)，`interactive` 模式下的 `REVISE` 与内容回修型 `BLOCKED` 仍受暂停点约束，父会话需先向用户展示评审结论与修订重点
- 对 `mdc-review`(spec/design/tasks)，`auto` 模式下若修订方向清楚、仍在当前范围内，可直接回到上游 skill 回修；若方向不清，仍应停止自动推进
- 对 `mdc-review`(spec/design/tasks)，若 `BLOCKED` 且需要经 router 重编排，父会话需先向用户展示阻塞原因，再回到 `using-mdc-workflow`
- 对其他 review / gate，若修订方向不明确，也应先与用户讨论，而不是机械自动推进

## 边界

这个 return contract 只定义"reviewer 回给父会话的摘要"，不替代 review 记录正文。

review 正文仍应按各 review skill 自身要求写入仓库路径。
