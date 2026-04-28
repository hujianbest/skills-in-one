# `mdc-specify`

## 简介

`mdc-specify` 用于澄清需求并起草可评审规格。它把需求收敛成后续设计和实现不需要靠猜测推进的规格草稿。

## 目录结构

```text
mdc-specify/
├── README.md
├── SKILL.md
├── references/
│   ├── requirement-authoring-contract.md
│   └── granularity-and-deferral.md
└── evals/
    ├── README.md
    └── evals.json
```

各文件职责：

- `README.md`：面向使用者的说明文档
- `SKILL.md`：skill 本体
- `references/requirement-authoring-contract.md`：需求编写最小契约
- `references/granularity-and-deferral.md`：粒度检查与延后判断规则
- `evals/README.md`：评测目标说明
- `evals/evals.json`：评测用 prompts

## 适用场景

以下场景适合使用 `mdc-specify`：

- 尚无已批准需求规格
- 现有规格仍停留在想法、草稿或待收敛状态
- `mdc-review(review_type=spec)` 返回 `需修改` 或 `阻塞`，需要按 findings 修订规格
- 用户明确需要先澄清范围、验收标准、边界、约束、非目标，再进入设计或实现

## 不适用场景

以下情况不建议直接使用：

- 已有已批准规格，当前问题已经进入 HOW 层设计，改用 `mdc-ar-design`
- 规格已批准、设计也已批准，当前需要任务计划，改用 `mdc-tasks`
- 当前是热修复、增量变更或阶段不清，先回到 `using-mdc-workflow`
- 当前只是要求执行规格评审，改用 `mdc-review(review_type=spec)`

## 核心能力

`mdc-specify` 会做以下事情：

1. 读取当前需求相关的最小上下文
2. 通过结构化澄清收敛需求
3. 当需求过大时做范围收敛和粒度检查
4. 起草规格文档，具备 ID、Priority、Source / Trace Anchor
5. 处理 deferred backlog
6. 派发 reviewer subagent 执行 `mdc-review(review_type=spec)`
7. 根据 review findings 定向回修

它不会直接跳到实现，也不会把接口、表结构、类设计、框架选择等实现细节写进需求规格。

## 高质量规格特征

交给 `mdc-review(review_type=spec)` 之前，规格至少应具备这些特征：

- 范围清晰，范围外内容显式写出
- 核心功能需求是可观察、可验证的，并具备稳定 `ID`
- 每条核心 `FR` / 关键 `NFR` 都有需求陈述、验收口径、优先级和 `Source / Trace Anchor`
- 需求粒度适合当前轮次，不把多个独立能力硬塞进一条 `FR`
- 真实的延后需求已被识别，并在需要时写入 deferred backlog
- 关键边界、失败路径或权限差异至少被识别
- 非功能需求和约束不是口号，而是可落地判断的条件
- 需求与设计决策分离，不提前做架构选型
- 阻塞性开放问题已解决

## 推荐输入

为了让它更高效，建议尽量提供：

- 你要解决的问题
- 谁会使用这个能力
- 已知范围和限制
- 明确不做的内容
- 成功标准或验收标准
- 现有草稿、旧文档或相关背景材料
- 指定的文档路径、模板或章节要求

信息不全也没关系，`mdc-specify` 会先通过提问帮助补齐。

## 典型工作流

### 1. 了解上下文

读取完成规格澄清所需的最少材料。

### 2. 范围收敛

如果当前请求同时包含多个相对独立的系统、阶段或产品能力，先帮助收敛当前轮次。

### 3. 分轮澄清需求

澄清时遵循 `Capture -> Challenge -> Clarify`：

- `Capture`：先复述当前理解的目标、对象和范围
- `Challenge`：指出模糊词、打包需求、隐藏假设或缺失边界
- `Clarify`：把想法收敛成可观察、可验证、可评审的表述

默认至少检查这些澄清轮次是否需要：

1. 问题、用户、目标与非目标
2. 核心行为与关键流程
3. 边界、异常与失败路径
4. 约束、依赖、接口与兼容性
5. 非功能需求与验收口径
6. 术语与待确认项

### 4. 整理 requirement rows

在写规格前，先把已确认内容整理成结构化 requirement rows。默认至少区分：

- `FR`：功能需求
- `NFR`：非功能需求
- `CON`：约束
- `IFR`：接口与依赖
- `ASM`：假设
- `EXC`：范围外内容

每条核心需求至少要有：`ID`、`Statement`、`Acceptance`、`Priority`、`Source / Trace Anchor`。

### 5. 粒度检查与延后判断

根据 `G1-G6` 信号检查需求是否过大，决定是否拆分或延后。

### 6. 起草规格

若 `AGENTS.md` 为当前项目声明了规格模板、章节骨架或命名要求，优先遵循这些约定。

若未提供模板覆盖，则使用默认结构：

```markdown
# <主题> 需求规格说明

- 状态: 草稿
- 主题: <主题>

## 1. 背景与问题陈述
## 2. 目标与成功标准
## 3. 用户角色与关键场景
## 4. 范围
## 5. 范围外内容
## 6. 术语与定义（按需）
## 7. 功能需求
## 8. 非功能需求
## 9. 外部接口与依赖（按需）
## 10. 约束
## 11. 假设（按需）
## 12. 开放问题
```

### 7. 评审前自检

交给 `mdc-review(review_type=spec)` 前，完成自检。

### 8. 派发 reviewer subagent

草稿准备好后，派发独立 reviewer subagent 执行 `mdc-review(review_type=spec)`。

### 9. 定向回修

根据 review findings 定向回修，不重新开启整轮无关澄清。

## 输出内容

完成时至少应产出：

- 一份可评审规格草稿
- 如适用，一份 deferred backlog
- 可供 reviewer 定位的最小上下文
- canonical handoff：`mdc-review(review_type=spec)`

推荐输出：

```markdown
需求规格草稿已起草完成，下一步应派发独立 reviewer subagent 执行 `mdc-review(review_type=spec)`。

推荐下一步 skill: `mdc-review(review_type=spec)`
```

## 相关文件

- Skill 本体：[`SKILL.md`](SKILL.md)
- 需求编写契约：[`references/requirement-authoring-contract.md`](references/requirement-authoring-contract.md)
- 粒度与延后规则：[`references/granularity-and-deferral.md`](references/granularity-and-deferral.md)
- 评测说明：[`evals/README.md`](evals/README.md)
- 评测数据：[`evals/evals.json`](evals/evals.json)

## 总结

`mdc-specify` 适合需求尚不稳定、范围需要澄清、想先获得一份规范文档草稿的场景。它不是给出设计方案，而是把需求收敛成后续设计和实现不需要靠猜测推进的规格草稿。
