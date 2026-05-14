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

## Excel Output

`scripts/excel_helper.py` consumes the JSON array of findings. Columns:

| Column | Source field |
|---|---|
| Severity | `severity` (color-coded) |
| Confidence | `confidence` |
| Category | `category` |
| Template ID | `template_id` |
| Name | `name` |
| Location | `location.file:line` (`function` if available) |
| Summary | `summary` |
| Evidence | `required_evidence` (joined, monospace) |
| FP Filters Ruled Out | `false_positive_filters_ruled_out` |
| Fix Suggestions | `fix_suggestions` |
| Context | `context` (monospace, wrap) |
| Timestamp | run timestamp |

Findings of `confidence: low` are written to a separate sheet `Audit Gaps`.
