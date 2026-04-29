---
name: devflow-completion-gate
description: 当 devflow-code-review 已通过且团队需要在 devflow-finalize 前独立确认 AR / DTS / CHANGE 实现工作项是否满足 devflow 完成定义时使用；也用于返工后复检，或用户询问某个 AR 是否可以算完成。仅适用于实现子街区，不适用于 requirement-analysis 档位下的 SR 工作项。不用于最终收口、状态收口、代码评审、新实现，或阶段和路由混乱。
---

# devflow 完成门禁（仅实现子街区）

判断当前 AR / DTS / CHANGE 实现 work item 是否满足 devflow Definition of Done：所有上游 review / gate 通过、证据齐全、追溯完整、嵌入式风险无未解释的 critical 项。**不**自宣完成、**不**自我验收、**不**做新实现。

devflow 默认以单个 AR / 单个 DTS 为 work item 边界，内部通过 `tasks.md` / `task-board.md` 感知 task 进度。本 skill 先判断当前 active task 是否满足 DoD；若还有唯一 next-ready task，回到 `devflow-tdd-implementation`，只有所有 task 都完成后才进入 `devflow-finalize`（implementation closeout）。

**适用范围**：仅实现子街区（profile = `standard` / `component-impact` / `hotfix` / `lightweight`）。SR work item（profile = `requirement-analysis`）**不**经过本节点；SR 的收口由 `devflow-finalize` 直接做 analysis closeout。如果 SR 工件被误路由进来 → blocked-workflow，`reroute_via_router=true`。

## 适用场景

适用：

- `devflow-code-review` verdict = `通过`，需独立判断完成
- 上一轮 completion-gate 返回 `需修改` / `阻塞`，已修订需复检
- 用户说"能不能算完成 / 这个 AR 完了没"

不适用 → 改用：

- 缺 code review / test-check 记录 → 上游补
- 需状态收口 / closeout → `devflow-finalize`
- 需新实现 → `devflow-tdd-implementation`
- 阶段不清 → `devflow-router`

## 硬性门禁

- 没有针对最新代码的验证证据，不得宣称完成
- 本轮没运行验证命令，不得宣称完成
- 缺实现交接块 / Refactor Note / test-check / code-review 记录，不得 `通过`
- profile 必需的上游证据矩阵不全，不得 `通过`
- 嵌入式 critical 风险（内存 / 并发 / 实时性 / 错误处理）无解释 → 不得 `通过`
- critical 静态分析 / 编译告警 / 编码规范违反无解释 → 不得 `通过`
- AR 实现设计未被同步到 `docs/ar-designs/AR<id>-<slug>.md`（由 `devflow-finalize` 完成同步即可，但 `通过` 时必须显式标注「待 finalize 同步」）
- 不得把"task 完成"等同于"workflow 可结束"——本 skill 通过后必须先检查 task-board，只有无剩余 ready / pending task 时才进入 `devflow-finalize`

## 对象契约

- Primary Object: completion evidence bundle + verdict
- Frontend Input Object: `features/<id>/requirement.md`、`features/<id>/reviews/spec-review.md`、`features/<id>/reviews/component-design-review.md`（component-impact 时必有）、`features/<id>/reviews/ar-design-review.md`、`features/<id>/reviews/test-check.md`、`features/<id>/reviews/code-review.md`、`features/<id>/implementation-log.md`（含实现交接块 + Refactor Note）、`features/<id>/evidence/{unit,integration,static-analysis,build}/`、`features/<id>/traceability.md`、`features/<id>/progress.md`、`docs/component-design.md`、`AGENTS.md`
- Backend Output Object: `features/<id>/completion.md` + 结构化 reviewer 返回摘要 + `progress.md` 同步
- Object Transformation: 把多源证据判定为能否完成；产出 evidence bundle
- Object Boundaries: 不写代码 / 不补测试 / 不修改设计 / 不替团队角色拍板
- Object Invariants: verdict ∈ {`通过`, `需修改`, `阻塞`}；通过后下一步由 task-board 决定：唯一 next-ready task → `devflow-tdd-implementation`；无剩余 task → `devflow-finalize`

## 方法原则

- **Definition of Done (devflow 版)**: 见 `references/definition-of-done.md`
- **Evidence Bundle Pattern**: 完成判断要求完整证据束（reviews + gates + 实现交接块 + 嵌入式风险审计）
- **Profile-Aware Rigor**: standard / component-impact / hotfix / lightweight 的证据矩阵不同；lightweight 不降低质量底线，只缩小验证范围
- **Fresh Evidence Verification**: 命令必须本会话执行，不依赖旧输出
- **Embedded Risk Audit**: critical 嵌入式风险须显式 audit
- **Task Queue Discipline**: completion 先关闭 Current Active Task，再依据 task-board 选择唯一 next-ready task；冲突回 router

## 工作流

### 1. 明确完成宣告范围

按 Definition of Done（详见 `references/definition-of-done.md`）写出本轮准备宣告什么：AR 行为完整 / DTS 修复完成 / 嵌入式风险无未解释项。

### 2. 对齐上游结论与 profile 证据矩阵

按 Profile-Aware Rigor 检查 profile（来自 progress.md）所要求的上游记录是否齐全：

| Profile | 必需的上游记录 |
|---|---|
| `standard` | spec-review、ar-design-review、test-check、code-review、实现交接块 + Refactor Note、evidence/{unit,static-analysis,build}/ |
| `component-impact` | 上面全部 + component-design-review |
| `hotfix` | reproduction.md、root-cause.md、fix-design.md、test-check、code-review、实现交接块 + Refactor Note、evidence/{unit,static-analysis,build}/ |
| `lightweight` | 同 `standard`（文档量可压缩，证据不可压缩） |

任一缺记录 → `阻塞`。

### 2.5 Precheck

- 缺上游证据 / 实现交接块 / Refactor Note → blocked-content，下一步 `devflow-tdd-implementation`
- profile / route / 上游 verdict 冲突 → blocked-workflow，`reroute_via_router=true`，下一步 `devflow-router`
- 否则进入步骤 3

### 3. 决定与执行验证命令

按 Fresh Evidence Verification 选取并执行能直接证明 completion claim 的命令，本会话内跑出新鲜证据：

- 全套单元测试至少跑一次
- 集成 / 仿真测试（若 AR 涉及）至少跑一次
- 静态分析至少跑一次
- 编译命令至少跑一次（含目标平台）

不接受「应该跑过」「最近没改这块」「上次本地跑过」。任一关键命令失败 → verdict ≥ `需修改`。

### 4. 阅读完整结果

逐项核对退出码、失败数、输出是否支持完成宣告、结果是否属于当前最新代码。任一关键命令失败 → `需修改` 或 `阻塞`。

### 5. 嵌入式风险审计

按 Embedded Risk Audit 综合 implementation-log.md 的 Refactor Note、code-review record、静态分析报告，对内存 / 并发 / 实时性 / 资源 / 错误处理 / ABI / SOA 边界各维度给出 `clean` / `documented-debt` / `critical-open` 状态（详见 `references/definition-of-done.md`）。任一 `critical-open` → `阻塞`。

### 6. 形成 completion evidence bundle

按 Evidence Bundle Pattern + `references/devflow-completion-record-template.md` 写入 `features/<id>/completion.md`。若本轮执行了具体验证命令，可按 `references/verification-record-template.md` 为 unit / integration / simulation / build / static-analysis / regression 等命令级证据补充独立 verification record。bundle 任一字段缺 → 视为 `需修改`。

### 7. 完成判定

按下表收敛唯一 verdict + 唯一下一步：

| 条件 | conclusion | `next_action_or_recommended_skill` | reroute_via_router |
|---|---|---|---|
| 上游证据齐全、本轮验证命令全绿、嵌入式风险审计 clean、当前 task 可标记 done，且存在唯一 next-ready task | `通过` | `devflow-tdd-implementation` | `false` |
| 上游证据齐全、本轮验证命令全绿、嵌入式风险审计 clean、所有 tasks 均 done，AR 设计可由 finalize 同步到 docs/ | `通过` | `devflow-finalize` | `false` |
| 验证命令有失败 / 嵌入式风险有未解释 critical / Refactor Note 字段缺 → 可定向回修 | `需修改` | `devflow-tdd-implementation` | `false` |
| 强制验证步骤因环境 / 工具链问题未完成（且 `AGENTS.md` / DoD 无降级许可） | `阻塞` | `devflow-completion-gate` | `false` |
| profile / route / 上游 verdict 冲突 / 实质修改组件边界 | `阻塞`（workflow） | `devflow-router` | `true` |

### 8. 同步状态

把 `features/<id>/task-board.md` 中 Current Active Task 标记为 `done`（通过时），再读取 queue。若存在唯一 next-ready task，更新 `progress.md` 的 `Current Active Task` 并写 `Next Action Or Recommended Skill = devflow-tdd-implementation`；若无剩余 ready / pending task，写 `Next Action Or Recommended Skill = devflow-finalize`；若候选不唯一或状态冲突，写 `Next Action Or Recommended Skill = devflow-router` 且 `reroute_via_router=true`。非通过时回 `devflow-tdd-implementation` / `devflow-completion-gate` / `devflow-router`。

## 输出契约

- Completion record：`features/<id>/completion.md`，按 `references/devflow-completion-record-template.md`
- 结构化 reviewer 返回摘要：record_path、conclusion、key_findings、finding_breakdown、`next_action_or_recommended_skill`、needs_human_confirmation（默认 `true` 等开发负责人 / 模块架构师确认进入 finalize）、reroute_via_router
- `features/<id>/progress.md` canonical 同步

## 风险信号

- 说「应该算完成了」
- 依赖旧输出（"上次跑过"）
- 把主观感觉当证据
- 认为 review 通过就等于运行成功
- 不读实现交接块 + Refactor Note 就宣告完成
- 嵌入式 critical 风险无显式 audit
- 单 task 完成后直接 finalize，未检查 task-board
- 把缺失的 docs/ar-designs/ 同步当作 `阻塞`（应在通过时显式标注「待 finalize 同步」）

## 常见错误

| 错误 | 修复 |
|---|---|
| code review 通过就直接给 `通过` | 仍需本轮验证命令 fresh evidence + 嵌入式风险 audit |
| 静态分析 critical 项被「先放着」 | 标 critical finding，verdict ≥ `需修改` |
| profile = component-impact 但 component-design-review 缺记录 | `阻塞`(workflow)，回 router |

## 验证清单

- [ ] completion record 已落盘到 `features/<id>/completion.md`
- [ ] 上游证据矩阵显式列出（含 N/A）
- [ ] 本轮验证命令、退出码、结果摘要、新鲜度锚点已记录
- [ ] 嵌入式风险审计显式给出
- [ ] verdict 唯一、下一步唯一、`reroute_via_router` 正确
- [ ] 通过时已检查 task-board：有唯一 next-ready task 则下一步 `devflow-tdd-implementation`，无剩余 task 才下一步 `devflow-finalize`
- [ ] progress.md canonical 同步
- [ ] needs_human_confirmation 默认 `true`，等开发负责人 / 模块架构师确认

## 本地 DevFlow 约定

本节由当前 skill 自己维护。不要加载共享约定文件；项目 `AGENTS.md` 可以覆盖等价路径或模板。

### 产物布局

默认产物布局来自 `docs/principles/03 artifact-layout.md`。项目 `AGENTS.md` 可以覆盖等价路径；没有覆盖时，本 skill 必须使用以下组件仓库布局：

```text
<component-repo>/
  docs/
    component-design.md           # 长期组件实现设计
    ar-designs/                   # 长期 AR 实现设计
      AR<id>-<slug>.md
    interfaces.md                 # 可选；仅团队启用时读取 / 同步
    dependencies.md               # 可选；仅团队启用时读取 / 同步
    runtime-behavior.md           # 可选；仅团队启用时读取 / 同步

  features/
    AR<id>-<slug>/                # 单个 AR 的过程产物
    DTS<id>-<slug>/               # 单个缺陷 / 问题修复的过程产物
    CHANGE<id>-<slug>/            # 单个轻量变更的过程产物
```

`docs/` 存放随代码提交的长期组件资产。`features/<id>/` 存放单个 work item 的过程产物：按需包含 `README.md`、`progress.md`、`requirement.md`、`ar-design-draft.md`、`tasks.md`、`task-board.md`、`traceability.md`、`implementation-log.md`、`reviews/`、`evidence/`、`completion.md`、`closeout.md`。

Read-on-presence 规则：

- 必需长期资产缺失时阻塞：component-impact 工作需要 `docs/component-design.md`；implementation closeout 前需要 `docs/ar-designs/AR<id>-<slug>.md`。
- 可选资产（`docs/interfaces.md`、`docs/dependencies.md`、`docs/runtime-behavior.md`）仅在项目启用时读取 / 同步。缺失的可选资产记录为 `N/A (project optional asset not enabled)`，不视为阻塞。
- 过程目录保留在 `features/` 下；不要把已关闭 work item 移到 `features/archived/`，否则会破坏追溯链接。

### Progress 字段

本 skill 读写 `features/<id>/progress.md` 时使用 canonical progress 字段：

- Work Item Type: SR / AR / DTS / CHANGE
- Work Item ID: SR1234、AR12345、DTS67890 或 CHANGE id
- Owning Component: AR / DTS / CHANGE 必填
- Owning Subsystem: SR 必填
- Workflow Profile: requirement-analysis / standard / component-impact / hotfix / lightweight
- Execution Mode: interactive / auto
- Current Stage: 当前 canonical devflow node
- Pending Reviews And Gates: 待处理 review / gate 列表
- Next Action Or Recommended Skill: 仅允许一个 canonical node
- Blockers: open blockers
- Last Updated: timestamp

### Handoff 字段

返回结构化 handoff，并使用本 skill 已知的字段：

- current_node
- work_item_id
- owning_component or owning_subsystem
- result or verdict
- artifact_paths
- record_path, when a review / gate / verification record exists
- evidence_summary
- traceability_links
- blockers
- next_action_or_recommended_skill
- reroute_via_router

不要把 `next_action_or_recommended_skill` 设为 `using-devflow` 或自由文本。

### Completion 记录

除非 `AGENTS.md` 覆盖路径，否则写入 `features/<id>/completion.md`。

### Completion 证据

检查已批准设计、已完成当前 task、test-check verdict、code-review verdict、unit/integration/build/static-analysis evidence、traceability 和 task-board state。若存在唯一 next-ready task，路由到 `devflow-tdd-implementation`；若无剩余工作，路由到 `devflow-finalize`；状态不明确则路由到 `devflow-router`。
## 支撑参考

| 文件 | 用途 |
|---|---|
| `references/definition-of-done.md` | devflow Definition of Done 各 profile 表 |
| `references/devflow-completion-record-template.md` | completion record 模板 |
| `references/verification-record-template.md` | 通用验证记录模板（命令、结果、新鲜度锚点、验证结论） |
