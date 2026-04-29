---
name: devflow-spec-review
description: Use when a requirement.md draft from devflow-specify is ready for an independent verdict (covering both the requirement-analysis sub-stream for SR work items and the implementation sub-stream for AR / DTS / CHANGE work items), when a reviewer subagent is dispatched to evaluate the spec for clarity / traceability / designability, or when spec-review needs to be re-run after the author revised in response to earlier findings. Not for writing or revising the spec itself (→ devflow-specify), not for component or AR design review (→ devflow-component-design-review / devflow-ar-design-review), not for stage / route confusion (→ devflow-router).
---

# devflow 需求规格评审（覆盖 SR-分析 与 AR-实现 两条子街区）

独立评审 `features/<id>/requirement.md`：

- **SR work item**（profile = `requirement-analysis`）→ 判断它是否可作为 `devflow-component-design`（仅当 SR 触发组件设计修订）或直接 `devflow-finalize`（analysis closeout）的稳定输入；同时把 AR Breakdown Candidates 推到可被需求负责人决策的程度
- **AR / DTS / CHANGE work item**（实现 profile）→ 判断它是否可作为 `devflow-component-design`（component-impact）或 `devflow-ar-design`（standard / lightweight）的稳定输入

本 skill 不写规格、不替需求负责人补业务事实、不替模块架构师决定组件归属、不替开发负责人决定候选 AR 的优先级。它只对规格对象给出 verdict + findings，并把唯一下一步交回父会话。

## When to Use

适用：

- `devflow-specify` 已产出 requirement.md 草稿（SR 或 AR / DTS / CHANGE），需正式 verdict
- reviewer subagent 被派发执行 spec 评审
- 用户明确要求「review 这份规格 / 评审需求」

不适用 → 改用：

- 缺规格或仅需继续写 → `devflow-specify`
- 阶段不清 / 证据冲突 → `devflow-router`
- 已有批准规格、需要做组件 / AR 设计评审 → `devflow-component-design-review` / `devflow-ar-design-review`

## Hard Gates

- 规格通过本 review 之前，不得进入 `devflow-component-design` 或 `devflow-ar-design`
- reviewer 不修改 requirement.md
- reviewer 不替需求负责人 / 模块架构师补业务事实、优先级、阈值
- reviewer 不返回多个候选下一步
- 工件不足以判定 stage / route → `reroute_via_router=true`，回 `devflow-router`

## Object Contract

- Primary Object: spec finding set + verdict
- Frontend Input Object: `features/<id>/requirement.md`、`features/<id>/traceability.md`、`features/<id>/progress.md`、组件仓库 `docs/component-design.md`（如存在）、IR / SR / AR 上游锚点
- Backend Output Object: `features/<id>/reviews/spec-review.md` + 结构化 reviewer 返回摘要
- Object Transformation: 把规格对象审查成发现项集合 + 唯一 verdict + 唯一下一步
- Object Boundaries: 不修改被评审工件 / 不顺手做设计 / 不替团队角色拍板
- Object Invariants: verdict 必为 `通过` / `需修改` / `阻塞` 之一，下一步必为 canonical devflow-* 节点名

## Methodology

- **Structured Walkthrough (Fagan Inspection, adapted)**：按 rubric 维度评分，量化判断；不做自由阅读式评审
- **Checklist-Based Review**：使用结构化检查清单覆盖 6 类质量维度
- **Separation Of Author / Reviewer**：reviewer 与 author 必须不同角色或 subagent
- **Evidence-Based Verdict**：每条 finding 必须锚定 requirement.md 的具体行 / 章节
- **Team Role Discipline**：业务事实 / 优先级 / 验收阈值缺失时分类为 `USER-INPUT`，由父会话上抛需求负责人

## Workflow

### 1. 建立证据基线

按 Evidence-Based + Read-On-Presence 读取 `features/<id>/requirement.md`、`features/<id>/traceability.md`、`features/<id>/progress.md`、`docs/component-design.md`（若存在）、`AGENTS.md` 模板覆盖。不依赖会话记忆判断「已批准」或「规格已经讲清楚」。

### 1.5 Precheck

判断能否合法进入 review：

- 缺规格 / 缺 traceability → 写最小 blocked record，下一步 `devflow-specify`
- route / stage / profile 冲突 → 写最小 blocked record，`reroute_via_router=true`，下一步 `devflow-router`
- 否则进入步骤 2

### 2. 多维评分与挑战式审查

按 Structured Walkthrough 对维度做 0-10 评分；任一关键维度 < 6 不得 `通过`。维度按 work item 类型有所不同（详见 `references/spec-review-rubric.md`）。

通用维度（所有 work item）：

| 维度 | 关注 |
|---|---|
| S1 Identity & Traceability | Work Item Type / ID、所属组件 / 子系统唯一、上游单据锚点齐全 |
| S2 Scope & Non-Scope Clarity | 范围与非范围显式且不冲突 |
| S3 Requirement Row Quality | 核心 row 含 ID / Statement / Acceptance / Source；Component Impact / Affected Components 按类型必填 |
| S4 Embedded NFR Quality | 实时性 / 内存 / 并发 / 资源 / 错误处理 NFR 含可判定阈值 |
| S6 Open Questions Closure | 阻塞 / 非阻塞分类、阻塞项已闭合或显式 USER-INPUT |

按 work item 类型的额外维度：

| Work Item Type | 额外维度 | 关注 |
|---|---|---|
| AR / DTS / CHANGE | S5 Component Impact Assessment + Interface Contract Candidates | 是否影响组件接口 / 依赖 / 状态机已显式判断；涉及接口时是否给出可供设计消费的语义级接口候选契约 |
| SR | S5-SR Subsystem Scope & Affected Components | 子系统范围与受影响组件清单完整且与 row 表交叉一致 |
| SR | S7-SR AR Breakdown Candidates | 候选 AR 拆分清单存在；每条候选含 Scope / Owning Component（唯一）/ Covers SR Rows / Hand-off Owner；如 SR 显式声明「无可拆分 AR」也明确说明并由需求负责人确认 |
| SR | S8-SR Component Design Impact | 若本 SR 触发 `devflow-component-design`，已显式列出受影响组件设计章节与修订方向 |

### 3. 正式 checklist 审查

按 Checklist-Based Review 跑 4 组规则（Group Q / A / C / G，详见 `references/spec-review-rubric.md`）。每条 finding 必须带 `severity`（critical / important / minor）、`classification`（USER-INPUT / LLM-FIXABLE / TEAM-EXPERT）、`rule_id`、`anchor`、描述、建议修复。

### 4. 形成 verdict

按下表收敛唯一 verdict + 唯一下一步；不能映射下表任一行 → verdict 未收敛，回步骤 2 / 3。

按 work item 类型：

**SR work item（profile = `requirement-analysis`）**：

| 条件 | conclusion | `next_action_or_recommended_skill` | reroute_via_router |
|---|---|---|---|
| 范围清晰、Affected Components / AR Breakdown Candidates 章节充分、Component Design Impact 显式判断为「需修订组件设计」、无阻塞 USER-INPUT | `通过` | `devflow-component-design` | `false` |
| 范围清晰、Affected Components / AR Breakdown Candidates 章节充分、Component Design Impact 显式判断为「无需修订」、无阻塞 USER-INPUT | `通过` | `devflow-finalize`（analysis closeout） | `false` |
| 有用但不完整，findings 可 1-2 轮定向修订 | `需修改` | `devflow-specify` | `false` |
| 子系统范围 / 候选 AR 拆分严重不清，findings 无法定向回修 | `阻塞`（内容） | `devflow-specify` | `false` |
| route / stage / profile / 上游证据冲突；或 SR 工件试图映射到实现节点 | `阻塞`（workflow） | `devflow-router` | `true` |

**AR / DTS / CHANGE work item（实现 profile）**：

| 条件 | conclusion | `next_action_or_recommended_skill` | reroute_via_router |
|---|---|---|---|
| 范围清晰、核心 rows 含 Acceptance、Component Impact 已判断、涉及接口时 Interface Contract Candidates 完整、无阻塞 USER-INPUT、足以喂下一节点 | `通过` | `devflow-component-design`（Component Impact ≠ none）/ `devflow-ar-design`（其余） | `false` |
| 有用但不完整，findings 可 1-2 轮定向修订 | `需修改` | `devflow-specify` | `false` |
| 范围 / 验收 / 组件归属严重不清，findings 无法定向回修 | `阻塞`（内容） | `devflow-specify` | `false` |
| route / stage / profile / 上游证据冲突 | `阻塞`（workflow） | `devflow-router` | `true` |

### 5. 写 review 记录并回传


## Output Contract

- Review record：`features/<id>/reviews/spec-review.md`（团队 `AGENTS.md` 覆盖路径优先）
- 结构化 reviewer 返回摘要含：
  - `record_path`
  - `conclusion`：`通过` / `需修改` / `阻塞`
  - `key_findings`：每条含 severity / classification / rule_id / anchor / 描述 / 建议修复
  - `finding_breakdown`：critical / important / minor 计数
  - `next_action_or_recommended_skill`：唯一 canonical devflow-* 节点
  - `needs_human_confirmation`：`通过` 时通常 `true`（需求负责人确认）
  - `reroute_via_router`：`true` 仅在 workflow blocker 时

## Red Flags

- 把 spec review 当成重新设计
- 因「以后再想」就放过缺失 Acceptance
- 忽略 IR / SR / AR 追溯断裂
- findings 无 USER-INPUT / LLM-FIXABLE / TEAM-EXPERT 分类
- 把 LLM-FIXABLE 问题抛给用户
- 通过后顺手开始写 AR 设计（reviewer 是 gate，不是 author）

## Common Mistakes

| 错误 | 修复 |
|---|---|
| 缺业务阈值仍给 `通过` | 标 `USER-INPUT` 阻塞，回需求负责人 |
| Component Impact 没判断 → 给 `通过` | 标 critical finding，verdict 至少 `需修改` |
| 影响接口但缺 Interface Contract Candidates | 标 critical finding，verdict 至少 `需修改` |
| 多个候选下一步 | 收敛为唯一 canonical 值；无法收敛即 `reroute_via_router=true` |

## Verification

- [ ] review record 已落盘
- [ ] precheck 结果显式记录
- [ ] 6 维度评分完整、findings 已分类
- [ ] verdict 唯一、下一步唯一、`reroute_via_router` 正确
- [ ] USER-INPUT 阻塞项显式列出
- [ ] 结构化摘要已回传父会话
- [ ] 未顺手修改 requirement.md

## Embedded Review Record Template

Write the review record to this skill's expected path unless AGENTS.md overrides it. Include only sections relevant to this review type.

- Metadata: review type, work item type/id, owning component/subsystem, reviewer identity, date, record path.
- Inputs Consumed: primary artifact path + freshness anchor, commit/branch, supporting context paths, AGENTS.md/team standards used.
- Multi-Dimension Scoring: rubric dimensions, 0-10 score, and evidence for each score; any critical dimension below threshold prevents pass.
- Findings: ID, severity, classification, rule_id, anchor/location, description, impact, suggested fix.
- Verdict: conclusion (pass / needs changes / blocked), rationale, next_action_or_recommended_skill, reroute_via_router, needs_human_confirmation.
- Follow-up Actions: owner and status for any required rework or confirmation.

## Reviewer Contract

This review skill is executed by an independent reviewer role or subagent. The reviewer must not modify the reviewed artifact, write code, add tests, or make team decisions.

Minimum structured return:

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

Rules: return exactly one next_action_or_recommended_skill; workflow conflicts route to devflow-router with reroute_via_router=true; a passing verdict cannot include critical findings.

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

### Review Record

Write the spec review record under features/<id>/reviews/spec-review.md unless AGENTS.md overrides it.

### Spec Review Inputs

Use requirement.md required sections, Requirement Rows, Component Impact Assessment, Interface Contract Candidates when interfaces are affected, Embedded NFR, open questions, and trace links. A passing review must map to one next node only.
## Supporting References

| 文件 | 用途 |
|---|---|
| `references/spec-review-rubric.md` | 6 维度 rubric + Group Q/A/C/G rule IDs |
