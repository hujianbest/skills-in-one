# DevFlow

[English](README.md) | [中文](README.zh-CN.md)

**DevFlow** 是面向 AI 编码 agent 的开发阶段 skill family。它把团队已经接受的 SR / AR / DTS / CHANGE work item 推进到规格澄清、设计、TDD 实现、独立评审、完成门禁和收尾——以 artifact-first 的方式从工件恢复，并坚持角色分离。

DevFlow 的范围比 idea-to-product 工作流更窄。它不负责产品发现、发布运维或线上事故管理，从团队接受的需求或问题单开始，重点是让工程执行可追溯、可评审，并能从磁盘工件恢复。

> **状态 — v1.0.0**：首个正式版本，目标平台为 **OpenCode**。本版本不覆盖 Claude Code、Cursor、Gemini、Copilot、Windsurf、Kiro 等其他工具集成。

---

## 生命周期

```
  CLARIFY        DESIGN          BUILD          VERIFY         GATE         CLOSE
 ┌──────┐      ┌────────┐     ┌───────┐     ┌───────────┐    ┌──────┐    ┌───────┐
 │ Spec │ ───▶ │ AR /   │ ──▶ │  TDD  │ ──▶ │   Test-   │ ─▶ │ Done │ ─▶ │ Final │
 │Review│      │Component│    │ R/G/R │     │  Check  / │    │ Gate │    │  ize  │
 └──────┘      │ Design │     └───────┘     │CodeReview │    └──────┘    └───────┘
               └────────┘                   └───────────┘
```

每一步都由**证据驱动**：下一步从磁盘工件（`features/<id>/progress.md`、`reviews/`、`evidence/`）恢复，而不是从聊天记忆猜。评审节点都派发**独立 subagent**，不允许内联。

DevFlow 支持一种**受控的 subagent-driven execution**：`devflow-router` 是唯一 reviewer subagent 派发者，`devflow-tdd-implementation` 是唯一 implementer subagent 派发者。重代码上下文可以进入 fresh implementer，但 review、gate、profile 和下一步路由仍由现有 DevFlow 工件链控制；这不是新增 workflow，也不会绕过 `devflow-test-review`、`devflow-code-review` 或 `devflow-completion-gate`。

---

## 快速开始（OpenCode）

1. 把本仓库克隆到 OpenCode 工作区可访问的位置：

   ```bash
   git clone https://github.com/hujianbest/devflow.git
   ```

2. 让 `skills/` 对 OpenCode 可见，并把本仓库的 [`AGENTS.md`](AGENTS.md) 复制到你的**组件仓库**（即 work item 实际存放的仓库）。

3. 用自然语言对话即可，DevFlow 会自动路由：

   ```text
   按 DevFlow 在本仓库澄清 AR12345，从 using-devflow 开始。
   ```

   如果 `features/<id>/` 下已经有过程工件：

   ```text
   按 DevFlow 继续 AR12345，读取工件并路由到下一步。
   ```

详细配置见 [`docs/guides/opencode-setup.md`](docs/guides/opencode-setup.md)。

---

## 技能目录（用户视角）

按"你想做什么"挑技能；DevFlow 会从入口技能自动路由。

| 你想做… | Skill | 关键原则 |
|---|---|---|
| 决定从哪里开始 | [`using-devflow`](skills/using-devflow/SKILL.md) | Front controller，direct invoke vs route-first |
| 让 agent 从工件证据决定下一步 | [`devflow-router`](skills/devflow-router/SKILL.md) | 基于证据的 FSM 路由 |
| 把 SR / AR / DTS / CHANGE 澄清成可评审的需求规格 | [`devflow-specify`](skills/devflow-specify/SKILL.md) | EARS、BDD、MoSCoW、INVEST、NFR QAS |
| 独立评审需求规格 | [`devflow-spec-review`](skills/devflow-spec-review/SKILL.md) | author/reviewer 分离、结构化 walkthrough |
| 写或修组件实现设计 | [`devflow-component-design`](skills/devflow-component-design/SKILL.md) | SOA 边界 + Design Options checkpoint |
| 独立评审组件实现设计 | [`devflow-component-design-review`](skills/devflow-component-design-review/SKILL.md) | 角色分离 verdict |
| 写 AR 实现设计（含测试设计章节） | [`devflow-ar-design`](skills/devflow-ar-design/SKILL.md) | 代码层设计 + 防御式 C/C++ + 内嵌测试设计 |
| 独立评审 AR 设计与测试设计 | [`devflow-ar-design-review`](skills/devflow-ar-design-review/SKILL.md) | 独立设计与测试设计审 |
| 用 TDD 实现（单 active task + fresh evidence） | [`devflow-tdd-implementation`](skills/devflow-tdd-implementation/SKILL.md) | task queue setup、RED/GREEN/REFACTOR、implementer subagent |
| 检查测试是否真有效 | [`devflow-test-review`](skills/devflow-test-review/SKILL.md) | TDD 后测试有效性独立审查 |
| C / C++ 代码检视 | [`devflow-code-review`](skills/devflow-code-review/SKILL.md) | Fagan 风格 + 嵌入式 C/C++ 风险 + SOA 边界 |
| 判断当前是否可以完成 | [`devflow-completion-gate`](skills/devflow-completion-gate/SKILL.md) | DoD + evidence bundle |
| 收尾 / 同步长期资产 / 交接 | [`devflow-finalize`](skills/devflow-finalize/SKILL.md) | closeout pack + 长期资产 promotion |
| 复现 / 根因 / 最小修复边界（DTS / Hotfix） | [`devflow-problem-fix`](skills/devflow-problem-fix/SKILL.md) | 复现 + 根因分析 + 最小安全修复 |

评审节点都由 `devflow-router` 派发**独立 subagent**，subagent 以对应的 `devflow-*-review`（或 `devflow-test-review` / `devflow-code-review`）skill 作为 system prompt。Reviewer subagent 只读被评审工件并返回结构化 verdict，不修改工件。

实现阶段的 subagent 只服务于当前 task：`devflow-tdd-implementation` 为唯一 `Current Active Task` 构造 Implementer Context Pack，派发 fresh implementer 完成 RED/GREEN/REFACTOR，并把结果写回 `task-board.md`、`implementation-log.md` 和 evidence 路径。

---

## Command 与 Skill 的对应关系

Command 是用户视角的阶段入口，负责把一次请求推进到合适阶段；Skill 是实际执行规则，定义每个 canonical 节点怎么做。Command 不复制、不替代 `SKILL.md`，也不绕开 `devflow-router`、独立评审和完成门禁。

| Command | 阶段 | 内部对应 skills |
|---|---|---|
| [`/devflow`](commands/devflow.md) | 入口 / 续作 | `using-devflow` → 按需 `devflow-router` |
| [`/devflow-specify`](commands/devflow-specify.md) | 规格阶段 | `devflow-specify` → `devflow-router` 派发 `devflow-spec-review` |
| [`/devflow-design`](commands/devflow-design.md) | 设计阶段 | 按需 `devflow-component-design` → `devflow-component-design-review` → `devflow-ar-design` → `devflow-ar-design-review` |
| [`/devflow-build`](commands/devflow-build.md) | 构建阶段 | `devflow-tdd-implementation` → `devflow-test-review` → `devflow-code-review` |
| [`/devflow-ship`](commands/devflow-ship.md) | 收尾阶段 | `devflow-completion-gate` → `devflow-finalize` |
| [`/devflow-fix`](commands/devflow-fix.md) | Hotfix / DTS | `devflow-router` 升级 hotfix → `devflow-problem-fix` → 回到 build / ship 链路 |

评审类 skill 必须由 `devflow-router` 派发独立 reviewer subagent；实现类 task 由 `devflow-tdd-implementation` 派发 implementer subagent。`auto` execution mode 只减少阶段间人工确认，不豁免任何评审、门禁或证据要求。

---

## Skill Family 目录

```text
commands/
  devflow.md
  devflow-specify.md
  devflow-design.md
  devflow-build.md
  devflow-ship.md
  devflow-fix.md
skills/
  using-devflow/
  devflow-router/
  devflow-specify/
  devflow-spec-review/
  devflow-component-design/
  devflow-component-design-review/
  devflow-ar-design/
  devflow-ar-design-review/
  devflow-tdd-implementation/
  devflow-test-review/
  devflow-code-review/
  devflow-completion-gate/
  devflow-finalize/
  devflow-problem-fix/
docs/
  guides/
    devflow-usage-guide.md
    opencode-setup.md
  principles/
    00 soul.md
    01 skill-node-define.md
    02 skill-anatomy.md
    03 artifact-layout.md
    04 workflow-architecture.md
    05 coding-principles.md
AGENTS.md
LICENSE
CONTRIBUTING.md
CHANGELOG.md
```

每个 skill 都按可独立使用来组织。共享约定和模板已经内化到各自的 `SKILL.md` 或本地 `references/` 目录中，不依赖 `skills/docs/` 或 `skills/templates/`。

---

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
  -> devflow-test-review
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
  -> devflow-test-review
  -> devflow-code-review
  -> devflow-completion-gate
  -> devflow-finalize
```

---

## 当前关键决策

DevFlow 围绕几个强约束做了简化：

- `devflow-tasks` 和 `devflow-tasks-review` 已合并进 `devflow-tdd-implementation`。task planning 现在是 TDD 前置 preflight，`tasks.md` 与 `task-board.md` 仍然是工件，但不再对应独立 skill。
- `devflow-tdd-implementation` 可以按 Current Active Task 派发 fresh implementer subagent，并用 context pack 降低 controller 上下文消耗。
- review 节点保持独立 reviewer subagent：spec review、component design review、AR design review、test review、code review。
- design 节点必须先做 Design Options checkpoint，再写完整设计。
- 每个 skill 自带本地约定和 references，不依赖共享 docs/templates 目录。

---

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
| 测试有效性审查 | `devflow-test-review` | 测试有效性、覆盖、mock/stub 边界、证据新鲜度 |
| 代码检视 | `devflow-code-review` | Fagan inspection、嵌入式 C/C++ 风险、SOA 边界检查 |
| 完成门禁 | `devflow-completion-gate` | Definition of Done、evidence bundle、下一 task vs finalize 判断 |
| 收尾 | `devflow-finalize` | closeout pack、长期资产同步、handoff |
| 问题修复 | `devflow-problem-fix` | 复现、根因分析、最小安全修复边界 |

---

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
  ar-specs/                  # AR 规格（由 finalize 从 features/<id>/requirement.md 升级）
  ar-designs/                # AR 实现设计（由 finalize 从 features/<id>/ar-design-draft.md 升级）
  interfaces.md              # optional, read-on-presence
  dependencies.md            # optional, read-on-presence
  runtime-behavior.md        # optional, read-on-presence
```

项目级 `AGENTS.md` 可以覆盖等价路径和模板。

---

## Subagent 上下文策略

controller 会话应该保持轻量。重代码上下文交给 subagent，但 subagent 编排保持受限双轨制：reviewer 只由 `devflow-router` 派发，implementer 只由 `devflow-tdd-implementation` 派发。

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

controller 把状态记录到 `task-board.md` / `implementation-log.md`，处理 concerns，然后派发 `devflow-test-review`。implementer 的 self-review 不能替代 test review 或 code review；`NEEDS_CONTEXT` 留在 `devflow-tdd-implementation` 内重打包，只有 routing、profile 或 scope blocker 才回到 `devflow-router`。

---

## Design Options Checkpoint

设计 authoring skill 不允许直接藏一个单一方案。

`devflow-component-design` 和 `devflow-ar-design` 在完整起草前都必须做 `Design Options` checkpoint：

- 提出 2-3 个方案
- 展示 trade-off
- 给出推荐方案
- 记录确认状态
- 只有确实低风险时才允许 `Single obvious option`，且必须写明理由

对应 review rubric 会检查这个 checkpoint 是否存在，以及是否用 `Single obvious option` 掩盖真实决策。

---

## 仓库说明

- `skills/` 是当前活跃 DevFlow skill family。高风险 skill（`devflow-router`、`devflow-tdd-implementation`、`devflow-test-review`、`devflow-completion-gate`）带 `evals/` 目录，枚举它们必须拒绝的误用场景。
- `docs/principles/` 是维护 DevFlow skills 的设计原则与演进依据（运行时不被 skill 消费）。
- `docs/guides/` 是面向使用者的使用与配置指南；`docs/guides/README.zh-CN.md` 是中文版深度使用指南（含案例骨架与截图占位），`docs/guides/opencode-setup.md` 是 OpenCode 接入说明，`docs/guides/devflow-usage-guide.md` 是日常使用场景与 FAQ。
- 每个 skill 的 references 刻意保持本地化，以支持独立安装和使用。

---

## License

[MIT](LICENSE)。

## 贡献

见 [CONTRIBUTING.md](CONTRIBUTING.md)。Skill 应满足：**具体**（可执行步骤）、**可验证**（证据要求）、**artifact-first**（从磁盘恢复）、**角色分离**（不允许 self-verification）。
