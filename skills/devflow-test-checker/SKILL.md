---
name: devflow-test-checker
description: 当 devflow-tdd-implementation 已完成且新写测试需要在代码检视前独立审查覆盖度、有效性、可维护性时使用；也用于派发评审子代理执行 TDD 后测试有效性审查，或上一轮 test-check 要求修改后复审。不用于编写或修复测试、评审生产代码，或阶段和路由混乱。
---

# devflow TDD 后测试有效性审查

独立审查 `devflow-tdd-implementation` 已落地的测试用例是否真正有效：覆盖 AR 关键行为 / 边界 / 异常路径 / 嵌入式风险，断言能证明行为而不是仅证明代码被调用，可执行 / 稳定 / 可维护。

本 skill **不**补写测试、**不**修改生产代码、**不**替开发负责人决定优先级。它产出 verdict + findings + 唯一下一步。

devflow-soul 要求：「TDD 中写出的测试用例不能天然视为有效，必须经过独立 test-check record。」本 skill 是这条纪律的工程化执行。

## 适用场景

适用：

- `devflow-tdd-implementation` 已写回 fresh evidence + 实现交接块，需独立审查测试有效性
- reviewer subagent 被派发执行 test-check
- 用户明确要求「review 测试 / test check / 测试有效性审查」

不适用 → 改用：

- 写 / 修测试 → `devflow-tdd-implementation`
- 评审 C / C++ 代码质量 → `devflow-code-review`
- 阶段不清 / 证据冲突 → `devflow-router`

## 硬性门禁

- `devflow-test-checker` 通过前不得进入 `devflow-code-review`
- reviewer **不**修改测试代码 / 生产代码 / AR 设计
- reviewer **不**补写测试用例（缺测试用例 → 视为 finding 让 `devflow-tdd-implementation` 回修）
- reviewer **不**替开发负责人 / 模块架构师拍板
- reviewer **不**返回多个候选下一步
- 缺实现交接块或 fresh evidence → blocked-content，下一步 `devflow-tdd-implementation`
- route / stage / profile 冲突 → blocked-workflow，`reroute_via_router=true`，下一步 `devflow-router`

## 对象契约

- Primary Object: implemented test quality finding set + verdict（已实现测试质量发现项与结论）
- Frontend Input Object: 测试代码（本轮新增 / 修改）、`features/<id>/implementation-log.md`（含 Current Active Task + 实现交接块）、`features/<id>/tasks.md`、`features/<id>/task-board.md`、`features/<id>/evidence/{unit,integration,static-analysis,build}/`、`features/<id>/ar-design-draft.md`（含测试设计章节）、`features/<id>/requirement.md`、`docs/component-design.md`、`AGENTS.md`
- Backend Output Object: `features/<id>/reviews/test-check.md` + 结构化 reviewer 返回摘要
- Object Transformation: 把已落地测试用例审查成有效性 / 覆盖性 / 可维护性结论
- Object Boundaries: 不修改测试 / 不写代码 / 不替团队角色拍板
- Object Invariants: verdict ∈ {`通过`, `需修改`, `阻塞`}

## 方法原则

- **Post-TDD Test Effectiveness Review**: 独立检查测试是否真正验证了行为，而不是只验证「代码被调用」
- **Coverage Categories**: 行为覆盖 / 边界覆盖 / 异常覆盖 / 嵌入式风险覆盖
- **Mutation Mindset**: 默认怀疑——如果改 1 行实现，测试是否能抓到？不能则视为弱断言
- **Fresh Evidence Verification**: RED / GREEN 证据必须本会话生成、可解释
- **Mock Boundary Audit**: mock 是否限定在真正边界，是否 mock 了内部纯逻辑或私有函数
- **Embedded Risk Coverage Check**: NFR 是否被 `embedded-risk` 用例覆盖
- **Traceability Check**: 每个用例是否回指 requirement row + AR 设计 Test Design Case ID
- **Separation Of Author / Reviewer**: reviewer 与 implementer 必须不同角色 / subagent

## 工作流

### 1. 建立证据基线

按 Evidence-Based + Read-On-Presence 读取测试代码、`features/<id>/implementation-log.md`（含 Current Active Task + 实现交接块 + Refactor Note）、tasks.md、task-board.md、`features/<id>/evidence/{unit,integration,static-analysis,build}/`、ar-design-draft.md（测试设计章节）、requirement.md、`docs/component-design.md`、`AGENTS.md`。

### 1.5 Precheck

- 缺关键测试资产或实现交接块 → blocked-content，下一步 `devflow-tdd-implementation`
- route / stage / profile 冲突 → blocked-workflow，`reroute_via_router=true`，下一步 `devflow-router`
- 否则进入步骤 2

### 2. 多维评分

按 Structured Walkthrough 对 7 个维度（详见 `references/test-check-rubric.md`）做 0-10 评分；任一关键维度 < 6 不得 `通过`。

| 维度 | 关注 |
|---|---|
| TC1 Fresh RED / GREEN Validity | RED 是否真失败、GREEN 是否本会话产生、新鲜度锚点完整 |
| TC2 Behavior & Acceptance Mapping | 测试是否覆盖 AR 关键行为；是否回指 requirement row |
| TC3 Boundary & Exception Coverage | 边界 / null / 错误路径 / 异常路径覆盖 |
| TC4 Embedded Risk Coverage | 内存 / 并发 / 实时性 / 资源 / 错误处理 / ABI 是否被 embedded-risk 用例覆盖 |
| TC5 Mock Boundary Discipline | mock 是否限定真正边界；不 mock 内部纯逻辑 / 私有函数 |
| TC6 Assertion Strength | 断言能证明行为而不是仅证明代码路径被走过 |
| TC7 Stability & Maintainability | 测试可独立运行 / 不依赖外部状态 / 命名清晰 / 无 flaky 信号 |

### 3. 正式 checklist 审查


### 4. 形成 verdict

按下表收敛唯一 verdict + 唯一下一步：

| 条件 | conclusion | `next_action_or_recommended_skill` | reroute_via_router |
|---|---|---|---|
| 7 维度均 ≥ 6、嵌入式风险矩阵被实测覆盖、断言强度足够、无 critical USER-INPUT | `通过` | `devflow-code-review` | `false` |
| findings 可 1-2 轮定向修订 | `需修改` | `devflow-tdd-implementation` | `false` |
| 测试过于薄弱 / 核心行为未覆盖 / 嵌入式风险大量未覆盖 / findings 无法定向回修 | `阻塞`（内容） | `devflow-tdd-implementation` | `false` |
| route / stage / profile / 上游证据冲突 | `阻塞`（workflow） | `devflow-router` | `true` |

### 5. 写 review 记录并回传


## 输出契约

- Review record：`features/<id>/reviews/test-check.md`
- 结构化 reviewer 返回摘要：record_path、conclusion、key_findings、finding_breakdown、`next_action_or_recommended_skill`、needs_human_confirmation（默认 `false`）、reroute_via_router

## 风险信号

- 不读实现交接块就审测试
- 「测试文件存在」等同于「测试充分」
- 忽略无效 RED / GREEN（一跑就绿、无 fresh evidence）
- 测试只覆盖 happy path 却给 `通过`
- 嵌入式 NFR 未被 embedded-risk 用例覆盖却给 `通过`
- mock 越过真正边界却没标 finding
- 评审中补写测试 / 改生产代码（reviewer 不是 author）
- 返回多个候选下一步

## 常见错误

| 错误 | 修复 |
|---|---|
| 看到「全绿」就给 `通过` | 检查 RED 是否真失败、断言是否能 mutation-kill |
| NFR-001（实时性）只在 happy path 验过 | 标 critical finding，verdict ≥ `需修改` |
| 测试 mock 了模块内部纯逻辑 | 标 important finding，要求改 mock 边界 |

## 验证清单

- [ ] review record 已落盘
- [ ] precheck 结果显式记录
- [ ] 7 维度评分完整、findings 已分类
- [ ] verdict 唯一、下一步唯一、`reroute_via_router` 正确
- [ ] 嵌入式风险覆盖矩阵已被实际测试落实情况已显式审查
- [ ] 结构化摘要已回传父会话
- [ ] 未顺手修改测试 / 生产代码

## 内嵌评审记录模板

除非 `AGENTS.md` 覆盖路径，否则把 review record 写到本 skill 预期路径。只保留与当前 review 类型相关的章节。

- Metadata：review type、work item type/id、owning component/subsystem、reviewer identity、date、record path。
- Inputs Consumed：primary artifact path + freshness anchor、commit/branch、supporting context paths、AGENTS.md/team standards used。
- Multi-Dimension Scoring：rubric dimensions、0-10 score，以及每个分数的 evidence；任一 critical dimension 低于阈值即不得通过。
- Findings：ID、severity、classification、rule_id、anchor/location、description、impact、suggested fix。
- Verdict：conclusion（pass / needs changes / blocked）、rationale、next_action_or_recommended_skill、reroute_via_router、needs_human_confirmation。
- Follow-up Actions：所需 rework 或 confirmation 的 owner 与 status。

## 评审者契约

本 review skill 由独立 reviewer 角色或 subagent 执行。reviewer 不得修改被评审产物、写代码、加测试或替团队做决策。

最小结构化返回：

```yaml
target_skill: <this skill name>
work_item_id: <id>
owning_component: <component or N/A>
record_path: <written review record>
conclusion: pass | needs_changes | blocked
verdict_rationale: <1-3 lines>
key_findings: []
finding_breakdown:
  critical: 0
  important: 0
  minor: 0
next_action_or_recommended_skill: <one canonical devflow node>
needs_human_confirmation: true | false
reroute_via_router: true | false
```

规则：只返回一个 `next_action_or_recommended_skill`；workflow conflict 路由到 `devflow-router` 且 `reroute_via_router=true`；通过结论不能包含 critical findings。

## 本地测试设计契约摘录

本 skill 检查测试设计时，要求每个 case 包含：case id、requirement row / design anchor、behavior under test、preconditions、inputs or stimuli、expected output or observable effect、mock/stub/simulation boundary、verification command or evidence path、embedded risk covered。DevFlow 不使用单独的 `test-design.md`；测试设计位于 AR design 中。

## 本地证据覆盖摘录

检查测试时，把 evidence 映射到 AR design cases 与 embedded risks：unit、integration/simulation、build、static analysis 以及任何 regression evidence。每条 evidence 必须包含 command、environment/config、result、freshness anchor。

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

### Test Check 记录

除非 `AGENTS.md` 覆盖路径，否则写入 `features/<id>/reviews/test-check.md`。

### Review 边界

按 AR design test cases、requirement coverage、evidence freshness、maintainability、mocks/stubs/simulation 和有意义的 RED/GREEN evidence 审查新写测试。不要在这里写或修测试。
## 支撑参考

| 文件 | 用途 |
|---|---|
| `references/test-check-rubric.md` | 7 维度 rubric + rule IDs（TC1-TC7） |
| `references/team-test-review-rubric.md` | 团队 UT 审查准则完整继承版 |
| Local Test Design Contract Excerpt | 测试设计章节契约（用例最小字段） |
