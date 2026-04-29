---
name: devflow-ar-design
description: Use when the spec is approved and the AR (or DTS that needs an AR-level design) needs a code-level implementation design with an embedded test design section, when component design is stable enough to be consumed (or has just been approved by devflow-component-design-review), or when devflow-ar-design-review returns 需修改/阻塞. Not for changing component architecture (→ devflow-component-design), not for writing production code (→ devflow-tdd-implementation), not for unclear spec (→ devflow-specify), not for hotfix root cause (→ devflow-problem-fix).
---

# devflow AR 实现设计

把单个 AR（或需要正式 AR 实现设计的 DTS）转化为**代码层设计**与**测试设计**。测试设计是本设计的**章节**，不作为独立文件存在。

本 skill 不修改组件实现设计（必要时回 `devflow-component-design`），不写代码（那是 `devflow-tdd-implementation`），不替开发负责人决定优先级。

## When to Use

适用：

- `devflow-spec-review` 已通过 + 当前修改不触及组件边界（standard / lightweight profile） → 直接进入本节点
- `devflow-component-design-review` 已通过且模块架构师 sign-off（component-impact profile） → 进入本节点
- `devflow-ar-design-review` 返回 `需修改` / `阻塞`，需按 findings 修订
- DTS 修复需要正式 AR 实现设计（可在 `devflow-problem-fix` 后触发）

不适用 → 改用：

- 当前修改影响组件接口 / 依赖 / 状态机 → 回 `devflow-component-design`
- 规格不清 → `devflow-specify`
- 已有可消费的 AR 设计但尚未形成 tasks → `devflow-tdd-implementation`；task queue preflight 已通过且 active task 已锁定才进入 `devflow-tdd-implementation`
- 阶段不清 / 证据冲突 → `devflow-router`

## Hard Gates

- AR 实现设计必须遵循团队模板（`references/devflow-ar-design-template.md`；模板留空时由开发负责人 / 模块架构师补齐章节后再交评审）
- AR 实现设计必须含**测试设计章节**；测试设计**不**作为独立 `test-design.md` 文件
- 不修改组件实现设计；触及组件边界 → 停下回 `devflow-router`
- 起草正式设计前必须提出 2-3 个实现方案并记录 trade-off / 推荐方案；低风险单一路径可写 `Single obvious option`，但必须说明为什么不展开多方案
- `interactive` 模式下，推荐方案需由开发负责人确认后再写完整 AR 设计；`auto` 模式下，若方案选择需要业务 / 架构拍板则停下回 `devflow-router`
- AR 实现设计 review 通过前，`devflow-tdd-implementation` 不得开始；`devflow-tdd-implementation` 只能消费已批准 AR 设计，并在内部完成 task queue preflight 后执行当前 active task
- 本设计中**不**写完整生产代码；可写关键控制流伪代码 / 接口签名草案以支撑 review
- 正式输出不得残留 `AI提示`、示例业务内容、变量替换说明、`TBD` / `{DATE}` 等模板占位符

## Object Contract

- Primary Object: AR implementation design model（含测试设计章节）
- Frontend Input Object: 已通过 spec-review 的 `features/<id>/requirement.md`、`docs/component-design.md`（已存在或已通过 component-design-review）；项目已启用可选子资产时一并读取 `docs/interfaces.md` / `docs/dependencies.md` / `docs/runtime-behavior.md`（未启用直接跳过、不阻塞）；当前组件代码现状摘要
- Backend Output Object: `features/<id>/ar-design-draft.md`（过程版） + 同步到 `docs/ar-designs/AR<id>-<slug>.md`（review 通过后由 `devflow-finalize` 同步）
- Object Transformation: 把单个 AR 转成代码层设计 + 可执行的测试意图
- Object Boundaries: 不写组件级设计；不写完整代码；不发明组件接口
- Object Invariants: AR ID、所属组件、SR / IR 锚点、设计目标 / 范围在 review 通过前保持稳定

## Methodology

- **Code-Level Design**: 数据结构、控制流、接口签名草案、关键路径伪代码
- **Requirements Traceability**: 设计章节回指 requirement.md 的 FR / NFR / IFR rows
- **SOLID / GRASP**: 职责清晰、低耦合、高内聚、可测试性
- **C / C++ Defensive Design**: 内存、生命周期、错误处理、并发、实时性、资源释放、ABI / API 兼容
- **Component Design Conformance**: 与 `docs/component-design.md` 的对 AR 设计的约束保持一致；不重新论证组件级决策
- **Design Options Before Draft**: 正式起草前先列 2-3 个代码层方案、trade-off、推荐项与确认状态
- **Template-Constrained Design**: 文档结构由团队模板决定（`references/devflow-ar-design-template.md`，留空待团队补齐）
- **Test Design Before Implementation**: 测试设计章节先于 TDD；用例覆盖 AR 关键行为、边界、异常路径、嵌入式风险

## Workflow

### 1. 对齐输入与角色

按 Requirements Traceability + Component Design Conformance 读取 requirement.md、reviews/spec-review.md（应 `通过`）、`docs/component-design.md`；项目已启用的可选子资产 `docs/interfaces.md` / `docs/dependencies.md` / `docs/runtime-behavior.md` 也一并读取，未启用直接跳过、不阻塞；相关代码现状摘要、component-design-review.md（component-impact 时）。

- spec-review 未通过 → 阻塞，回 `devflow-router`
- profile 是 component-impact 但 component-design-review 未通过 → 阻塞，回 `devflow-router`
- 团队模板未补齐 → 不阻塞写作，但显式标注「使用 devflow 占位模板，待团队模板补齐」

### 2. 检查是否触及组件边界

按 SOA Boundary 检查对照 requirement.md 的 Component Impact 与当前 AR 的初步思路。**触及组件接口 / 依赖 / 状态机** → 立即停下，标 `reroute_via_router=true`，回 `devflow-router` 升级 component-impact。AR 实现设计**不**修改组件架构。

### 3. 方案选择 checkpoint

在写完整 `ar-design-draft.md` 前，先产出 `Design Options` 小节，列 2-3 个可行实现方案；每个方案至少包含：

- 改动范围：涉及文件 / 模块 / 接口签名草案
- 控制流 / 数据结构要点
- 测试策略：会驱动哪些 Test Design Case ID 或测试类型
- 风险：内存 / 并发 / 实时性 / 错误处理 / ABI / SOA 边界
- 成本与取舍：实现复杂度、可回滚性、后续维护影响

给出推荐方案和理由。若只有一个显然方案，写 `Single obvious option`，说明为什么其它方案不成立（例如组件设计已限定、变更极小、接口不可变）。

`interactive` 模式下，把方案摘要交给开发负责人确认后再进入完整设计；`auto` 模式下，只有当推荐方案不需要业务 / 架构拍板且不改变组件边界时才继续，否则标 `reroute_via_router=true` 回 `devflow-router`。

### 4. 加载团队模板

按 Template-Constrained Design 加载 `references/devflow-ar-design-template.md`（项目 `AGENTS.md` 覆盖优先）；模板章节留空时显式标注「使用 devflow 占位模板，待团队模板补齐」。

### 5. 起草代码层设计

按 Code-Level Design + SOLID / GRASP + C / C++ Defensive Design 写 `features/<id>/ar-design-draft.md`。具体结构必须遵循 `references/devflow-ar-design-template.md` 的团队章节，不再使用 devflow 简化骨架。至少完整覆盖：

- **1 AR 概述**：Work Item ID、AR 系统流水号、AR 描述、所属组件、关联 IR / SR、Owner、组件基线
- **2 动态行为**：PlantUML 交互时序图，参与者使用真实组件 / 类 / 服务名，消息体现接口或方法调用
- **3 功能点分解**：功能点 ID、Covers Requirement、描述、优先级、是否可独立测试；每个功能点必须可回指 requirement row
- **4 实现设计**：Design Options（候选方案 / trade-off / 推荐项 / 确认状态）、功能实现思路、用例 / 流程图、正常 / 异常流程、持久化设计（如有）、接口描述、代码设计、MDC 场景设计
- **4.7 MDC 场景设计**：并发、启动退出、休眠唤醒、可靠性、SELinux 五类场景均需分析；写“不涉及”时必须给出判定依据
- **5 重构设计**：需要重构时说明范围、影响模块、验证方式和是否触发升级
- **6 测试设计**：必含，见步骤 5
- **7 模板修订记录**

任一必含章节缺失、Design Options 缺推荐项 / 确认状态、图形只有占位、功能点不能追溯到 requirement row、或模板占位符未清理 → 不能进入步骤 6 / 评审。

### 6. 起草测试设计章节（必含）

按 Test Design Before Implementation 把 requirement.md 中的 FR / NFR / IFR 行落成测试设计章节。测试设计是 AR 实现设计的**章节**，**不**作为独立 `test-design.md` 文件。最小字段契约见 `references/test-design-section-contract.md`。至少含：

- 测试点汇总：Case ID、覆盖功能点、回指 requirement row ID、测试层级（unit / integration / simulation）、覆盖类型（happy / boundary / exception / embedded-risk）、测试因子、组合方式、逻辑覆盖程度
- 单元测试 / 接口测试 / 业务场景测试 / 异常场景测试：每个用例含前置条件、触发步骤、预期结果、观测点
- Mock / Stub / 仿真说明：边界点 + 哪些依赖必须 mock、哪些必须真实运行
- RED / GREEN / REFACTOR 证据要求：哪些命令 / 日志 / 静态分析结果必须保留
- 嵌入式风险覆盖矩阵：内存 / 并发 / 实时性 / 资源 / 错误处理 / ABI 各维度覆盖了哪些用例

测试用例未回指 requirement row、或嵌入式 NFR 未被任何用例覆盖 → 回步骤 5 / 6 修订。

### 7. 同步 traceability 与 progress

按 Requirements Traceability 在 `features/<id>/traceability.md` 补「AR Design Section」与「Test Design Case」列；把 `features/<id>/progress.md` 写为 `Current Stage = devflow-ar-design`、`Pending Reviews And Gates` 含 `ar-design-review`、`Next Action Or Recommended Skill = devflow-ar-design-review`。

### 8. 自检与 handoff

进入 handoff 前自检：旧 AR 模板章节齐全；Design Options 已列候选方案 / trade-off / 推荐项 / 确认状态（或 Single obvious option 理由）；无 `AI提示`、示例业务内容、变量替换说明、`TBD` / `{DATE}` 等残留；动态行为 / 流程 / 类图等图形已替换为真实内容或明确 N/A 理由；功能点可追溯且可被测试设计覆盖；MDC 五场景均已分析；接口描述含参数 / 返回值 / 错误码 / 并发约束；与组件设计一致且未修改组件接口；测试设计章节存在且每个用例回指 requirement row + 功能点；嵌入式风险覆盖矩阵完整；风险与未决问题已分类。任一失败 → 回步骤 5 / 6。自检通过 → 父会话派发独立 reviewer subagent 执行 `devflow-ar-design-review`。

## Output Contract

- `features/<id>/ar-design-draft.md`（过程版本）
- review 通过后由 `devflow-finalize` 同步到 `docs/ar-designs/AR<id>-<slug>.md`
- traceability.md 补充 AR Design Section + Test Design Case
- progress.md 同步：
  - `Current Stage = devflow-ar-design`
  - `Next Action Or Recommended Skill = devflow-ar-design-review`
  - `Pending Reviews And Gates` 含 `ar-design-review`
- handoff 摘要按 Local DevFlow Conventions；`reviewer_dispatch_request` 指向 `devflow-ar-design-review`

## Red Flags

- 把整段实现代码贴进设计
- 跳过 Design Options，直接写单一实现方案
- 用 `Single obvious option` 掩盖仍需要开发负责人 / 架构师拍板的取舍
- 在 AR 设计中改写组件接口 / 依赖 / 状态机
- 测试设计被拆成独立 `test-design.md` 文件（devflow 硬约定：测试设计必须是 AR 实现设计的章节）
- 测试用例不回指 requirement row
- 嵌入式 NFR 不被任何用例覆盖
- 模板未补齐却伪装完整
- 因「以后再说」放过错误处理章节
- 把开放问题藏在 prose 而无显式分类

## Common Mistakes

| 错误 | 修复 |
|---|---|
| 把组件接口的修改作为 AR 设计的一部分 | 停下回 `devflow-router` 升级 component-impact |
| 测试设计写成独立文件 | 重新作为 ar-design-draft.md 的章节 |
| 测试用例只覆盖 happy path | 补充边界 / 异常 / 嵌入式风险用例 |

## Verification

- [ ] `features/<id>/ar-design-draft.md` 已落盘
- [ ] 团队 AR 模板章节齐全，且无模板提示 / 示例业务内容 / 占位符残留
- [ ] AR 概述 / 动态行为 / 功能点分解 / 实现设计 / MDC 五场景 / 重构设计 / 测试设计 / 修订记录章节齐全
- [ ] Design Options 已包含候选方案、trade-off、推荐项和确认状态；或写明 Single obvious option 理由
- [ ] 功能点分解、接口描述、代码设计、流程图 / 时序图 / 类图内容可支撑 tasks 与 TDD
- [ ] 与组件设计一致性显式说明
- [ ] 测试设计章节存在且每个用例回指 requirement row（含嵌入式风险覆盖矩阵）
- [ ] traceability.md 已补充 AR Design + Test Design Case
- [ ] progress.md canonical 同步，下一步 `devflow-ar-design-review`
- [ ] 父会话准备派发独立 reviewer subagent

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

### AR Design Assets

Use features/<id>/ar-design-draft.md for the process draft and docs/ar-designs/AR<id>-<slug>.md for the promoted long-term AR design.

### AR Design Minimum Content

Cover AR id, SR link, owning component, goal/scope, affected files/modules/interfaces, data/control flow, C/C++ implementation strategy, consistency with component design, embedded test design, risks, and open questions.

DevFlow does not maintain a separate test-design.md; test design is an AR design section.
## Supporting References

| 文件 | 用途 |
|---|---|
| `references/test-design-section-contract.md` | 测试设计章节最小契约 |
| `references/devflow-ar-design-template.md` | 团队 AR 设计模板（待团队补齐） |
