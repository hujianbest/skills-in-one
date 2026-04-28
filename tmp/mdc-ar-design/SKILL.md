---
name: mdc-ar-design
description: AR 级实现设计技能。生成/更新 AR 实现设计文档，包含功能点分解、实现设计、接口描述、代码设计、MDC场景分析和测试设计。适用于架构设计已批准（或仅需 AR 级设计）时生成 AR 文档、用户请求生成/更新 AR 文档、设计评审被退回需修订的场景。触发词：生成AR、更新AR、技术设计文档、AR文档、需求实现设计。不适用需要架构级决策（→ mdc-arch-design）、规格仍是草稿（→ mdc-specify）、阶段不清（→ using-mdc-workflow）。
---

# AR Design Doc Generator

AR 级实现设计技能。在架构设计已批准后（或标准/lightweight profile 直接进入时），生成 AR 实现设计文档。产出经评审确认后进入 `mdc-tasks`。

**两级设计区分**：
- **组件级设计**（`mdc-arch-design`）：定义组件基线，仅新增组件时执行
- **AR级设计**（本技能）：定义本轮 AR 的增量实现，**每轮 AR 必经**

**基线来源**（按优先级）：
1. 若 `docs/<component-name>-design.md` 存在（mdc-arch-design 已执行）：引用组件基线，描述增量修改
2. 若组件已有代码但无 design doc：基于现有代码逆向分析，完整描述本轮实现
3. 无基线无代码：Red Flag，应先走 mdc-arch-design

## When to Use

适用：
- 架构设计已批准，需生成 AR 实现设计文档（引用组件基线做增量）
- 标准或 lightweight profile，需求规格已批准且不涉及新增组件（基于现有代码做 AR 实现）
- `mdc-review`(ar-design) 返回 `需修改`，需修订 AR 设计
- 用户请求生成/更新 AR 文档

不适用：涉及新增组件/模块/接口需架构级决策 → `mdc-arch-design`；规格仍是草稿 → `mdc-specify`；仅需设计评审 → `mdc-review`；阶段不清 → `using-mdc-workflow`。

## Hard Gates

- AR 设计未评审获批前，不得拆解任务或编写实现代码
- 未经 `using-mdc-workflow` 入口判断，不直接开始 AR 设计

## Workflow

### 1. 确定基线来源与文档类型 ⬅ 当前步骤

**todo**: 确定基线来源，询问用户并确定文档类型

**1.1 确定基线来源**（按优先级检查）：

1. 检查 `docs/<component-name>-design.md` 是否存在
   - 存在 → 基线模式 = **引用组件基线**，AR 设计需标注"在组件基线上做增量"
   - 不存在 → 继续
2. 检查组件代码目录是否存在且非空
   - 存在 → 基线模式 = **基于现有代码**，AR 设计需逆向分析代码结构
   - 不存在 → **Red Flag**：新增组件但无组件基线，应先走 `mdc-arch-design`

**1.2 询问用户**：

> 请选择文档类型并提供相应信息：
> - **生成新文档**：请提供需求描述（背景、功能、性能要求、约束条件），以及代码路径
> - **更新已有文档**：请提供代码修改所在的目录路径（无需需求描述）和AR文档路径
> 
> **示例回复（生成模式）**：
> ```
> 文档类型：生成新文档
> 需求描述：实现MCU异常后自动复位功能...
> 代码路径：D:\project\mdc\mcu
> ```
> 
> **示例回复（更新模式）**：
> ```
> 文档类型：更新文档
> 代码路径：D:\project\mdc\mcu，AR文档路径
> ```

**解析规则**：
- 判断文档类型：根据用户回复中是否包含"更新"、"修改"等词，或用户明确选择
- 生成模式：解析需求描述提取需求名称，路径优先使用用户提供的
- 更新模式：直接进入下一步，无需需求描述

### 2. 自动获取代码仓库信息

**todo**: 验证路径、获取Git修改、确定AR编号、需求名称、作者

系统自动完成（无需用户参与）：

#### 2.1 路径有效性检查

**todo**: 验证代码仓库路径有效性

1. 用户提供路径后，验证该路径是否可用git命令
2. 如果当前路径不能使用git命令，逐级向上查询父目录
3. **找到git仓库后**：向用户确认"是否使用 `{找到的git仓库路径}` 作为代码根目录？"
4. 用户确认后使用该路径；用户否认则继续向上查找或请求手动指定
5. 如果用户未提供路径，使用当前工作目录，向上查找最近git仓库

#### 2.2 获取 Git 修改信息

**todo**: 查看代码修改内容

使用 git 命令查看修改内容，详见 [git-commands.md](references/git-commands.md)

#### 2.3 获取 AR 编号

**todo**: 确定 AR 编号

- **生成模式**：从 git commit 获取，或使用当天日期+00001
- **更新模式**：从现有AR文档中直接读取AR编号

#### 2.4 获取需求名称

**todo**: 提取需求名称

- **生成模式**：从 git commit 消息和需求描述中提取关键词组成需求名称
- **更新模式**：从现有AR文档中直接读取需求名称

#### 2.5 获取作者信息

**todo**: 获取文档作者

- **生成模式**：运行 `git config user.name` 自动获取用户名
- **更新模式**：从现有AR文档中直接读取作者信息，运行 `git config user.name` 自动获取用户名，作者可以有多个

### 3. 生成/更新 AR 文档

#### 3.1 确定 AR 文档工作路径

**todo**: 确定 AR 目录和文档工作路径

1. AR 目录由 `using-mdc-workflow` 在 workflow 开始时锁定为 `features/<active>/`，其中 `<active>` 形如 `<TICKET>-kebab-slug/`
2. AR 设计文档工作路径为 `features/<active>/ar-design.md`
3. 归档路径（finalize 时由 mdc-finalize 执行）：`docs/ar_design/MDC_CORE_5.0.0_AR{编号}_{需求名称}.md`

#### 3.2 生成新文档

**适用场景**：用户选择生成新文档

1. 文件保存路径：`features/<active>/ar-design.md`
2. **基线引用（重要）**：
    - 若基线模式 = 引用组件基线：文档开头须声明"组件基线：`docs/<component-name>-design.md`"，功能点编号对齐基线的功能列表，接口修改限定为新增/修改
    - 若基线模式 = 基于现有代码：文档开头须声明"基于现有代码逆向分析"，功能点独立编号
3. **命名规范（重要）**：
    - 变量名、函数名：**小驼峰命名** (camelCase)，如 `mcuRunTime`、`notifyCc2SS`
    - 类名：**大驼峰命名** (PascalCase)，如 `UserService`
    - 常量：**小驼峰命名**，如 `maxCount`

#### 3.3 更新已有文档

**适用场景**：用户选择更新已有文档（简化流程，无需需求描述）

1. **收集代码修改信息**：获取 git diff 内容，了解本次代码变更
2. **读取现有 AR 文档**：从 `features/<active>/ar-design.md` 读取
3. **对比差异**：比较代码修改内容与 AR 文档描述的差异
4. **更新文档**：
    - 在修订记录中新增一条变更记录（包含变更人、变更时间、变更内容描述）
    - 根据代码差异更新文档中的：设计方案、接口描述、流程图、时序图等所有相关内容
    - 保持原有文档结构不变

#### 3.4 文件存在处理逻辑

| 场景 | 处理方式 |
|------|----------|
| `features/<active>/ar-design.md` 已存在 | 修改现有文件，在修订记录中新增一条 |
| `features/<active>/ar-design.md` 不存在 | 新建文件 |

**模板**：生成AR文档时请参考 [ar-template.md](references/ar-template.md) 模板内容，按照其结构填充具体需求实现设计内容。

**参考示例**：实际 AR 文档案例见 [AR20251013933991_Sentry_SafetyIsland.md](references/AR20251013933991_Sentry_SafetyIsland.md)，有不确定内容时可加载，参考格式

**注意**：生成最终 AR 文档时，**不要包含**模板中的"变量替换规则"、"命名规则"、"Document Format Requirements"、"简介"章节以及任何的"AI提示"，这些仅供 AI 参考。

### 4. 提交评审

**todo**: 将 AR 设计提交 `mdc-review`(ar-design) 评审

AR 设计文档生成/更新后，**不得直接进入 `mdc-tasks`**，必须经过正式评审：

1. AR 设计完成后，父会话构造 review request，派发独立 reviewer subagent
2. Reviewer 按 `references/ar-design-review-checklist.md` 执行 9 维度评审
3. 根据评审结论处理：
   - `通过` → 进入 AR 设计真人确认
   - `需修改` → 回到本 skill 修订 AR 文档，修订后重新提交评审
   - `阻塞` → 回到本 skill 或回退到 `mdc-arch-design`（若存在架构级决策问题）

**Self-Check（提交评审前自检）**：

在提交评审前，按以下清单自检 AR 文档质量：

- [ ] 每个功能点可回指到规格/架构设计的具体条目（AR1）
- [ ] 功能点分解覆盖所有需求，优先级明确，粒度可独立测试（AR2）
- [ ] 实现思路包含关键设计要点，开发者可直接编码（AR3）
- [ ] 每个接口有完整的参数名/类型/描述/返回值（AR4）
- [ ] MDC 五大场景（并发、启动退出、休眠唤醒、可靠性、SELinux）均有分析（AR5）
- [ ] 正常流程 + 异常流程均有设计（AR6）
- [ ] UT/接口测试/异常场景测试覆盖功能点，逻辑覆盖度明确（AR7）
- [ ] 包结构、类设计、类图与实现对应，命名符合规范（AR8）
- [ ] 基线一致性（AR9）：组件基线存在时功能点编号对齐基线且接口修改为增量式；无基线有代码时设计与现有结构一致；无基线无代码→红旗
- [ ] 无模板占位符残留（RA10）
- [ ] 无架构级决策泄漏到 AR 中（RA7）

## 错误处理

| 场景 | 处理方式 |
|------|----------|
| 路径不存在 | 搜索相似路径 →找不到则仅基于需求生成，告知用户 |
| 非 git 仓库 | 告知用户，仅基于需求生成 |
| 无 git 修改 | 告知用户，仅基于需求生成 |
| 获取作者失败 | 使用 "Unknown" 作为默认值 |
| `features/<active>/` 未锁定 | 告知用户应通过 `using-mdc-workflow` 入口 |

## Output Contract

- AR 设计文档（`features/<active>/ar-design.md`）
- `features/<active>/progress.md` 更新：`Current Stage` → `mdc-ar-design`；`Next Action Or Recommended Skill` → `mdc-review`(ar-design)
- **注意**：AR 设计归档（`docs/ar_design/MDC_CORE_5.0.0_AR{编号}_{需求名称}.md`）由 `mdc-finalize` 在 closeout 时执行

## 和其他 Skill 的区别

| 易混淆 skill | 区别 |
|---|---|
| `mdc-arch-design` | arch-design 是组件级（仅新增组件时执行），产出组件基线；本 skill 是 AR 级（每轮 AR 必经），基于组件基线或现有代码做增量实现设计 |
| `mdc-review` | 本 skill 负责起草设计；review 负责评审 |
| `mdc-specify` | specify 回答"做什么"；本 skill 回答"如何做（AR 级增量实现）" |
| `mdc-tasks` | 设计批准后才拆任务 |

## Reference Guide

| 文件 | 用途 |
|---|---|
| `references/ar-template.md` | AR 文档模板 |
| `references/git-commands.md` | Git 命令参考 |
| `references/AR20251013933991_Sentry_SafetyIsland.md` | AR 文档示例 |

## Red Flags

- AR 文档包含模板中的 AI 提示章节
- 架构级决策出现在 AR 文档中（应属于 mdc-arch-design）
- 缺少 MDC 场景分析（并发、启动退出、休眠唤醒、可靠性、SELinux）
- 组件基线存在但 AR 设计未引用基线，或功能编号与基线不对齐
- 无组件基线也无代码时直接做 AR 设计（应先走 mdc-arch-design）
- AR 设计中出现组件级架构决策（新增组件/模块/系统接口定义，应回退到 mdc-arch-design）

## Verification

- [ ] AR 文档已生成/更新到 `features/<active>/ar-design.md`
- [ ] AR 文档不包含 AI 提示标记
- [ ] Self-Check 清单已完成
- [ ] `features/<active>/progress.md` 已按 canonical schema 更新
- [ ] handoff 目标唯一指向 `mdc-review`(ar-design)
