# DevFlow Agents

DevFlow 的两个独立子代理 persona。每个 persona 是一个 system-prompt 级 Markdown 文件，由其唯一合法派发者按 `AGENTS.md` 的派发契约启动。

| Persona | 派发者 | 角色定位 | 包装的 canonical skills |
|---|---|---|---|
| [devflow-reviewer](devflow-reviewer.md) | 仅 `devflow-router` | 独立评审子代理（5 个评审节点共用，按 `target_skill` 参数化） | `devflow-spec-review`、`devflow-component-design-review`、`devflow-ar-design-review`、`devflow-test-review`、`devflow-code-review` |
| [devflow-implementer](devflow-implementer.md) | 仅 `devflow-tdd-implementation` | TDD 实现子代理（每次 next-ready task 一次新派发） | 在 `devflow-tdd-implementation` 内部执行 RED-GREEN-REFACTOR |

## Persona / Skill / Command 三者关系

| 层 | 它是什么 | 例 | 编排角色 |
|---|---|---|---|
| Skill | 工作流（步骤 + 退出准则） | `devflow-ar-design`、`devflow-spec-review` | *How*：在 command 或 persona 内部被严格遵循 |
| Persona | 角色视角 + 输出契约的子代理 | `devflow-reviewer`、`devflow-implementer` | *Who*：被 router 或 tdd-implementation 派发 |
| Command | 用户视角的工作流阶段入口 | `/devflow-specify`、`/devflow-build` | *When*：组合多个 skill 推进一个阶段 |

**Personas 不调用其它 personas**。这是 AGENTS.md §3 / §6 的硬约束，也是 OpenCode / Claude Code 平台对子代理的硬约束（"subagents cannot spawn other subagents"）。任何跨视角发现都写进 findings，由派发者（router 或 tdd-implementation）决定下一步。

## 派发模式

### 评审子代理（`devflow-reviewer`）

`devflow-router` 构造 Review Request Pack 后派发独立子代理：

```text
target_skill        ∈ {devflow-spec-review | devflow-component-design-review |
                       devflow-ar-design-review | devflow-test-review | devflow-code-review}
work_item_id        e.g. AR12345
owning_component    e.g. memory-pool        # 或 owning_subsystem（SR 工作项）
primary_artifact    features/<id>/requirement.md | ar-design-draft.md | ...
supporting_context  progress.md 摘要 + 相邻 docs/
agents_md_anchor    项目 AGENTS.md 覆盖锚点
expected_return_contract  verdict + findings + record_path +
                          next_action_or_recommended_skill + reroute_via_router
```

子代理在新会话内载入 `agents/devflow-reviewer.md` 作为 system prompt，根据 `target_skill` 加载并执行 `skills/<target_skill>/SKILL.md` 的 `工作流` 章节，返回结构化 verdict 后会话结束。

### 实现子代理（`devflow-implementer`）

`devflow-tdd-implementation` 构造 Implementer Context Pack 后派发独立子代理：

```text
work_item_id, owning_component
current_task        id + acceptance criteria + 对应 AR 设计章节锚点 + 测试设计章节锚点
coding_standards    适用编码规范 / 静态分析配置 / MISRA-CERT 子集（若启用）
evidence_paths      evidence 输出位置（features/<id>/evidence/...）
test_and_build_cmds 测试与构建命令
expected_return_contract  result ∈ {DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED}
                          + task_id + files_touched + tests_added + evidence_paths
                          + concerns + reroute_via_router
```

`NEEDS_CONTEXT` 不外溢到父会话；由 `devflow-tdd-implementation` 内部重新打包再试。只有 `BLOCKED + reroute_via_router=true` 才回到 `devflow-router`。

## 决策矩阵

```
要审查某个 devflow 工件？
└── 是 → 由 devflow-router 派发 devflow-reviewer（按 target_skill 路由）

要按一个 task 推进 TDD？
└── 是 → 由 devflow-tdd-implementation 派发 devflow-implementer

要在不同 persona 之间转发或合并视角？
└── 禁止。回到 devflow-router 由其消费 verdict 并决定下一步。
```

## Personas 的硬约束

1. 单一角色 + 单一输出契约。出现第二角色 → 应该是第二个 persona，不是第二段 system prompt。
2. 评审 persona **不修改** 任何生产代码 / 测试 / 设计制品。
3. 实现 persona **不修改** task 计划 / AR 设计 / task-board 顺序；越界 → `BLOCKED + reroute_via_router=true`。
4. 任一 persona 都 **不调用** 另一 persona；跨视角发现写进 findings / concerns。
5. 每个 persona 文件末尾必须有 `Composition` 块说明唯一合法派发者。
