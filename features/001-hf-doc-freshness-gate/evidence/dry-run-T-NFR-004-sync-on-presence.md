# Dry Run T-NFR-004-sync-on-presence — Sync-on-Presence Tolerance

- Date: 2026-04-23
- Profile: full（用 full profile 是为了激活更多维度，验证未启用资产正确判 N/A）
- Purpose: 验证 NFR-004 "未启用文档载体维度 = N/A，不构成 blocked"

## Dry Run Setup

- 被测对象: `features/001-hf-doc-freshness-gate/` 自身
- full profile 强制激活全部 spec §6.2 本 gate ✅ 行
- 仓库当前对外可见文档载体状态（基线即测试环境）：

| 文档载体 | 当前仓库状态 |
|---|---|
| 仓库根 `README.md` 产品介绍段 | ✅ 存在 |
| 仓库根 `README.zh-CN.md` (i18n 副本) | ✅ 存在（README.md 的中文副本，HF 自身就有 i18n） |
| `Conventional Commits` `docs:` 标记 | ✅ git log 可访问 |
| 模块层 / 子包 README | ❌ **不存在**（无 `packages/` / `apps/` / `src/<module>/README.md`） |
| 公共 API docstring / OpenAPI | ❌ **不存在**（HF 是 prose skill pack，无 runtime API） |
| 自动文档站 source | ❌ **不存在**（HF 仅靠 GitHub README 与 docs/ markdown） |
| `CONTRIBUTING.md` | ❌ **不存在** |
| onboarding doc | ❌ **不存在**（按需启用） |

## 维度判定

按 `references/profile-rubric.md` §"维度判定流程"：

| 维度 | step 1: 文件系统检测 | step 2: change list 触发 | step 3: 同步状态 | verdict | evidence 标注 |
|---|---|---|---|---|---|
| 仓库根 README 产品介绍段 | ✅ 存在 | ✅ 触发（引入新 skill 影响 skill 列表） | 当前未同步（待 finalize closeout） | partial 或 N/A | "本 task=T7 不更新 README；该更新由 hf-finalize 同步——按 §6.2 责任矩阵 README 顶层导航行归 finalize；产品介绍段同步在 closeout commit" |
| 仓库根 README 中 *active feature / ADR 索引行* (指针式导航) | — | — | — | **out of scope** | "by spec §6.2 + responsibility-matrix.md 归 hf-finalize" |
| 模块层 README | ❌ 不存在 | — | — | **N/A** | "项目当前未启用此资产" |
| 公共 API doc / OpenAPI | ❌ 不存在 | — | — | **N/A** | "项目当前未启用此资产" (HF 是 prose skill pack) |
| 自动文档站 | ❌ 不存在 | — | — | **N/A** | "项目当前未启用此资产" |
| `README.zh-CN.md` (i18n) | ✅ 存在 | ✅ 触发（同 README.md） | 同 README.md | 同 README.md verdict | "i18n 副本同步状态与 README.md 同步" |
| `CONTRIBUTING.md` | ❌ 不存在 | — | — | **N/A** | "项目当前未启用此资产" |
| onboarding doc | ❌ 不存在 | — | — | **N/A** | "项目当前未启用此资产" |
| Conventional Commits docs 标记 | ✅ git log | ✅ 触发 | docs commit 待 finalize 阶段创建 | N/A | "本 task 不创建 docs commit；finalize 阶段同步" |

## NFR-004 判定

**关键检测点**：5 个 "❌ 不存在" 的维度（模块层 README / 公共 API doc / 自动文档站 / CONTRIBUTING.md / onboarding doc）**全部** verdict = `N/A`，**没有**任何一个被误判为 `blocked`。

→ **NFR-004 sync-on-presence 容错 PASS** ✅

evidence 标注全部使用规范的 "项目当前未启用此资产" 措辞（与 SKILL.md Hard Gates "未启用文档载体 → verdict 该维度 = N/A，**不构成 blocked**" 完全一致）。

## 整体 verdict 聚合（参考 SKILL §3 末尾规则）

按聚合规则：

- 任一 blocked → blocked → **不触发**（无 blocked 维度）
- 任一 partial → partial → **可能触发**（仓库根 README 维度若判 partial）
- 否则全部 ∈ {pass, N/A} → 至少一个 pass → pass；全部 N/A → N/A

本 dogfooding dry run 整体 verdict：

- **若按"本 task 不需更新 README，封 finalize 同步"判定 → 整体 verdict = N/A**（5 维 N/A + 仓库根 README + i18n + Commits 全 N/A）
- **若按"本 task user-visible change 已经触发但未同步" 判定 → 整体 verdict = partial**（README 维度 partial + 其余 N/A）

实际选定：**N/A**（理由：本 dry run 的 user-visible change = 引入新 skill，但同步该 change 是 finalize 既有合同覆盖的 CHANGELOG / 顶层导航 / ADR 状态翻转 —— 按 §6.2 责任矩阵跨 skill 归属，本 gate 不重叠 finalize 职责；仓库根 README "产品介绍段" 与 "顶层导航行" 在本 feature 的同步事实上是同一个 finalize 同步动作，不应被本 gate 重复 verdict）。
