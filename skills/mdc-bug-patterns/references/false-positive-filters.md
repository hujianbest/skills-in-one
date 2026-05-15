# Cross-Template False-Positive Filters

These filters apply across many templates and are the single biggest lever for reducing FP rate. Apply them in Pass 3 before promoting any candidate to a finding. Each filter has a stable ID — cite it in the `suppressed_by` field of the coverage tracker so reviewers can audit your suppressions.

---

## fp.ownership.smart-pointer

**Applies to:** `mem-leak-*`, `mem-array-*`, `mem-double-free`, `mem-use-after-free`, `mem-no-destructor`.

**Suppress when:** the raw pointer returned by `new` (or `malloc`) is, on **every** subsequent path, immediately captured by a smart-pointer-like owner.

Owner detection (extend with project-local owners discovered in Pass 1):

- `std::unique_ptr<T>(p)`, `std::shared_ptr<T>(p)`, `std::make_unique`, `std::make_shared`.
- `absl::WrapUnique(p)`, `base::WrapUnique(p)`.
- `scoped_refptr<T>(p)`, `boost::intrusive_ptr<T>(p)`.
- Project-defined wrappers, e.g. `MakeRefCounted<T>(...)`, `RefPtr<T>(p)`.
- `gsl::owner<T*>` annotation **plus** a clear later `delete`.

**Do not suppress** if any path between `new` and the wrap can `throw` or `return` early (the bare pointer leaks on that path).

---

## fp.ownership.transfer-to-sink

**Applies to:** `mem-leak-*`, `res-fd-leak-on-error`.

**Suppress when:** the pointer / handle is passed to a function whose contract takes ownership. Detect by:

- Signature: parameter is `std::unique_ptr<T>` (with `std::move`), `T&&`, or annotated `[[gsl::owner]]`.
- Naming convention: `Take`, `Adopt`, `Acquire`, `Consume`, `into_*`, `set_owned_*`.
- Project documentation / comments stating ownership transfer.

For each candidate exit, **prove** the ownership transfer happens on that exit. A transfer on the success path does not save the failure path.

---

## fp.ownership.container-with-destructor

**Applies to:** `mem-leak-*`, `mem-no-destructor`.

**Suppress when:** the pointer is stored in a member that is owned by a class with a destructor (or default-destructor of an owning member type) that releases it. Verify the destructor exists and traverses all elements.

Common shapes:
- `std::vector<std::unique_ptr<T>> children_;`
- `std::map<K, T*> entries_;` **with** `~Foo() { for (auto& [k, v] : entries_) delete v; }`.
- Intrusive list owned by parent.

If the container holds raw `T*` and the owner's destructor is missing or does not delete entries → that is itself the bug (`mem-no-destructor`); do not suppress, report.

---

## fp.null.proven-non-null

**Applies to:** `ptr-deref-no-check`.

**Suppress when:** the pointer is provably non-null at the deref site. Acceptable proofs:

1. **Just-checked** — there is an `if (p == nullptr) { return / throw / abort; }` (or `assert(p)`, `CHECK(p)`, `if (!p) …`) earlier in the same function with no rebinding in between.
2. **Caller-established** — every reachable caller passes a non-null value (e.g. `&local`, `this`, dereferenced smart pointer with prior check, address-of-array). You MUST have inspected at least the call sites returned by `rg -n '<func>(' --type cpp` (bounded to ≤ 20 callers; if more, treat as `inconclusive`).
3. **Type guarantees non-null** — `T&` rather than `T*`, `gsl::not_null<T*>`.
4. **Allocation-then-check macro** — e.g. `auto p = New(...); RETURN_IF_NULL(p);`.

If the function is part of a public API with no precondition documentation, do not assume callers check; report `medium`.

---

## fp.null.optional-with-value-or

**Applies to:** `ptr-optional-value-no-check`.

**Suppress when:** access uses `value_or(default)` or is preceded by `has_value()` / `if (opt)`.

---

## fp.concurrency.single-threaded

**Applies to:** all `con-*`.

**Suppress when:** the access can only execute on a single thread. Acceptable proofs:

- The function is called only from initialization (before any thread is started) or destruction (after all joined).
- Project convention asserts thread affinity (e.g. `DCHECK_CALLED_ON_VALID_SEQUENCE(seq_)`, `assert_single_threaded()`); cite the assertion line.
- The data is thread-local (`thread_local` storage, per-thread struct).

---

## fp.concurrency.protected-by-lock

**Applies to:** `con-unsynchronized-shared-write`.

**Suppress when:** every read AND write of the variable goes through a consistent lock. Verification requires enumerating all readers and all writers, not just the matched candidate.

If readers go through lock but writers don't (or vice versa), the asymmetry is the bug — do not suppress.

---

## fp.concurrency.published-once

**Applies to:** `con-unsynchronized-shared-write`.

**Suppress when:** the field is written once before publication (e.g. in the constructor before `std::thread` start, or while holding the only reference) and never written again. Verify:

- All writes are in init / constructor.
- The publication store has acquire/release semantics (e.g. release on store, acquire on load) **or** is naturally ordered by happens-before (thread start, mutex lock).

---

## fp.concurrency.atomic-with-correct-order

**Applies to:** `con-unsynchronized-shared-write`, `con-missing-memory-order`.

**Suppress when:** the variable is `std::atomic<T>` and the operations use `seq_cst` (default) or a documented relaxed/acquire-release pattern that matches the algorithm. Cite the algorithm requirement.

If `std::atomic` is used with `memory_order_relaxed` to publish a pointer or coordinate handoff, that is `con-missing-memory-order` — do not suppress.

---

## fp.deadlock.no-cycle-observed

**Applies to:** `con-lock-ordering-deadlock`.

**Suppress when:** building the lock-acquisition graph for the project (or scoped subsystem) reveals no cycle that can simultaneously execute on different threads. Acceptable evidence:

- All call sites in the cycle are on the same thread (cannot deadlock with itself for `std::recursive_mutex`).
- One path uses `std::try_lock` / `try_to_lock` and backs off on failure.
- The project uses `absl::Mutex` with `Mutex::AssertHeld` invariants that prevent the inverse order.

---

## fp.deadlock.scoped-lock

**Applies to:** `con-lock-ordering-deadlock`.

**Suppress when:** the multi-lock acquisition uses `std::scoped_lock(mu1, mu2)` or `std::lock(mu1, mu2)` (deadlock-avoiding two-phase locking). The order in source is irrelevant in this case.

---

## fp.integer.bounded-by-precondition

**Applies to:** all `int-*`.

**Suppress when:** every operand's domain is bounded such that the operation cannot overflow / underflow / shift out of range.

Examples:
- `for (size_t i = 0; i < n; ++i) sum += i;` where `n <= 1000` because `n` came from a validated config.
- `int x = clamp(input, 0, 1024); int y = x * 4;` — bounded.
- `if (count > kMax) return; total = count * sizeof(T);` — bounded by check.

The bound must be **provable** from the function or its immediate caller, not asserted by hand-waving.

---

## fp.integer.allocator-already-checks

**Applies to:** `int-mul-overflow-alloc-size`.

**Suppress when:** the size is computed inside an allocator that itself checks overflow (e.g. `std::vector::resize(n)` with `n` from `size_t`, since vector internally uses `n * sizeof(T)` checked).

Do **not** suppress for `new T[n]` with user-influenced `n` — `operator new[]` historically does not protect against overflow, and `n * sizeof(T)` is computed in `size_t` which can wrap.

---

## fp.signed-unsigned.deliberate-modular

**Applies to:** `int-signed-unsigned-mix`, `int-add-overflow` on unsigned.

**Suppress when:** the code uses unsigned modular arithmetic deliberately (hash mixing, ring buffers, CRC). Look for nearby `% N` operations or comments documenting modular intent.

---

## fp.divbyzero.unreachable

**Applies to:** `div-by-zero`.

**Suppress when:** the divisor is provably non-zero (literal constant, just-checked, type guarantees positive like `size()` for non-empty container with prior check).

---

## fp.empty-container.checked

**Applies to:** `empty-container-front-back`.

**Suppress when:** preceded by `if (c.empty()) return;`, `if (!c.empty())`, `assert(!c.empty())`, or in a loop body that is guarded by `for (auto& x : c)` (which does not execute on empty).

---

## fp.generated-code

**Applies to:** all templates.

**Suppress when:** the candidate file is generated. Markers:

- File name suggests generation: `*.pb.cc`, `*.pb.h`, `moc_*.cpp`, `*.flatc.cc`, `*_generated.h`, `*.tab.c`.
- Header banner says "DO NOT EDIT" / "AUTO GENERATED".
- File lives under `build/`, `gen/`, `generated/`.

Report findings against the **generator template**, not the generated output.

---

## fp.test-code

**Applies to:** all templates, **except** `mem-leak-*` in long-running test fixtures.

**Suppress when:** the file is part of a unit test (`*_test.cc`, `*_test.cpp`, `tests/`, `gtest/`) **and** the bug only matters at scale (e.g. integer overflow with hard-coded `int n = 10`).

Do **not** suppress if the test is a fuzz harness or stress test exercising production logic.

---

## fp.dead-code

**Applies to:** all templates.

**Suppress when:** the candidate code is provably unreachable. Acceptable proofs:

- `#if 0` / `#ifdef DEPRECATED` block.
- The function is `static` and has no callers in the translation unit (verify with `rg`).
- Behind a feature flag known to be off (cite where the flag is set).

---

## How to Cite a Suppression

When you suppress a candidate, record both the filter ID and a one-line justification:

```json
{
  "candidate_id": "mem-leak-new-no-delete::src/cache.cc:88",
  "status": "suppressed",
  "filter": "fp.ownership.smart-pointer",
  "justification": "wrapped in absl::WrapUnique on the only post-allocation line (cache.cc:90)"
}
```

A bare `"status": "suppressed"` without filter + justification is **invalid** and must be re-evaluated.
