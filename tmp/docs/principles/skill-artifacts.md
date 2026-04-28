# MDC Workflow 交付件规则

- 定位：项目级原则文档，定义在 MDC workflow 下，**过程交付件**与**项目长期资产**应该如何组织、命名与流转。
- 关联：
  - MDC 工作流编排：`mdc-workflow/using-mdc-workflow/SKILL.md`

## 定位

本文回答一个具体问题：**在 MDC 组件开发过程中，工件应该放在哪里、叫什么名字、什么时候从过程交付件晋升为长期资产。**

它不替代各 skill 内的 progress schema、verdict 词表、record_path 语义等运行时约束；它只回答"工件物理布局与生命周期"这一层。

## 核心原则

组件仓库下，`docs/` 和 `features/` 与 `src/`、`test/` 同级：

```text
<component-repo>/
  src/
  test/
  docs/        ← 项目长期资产
  features/    ← 过程交付件
```

| 目录 | 性质 | 时间尺度 | 演化方式 |
|---|---|---|---|
| `docs/` | **项目长期资产** | 跨多个 AR 周期 | 慢、累积，被多个 AR 修改 |
| `features/` | **过程交付件** | 单个 AR 周期内 | 一次性产出，closeout 后基本不动 |

一句话：

> `docs/` 回答"组件现在是什么样、为什么是这样"；`features/` 回答"这一轮 AR 做了什么、怎么做的、谁批准的"。

**AR 是分配需求的概念，一个 AR 只归属一个组件。** 因此 `features/` 下的每个 AR 目录天然属于当前组件仓库，不存在跨组件的 AR。

## 总则

1. 项目根目录 `AGENTS.md` 可声明路径映射覆盖默认路径，各 skill 遵循"若 AGENTS.md 声明了等价路径，按映射保存"。
2. 文件名使用小写英文、连字符分隔，避免空格和特殊字符。
3. 每个交付件文档必须包含 `状态:` 字段，取值为 `草稿` / `已批准`。

## `docs/` — 项目长期资产

`docs/` 下按类型拆分子目录，每个组件一份 spec + 一份 design，另设 `ar_design/` 保存 AR 设计归档：

**两级设计区分**：
- **`<component-name>-design.md`**（组件实现设计说明书）：组件级基线，定义"这个组件是什么、包含什么、怎么组织"。**仅新增组件时由 `mdc-arch-design` 产出**，后续 AR 周期的增量由 closeout 同步。
- **`ar_design/` 下的归档**（AR 实现设计文档）：AR 级增量设计，定义"本轮 AR 做了什么增量实现"。**每轮 AR 都由 `mdc-ar-design` 产出**，引用组件基线（若存在）或基于现有代码。

```text
docs/
  <component-name>-spec.md      # 组件规格
  <component-name>-design.md    # 组件设计（整合 ADR / C4 / 接口）
  ar_design/                    # AR 设计归档（finalize 后从 features/ 晋升）
    MDC_CORE_5.0.0_AR{编号}_{需求名称}.md
```

示例（组件名为 `lidar-driver`，AR 编号为 20260421964780）：

```text
docs/
  lidar-driver-spec.md
  lidar-driver-design.md
  ar_design/
    MDC_CORE_5.0.0_AR20260421964780_MCU自复位机制.md
```

约束：

- **文件名即组件名**，kebab-case，与仓库名/模块名一致。
- **`<component-name>-spec.md`** 是组件需求规格的长期归宿。AR 周期内的 `ar-spec.md` 经 closeout 后，增量同步到本文件。
- **`<component-name>-design.md`** 是组件实现设计说明书的长期归宿（由 `mdc-arch-design` 产出，**仅新增组件时**），整合以下内容：
  - 组件上下文视图与全量功能列表
  - 开发视图（代码结构模型、实现模型/类图、数据设计、构建依赖）
  - 运行视图（交互机制、通信机制、数据流机制、并发机制）
  - 接口定义（Service/Topic/API/内部接口，含并发约束声明）
  - 功能列表详设（场景流程、AR 需求追溯）
  - 软件单元设计（类列表、函数级设计）
  - 测试设计与成本评估
  - ADR 编号在本文件内分配，组件内顺序号。被替代时更新 supersedes / superseded-by 双向链接。ADR 永不删除、永不重新编号。
- ADR 编号在本文件内分配，组件内顺序号。被替代时更新 supersedes / superseded-by 双向链接。ADR 永不删除、永不重新编号。
- **`docs/ar_design/`** 是 AR 设计文档的长期归档目录。finalize 后，`features/<active>/ar-design.md` 复制到本目录，文件名格式为 `MDC_CORE_5.0.0_AR{编号}_{需求名称}.md`。该归档保留完整 AR 设计，便于跨 AR 周期回溯。
- `CHANGELOG.md` 仍放仓库根（Keep a Changelog 惯例）。

### `docs/ar_design/` AR 设计归档命名

文件名格式：`MDC_CORE_5.0.0_AR{编号}_{需求名称}.md`

- `{编号}`：AR 编号，如 `20260421964780`
- `{需求名称}`：中文需求名称，直接使用原始需求标题
- 示例：`MDC_CORE_5.0.0_AR20260421964780_MCU自复位机制.md`

### 代码命名规范

- 变量名、函数名：**小驼峰命名** (camelCase)，如 `mcuRunTime`、`notifyCc2SS`
- 类名：**大驼峰命名** (PascalCase)，如 `UserService`
- 常量：**小驼峰命名**，如 `maxCount`

## `features/` — 过程交付件

每个 AR 一个目录：

```text
features/
  003-rate-limiting/
    README.md                  # AR 入口 + 状态总览
    ar-spec.md                 # 需求规格（本轮 AR 的范围与上下文）
    arch-design-record.md      # 架构决策记录（mdc-arch-design 过程交付件，仅 full profile 涉及新增组件时）
    ar-design.md               # AR 级实现设计（引用组件基线）
    tasks.md                   # 任务拆解
    task-board.md              # 可选；用于 task-to-task 自动推进
    progress.md                # AR 范围内的 task-progress（唯一权威）
    reviews/
      spec-review-2026-04-18.md
      ar-design-review-2026-04-19.md
      tasks-review-2026-04-19.md
      code-review-task-001.md
      test-review-task-001.md
      traceability-review.md
    approvals/
      ar-spec-approval-2026-04-18.md
      ar-design-approval-2026-04-19.md
      tasks-approval-2026-04-20.md
    verification/
      regression-2026-04-21.md
      completion-2026-04-21.md
    evidence/                  # fresh evidence（命令输出 / 日志 / 构建日志）
      task-001-red.log
      task-001-green.log
    closeout.md                # finalize 的 closeout pack
```

约束：

- **AR 目录是自包含的工件包**。同一 AR 的所有过程证据都聚在一个目录里，便于 PR diff、review、归档与移交。
- **`README.md` 是 AR 入口**，必须列出：AR 状态、关键日期、ar-spec / ar-design / tasks 文件路径、当前 active task、closeout 状态。
- **`progress.md` 是该 AR 的唯一 task-progress 落点**。仓库根**不再保留全局 `task-progress.md`**。
- **closeout pack 文件名为 `closeout.md`**。
- **不引入 `archived/` / `done/` 子目录**。closeout 后的 AR 平铺保留在 `features/` 下，状态从 `closeout.md` 内读取。

## features/ 目录命名

`features/<TICKET>-kebab-slug/`

`<TICKET>` 取自上下文中的 AR 或 DTS 编号：

| 类型 | 格式 | 示例 |
|------|------|------|
| AR（需求分配） | `ARXXXX` | `features/AR1234-lidar-comm-loss/` |
| DTS（问题单） | `DTSXXXX` | `features/DTS5678-packet-drop-fix/` |

规则：

- 目录名中的编号从上下文信息（用户输入、工单链接、issue 描述等）中提取。如果上下文中找不到 AR 或 DTS 编号，**必须询问用户**，不可自行编造。
- `slug`：kebab-case 短描述，概括本项工作内容。
- 目录名一旦创建不再改名（即使后续发现编号有误，也通过 `README.md` 内修正说明解决）。

## features/ 目录内固定文件名

| 文件 | 必需性 | 说明 |
|---|---|---|
| `README.md` | 必需 | 入口与状态总览 |
| `ar-spec.md` | 必需 | `mdc-specify` 输出 |
| `arch-design-record.md` | full profile 涉及新增组件时必需 | `mdc-arch-design` 过程交付件（组件级基线决策） |
| `ar-design.md` | 必需 | `mdc-ar-design` 输出 |
| `tasks.md` | 必需 | `mdc-tasks` 输出 |
| `progress.md` | 必需 | task-progress |
| `closeout.md` | finalize 后必需 | `mdc-finalize` 输出 |
| `task-board.md` | 可选 | 当需要 task-to-task 自动推进时 |

## 各阶段交付件命名规则

### 1. 需求规格 — `ar-spec.md`

本轮 AR 的需求规格，描述变更范围与上下文。引用 `docs/<component-name>-spec.md` 作为基线。

需求条目使用结构化 ID：

| 前缀   | 类型       |
| ------ | ---------- |
| `FR-`  | 功能需求   |
| `NFR-` | 非功能需求 |
| `CON-` | 约束条件   |
| `IFR-` | 接口需求   |
| `ASM-` | 假设条件   |
| `EXC-` | 排除项     |

### 2. AR 级实现设计 — `ar-design.md`

`mdc-ar-design` 输出，AR 级增量实现设计文档。基线来源取决于场景：
- 若 `docs/<component-name>-design.md` 存在（mdc-arch-design 已执行）：引用组件基线，描述增量修改
- 若组件已有代码但无 design doc：基于现有代码逆向分析，完整描述本轮实现

文档内含修订记录表，每次更新新增一行：

| 字段 | 说明 |
|------|------|
| 日期 | 修订日期 |
| 版本 | 1.00 → 1.01 → ... |
| 修改章节 | 修改的章节号 |
| 修改说明 | 变更描述 |
| 作者 | 修订人 |

### 3. 任务计划 — `tasks.md`

任务 ID 使用稳定标识符：`T1` / `T-APP-1` / `TASK-01` 等。

每个任务必须包含：Goal、需求追溯、设计追溯、Dependencies、涉及工件、验证方式、完成定义。

任务状态机：`pending` → `ready` → `in_progress` → `done`（或 `blocked` / `cancelled`），同一时刻仅允许一个 `in_progress`。

### 4. 评审记录 — `reviews/`

模式：`<kind>-<scope>-YYYY-MM-DD.md`

| 交付件 | 命名模式 | 示例 |
|--------|----------|------|
| 需求规格评审 | `spec-review-YYYY-MM-DD.md` | `reviews/spec-review-2026-04-18.md` |
| 架构设计评审 | `arch-design-review-YYYY-MM-DD.md` | `reviews/arch-design-review-2026-04-18.md` |
| AR 设计评审 | `ar-design-review-YYYY-MM-DD.md` | `reviews/ar-design-review-2026-04-19.md` |
| 任务评审 | `tasks-review-YYYY-MM-DD.md` | `reviews/tasks-review-2026-04-19.md` |
| 代码评审 | `code-review-task-NNN.md` | `reviews/code-review-task-001.md` |
| 测试评审 | `test-review-task-NNN.md` | `reviews/test-review-task-001.md` |
| 追溯链评审 | `traceability-review.md` | `reviews/traceability-review.md` |

评审结论取值：`通过` / `需修改` / `阻塞`。

发现项分类：`USER-INPUT`（需人工处理）或 `LLM-FIXABLE`（可自动修复）。

同日多份按需追加 `-NN` 序号后缀。

### 5. 批准记录 — `approvals/`

模式：`<kind>-approval-YYYY-MM-DD.md`

| 交付件 | 命名模式 | 示例 |
|--------|----------|------|
| 需求规格批准 | `ar-spec-approval-YYYY-MM-DD.md` | `approvals/ar-spec-approval-2026-04-18.md` |
| 架构设计批准 | `arch-design-approval-YYYY-MM-DD.md` | `approvals/arch-design-approval-2026-04-18.md` |
| AR 设计批准 | `ar-design-approval-YYYY-MM-DD.md` | `approvals/ar-design-approval-2026-04-19.md` |
| 任务批准 | `tasks-approval-YYYY-MM-DD.md` | `approvals/tasks-approval-2026-04-20.md` |

可接受的批准证据（满足任一即可）：

- 批准记录包含 `Human Confirmation: Yes`
- 指定审批人的 PR 审批已通过
- 工单状态变为 `Design Approved`
- 文档 `状态:` 字段标记为 `已批准` 或 `Status: Approved`

### 6. 验证记录 — `verification/`

模式：`<kind>-YYYY-MM-DD.md`

| 交付件 | 命名模式 | 示例 |
|--------|----------|------|
| 回归验证 | `regression-YYYY-MM-DD.md` | `verification/regression-2026-04-21.md` |
| 完成验证 | `completion-YYYY-MM-DD.md` | `verification/completion-2026-04-21.md` |

## 中央协调工件

### progress.md

存放位置：`features/<active>/progress.md`（**仓库根不再保留全局 `task-progress.md`**）。

## 追溯链规则

交付件之间通过以下机制保持追溯：

1. **需求→设计**：ar-design 引用 ar-spec 中的需求 ID（如 `FR-001`）
2. **设计→任务**：任务条目引用 ar-design 章节号
3. **任务→实现**：代码变更关联任务 ID
4. **实现→验证**：验证记录引用任务 ID 和代码变更
5. **finalize 内嵌追溯链检查**：6 维评分（0-10），任一维度 < 6 阻断推进

## Promotion Rules（过程交付件 → 长期资产）

| 长期资产 | 修改时机 | 修改方式 |
|---|---|---|
| **`docs/<component-name>-spec.md`** | closeout 阶段同步 | `ar-spec.md` 中已批准的需求增量，由 closeout 同步到本文件 |
| **`docs/<component-name>-design.md`** | `mdc-arch-design` 直接写入；closeout 阶段增量同步 | `mdc-arch-design` 直接产出本文件；`ar-design.md` 中已批准的设计增量，由 closeout 增量同步到本文件；ADR 状态随同步更新 |
| **`docs/ar_design/MDC_CORE_5.0.0_AR{编号}_{需求名称}.md`** | closeout 阶段归档 | `ar-design.md` 整份复制到本路径，作为 AR 设计的完整归档 |

**统一由 closeout 阶段同步**（`docs/<component-name>-design.md` 除外，该文件由 `mdc-arch-design` 直接产出），理由：

- `docs/<component-name>-design.md` 由 `mdc-arch-design` 在架构设计阶段直接写入，后续 `ar-design.md` 的增量由 closeout 同步到本文件
- `docs/<component-name>-spec.md` 始终保持"已批准状态"，避免规格未通过前 `docs/` 已被改
- 多 AR 并行时降低 `docs/` 冲突频率。
- review 阶段评审范围聚焦 `features/<NNN>/`，不必横跨两个目录。

### `mdc-finalize` 的同步责任

`closeout.md` 必须显式列出本次 closeout 同步到 `docs/` 的所有路径，作为 release/docs sync 证据：

```markdown
## Release / Docs Sync

- Updated Docs:
  - `docs/lidar-driver-spec.md`（新增 FR-012 / 修改 FR-003）
  - `docs/lidar-driver-design.md`（新增 ADR-03，更新接口定义）
- Archived AR Design:
  - `docs/ar_design/MDC_CORE_5.0.0_AR20260421964780_MCU自复位机制.md`（归档自 `features/AR20260421964780-xxx/ar-design.md`）
- CHANGELOG: `CHANGELOG.md`（v1.5.0 入口）
```

如果同步项缺失，`mdc-finalize` 应判 `blocked` 并回 `using-mdc-workflow`。

## `AGENTS.md` 路径声明

`AGENTS.md` 中至少应声明：

```text
- ar spec path: features/<active>/ar-spec.md
- arch design record path: features/<active>/arch-design-record.md
- ar design path: features/<active>/ar-design.md
- task plan path: features/<active>/tasks.md
- progress path: features/<active>/progress.md
- review path: features/<active>/reviews/
- approval path: features/<active>/approvals/
- verification path: features/<active>/verification/
- closeout pack path: features/<active>/closeout.md
- component spec path: docs/<component-name>-spec.md
- component design path: docs/<component-name>-design.md
- ar design archive path: docs/ar_design/
- changelog path: CHANGELOG.md
```

`<active>` 在每个 workflow 周期开始时由 `using-mdc-workflow` 锁定为具体 AR 目录名。

## Lifecycle 总览

### Full Profile（涉及新增组件）

```text
[ 新工作项启动 ]
  └─> 在 features/<TICKET>-<slug>/ 下创建 README.md + ar-spec.md（来自 skill 模板）
       │
       ▼
[ mdc-specify ] ──> features/<active>/ar-spec.md（草稿）
       │              reviews/spec-review-YYYY-MM-DD.md
       │              approvals/ar-spec-approval-YYYY-MM-DD.md
       ▼
[ 规格真人确认 ]
       │
       ▼
[ mdc-arch-design ] ──> features/<active>/arch-design-record.md  ← 组件级基线决策
       │                 docs/<component-name>-design.md         ← 组件实现设计说明书（长期资产）
       │                 reviews/arch-design-review-YYYY-MM-DD.md
       │                 approvals/arch-design-approval-YYYY-MM-DD.md
       ▼
[ 架构设计真人确认 ] ← 组件基线确立
       │
       ▼
[ mdc-ar-design ] ──> features/<active>/ar-design.md  ← AR 级增量设计（引用组件基线）
       │                 reviews/ar-design-review-YYYY-MM-DD.md
       │                 approvals/ar-design-approval-YYYY-MM-DD.md
       ▼
[ AR设计真人确认 ]
       │
       ▼
[ mdc-tasks ] ────> features/<active>/tasks.md
       │              reviews/tasks-review-YYYY-MM-DD.md
       │              approvals/tasks-approval-YYYY-MM-DD.md
       ▼
[ 任务真人确认 ]
       │
       ▼
[ mdc-test-driven-dev / mdc-test-checker / mdc-code-review ]
       │              reviews/code-review-task-NNN.md
       │              reviews/test-review-task-NNN.md
       │              evidence/...
       ▼
[ mdc-finalize ] ──> features/<active>/verification/regression-...md
       │              features/<active>/verification/completion-...md
       │              features/<active>/closeout.md
       │              docs/<component-name>-spec.md（同步增量）
       │              docs/<component-name>-design.md（同步增量）
       │              docs/ar_design/MDC_CORE_5.0.0_AR{编号}_{需求名称}.md（归档 AR 设计）
       │              CHANGELOG.md
       ▼
[ closeout 完成 ] ──> features/<TICKET>-<slug>/ 进入只读状态
```

### Standard / Lightweight Profile（现有组件修改，无新增组件）

```text
[ 新工作项启动 ]
  └─> 在 features/<TICKET>-<slug>/ 下创建 README.md + ar-spec.md
       │
       ▼
[ mdc-specify ] ──> features/<active>/ar-spec.md（草稿）  ← standard profile；lightweight 可简化
       │              reviews/spec-review-YYYY-MM-DD.md
       │              approvals/ar-spec-approval-YYYY-MM-DD.md
       ▼
[ 规格真人确认 ]
       │
       ▼
[ mdc-ar-design ] ──> features/<active>/ar-design.md  ← AR 级增量设计（基于现有代码或 docs/<component-name>-design.md）
       │                 reviews/ar-design-review-YYYY-MM-DD.md
       │                 approvals/ar-design-approval-YYYY-MM-DD.md
       ▼
[ AR设计真人确认 ]
       │
       ▼
[ 后续同 full profile 的 mdc-tasks → ... → closeout ]
```

closeout 后 `features/<TICKET>-<slug>/` 进入只读状态，仅在以下情况修改 `README.md`：

- 该工作项涉及的设计被新工作项修改，加一行 backlink；
- 出 hotfix 复用了该 AR 的边界，加 incident 链接。

## Discipline Without Schema / CI

本约定不引入 frontmatter schema、JSON schema 或 CI lint。维持纪律的手段是：

1. **模板就是最强的强制力**。skill 内置的模板保持完整与最新；agent 与人创建工件时复制模板，骨架自然一致。项目可在 `AGENTS.md` 中声明等价覆盖路径。
2. **`README.md` 作为 AR 总览页**强制要求列出各阶段工件路径与状态，肉眼一看即可发现缺件。
3. **reviewer subagent 的 checklist 作为运行时强制**。各 review skill 中的 *Practical Checklist* 与 *Verification* 段，必须由 reviewer 逐条勾对实际工件。
4. **commit message 规范**：建议 commit message 显式 reference AR 目录（例如 `Refs: features/003-rate-limiting`），让 `git log` 自然成为过程证据流。

承认的剩余风险：当 AR 数到 30+ 时，纯靠纪律会出现散文式漂移（链接失效、component-spec 漏更新）。届时再考虑加一个超轻的 `scripts/artifact-check.sh`（不是 CI、不是 schema，就是 shell 扫一遍 broken link / closeout 缺件）。**不**提前引入。

## Red Flags

- closeout 时只写 `closeout.md`，未同步 `docs/<component-name>-spec.md` / `docs/<component-name>-design.md`，或未归档 `docs/ar_design/`。
- 把 closeout 后的 AR 移动到 `features/archived/`，破坏反向引用。
- 仓库根又出现了全局 `task-progress.md`（应只在 AR 目录内）。
- review / approval / verification 的记录散落到仓库级目录而不是 AR 目录内。
- AR 目录命名只用 slug 不带 AR/DTS 编号，导致无法追溯到工单系统。
- `docs/<component-name>-design.md` 内 ADR 被删除或重新编号。
- full profile 涉及新增组件时，`features/<active>/arch-design-record.md` 不存在。

## Verification

- [ ] 每个 active 工作项在 `features/` 下有自包含目录，且目录名形如 `<TICKET>-kebab-slug/`
- [ ] 目录名包含有效的 AR 或 DTS 编号
- [ ] AR 目录内 `README.md` / `ar-spec.md` / `ar-design.md` / `tasks.md` / `progress.md` 均存在
- [ ] 若为 full profile 且涉及新增组件，`features/<active>/arch-design-record.md` 存在
- [ ] AR 目录内 `reviews/` / `approvals/` / `verification/` 已收口，文件命名遵循约定
- [ ] closeout 后 `closeout.md` 已写，且 *Release / Docs Sync* 区块列出实际同步到 `docs/` 的路径及归档到 `docs/ar_design/` 的路径
- [ ] 仓库根没有遗留全局 `task-progress.md`
- [ ] `AGENTS.md` 已声明本约定要求的路径覆盖
