---
name: devflow-component-design
description: 当需要创建或修订组件实现设计时使用；触发场景包括 requirement-analysis 档位下的 SR 被 devflow-spec-review 判定需要修订组件设计，或 component-impact 档位下的 AR 范围触及 SOA 接口、依赖、状态机、运行机制。也用于 devflow-component-design-review 返回需修改或阻塞后的修订。不用于 AR 代码层设计、通用规格澄清，或普通组件内变更。
---

# devflow 组件实现设计（覆盖 SR-分析 与 AR-实现 两条子街区）

为唯一所属组件产出或修订**组件实现设计**，描述该组件的职责、SOA 接口、依赖、数据 / 状态、运行机制和对 AR 实现设计的约束。

本 skill 同时服务两个子街区：

1. **需求分析子街区（SR triggered）**：SR 在 `devflow-spec-review` 中被判定「需修订组件设计」时进入；通过 review 后由 `devflow-finalize` 写 **analysis closeout** 并 promote 到 `docs/component-design.md`；**不**进入 `devflow-ar-design`。
2. **实现子街区（AR component-impact triggered）**：AR work item profile 升级为 component-impact 时进入；通过 review 后下一步是 `devflow-ar-design`。

本 skill 不写单个 AR 的代码层设计（那是 `devflow-ar-design` 的职责），不写代码，不修改其他组件。它的输出是组件长期资产，受团队组件设计模板约束。

## 适用场景

适用：

- **SR triggered**：profile = `requirement-analysis`，SR `devflow-spec-review` 通过且 verdict 表明 SR 需修订组件设计
- **AR triggered**：`devflow-router` 已升级到 `component-impact` profile 且组件设计需要新增 / 修订（新增组件、修改 SOA 接口、修改组件职责或依赖方向、修改状态机或运行时机制）
- 现有 `docs/component-design.md` 缺失、过期或与代码明显不一致
- `devflow-component-design-review` 返回 `需修改` / `阻塞` 需修订

不适用 → 改用：

- 仅修改本组件内部实现而不影响接口 / 依赖 / 状态机 → `devflow-ar-design`
- 需求不清 → `devflow-specify`
- 直接进入 AR 代码层设计 → `devflow-ar-design`
- 阶段不清 / 证据冲突 → `devflow-router`

## 硬性门禁

- 组件实现设计必须遵循团队模板（`references/devflow-component-design-template.md`；模板留空时由模块架构师手动补齐章节后再交评审）
- 不替模块架构师拍板组件边界 / SOA 接口 / 跨组件依赖；模块架构师必须 sign-off
- 起草完整组件设计前必须提出 2-3 个组件级方案并记录 trade-off / 推荐方案；低风险单一路径可写 `Single obvious option`，但必须说明为什么不展开多方案
- `interactive` 模式下，推荐方案需由模块架构师确认后再写完整组件设计；`auto` 模式下，若方案选择需要架构拍板或跨组件协调则停下回 `devflow-router`
- 组件实现设计 review 通过前，AR 实现设计**不得**消费本设计的草稿版本
- 组件实现设计中**不得**写单个 AR 的代码层设计
- 不修改其他组件
- AR triggered 时未经 router 升级到 component-impact profile，不得直接进入本节点
- SR triggered 时本节点完成后下一步是 `devflow-component-design-review` → `devflow-finalize`（analysis closeout），**不得**指向 `devflow-ar-design`
- 正式输出不得残留 `AI提示`、示例业务内容、变量替换说明、`TBD` / `{DATE}` 等模板占位符

## 对象契约

- Primary Object: component implementation design model（组件实现设计模型）
- Frontend Input Object: `features/<id>/requirement.md`（已通过 spec-review）、`features/<id>/traceability.md`、当前 `docs/component-design.md`（如存在）、相关 SR / AR 上游锚点、组件代码现状摘要
- Backend Output Object: `features/<id>/component-design-draft.md`（过程版） + 同步到 `docs/component-design.md`（review 通过且模块架构师 sign-off 后）
- Object Transformation: 把组件职责 / 接口 / 依赖 / 数据 / 运行机制写成长期可消费的设计
- Object Boundaries: 不写 AR 代码层设计；不修改其他组件；不写代码
- Object Invariants: 组件名、所属子系统、模块架构师 owner 在 review 通过前保持稳定

## 方法原则

- **SOA Component Boundary Analysis**: 显式说明组件职责 / 接口 / 依赖 / 跨组件影响
- **Clean Architecture Boundary Discipline**: 保持依赖方向稳定；不让实现细节倒灌到上层
- **Interface Segregation**: 组件对外接口尽量内聚、最小知识
- **Design Options Before Draft**: 正式起草前先列 2-3 个组件级方案、trade-off、推荐项与模块架构师确认状态
- **C / C++ Defensive Design**: 组件级内存模型、并发模型、错误处理 / 资源生命周期约束
- **Template-Constrained Design**: 设计文档结构由团队模板决定（`references/devflow-component-design-template.md`，留空待团队补齐）
- **Embedded Risk Awareness**: 实时性 / 中断上下文 / ABI 兼容 / 编译条件作为一等约束

## 工作流

### 1. 对齐输入与角色

按 Read-On-Presence 读取 `features/<id>/requirement.md`（SR 含 Affected Components / Component Design Impact 章节；AR 含 Component Impact Assessment 章节）、`features/<id>/reviews/spec-review.md`（verdict 应 `通过`）、当前 `docs/component-design.md`（若存在）、组件代码现状的最少必要摘要；项目若启用了可选子资产 `docs/interfaces.md` / `docs/dependencies.md` / `docs/runtime-behavior.md` 也一并读取，未启用直接跳过、不阻塞。spec-review 未通过 → 阻塞，回 `devflow-router`；模块架构师 owner 未指定 → 阻塞，回需求负责人。

确认本次进入子街区：

- profile = `requirement-analysis` → SR triggered，本节点完成后下一步是 `devflow-component-design-review` → `devflow-finalize`（analysis closeout）
- profile = `component-impact` → AR triggered，本节点完成后下一步是 `devflow-component-design-review` → `devflow-ar-design`

### 2. 判定本次是新增 / 修订 / 单纯消费

对照 requirement.md 的 Component Impact Assessment 与当前 docs 状态，三选一：

- `new`：新增组件 / 新增章节
- `revise`：修订现有 `docs/component-design.md` 的某些章节
- `consume-only`：本次只消费现有组件设计 → 标 `reroute_via_router=true`，下一步 `devflow-router`（router 应把 profile 退回 standard，不应进入本节点）

### 3. 方案选择 checkpoint

在写完整 `component-design-draft.md` 前，先产出 `Design Options` 小节，列 2-3 个组件级方案；每个方案至少包含：

- 组件职责 / 非职责变化
- SOA 接口 / Topic / API / 软件单元接口影响
- 依赖方向、状态机、运行时机制影响
- 并发 / 实时性 / 资源 / 错误处理 / ABI 风险
- 跨组件协调点与是否需要其他组件 work item
- 成本与取舍：复杂度、兼容性、迁移风险、可回滚性、长期维护影响

给出推荐方案和理由。若只有一个显然方案，写 `Single obvious option`，说明为什么其它方案不成立（例如团队组件模板已限定、现有接口不可变、修订仅为文档同步）。

`interactive` 模式下，把方案摘要交给模块架构师确认后再进入完整设计；`auto` 模式下，只有当推荐方案不需要架构拍板、不改变跨组件契约且无开放协调点时才继续，否则标 `reroute_via_router=true` 回 `devflow-router`。

### 4. 加载团队模板

按 Template-Constrained Design，加载 `references/devflow-component-design-template.md`（项目 `AGENTS.md` 模板覆盖优先）。模板章节留空（团队未补齐）时**不阻塞写作**，但草稿中显式标注「使用 devflow 占位模板，待团队模板补齐」；review 前由模块架构师把模板章节补齐到团队规定结构。

### 5. 起草 / 修订设计

按 SOA Component Boundary Analysis + Clean Architecture + Interface Segregation + C/C++ Defensive Design 写 `features/<id>/component-design-draft.md`。具体结构必须遵循 `references/devflow-component-design-template.md` 的团队章节，不再使用 devflow 简化骨架。至少完整覆盖：

- **1 修订记录**、**2 术语**、**3 概述**：组件名、所属系统、职责 / 非职责、ASIL、Owner、参考资料
- **4 输入**：组件上下文视图（PlantUML）与组件全量功能列表；功能编号作为后续 AR 的基线引用
- **5 组件详细设计**：Design Options（候选方案 / trade-off / 推荐项 / 确认状态）、开发视图、代码结构模型、领域模型（如有）、实现模型、数据设计、构建依赖、运行视图、通信 / 数据流 / 并发机制
- **6 组件或子组件关键功能设计**：接口定义、功能列表详设、软件单元设计、需求描述列表、测试设计
- **6.1 接口定义**：Service / Topic / API / 软件单元间内部接口必须声明参数、返回值 / 错误码、是否支持并发、并发约束 / 保护机制、兼容性策略
- **6.2 功能列表详设**：每个关键功能 / 场景必须有 PlantUML 时序图；时序图必须细化到软件单元 / 类 / 方法调用级别，不能停留在组件级粗交互
- **6.3 软件单元设计**：核心类列表、文件映射、函数类型、函数名称、函数功能、输入 / 输出、错误处理，粒度需足以支撑 AR 设计和编码
- **6.5 测试设计**：测试项 ID、期望结果、观测点和对应功能编号
- **7 详细设计方案评审纪要**、**8 软件成本项设计评估（ASPICE）**：CPU、MEMORY、RAM / Disk、AI Core 等资源上限预估

任一必含章节缺失、Design Options 缺推荐项 / 确认状态、接口未声明并发约束、关键功能时序图未到类 / 方法级、软件单元未到函数级、测试设计缺观测点、成本评估未填写、或模板占位符未清理 → 不能进入评审。

### 6. 校验跨组件影响

按 SOA Component Boundary Analysis 列出修订接口 / 依赖 / 状态机带来的下游组件影响，以及是否需要在其他组件仓库分别开 work item / 升级 component-impact。跨组件协调点未确认 → 标为 Open Question 回需求负责人 / 模块架构师，不在本设计中替其他组件做决策。

### 7. 同步 traceability 与 progress

按 Requirements Traceability 在 `features/<id>/traceability.md` 补「Component Design Section」列，并把 `features/<id>/progress.md` 写为 `Current Stage = devflow-component-design`、`Pending Reviews And Gates` 含 `component-design-review`、`Next Action Or Recommended Skill = devflow-component-design-review`。canonical 字段不允许自由文本。

`Workflow Profile` 字段保持 router 分配的值（`requirement-analysis` 或 `component-impact`），本节点不切换 profile。

### 8. 自检与 handoff

进入 handoff 前自检：旧组件模板章节齐全；Design Options 已列候选方案 / trade-off / 推荐项 / 模块架构师确认状态（或 Single obvious option 理由）；无 `AI提示`、示例业务内容、变量替换说明、`TBD` / `{DATE}` 等残留；组件职责 / 非职责清晰；全量功能列表可作为 AR 基线；SOA 接口含参数、返回值 / 错误码、时序约束、兼容性和并发约束；依赖方向无环；状态机覆盖核心生命周期；并发 / 实时性 / 资源 / 错误处理已落到具体章节；每个关键功能 / 场景的时序图细化到软件单元 / 类 / 方法调用级；软件单元设计细化到函数级；测试设计有明确观测点；软件成本项已填写；「对 AR 实现设计的约束」可被下游消费；跨组件影响已显式列出。任一失败 → 回步骤 5 / 6。自检通过 → 父会话派发独立 reviewer subagent 执行 `devflow-component-design-review`。

## 输出契约

- `features/<id>/component-design-draft.md`（过程版本）
- review 通过且模块架构师 sign-off 后，**由 `devflow-finalize` 同步**到 `docs/component-design.md`（仅当项目已启用并触发变化时，再同步可选子资产 `docs/interfaces.md` / `docs/dependencies.md` / `docs/runtime-behavior.md`；未启用的，相关变化合并进 `docs/component-design.md` 对应章节）
- `features/<id>/traceability.md` 补充组件设计章节锚点
- `features/<id>/progress.md` 同步：
  - `Current Stage = devflow-component-design`
  - `Next Action Or Recommended Skill = devflow-component-design-review`
  - `Pending Reviews And Gates` 含 `component-design-review`
- handoff 摘要按 Local DevFlow Conventions 字段；`reviewer_dispatch_request` 字段指向 `devflow-component-design-review`

## 风险信号

- 把单个 AR 的代码层设计写进组件设计
- 跳过 Design Options，直接写单一组件方案
- 用 `Single obvious option` 掩盖仍需要模块架构师拍板的架构取舍
- 在 AR 上下文里临时改写组件架构（应停下回到本节点或上抛模块架构师）
- 修改其他组件
- 模板未补齐就让 reviewer 给 `通过`（应该让 reviewer 把模板留空作为 finding）
- 把模糊词（"高效"、"必要时"）作为组件级约束
- 跨组件协调未确认就声称设计完整

## 常见错误

| 错误 | 修复 |
|---|---|
| 把"AR-XYZ 的实现思路"写进组件设计 | 抽离回 `devflow-ar-design`；本设计只写组件级约束 |
| 团队模板留空，写得很短 | 显式标注待补齐章节；不要伪装完整 |
| 修订 SOA 接口未列错误码兼容性 | 补完错误码集合 + 兼容性策略 |

## 验证清单

- [ ] `features/<id>/component-design-draft.md` 已落盘
- [ ] 团队组件模板章节齐全，且无模板提示 / 示例业务内容 / 占位符残留
- [ ] 修订记录、术语、概述、输入、组件详细设计、关键功能设计、评审纪要、软件成本项章节齐全
- [ ] Design Options 已包含候选方案、trade-off、推荐项和模块架构师确认状态；或写明 Single obvious option 理由
- [ ] SOA 接口、依赖、数据 / 状态、并发 / 实时性 / 资源、错误处理、配置项、对 AR 设计的约束章节存在
- [ ] 接口并发约束完整，关键功能时序图到类 / 方法级，软件单元设计到函数级
- [ ] 测试设计观测点明确，软件成本项已填写
- [ ] 跨组件影响已显式列出
- [ ] traceability.md 已补充组件设计章节锚点
- [ ] progress.md 已 canonical 同步，下一步 `devflow-component-design-review`
- [ ] 模块架构师 owner 已记录
- [ ] 父会话准备派发独立 reviewer subagent

## 本地路由触发说明

仅当 router 选择了带组件设计修订的 `requirement-analysis`，或因 AR 触及组件职责、SOA interfaces、dependencies、state machine、runtime mechanism 而选择 `component-impact` 时，才进入本 skill。若本 skill 只是消费既有组件设计，回路由到 `devflow-router`。

## 本地 DevFlow 约定

本节由当前 skill 自己维护。不要加载共享约定文件；项目 `AGENTS.md` 可以覆盖等价路径或模板。

### 产物布局

默认产物布局来自 `docs/principles/03 artifact-layout.md`。项目 `AGENTS.md` 可以覆盖等价路径；没有覆盖时，本 skill 必须使用以下组件仓库布局：

```text
<component-repo>/
  docs/
    component-design.md           # 长期组件实现设计
    ar-designs/                   # 长期 AR 实现设计
      AR<id>-<slug>.md
    interfaces.md                 # 可选；仅团队启用时读取 / 同步
    dependencies.md               # 可选；仅团队启用时读取 / 同步
    runtime-behavior.md           # 可选；仅团队启用时读取 / 同步

  features/
    AR<id>-<slug>/                # 单个 AR 的过程产物
    DTS<id>-<slug>/               # 单个缺陷 / 问题修复的过程产物
    CHANGE<id>-<slug>/            # 单个轻量变更的过程产物
```

`docs/` 存放随代码提交的长期组件资产。`features/<id>/` 存放单个 work item 的过程产物：按需包含 `README.md`、`progress.md`、`requirement.md`、`ar-design-draft.md`、`tasks.md`、`task-board.md`、`traceability.md`、`implementation-log.md`、`reviews/`、`evidence/`、`completion.md`、`closeout.md`。

Read-on-presence 规则：

- 必需长期资产缺失时阻塞：component-impact 工作需要 `docs/component-design.md`；implementation closeout 前需要 `docs/ar-designs/AR<id>-<slug>.md`。
- 可选资产（`docs/interfaces.md`、`docs/dependencies.md`、`docs/runtime-behavior.md`）仅在项目启用时读取 / 同步。缺失的可选资产记录为 `N/A (project optional asset not enabled)`，不视为阻塞。
- 过程目录保留在 `features/` 下；不要把已关闭 work item 移到 `features/archived/`，否则会破坏追溯链接。

### Progress 字段

本 skill 读写 `features/<id>/progress.md` 时使用 canonical progress 字段：

- Work Item Type: SR / AR / DTS / CHANGE
- Work Item ID: SR1234、AR12345、DTS67890 或 CHANGE id
- Owning Component: AR / DTS / CHANGE 必填
- Owning Subsystem: SR 必填
- Workflow Profile: requirement-analysis / standard / component-impact / hotfix / lightweight
- Execution Mode: interactive / auto
- Current Stage: 当前 canonical devflow node
- Pending Reviews And Gates: 待处理 review / gate 列表
- Next Action Or Recommended Skill: 仅允许一个 canonical node
- Blockers: open blockers
- Last Updated: timestamp

### Handoff 字段

返回结构化 handoff，并使用本 skill 已知的字段：

- current_node
- work_item_id
- owning_component or owning_subsystem
- result or verdict
- artifact_paths
- record_path, when a review / gate / verification record exists
- evidence_summary
- traceability_links
- blockers
- next_action_or_recommended_skill
- reroute_via_router

不要把 `next_action_or_recommended_skill` 设为 `using-devflow` 或自由文本。

### 组件设计资产

当 `docs/component-design.md` 存在或必需时读取。可选资产 `docs/interfaces.md`、`docs/dependencies.md`、`docs/runtime-behavior.md` 按 read-on-presence 读取；缺失可选资产不阻塞。

### 组件设计最小内容

覆盖组件职责、SOA services/interfaces、dependencies、data model/state machine、concurrency/realtime/resources、error handling、configuration，以及对 AR design 的约束。
## 支撑参考

| 文件 | 用途 |
|---|---|
| `references/devflow-component-design-template.md` | 团队组件设计模板（待团队补齐） |
