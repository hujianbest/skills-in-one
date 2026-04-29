---
name: devflow-component-design-review
description: 当 devflow-component-design 产出的 component-design-draft.md 需要独立评审结论时使用，覆盖 SR 触发的分析子街区和 AR 触发的 component-impact 子街区；也用于派发评审子代理审查组件边界、SOA 接口、依赖、状态机、运行机制，或修订后重跑组件设计评审。不用于编写或修订组件设计、AR 代码层设计评审，或阶段和路由混乱。
---

# devflow 组件实现设计评审（覆盖 SR-分析 与 AR-实现 两条子街区）

独立评审 `features/<id>/component-design-draft.md`，判断它是否可由 `devflow-finalize` 同步到 `docs/component-design.md`，以及（仅 AR 实现子街区）是否可作为下游 `devflow-ar-design` 的稳定输入。

本 skill 不写设计 / 不替模块架构师拍板组件边界 / 不修改设计草稿。它只产出 verdict + findings + 唯一下一步。

## 适用场景

适用：

- `devflow-component-design` 已产出 component-design-draft.md，需正式 verdict
- reviewer subagent 被派发执行组件设计评审
- 用户明确要求「review 这份组件设计」

不适用 → 改用：

- 缺草稿或仅需继续写 → `devflow-component-design`
- AR 代码层设计评审 → `devflow-ar-design-review`
- 阶段不清 / 证据冲突 → `devflow-router`

## 硬性门禁

- AR 子街区中，组件设计通过本 review 之前不得进入 `devflow-ar-design`
- SR 子街区中，组件设计通过本 review 之前不得进入 `devflow-finalize`（analysis closeout）；通过后 SR 子街区**仍不得**进入 `devflow-ar-design`
- reviewer 不修改设计草稿
- reviewer 不替模块架构师拍板组件边界 / SOA 接口 / 跨组件协调
- reviewer 不返回多个候选下一步
- 模块架构师 sign-off 是 `通过` 的硬性 USER-INPUT 项；缺 sign-off 的 `通过` 必须标 `needs_human_confirmation=true`

## 对象契约

- Primary Object: component design finding set + verdict（组件设计发现项与结论）
- Frontend Input Object: `features/<id>/component-design-draft.md`、`features/<id>/requirement.md`、`features/<id>/traceability.md`、当前 `docs/component-design.md`（如存在；用于对比修订前后）；项目已启用可选子资产时一并读取 `docs/interfaces.md` / `docs/dependencies.md` / `docs/runtime-behavior.md`（未启用直接跳过、不阻塞）；`AGENTS.md` 团队模板覆盖
- Backend Output Object: `features/<id>/reviews/component-design-review.md` + 结构化 reviewer 返回摘要
- Object Transformation: 把组件设计草稿审查成发现项集合 + 唯一 verdict + 唯一下一步
- Object Boundaries: 不修改被评审工件 / 不顺手优化设计 / 不替团队角色拍板
- Object Invariants: verdict 必为 `通过` / `需修改` / `阻塞` 之一

## 方法原则

- **SOA Component Boundary Analysis**: 检查组件职责、接口、服务契约、依赖方向、跨组件影响
- **Clean Architecture Boundary Discipline**: 检查依赖方向稳定性、实现细节是否倒灌
- **Interface Segregation Check**: SOA 接口是否最小知识、是否聚合多个无关用途
- **Template Conformance Check**: 是否符合团队组件设计模板（含模板未补齐时的占位声明）
- **Embedded Risk Review**: 检查并发、实时性、资源生命周期、错误处理、ABI / API 兼容性
- **Cross-Component Impact Audit**: 跨组件影响是否被显式列出且与下游组件的协调路径明确

## 工作流

### 1. 建立证据基线

按 Evidence-Based + Read-On-Presence 读取 component-design-draft.md、requirement.md、traceability.md、当前 `docs/component-design.md`（若存在）；项目已启用的可选子资产 `docs/interfaces.md` / `docs/dependencies.md` / `docs/runtime-behavior.md` 也一并读取，未启用直接跳过、不阻塞；`AGENTS.md` 模板覆盖。

### 1.5 Precheck

- 缺设计草稿 → blocked-content，下一步 `devflow-component-design`
- route / stage / profile 冲突（如未升级 component-impact 却进入本节点） → blocked-workflow，`reroute_via_router=true`，下一步 `devflow-router`
- spec-review 未通过 → blocked-workflow，`reroute_via_router=true`
- 否则进入步骤 2

### 2. 多维评分

按 Structured Walkthrough 对 7 个维度（详见 `references/component-design-review-rubric.md`）做 0-10 评分；任一关键维度 < 6 不得 `通过`。

| 维度 | 关注 |
|---|---|
| CD1 Identity & Template Conformance | Owner、组件名、子系统、模板章节齐全（或显式标注占位） |
| CD2 Responsibility & Non-Responsibility | 职责 / 非职责清晰，未承接其他组件职责 |
| CD3 SOA Interface Quality | 接口名 / 参数 / 错误码 / 时序约束 / 兼容性完整 |
| CD4 Dependency & Direction | 依赖方向无环、初始化 / shutdown 顺序明确、版本约束清晰 |
| CD5 Data Model & State Machine | 数据 / 状态机覆盖核心生命周期、转换条件清晰 |
| CD6 Concurrency / Real-time / Resource / Error Handling | 中断上下文限制、锁策略、资源回收、错误处理清晰 |
| CD7 AR Design Constraints & Cross-Component Impact | 「对 AR 实现设计的约束」章节存在；跨组件影响显式列出 |

### 3. 正式 checklist 审查

按 Checklist-Based Review（详见 `references/component-design-review-rubric.md` Group CD1-CD7 子规则）逐项审查；每条 finding 带 `severity` / `classification`（USER-INPUT / LLM-FIXABLE / TEAM-EXPERT） / `rule_id` / `anchor` / 描述 / 建议修复。

### 4. 形成 verdict

按下表收敛唯一 verdict + 唯一下一步；`通过` 时下一步取决于本 work item 的 profile：

**SR work item（profile = `requirement-analysis`）**：

| 条件 | conclusion | `next_action_or_recommended_skill` | reroute_via_router | needs_human_confirmation |
|---|---|---|---|---|
| 7 维度均 ≥ 6、无 critical USER-INPUT、模块架构师可被请求 sign-off | `通过` | `devflow-finalize`（analysis closeout） | `false` | `true`（等模块架构师 sign-off） |
| findings 可 1-2 轮定向修订 | `需修改` | `devflow-component-design` | `false` | `false` |
| 组件边界 / SOA 接口严重不清 / 跨组件协调缺失 | `阻塞`（内容） | `devflow-component-design` | `false` | `false` |
| route / stage / profile / 上游证据冲突；或 SR 工件试图映射到 `devflow-ar-design` | `阻塞`（workflow） | `devflow-router` | `true` | `false` |

**AR work item（profile = `component-impact`）**：

| 条件 | conclusion | `next_action_or_recommended_skill` | reroute_via_router | needs_human_confirmation |
|---|---|---|---|---|
| 7 维度均 ≥ 6、无 critical USER-INPUT、模块架构师可被请求 sign-off | `通过` | `devflow-ar-design` | `false` | `true`（等模块架构师 sign-off） |
| findings 可 1-2 轮定向修订 | `需修改` | `devflow-component-design` | `false` | `false` |
| 组件边界 / SOA 接口严重不清 / 跨组件协调缺失 | `阻塞`（内容） | `devflow-component-design` | `false` | `false` |
| route / stage / profile / 上游证据冲突 | `阻塞`（workflow） | `devflow-router` | `true` | `false` |

### 5. 写 review 记录并回传


## 输出契约

- Review record：`features/<id>/reviews/component-design-review.md`
- 结构化 reviewer 返回摘要含 record_path、conclusion、key_findings、finding_breakdown、`next_action_or_recommended_skill`、needs_human_confirmation、reroute_via_router
- `通过` 时 needs_human_confirmation 默认 `true`（等模块架构师 sign-off），由父会话决定何时进入 `devflow-ar-design`

## 风险信号

- 顺手把 AR 设计建议写进 review record
- 因「先做着试试」放过 SOA 接口不完整
- 忽略依赖方向有环
- 因模板未补齐就给 `通过`
- 跨组件影响未列出却给 `通过`
- 因「实现简单」就放过状态机覆盖不全
- findings 无分类

## 常见错误

| 错误 | 修复 |
|---|---|
| 评审中「顺手」补设计章节 | reviewer 是 gate，不是 author，返回 finding 让 author 修 |
| 模块架构师未 sign-off 仍给 `通过` 且 `needs_human_confirmation=false` | 强制 `needs_human_confirmation=true` |
| 跨组件影响未审查 | 加 critical finding |

## 验证清单

- [ ] review record 已落盘
- [ ] precheck 结果显式记录
- [ ] 7 维度评分完整、findings 已分类
- [ ] verdict 唯一、下一步唯一、`reroute_via_router` 正确
- [ ] `通过` 时 `needs_human_confirmation=true` 等模块架构师 sign-off
- [ ] 结构化摘要已回传父会话
- [ ] 未顺手修改设计草稿

## 内嵌评审记录模板

除非 `AGENTS.md` 覆盖路径，否则把 review record 写到本 skill 预期路径。只保留与当前 review 类型相关的章节。

- Metadata：review type、work item type/id、owning component/subsystem、reviewer identity、date、record path。
- Inputs Consumed：primary artifact path + freshness anchor、commit/branch、supporting context paths、AGENTS.md/team standards used。
- Multi-Dimension Scoring：rubric dimensions、0-10 score，以及每个分数的 evidence；任一 critical dimension 低于阈值即不得通过。
- Findings：ID、severity、classification、rule_id、anchor/location、description、impact、suggested fix。
- Verdict：conclusion（pass / needs changes / blocked）、rationale、next_action_or_recommended_skill、reroute_via_router、needs_human_confirmation。
- Follow-up Actions：所需 rework 或 confirmation 的 owner 与 status。

## 评审者契约

本 review skill 由独立 reviewer 角色或 subagent 执行。reviewer 不得修改被评审产物、写代码、加测试或替团队做决策。

最小结构化返回：

```yaml
target_skill: <this skill name>
work_item_id: <id>
owning_component: <component or N/A>
record_path: <written review record>
conclusion: pass | needs_changes | blocked
verdict_rationale: <1-3 lines>
key_findings: []
finding_breakdown:
  critical: 0
  important: 0
  minor: 0
next_action_or_recommended_skill: <one canonical devflow node>
needs_human_confirmation: true | false
reroute_via_router: true | false
```

规则：只返回一个 `next_action_or_recommended_skill`；workflow conflict 路由到 `devflow-router` 且 `reroute_via_router=true`；通过结论不能包含 critical findings。

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

### 组件设计评审记录

除非 `AGENTS.md` 覆盖路径，否则写入 `features/<id>/reviews/component-design-review.md`。

### Review 边界

评审组件职责、SOA 接口、依赖、状态机、运行时行为、可选长期资产和角色归属。不要在 review skill 内修订设计。
## 支撑参考

| 文件 | 用途 |
|---|---|
| `references/component-design-review-rubric.md` | 7 维度 rubric + rule IDs |
