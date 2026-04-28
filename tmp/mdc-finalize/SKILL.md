---
name: mdc-finalize
description: 统一后端节点技能，按步骤执行回归门禁(regression)、完成门禁(completion)、收尾(finalize)。在 code-review 通过后依次推进，确保有足够最新证据才宣告任务完成并收尾。不适用判断追溯完整性（已内嵌）、阶段不清（→ using-mdc-workflow）。
---

# MDC Finalize

统一后端节点技能，将回归门禁、完成门禁和收尾合并为一个技能内部按步骤推进。code-review 通过后，依次执行：

1. 追溯链检查（内嵌）→ 2. 回归门禁 → 3. 完成门禁 → 4. 收尾

## When to Use

适用：code-review 通过后、用户要求回归验证或判断任务完成或收尾。

不适用：缺 code-review 记录 → `mdc-code-review`；阶段不清 → `using-mdc-workflow`。

## Hard Gates

 - 无 fresh evidence 不得宣称通过任何门禁
 - 上游 review/gate 记录缺失不通过
 - worktree-active 时 evidence 必须锚定同一 Worktree Path
 - 本轮没运行验证命令不得宣称完成

## Workflow

### 1. 追溯链检查（内嵌）

检查证据链完整性：spec→design→tasks→impl→test/verification。防止"代码能跑但不再匹配已批准工件"。

**执行步骤：**

1. 读取已批准规格、设计、任务计划、实现交接块、code-review 记录
2. 6 维度评分（0-10）：spec→设计、design→任务、task→实现、实现→验证、漂移回写、整体链路闭合
3. 任一维度 < 6 不得通过
4. 结论：`通过` → 进入 Step 2；`需修改` → `mdc-test-driven-dev`；`阻塞` → `using-mdc-workflow`

## Step 2: 回归门禁

防止"修好了本地但破坏相邻模块"。在最小回归范围内收集 fresh evidence。

### Methodology

- **Regression Testing Best Practice (ISTQB)**：区分三级覆盖
- **Impact-Based Testing**：回归范围基于追溯链识别的影响区域
- **Fresh Evidence Principle**：不接受历史运行结果

### Workflow

1. 对齐上游结论：确认上游记录齐全
2. 定义回归面：`full`（所有区域）/`standard`（直接相关模块）/`lightweight`（最小入口）
3. 执行回归检查：使用 CMake/CTest 完整运行。示例 `git-mm exec <repo> "cd build && ctest --output-on-failure"`
4. 阅读结果：检查退出码、失败数量、输出
5. 形成 evidence bundle：记录回归面、命令、退出码、结果摘要、新鲜度锚点
6. 门禁判断：
   - `通过` → 进入 Step 3
   - `需修改` → `mdc-test-driven-dev`
   - `阻塞`（环境） → 重试
   - `阻塞`（上游） → `using-mdc-workflow`

### Output

 - 回归记录（`features/<active>/verification/regression-YYYY-MM-DD.md`）

### 3. 完成门禁

确认有足够、最新且同范围的证据才宣告任务完成。判断"当前 task 完成是否成立"，不自动等于整个 workflow 完成。

**执行步骤：**

- **Definition of Done (Scrum)**：任务完成是所有验收条件满足、证据产生、状态同步后的客观判断
- **Evidence Bundle Pattern**：完整证据束（reviews + gates + 实现交接块）

### Workflow

1. 明确完成范围：写当前准备宣告什么
2. 对齐上游结论与 profile 条件
3. 确定验证命令，立即运行
4. 阅读结果，形成完成证据束
5. 门禁判断：
   - `通过` + 有唯一 next-ready task → `using-mdc-workflow`（锁定新任务）
   - `通过` + 无剩余任务 → 进入 Step 4
   - `需修改` → `mdc-test-driven-dev`
   - `阻塞`（next-ready 不唯一） → `using-mdc-workflow`

### Output

 - 完成记录（`features/<active>/verification/completion-YYYY-MM-DD.md`）

### 4. 收尾

正式收尾 — 任务收尾（剩余任务存在）或工作流收尾（所有任务完成）。

**执行步骤：**

1. 确认 completion gate 允许收尾
2. 收集 closeout 输入：所有 review/gate/verification 记录、任务计划最终状态
3. 执行收尾动作：
    - 更新 `features/<active>/progress.md` 最终状态
    - 更新 `RELEASE_NOTES.md`（如有用户可见变更）
    - 更新任务计划最终状态
    - 执行 closeout/docs sync：将 `features/<active>/ar-spec.md` 已批准需求增量同步到 `docs/<component-name>-spec.md`
    - 执行 closeout/docs sync：将 `features/<active>/ar-design.md` 已批准设计增量同步到 `docs/<component-name>-design.md`
    - 执行 closeout/docs archive：将 `features/<active>/ar-design.md` 完整复制归档到 `docs/ar_design/MDC_CORE_5.0.0_AR{编号}_{需求名称}.md`
4. 判断收尾类型：
   - task closeout（仍有剩余任务） → `using-mdc-workflow`
   - workflow closeout（无剩余任务） → workflow 结束
   - blocked → `using-mdc-workflow`

## 和其他 Skill 的区别

| Skill | 区别 |
|---|---|
| `mdc-code-review` | code-review 是质量评审；本技能是验证+门禁+收尾 |
| `using-mdc-workflow` | 编排 |
| `mdc-test-driven-dev` | 实现 |

## Reference Guide

| 文件 | 用途 |
|---|---|
| `references/verification-record.md` | 验证记录模板（回归/完成门禁） |
| `references/finalize-closeout-pack.md` | 收尾 closeout pack 模板 |

## Red Flags

- 不读上游记录就跑回归
- "本地测试通过"等同于回归安全
- 依赖旧输出
- 无 fresh evidence 就宣称完成
- completion gate 通过后直接结束而不检查剩余任务

## Verification

- [ ] 追溯链检查已完成
- [ ] regression record 已落盘
- [ ] completion record 已落盘（如适用）
- [ ] finalize 输出已落盘（如适用）
- [ ] 所有 evidence 为 fresh
- [ ] `features/<active>/progress.md` 已同步
- [ ] closeout/docs sync 已完成（`docs/<component-name>-spec.md`、`docs/<component-name>-design.md` 已更新）
- [ ] closeout docs archive 已完成（`docs/ar_design/MDC_CORE_5.0.0_AR{编号}_{需求名称}.md` 已归档）
- [ ] 基于 fresh evidence 给出唯一下一步
