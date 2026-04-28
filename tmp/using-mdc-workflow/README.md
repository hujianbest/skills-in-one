# `using-mdc-workflow`

## 简介

`using-mdc-workflow` 用于作为所有软件交付请求的入口，判断当前阶段、选择工作流配置文件、路由到正确的下游技能。

它关注的不是"直接开始编码"，而是把软件交付请求整理成：

- 当前阶段判断
- 已有工件检查
- 工作流 Profile 选择
- 下游技能路由
- 决策证据提供
- 下一步行动明确

## 目录结构

```text
using-mdc-workflow/
├── README.md
├── SKILL.md
└── evals/
    └── evals.json
```

各文件职责：

- `README.md`：面向使用者的说明文档
- `SKILL.md`：skill 本体
- `evals/evals.json`：评测用 prompts

## 适用场景

以下场景适合使用 `using-mdc-workflow`：

- 用户提出新功能需求，需要从需求规格开始
- 已有需求规格，需要进行技术设计
- 已有设计文档，需要拆分任务
- 已有任务计划，需要开始实现
- 代码实现完成，需要代码检视
- 发现 Bug，需要修复
- 不确定当前应该调用哪个下游技能

## 不适用场景

以下情况不建议优先使用这个版本：

- 用户明确知道要调用的具体技能（可直接调用）
- 请求不属于软件交付类（如纯咨询、知识问答）
- 已经在下游技能执行过程中，无需重新路由

## 核心能力

`using-mdc-workflow` 会做 6 件事：

1. 分析请求类型（新功能、Bug 修复、代码变更、需求分析等）
2. 检查已有工件（docs/specs/、docs/designs/、docs/tasks/ 目录）
3. 判断当前阶段（需求、设计、任务、实现、检视）
4. 选择工作流 Profile（Full / Standard / Lightweight）
5. 路由到下游技能并明确告知用户
6. 提供决策证据和下一步行动建议

它不会跳过阶段判断直接执行，也不会在缺少必要工件时臆造进度。

## 工作流 Profile

### Full Profile（完整工作流）

适用于全新需求，从零开始：

```text
starter → mdc-specify → mdc-ar-design → mdc-tasks → mdc-test-driven-dev → mdc-code-review → 完成
```

### Standard Profile（标准工作流）

适用于已有规格和设计，需要任务拆分和实现：

```text
starter → mdc-tasks → mdc-test-driven-dev → mdc-code-review → 完成
```

### Lightweight Profile（轻量工作流）

适用于简单变更、Bug 修复、小优化：

```text
starter → mdc-test-driven-dev → mdc-code-review → 完成
```

## 路由规则

| 当前阶段 | 已有工件 | 下游技能 | Profile |
|----------|----------|----------|---------|
| 全新需求 | 无 | mdc-specify | Full |
| 规格已完成 | 需求规格（已批准）| mdc-ar-design | Full |
| 设计已完成 | 设计文档（已批准）| mdc-tasks | Standard |
| 任务已完成 | 任务计划 | mdc-test-driven-dev | Standard |
| 实现已完成 | 代码+单元测试 | mdc-code-review | - |
| Bug修复 | - | mdc-test-driven-dev | Lightweight |

## 推荐输入

为了让它更高效，建议尽量提供：

- 明确的请求类型（新功能/Bug 修复/代码变更/需求分析）
- 已知的需求文档或设计文档路径
- 已知的任务计划或代码位置
- 当前阶段的大致判断（如果已知）

如果输入不足，`using-mdc-workflow` 会主动检查工件目录并告知当前状态。

## 推荐使用方式

最简单的调用方式，是直接提出软件交付请求：

```text
我需要实现一个新功能：用户审批流程。请帮我判断下一步应该做什么。
```

如果已经有部分工件：

```text
我已经有需求规格和设计文档了，都在 docs/ 目录下。请判断当前阶段并告诉我下一步调用哪个技能。
```

如果遇到 Bug：

```text
发现一个 Bug：审批页面无法加载。请帮我路由到正确的技能来修复它。
```

## 典型工作流

### 1. 接收请求

用户提出软件交付类请求，`using-mdc-workflow` 接收并开始分析。

### 2. 分析请求类型

判断请求类型：新功能、Bug 修复、代码变更、需求分析等。

### 3. 检查已有工件

检查工件目录：

- `docs/specs/` - 需求规格
- `docs/designs/` - 设计文档
- `docs/tasks/` - 任务计划

### 4. 判断当前阶段

基于请求类型和已有工件，判断当前阶段。

### 5. 选择 Profile

根据阶段和工件完整性，选择 Full / Standard / Lightweight Profile。

### 6. 路由下游技能

明确告知用户下一步调用哪个技能，并提供决策证据。

## 输出内容

完成时通常会得到：

### 1. 工作流分析

```markdown
**请求类型**: 新功能
**已有工件**: 需求规格（已批准）
**当前阶段**: 设计
```

### 2. 路由决策

```markdown
**选择 Profile**: Full
**下游技能**: mdc-ar-design
```

### 3. 决策依据

解释为什么选择这个路由，引用具体证据。

### 4. 下一步行动

```markdown
调用 mdc-ar-design 技能，执行设计文档生成。
```

## 常见误区

使用 `using-mdc-workflow` 时，常见问题包括：

- 直接跳过路由，手动选择下游技能，导致阶段错位
- 忽略工件检查，在缺少必要文档时强行进入下一阶段
- 对 Bug 修复使用 Full Profile，导致过度流程化
- 不确认工件是否已批准，就进入下游技能

如果出现这些情况，应该先通过 `using-mdc-workflow` 正确路由。

## 快速提示词

可以直接复制这些说法来调用：

```text
我需要实现一个新功能，请帮我判断当前阶段并路由到正确的技能。
```

```text
已有需求规格和设计文档，请告诉我下一步调用哪个技能。
```

```text
发现 Bug，请帮我路由到修复流程。
```

```text
我不确定当前应该做什么，请帮我分析工件状态并给出下一步建议。
```

## 测试结果

- **Iteration 2**: 6/6 测试用例通过（100% pass rate）
- **Baseline**: 0/6 通过（0% pass rate）
- **改进**: +100 percentage points

### 测试用例

| 测试 | 场景 | 结果 |
|------|------|------|
| eval-1 | 全新需求 → mdc-specify | ✅ PASS |
| eval-2 | 规格已完成 → mdc-ar-design | ✅ PASS |
| eval-3 | 设计已完成 → mdc-tasks | ✅ PASS |
| eval-4 | 任务已完成 → mdc-test-driven-dev | ✅ PASS |
| eval-5 | 实现已完成 → mdc-code-review | ✅ PASS |
| eval-6 | Bug修复 → mdc-test-driven-dev | ✅ PASS |

## 相关文件

- Skill 本体：[`SKILL.md`](SKILL.md)
- 评测数据：[`evals/evals.json`](evals/evals.json)

## 相关技能

- **mdc-specify**: 需求规格化
- **mdc-arch-design**: 架构设计
- **mdc-ar-design**: AR 实现设计（AR文档）
- **mdc-tasks**: 任务拆分
- **mdc-test-driven-dev**: 测试驱动开发
- **mdc-code-review**: 代码检视

## 总结

如果你的目标是"让软件交付请求自动路由到正确的下游技能"，`using-mdc-workflow` 就是合适入口。

它最适合不确定当前阶段、需要检查已有工件、或需要明确下一步行动的场景。

---

**注意**: 本技能只编排 `mdc-workflow/` 目录下的技能，不涉及 `mdc-dtfuzz-generator` 和 `mdc-hdt-generator`。
