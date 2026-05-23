# DevFlow

[English](README.md) | [中文](README.zh-CN.md)

**面向 AI 编码 agent 的 artifact-first SDD、门禁式 TDD 与角色分离评审工作流。**

DevFlow 是一个开发阶段工作流，用来把团队已经接受的 SR / AR / DTS / CHANGE work item 推进到规格澄清、设计、TDD 实现、独立评审、完成门禁和收尾。下一步永远从持久化工件恢复，而不是从聊天记忆猜。

DevFlow 的范围故意比 idea-to-product 工作流更窄。它不负责产品发现、发布运维、系统 / 集成 / 验收测试，也不负责线上事故管理。它从团队已经接受的需求或问题单开始。

> **状态 - v1.0.0**：首个正式版本，目标平台为 **OpenCode**。Claude Code、Cursor、Gemini、Copilot、Windsurf、Kiro 等多工具集成不在本版本范围内。

---

## Command Intents

OpenCode v1 通过自然语言和自动 skill discovery 使用 DevFlow。`commands/` 目录记录 slash-style 阶段意图，团队可以把它们接入自己的客户端；但每个 command 都只是 bias，不是 bypass：`using-devflow` 和 `devflow-router` 仍然要先检查仓库工件，再选择下一个 canonical 节点。

| 你要做什么 | Command intent | 关键原则 |
|---|---|---|
| 进入或续作 DevFlow | [`/devflow`](commands/devflow.md) | 从工件路由 |
| 定义要做什么 | [`/devflow-specify`](commands/devflow-specify.md) | 先规格，后设计或代码 |
| 规划怎么做 | [`/devflow-design`](commands/devflow-design.md) | 先设计选项，再确定方案 |
| 构建一个 active task | [`/devflow-build`](commands/devflow-build.md) | RED -> GREEN -> REFACTOR，并记录新鲜证据 |
| 收尾工程工作 | [`/devflow-ship`](commands/devflow-ship.md) | 先评审和门禁，再 closeout |
| 修复 DTS / hotfix | [`/devflow-fix`](commands/devflow-fix.md) | 先复现和根因，再做最小安全修复 |

评审不是用户直接调用的捷径。`devflow-router` 负责派发独立 reviewer subagent，覆盖 spec、component-design、AR-design、test 和 code review。

---

## 快速开始

### OpenCode

DevFlow v1.0 仅面向 OpenCode。你可以把 skill pack 放在组件仓库旁边，也可以把它 vendor 到实际存放 work item 的组件仓库中。

#### 方案 A - 作为旁路 Skill Pack

```bash
git clone https://github.com/hujianbest/devflow.git ~/devflow
cd /path/to/your-component-repo
ln -s ~/devflow/skills .opencode-skills
cp ~/devflow/AGENTS.md ./AGENTS.md
```

然后编辑复制过去的 `AGENTS.md` 中的 `## Project overrides`，写入你的组件路径、模板和编码规范。

#### 方案 B - Vendor 进组件仓库

```bash
cd /path/to/your-component-repo
git subtree add --prefix .devflow https://github.com/hujianbest/devflow.git v1.0.0 --squash
cp .devflow/AGENTS.md ./AGENTS.md
```

然后让 OpenCode 指向 `.devflow/skills/`。

更多配置细节见 [`docs/guides/opencode-setup.md`](docs/guides/opencode-setup.md)。

### 试一下

```text
Use DevFlow from this repo. Start with using-devflow.
I want to clarify AR12345 for the notifications component.
Do not jump straight to code.
```

如果已经存在过程工件：

```text
Continue AR12345 with DevFlow. Read features/AR12345-*/progress.md and route me to the next step.
```

---

## See It Work

```text
You:       Use DevFlow to clarify AR12345.

DevFlow:   通过 using-devflow 进入，编写或修订 requirement
           工件，然后路由到独立 spec review。

You:       Use DevFlow to design the approved AR.

DevFlow:   检查是否需要 component-impact 设计，记录 design
           options，编写带内嵌测试设计的 AR implementation
           design，并把相关设计送入独立评审。

You:       Use DevFlow to build the current active task.

DevFlow:   锁定唯一 Current Active Task，准备 Implementer Context
           Pack，执行 RED -> GREEN -> REFACTOR，并把证据记录到
           task-board、implementation-log 和 evidence 路径。

You:       Use DevFlow to verify and close this work.

DevFlow:   派发 test review、code review、completion gate 和
           finalize。长期 AR 资产只会在 closeout 阶段 promotion。
```

对 DTS 或 hotfix，DevFlow 会先在 `devflow-problem-fix` 中复现问题并记录根因，再按需要回到同一条 design / build / review / gate 链路。

---

## Skill Catalog

DevFlow 包含一个 public entry skill，以及 13 个 canonical `devflow-*` runtime nodes。

### Meta 与路由

| Skill | 做什么 | 什么时候用 |
|---|---|---|
| [`using-devflow`](skills/using-devflow/SKILL.md) | public entry，判断 direct-invoke vs route-first | 新会话或高层 DevFlow 意图 |
| [`devflow-router`](skills/devflow-router/SKILL.md) | 基于证据的 runtime router 与恢复控制器 | 从工件续作，或消费 review / gate 结论 |

### Define

| Skill | 做什么 | 什么时候用 |
|---|---|---|
| [`devflow-specify`](skills/devflow-specify/SKILL.md) | 把 SR / AR / DTS / CHANGE 意图转成可测试需求 | 编写或修订可评审规格 |
| [`devflow-spec-review`](skills/devflow-spec-review/SKILL.md) | 从清晰度、完整性、可测试性评审规格 | spec 工件准备好独立评审 |

### Plan

| Skill | 做什么 | 什么时候用 |
|---|---|---|
| [`devflow-component-design`](skills/devflow-component-design/SKILL.md) | 编写或修订组件实现设计 | work item 有 component-impact，或 SR analysis 需要组件设计 |
| [`devflow-component-design-review`](skills/devflow-component-design-review/SKILL.md) | 角色分离地评审组件设计 | 组件设计需要独立 verdict |
| [`devflow-ar-design`](skills/devflow-ar-design/SKILL.md) | 产出带内嵌测试设计的 AR 实现设计 | 已批准需求进入 TDD 前需要代码层设计 |
| [`devflow-ar-design-review`](skills/devflow-ar-design-review/SKILL.md) | 评审 AR 设计与测试设计 | AR 设计准备好独立评审 |

### Build、Verify 与 Close

| Skill | 做什么 | 什么时候用 |
|---|---|---|
| [`devflow-tdd-implementation`](skills/devflow-tdd-implementation/SKILL.md) | 通过 task preflight、RED/GREEN/REFACTOR 和证据实现一个 active task | 已评审设计准备进入 TDD 实现 |
| [`devflow-test-review`](skills/devflow-test-review/SKILL.md) | 评审测试有效性和 fail-first 证据 | TDD 证据准备好独立测试评审 |
| [`devflow-code-review`](skills/devflow-code-review/SKILL.md) | 评审实现质量与 C / C++ 风险 | 代码准备好独立评审 |
| [`devflow-completion-gate`](skills/devflow-completion-gate/SKILL.md) | 判断证据是否足以完成或继续 | review 已存在，需要 completion 判断 |
| [`devflow-finalize`](skills/devflow-finalize/SKILL.md) | 写 closeout，并 promotion 长期资产 | completion gate 允许收尾 |
| [`devflow-problem-fix`](skills/devflow-problem-fix/SKILL.md) | 复现、根因分析并界定 DTS / hotfix 范围 | 已发布行为缺陷或紧急问题需要受控恢复 |

---

## DevFlow 方法

DevFlow 不是 prompt 集合，而是面向 agent 的受控工程工作流。

| 层次 | DevFlow 方法 | 为什么重要 |
|---|---|---|
| 意图 | 规格锚定的 SDD | 把范围、约束和验收标准留在可评审文件中 |
| 规划 | 设计选项和评审门禁 | 在代码前显式记录架构、接口、风险和测试设计 |
| 执行 | 门禁式 TDD | 要求 fail-first 证据、GREEN 验证，并且一次只有一个 active task |
| 路由 | 基于工件恢复 | 让另一个 agent 可从 `progress.md`、reviews、evidence 和 completion records 续作 |
| 评审 | 角色分离 subagent | 防止作者和批准者塌缩到同一个会话 |
| 验证 | Test review、code review、completion gate | 区分“测试跑过了”和“证据足够完成” |
| 收尾 | 长期资产 promotion | 只在 gate 允许时把已接受的规格与设计同步到 `docs/` |

---

## Skills 如何工作

每个 skill 都是一份自包含的操作规程：

```text
SKILL.md
├── Frontmatter classifier
├── Overview and trigger conditions
├── Hard gates and object contract
├── Step-by-step workflow
├── Required artifacts and evidence
├── Review or gate contract
├── Red flags and common rationalizations
├── Verification checklist
└── Local DevFlow conventions
```

关键设计选择：

- **证据优先于记忆。** 路由读取 `features/<id>/progress.md`、reviews、approvals、evidence 和 completion records。
- **只允许 canonical name。** `Next Action Or Recommended Skill` 必须是 canonical `devflow-*` 节点；`using-devflow` 只是 public entry，不能写入 runtime handoff 字段。
- **受控 subagent。** `devflow-router` 是唯一 reviewer 派发者；`devflow-tdd-implementation` 是唯一 implementer 派发者。
- **禁止 self-verification。** Authoring skill 只写工件并交接；独立 reviewer 返回 verdict，不修改生产工件。
- **本地 references。** 每个 skill 自己拥有 `references/`，必要时拥有 `evals/`；不存在共享 `skills/docs/` 依赖。

---

## 工件模型

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
  ar-specs/                  # 由 features/<id>/requirement.md promotion 的 AR 规格
  ar-designs/                # 由 features/<id>/ar-design-draft.md promotion 的 AR 实现设计
  interfaces.md              # optional, read-on-presence
  dependencies.md            # optional, read-on-presence
  runtime-behavior.md        # optional, read-on-presence
```

项目级 `AGENTS.md` 可以覆盖等价路径和模板。已关闭 work item 继续保留在 `features/<id>/` 下，避免破坏 traceability links。

---

## 项目结构

```text
devflow/
├── AGENTS.md                         # OpenCode hard contract
├── commands/                         # slash-style command intent definitions
├── agents/                           # reviewer / implementer role mirrors
├── skills/                           # entry skill + 13 canonical devflow-* nodes
│   ├── using-devflow/
│   ├── devflow-router/
│   ├── devflow-specify/
│   ├── devflow-spec-review/
│   ├── devflow-component-design/
│   ├── devflow-component-design-review/
│   ├── devflow-ar-design/
│   ├── devflow-ar-design-review/
│   ├── devflow-tdd-implementation/
│   ├── devflow-test-review/
│   ├── devflow-code-review/
│   ├── devflow-completion-gate/
│   ├── devflow-finalize/
│   └── devflow-problem-fix/
├── docs/
│   ├── guides/
│   │   └── opencode-setup.md
│   └── principles/
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

`devflow-router`、`devflow-tdd-implementation`、`devflow-test-review`、`devflow-completion-gate` 等高风险 skill 带有 `evals/` 目录，枚举它们必须拒绝的误用场景。

---

## 为什么是 DevFlow？

AI 编码 agent 很容易从请求直接跳到实现。DevFlow 给它们一条更窄、更硬的路径：澄清已接受 work item，先设计再切分工作，用 TDD 证明行为，把 reviewer 和 author 分离，并用持久证据闭环。

DevFlow 也清楚划定 shipping 边界。它可以完成工程 closeout 并产出可追溯 handoff 工件，但部署、灰度、监控、回滚和上线后运营仍属于项目自己的生产系统。

---

## 贡献

见 [CONTRIBUTING.md](CONTRIBUTING.md)。请保持 skill 具体、可验证、artifact-first、可独立安装，并坚持角色分离。

## License

[MIT](LICENSE) - 可在你的项目、团队和工具中使用。
