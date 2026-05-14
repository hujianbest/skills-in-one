# Audit Methodology for Large C/C++ Codebases

This is the playbook executed by `mdc-bug-patterns`. SKILL.md gives the four-pass overview; this file gives the operational detail.

> **Read me before Pass 1.** Re-read the relevant section before each pass.

## Guiding Principles

1. **Trade tokens for code quality.** The unit of audit is a code unit (function, method, small file). The LLM reads each unit end-to-end and applies all relevant templates as a checklist. This is expensive on purpose; it produces findings that survive scrutiny.
2. **Pattern matching is a prior, not a verdict.** Grep / ripgrep tells you *where to look first*; the LLM decides whether there is a bug by reading the code.
3. **Coverage is measurable.** Every unit in scope has one of three statuses: reviewed (with or without findings), inconclusive (audit gap), or un-reviewed (audit gap). The report says how many of each.
4. **Bounded effort beats perfectionism.** Each *uncertain question* gets ~10 minutes of follow-up reads; if still uncertain, downgrade and continue. Do not abandon the unit.
5. **The default report is "high signal".** Low-confidence findings live in a separate "audit gaps" section so reviewers do not drown in maybes.

## Pass 1 — Map (cheap, structural)

### Goal

Build a small, structured picture of the repository that lets you (a) scope subsequent passes, (b) decide which templates apply, (c) recognise FP filters that come from the project's own conventions (e.g. a custom smart pointer).

### Required outputs

Keep these in your TodoWrite or scratch notes.

0. **Specialty selection** — read `references/templates.md` (the specialty index). Use its decision tree to choose one of:
   `memory-safety` / `lock-usage` / `concurrency-and-isr` / `resource-management` / `logic-and-numeric` / `embedded-hardware`. Loading multiple is acceptable but should be deliberate (the most common pairing is `lock-usage` + `concurrency-and-isr` for an embedded sync audit). Loading all 6 is rare ("comprehensive audit"). Recording which specialties you chose is itself an audit artefact (cite it in Pass 4).
1. **Layout & size**
   - Top-level directories and approximate LoC each.
   - Tooling: `tokei` → `cloc` → `find … -name '*.c*' | xargs wc -l`.
2. **Build system & entry points**
   - `CMakeLists.txt` / `Makefile` / `BUILD.bazel`.
   - Main binaries, libraries, plugins.
3. **Concurrency surface** (if concurrency is in scope)
   - `rg -n 'std::thread|pthread_create|std::async|tbb::|absl::Mutex|std::mutex|std::shared_mutex|std::atomic|std::condition_variable' --type cpp`
   - Identify which subsystems own threads vs. which are called from them.
4. **Memory ownership conventions**
   - Custom smart pointers (`MyPtr`, `RefCountedPtr`, `scoped_refptr`, `intrusive_ptr`, etc.). These become FP filters.
   - Allocator wrappers (`Allocate`, `New<T>`, `Make…`).
5. **Existing safety nets** (so you don't re-find what's already caught)
   - Sanitizers: search `CMakeLists.txt` / `Makefile` / CI configs for `-fsanitize=address|thread|undefined|memory`.
   - Static analyzers: `clang-tidy`, `cppcheck`, `infer`, `coverity` configs.
   - Existing tests / fuzz harnesses.
6. **In-scope vs. out-of-scope**
   - Vendored / third-party (`third_party/`, `vendor/`, `external/`) is out-of-scope unless requested.
   - Generated code (`*.pb.cc`, `moc_*.cpp`, etc.) is out-of-scope by default.

### Time budget

Cheap and structural — no per-line LLM reading here. Aim for ≤ 5 minutes of tool calls for ≤ 1M LoC. Depth comes in Pass 3.

## Pass 2 — Prioritise units (rg signals → ranked unit list)

### Goal

Produce a ranked list of **code units** to deeply review in Pass 3. The unit of audit is a function / method (preferred) or a small file (~ ≤ 200 LoC) when granularity is hard to determine.

### Procedure

1. Decide which specialty file(s) apply (you already chose in Pass 1, step 0). Defaults:
   - User asked for "锁使用 / mutex / lock_guard / 临界区 / 死锁 / 优先级反转" → `lock-usage.md` (often paired with `concurrency-and-isr.md`).
   - User asked for "concurrency / ISR / RTOS / atomic / volatile / 数据竞争" → `concurrency-and-isr.md` (often paired with `lock-usage.md`).
   - User asked for "memory safety / 内存安全 / DMA / 指针" → `memory-safety.md`.
   - User asked for "外设 / 资源 / 时钟 / 任务管理 / fd 泄漏" → `resource-management.md` (mutex unlock 泄漏在 `lock-usage.md`).
   - User asked for "整数 / 字节序 / 可移植性" → `logic-and-numeric.md`.
   - User asked for "看门狗 / 低功耗 / Flash / IRQ-disable 临界区过长" → `embedded-hardware.md`.
   - User asked for "general code review" → all 6 specialty files.
2. Run `scripts/scan_candidates.py --specialty <name> --path <scope> --out candidates.jsonl` (single specialty), or omit `--specialty` to scan all specialties under `references/templates/`. `--template ID` further narrows to a single template.
3. Run `scripts/list_units.py --candidates candidates.jsonl --path <scope> --out units.jsonl`. Output is a ranked work-list:
   ```json
   {"unit_id":"src/cache.cc::Cache::Insert", "file":"src/cache.cc",
    "line_start":80, "line_end":110, "score":17.5,
    "signals":["mem-leak-new-no-delete","con-unsynchronized-shared-write",
               "primitive:std::mutex","primitive:new"]}
   ```
4. Process units in priority order in Pass 3. Write a partial coverage report after every batch of ~20 units so progress survives a context reset.
5. Units with very low scores (no candidates, no concurrency / memory primitives) may be reviewed last or skipped with explicit notation.

### Pass 2 anti-patterns

- "I read a few files and inferred the rest" → run the queries and produce the ranked list.
- "The template doesn't apply because the codebase is modern C++" → still rank the units; modern code uses `new` more than you'd guess.
- "Too many units, I'll spot-check" → process by priority and explicitly mark un-reviewed units as audit gaps.
- Treating the candidate list as a finding list → no, it's only a *signal* for ranking. Findings come from Pass 3.

## Pass 3 — Unit-by-unit deep semantic review (the token spend)

### Goal

For each prioritised unit, the LLM **reads the unit end-to-end and applies every relevant template as a checklist**, recording findings, suppressed candidates, and inconclusive items.

### The Unit Review Protocol

For every unit:

1. **Read the entire unit.** Function or method body, not just matched lines. If member state is involved, read the class declaration.
2. **Read necessary callers.** `rg -n '\b<func_name>\s*\('` (bounded to ≤ 20 callers). For functions whose preconditions matter (null pointers, lock-set, thread affinity), this is mandatory.
3. **Read necessary callees.** For ownership transfer, lock acquisition inside helpers, thread-pool posts, etc., read the called function's relevant parts.
4. **Decide which templates are relevant.** Use the unit's signals (from `list_units.py`) plus your read of the code. Concurrency unit ⇒ all `con-*`. Allocator unit ⇒ all `mem-*`. A function returning `int` from a multiplication ⇒ `int-*`. Apply *all* relevant templates in this single read of the unit.
5. **Run each relevant template's `verification` checklist.** Per `references/templates.md`. For each potential finding, construct the `required_evidence` block.
6. **Apply false-positive filters.** Read `references/false-positive-filters.md` and explicitly rule out applicable filters. Cite which filters you ruled out.
7. **Decide outcome per finding:**
   - **Confirmed** — promote to a finding with full `required_evidence`.
   - **Suppressed** — cite the FP filter and the line(s) that justify suppression.
   - **Inconclusive** — record as `low` confidence; counts as audit gap.
8. **Record outcomes** with `scripts/coverage_tracker.py`:
   - `mark --status confirmed --confidence high|medium --reason "..."` per finding.
   - `mark --status suppressed --filter <fp.id> --reason "..."` per ruled-out candidate.
   - `mark --status inconclusive --reason "..."` per uncertain.
   - For units that produced no findings *after* deep review, record an explicit unit-level "reviewed, clean" note. This is how coverage is measured.

### Token discipline

- Spend generously to fully understand the unit. Re-read functions, follow callers, follow callees. Quality > token count.
- Bounded effort applies *per uncertain sub-question*, not per unit. Each sub-question gets ~10 minutes (≈ 5–10 file reads). If still uncertain, downgrade that finding to `low` and continue with the unit.
- A unit that yields 0 findings is a *positive result* and must be recorded.

### Concurrency Deep Dive

Concurrency findings are the highest-FP category. Apply this protocol for every unit that touches concurrency primitives:

1. **Determine the access** — variable, member, or memory region under suspicion. Note its declaration and storage class.
2. **Build a thread-affinity sketch.** Which threads can execute this function? Search:
   - Direct thread starts: `std::thread(..., &Class::Method, …)`, `pthread_create(..., Class::Method, …)`.
   - Indirect: posted to thread pools / event loops / executors. Search the project's executor-post idiom.
   - If exactly one thread executes the function in all reachable callers, the access is **single-threaded** → suppress with `fp.concurrency.single-threaded`.
3. **Build a lock-set sketch.** Walk callers and the function body to determine which mutexes are held when this access executes.
   - If a lock consistently protects the access on **all** read and write paths, suppress with `fp.concurrency.protected-by-lock`.
   - If only some paths hold a lock, that asymmetry is the bug — report it with the lock-mismatched path as evidence.
4. **Check atomics / memory order.** If the variable is `std::atomic<T>`, the data race goes away but `memory_order_relaxed` may still be wrong (`con-missing-memory-order`).
5. **Check publication.** If the field is only written before the object is published to other threads (e.g. set in constructor before `std::thread` starts), suppress with `fp.concurrency.published-once`.
6. **For deadlock candidates,** build a 2-D lock acquisition graph: per function, list `(acquired_locks, additional_locks_taken)`. A cycle in this graph is a real deadlock candidate. No cycle → suppress with `fp.deadlock.no-cycle-observed`.

If any of steps 2–6 cannot be completed within the bounded effort, mark `inconclusive` rather than guessing.

### Memory Safety Deep Dive

For every unit that allocates or holds raw pointers / handles:

1. **Identify the owner.** Trace each pointer from allocation to last use. The owner is whoever is responsible for `delete` / cleanup.
2. **Enumerate exits.** Every `return`, `throw`, `goto`, `co_return`, exception path. The bug exists if **any** exit reachable after allocation does not release.
3. **Check ownership transfer.** If the pointer is passed to a function whose name or signature implies ownership transfer (e.g. `std::unique_ptr<T>(p)`, `Take`, `Release`, `into_*`, `add_child`, `set_*` on a container that owns its children), that exit is OK.
4. **Check container storage.** If the pointer is stored in a member of a class that has a destructor releasing it, that exit is OK (still note the contract is fragile).
5. **For UAF / double-free,** trace the pointer past the freeing call. A read or second free after the first free is the bug.
6. **For uninitialized reads,** require both: (a) a member or stack variable not initialized in all constructors / control flow paths, **and** (b) a read on a path that does not write first.

### Logic / Integer Deep Dive

For every unit doing arithmetic on values that flow from input or are used as sizes:

1. **Compute the input domain.** What range can each operand take, given upstream checks (function preconditions, validated parameters, bounded loop indices)?
2. **If the domain cannot reach the dangerous value**, suppress with reason "domain bounded by `<file:line>` check".
3. For overflow templates, prefer reporting only when the value can plausibly come from untrusted input or from a multiplication used as an allocation size.

## Pass 4 — Report

See `references/reporting.md` for the format. Key rules:

- Default report contains only `high` and `medium` findings.
- Include a coverage table: units in scope / units reviewed / units inconclusive / units un-reviewed; per-template hit / suppression / inconclusive counts.
- List `low` / `inconclusive` items in an "audit gaps" section so the human reviewer can decide whether to invest more time.
- For every confirmed finding, the evidence block must independently justify the bug — do not rely on the reader to re-derive it.

## Working in Long Sessions

Large audits exceed a single context window. Discipline:

- After Pass 1, write the Map to a working file (`audit/00-map.md`).
- After Pass 2, persist the unit work-list to `audit/01-units.jsonl`.
- After every batch of ~20 units in Pass 3, update `audit/coverage.json` via `scripts/coverage_tracker.py` and write a partial findings file (`audit/findings-<batch>.md`).
- The final Pass 4 deliverable concatenates and de-duplicates partials, then renders to Excel via `scripts/excel_helper.py`.

## Calibration Examples

These are the "tests" of this skill — re-read them when you find yourself rationalising a weak finding.

### Example A — Suppressed `mem-leak-new-no-delete`

Candidate: `Foo* f = new Foo(); registry_->Register(f);`
- Verification: read `Registry::Register` — signature is `void Register(Foo*)`; the registry stores raw pointers but `Registry::~Registry()` calls `delete` on every entry.
- Filter applied: `fp.ownership.container-with-destructor`.
- Outcome: **suppressed**, recorded with reason "ownership transferred to Registry; ~Registry deletes entries (registry.cc:54)".

### Example B — Confirmed `con-unsynchronized-shared-write`

Candidate: `cache_size_ += entry.size;` inside `Cache::Insert`.
- Thread affinity: `Insert` is called from worker threads (verified at `worker.cc:88`) and from the main thread's eviction tick.
- Lock set: `Insert` takes `cache_mutex_` at top. But the candidate write is in a helper method `BumpCacheSize` that is also called from `RemoveExpired`, where `cache_mutex_` is **not** held (verified at `cache.cc:142`).
- Evidence: `cache.cc:88` (writer with lock), `cache.cc:142` (writer without lock), `cache.h:34` (no atomic).
- Outcome: **confirmed**, `high` confidence.

### Example C — Inconclusive `con-lock-ordering-deadlock`

Candidate: `mutex_a.lock(); ... callback(); ...` in `Foo::DoWork`; callback is a `std::function` provided by user.
- Verification: cannot statically determine what locks `callback` takes within bounded effort.
- Outcome: **inconclusive**, `low` confidence, reported under audit gaps with the recommendation "audit all callers that supply a callback to `Foo::DoWork`".

## Anti-Patterns Checklist (re-read at end of every Pass 3 batch)

- [ ] I am citing line numbers in every finding.
- [ ] I am naming the FP filter I ruled out for borderline cases.
- [ ] I have read the *full* function body of every unit I claim to have reviewed.
- [ ] I have read at least the immediate callers when caller invariants matter.
- [ ] I have not silently dropped any candidate or unit — each is recorded in the tracker.
- [ ] I have not promoted any finding without all `required_evidence` items.
- [ ] My `high` confidence findings have a complete data-flow / lock-set / thread-affinity trace.
- [ ] I have not "saved tokens" by skipping deep reads. Tokens spent on quality is the point.
