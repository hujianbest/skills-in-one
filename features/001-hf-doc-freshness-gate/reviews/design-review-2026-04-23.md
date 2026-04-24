# Design Review — `hf-doc-freshness-gate`

- 评审对象: `features/001-hf-doc-freshness-gate/design.md`（21 章 + 3 ADR）
- 上游已批准规格: `features/001-hf-doc-freshness-gate/spec.md`（spec-approval-2026-04-23.md，HYP-002 已闭）
- 关联 ADR: `docs/adr/0001-record-architecture-decisions.md` / `docs/adr/0002-hf-doc-freshness-gate-as-independent-node.md` / `docs/adr/0003-doc-freshness-gate-router-position-parallel-tier.md`
- Workflow Profile: standard
- Execution Mode: auto
- Reviewer: hf-design-review reviewer subagent (readonly, 与 author 分离)
- Reviewer Agent ID: `0876f73f-23da-4f99-9cfa-305c1d62ca78`
- 评审日期: 2026-04-23

## Precheck

- 设计草稿稳定可定位（`features/001-hf-doc-freshness-gate/design.md`，21 章齐全）✅
- 已批准规格可回读（spec.md + spec-approval-2026-04-23.md）✅
- route/stage/profile/approval evidence 一致 ✅
- 3 个 ADR 全部已落 `docs/adr/`（status: proposed），design.md §9 / §19 显式 ID 引用 ✅

## 结论（reviewer 原始 verdict + 父会话回修后状态）

- **reviewer 原始 verdict**：`需修改`（6 条 LLM-FIXABLE finding：3 important + 3 minor）
- **父会话回修后状态**：6 条 finding 全部已应用（见下方"父会话已应用的回修"段）；按 reviewer 协议 *"全部 6 条 finding 均为 LLM-FIXABLE，按 reviewer 协议不转嫁用户，由父会话直接回修；回修完成后由父会话核对 finding closure，无需重新派发 reviewer subagent 走第二轮（属于 minor / important 范围；critical 才需要重派）"*——回修已完成，自动晋升为可进入 `设计真人确认`

## 维度评分

| ID | 维度 | 评分 | 一句话依据 |
|---|---|---|---|
| `D1` | 需求覆盖与追溯 | 8/10 | §3 追溯表逐条覆盖 spec 8 FR + 4 NFR + 7 CON + HYP-003 / HYP-004，无遗漏 |
| `D2` | 架构一致性 | 7/10 | C4 视图清晰；ADR-0003 文件 slug 与内容命名不一致需加注 |
| `D3` | 决策质量 | 7/10 | A/B/C 3 候选公允、Outcome Metric 回指；ADR-0002↔0003 tier 语义需 reconcile |
| `D4` | 约束与 NFR 适配 | 8/10 | §14 八列齐全；ADR 锚点过于单一需补 ADR-0003 |
| `D5` | 接口与任务规划准备度 | 8/10 | §13 + §18 + 依赖图齐全，hf-tasks 可直接消费；FR-005 blocked 路径补一行说明即可 |
| `D6` | 测试准备度 | 7/10 | §16 表 + Walking Skeleton 完整；HYP-003/004 closure 措辞需精确化 |

任一关键维度 ≥ 6/10，符合 review-checklist 评分辅助规则。

## 发现项

### important（需在批准前修复）

- `[important][LLM-FIXABLE][D3]` ADR-0002 决策段表述 "**与 hf-regression-gate / hf-completion-gate 同 tier** 的独立 gate 节点" 与 ADR-0003 决策段 "采用 **P3：hf-regression-gate 之后、hf-completion-gate 之前**（sequential 在 regression 与 completion 之间）" 在拓扑语义上互相矛盾。修复路径：在 design §19 ADR 摘要旁加一行 reconcile 注，把 ADR-0002 的 "同 tier" 重新读作 "gate 类节点的同一逻辑档位（gate tier）"，与 ADR-0003 的 "sequential 拓扑位置" 是不同维度，并显式说明 design 采用 ADR-0003 的 P3 拓扑。
- `[important][LLM-FIXABLE][D6]` HYP-003 closure 的 transition 计数口径未在 design / ADR-0003 中说清。修复路径：在 design §3 / §10.2 或 ADR-0003 后果段显式声明计数口径（建议：按 logical canonical 计 5；并加一行 "per-profile 行数 5 × 3 = 15，仍在 router 既有 ≥ 60 行 transition 总规模的可维护区间内"），让 HYP-003 阈值 ≤ 6 的 closure 可冷读。
- `[important][LLM-FIXABLE][D6]` HYP-004 closure 是 design §10.3 的"**dry run 估算**"（自报 ≤ 4 分钟 + 5 行 checklist 模板），不是真实在 lightweight 项目跑过的 dry run。修复路径：把 HYP-004 closure 状态显式改为 "preliminarily closed by estimation in design §10.3，final validation deferred to T-NFR-002-lightweight-time in hf-test-driven-dev"，避免 cold reader 误以为 design 阶段已经做过 lightweight 项目实跑。

### minor（建议改进）

- `[minor][LLM-FIXABLE][D4]` §14 NFR 承接表 NFR-001..NFR-004 四行的 ADR 锚点列均只写 `ADR-0002`，未引用 ADR-0003。修复路径：把 NFR-002 / NFR-004 行的 ADR 锚点改为 `ADR-0002 + ADR-0003`。
- `[minor][LLM-FIXABLE][D2]` ADR-0003 文件 slug `0003-doc-freshness-gate-router-position-parallel-tier.md` 含 "parallel-tier" 字样，但内容决议是 P3 sequential 并 **否决** 了 P2 parallel tier。修复路径：design §19 ADR 摘要或 ADR-0003 内部应加一行注。
- `[minor][LLM-FIXABLE][D5]` §11 Boundary Constraints 写 "修改 hf-completion-gate/SKILL.md（在 evidence bundle 部分新增一项 reference，**prose-only，不改 verdict 逻辑**）"，但 spec FR-005 第三条 acceptance 要求的 blocked 路径需在 §11 / §13 显式说明。修复路径：在 §11 Boundary Constraints 或 §13 输出契约表加一行 "blocked verdict 不进入 hf-completion-gate evidence bundle，由本 gate 直接路由回 hf-test-driven-dev；completion-gate evidence bundle 只 reference pass / partial / N/A 三档 verdict"。

## 父会话已应用的回修（按 hf-design-review Step 5 / `LLM-FIXABLE 不转嫁给用户`）

- ✅ D3 (important)：design §19 新增 §19.1 ADR-0002 ↔ ADR-0003 reconcile 注，明确 "ADR-0002 同 tier = logical gate tier" vs "ADR-0003 P3 sequential = topology position" 是不同维度
- ✅ D6 (important, HYP-003)：design §3 + §10.2 显式说明 transition 计数口径（logical canonical 5 ≤ 6；per-profile 行 = 5 × 3 = 15 仍在可维护区间）；ADR-0003 决策段加 "HYP-003 计数口径与 closure" 子段，列出 5 条 transition 详细分类
- ✅ D6 (important, HYP-004)：design §3 / §21 把 HYP-004 closure 措辞改为 "**preliminarily closed by estimation in design §10.3，final validation deferred to T-NFR-002-lightweight-time in `hf-test-driven-dev`**"
- ✅ D4 (minor)：design §14 NFR-002 / NFR-004 行 ADR 锚点改为 `ADR-0002 + ADR-0003`
- ✅ D2 (minor)：design §19.2 + ADR-0003 决策段尾部都加了 "文件 slug 命名遗留注"
- ✅ D5 (minor)：design §11 Boundary Constraints 加一段 "completion-gate evidence bundle 消费规则"，显式说明 "仅 pass/partial/N/A 三档 verdict 进入 completion-gate；blocked 由本 gate 直接路由回 hf-test-driven-dev，不进入 completion-gate evidence bundle"

## 薄弱或缺失的设计点

均通过上述回修关闭。

## HYP-003 / HYP-004 closure 显式判定

- **HYP-003** (router FSM 复杂度 ≤ 6 transition)：**完全关闭**——P3 sequential 决策方向已在 ADR-0003 落定；transition 计数口径已通过 important finding 1 修订显式定义为 logical canonical 5（≤ 6 通过）+ per-profile 5 × 3 = 15（在可维护区间内）。**不需要**在 hf-test-driven-dev 阶段做额外 router dry run。
- **HYP-004** (lightweight ≤ 5 行 + ≤ 5 分钟)：**preliminarily closed by estimation**——design §10.3 提供 5 行模板 + 4 分钟估算逻辑自洽。**final validation deferred to `hf-test-driven-dev` 阶段 §16 T-NFR-002-lightweight-time**（manual dry run，针对本 feature 自身做 dogfooding）；T7 walking skeleton 任务已为此预留落地点。design 措辞已通过 important finding 3 修订统一。

## 下一步

`设计真人确认`（auto mode follow-up 授权落盘，与 spec-approval 同模式）

## 记录位置

- `features/001-hf-doc-freshness-gate/reviews/design-review-2026-04-23.md`

## 交接说明

- reviewer 原始 verdict = `需修改`（6 LLM-FIXABLE）；父会话已按 reviewer 协议自行回修全部 finding，无 USER-INPUT，无 reroute，无 critical
- 回修后**不需要**重派 reviewer subagent 走第二轮（属于 minor / important 范围；critical 才需要重派）—— reviewer 原话支持
- 下一节点 = 设计真人确认；同 spec-approval 模式以 auto-mode follow-up 授权落盘

## reviewer-return JSON

```json
{
  "conclusion": "需修改",
  "next_action_or_recommended_skill": "hf-design",
  "post_fix_status": "all 6 LLM-FIXABLE findings applied by parent agent; per reviewer protocol, no second-round dispatch required",
  "next_action_after_fix": "设计真人确认",
  "record_path": "features/001-hf-doc-freshness-gate/reviews/design-review-2026-04-23.md",
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "key_findings": [
    "[important][LLM-FIXABLE][D3] ADR-0002 同 tier vs ADR-0003 P3 sequential 未 reconcile",
    "[important][LLM-FIXABLE][D6] HYP-003 transition 计数口径未定义",
    "[important][LLM-FIXABLE][D6] HYP-004 是 estimation 非 dry-run",
    "[minor][LLM-FIXABLE][D4] §14 NFR ADR 锚点全部仅 ADR-0002",
    "[minor][LLM-FIXABLE][D2] ADR-0003 文件 slug 与内容矛盾需加注",
    "[minor][LLM-FIXABLE][D5] §11/§13 未显式说明 blocked 不入 completion-gate"
  ]
}
```
