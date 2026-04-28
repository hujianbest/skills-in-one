---
name: using-mdc-workflow
description: MDC 软件交付工作流编排器。作为所有软件交付请求的入口和 runtime authority，负责判断当前阶段、选择工作流配置文件、路由到正确的下游技能、派发 reviewer subagent、恢复编排等。当用户提出新功能、Bug修复、代码变更、需求分析等软件交付类请求时，必须首先通过本技能进行阶段判断和路由。
---

# 使用 MDC 工作流

## 概述

MDC 工作流是一套软件交付技能集合，按开发阶段组织。本技能承担双重职责：

1. **Public Entry**: 帮助用户发现并进入正确的 MDC 技能
2. **Runtime Authority**: 权威路由决策、review dispatch、恢复编排

简化后的 MDC 工作流包含 **10 个技能**：

| 技能 | 职责 |
|---|---|
| `using-mdc-workflow` | 编排入口 |
| `mdc-specify` | 需求规格 |
| `mdc-review` | 统一评审（spec/arch-design/ar-design/tasks，参数化 review_type） |
| `mdc-arch-design` | 架构级设计（仅新增组件时执行，产出架构决策记录 + 组件实现设计说明书） |
| `mdc-ar-design` | AR实现设计（每轮 AR 必经，产出 AR 实现设计文档） |
| `mdc-tasks` | 任务拆分 |
| `mdc-test-driven-dev` | TDD 实现 |
| `mdc-test-checker` | 测试评审 |
| `mdc-code-review` | 代码检视 |
| `mdc-finalize` | 回归门禁+完成门禁+收尾（含内嵌追溯链检查） |
| `mdc-bug-patterns` | Bug 模式检测 |

## Workflow

### 1. 识别请求类型

分析用户输入，识别请求类型：

1. **判断是否为明确的功能/需求请求**：关键词如"需要"、"增加"、"实现"、"添加"、"开发"
2. **判断是否为 Bug 修复请求**：关键词如"修复"、"bug"、"错误"、"崩溃"、"失败"
3. **判断是否暗示已有工件**：用户提到"已完成"、"已经"、"写好了"
4. **判断是否为测试通过信号**：提到"通过"、"已检视"、"reviewed"

### 2. 检测已有工件

按优先级检查工件存在性和状态：

**优先级 1：检查 `features/<active>/` 目录**
```bash
# 查找 features/ 下最新的 AR 目录
ls -t features/ | head -1  # 获取最新的 <TICKET>-<slug>
```

- 读取 `features/<active>/progress.md`，识别当前阶段
- 检查 `features/<active>/ar-spec.md`，读取状态（草稿/已批准）
- 检查 `features/<active>/ar-design.md`，读取状态
- 检查 `features/<active>/tasks.md`
- 检查 `features/<active>/reviews/` 下的最新评审记录

**优先级 2：检查项目长期资产**
- 存在 `docs/<component-name>-spec.md`
- 存在 `docs/<component-name>-design.md`

### 3. 判断是否涉及新增组件

**关键判断逻辑**，决定是走 `mdc-arch-design` 还是直接走 `mdc-ar-design`。

**两级设计区分**：
- **组件级设计**（`mdc-arch-design`）：定义"这个组件是什么、包含什么、怎么组织"。产出组件实现设计说明书（`docs/<component-name>-design.md`），作为组件基线。**仅当新增组件时需要**。
- **AR级设计**（`mdc-ar-design`）：定义"本轮 AR 在组件基线上做什么增量实现"。产出 AR 实现设计文档（`features/<active>/ar-design.md`）。**每轮 AR 都必须执行**。

检查用户输入和上下文，判断是否涉及以下内容：

1. **新增组件**：新建服务、添加新模块
2. **新增接口**：定义新的系统边界或公共 API
3. **数据模型重大变更**：改变核心数据结构（不只是字段增减）
4. **新子系统**：添加完整的功能子系统

**判断信号**（任一命中则认为需要架构级设计）：
- 用户明确提到"新增服务"、"新增模块"、"添加组件"
- 提到"创建新的"、"需要新的服务"
- Bug 修复范围涉及"新增"、"搭建"
- 需求范围跨越多个组件或子系统

**否则**（现有组件修改）：
- 功能描述指向已知组件（如 lidar-driver、perception-service）
- Bug 修复明确限定于现有模块
- 提到"在XX组件上"、"改动XX"

**关键结论**：
- 需要新增组件 → 先 `mdc-arch-design`（建立组件基线），再 `mdc-ar-design`（基于基线做 AR 增量设计）
- 仅修改现有组件 → 直接 `mdc-ar-design`（基于现有代码或 `docs/<component-name>-design.md`（若存在）做 AR 实现）

### 4. 判断当前阶段并选择路由

基于工件检查结果，判断当前在工作流的哪个阶段：

| 已有工件状态 | 阶段判断 | 下一步路由 |
|------------|---------|-----------|
| 无任何工件 | 入口阶段 | `mdc-specify` |
| 有 `ar-spec.md`（草稿） | 规格阶段 | `mdc-specify`（修订） |
| 有 `ar-spec.md`（已批准），无设计 | 设计阶段 | **[判断是否新增组件]** → 是: `mdc-arch-design`（先建立组件基线）; 否: `mdc-ar-design`（基于现有代码/组件设计做 AR 实现） |
| 有 `ar-design.md`（草稿） | AR设计阶段 | `mdc-ar-design` |
| 有 `ar-design.md`（已批准），无任务 | 任务阶段 | `mdc-tasks` |
| 有 `tasks.md`，无实现 | 实现阶段 | `mdc-test-driven-dev` |
| 有实现，无 review | 检视阶段 | `mdc-code-review` |
| Code review 通过 | Finish 阶段 | `mdc-finalize` |

### 5. 选择 Workflow Profile

基于当前证据选择最匹配的 profile：

**Full Profile**：
- 未有已批准规格
- 涉及新增组件/模块/接口
- 架构或接口有重大变更
- 高风险模块的变更
- 用户明确要求从头开始

**Standard Profile**：
- 已有已批准规格+设计
- 需要新增任务
- 中等复杂度的扩展或 bugfix
- 不涉及架构级变更

**Lightweight Profile**：
- 仅文档/配置/样式变化
- 低风险单文件 bugfix
- 无功能行为变化
- 明确限定于现有组件的小改动

**Bug 修复特殊规则**：
- 简单 bug（低风险单文件）→ `lightweight`
- 中等 bug → `standard`
- 复杂 bug（涉及架构/接口变更）→ `full`

### 6. 构造路由决策

基于以上判断，构造标准化的路由输出：

```markdown
## 工作流分析

**请求类型**: [新功能/Bug修复/代码变更]
**已有工件**: [ar-spec|ar-design|tasks|无]
**当前阶段**: [需求收集/设计/任务拆分/实现/检视]
**涉及新增组件**: [是/否]
**设计基线**: [component-design-doc 存在/仅代码存在/无基线]
**Workflow Profile**: [full/standard/lightweight]

## 路由决策

**推荐下一步节点**: [mdc-specify|mdc-arch-design|mdc-ar-design|mdc-tasks|mdc-test-driven-dev|mdc-code-review|mdc-finalize]
**工件路径**: features/<active>/[ar-spec.md|ar-design.md|tasks.md|reviews/|verification/]
**是否 Review 节点**: [是/否]

## 决策依据

[解释路由决策的具体原因]
```

### 7. 派发游下一步行动

根据路由决策，引导用户进入对应 skill：

- **非 Review 节点**：直接说明使用哪个 skill，用户可选择启动
- **Review 节点**：说明将派发独立 reviewer subagent
- **阶段不清**：提出澄清问题，帮助用户明确状态

## 核心原则

### Review 节点必须派发独立 Subagent

**这是强制要求，不可协商：**

- review 节点进入时，父会话**不得**直接执行评审判断
- 父会话必须构造 review request，启动**独立 reviewer subagent**
- reviewer subagent 在 fresh context 中执行评审，写 review 记录并回传结构化摘要
- 父会话消费摘要后，继续主链推进或进入 approval step

详细协议见 `references/review-dispatch-protocol.md`。

### Execution Mode 规则

- `interactive`: approval step 需要等待用户输入
- `auto`: approval step 可由父会话按 policy 写 approval record 后自动继续
- `auto` **不等于**跳过 review、gate 或 approval 节点

## 技能发现与路由

当任务到达时，识别开发阶段并应用相应的技能：

```
软件交付请求到达
    │
    ├── 模糊想法/需要细化？ ─────────→ mdc-specify
    ├── 新功能/新需求？ ─────────────→ mdc-specify → mdc-review(review_type=spec) → 规格真人确认
    │                                    │
    │                                    └── [判断: 是否涉及新增组件/模块/接口?]
    │                                        ├─ 是 → mdc-arch-design → mdc-review(review_type=arch-design) → 架构设计真人确认 → mdc-ar-design
    │                                        │      （产出组件基线：arch-design-record + component-design-doc）
    │                                        └─ 否 → mdc-ar-design → mdc-review(review_type=ar-design) → AR设计真人确认
    │                                               （基于现有代码或 component-design-doc 做 AR 增量）
    │
    ├── 已有规格，需要设计？ ───────→ [判断: 是否涉及新增组件?] → ... (同上)
    ├── 已有设计，需要任务？ ───────→ mdc-tasks → mdc-review(review_type=tasks) → 任务真人确认
    ├── 已有任务，需要实现？ ───────→ mdc-test-driven-dev → mdc-test-checker → mdc-code-review
    │                                                ↓
    ├── 代码检视通过？ ─────────────→ mdc-finalize
    └── Bug 修复？ ─────────────────→ [按复杂度选 profile，进主链]
```

Bug 修复路由策略（替代 hotfix 支线）：
- **简单 bug**（低风险单文件）→ `lightweight` profile → `mdc-ar-design` → `mdc-review`(ar-design) → AR设计真人确认
- **中等 bug** → `standard` profile → `mdc-ar-design` → `mdc-review`(ar-design) → AR设计真人确认
- **复杂 bug**（涉及架构/接口变更）→ `full` profile → `mdc-specify`

需求变更/范围调整路由策略（替代 increment 支线）：
- 直接回到 `using-mdc-workflow` 重新判断 profile 和重入点
- 若变更使已批准工件失效，从失效的最上游节点重入

## 工作流 Profile 选择

### Profile 定义

| Profile | 适用场景 |
| --- | --- |
| `full` | 无已批准规格或设计、架构/接口/数据模型变化、高风险模块、从头开始 |
| `standard` | 已有已批准规格+设计，需要新增任务；中等复杂度扩展或 bugfix |
| `lightweight` | 纯文档/配置/样式变化，或低风险单文件 bugfix，且无功能行为变化 |

### 判定规则

1. 先执行 `AGENTS.md` 中的强制 profile 规则
2. 若 `features/<active>/progress.md` 中已有仍有效的 profile，沿用
3. 否则按当前证据选择最匹配的 profile
4. 若信号冲突，选择更重的 profile

升级规则：`lightweight` → `standard` → `full`，不允许降级。

## 合法节点集合

### full profile 主链节点

- `mdc-specify`
- `mdc-review` (review_type=spec, 派发 subagent)
- `规格真人确认`
- `mdc-arch-design` (条件：涉及新增组件时执行；产出 arch-design-record + component-design-doc)
- `mdc-review` (review_type=arch-design, 派发 subagent)
- `架构设计真人确认`
- `mdc-ar-design`
- `mdc-review` (review_type=ar-design, 派发 subagent)
- `AR设计真人确认`
- `mdc-tasks`
- `mdc-review` (review_type=tasks, 派发 subagent)
- `任务真人确认`
- `mdc-test-driven-dev`
- `mdc-test-checker` (派发 subagent)
- `mdc-code-review` (派发 subagent)
- `mdc-finalize`

### standard profile 主链节点

- `mdc-specify` (如果规格未批准)
- `mdc-review` (review_type=spec, 派发 subagent) (如果规格未批准)
- `规格真人确认` (如果规格未批准)
- `mdc-ar-design`
- `mdc-review` (review_type=ar-design, 派发 subagent)
- `AR设计真人确认`
- `mdc-tasks`
- `mdc-review` (review_type=tasks, 派发 subagent)
- `任务真人确认`
- `mdc-test-driven-dev`
- `mdc-test-checker` (派发 subagent)
- `mdc-code-review` (派发 subagent)
- `mdc-finalize`

### lightweight profile 主链节点

- `mdc-ar-design`
- `mdc-review` (review_type=ar-design, 派发 subagent)
- `AR设计真人确认`
- `mdc-tasks`
- `mdc-test-driven-dev`
- `mdc-test-checker` (派发 subagent)
- `mdc-code-review` (派发 subagent)
- `mdc-finalize`

详细迁移表见 `references/profile-node-and-transition-map.md`。

## Review Dispatch Protocol

当路由结果命中 review 节点时：

### 1. 不要在父会话内联执行

```
错误做法：直接在当前会话展开 review 判断
正确做法：构造 review request，派发独立 reviewer subagent
```

### 2. 构造 Review Request

```json
{
  "review_type": "spec|arch-design|ar-design|tasks|code",
  "review_skill": "mdc-review|mdc-code-review",
  "topic": "本次评审主题",
  "artifact_paths": ["被检视交付件路径"],
  "supporting_context_paths": ["最小必要辅助上下文路径"],
  "workspace_isolation": "in-place|worktree-required|worktree-active",
  "worktree_path": "当前 worktree 根路径",
  "worktree_branch": "当前分支",
  "expected_record_path": "features/<active>/reviews/...",
  "current_profile": "full|standard|lightweight"
}
```

### 3. 派发 Subagent

使用 Task 工具启动 reviewer subagent：
- subagent_type: `general`
- 在 fresh context 中执行评审
- 读取 `mdc-review` 或 `mdc-code-review` skill

### 4. 消费 Reviewer 返回

Reviewer 返回结构化摘要：

```json
{
  "conclusion": "通过|需修改|阻塞",
  "next_action_or_recommended_skill": "推荐下一步 canonical 节点",
  "record_path": "实际写入的 review 记录路径",
  "key_findings": ["关键发现"],
  "needs_human_confirmation": false,
  "reroute_via_router": false
}
```

详细协议见 `references/reviewer-return-contract.md`。

### 5. 处理结论

按以下顺序处理：

1. 若 `reroute_via_router=true`，回到 `using-mdc-workflow` 重编排
2. 若 `conclusion=通过` 且 `needs_human_confirmation=true`：
   - `interactive`: 进入真人确认
   - `auto`: 写 approval record 后继续
3. 若 `conclusion=需修改` 或 `阻塞`，按 `next_action_or_recommended_skill` 回修

## 结果驱动迁移表

### full profile 迁移表

| 当前节点 | 结论 | 下一推荐节点 |
|---|---|---|
| `mdc-review`(spec) | `通过` | 规格真人确认 |
| `mdc-review`(spec) | `需修改` / `阻塞` | `mdc-specify` |
| `mdc-review`(spec) | `阻塞`（需重编排） | `using-mdc-workflow` |
| 规格真人确认 | approval step 完成 | `[判断: 是否涉及新增组件?] → 是:mdc-arch-design（建立组件基线） / 否:mdc-ar-design（基于代码或已有 design doc）` |
| 规格真人确认 | 要求修改 | `mdc-specify` |
| `mdc-arch-design` | 设计完成 | `mdc-review`(arch-design) |
| `mdc-review`(arch-design) | `通过` | 架构设计真人确认 |
| `mdc-review`(arch-design) | `需修改` / `阻塞` | `mdc-arch-design` |
| `mdc-review`(arch-design) | `阻塞`（需重编排） | `using-mdc-workflow` |
| 架构设计真人确认 | approval step 完成 | `mdc-ar-design` |
| 架构设计真人确认 | 要求修改 | `mdc-arch-design` |
| `mdc-ar-design` | AR 设计完成 | `mdc-review`(ar-design) |
| `mdc-review`(ar-design) | `通过` | AR设计真人确认 |
| `mdc-review`(ar-design) | `需修改` / `阻塞` | `mdc-ar-design` |
| `mdc-review`(ar-design) | `阻塞`（需重编排） | `using-mdc-workflow` |
| AR设计真人确认 | approval step 完成 | `mdc-tasks` |
| AR设计真人确认 | 要求修改 | `mdc-ar-design` |
| `mdc-tasks` | 任务计划完成 | `mdc-review`(tasks) |
| `mdc-review`(tasks) | `通过` | 任务真人确认 |
| `mdc-review`(tasks) | `需修改` / `阻塞` | `mdc-tasks` |
| `mdc-review`(tasks) | `阻塞`（需重编排） | `using-mdc-workflow` |
| 任务真人确认 | approval step 完成 | `mdc-test-driven-dev` |
| 任务真人确认 | 要求修改 | `mdc-tasks` |
| `mdc-test-driven-dev` | 实现完成 | `mdc-test-checker` |
| `mdc-test-checker` | `通过` | `mdc-code-review` |
| `mdc-test-checker` | `需修改` / `阻塞` | `mdc-test-driven-dev` |
| `mdc-code-review` | `通过` | `mdc-finalize` |
| `mdc-code-review` | `需修改` / `阻塞` | `mdc-test-driven-dev` |
| `mdc-finalize` | 追溯链不通过 | `mdc-test-driven-dev` |
| `mdc-finalize` | 回归不通过 | `mdc-test-driven-dev` |
| `mdc-finalize` | 完成通过 + 有唯一 next-ready task | `using-mdc-workflow` |
| `mdc-finalize` | 完成通过 + 无剩余任务 | workflow 收尾（内嵌 finalize） |
| `mdc-finalize` | 完成通过 + 有剩余任务但 next-ready 不唯一 | `using-mdc-workflow` |
| `mdc-finalize` | `阻塞`（环境） | `mdc-finalize`（重试） |
| `mdc-finalize` | `阻塞`（上游） | `using-mdc-workflow` |
| `mdc-finalize` | task closeout | `using-mdc-workflow` |
| `mdc-finalize` | workflow closeout | workflow 结束 |
| `mdc-finalize` | `blocked` | `using-mdc-workflow` |

### standard profile 迁移表

| 当前节点 | 结论 | 下一推荐节点 |
|---|---|---|
| `mdc-ar-design` | AR 设计完成 | `mdc-review`(ar-design) |
| `mdc-review`(ar-design) | `通过` | AR设计真人确认 |
| `mdc-review`(ar-design) | `需修改` / `阻塞` | `mdc-ar-design` |
| AR设计真人确认 | approval step 完成 | `mdc-tasks` |
| AR设计真人确认 | 要求修改 | `mdc-ar-design` |
| `mdc-tasks` | 任务计划完成 | `mdc-review`(tasks) |
| `mdc-review`(tasks) | `通过` | 任务真人确认 |
| `mdc-review`(tasks) | `需修改` / `阻塞` | `mdc-tasks` |
| 任务真人确认 | approval step 完成 | `mdc-test-driven-dev` |
| `mdc-test-driven-dev` | 实现完成 | `mdc-test-checker` |
| `mdc-test-checker` | `通过` | `mdc-code-review` |
| `mdc-code-review` | `通过` | `mdc-finalize` |
| `mdc-finalize` | 完成 | 同 full profile finalize 行为 |

### lightweight profile 迁移表

| 当前节点 | 结论 | 下一推荐节点 |
|---|---|---|
| `mdc-ar-design` | AR 设计完成 | `mdc-review`(ar-design) |
| `mdc-review`(ar-design) | `通过` | AR设计真人确认 |
| `mdc-review`(ar-design) | `需修改` / `阻塞` | `mdc-ar-design` |
| AR设计真人确认 | approval step 完成 | `mdc-tasks` |
| AR设计真人确认 | 要求修改 | `mdc-ar-design` |
| `mdc-tasks` | 任务计划完成 | `mdc-test-driven-dev` |
| `mdc-test-driven-dev` | 实现完成 | `mdc-test-checker` |
| `mdc-test-checker` | `通过` | `mdc-code-review` |
| `mdc-code-review` | `通过` | `mdc-finalize` |
| `mdc-finalize` | 完成 | 同 full profile finalize 行为 |

详细迁移表见 `references/profile-node-and-transition-map.md`。

## 核心行为准则

### 1. 明确假设

在实现任何非平凡内容前，明确陈述你的假设：

```
我正在做出的假设：
1. [关于需求的假设]
2. [关于架构的假设]
→ 如有错误请立即纠正，否则我将按这些假设继续。
```

### 2. 主动管理困惑

当遇到不一致、冲突的需求或不清晰的规格时：

1. **停止。** 不要猜测并继续。
2. 说出具体的困惑点。
3. 呈现权衡或提出澄清问题。
4. 等待解决后再继续。

### 3. 必要时反驳

你不是唯命是从的机器。当一个方法有明显问题时：

- 直接指出问题
- 解释具体的负面影响（尽可能量化）
- 提出替代方案
- 如果用户在充分了解情况后决定覆盖，接受用户的决定

### 4. 强制简洁

在完成任何实现前，问：
- 这能用更少的代码行完成吗？
- 这些抽象是否值得它们的复杂性？

### 5. 维护范围纪律

只触及你被要求触及的内容。不要做未经请求的翻新。

### 6. 验证，不要假设

每个技能都包含验证步骤。任务在验证通过之前不算完成。

## 阶段判断证据要求

### 已有工件检查

- `features/<active>/ar-spec.md` 存在且状态为"已批准"
- `features/<active>/ar-design.md` 存在且状态为"已批准"
- `features/<active>/tasks.md` 存在且包含可执行任务项
- `docs/<component-name>-spec.md` 存在（长期资产基线）
- `docs/<component-name>-design.md` 存在（长期资产基线）

`<active>` 为当前 AR 目录名，形如 `<TICKET>-kebab-slug/`。

### 批准状态验证

可接受的批准证据：
- 评审记录中包含 `Human Confirmation: Yes`
- 指定审批人的 PR 审批已通过
- 工单状态变为 `Design Approved`
- 规格文档状态标记为"已批准"或 `Status: Approved`

## 输出格式

```
## 工作流分析

**请求类型**: [新功能/Bug修复/代码变更/需求分析]
**已有工件**: [规格/设计/任务/无]
**当前阶段**: [需求收集/设计/任务拆分/实现/检视]
**Workflow Profile**: [full/standard/lightweight]
**Execution Mode**: [interactive/auto]

## 路由决策

**下一步节点**: [技能名称]
**是否 Review 节点**: [是/否]
**是否需要派发 Subagent**: [是/否]

## 决策依据

[解释为什么选择这个路由，引用具体证据]

## 下一步行动

[具体行动描述]
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "用户点名了某个 skill，就直接进去吧" | 点名 skill 不等于当前时机正确，仍要先判断能否合法进入 |
| "我可以在父会话里顺手 review 一下" | **禁止。** review 节点必须派发独立 reviewer subagent |
| "auto 模式可以跳过 approval step" | `auto` 只改变 approval step 的解决方式，不删除节点 |
| "项目已经有代码了，不需要写规格" | 代码存在 ≠ 规格已批准。无已批准规格文档就必须从 mdc-specify 开始，归入 full profile |
| "这只是简单继续，不用重新判断 profile" | "继续"不等于实现阶段，必须绑定当前证据重新判断 |
| "没有 component-design-doc 就不能做 AR 设计" | 不需要。AR 设计可基于现有代码逆向分析，component-design-doc 仅在新增组件时由 mdc-arch-design 产出 |

## Red Flags

- 在父会话内联执行 review 判断（**严重违规**）
- 因为命令名或用户点名，就跳过 route/profile 判断
- 把 `auto` 理解成"可以跳过 approval step"
- 忽略 evidence conflict，继续沿用上一轮印象推进
- 发现 profile 不再成立却不升级
- 把代码实现存在当作规格已批准，跳过 mdc-specify
- 新增组件时跳过 mdc-arch-design 直接到 mdc-ar-design（无组件基线就做 AR 增量设计）
- 在 ar-design 中重新定义组件级架构（应属于 mdc-arch-design）

## 支持参考

- `references/review-dispatch-protocol.md`
- `references/reviewer-return-contract.md`
- `references/profile-node-and-transition-map.md`
- `references/task-progress.md` — canonical 任务进度模板（实际落盘路径：`features/<active>/progress.md`）

## Verification

只有在以下条件全部满足时，这个 skill 才算完成：

- [ ] 已判断当前是在做 entry discovery 还是 runtime routing
- [ ] 已基于最新证据决定 `Workflow Profile`
- [ ] 已归一化当前 `Execution Mode`
- [ ] 已把推荐节点约束在当前 profile 的合法节点集合内
- [ ] 若当前是 review 节点，会派发 reviewer subagent，**不是**在父会话里内联评审
- [ ] 若当前不是 hard stop，会在同一轮继续执行
- [ ] 若命中 approval step，已按 `Execution Mode` 处理
