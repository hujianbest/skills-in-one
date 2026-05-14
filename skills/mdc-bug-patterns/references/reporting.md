# Reporting Format

Pass 4 produces a single audit report. The format below is mandatory because it doubles as the input to `scripts/excel_helper.py`.

## Report Structure

1. **Audit metadata** — repo, commit SHA, scope (paths included/excluded), templates applied, who/when ran the audit.
2. **Coverage summary** — table of candidates per template and how each was disposed.
3. **Findings** — `high` and `medium` confidence items, sorted by (severity, confidence, file).
4. **Audit gaps** — `low` confidence and `inconclusive` items, plus any un-processed shards from Pass 2.
5. **Recommendations** — prioritised fix list and next steps (re-run, expand scope, add tests, etc.).

## Finding Schema (JSON)

Each finding is one JSON object. The Excel helper consumes a list of these.

```json
{
  "id": "con-unsynchronized-shared-write::src/cache.cc:142",
  "template_id": "con-unsynchronized-shared-write",
  "name": "Unsynchronized shared write",
  "category": "concurrency",
  "severity": "critical",
  "confidence": "high",
  "location": {
    "file": "src/cache.cc",
    "line": 142,
    "function": "Cache::RemoveExpired"
  },
  "summary": "cache_size_ is mutated without holding cache_mutex_ in RemoveExpired, while Insert holds cache_mutex_ on every write.",
  "required_evidence": {
    "writer_with_lock":   "src/cache.cc:88   cache_mutex_.lock(); ... cache_size_ += entry.size;",
    "writer_without_lock":"src/cache.cc:142  cache_size_ -= entry.size;  // no lock",
    "thread_affinity":    "src/worker.cc:88 RemoveExpired posted to worker pool; Insert called from request threads",
    "field_declaration":  "src/cache.h:34   size_t cache_size_;  // not std::atomic"
  },
  "false_positive_filters_ruled_out": [
    "fp.concurrency.single-threaded",
    "fp.concurrency.protected-by-lock",
    "fp.concurrency.published-once",
    "fp.concurrency.atomic-with-correct-order"
  ],
  "fix_suggestions": [
    "Acquire cache_mutex_ in RemoveExpired before mutating cache_size_.",
    "Or change cache_size_ to std::atomic<size_t> and audit every read for ordering."
  ],
  "context": [
    "  140:   for (auto it = entries_.begin(); it != entries_.end();) {",
    "  141:     if (it->second.expired_at < now) {",
    ">>142:       cache_size_ -= it->second.size;",
    "  143:       it = entries_.erase(it);",
    "  144:     } else { ++it; }"
  ]
}
```

Required fields (all must be present, non-empty):
- `id`, `template_id`, `name`, `category`, `severity`, `confidence`
- `location.{file,line}`
- `summary`
- `required_evidence` — keys must match the template's `required_evidence` schema; each value is a `<file:line> <code excerpt>` string
- `false_positive_filters_ruled_out` — must list the FP filters from the template plus the cross-cutting ones in `references/false-positive-filters.md` that you actively ruled out
- `fix_suggestions` (≥ 1)
- `context` — ≥ 5 lines around the primary location with the bug line marked `>>`

A finding missing any required field is **invalid** — drop it or downgrade to `low` and move it to audit gaps.

## Severity vs Confidence

These are independent axes. Both are required.

| Axis | Values | Meaning |
|---|---|---|
| `severity` | `critical`, `high`, `medium`, `low` | How bad if true. Comes from the template default; can be raised/lowered with reason. |
| `confidence` | `high`, `medium`, `low` | How sure we are it is true. Comes from the template's `confidence_rubric`. |

A `critical / high` finding is "this will probably crash / corrupt and we are confident". A `critical / low` finding is a maybe-crash worth investigating but not yet proven.

## Coverage Summary Table

```
| template_id                          | candidates | confirmed | suppressed | inconclusive | coverage |
|--------------------------------------|------------|-----------|------------|--------------|----------|
| mem-leak-new-no-delete               |        184 |         3 |        180 |            1 |   99.5%  |
| con-unsynchronized-shared-write      |         42 |         2 |         38 |            2 |   95.2%  |
| con-lock-ordering-deadlock           |         11 |         1 |          7 |            3 |   72.7%  |
| ...                                  |            |           |            |              |          |
```

`coverage = (confirmed + suppressed) / candidates`. A coverage below 80% is itself an audit gap.

## Audit Gaps Section

For each `inconclusive` candidate or un-processed shard:

```
- [con-lock-ordering-deadlock] src/io/server.cc:204
  Reason: callback supplied by user code; cannot statically determine its lock-set.
  Recommendation: enumerate all callers of Server::OnEvent and audit their callbacks for mutex acquisition.
```

For shards not processed:

```
- [mem-leak-new-no-delete] third_party/legacy/*  — 612 candidates, not processed
  Reason: out-of-scope per Pass 1; user did not request third_party.
```

## Recommendations Section

A short prioritized list, e.g.:

```
1. Fix cache.cc:142 unsynchronized write (con-unsynchronized-shared-write, critical/high). Add lock or atomic.
2. Fix io/server.cc:88 lock-order inversion with `engine_mutex_` then `worker_mutex_` (con-lock-ordering-deadlock, critical/high). Use std::scoped_lock.
3. Adopt std::unique_ptr in TaskQueue::Push to eliminate 4 leak candidates (mem-leak-new-no-delete, high/medium).
4. Re-audit with `--include third_party/legacy` if those modules are shipped in production.
```

## Excel Output (中文, 面向人工复核)

The deliverable to the human reviewer is a Chinese-language workbook produced by `scripts/excel_helper.py`. The workbook is designed for **at-a-glance triage and per-finding sign-off** — every column header, severity / confidence / category label is in Chinese, and each finding row carries a dropdown for the reviewer to mark agreement.

### Invocation

```bash
scripts/excel_helper.py \
    --bugs-file findings.json \
    --coverage  coverage.json \
    --repo "org/repo" --scope "src/io/" --reviewer "alice" \
    --output bug_report.xlsx
```

`--coverage` is optional; when provided (a `coverage_tracker.py` DB), the overview and per-template stats are populated from real Pass 3 outcomes. Without it, those stats are derived from the findings list alone.

### Workbook structure (4 sheets)

#### 1. `审查总览` — Audit Overview

- **基本信息**: 仓库 / 分支, 审计范围, 审计人, 审计时间, 审计模板数, 已审候选数 / 总候选数
- **发现统计** table: rows by severity (严重 / 高 / 中 / 低), columns 高可信 / 中可信 / 审计盲区(低/待定) / 合计 — with severity-coloured row labels.
- **阅读指引**: a 5-point Chinese reading guide telling the reviewer how to use the other sheets, what severity vs. confidence mean, and how to fill in the human-confirmation column.

#### 2. `发现明细` — Findings (high + medium confidence)

One finding per row, frozen header (row 1) and frozen first two columns (编号 + 严重程度), `auto_filter` on every column.

| Column | Source | Notes |
|---|---|---|
| 编号 | row index | for citing in code review comments |
| 严重程度 | `severity` | translated; bold, severity-coloured cell |
| 可信度 | `confidence` | translated |
| 类别 | `category` | translated to 内存安全 / 并发 / 资源管理 / 空指针 / 逻辑·数值 |
| 模板ID | `template_id` | stable id (English; matches `references/templates.md`) |
| 文件:行 | `location.file:line` | for fast jump in the editor |
| 所在函数 | `location.function` | optional |
| 问题摘要 | `summary` (or `name`) | one-line Chinese summary |
| 证据 (file:line + 代码) | `required_evidence` | bullet list, **monospace**, one item per evidence key |
| 已排除的误报模式 | `false_positive_filters_ruled_out` | the `fp.*` ids that the LLM actively ruled out |
| 修复建议 | `fix_suggestions` | bullet list |
| 代码上下文 (>>为问题行) | `context` | monospace, line-numbered, problem line marked `>>` |
| **人工确认** | (empty) | dropdown: ✓ 同意 (确认是bug) / ✗ 误报 (附理由) / ? 待定 (需更多上下文) |
| **备注** | (empty) | free text for the reviewer |

Row backgrounds are tinted by severity (light pink / light orange / light yellow / light green).

#### 3. `审计盲区` — Audit Gaps (low confidence + inconclusive)

Same column structure as `发现明细`. Findings whose `confidence` is `low`, or whose `status` is `inconclusive` / `open`, go here. The 备注 column is pre-populated with the suppression / inconclusion reason if available, so the reviewer can quickly decide whether to dig deeper.

#### 4. `覆盖率明细` — Coverage Detail

Two stacked tables:

- **按模板的覆盖统计** — 模板ID / 类别 / 默认严重 / 候选数 / 已确认 / 已抑制 / 不确定 / 覆盖率. Computed from `coverage.json` when provided, else from the findings list.
- **按文件的发现统计** — 文件 / 高可信发现 / 中可信发现 / 低/不确定 / 总发现.

These two tables together let the reviewer answer "did we look hard enough at every template?" and "which files concentrate the risk?".

### Human-confirmation workflow

1. Open the workbook. Read `审查总览` for the high-level picture.
2. Open `发现明细`. The auto-filter and severity colours let you focus on `严重` / `高可信` first.
3. For each row, read 问题摘要 → 证据 → 代码上下文. Use 已排除的误报模式 to verify that the relevant FP filters were actually ruled out.
4. In the **人工确认** dropdown, pick one of:
   - `✓ 同意 (确认是bug)` — agree, the bug is real.
   - `✗ 误报 (附理由)` — disagree, with a reason in 备注.
   - `? 待定 (需更多上下文)` — needs more investigation.
5. After finishing 发现明细, do the same for 审计盲区 — these are not confirmed bugs but the audit could not rule them out within bounded effort.
6. Use `覆盖率明细` to decide whether to expand scope (e.g. re-audit a template with 0% coverage on a critical file).

### Schema notes

The finding JSON schema (above) stays in **English** — it is the machine-readable interface between the LLM-driven Pass 3 and the renderer. All Chinese is produced at render time. This means:

- LLM agents producing findings always write English keys (`severity`, `confidence`, `category`, `required_evidence`, `false_positive_filters_ruled_out`, `fix_suggestions`, `context`).
- Human reviewers see Chinese throughout the Excel.
- The English `template_id` is preserved so reviewers and engineers can search the codebase for the same id.

A finding missing any required field is **invalid** — drop it or downgrade to `low` and move it to the 审计盲区 sheet.
