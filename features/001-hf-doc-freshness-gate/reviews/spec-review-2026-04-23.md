# Spec Review — `hf-doc-freshness-gate`

- 评审对象: `features/001-hf-doc-freshness-gate/spec.md`
- Reviewer: hf-spec-review reviewer subagent (readonly, 与 author 分离)
- Reviewer Agent ID: `1fb2f95f-bad4-48c0-b0be-7932b3d093eb`
- Author: Cursor Cloud Agent (HF self-application, 父会话)
- 评审日期: 2026-04-23
- Workflow Profile: standard
- Execution Mode: auto
- Rubric: `skills/hf-spec-review/references/spec-review-rubric.md`（Group Q / A / C / G）

## 结论

**通过**

spec 草稿已具备成为 `hf-design` 稳定输入的契约形态：8 条 FR 与 4 条 NFR 全部满足 `requirement-authoring-contract.md` + `nfr-quality-attribute-scenarios.md` 最小字段；§6.2 责任矩阵冷读无歧义，HYP-002 (U2) 由本评审关闭；HYP-001 由 desk-research probe Pass 关闭且对其方法局限的承接路径已在 §12 + `progress.md` Open Risks 中显式留痕；§13 "阻塞=无" 属实。共 4 条 minor LLM-FIXABLE 措辞项，可由 `hf-specify` 一轮回修；无 USER-INPUT 阻塞、无 route / stage / 证据冲突，不触发 reroute。

## 维度判定

| 组 | 判定 | 一句话理由 |
|---|---|---|
| Group Q (Q1–Q8 Quality Attributes) | 通过 | 8 FR / 4 NFR 全员带 ID + Source 锚点（多数 `HYP-xxx` / `§6.2` / discovery 段号），EARS / BDD / MoSCoW / ISO 25010 / QAS 五要素到位，仅 Lagging Indicator 与 NFR-001 Acceptance 两处可量化打磨。 |
| Group A (A1–A6 Anti-Patterns) | 通过 | 无未量化形容词；FR 主体均为"系统必须…"；§6.1 整合点描述属"集成范围"而非 endpoint / 表结构 A3 设计泄漏；§7 *Considered Alternatives* 保留 A2 / A3 是健康的决策史，不构成 A3。 |
| Group C (C1–C7 Completeness & Contract) | 通过 | C1 / C2 / C4 / C5 / C7 到位；C3 §13 "阻塞=无" 属实（HYP-002 本评审关闭、HYP-001 已 probe Pass、HYP-003 / HYP-004 显式 design 处理）；C6 Outcome Metric 与 Threshold 分行符合模板。 |
| Group G (G1–G3 + GS1–GS6 Granularity & Scope-Fit) | 通过 | 8 FR 单一可观察行为；FR-004 内嵌 profile 表属同一决策的合理表达不命中 GS3 / GS5；当前轮 vs Phase 1 / design / 后续增量已在 §6.3 + §13 显式区分，未触发 G2 混写；findings 收敛在 1 轮定向回修内（满足 G3）。 |

## 反模式扫描（A1–A6）

- A1（模糊词）：未触发。NFR-001 Response Measure = 100%、NFR-002 = ≤ 5 分钟 / ≤ 30 行、NFR-004 = `N/A ≠ blocked` 硬判定，均带可验证条件。NFR-003 Response Measure 是"不强依赖任何外部工具链 + 缺失不构成 `blocked`" 的二值判定，符合 QAS"明确判定准则" 允许形态。
- A2（复合需求）：未触发。FR-001 三类 input source 是 OR 关系且共享同一决策面（user-visible behavior change list），FR-004 profile 表是同一字段的三档表达，不构成多能力打包。
- A3（设计泄漏）：未触发但有 1 处轻度边界（见 finding M3）。
- A4（无主体被动表达）：未触发，主体均为系统/父会话/reviewer subagent。
- A5（占位 / 待定）：未触发。FR-004 lightweight 引用 HYP-004 design dry run 是验证路径而非占位阈值（≤ 5 分钟 / ≤ 30 行已写死）。
- A6（缺少负路径）：未触发。FR-001 / FR-003 / FR-005 / FR-007 均带至少一条负路径 BDD；S1–S5 场景覆盖 pass / partial / N/A / blocked 四值。

## HYP-002 (U2) 责任矩阵冷读判定

逐行冷读 §6.2 表 14 行 × 5 skill 列，无任一条目存在歧义：

- 单 ✅ 行（Row 1 / 3 / 5 / 6 即本 gate 独占维度）冷读直接归 `hf-doc-freshness-gate`；
- ⚠ 与 ✅ 共存行（Row 4 公共 API：本 gate ✅ verdict + evidence；`hf-code-review` ⚠ 实现层正确性 review）通过"verdict 归属 vs review 检视职责"区分，例 docstring 因实现变更而失同步 → 本 gate；docstring 内容本身实现错误 → review；
- Row 11 多职能行（`docs/insights/...` / closeout pack）：`hf-finalize ❌`（显式排除）+ `hf-increment ⚠ 范围变更时同步` + `hf-traceability-review ✅`（主 verdict 归属），通过"时机限定 ⚠ vs 主 verdict ✅"无歧义；
- Row 13 元行（"代码已实现新行为，但文档仍是旧结论" 心态 Red Flag）：本 gate ❌ 带注（verdict + fresh evidence 形态）+ `hf-increment ✅` 带注（prose Red Flag 所有权 + 作为本 gate 诊断辅助），prose 与 verdict 形态显式不重叠。

→ 结论：§6.2 通过本评审无 U2 finding；HYP-002 (U2) 据 §4 footnote "本表通过 hf-spec-review 时无 U2 finding" 关闭。建议 `hf-specify` 在回修阶段把 §4 HYP-002 行同步更新为 Confidence: high (closed by spec-review)、Blocking: 否（与 HYP-001 post-probe 同款方式）—— **父会话已在本 review 同 commit 内完成此更新**。

## HYP-001 (A1) 关闭证据链冷读

probe 在 cloud agent 环境用户访谈通道不可用的客观限制下改用 desk research 5 维度证据汇总（按 `hf-experiment` Step 3 lowest-cost-first 规则），命中 5 / 5 远超 ≥ 3 / 5 门槛，证据全部带 file:line 引用 + 关键句节选（`docs/experiments/2026-04-23-hf-doc-freshness-gate-hyp-001/artifacts/desk-research-evidence.md`）。

对 Desirability 类假设以"结构性原则一致性"作为 user signal 的替代，本属方法学软约束；但本 spec 是 HF 自适配（HF 用户 ≈ HF 原则的承担者），且 spec §12 Open Risks + `progress.md` Open Risks + probe-result §6 三处显式承接"未来真实用户访谈可在 spec / design / 投产阶段顺手追问以提升外部置信度（nice-to-have，非阻塞）"+ "如反向证据通过 `hf-increment` 修订"的回流路径，证据链对 HF 自适配场景成立，承接诚实，本评审不就此打回。后续如接入真实 HF 用户访谈通道，应按 spec §12 与 `progress.md` Open Risks 既定路径回修，不属于本评审阻塞器。

## 发现项

- [minor][LLM-FIXABLE][Q2] §3 Success Metrics 的 Lagging Indicator "用户可见行为漂移条数...目标趋势下降" 缺数值阈值，"趋势下降"无 baseline / delta，冷读时无法形成通过 / 不通过判断。建议改写为可冷读判定的形式，例如"在引入本 gate 后 N=3 次连续增量开发的 reviewer 抽样窗口内，'reviewer 标 pass 但实际 README 漂移' 案例数 = 0"（与 §3 Threshold 同款判定形式）。Q2 / Q6。
- [minor][LLM-FIXABLE][Q4] §9 NFR-001 Acceptance "两次返回的 verdict 字段 + dimension breakdown 必须完全一致" 与 NFR-001 QAS Response Measure "允许 evidence 文件名 timestamp 不同，但 verdict 词与维度判定结果必须一致" 在严格度上略有不一致："完全一致" 字面包含 timestamp。建议 Acceptance 句改写为"两次返回的 `verdict` 字段与 `dimension breakdown` 完全一致（允许 evidence 文件名 timestamp 不同）"，与 QAS 同语义。Q4 / Q7。
- [minor][LLM-FIXABLE][Q5] §8 全部 8 条 FR 优先级均为 Must，未给出 Should / Could 差异化。这在"新 skill 最小契约 8 条全部不可少" 的语境下可辩护，但 cold reader 会触发 Q5 "默认全部最高优"的怀疑。建议在 §8 段首加一句话理由，例如 "本 gate 的 8 条 FR 共同构成 'gate skill 可被冷读消费' 的最小契约，缺任一条则 gate 不可宣告完成；故全部 Must。" Q5。
- [minor][LLM-FIXABLE][A3] §6.1 列出 "在 `hf-workflow-router` 的 transition map 中加入新 gate 节点" + "在 `hf-completion-gate` 的 evidence bundle 中显式列入本 gate 的 verdict" + "在 `hf-finalize` 的 evidence matrix 中显式 reference 本 gate" 三条整合点描述了 *其他 skill 的预期行为*，靠近 A3 设计泄漏边界。建议改写为"本 gate 必须输出可被既有 evidence bundle / closeout pack 约定 reference 的 verdict 文件"（把责任落在本 gate 输出契约而非下游 skill 行为变更上）。当前形态对 spec 评审通过不构成阻塞，但可在 `hf-specify` 回修时顺手收紧。A3 / Q4。

## 父会话已应用的回修（按 hf-spec-review Step 5 "LLM-FIXABLE 不转嫁给用户"）

- ✅ Q2 finding：§3 Lagging Indicator 已重写为 "N=3 次连续增量开发 reviewer 抽样窗口内 'pass 但实际漂移' 案例数 = 0"
- ✅ Q4 finding：NFR-001 Acceptance 已加 "（允许 evidence 文件名 timestamp 不同；与 QAS Response Measure 一致）" 子句
- ✅ Q5 finding：§8 段首已添加优先级总体说明
- ✅ A3 finding：§6.1 三条整合点已重写为本 gate 输出契约形式（"本 gate 必须输出符合既有 evidence bundle 与 closeout pack reference 约定的 verdict 文件"），把责任落在本 gate 自身输出
- ✅ HYP-002 行同步更新：Confidence medium → high (closed by spec-review)、Blocking 是 → 否；§4 段尾的"Blocking 假设关闭策略"段也同步更新为"已于 2026-04-23 关闭"，"本 spec 当前无 Blocking 假设"

## 缺失或薄弱项

- §4 HYP-002 行 Blocking 字段在本评审通过后将语义性翻为 "否"。当前 spec 状态正确（"评审中、待 reviewer 判定"）；建议 `hf-specify` 在回修阶段同步更新 HYP-002 行（参照 HYP-001 post-probe 同款方式）→ **已应用**。
- HYP-001 关闭证据为 desk-research-only。本评审已在上文判定证据链对 HF 自适配场景成立（理由：HF 用户 ≈ HF 原则承担者；spec §12 + `progress.md` Open Risks + probe-result §6 三处承接 nice-to-have 用户信号回流路径）。`hf-specify` 不需为此回修；spec 的 future-proof 路径已就位。
- §3 Outcome Metric 是叙事性表述（"成为可被冷读的 gate verdict + fresh evidence"），定量 bar 落在 Threshold 行。这符合 `success-metrics-and-hypotheses.md` 模板表头分工，不构成 finding；可在未来增量内顺手把 Outcome Metric 一句话替换为度量化短语（例如"每次 task / workflow closeout 产出 1 份带 verdict 的 doc-freshness 文件"），但当前不阻塞。

## Precheck 状态

未触发 precheck 阻塞：spec 草稿稳定可定位（`features/001-hf-doc-freshness-gate/spec.md`），路径符合 `sdd-artifact-layout.md` Feature 目录约定；`progress.md` Current Stage / Next Action / Workflow Profile / Execution Mode 与本次派发一致；上游 discovery + discovery-review + HYP-001 probe 三链证据齐全且互相一致，无 route / stage / profile / 证据冲突，无需 `reroute_via_router`。

## 下一步

- `通过` → **`规格真人确认`**（auto mode 仍不可跳；按 `using-hf-workflow` Step 3 + `hf-specify` Hard Gates）
- 4 条 minor LLM-FIXABLE finding 已由父会话应用（见上方"已应用的回修"段）
- §4 HYP-002 行 Blocking / Confidence 已同步更新
- USER-INPUT 数 = 0，无需向用户发起最小定向问题

## 交接说明

- `规格真人确认`：本评审 verdict = 通过；4 条 LLM-FIXABLE 已回修；待父会话发起 approval step（`auto` 模式下需写 approval record，**不能跳过**）
- `hf-workflow-router`：本评审无 reroute 触发条件
- 评审通过 + `规格真人确认` 落盘后才能进入 `hf-design`（`hf-spec-review` Hard Gate）

## 结构化返回（JSON）

```json
{
  "conclusion": "通过",
  "next_action_or_recommended_skill": "规格真人确认",
  "record_path": "features/001-hf-doc-freshness-gate/reviews/spec-review-2026-04-23.md",
  "key_findings": [
    "[minor][LLM-FIXABLE][Q2] §3 Lagging Indicator '趋势下降' 缺数值阈值，应改写为 reviewer 抽样窗口内 'pass 但实际漂移' 案例数 = 0 之类可冷读判定形式",
    "[minor][LLM-FIXABLE][Q4] NFR-001 Acceptance '完全一致' 与 QAS Response Measure 允许 evidence 文件名 timestamp 不同 略不一致，建议 Acceptance 句子并入 timestamp 例外",
    "[minor][LLM-FIXABLE][Q5] §8 全部 8 条 FR 均为 Must 但未给差异化理由，建议段首一句话说明 8 条共同构成 gate skill 最小契约",
    "[minor][LLM-FIXABLE][A3] §6.1 三条整合点描述了下游 skill 的预期行为，靠近 A3 边界；建议改写为本 gate 的 'verdict 文件输出契约'，把责任落在自身输出而非下游行为变更"
  ],
  "needs_human_confirmation": true,
  "reroute_via_router": false,
  "finding_breakdown": [
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "Q2",
      "summary": "§3 Lagging Indicator '趋势下降' 缺数值阈值；建议改写为可冷读判定形式（与 §3 Threshold 同款）"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "Q4",
      "summary": "NFR-001 Acceptance '完全一致' 字面包含 timestamp，与 QAS Response Measure 允许 timestamp 不同 略不一致"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "Q5",
      "summary": "§8 全部 8 条 FR 均 Must 未差异化；建议段首一句话说明 8 条共同构成 gate skill 最小契约"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "A3",
      "summary": "§6.1 三条整合点描述其他 skill 的预期行为，靠近 A3 边界；建议改写为本 gate 的输出契约形式"
    }
  ]
}
```
