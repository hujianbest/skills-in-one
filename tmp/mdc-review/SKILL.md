---
name: mdc-review
description: 统一评审技能，支持规格评审(spec)、架构设计评审(arch-design)、AR设计评审(ar-design)、任务计划评审(tasks)四种 review_type。参数化执行评审、写记录、返回结构化摘要。适用于各类评审草稿已完成需正式 review verdict、reviewer subagent 被派发的场景。不适用写/修草稿（→ mdc-specify/mdc-arch-design/mdc-ar-design/mdc-tasks）、阶段不清（→ using-mdc-workflow）。
---

# MDC Review

统一评审技能，通过 `review_type` 参数区分规格评审、架构设计评审、AR设计评审、任务计划评审。核心职责：防止过早推进下游节点，确保上游工件质量达标。

## When to Use

适用：
- 规格草稿已完成，需正式 review verdict（`review_type=spec`）
- 架构设计草稿已完成，需正式 review verdict（`review_type=arch-design`）
- AR设计草稿已完成，需正式 review verdict（`review_type=ar-design`）
- 任务计划草稿已完成，需正式 review verdict（`review_type=tasks`）
- reviewer subagent 被派发执行评审

不适用：缺草稿或只需继续写 → 对应 authoring skill；阶段不清 → `using-mdc-workflow`。

## Hard Gates

- 评审通过并完成 approval step 前，不得进入下游节点
- reviewer 不代替父会话完成 approval step
- reviewer 不得为让工件"看起来能过"而发明业务事实

## Workflow

### 1. 建立证据基线

读取并固定：当前工件、上游工件（spec/arch-design/ar-design/tasks 按类型）、`AGENTS.md` 约定、`features/<active>/progress.md`。

### 2. Precheck

检查：是否存在稳定可定位的草稿、route/stage/profile 是否已明确、上游证据是否一致。

- route/stage/证据冲突 → 写最小 blocked precheck record，`reroute_via_router=true`
- route 明确但缺稳定草稿 → 写最小 blocked record，下一步对应 authoring skill
- precheck 通过 → 继续正式评审

### 3. 按 review_type 执行正式评审

#### review_type=spec：规格评审

详细规则：`references/spec-review-rubric.md`

- Group Q: Quality Attributes — 核心需求可回指来源？模糊词已量化？验收标准可判断？
- Group A: Anti-Patterns — 模糊词、复合需求、设计泄漏、无主体被动表达
- Group C: Completeness And Contract — 核心 FR/NFR 具备 ID/Statement/Acceptance/Priority/Source？范围内外闭合？
- Group G: Granularity And Scope-Fit — oversized requirements？当前轮和后续增量混写？

#### review_type=arch-design：架构设计评审

- 8 维度评分（0-10）：需求覆盖与追溯、架构一致性、决策质量、约束 NFR 适配、接口与组件定义、测试准备度、实现设计完整性、文档合规性
- 任一关键维度（AD1-AD5）< 6 不得通过，重要维度（AD6-AD8）< 6 需修改
- **重点检查**：component-design-doc 中每个功能点的每个场景必须有 PlantUML 时序图（细化到软件单元/类的方法调用，非组件级粗交互）；各章节内容必须足以支撑后续各 AR 的实现设计
- 详细清单：`references/arch-design-review-checklist.md`

#### review_type=ar-design：AR设计评审

- 9 维度评分（0-10）：需求覆盖与追溯、功能点完备性、实现设计充分性、接口契约清晰度、MDC场景覆盖、异常流程完备性、测试设计可执行性、代码设计可落地性、基线一致性
- 关键维度（AR1-AR4, AR9）< 6 阻塞，重要维度（AR5-AR8）< 6 需修改
- **基线一致性检查**：若 component-design-doc 存在，检查 AR 是否正确引用基线、功能 ID 对齐、接口变更为增量式；若基线不存在但代码存在，检查 AR 是否与现有代码结构一致；无基线且无代码 → 红旗，应回退 mdc-arch-design
- 详细清单：`references/ar-design-review-checklist.md`

#### review_type=tasks：任务计划评审

- 6 维度评分（0-10）：可执行性、任务合同完整性、验证与测试种子、依赖/顺序、追溯覆盖、Router 重选就绪度
- 任一关键维度 < 6 不得通过
- INVEST Validation：每个任务 Independent/Negotiable/Valuable/Estimable/Small/Testable
- 详细清单：`references/tasks-review-checklist.md`

### 4. Finding 分类

每条 finding 带 `severity`（critical/important/minor）、`classification`（USER-INPUT/LLM-FIXABLE）、`rule_id`。

### 5. 形成 verdict 与下一步

| review_type | 条件 | verdict | 下一步 |
|---|---|---|---|
| spec | 范围清晰、核心需求可验收、无阻塞 USER-INPUT | `通过` | 规格真人确认 |
| spec | 有用但不完整，findings 可定向修订 | `需修改` | `mdc-specify` |
| spec | 过于模糊/核心范围未定 | `阻塞` | `mdc-specify` |
| arch-design | 可追溯规格、新增组件定义清晰、接口足以支撑组件设计 | `通过` | 架构设计真人确认 |
| arch-design | 架构可用但有缺口 | `需修改` | `mdc-arch-design` |
| arch-design | 设计无法支撑规格 | `阻塞` | `mdc-arch-design` |
| ar-design | 功能点完备、实现设计充分、接口清晰、无阻塞 USER-INPUT | `通过` | AR设计真人确认 |
| ar-design | AR可用但有缺口（关键维度>=6，重要维度<6） | `需修改` | `mdc-ar-design` |
| ar-design | 核心功能遗漏/实现思路缺失/存在架构级决策 | `阻塞` | `mdc-ar-design` |
| tasks | 可执行、可验证、排序正确、忠实覆盖 | `通过` | 任务真人确认 |
| tasks | 有用但不完整 | `需修改` | `mdc-tasks` |
| tasks | 过于粗略/依赖关系错误 | `阻塞` | `mdc-tasks` |
| any | route/stage/证据冲突 | `阻塞`(workflow) | `using-mdc-workflow` |

### 6. 写 review 记录

按 `references/review-record-template.md` 的结构写记录，保存到：
- spec: `features/<active>/reviews/spec-review-YYYY-MM-DD.md`
- arch-design: `features/<active>/reviews/arch-design-review-YYYY-MM-DD.md`
- ar-design: `features/<active>/reviews/ar-design-review-YYYY-MM-DD.md`
- tasks: `features/<active>/reviews/tasks-review-YYYY-MM-DD.md`

交互约束：
- 父会话先展示 1-2 句 plain-language 结论，再只提 USER-INPUT 问题
- LLM-FIXABLE 问题不转嫁给用户
- 不整段粘贴 rubric/JSON/全量 findings 给用户

## Reference Guide

| 文件 | 用途 |
|---|---|
| `references/spec-review-rubric.md` | 规格评审 rubric（Q/A/C/G 四组） |
| `references/arch-design-review-checklist.md` | 架构设计评审清单 |
| `references/ar-design-review-checklist.md` | AR设计评审清单 |
| `references/tasks-review-checklist.md` | 任务计划评审清单 |
| `references/review-record-template.md` | 记录结构、JSON 格式、返回规则 |

## Red Flags

- 把评审变成重新写/设计
- 因为"后面再想"就直接批准
- findings 没有 USER-INPUT/LLM-FIXABLE 分类
- 通过后直接进入下游节点（跳过 approval step）
- 不读上游工件就审

## Verification

- [ ] review record 已落盘
- [ ] 给出明确结论、findings 和唯一下一步
- [ ] findings 标明 severity/classification/rule_id
- [ ] precheck blocked 时已写明 workflow blocker 和 reroute_via_router
- [ ] `通过` 时已明确要求进入对应真人确认
- [ ] 结构化摘要已回传父会话
