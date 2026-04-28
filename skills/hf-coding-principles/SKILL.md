---
name: hf-coding-principles
description: HF skill pack 的 always-on 指导性前置 skill。任何 HF 节点（含 using-hf-workflow / hf-workflow-router 与所有 leaf skill）启动前都必须先读它，把"先想再写、最简实现、外科式改动、目标驱动"这四条 LLM coding 行为准则注入当前节点的执行上下文。不进入 canonical workflow `Next Action Or Recommended Skill` vocabulary，不替代 router、authoring、review、gate 或 finalize 节点的本地职责。
---

# HF Coding Principles（Karpathy-Style Behavioral Preface）

HF skill family 的 **always-on preface**。它把 Andrej Karpathy 总结的 4 条 LLM coding 反常见错误准则，落成 HF 风格的"行为前置层"。

它**不是**一个 workflow 节点，**不进入** `Next Action Or Recommended Skill` 受控词表，**不替代** `using-hf-workflow` 的 family discovery 或 `hf-workflow-router` 的 runtime routing。它是所有 HF 节点都要在自己开工之前先读、并在执行过程中持续自检的 **行为基线**。

> 来源：基于 [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills) 中的 `CLAUDE.md`，按 HF 命名与方法论习惯重写并与 `using-hf-workflow` / `hf-workflow-router` / `hf-test-driven-dev` / `hf-code-review` 的现有边界对齐。

## When to Use

**总是 use（默认 always-on）**：

- 任何 HF 节点（public entry / router / authoring / review / gate / branch / finalize / bug-patterns 等）开始当前回合的工作之前，先把这 4 条准则加载到当前推理上下文，然后再继续目标 skill 的具体步骤。
- 用户说"继续 / 推进 / 开始做"、点名某个 `hf-*` skill、用 `/hf-*` 命令意图、或 router 派发下游节点时，目标 skill 的 kickoff 必须先经过本 skill 的"行为自检"。

**不适用**：

- 把它当成 canonical 节点写进 `Next Action Or Recommended Skill`、`Pending Reviews And Gates`、迁移表、或 reviewer subagent 的 `next_action_or_recommended_skill`。**绝对不允许**。
- 把它当成 review / gate / approval 节点替代品。它**不**产出 review 记录、不**产出** verdict、不**接管** approval。
- 用它来跳过 `hf-workflow-router` 对 profile / mode / route / stage 的 authoritative 判断。

## Hard Rules

- 本 skill 是 **preface**，不是 workflow 节点：不写 review / verification / approval / closeout 工件，不与 `hf-workflow-router` 竞争 routing 权威。
- 本 skill 不替代 `hf-test-driven-dev` 的 RED-GREEN evidence、不替代 `hf-code-review` 的 Fagan 检视、不替代 `hf-completion-gate` 的 DoD。
- 本 skill 任何条款与 `docs/principles/soul.md` 或 `AGENTS.md` 显式声明冲突时，以 soul / `AGENTS.md` 为准。
- 不允许把本 skill 写成 `Current Stage`、`Next Action Or Recommended Skill` 或迁移边的合法值。

## Methodology

| 方法 | 核心原则 | 来源 | 在 HF 中的落点 |
|------|----------|------|---------------|
| **Think Before Coding** | 不假设、不藏混乱、显式列出 trade-off | Karpathy / LLM coding pitfalls | `using-hf-workflow` 入口分流、`hf-specify` / `hf-design` authoring、`hf-test-driven-dev` 的 test design 阶段 |
| **Simplicity First (YAGNI)** | 解决问题的最小代码，不写未被要求的能力 | Karpathy / Beck YAGNI / Two Hats | `hf-specify`（MoSCoW）、`hf-design`（emergent vs upfront）、`hf-test-driven-dev` REFACTOR window |
| **Surgical Changes** | 只动应该动的，不顺手"改进"邻居代码 | Karpathy / Boy-Scout-Rule 的克制版 | `hf-test-driven-dev` Two Hats、`hf-code-review` 检视、`hf-increment` change impact |
| **Goal-Driven Execution** | 把任务转成可验证目标，循环到 verified | Karpathy / Goal-Directed Reasoning | `hf-test-driven-dev` 的 fresh RED/GREEN、`hf-completion-gate` 的 DoD evidence bundle |

## The Four Principles

### 1. Think Before Coding — 不假设，显式 trade-off

**别假设、别藏混乱、把 trade-off 摊开。**

- 实现前先把 **assumption** 显式说出来。不确定就停下来问。
- 出现多种合理解读时，列出来再请用户裁决；不要静默选一个。
- 看到更简单的做法，主动说出来；当应该 push back 的时候 push back。
- 哪里不清楚，先 stop、命名清楚是哪里不清楚、再问。

> 在 HF 中：这条对应 `using-hf-workflow` 步骤 4A 的"单事实分流检查点"、`hf-specify` 的 EARS / Socratic Elicitation、`hf-test-driven-dev` 的 test design preface（先写 test design，再开始 RED）。

### 2. Simplicity First — 最简实现，YAGNI 到底

**只写解决当前问题的最小代码。**

- 没被要求的功能不要加。
- 单次使用的代码不要为它发明抽象。
- 没人要求的 "灵活性 / 可配置性" 不要加。
- 不为不可能发生的场景写错误处理。
- 写到 200 行能压到 50 行就重写。

自检问题："一个资深工程师会不会觉得这是 over-engineered？" 如果是 → 简化。

> 在 HF 中：这条对应 `hf-specify` 的 MoSCoW、`hf-design` 的 emergent vs upfront patterns 治理（GoF 模式刻意 emergent）、`hf-test-driven-dev` 的 GREEN 之后才允许 REFACTOR 的 Two Hats 顺序。

### 3. Surgical Changes — 外科式改动，只动该动的

**只动你必须动的；只清理你自己造成的脏。**

编辑既有代码时：

- 不要"顺手改善"周边代码、注释、格式。
- 不要重构没坏的东西。
- 沿用既有风格，即使你个人会换种写法。
- 看到无关 dead code → **指出**，不要顺手删。

你的修改产生孤儿（unused import / 变量 / 函数）时：

- 删除**因你的本次修改才变得无用**的东西。
- 不要顺手删既有 dead code，除非用户明确要求。

测试标准：每一行被修改的代码都能直接溯源到用户的本次请求。

> 在 HF 中：这条对应 `hf-test-driven-dev` 的 Two Hats（GREEN 帽子下不重构）、Boy-Scout 克制版的 opportunistic refactoring boundary、`hf-code-review` 的 architectural smells / scope-creep 检视、`hf-increment` 的 change impact analysis。

### 4. Goal-Driven Execution — 目标驱动，循环到可验证

**先定义成功标准，再循环执行到 verified。**

把任务翻译成**可验证目标**：

- "加一个 validation" → "为非法输入写测试，再让它们通过"
- "修这个 bug" → "写一个能重现 bug 的测试，再让它通过"
- "重构 X" → "重构前后跑同一组测试都通过"

多步任务先给一个简短计划：

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

强成功标准让你能独立循环；弱标准（"让它能跑就行"）会逼你不停回来要澄清。

> 在 HF 中：这条对应 `hf-test-driven-dev` 的 fresh RED/GREEN evidence、`hf-regression-gate` 的 impact-based 评估、`hf-completion-gate` 的 Definition of Done + evidence bundle、reviewer return contract 中的 `key_findings` 必须有证据锚点。

## How To Use（在每个 HF 节点开工前）

进入任意 HF 节点的 kickoff 时，按下面这个最小自检流程跑一遍，再继续目标 skill 自己的步骤：

1. **Think 自检**：我对当前请求是否有未说出口的 assumption？是否存在多解？是否需要先问 1 个最小判别问题？
2. **Simplicity 自检**：当前节点准备产出的工件 / 代码，是否包含**未被规格 / 任务 / 用户当前请求显式要求**的能力？
3. **Surgical 自检**：本回合的 diff / 工件改动，是否每一处都能溯源到当前请求？是否准备顺手"改善"无关区域？
4. **Goal 自检**：当前节点的"完成"长什么样？是否有可验证的 check？多步执行是否准备先列计划再走？

自检结果：

- **clear case**：4 条都明显满足 → 不展开，直接进入目标 skill 的下一步。
- **single missing fact**：仅缺 1 个判别事实 → 在目标 skill 里用最小一问解决（与 `using-hf-workflow` 的 "单事实分流检查点" 对齐），不展开整轮 intake。
- **conflict / unclear**：存在 trade-off、范围漂移、或未说出口的 assumption → 不要硬做；按目标 skill 的回流规则处理（authoring 节点 → 显式列出 trade-off 给用户；implementation / gate → 回 router 或回上游）。

## Output Contract

本 skill **不**要求每次都生成可见输出。默认是"加载并自检后静默继续"。

只有当自检命中以下情况之一，目标 skill 才在自己的输出中**显式带一段 preface 自检结论**（建议放在目标 skill 输出的最前面，1-3 行）：

- 命中 single missing fact，正在用最小一问解决 → 写一行 `Coding Principles Note: [Think] 缺 1 个判别事实：……`
- 命中 simplicity 风险 → 写一行 `Coding Principles Note: [Simplicity] 已剔除非显式要求的 X / Y`
- 命中 surgical 风险（diff 中存在与本次请求无直接关联的改动）→ 写一行 `Coding Principles Note: [Surgical] 仅指出不动：<file/symbol>`
- 命中 goal 风险（任务无可验证 check）→ 写一行 `Coding Principles Note: [Goal] 已为本任务补齐 verify 条件：<check>`

不允许把这些 note 写成 review 结论，也不允许用它们替代 reviewer / gate verdict。

## 和其他 Skill 的区别

| Skill | 区别 |
|-------|------|
| `using-hf-workflow` | family discovery / 入口分流；本 skill 是它（以及所有 leaf skill）的 preface，不替代它做 direct vs route 决策 |
| `hf-workflow-router` | runtime routing / profile / mode / 恢复编排；本 skill 不接管 routing，不写 canonical handoff |
| `hf-specify` / `hf-design` / `hf-tasks` | 产出 spec / design / tasks 正文；本 skill 只把 4 条准则注入到它们的 authoring 行为里，不替它们完成工件 |
| `hf-test-driven-dev` | RED-GREEN-REFACTOR 实现；本 skill 强化它的 Two Hats 顺序与 surgical / simplicity 自检，不替代 fresh evidence |
| `hf-code-review` / `hf-test-review` / `hf-traceability-review` / `hf-design-review` / `hf-ui-review` | 独立 review 节点；本 skill 不出 verdict、不出 review 记录 |
| `hf-completion-gate` / `hf-regression-gate` | 门禁评判；本 skill 不替代 DoD / regression evidence |
| `hf-bug-patterns` | 经验固化；本 skill 不写 catalog，不替代 human-in-the-loop confirmation |

## Red Flags

- 把 `hf-coding-principles` 写进 `Next Action Or Recommended Skill`
- 把 `hf-coding-principles` 写进 `Current Stage` 或 `Pending Reviews And Gates`
- 用本 skill 的"Goal 自检"替代 `hf-completion-gate` 的 evidence bundle
- 用本 skill 的"Surgical 自检"替代 `hf-code-review` 的 Fagan 检视
- 用本 skill 的"Think 自检"替代 `hf-specify` 的 EARS / `hf-design` 的 ADR
- 在 router 已经决定 profile / mode 之后，再用 preface 自检反向覆盖 router
- 把它当成"先批准 / 默认通过"的捷径
- 看到 trade-off 但因为已经在 GREEN 帽子下就静默选了一个

## Verification

- [ ] 当前节点 kickoff 前已对 4 条原则各做一次自检
- [ ] 命中 single missing fact / simplicity / surgical / goal 风险时，已在目标 skill 输出中显式带一行 preface note
- [ ] 没有把 `hf-coding-principles` 写进任何 canonical workflow vocabulary
- [ ] 没有用本 skill 替代 review / gate / approval / finalize 的本地职责
- [ ] 与 `docs/principles/soul.md` / `AGENTS.md` 冲突时已让位

## Supporting References

| 文件 | 用途 |
|------|------|
| `skills/docs/hf-workflow-shared-conventions.md` | always-on preface 与 canonical schema 的边界 |
| `skills/docs/hf-workflow-entrypoints.md` | 入口策略；本 skill 是入口前的 preface，不替代入口判断 |
| `using-hf-workflow/SKILL.md` | family discovery 入口；其 kickoff 必须先经过本 skill |
| `hf-workflow-router/SKILL.md` | runtime routing 权威；其 routing 输出仍是唯一权威，本 skill 只补行为层基线 |
