---
name: devflow-problem-fix
description: 当 DTS、紧急缺陷或已上线问题在任何代码修改前需要复现、根因分析和最小安全修复边界时使用；也用于 devflow-router 已选择 hotfix 档位，或 AR 路线中遇到需要先按问题分析处理的回归。不用于编写修复代码、AR 设计、组件设计变更，或阶段和路由混乱。
---

# devflow 问题修改 / Hotfix 分析

在不放弃验证纪律的前提下，处理 DTS / 紧急缺陷：复现路径、根因收敛、最小安全修复边界、决定回流节点。

本 skill **不**写生产代码（那是 `devflow-tdd-implementation` 的职责），**不**修改组件实现设计（必要时回 `devflow-component-design`），**不**替开发负责人决定优先级，**不**绕过 review / gate。紧急 ≠ 跳过。

## 适用场景

适用：

- DTS / 缺陷单 / 紧急问题需要修复前的复现 + 根因 + 修复边界
- `devflow-router` 已选择 `hotfix` profile
- 用户说"先把这个问题分析清楚再改"

不适用 → 改用：

- 写修复代码 → `devflow-tdd-implementation`
- 需求变更 / 范围调整 → 回 `devflow-specify`（或 router）
- 修复需要 AR 实现设计 → `devflow-ar-design`
- 修复触及组件边界 → `devflow-component-design`
- 阶段不清 / 证据冲突 → `devflow-router`

## 硬性门禁

- 必须有复现路径（或显式无法复现说明）才能 handoff 给 `devflow-tdd-implementation`
- 必须确认根因 + 最小安全修复边界
- 不得把 hotfix 当作跳过 `devflow-test-checker` / `devflow-code-review` / `devflow-completion-gate` 的理由
- 修复边界扩散（跨多模块 / 改公共接口 / 改用户可见行为 / 改数据契约）→ `interactive` 模式下必须先确认边界，`auto` 模式下回 router
- 不替模块架构师决定接口 / 数据契约改动
- 修复若实质上是「新增能力」或「需求变更」→ 不走 hotfix，回 `devflow-specify` 或 router
- 不写生产代码

## 对象契约

- Primary Object: problem-fix package（reproduction + root cause + fix boundary + 回流节点）
- Frontend Input Object: DTS / 缺陷单原文、用户描述、相关代码 / 日志、`docs/component-design.md`、`docs/ar-designs/`、`AGENTS.md`、当前 `features/<id>/progress.md`（若已存在）
- Backend Output Object:
  - `features/DTS<id>-<slug>/reproduction.md`
  - `features/DTS<id>-<slug>/root-cause.md`
  - `features/DTS<id>-<slug>/fix-design.md`
  - `features/DTS<id>-<slug>/progress.md` canonical 同步
  - `features/DTS<id>-<slug>/README.md` 状态同步
- Object Transformation: 把缺陷输入转成可被 `devflow-tdd-implementation` 消费的最小修复包
- Object Boundaries: 不写生产代码 / 不修改 AR 设计或组件设计 / 不顺手优化
- Object Invariants: DTS ID / 所属组件 / 复现路径在 handoff 后保持稳定

## 方法原则

- **Root Cause Analysis (RCA / 5 Whys)**: 从表象逐层追问到根因；不只修表象
- **Minimum Safe Fix Boundary**: 显式定义改什么 / 不改什么 / 影响什么
- **Reproduce First**: 必须先复现或显式无法复现
- **Contract Sanity Check**: 校对当前行为是否真的违反既有 spec / 设计 / API 契约
- **Blameless Post-Mortem Mindset**: 关注机制 / 系统性原因，不归咎个人
- **Embedded Risk Awareness**: 内存 / 并发 / 实时性 / 资源 / 错误处理在根因分析中作为一等输入

## 工作流

### 1. 建立证据基线

按 Read-On-Presence + Contract Sanity Check 读取缺陷报告原文、用户描述、相关代码 / 日志、`docs/component-design.md`、`docs/ar-designs/`、相关 review / verification 记录、`features/<id>/progress.md`（若存在）。

如果缺陷描述指向「需求变更」/「新增能力」（既有 spec / 设计未要求当前行为）→ 不走 hotfix，阻塞回 `devflow-specify` 或 `devflow-router`。

### 2. 初始化或对齐 work item 目录


### 3. 构建复现路径

按 Reproduce First 写 `features/DTS<id>-<slug>/reproduction.md`，至少含期望行为（指向既有 spec / 设计 / API 契约的具体锚点）、实际行为、复现步骤（环境、版本、配置、命令）、失败证据（日志 / 退出码 / stack trace）、复现稳定性（每次必现 / 偶现 / 仅特定环境）。无法复现 → 显式标 `unable-to-reproduce`，写明已尝试的环境与下一步建议；不得隐瞒。

### 4. 根因分析

按 Root Cause Analysis (5 Whys) + Embedded Risk Awareness 写 `features/DTS<id>-<slug>/root-cause.md`，至少含 5 Whys 链、根因维度（编码错误 / 设计缺陷 / 接口契约不一致 / 内存 / 并发 / 实时性 / 配置 / ABI / ...）、信心程度（`demonstrated` / `probable`）、横向影响（是否在其他相似路径上也存在）。信心仅 `probable` 且修复边界扩散 → 不能 handoff，回步骤 3 补复现或上抛模块架构师。

### 5. 最小安全修复边界

按 Minimum Safe Fix Boundary 写 `features/DTS<id>-<slug>/fix-design.md`，至少含改什么（文件 / 函数 / 配置）、不改什么（显式列出避免顺手扩散）、影响什么（用户可见行为 / 公共接口 / 数据契约 / 跨组件）、是否需要补 AR 实现设计或修订组件实现设计、测试设计要点（复现脚本作为 RED 用例 + 额外边界 / 异常用例）、嵌入式风险审计（内存 / 并发 / 实时性 / 资源 / 错误处理 / ABI 各维度）。

### 5A. 修复边界确认点

出现以下任一信号时，**不要直接 handoff 实现**：

- 修复扩散到多模块 / 多行为
- 修复改用户可见行为 / 公共接口 / 数据契约
- 根因仅 `probable`

处理：

- `interactive`：先展示「建议修什么 / 明确不修什么 / 为什么这是最小边界」，等真人确认
- `auto`：边界仍清晰且证据充分时继续；否则 `reroute_via_router=true` 回 `devflow-router`

### 6. 决定回流节点

按 Route Decision：

| 条件 | 回流节点 |
|---|---|
| 复现 + 根因 + 修复边界清晰、不触组件 / 不需要正式 AR 设计 | `devflow-tdd-implementation` |
| 修复需要正式 AR 实现设计 | `devflow-ar-design` |
| 修复触及组件边界 | `devflow-component-design`（先升 component-impact） |
| 实际是需求变更 | `devflow-specify` |
| 证据不足以确认根因 | `devflow-router`（`reroute_via_router=true`） |

### 7. 同步 progress 与 traceability

按 Canonical Field Sync：

- `features/DTS<id>-<slug>/traceability.md`：补 IR / SR / AR（若涉及功能需求）/ 设计 / 代码 / 测试占位
- `features/DTS<id>-<slug>/progress.md`：`Current Stage = devflow-problem-fix`、`Pending Reviews And Gates = test-check, code-review, completion-gate`、`Next Action Or Recommended Skill = <步骤 6 回流节点>`

## 输出契约

- `features/DTS<id>-<slug>/reproduction.md`、`root-cause.md`、`fix-design.md`
- `features/DTS<id>-<slug>/progress.md` canonical 同步
- `features/DTS<id>-<slug>/README.md` 状态同步
- handoff 摘要：

  ```yaml
  current_node: devflow-problem-fix
  work_item_id: DTS<id>
  owning_component: <component>
  result:
    reproduction: stable | flaky | unable-to-reproduce
    root_cause_confidence: demonstrated | probable
    fix_boundary: minimal | confirmed-narrow | escalated
  artifact_paths:
    - features/DTS<id>-<slug>/reproduction.md
    - features/DTS<id>-<slug>/root-cause.md
    - features/DTS<id>-<slug>/fix-design.md
  `next_action_or_recommended_skill`: <步骤 7 回流节点>
  reroute_via_router: true | false
  ```

## 风险信号

- 不复现就给修复方案
- 顺手「优化」其他代码
- 把 hotfix 当借口跳过 review / gate
- 根因仅 `probable` 却直接 handoff 实现
- 修复边界已扩散却不暂停确认
- 把需求变更包装成 hotfix（绕过 spec 流程）
- 在 fix-design.md 中写完整生产代码
- DTS 触及组件边界仍指向 `devflow-tdd-implementation`

## 常见错误

| 错误 | 修复 |
|---|---|
| 复现失败就跳过复现节直接给方案 | 标 `unable-to-reproduce`，回 router 决定是否上抛 |
| 修复扩散到多模块仍指向 tdd | 触发步骤 6 边界确认点；超过则回 router 升 component-impact |
| DTS 实际是新增能力 | 阻塞，回 `devflow-specify` 或 router |

## 验证清单

- [ ] `features/DTS<id>-<slug>/` 目录骨架已建立
- [ ] reproduction.md 已落盘（含期望 / 实际 / 步骤 / 证据 / 稳定性）
- [ ] root-cause.md 已落盘（含 5 Whys / 维度 / 信心 / 横向影响）
- [ ] fix-design.md 已落盘（含改什么 / 不改什么 / 影响什么 / 嵌入式风险）
- [ ] 修复边界扩散信号已显式处理（确认或回 router）
- [ ] traceability.md 已补 DTS 相关行
- [ ] progress.md canonical 同步，下一步唯一指向回流节点
- [ ] 未写生产代码

## 本地 Hotfix 路由说明

当 `devflow-router` 为 DTS / urgent production defects 选择 hotfix，或证据显示安全实现前需要先做复现与根因分析时，进入本 skill。若问题实质是新需求或范围变更，路由到 `devflow-specify` 或 `devflow-router`。

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

### DTS / Hotfix 路径

Default DTS directory is features/DTS<id>-<slug>/. Create or update README.md, progress.md, reproduction.md, root-cause.md, and fix-design.md as needed.

### Evidence 路径

把 reproduction evidence、logs、unit/integration evidence、static-analysis output 和 build output 存到 work item evidence 目录下。Root cause 必须由 fresh evidence 支撑，不能靠猜测。
## 支撑参考

| 文件 | 用途 |
|---|---|
| `references/repro-and-rca-templates.md` | reproduction.md / root-cause.md / fix-design.md 模板 |
| `references/devflow-work-item-readme-template.md` | DTS work item README 模板 |
| `references/devflow-progress-template.md` | progress.md 模板 |
