---
name: devflow-specify
description: Use when the team has accepted an SR / AR / DTS / change request as input and needs it clarified into a reviewable spec. Covers two sub-streams: (a) requirement-analysis sub-stream — clarify subsystem-level SR + optional component implementation design; does NOT proceed to AR-level implementation; (b) implementation sub-stream — clarify AR (or DTS that needs an AR-level spec) before devflow-ar-design / devflow-tdd-implementation. Not for product discovery (回需求负责人), not for designing the AR implementation (→ devflow-ar-design), not for component implementation design authoring (→ devflow-component-design), not for hotfix reproduction / root cause (→ devflow-problem-fix).
---

# devflow 需求规格澄清（覆盖 SR-分析 与 AR-实现 两条子街区）

把团队已经接受的需求输入澄清成可被 `devflow-spec-review` 评审的需求规格对象。本 skill 同时服务两个子街区：

1. **需求分析子街区（SR）**：澄清子系统级需求 / 修订；下一步可选地进入 `devflow-component-design` 修订组件实现设计；分析阶段以 **analysis closeout** 结束，**不**进入 `devflow-ar-design` / TDD / completion-gate。SR 拆出的候选 AR 由需求负责人按 closeout 中的 AR Breakdown Candidates **新建** AR work item，后者重新走实现子街区。
2. **实现子街区（AR / DTS / CHANGE）**：澄清单个 AR（或需要 AR-级规格的 DTS）；下一步进入 `devflow-ar-design` 或 `devflow-component-design`（component-impact）。

本 skill 不做产品发现、不创造需求方向、不替需求负责人决定优先级；当输入不清且涉及方向 / 范围 / 验收标准时，只整理待决问题列表，回需求负责人。

## When to Use

适用：

- **SR**：已接收 SR 输入，需要澄清子系统级范围 / 受影响组件 / 候选 AR 拆分；本 SR work item 可选地继续到组件设计修订，但**不**进入 AR 实现
- **AR / DTS / CHANGE**：已有 AR / DTS / 变更请求，但需求规格尚不足以进入 AR 实现设计；AR 范围、所属组件、SR / IR 追溯关系、验收标准仍需澄清
- `devflow-spec-review` 返回 `需修改` / `阻塞`，需按 findings 修订规格
- 用户说"先把这个 SR / AR 的需求理清楚"

不适用 → 改用：

- 仍在判断该需求是否值得做 → 不属于 df，回需求负责人
- 已有可设计规格，要写 AR 实现设计 → `devflow-ar-design`
- 已有可设计规格，要写组件实现设计 → `devflow-component-design`
- 紧急缺陷的复现 / 根因 → `devflow-problem-fix`
- 阶段不清 / 证据冲突 → `devflow-router`

## Hard Gates

- 需求规格通过 `devflow-spec-review` 之前，不得进入 `devflow-component-design`、`devflow-ar-design`
- SR work item 不得进入 `devflow-ar-design` / `devflow-tdd-implementation` / `devflow-test-checker` / `devflow-code-review` / `devflow-completion-gate` / `devflow-problem-fix`；SR 拆出的候选 AR 必须新建 AR work item
- 不得替需求负责人 / 模块架构师创造业务规则、优先级或验收阈值
- AR / DTS / CHANGE 必须有唯一所属组件；SR 必须有唯一所属子系统；不唯一时阻塞，回需求负责人
- IR / SR / AR 追溯关系冲突 → 阻塞，回需求负责人
- 不把待决问题只藏在正文里，必须显式列在「Open Questions」章节
- AR / DTS / CHANGE 若出现 `IFR` 或 `Component Impact = interface`，必须维护 `Interface Contract Candidates`；不得只写“影响接口”而不给设计可消费的契约边界
- 未经 `using-devflow` / `devflow-router` 入口判断 → 先回 router

## Object Contract

- Primary Object: requirement specification model（一个 work item 的需求规格）
- Frontend Input Object：
  - **SR**：已接受的 IR / SR 输入 + 团队既有输入文档 + 当前组件仓库 / 子系统范围内的 `docs/component-design.md`（如存在；用于评估受影响组件）
  - **AR / DTS / CHANGE**：已接受的 IR / SR / AR / DTS / 变更请求 + 团队既有输入文档 + 当前组件仓库的 `docs/component-design.md`（如存在）
- Backend Output Object: `features/<id>/requirement.md` 草稿 + `features/<id>/traceability.md` 骨架 + `features/<id>/progress.md` canonical 字段同步
- Object Transformation: 把团队已接受的输入澄清为可设计的需求规格对象（含范围 / 非范围 / 验收 / 待决问题 / 追溯）
  - SR 额外产出：Subsystem Scope Assessment、Affected Components、AR Breakdown Candidates、Component Design Impact
  - AR / DTS / CHANGE 额外产出：Component Impact Assessment、Interface Contract Candidates（当涉及接口）
- Object Boundaries: 不写实现设计 / 不写代码 / 不修改既有组件实现设计 / 不重新决定要不要做这个需求；SR 不预先做 AR 级实现设计
- Object Invariants: Work Item ID、所属组件 / 子系统、上游追溯（IR / SR）、当前轮范围在 spec-review 通过前保持稳定

## Methodology

- **Requirements Traceability**: 显式建立 IR -> SR -> AR 链路；DTS 修改若涉及功能需求时建立 DTS -> AR -> SR 反向锚点
- **Scope / Non-Scope / Acceptance Criteria**: 规格按"做什么 / 不做什么 / 怎样算完成"组织
- **Socratic Elicitation**: Capture → Challenge → Clarify 三段式提问，先收敛范围 / 角色 / 成功标准，再收敛边界细节
- **EARS（Easy Approach to Requirements Syntax — Mavin 等, 2009）**: 需求 Statement 使用结构化句式（常驻 / 事件触发 / 状态约束 / 异常 / 可选），让 reviewer 可冷读判断；详见 `references/requirement-rows-contract.md` 的 Statement Patterns 节
- **BDD Acceptance（Dan North, 2006）**: Acceptance 用 Given / When / Then 表达；AR row 要可测试（直接落 RED 用例），SR row 要可观察（端到端判定）；详见 `references/requirement-rows-contract.md` 的 Acceptance Criteria Rules 节
- **MoSCoW Priority（DSDM, 1994）或团队等价**: row 级 Priority；多条 Must 冲突时回需求负责人；devflow 不维护跨工作项 backlog
- **INVEST Granularity（Bill Wake, 2003）**: 单条 row 的 `Small` + `Independent` 检查（G1-G6 + 嵌入式 GE1-GE2）；以及 SR 候选 AR 的拆分启发式；详见 `references/granularity-and-split.md`
- **NFR Quality Attribute Scenarios（ISO/IEC 25010 + Bass / Clements / Kazman）**: 每条核心 NFR 用五要素（Stimulus Source / Stimulus / Environment / Response / Response Measure）表达，给出可判定阈值；详见 `references/nfr-quality-attribute-scenarios.md`
- **Brainstorming Notes Normalization**: 头脑风暴 / 会议散点输入先做事实 vs 假设、业务意图 vs 实现细节、当前 vs 后续三轮归一化，再写 row；详见 `references/requirement-rows-contract.md` 同名节
- **Embedded Domain Awareness**: 嵌入式语境中识别可能影响 AR 设计的内存 / 实时性 / 资源约束（写为 NFR 不写实现），并指向 `docs/component-design.md` 的相关章节
- **Interface Contract Candidate Capture**: 对外接口 / SOA 服务 / 协议 / 错误码先形成语义级候选契约，供组件设计或 AR 设计消费；不在 spec 阶段写语言级签名或内部数据结构
- **Team Role Discipline**: 业务方向 / 优先级 / 验收阈值留给需求负责人 / 模块架构师；本节点只澄清，不拍板

## Workflow

### 1. 对齐最少必要上下文 + 确认 work item 类型与子街区

按 Read-On-Presence 读取澄清规格所需的最少材料：用户请求 / 上游单据（IR / SR / AR / DTS）摘要、团队 `AGENTS.md` 路径映射、`features/<id>/progress.md`（若存在）、当前组件仓库的 `docs/component-design.md` / `docs/ar-designs/`（若存在）。

显式确认本 work item 类型与子街区：

- `SR` → 需求分析子街区，profile = `requirement-analysis`；本节点产出 SR 规格 + AR Breakdown Candidates；**不**进入 AR 实现设计 / TDD / completion-gate
- `AR` / `CHANGE` → 实现子街区；按 router 分配的 `standard` / `component-impact` / `lightweight` profile 推进
- `DTS`（需要 AR-级规格）→ 实现子街区；通常已先经 `devflow-problem-fix` 产出 reproduction / root-cause / fix-design

工件冲突、不确定 work item 类型，或用户描述介于 SR / AR 之间 → 回 `devflow-router`。

### 2. 初始化或对齐 work item 目录


按 work item 类型校验必填字段：

- `SR`：必须有 `Work Item ID`、`Owning Subsystem`；`Owning Component` 可空（子系统级 / 跨组件）
- `AR` / `DTS` / `CHANGE`：必须有 `Work Item ID`、`Owning Component`

缺必填字段 → 阻塞，回需求负责人。

### 3. 澄清需求（Capture → Challenge → Clarify）

按 Socratic Elicitation 三段式提问，覆盖以下面（已覆盖的跳过、不重复追问）：

1. 用户、目标、成功标准、非目标
2. 核心行为与触发条件
3. 边界、异常路径、失败处理
4. 接口、依赖、兼容性、跨组件影响；若涉及接口，澄清 provider / consumer / operation / inputs / outputs / error semantics
5. 嵌入式相关 NFR（实时性 / 内存 / 资源 / 错误处理）
6. 待澄清术语与 assumption

每轮结束前总结已锁定与待确认；只剩 1-2 个阻塞事实时合并问。若需要 ≥3 轮且全部依赖业务判断 → 阻塞，回需求负责人；devflow 不替业务方拍板。

### 4. 整理 requirement rows

按 Scope / Non-Scope / Acceptance Criteria + EARS Statement Patterns + BDD Acceptance Rules + MoSCoW Priority 把澄清结果结构化。每条核心 row 至少含 `ID`（FR / NFR / CON / IFR / ASM / EXC）、`Statement`（EARS 句式）、`Acceptance`（BDD Given/When/Then）、`Priority`、`Source / Trace Anchor`、`Component Impact`（AR / DTS / CHANGE）或 `Affected Components`（SR）。最小字段契约 + 句式表 + Brainstorming Notes Normalization 详见 `references/requirement-rows-contract.md`。

核心 NFR 必须能写成 QAS 五要素：Stimulus Source / Stimulus / Environment / Response / Response Measure（含阈值或可判定准则）。详见 `references/nfr-quality-attribute-scenarios.md`。如果某条 NFR 写不出 QAS → 该 NFR 描述还不够具体，回步骤 3 找需求负责人 / 模块架构师补阈值。

按 INVEST 检查每条 row 的 `Small` + `Independent`：命中 G1-G6 / GE1-GE2 任一信号 → 按 Split Rules 拆分；详见 `references/granularity-and-split.md`。任一核心 row 缺 Acceptance / 缺 Priority / NFR 缺 QAS 阈值 → 回步骤 3。

### 5. 草拟规格文档

按 Template-Constrained 写 `features/<id>/requirement.md`，结构遵循团队 `AGENTS.md` 模板覆盖。

通用默认章节：Identity、Background And Goal、Scope / Non-Scope、Requirement Rows、Acceptance Criteria、Embedded NFR（若适用）、Open Questions（阻塞 / 非阻塞分类）、Assumptions And Dependencies。

按 work item 类型的额外必填章节：

- **SR**：
  - **Subsystem Scope Assessment**：本 SR 影响子系统范围、跨组件影响
  - **Affected Components**：受影响组件清单 + 每个组件的预计修改面（接口 / 依赖 / 状态机 / 数据 / 实现）
  - **AR Breakdown Candidates**：候选 AR 拆分清单（每条候选含范围 / 所属组件 / 优先级 / 上抛对象；本字段在 spec-review 后可能继续修订，最终在 `devflow-finalize` analysis closeout 时定稿）
  - **Component Design Impact**：本 SR 是否需要 `devflow-component-design`；若需要，要修订哪些章节
- **AR / DTS / CHANGE**：
  - **Component Impact Assessment**：本需求是否影响 SOA 接口 / 组件依赖 / 状态机；指向 `docs/component-design.md` 相关章节
  - **Interface Contract Candidates**：当存在 `IFR` row 或 `Component Impact = interface` 时必填。每条候选至少含：
    - Interface / Service Name（可为候选名）
    - Provider Component
    - Consumer / Caller
    - Trigger / Operation
    - Inputs（语义级字段、单位、约束；不强制语言类型）
    - Outputs / Observable Result
    - Error / Return Semantics
    - Sync / Async / Timing Expectation
    - Compatibility / Versioning
    - Covers Requirement Rows
    - Open Questions / Owner

接口候选契约的边界：它应足够让 `devflow-component-design` / `devflow-ar-design` 消费，但不得在 spec 阶段锁死内部函数签名、私有数据结构、重试次数、线程模型或具体库选择。这些设计选择进入后续 design 节点。

### 6. 同步 traceability 与 progress

按 Requirements Traceability，把上游 IR / SR / AR 锚点填入 `features/<id>/traceability.md`：

- SR 的 traceability 含 IR / SR、Affected Components、Candidate AR Breakdown 列；不含 Code / Test / Verification 列
- AR / DTS / CHANGE 的 traceability 含 IR / SR / AR、Component Design Section、AR Design Section、Code / Test / Verification 占位

在 `features/<id>/progress.md` 写入 canonical 字段：`Current Stage = devflow-specify`、`Workflow Profile = requirement-analysis`（SR）/ router 分配的实现 profile（AR/DTS/CHANGE）、`Pending Reviews And Gates = spec-review`、`Next Action Or Recommended Skill = devflow-spec-review`、`Last Updated`。不允许自由文本下一步。

SR 还需在 progress 中写入 `Owning Subsystem`；可空字段 `AR Breakdown Candidates` 可在草稿期为空，等 spec-review 后定稿。

### 7. 评审前自检

通用自检：

- 业务背景 / 目标 / 用户清晰
- 范围 / 非范围显式
- 核心 FR / NFR 含 ID / Statement（EARS）/ Acceptance（BDD）/ Priority（MoSCoW 或团队等价）/ Source
- 核心 NFR 已归类到 ISO/IEC 25010 维度并含 QAS 五要素；Response Measure 有阈值；Acceptance 与 QAS 一致（详见 `references/nfr-quality-attribute-scenarios.md` 最小签入条件）
- 单条 row 已通过 INVEST `Small` + `Independent` 检查（无未处理的 G1-G6 / GE1-GE2 oversized 信号；详见 `references/granularity-and-split.md`）
- Brainstorming Notes 已按归一化表落到正确 row 类别，未把猜测当事实
- Open Questions 已分类（阻塞 / 非阻塞），阻塞项已闭合或显式回需求负责人
- traceability.md 至少含上游追溯行

按 work item 类型的额外自检：

- SR：
  - Subsystem Scope Assessment / Affected Components / AR Breakdown Candidates（草稿可待定）/ Component Design Impact 章节存在
  - AR Breakdown Candidates 中的候选已通过 SR Breakdown Heuristics 检查（Owning Component 唯一、不太粗 / 不太细、无循环依赖；详见 `references/granularity-and-split.md`）
  - 若声明「无可拆分 AR」，已写明理由
- AR / DTS / CHANGE：
  - Component Impact Assessment 章节存在并已显式判断
  - 若存在 `IFR` 或 `Component Impact = interface`，Interface Contract Candidates 章节存在，且每条候选含 provider / consumer / operation / inputs / outputs / error semantics / compatibility / open questions
  - AR row 的 Acceptance 可直接落成 RED 用例

任一失败 → 回步骤 4 / 5。

### 8. Handoff


## Output Contract

完成时产出：

- `features/<Work Item Id>-<slug>/requirement.md`（团队 `AGENTS.md` 覆盖路径优先；按 work item 类型含相应额外章节）
- `features/<Work Item Id>-<slug>/traceability.md`（按 work item 类型初始化对应列）
- `features/<Work Item Id>-<slug>/progress.md` 已同步：
  - `Current Stage` = `devflow-specify`
  - `Workflow Profile` = `requirement-analysis`（SR）/ router 分配的实现 profile（AR / DTS / CHANGE）
  - `Pending Reviews And Gates` 含 `spec-review`
  - `Next Action Or Recommended Skill` = `devflow-spec-review`
- `features/<Work Item Id>-<slug>/README.md` 中 Requirement 行更新

handoff 摘要（按 Local DevFlow Conventions 字段）：`work_item_id`、`owning_component` / `owning_subsystem`、`workflow_profile`、`artifact_paths`、`traceability_links`、`blockers`（如有 USER-INPUT 阻塞项）、`next_action_or_recommended_skill = devflow-spec-review`。

未达评审门槛时不伪造 handoff；明确仍缺什么。

## Red Flags

- 把用户输入的自然语言需求直接当 requirement rows
- 越过模块架构师，自行决定组件归属
- 把"以后再做"只留在 prose 而无 Open Questions / 非范围
- 缺 Acceptance 却声称需求清晰
- 把实现细节（接口签名、表结构、数据结构）写进 Statement
- AR 影响 SOA 接口却不在 Component Impact Assessment 中标注
- AR / DTS / CHANGE 影响接口却缺 Interface Contract Candidates
- 在 Interface Contract Candidates 中写死内部函数签名 / 私有数据结构 / 线程模型
- 把 USER-INPUT 阻塞项当 LLM-FIXABLE 自我硬补
- 不更新 progress.md 就声称交接

## Common Mistakes

| 错误 | 修复 |
|---|---|
| 直接抄输入文档作为 requirement.md | 重新拆成 rows + 显式 Acceptance |
| 含糊的 NFR（"足够快"） | 改成可判定阈值或回需求负责人补阈值 |
| 误把组件设计修订写进 requirement.md | 仅在 Component Impact Assessment 标注，由 router 决定是否进入 `devflow-component-design` |
| 把接口候选写成 C++ 函数签名 | 改成语义级契约：provider / consumer / operation / inputs / outputs / error semantics |

## Verification

通用：

- [ ] `features/<id>/requirement.md` 已落盘
- [ ] 业务背景、目标、范围、非范围、Acceptance Criteria 已写清
- [ ] 核心 FR / NFR 具备 ID / Statement（EARS 句式）/ Acceptance（BDD Given/When/Then）/ Priority（MoSCoW 或团队等价）/ Source
- [ ] 核心 NFR 已归类到 ISO/IEC 25010 维度并含 QAS 五要素；Response Measure 有阈值；Acceptance 与 QAS 一致
- [ ] 单条 row 通过 INVEST `Small` + `Independent` 检查；命中 G1-G6 / GE1-GE2 已按 Split Rules 处理或显式标注
- [ ] Brainstorming Notes 已按归一化表落到正确 row 类别
- [ ] Open Questions 已分类为阻塞 / 非阻塞，阻塞项已闭合或回需求负责人
- [ ] progress.md 已按 canonical schema 同步，含 `Workflow Profile`，下一步为 `devflow-spec-review`
- [ ] feature README 中 Requirement 行已更新

SR work item 额外项：

- [ ] Subsystem Scope Assessment / Affected Components / AR Breakdown Candidates（草稿可待定）/ Component Design Impact 章节存在
- [ ] AR Breakdown Candidates 通过 SR Breakdown Heuristics 检查（Owning Component 唯一、不太粗 / 不太细、无循环依赖），或显式声明「无可拆分 AR」+ 理由
- [ ] traceability.md 含 IR / SR、Affected Components、Candidate AR Breakdown 列
- [ ] `Owning Subsystem` 已记录

AR / DTS / CHANGE work item 额外项：

- [ ] Component Impact Assessment 已显式判断
- [ ] 涉及接口时，Interface Contract Candidates 已给出 provider / consumer / operation / inputs / outputs / error semantics / compatibility / open questions
- [ ] traceability.md 含 IR / SR / AR 行
- [ ] `Owning Component` 已记录

## Local DevFlow Conventions

This section is owned by this skill. Do not load a shared conventions file. Project AGENTS.md may override equivalent paths or templates.

### Artifact Layout

Default artifact layout is copied from `docs/principles/03 artifact-layout.md`. Project `AGENTS.md` may override equivalent paths, but absent an override this skill must use the following component-repo layout:

```text
<component-repo>/
  docs/
    component-design.md           # long-lived component implementation design
    ar-designs/                   # long-lived AR implementation designs
      AR<id>-<slug>.md
    interfaces.md                 # optional, read/sync only when enabled by team
    dependencies.md               # optional, read/sync only when enabled by team
    runtime-behavior.md           # optional, read/sync only when enabled by team

  features/
    AR<id>-<slug>/                # process artifacts for one AR
    DTS<id>-<slug>/               # process artifacts for one defect / problem fix
    CHANGE<id>-<slug>/            # process artifacts for one lightweight change
```

`docs/` is for long-lived component assets that are committed with code. `features/<id>/` is for one work item's process artifacts: `README.md`, `progress.md`, `requirement.md`, `ar-design-draft.md`, `tasks.md`, `task-board.md`, `traceability.md`, `implementation-log.md`, `reviews/`, `evidence/`, `completion.md`, and `closeout.md` as applicable.

Read-on-presence rules:

- Required long-lived assets block when missing: `docs/component-design.md` for component-impact work, and `docs/ar-designs/AR<id>-<slug>.md` by implementation closeout.
- Optional assets (`docs/interfaces.md`, `docs/dependencies.md`, `docs/runtime-behavior.md`) are read/synced only when the project has enabled them. Missing optional assets are recorded as `N/A (project optional asset not enabled)`, not treated as blockers.
- Process directories stay under `features/`; do not move closed work items to `features/archived/` because that breaks traceability links.

### Progress Fields

Use canonical progress fields when this skill reads or writes features/<id>/progress.md:

- Work Item Type: SR / AR / DTS / CHANGE
- Work Item ID: SR1234, AR12345, DTS67890, or CHANGE id
- Owning Component: required for AR / DTS / CHANGE
- Owning Subsystem: required for SR
- Workflow Profile: requirement-analysis / standard / component-impact / hotfix / lightweight
- Execution Mode: interactive / auto
- Current Stage: current canonical devflow node
- Pending Reviews And Gates: pending review or gate list
- Next Action Or Recommended Skill: one canonical node only
- Blockers: open blockers
- Last Updated: timestamp

### Handoff Fields

Return a structured handoff with the fields this skill knows:

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

Do not set next_action_or_recommended_skill to using-devflow or free text.

### Work Item Skeleton

Default process directories are features/SR<id>-<slug>/, features/AR<id>-<slug>/, features/DTS<id>-<slug>/, and features/CHANGE<id>-<slug>/.

### Requirement.md Minimum Content

- Identity: type, id, owner, component/subsystem, IR/SR/AR links, profile
- Background And Goal
- Scope / Non-Scope
- Requirement Rows with ID, statement, acceptance, source, component impact
- Acceptance Criteria
- Embedded NFR when relevant
- Open Questions split into blocking and non-blocking
- Assumptions And Dependencies
- SR adds Subsystem Scope Assessment, Affected Components, AR Breakdown Candidates, Component Design Impact
- AR / DTS / CHANGE adds Component Impact Assessment and Interface Contract Candidates when interfaces are affected
## Supporting References

| 文件 | 用途 |
|---|---|
| `references/requirement-rows-contract.md` | requirement rows 最小字段、EARS Statement Patterns、BDD Acceptance Rules、MoSCoW Priority、Source / Trace Anchor、Brainstorming Notes Normalization、Common Failure Modes |
| `references/granularity-and-split.md` | INVEST `Small` + `Independent` 检查（G1-G6 + 嵌入式 GE1-GE2）、Split Rules、Mechanical vs Scope-Shaping Split、Cross-Work-Item Split、SR Breakdown Heuristics |
| `references/nfr-quality-attribute-scenarios.md` | ISO/IEC 25010 质量维度、QAS 五要素、嵌入式 NFR 改写示例（实时性 / 内存 / 并发 / 资源 / 错误处理 / 安全）、SR 视角 NFR、最小签入条件 |
| `references/devflow-work-item-readme-template.md` | work item README 模板 |
| `references/devflow-progress-template.md` | progress.md 模板 |
| `references/devflow-traceability-template.md` | traceability.md 模板 |
