---
name: mdc-specify
description: 澄清需求并起草可评审规格。适用于尚无已批准规格、现有规格仍是草稿或被 `mdc-review(review_type=spec)` 退回的场景。若阶段不清，先回到 `using-mdc-workflow`。
---

# MDC 需求澄清

创建一份定义"做什么、为什么做、做到什么程度算完成"的需求规格说明，准备到可交给 `mdc-review(review_type=spec)` 的状态。

本 skill 不给设计方案，只把需求收敛成后续节点不需要猜测推进的规格草稿。

## When to Use

适用：
- 尚无已批准需求规格
- 现有规格仍为草稿或待收敛
- `mdc-review(review_type=spec)` 返回 `需修改` 或 `阻塞`，需按 findings 修订
- 用户需要先澄清范围、验收标准、边界、约束、非目标

不适用 → 改用：
- 已有批准规格，问题在 HOW 层 → `mdc-ar-design`
- 规格和设计都已批准，需要任务计划 → `mdc-tasks`
- 热修复/增量变更/阶段不清 → `using-mdc-workflow`

Direct invoke 信号："先把需求梳理清楚"、"帮我写规格"、"规格被 review 打回了"、"先别做设计"。

## Hard Gates

- 规格通过评审前，不得开始设计、任务拆解或实现
- `mdc-review(review_type=spec)` 给出"通过"前，不发起 approval step
- 不得为缺失的业务规则、优先级或来源锚点自行编造
- 不得把延后需求只藏在 prose 里而不显式标成延后项
- 若请求未经过入口判断，先回到 `using-mdc-workflow`

## Workflow

### 1. 了解最少必要上下文

只读完成规格澄清所需的最少材料：用户请求、相关项目文档、现有草稿/评审记录、`AGENTS.md` 路径映射、`features/<active>/progress.md`。

先提炼：已确认事实、初始目标与成功标准、约束与依赖、未知项与矛盾点。

### 2. 收敛当前轮范围

若请求包含多个独立系统/阶段/能力，先帮用户收敛：
- 这一轮最值得优先解决的核心问题
- 哪些能力必须进入当前版本
- 哪些应推迟到后续增量

规格服务于当前轮可被评审、可被设计的范围。

### 3. 分轮澄清需求

遵循 `Capture → Challenge → Clarify`。默认检查覆盖面：

1. 问题、用户、目标与非目标
2. 核心行为与关键流程
3. 边界、异常与失败路径
4. 约束、依赖、接口与兼容性
5. 非功能需求与验收口径
6. 术语与待确认项

**这是 coverage checklist，不是 6 轮脚本。** 已覆盖的跳过；只剩 1-2 个阻塞事实的合并在一轮问完。

提问规则：先问范围/角色/成功标准，再问边界细节；合并共享同一决策的问题；用 assume-and-confirm 加速；每轮结束前总结已锁定与待确认项。

若因 review findings 重新进入：只针对阻塞项补充确认，不重新发起整轮澄清。

### 4. 整理 requirement rows

写规格前，先把确认内容整理成结构化行。默认区分：`FR`、`NFR`、`CON`、`IFR`、`ASM`、`EXC`。

核心需求编号如 `FR-001`、`NFR-001`。最小字段契约见 `references/requirement-authoring-contract.md`，每条至少：
- `ID` + `Statement`（可观察、可判断）
- `Acceptance`（至少一个可验证标准）
- `Priority`（`Must/Should/Could/Won't`）
- `Source / Trace Anchor`

### 5. 粒度检查与延后判断

按 `references/granularity-and-deferral.md` 检查：
- 是否命中 G1-G6 oversized 信号
- 哪些需求属于后续增量而非当前轮
- `EXC` 是真正非目标还是应回收到 deferred backlog

1-3 个不改变范围的拆分可在草稿中直接建议；4 个及以上或改变范围边界的必须向用户确认。deferred 需求写入 backlog。

### 6. 起草规格

按 `references/spec-template.md` 的默认结构起草。若 `AGENTS.md` 声明了模板覆盖，优先遵循。

编写要求：背景写"为什么"不写方案；功能需求写可观察行为；非功能需求写可判断条件；约束写硬性限制；假设写失效风险。

### 7. 区分开放问题

- **已确认**：直接写入正文
- **需用户确认**：先问清再写
- **非阻塞**：可保留但不影响主干
- **阻塞**：交 reviewer 前必须解决（核心范围摇摆、主要成功标准未定、关键约束未知等）

### 8. 评审前自检

交 `mdc-review(review_type=spec)` 前确认：
- 问题陈述、目标、主要用户清楚
- 范围内/范围外显式说明
- 核心功能需求逐条可观察、可验证、带 ID
- 需求与验收标准粒度对应
- G1-G6 oversized 已拆分或标注
- deferred requirements 已写入 backlog
- 模糊词已量化、需求未混入设计选择
- 阻塞性开放问题已解决

### 9. 派发 reviewer

按 `references/reviewer-handoff.md` 派发独立 reviewer subagent 执行 `mdc-review(review_type=spec)`，不内联执行。reviewer 返回后按协议处理结果。

## Output Contract

完成时产出：
- 可评审规格草稿（保存到 `features/<active>/ar-spec.md`）
- 如适用，deferred backlog（相邻路径）
- `features/<active>/progress.md` 状态同步：Current Stage → "规格草稿已完成"，Next Action → `mdc-review(review_type=spec)`

若草稿未达评审门槛，不伪造 handoff；明确写出仍缺什么。

## Red Flags

- 从用户想法直接跳到架构设计
- 把头脑风暴笔记当成已批准规格
- 规格里写任务、里程碑或提交计划
- 多个独立能力打包成一句"大需求"
- 核心需求缺少 Priority 或 Source
- 只写 happy path，不写边界和失败路径
- 提前使用 class、endpoint、table 等设计语言
- "后续再做"只留在 prose 里无 backlog
- 成功标准留成隐含信息
- handoff 缺失却声称"可以继续往下走"

## Reference Guide

| 文件 | 用途 |
|------|------|
| `references/requirement-authoring-contract.md` | 核心需求最小字段契约与编号规范 |
| `references/granularity-and-deferral.md` | G1-G6 粒度信号、拆分规则、deferred 判断 |
| `references/spec-template.md` | 默认规格模板结构与保存路径 |
| `references/reviewer-handoff.md` | reviewer 派发协议、结果处理、定向回修规则 |

## Verification

- [ ] 规格草稿已保存到 `features/<active>/ar-spec.md`
- [ ] 范围、范围外、核心功能需求、约束、关键 NFR 已写清
- [ ] 核心 FR/NFR 具备 ID、Priority、Source
- [ ] oversized 需求已按 G1-G6 处理
- [ ] deferred requirements 已写入 backlog 或明确不存在
- [ ] 阻塞性开放问题已解决
- [ ] `features/<active>/progress.md` 已同步，下一步为 `mdc-review(review_type=spec)`
