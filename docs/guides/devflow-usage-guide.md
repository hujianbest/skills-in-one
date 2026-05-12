# DevFlow 使用指南

本文面向日常使用者，说明什么时候使用 DevFlow、如何向 AI 发起流程，以及常见问题如何判断。

## 1. DevFlow 简单介绍

### 1.1 DevFlow 是什么

DevFlow 是一套面向需求澄清、设计、实现、评审和收尾的 AI 协作流程 skills。它适合处理团队已经接受的 SR、AR、DTS 或 CHANGE，把输入推进成可追溯、可评审、可验证的工程产物。

DevFlow 不负责产品发现，也不替需求负责人、模块架构师、开发负责人做业务或架构拍板。它的价值是把已经决定要处理的工作项，按稳定流程落到规格、设计、代码、测试证据和收尾记录中。

### 1.2 DevFlow 适合解决什么问题

- 把模糊的 SR / AR / CHANGE 输入澄清成可评审的需求规格。
- 在新增组件、修改组件职责、SOA 接口、依赖、状态机时，编写组件实现设计。
- 为单个 AR 编写代码层实现设计，并把测试设计作为 AR 设计的一部分。
- 按 TDD 执行实现任务，并保留 RED / GREEN / REFACTOR 证据。
- 对测试有效性、代码质量、完成状态做独立审查。
- 对 DTS / Hotfix 做复现、根因分析和最小安全修复边界确认。

### 1.3 DevFlow 的基本流程

普通 AR 的主流程：

```text
需求澄清
  -> 规格评审
  -> AR 实现设计
  -> AR 设计评审
  -> TDD 实现
  -> 测试有效性审查
  -> 代码检视
  -> 完成门禁
  -> 收尾
```

如果影响组件边界，会在规格评审后插入组件实现设计：

```text
需求澄清
  -> 规格评审
  -> 组件实现设计
  -> 组件设计评审
  -> AR 实现设计
  -> 后续实现与检查
```

如果是 DTS / Hotfix，会先做问题分析：

```text
问题复现
  -> 根因分析
  -> 最小修复边界
  -> 进入 AR 设计或 TDD 实现
  -> 后续检查与收尾
```

### 1.4 使用时的基本原则

- 不知道入口时，直接说明目标，让 AI 判断应该进入哪个 DevFlow 节点。
- 需求规格未通过评审前，不进入设计。
- 组件实现设计未通过评审前，不进入依赖它的 AR 实现设计。
- AR 实现设计未通过评审前，不进入 TDD 实现。
- TDD 完成后，不能直接进入代码检视，必须先做测试有效性审查。
- 代码检视通过后，不能直接宣布完成，必须经过完成门禁。
- SR 只做需求分析和可选组件设计修订，不在同一个 SR 工作项里直接进入实现。
- Hotfix 只压缩路径，不跳过复现、根因、测试检查、代码检视和完成门禁。

## 2. 使用场景说明

### 场景 1：新增组件，编写组件实现设计

适用情况：

当一个工作项会新增组件，或修改组件职责、SOA 接口、组件依赖、状态机、运行机制时，应该先通过 DevFlow 做组件实现设计，不能直接进入 AR 代码层实现设计。

关键流程：

```text
需求澄清 -> 规格评审 -> 组件实现设计 -> 组件设计评审 -> AR 实现设计
```

你可以这样说：

```text
你：
我要新增一个 XXX 组件，请按 DevFlow 先帮我澄清需求，并进入组件实现设计。

AI：
我会先判断这是 SR 分析还是 AR 实现工作项，澄清需求并生成 requirement.md。
规格评审通过后，如果确认影响组件边界，会进入组件实现设计，产出 component-design-draft.md，并派发独立组件设计评审。
```

产物结果：

- `features/<id>/requirement.md`
- `features/<id>/reviews/spec-review.md`
- `features/<id>/component-design-draft.md`
- `features/<id>/reviews/component-design-review.md`
- 收尾时同步到 `docs/component-design.md`

### 场景 2：修改组件接口或依赖关系

适用情况：

当 AR 不是新增组件，但会改 SOA 服务接口、参数语义、错误码、依赖方向、初始化顺序、状态机或运行时机制时，也属于组件影响场景。

关键流程：

```text
需求澄清 -> 规格评审 -> 组件实现设计修订 -> 组件设计评审 -> AR 实现设计
```

你可以这样说：

```text
你：
这个 AR 会修改 XXX 组件对外接口，请按 DevFlow 判断是否需要先修订组件实现设计。

AI：
我会先读取或建立需求规格，确认 Component Impact。
如果接口或依赖变化成立，会进入 component-impact 路径，先修订组件实现设计，再进入 AR 实现设计。
```

产物结果：

- 更新后的需求规格与影响判断
- `component-design-draft.md`
- 组件设计评审记录
- 后续 AR 实现设计输入

### 场景 3：普通 AR 功能实现

适用情况：

当需求已经被团队接受，且主要是既有组件内部行为变更，不影响组件职责、接口、依赖、状态机或运行机制时，走普通 AR 实现路径。

关键流程：

```text
需求澄清
  -> 规格评审
  -> AR 实现设计
  -> AR 设计评审
  -> TDD 实现
  -> 测试有效性审查
  -> 代码检视
  -> 完成门禁
  -> 收尾
```

你可以这样说：

```text
你：
我要实现 AR12345，需求背景是 XXX，所属组件是 YYY。请按 DevFlow 从需求澄清开始推进。

AI：
我会先把输入整理成 requirement.md，并明确范围、非范围、验收标准和追溯关系。
规格评审通过后，会进入 AR 实现设计，设计评审通过后再创建 task queue 并按 TDD 实现。
```

产物结果：

- `features/AR12345-<slug>/requirement.md`
- `features/AR12345-<slug>/ar-design-draft.md`
- `features/AR12345-<slug>/tasks.md`
- `features/AR12345-<slug>/task-board.md`
- `features/AR12345-<slug>/implementation-log.md`
- `features/AR12345-<slug>/reviews/`
- `features/AR12345-<slug>/evidence/`
- `features/AR12345-<slug>/completion.md`
- `features/AR12345-<slug>/closeout.md`
- 收尾时同步到 `docs/ar-specs/AR12345-<slug>.md`（从 `requirement.md` 升级）
- 收尾时同步到 `docs/ar-designs/AR12345-<slug>.md`（从 `ar-design-draft.md` 升级）

### 场景 4：只做 SR 需求分析，不进入实现

适用情况：

当输入是子系统级 SR，目标是澄清范围、影响组件、候选 AR 拆分，或者决定是否需要修订组件设计时，走 SR 需求分析路径。SR 不会在同一个工作项中直接进入 AR 实现、TDD、测试检查或代码检视。

关键流程：

```text
需求澄清 -> 规格评审 -> 可选组件实现设计 -> 分析收尾
```

你可以这样说：

```text
你：
我有一个 SR，需要先分析清楚子系统范围、受影响组件和候选 AR，请按 DevFlow 做需求分析，不要进入实现。

AI：
我会把 SR 输入澄清成 requirement.md，补充 Affected Components、AR Breakdown Candidates 和 Component Design Impact。
如果规格评审判断需要修订组件设计，会进入组件实现设计；否则直接进入分析收尾。
```

产物结果：

- `features/SR<id>-<slug>/requirement.md`
- `features/SR<id>-<slug>/reviews/spec-review.md`
- 可选的 `component-design-draft.md`
- `features/SR<id>-<slug>/closeout.md`
- closeout 中的 `AR Breakdown Candidates` 供需求负责人后续新建 AR 工作项

### 场景 5：DTS / Hotfix 问题修复

适用情况：

当输入是 DTS、线上问题、紧急缺陷或回归问题时，不能直接让 AI 改代码。应先复现问题、确认根因和最小安全修复边界，再决定回到 AR 设计或 TDD 实现。

关键流程：

```text
问题复现 -> 根因分析 -> 最小修复边界 -> TDD 实现 -> 测试有效性审查 -> 代码检视 -> 完成门禁 -> 收尾
```

你可以这样说：

```text
你：
DTS67890 描述的是 XXX 问题，请按 DevFlow 先做复现、根因分析和最小修复边界，不要直接改代码。

AI：
我会先建立问题修复包，包括 reproduction.md、root-cause.md 和 fix-design.md。
只有复现、根因和修复边界足够清楚后，才会进入 TDD 实现或回到 AR / 组件设计。
```

产物结果：

- `features/DTS67890-<slug>/reproduction.md`
- `features/DTS67890-<slug>/root-cause.md`
- `features/DTS67890-<slug>/fix-design.md`
- 后续实现、评审、完成门禁和收尾产物

### 场景 6：继续一个进行中的 work item

适用情况：

当一个 AR / DTS / SR 已经有过程产物，但你不确定当前应该继续写设计、做评审、实现、补证据还是收尾时，让 AI 先按 DevFlow 路由判断。

关键流程：

```text
读取 progress.md / reviews / evidence -> 判断当前阶段 -> 路由到唯一下一步
```

你可以这样说：

```text
你：
继续 AR12345，请按 DevFlow 判断当前应该进入哪个阶段，然后推进下一步。

AI：
我会先读取 progress.md、reviews、evidence 和 completion 状态。
如果阶段清晰，会进入唯一下一步；如果证据冲突，会停下来说明冲突并回到路由判断。
```

产物结果：

- 更新后的 `progress.md`
- 对应阶段的新增或修订产物
- 必要时新增 review / gate 记录

### 场景 7：AR 设计已经完成，开始 TDD 实现

适用情况：

当 AR 实现设计和 AR 设计评审已经通过，需要把设计映射成任务队列并按 TDD 实现时，进入实现阶段。此时不能再随意扩大 AR 范围或补充未批准的新行为。

关键流程：

```text
AR 设计评审通过 -> 创建 / 校验 tasks.md -> 锁定 Current Active Task -> RED -> GREEN -> REFACTOR -> 测试有效性审查
```

你可以这样说：

```text
你：
AR12345 的 AR 设计已经评审通过，请按 DevFlow 创建任务队列，并开始第一个 TDD task。

AI：
我会先校验 ar-design-draft.md 和 ar-design-review.md，再创建或检查 tasks.md / task-board.md。
锁定唯一 Current Active Task 后，按 RED / GREEN / REFACTOR 执行，并记录 fresh evidence。
```

产物结果：

- `tasks.md`
- `task-board.md`
- 测试代码和生产代码变更
- `implementation-log.md`
- `evidence/{unit,integration,static-analysis,build}/`
- 下一步 `test-check`

### 场景 8：代码已经写完，判断是否可以完成

适用情况：

当实现已经完成并有测试证据，但还没有独立 test-check、code-review、completion-gate 时，不能直接宣布完成。

关键流程：

```text
测试有效性审查 -> 代码检视 -> 完成门禁 -> 收尾
```

你可以这样说：

```text
你：
AR12345 代码已经实现并跑过测试，请按 DevFlow 检查是否可以完成。

AI：
我会先确认是否已有 implementation-log 和 fresh evidence。
然后派发测试有效性审查，通过后进入代码检视；代码检视通过后，再运行完成门禁确认是否可以收尾。
```

产物结果：

- `reviews/test-check.md`
- `reviews/code-review.md`
- `completion.md`
- `closeout.md`
- 长期资产同步到 `docs/`

### 场景 9：只想评审某份产物

适用情况：

当你已经有某份规格、组件设计、AR 设计、测试或代码实现，需要 AI 按 DevFlow 做独立评审时，可以直接说明评审对象。评审者不会顺手修改被评审产物，只会给 verdict、findings 和下一步。

关键流程：

```text
读取被评审产物 -> 多维度审查 -> 输出 review record -> 给出唯一下一步
```

你可以这样说：

```text
你：
请按 DevFlow review 这份 AR 实现设计，重点检查测试设计章节是否足够支撑 TDD。

AI：
我会作为独立 reviewer 读取 ar-design-draft.md、requirement.md 和组件设计，检查设计完整性、组件一致性、嵌入式风险和测试设计充分性。
评审完成后会输出 ar-design-review.md，并给出通过、需修改或阻塞结论。
```

产物结果：

- 对应的 `reviews/<review-type>.md`
- 结构化 findings
- 唯一的 `next_action_or_recommended_skill`

## 3. FAQ

### 3.1 我不知道该用哪个 DevFlow skill，怎么办？

直接描述你的目标和工作项，例如：

```text
请按 DevFlow 继续 AR12345，判断当前应该进入哪个阶段。
```

AI 会先判断是可以直接进入某个节点，还是需要通过路由节点读取工件后再决定。

### 3.2 什么情况下需要先做组件实现设计？

出现以下任一情况时，通常需要先做组件实现设计：

- 新增组件。
- 修改组件职责或非职责。
- 修改 SOA 接口、Topic、API、错误码或语义契约。
- 修改组件依赖方向、初始化 / shutdown 顺序。
- 修改状态机或运行时机制。
- 现有 `docs/component-design.md` 缺失、过期或与代码明显不一致。

如果只是组件内部局部实现变化，通常进入 AR 实现设计即可。

### 3.3 组件实现设计和 AR 实现设计有什么区别？

组件实现设计描述组件本身，包括职责、接口、依赖、数据 / 状态、运行机制、并发、资源、错误处理以及对 AR 设计的约束。

AR 实现设计描述单个 AR 如何落到代码，包括受影响文件、控制流、数据结构、接口签名草案、异常路径和测试设计章节。

简单说：组件实现设计是长期组件资产，AR 实现设计是单个工作项的代码层设计。

### 3.4 SR 能不能直接进入实现？

不能。SR 走 `requirement-analysis` 路径，只负责澄清子系统级范围、受影响组件、候选 AR 和可选组件设计修订。SR 收尾后，候选 AR 由需求负责人新建为独立 AR 工作项，再重新进入 DevFlow 实现路径。

### 3.5 Hotfix 能不能跳过评审和完成门禁？

不能。Hotfix 可以更聚焦，但不能跳过质量门禁。至少需要复现或记录无法复现原因、根因分析、最小安全修复边界、TDD 证据、测试有效性审查、代码检视和完成门禁。

### 3.6 `auto mode` 是不是表示 AI 可以跳过确认？

不是。`auto mode` 只是执行模式偏好，不代表可以跳过评审、门禁、证据或团队角色确认。涉及业务判断、架构拍板、跨组件协调、接口契约变化时，AI 仍应停下并要求人工确认。

### 3.7 已经写完代码了，还需要走哪些检查？

通常仍需要：

```text
测试有效性审查 -> 代码检视 -> 完成门禁 -> 收尾
```

测试通过只能说明某些命令通过，不等于测试足够有效，也不等于代码质量、嵌入式风险和完成证据都满足要求。

### 3.8 为什么测试通过后还要做 test-check？

因为 TDD 中写出的测试不天然等于有效测试。`test-check` 会独立检查：

- RED 是否真的失败过。
- GREEN evidence 是否新鲜。
- 测试是否覆盖需求、边界、异常和嵌入式风险。
- 断言是否能证明行为，而不只是证明代码被调用。
- mock 是否越过真实边界。

### 3.9 为什么 code-review 通过后还要 completion-gate？

代码检视关注代码质量和设计一致性；完成门禁关注整个工作项是否可以宣告完成。completion-gate 会检查上游 review 是否齐全、本轮验证命令是否新鲜、嵌入式风险是否无未解释 critical 项、task-board 是否还有未完成任务。

### 3.10 DevFlow 会生成哪些主要产物？

常见产物包括：

- `requirement.md`：需求规格。
- `traceability.md`：追溯关系。
- `progress.md`：当前阶段和下一步。
- `component-design-draft.md`：组件实现设计草稿。
- `ar-design-draft.md`：AR 实现设计草稿，含测试设计章节。
- `tasks.md` / `task-board.md`：实现任务队列。
- `implementation-log.md`：实现记录和证据摘要。
- `reviews/*.md`：规格、组件设计、AR 设计、测试有效性、代码检视记录。
- `evidence/`：RED / GREEN / build / static analysis 等证据。
- `completion.md`：完成门禁记录。
- `closeout.md`：收尾记录。
- `docs/component-design.md`、`docs/ar-specs/` 和 `docs/ar-designs/`：收尾后同步的长期资产（component-design 描述组件、ar-specs 描述 AR 需求规格、ar-designs 描述 AR 实现设计）。

### 3.11 如果某个 review 不通过怎么办？

按 review finding 回到对应上游节点修订。例如：

- 规格评审不通过，回 `devflow-specify`。
- 组件设计评审不通过，回 `devflow-component-design`。
- AR 设计评审不通过，回 `devflow-ar-design`。
- 测试有效性审查不通过，回 `devflow-tdd-implementation`。
- 代码检视不通过，回 `devflow-tdd-implementation`。

修订后重新评审，不能绕过。

### 3.12 可以直接让 AI 从中间阶段开始吗？

可以，但前提是上游工件和评审记录存在且通过。例如你可以说：

```text
AR12345 的规格和 AR 设计都已通过评审，请按 DevFlow 从 TDD 实现继续。
```

AI 应先读取证据确认阶段合法。如果证据缺失或冲突，会回到路由判断或上游节点补齐。

### 3.13 DevFlow 适合极小改动吗？

适合，但可以走 `lightweight` 路径压缩文档量。压缩的是文档篇幅，不是质量底线。traceability、测试证据、review 和 completion 仍然要保留。

### 3.14 DevFlow 不适合什么场景？

DevFlow 不适合：

- 还没决定是否要做的产品发现。
- 没有被团队接受的需求方向探索。
- 系统级、集成级、验收级测试流程本身。
- 需要跨多个 work item 的项目管理或优先级排序。
- 让 AI 替业务负责人或架构负责人做最终拍板。
