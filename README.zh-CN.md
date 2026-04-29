# HarnessFlow

[English](README.md) | [中文](README.zh-CN.md)

HarnessFlow 是一个用于构建 agent workflow skills 的工作区。当前活跃的 skill family 是 **DevFlow**：一套面向开发阶段的工作流，用来把已接受的 SR / AR / DTS / CHANGE work item 推进到规格澄清、设计、TDD 实现、独立评审、完成门禁和收尾。

DevFlow 的范围比早期 “idea-to-product” 方向更窄。它不负责产品发现、发布运维或线上事故管理。它从团队已经接受的需求或问题单开始，重点是让工程执行可追溯、可评审，并能从磁盘工件恢复。

## 当前 Skill Family

当前 pack 位于 `devflow-skills/`。

```text
devflow-skills/
  using-devflow/
  devflow-router/
  devflow-specify/
  devflow-spec-review/
  devflow-component-design/
  devflow-component-design-review/
  devflow-ar-design/
  devflow-ar-design-review/
  devflow-tdd-implementation/
  devflow-test-checker/
  devflow-code-review/
  devflow-completion-gate/
  devflow-finalize/
  devflow-problem-fix/
```

每个 skill 都按可独立使用来组织。共享约定和模板已经内化到各自的 `SKILL.md` 或本地 `references/` 目录中，不再依赖 `devflow-skills/docs/` 或 `devflow-skills/templates/`。

## 主工作流

典型实现链路：

```text
using-devflow
  -> devflow-router
  -> devflow-specify
  -> devflow-spec-review
  -> (optional) devflow-component-design
  -> (optional) devflow-component-design-review
  -> devflow-ar-design
  -> devflow-ar-design-review
  -> devflow-tdd-implementation
  -> devflow-test-checker
  -> devflow-code-review
  -> devflow-completion-gate
  -> (next-ready task ? devflow-tdd-implementation : devflow-finalize)
```

SR 需求分析链路：

```text
using-devflow
  -> devflow-router
  -> devflow-specify
  -> devflow-spec-review
  -> (optional) devflow-component-design
  -> (optional) devflow-component-design-review
  -> devflow-finalize
```

Hotfix / 问题修复链路：

```text
using-devflow
  -> devflow-router
  -> devflow-problem-fix
  -> (optional) devflow-ar-design
  -> (optional) devflow-ar-design-review
  -> devflow-tdd-implementation
  -> devflow-test-checker
  -> devflow-code-review
  -> devflow-completion-gate
  -> devflow-finalize
```

## 当前关键决策

DevFlow 最近围绕几个强约束做了简化：

- `devflow-tasks` 和 `devflow-tasks-review` 已合并进 `devflow-tdd-implementation`。
- task planning 现在是 TDD 前置的 task queue setup / preflight，不再是独立 workflow 节点。
- `tasks.md` 和 `task-board.md` 仍然是工件，但不再对应独立 skill。
- `devflow-tdd-implementation` 可以按 Current Active Task 派发 fresh implementer subagent，并用 context pack 降低 controller 上下文消耗。
- review 节点仍保持独立 reviewer subagent：spec review、component design review、AR design review、test checker、code review。
- design 节点现在必须先做 Design Options checkpoint，再写完整设计。
- 每个 skill 自带本地约定和 references，不依赖共享 docs/templates 目录。

## 各阶段方法

| 阶段 | Skill | 方法 |
|---|---|---|
| 入口 | `using-devflow` | Front controller，direct-invoke vs route-first |
| 路由 | `devflow-router` | 基于证据的 FSM 路由、profile 选择、从工件恢复 |
| 规格澄清 | `devflow-specify` | EARS、BDD acceptance、MoSCoW、INVEST、NFR QAS |
| 规格评审 | `devflow-spec-review` | Structured walkthrough、checklist review、author/reviewer 分离 |
| 组件设计 | `devflow-component-design` | SOA 边界分析、Clean Architecture 边界、接口隔离、Design Options checkpoint |
| 组件设计评审 | `devflow-component-design-review` | 独立组件设计评审、角色分离 verdict |
| AR 设计 | `devflow-ar-design` | 代码层设计、防御式 C/C++ 设计、内嵌测试设计、Design Options checkpoint |
| AR 设计评审 | `devflow-ar-design-review` | 独立 AR 设计与测试设计评审 |
| TDD 实现 | `devflow-tdd-implementation` | task queue setup、单 active task、RED/GREEN/REFACTOR、fresh evidence、implementer subagent context pack |
| 测试有效性审查 | `devflow-test-checker` | 测试有效性、覆盖、mock/stub 边界、证据新鲜度 |
| 代码检视 | `devflow-code-review` | Fagan inspection、嵌入式 C/C++ 风险、SOA 边界检查 |
| 完成门禁 | `devflow-completion-gate` | Definition of Done、evidence bundle、下一 task vs finalize 判断 |
| 收尾 | `devflow-finalize` | closeout pack、长期资产同步、handoff |
| 问题修复 | `devflow-problem-fix` | 复现、根因分析、最小安全修复边界 |

## 工件模型

DevFlow 是 artifact-first。下一步从磁盘工件恢复，而不是从聊天记忆猜。

默认过程工件位于组件仓库的 `features/<id>/`：

```text
features/<id>/
  README.md
  progress.md
  requirement.md
  ar-design-draft.md
  component-design-draft.md
  tasks.md
  task-board.md
  traceability.md
  implementation-log.md
  reviews/
  evidence/
  completion.md
  closeout.md
```

长期资产位于组件仓库的 `docs/`：

```text
docs/
  component-design.md
  ar-designs/
  interfaces.md              # optional, read-on-presence
  dependencies.md            # optional, read-on-presence
  runtime-behavior.md        # optional, read-on-presence
```

项目级 `AGENTS.md` 可以覆盖等价路径和模板。

## Subagent 上下文策略

controller 会话应该保持轻量。重代码上下文交给 subagent。

`devflow-tdd-implementation` 会为每个 Current Active Task 准备 **Implementer Context Pack**：

```text
Work Item Type / ID
Owning Component
Current Active Task
Task Goal and Acceptance
Allowed files
Out-of-scope files
Requirement rows
AR design anchors
Test Design Case IDs
Verify commands
Evidence paths
Hard stops
```

implementer subagent 只接收这个 context pack，不继承完整聊天历史，也不读取大范围仓库上下文。它返回：

- `DONE`
- `DONE_WITH_CONCERNS`
- `NEEDS_CONTEXT`
- `BLOCKED`

controller 把状态记录到 `task-board.md` / `implementation-log.md`，处理 concerns，然后派发 `devflow-test-checker`。implementer 的 self-review 不能替代 test review 或 code review。

## Design Options Checkpoint

设计 authoring skill 不允许直接藏一个单一方案。

`devflow-component-design` 和 `devflow-ar-design` 在完整起草前都必须做 `Design Options` checkpoint：

- 提出 2-3 个方案
- 展示 trade-off
- 给出推荐方案
- 记录确认状态
- 只有确实低风险时才允许 `Single obvious option`，且必须写明理由

对应 review rubric 会检查这个 checkpoint 是否存在，以及是否用 `Single obvious option` 掩盖真实决策。

## Quick Start

直接用自然语言即可，不需要公共命令封装。

```text
Use DevFlow from this repo. Start with using-devflow.
Continue this AR from the current artifacts and route me to the correct next step.
```

也可以使用这些请求：

```text
Use DevFlow to clarify this AR requirement.
Use DevFlow to review this requirement.md.
Use DevFlow to write the AR implementation design.
Use DevFlow to implement the current active task with TDD and fresh evidence.
Use DevFlow to review the tests and then the code.
Use DevFlow to decide whether this AR can be completed.
Use DevFlow to finalize the work item.
```

## 仓库说明

- `devflow-skills/` 是当前活跃 skill family。
- `docs/devflow-principles/` 是维护 DevFlow skills 的设计原则和演进依据。
- 旧的 `skills/hf-*` 和临时 dry-run 材料可能仍作为历史资产存在，但本文描述的当前工作流是 DevFlow。
- 每个 skill 的 references 刻意保持本地化，以支持独立安装和使用。

## 当前状态

DevFlow 仍在活跃演进中。当前形态聚焦嵌入式 / 组件化软件开发，尤其包含 C/C++ 代码检视关注点；但工作流控制本身是可迁移的：基于工件路由、显式设计取舍、单任务 TDD、独立评审和基于证据的完成判断。
