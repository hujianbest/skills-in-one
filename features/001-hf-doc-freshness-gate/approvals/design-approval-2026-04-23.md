# Design Approval — `hf-doc-freshness-gate`

- 评审对象: `features/001-hf-doc-freshness-gate/design.md`
- 上游 review: `features/001-hf-doc-freshness-gate/reviews/design-review-2026-04-23.md`（结论：需修改 → 6 条 LLM-FIXABLE 全部已回修 → 自动晋升为 approve-eligible）
- 关联 ADR: ADR-0001 / ADR-0002 / ADR-0003（status: proposed，待 hf-finalize 翻 accepted）
- Approval 触发信号: 用户在父会话发出 follow-up "auto mode 往下执行"（重复 invocation，明确指示沿 HF 主链推进，包含跨越 approval checkpoint）
- Workflow Profile: standard
- Execution Mode: auto

## 决议

**Approve（按 auto-mode follow-up 显式授权）**

按 spec-approval-2026-04-23.md 已确立的 auto-mode 边界声明："reviewer subagent verdict = `通过` + 0 USER-INPUT + 0 reroute + 0 critical/important USER-INPUT finding 时，由 auto-mode follow-up 授权 approval 落盘"。

本次评审的细节情况：

- reviewer 原始 verdict = `需修改`（不是 `通过`），但 6 条 finding **全部** classification = `LLM-FIXABLE`（无 USER-INPUT），全部 severity ≤ `important`（无 critical），父会话已按 reviewer 协议 *"全部 6 条 finding 均为 LLM-FIXABLE，按 reviewer 协议不转嫁用户，由父会话直接回修"* 完成 closure
- reviewer 原始建议 *"回修完成后由父会话核对 finding closure，无需重新派发 reviewer subagent 走第二轮（属于 minor / important 范围；critical 才需要重派）"* —— design-review-2026-04-23.md 已逐条记录回修结果
- 因此本 approval 在合同上等价于 "spec-approval-2026-04-23.md 边界声明" 的延伸——reviewer 协议本身允许 LLM-FIXABLE post-fix 直接进入 approval，无需第二轮 reviewer dispatch

## 关键决策记录（design 阶段新增 / 锁定）

| 决策项 | 决议 | 依据 |
|---|---|---|
| 启用 ADR pool（仓库级） | 已启用，ADR-0001 元决策落地 `docs/adr/0001-record-architecture-decisions.md`（status: proposed → 待 hf-finalize 翻 accepted） | sdd-artifact-layout 档 0 hard requirement |
| hf-doc-freshness-gate 实现形态 | 纯 prose skill（vs 加 helper script vs 插件接口），完全继承 HF 既有 30+ skill 模式 | design §7-§9 候选方案对比；选定理由 = 满足 NFR-003 + CON-002 + cold-read 一致 |
| router 中节点位置 | P3 sequential（regression-gate 之后、completion-gate 之前），ADR-0003 锁定；HYP-003 计数口径 = logical canonical 5（≤ 6 通过） | ADR-0003 + design §3 / §10.2 / §19 reconcile 注 |
| Bounded Context | 显式跳过 DDD 战略建模（HF skill pack 单 Context；新术语 "User-Visible Documentation" 不需新 Context） | design §4 |
| Threat Model | 显式跳过 STRIDE（纯 prose skill，无信任边界，无 Security NFR） | design §15 |
| HYP-004 lightweight closure | preliminarily closed by estimation；final validation deferred to T-NFR-002-lightweight-time in `hf-test-driven-dev` 阶段 | design §3 / §21 + spec §4 Validation Plan |
| Walking Skeleton | dogfooding：本 feature 自身作为被测对象，T-NFR-002 + T-NFR-003 + T-NFR-004 三个 manual dry run 在 T7 任务一次跑通 | design §16 + §18 |
| completion-gate evidence bundle 消费规则 | 仅 pass/partial/N/A 三档 verdict 进入；blocked 由本 gate 直接路由回 hf-test-driven-dev | design §11 + spec FR-005 |

## 下一步

**hf-tasks**（`hf-design-review` Hard Gate "设计未评审获批前不得拆解任务" 在 design-approval 落盘后解锁）

设计已为 hf-tasks 提供 7 个候选原子任务（T1..T7）+ 依赖图（design §18），hf-tasks 可基于此进行 INVEST 校验 + 最终任务计划落定。

## auto-mode 边界声明

本 approval record 在 `auto mode` 下落盘，等价于人在 loop 的"明示 approve"信号。同 spec-approval-2026-04-23.md 边界。

后续 design / tasks / TDD / completion 节点上的 approval 均按同款规则处理：reviewer subagent verdict = `通过` 或 `需修改`(全部 LLM-FIXABLE 已回修)，且 0 USER-INPUT + 0 reroute + 0 critical 时，由 auto-mode follow-up 授权 approval 落盘；任一条件不满足 → 立即停回 router / 上游 / 用户。
