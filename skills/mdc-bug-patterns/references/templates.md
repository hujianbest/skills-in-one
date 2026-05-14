# Bug Pattern Templates

Each template below is a **per-unit checklist**, not a prompt. During Pass 3 you read each prioritised code unit (function / method / small file) end-to-end and apply *all* relevant templates as a checklist on that single read.

Roles of each template field:

- `detection_query` — a `rg` (ripgrep) invocation used in Pass 2 only. It is a **prior / ranking signal**, not a finding gate. The query intentionally over-matches; the LLM decides whether there is a bug by reading the code.
- `false_positive_filters` — filters from `references/false-positive-filters.md` that the LLM must explicitly rule out before promoting a finding.
- `verification` — the procedural checklist the LLM executes on each unit where the template might apply.
- `required_evidence` — the exact pieces of code / data flow that must be cited in the report. **A finding is invalid if any item is missing.**
- `confidence_rubric` — how to rate `high` / `medium` / `low` for this template.
- `bad_example` / `good_example` — calibration examples.
- `fix_suggestions` — recommended fixes.

Reminder of the philosophy: **trade tokens for code quality**. Pattern matching tells you *where to look first*; the LLM decides *whether there is a bug* by actually reading and understanding the code.

---

## Memory safety

### `mem-leak-new-no-delete`
- **name:** Raw `new` without matching `delete` on all paths
- **category:** memory
- **severity:** critical
- **detection_query:**
  ```bash
  rg -n --type cpp '\bnew\s+[A-Za-z_]' -g '!third_party/**' -g '!build/**'
  ```
  The query intentionally over-matches every `new T...` site (including `new T[n]`, `new (placement) T`, smart-pointer wraps).  Pass 3 must trace ownership.
- **false_positive_filters:**
  - `fp.ownership.smart-pointer`
  - `fp.ownership.transfer-to-sink`
  - `fp.ownership.container-with-destructor`
  - `fp.generated-code`
  - `fp.test-code` (only for short-lived test fixtures)
- **verification:**
  1. Identify the receiving variable / expression of the `new`.
  2. Enumerate **every** exit reachable after the allocation (`return`, `throw`, `goto`, `co_return`, falls-off-end). Use the file's full function body.
  3. For each exit, determine whether the pointer has been: deleted, transferred to an owning sink, stored in a container with a releasing destructor, or wrapped in a smart pointer.
  4. The bug exists if **any** reachable exit lacks one of the above.
  5. If the function can `throw` between `new` and the wrapping/store, that path is also a leak (RAII is required for exception safety).
- **required_evidence:**
  - `allocation_site`: `<file:line>` of the `new`.
  - `leaking_exit`: `<file:line>` of the exit that does not release.
  - `ownership_search`: brief note of where you searched for ownership transfer (caller? sink? destructor?).
- **confidence_rubric:**
  - `high`: at least one concrete leaking exit cited; ownership search ruled out a wrap on that path.
  - `medium`: pointer escapes to a sink with unclear ownership semantics; no destructor visible.
  - `low`: cannot determine ownership without reading code outside the audited scope.
- **bad_example:**
  ```cpp
  void Process(Reader* r) {
    Buffer* b = new Buffer(r->size());
    if (!r->Fill(b)) return;        // leak on this path
    Consume(b);
    delete b;
  }
  ```
- **good_example:**
  ```cpp
  void Process(Reader* r) {
    auto b = std::make_unique<Buffer>(r->size());
    if (!r->Fill(b.get())) return;
    Consume(std::move(b));
  }
  ```
- **fix_suggestions:**
  - Replace `new T(...)` with `std::make_unique<T>(...)` or `std::make_shared<T>(...)`.
  - If C++ smart pointers are unavailable (legacy), wrap each path with explicit `delete` and use `goto cleanup` or a small RAII guard.

---

### `mem-array-new-mismatched-delete`
- **name:** `new[]` paired with `delete` (not `delete[]`), or vice versa
- **category:** memory
- **severity:** critical
- **detection_query:**
  ```bash
  rg -n --type cpp '\bnew\s+[A-Za-z_][\w:]*\s*\[' -g '!third_party/**' -g '!build/**'
  ```
  Pass 3 also runs the paired freeing query:
  ```bash
  rg -n --type cpp '\bdelete\s+[A-Za-z_]' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - `fp.ownership.smart-pointer` (e.g. `std::unique_ptr<T[]>` is correct).
- **verification:**
  1. For each `new T[n]` site, find the freeing site (same scope or owning destructor).
  2. Confirm freeing uses `delete[]` (not `delete`).
  3. Conversely, for each `delete[]` site, ensure allocation was `new[]`.
- **required_evidence:**
  - `allocation_site`: `<file:line>` with the array allocation.
  - `freeing_site`: `<file:line>` with the freeing form.
  - `mismatch`: the exact mismatched form quoted from each line.
- **confidence_rubric:**
  - `high`: both sites located and operator forms differ.
  - `medium`: freeing site located but ambiguous (e.g. virtual destructor chain).
  - `low`: cannot locate freeing site — escalate to `mem-leak-new-no-delete` instead.
- **bad_example:**
  ```cpp
  int* a = new int[100];
  delete a;   // UB: should be delete[]
  ```
- **fix_suggestions:**
  - Use `std::vector<T>` or `std::unique_ptr<T[]>`.
  - If raw arrays are required, match `new[]` with `delete[]`.

---

### `mem-double-free`
- **name:** Double `delete` / `free` of the same pointer
- **category:** memory
- **severity:** critical
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(delete|free)\s*\(?[A-Za-z_][\w\.\->]*\)?\s*;' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - `fp.dead-code`
  - Pointer is set to `nullptr` immediately after first free (subsequent `delete nullptr` is a no-op).
- **verification:**
  1. For each free site, find all other free sites of the same pointer expression in reachable scopes (same function, callers, destructors).
  2. Determine if two frees can occur on the same logical object (e.g. parent destroys child explicitly **and** child destructor frees, or copy without deep-copy semantics).
  3. Check Rule of Three/Five: if a class has a custom destructor that `delete`s a member but no copy constructor / assignment, copying causes double-free.
- **required_evidence:**
  - `first_free`: `<file:line>` of the first free.
  - `second_free`: `<file:line>` of the second free, with the path that reaches it.
  - `aliasing_proof`: how the two sites reach the same object (copy, alias, container).
- **confidence_rubric:**
  - `high`: two concrete free sites and a path that hits both.
  - `medium`: shape matches Rule-of-Three violation but no concrete callsite triggers copy.
  - `low`: speculative aliasing across translation units.
- **bad_example:**
  ```cpp
  struct Buf { ~Buf() { delete[] p_; } char* p_; };
  Buf x; Buf y = x;   // shallow copy; both destructors delete p_
  ```
- **fix_suggestions:**
  - Implement copy/move per Rule of Five, or `= delete` them, or use `std::unique_ptr<char[]>`.
  - Set freed pointers to `nullptr` (defense in depth).

---

### `mem-use-after-free`
- **name:** Read or write of a pointer after its referent is freed
- **category:** memory
- **severity:** critical
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(delete|free|reset|clear|pop_back|erase)\b' -g '!third_party/**'
  ```
  Intentionally noisy. Pass 3 verifies whether a use of the same object follows the free.
- **false_positive_filters:**
  - Subsequent use is on a different object (verify identity).
  - Iterator / reference invalidation falls under `ptr-iterator-invalidated` (see below).
  - `fp.dead-code`
- **verification:**
  1. Identify the freeing call and the dereference. Confirm they refer to the same object (alias, member, container element).
  2. For container operations (`erase`, `pop_back`, `clear`, `reset`), check whether iterators / references / pointers obtained before the call are reused after.
  3. For object lifetime: if the object's owner destroys it (via `delete` / scope exit / `unique_ptr::reset`), any later use of a stale raw pointer is UAF.
- **required_evidence:**
  - `free_site`: `<file:line>`.
  - `use_site`: `<file:line>` after the free.
  - `reachability`: control-flow path or callgraph linking them.
- **confidence_rubric:**
  - `high`: use within the same function after a free with no rebinding; or use of an iterator after a documented invalidating operation.
  - `medium`: use across function boundary where lifetime contract is implicit.
  - `low`: use within an async callback where lifetime cannot be statically proven.
- **bad_example:**
  ```cpp
  std::vector<int> v = {1,2,3};
  auto it = v.begin();
  v.push_back(4);   // may invalidate it
  *it = 0;          // UAF
  ```
- **fix_suggestions:**
  - Re-acquire iterators after mutation.
  - Use `std::weak_ptr` for non-owning references to shared lifetimes.
  - For async callbacks, capture by `std::shared_ptr` or guard with `std::weak_ptr::lock()`.

---

### `mem-uninitialized-read`
- **name:** Read of an uninitialized member or local
- **category:** memory
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '^\s*(class|struct)\s+\w+' -g '!third_party/**'
  ```
  Pass 3 uses this to enumerate type declarations, then per type checks constructors and member initializers.
- **false_positive_filters:**
  - All constructors initialize the member.
  - In-class member initializer present (`int x = 0;`).
  - Type is `std::optional<T>` (default-constructs to empty, well-defined).
- **verification:**
  1. Locate every constructor for the class (including defaulted).
  2. For each scalar / pointer member, confirm initialization either (a) in-class, (b) in member initializer list, or (c) in the constructor body before any function returns.
  3. Locate at least one read site of the member (search for `obj.member` / `this->member` / `member`) on a path that does not write first.
- **required_evidence:**
  - `class_declaration`: `<file:line>` of the class.
  - `uninitialized_members`: list of member names that lack initialization in some constructor.
  - `unsafe_read`: `<file:line>` reading the member before write.
- **confidence_rubric:**
  - `high`: an uninitialized member is read on the very first method call after construction.
  - `medium`: read happens but only after some methods that *might* initialize.
  - `low`: speculative — no reachable read found.
- **fix_suggestions:**
  - Add in-class member initializers (`int x{};`, `T* p = nullptr;`).
  - Use `= default` constructors only when all members have in-class initializers.

---

### `mem-rule-of-three-five`
- **name:** Class with custom destructor missing copy/move
- **category:** memory
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '~\w+\s*\(' -g '!third_party/**'
  ```
  Pass 3 inspects each destructor body for resource-releasing calls (`delete`, `free`, `fclose`, `close`) and then checks the class for copy/move operations.
- **false_positive_filters:**
  - Class has explicit `=delete` for copy / assignment / move.
  - Class is final & non-copyable per project convention (e.g. inherits `Noncopyable`).
- **verification:**
  1. From the destructor match, find the class declaration.
  2. Check for explicit copy ctor, copy assign, move ctor, move assign — at least one of (delete) or (custom).
  3. If none and the class manages a resource, copies will double-free; report.
- **required_evidence:**
  - `class_declaration`: `<file:line>`.
  - `destructor`: `<file:line>` showing resource release.
  - `missing_methods`: list of missing methods (copy ctor, copy assign, move ctor, move assign).
- **confidence_rubric:**
  - `high`: class is copy-constructed / assigned somewhere in the codebase.
  - `medium`: class is value-typed and could be copied (no `=delete`).
  - `low`: class only ever stored via pointer; copies are unlikely but possible.
- **fix_suggestions:**
  - Define copy/move per Rule of Five, or `=delete` them.
  - Replace raw resource handle with `std::unique_ptr` and you get the right defaults for free.

---

### `mem-buffer-overflow-index`
- **name:** Indexing a buffer with an unchecked size
- **category:** memory
- **severity:** critical
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(memcpy|memmove|memset|strcpy|strcat|sprintf|snprintf|gets)\s*\(' -g '!third_party/**'
  ```
  Pass 3 also runs the indexing query when relevant:
  ```bash
  rg -n --type cpp '\b(buf|buffer|data|arr)\s*\[' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - Index is bounded by an immediately preceding `if (i < N)` / `assert(i < N)` / for-loop bound.
  - `fp.integer.bounded-by-precondition`.
- **verification:**
  1. For `memcpy`/`memmove`/`memset`/`strcpy`/`strcat`/`sprintf`, confirm the destination size ≥ the count.
  2. For raw indexing, confirm the index is bounded ≤ buffer size on every path.
  3. For `snprintf`, confirm the size argument equals or exceeds the buffer size.
- **required_evidence:**
  - `call_or_access_site`: `<file:line>`.
  - `buffer_size`: how the buffer size is known (declaration, allocation, sizeof).
  - `index_or_count_source`: where the index/count comes from and why it can exceed the buffer.
- **confidence_rubric:**
  - `high`: count/index demonstrably can come from untrusted input without a bound check.
  - `medium`: count is a function parameter with no documented precondition.
  - `low`: count is bounded by structure but the bound is not verified within the audited scope.
- **fix_suggestions:**
  - Use `std::array`/`std::vector` and `.at()` for checked access.
  - Use `std::span` for size-carrying buffer parameters.
  - Use `snprintf` instead of `sprintf`; pass the actual buffer size.

---

### `mem-strncpy-no-terminator`
- **name:** `strncpy` without explicit null-termination
- **category:** memory
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '\bstrncpy\s*\(' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - The line is followed by an explicit `dst[N-1] = '\0';`.
  - Destination buffer is zero-initialized and `n < dst_size`.
- **verification:**
  1. Confirm the call writes up to `n` bytes from `src` into `dst`, with `n` ≤ `strlen(src)`.
  2. If so, check that `dst` is null-terminated by some other mechanism.
- **required_evidence:**
  - `strncpy_site`: `<file:line>`.
  - `termination_check`: code (or absence thereof) that ensures null termination.
- **confidence_rubric:**
  - `high`: clear example of unterminated buffer being read by `strlen`/`printf("%s")` later.
  - `medium`: `strncpy` is used and no termination is visible in the function.
- **fix_suggestions:**
  - Use `snprintf(dst, dst_size, "%s", src)`.
  - Or explicitly null-terminate after `strncpy`.

---

## Null / pointer / iterator

### `ptr-deref-no-check`
- **name:** Pointer dereferenced without null check
- **category:** null
- **severity:** critical
- **detection_query:**
  ```bash
  rg -n --type cpp -e '->' -g '!third_party/**'
  ```
  Intentionally very noisy. In practice you should narrow Pass 2 by sub-directory or by suspected pointer parameter names.  Pass 3 verification is required for every candidate.
- **false_positive_filters:**
  - `fp.null.proven-non-null`
  - `fp.dead-code`
  - `fp.test-code`
- **verification:**
  1. Take the dereferenced expression. Find its definition / parameter.
  2. Walk the function from entry to the deref. If any check (`if (p)`, `assert(p)`, `CHECK`, project macro) establishes non-null without rebinding, suppress.
  3. Otherwise, examine callers (≤ 20). If all reachable callers pass non-null, suppress with `fp.null.proven-non-null` proof 2.
  4. Else report.
- **required_evidence:**
  - `deref_site`: `<file:line>`.
  - `pointer_origin`: where the pointer came from (parameter, member, return).
  - `caller_audit`: a list of callers checked or a statement that the function is public API with no documented precondition.
- **confidence_rubric:**
  - `high`: at least one caller demonstrably passes `nullptr` or returns `nullptr` to the function.
  - `medium`: public API with no caller audit possible (treat parameter as untrusted).
  - `low`: private helper; callers all happen to pass non-null but no enforcement.
- **fix_suggestions:**
  - Add explicit null check.
  - Change parameter to `T&` if null is invalid.
  - Use `gsl::not_null<T*>`.

---

### `ptr-this-may-be-null-callback`
- **name:** Member access in async callback where `this` may have been destroyed
- **category:** null
- **severity:** critical
- **detection_query:**
  ```bash
  rg -n --type cpp '\[\s*(this|=)\s*[,\]]' -g '!third_party/**'
  ```
  Pass 3 examines each lambda capturing `this` and traces the registration site / dispatcher lifetime.
- **false_positive_filters:**
  - Callback is captured by `shared_ptr` of the owning object.
  - Callback is unregistered in destructor (verify in `~Class()`).
  - Class inherits a project lifetime guard (e.g. `WeakPtrFactory` cancellation).
- **verification:**
  1. For each `[this]` capture, identify what the callback is registered with.
  2. Determine whether the registration is unregistered in `~Class()`.
  3. Determine whether the callback can fire after `~Class()` (e.g. registered with a global / longer-lived dispatcher).
- **required_evidence:**
  - `callback_site`: `<file:line>` of the lambda capturing `this`.
  - `owner_lifetime`: how the owner could be destroyed before the callback runs.
  - `registration_site`: where the callback is given to the dispatcher.
- **confidence_rubric:**
  - `high`: dispatcher outlives `this` and no unregister in destructor.
  - `medium`: dispatcher lifetime is unclear.
  - `low`: same-thread synchronous callback (rarely a UAF).
- **fix_suggestions:**
  - Capture `std::weak_ptr<Self>` and `lock()` before use.
  - Unregister callbacks in the destructor.
  - Use a per-object `WeakPtrFactory` / cancellation token.

---

### `ptr-optional-value-no-check`
- **name:** `std::optional::value()` / unchecked deref of optional
- **category:** null
- **severity:** medium
- **detection_query:**
  ```bash
  rg -n --type cpp '\.value\(\)' -g '!third_party/**'
  ```
  Pass 3 verifies the receiver is `std::optional`/`absl::optional` and that no preceding check exists.
- **false_positive_filters:**
  - `fp.null.optional-with-value-or`
- **verification:**
  1. Confirm the variable type is `std::optional<...>` or compatible (`absl::optional`, `boost::optional`).
  2. Check for prior `has_value()` / `if (opt)` / `value_or` on the same variable.
- **required_evidence:**
  - `value_site`, `optional_declaration`, `prior_check_search`.
- **fix_suggestions:**
  - Replace with `value_or(default)`.
  - Wrap in `if (opt) { auto v = *opt; … }`.

---

### `ptr-iterator-invalidated`
- **name:** Iterator/reference used after a container-mutating call
- **category:** null
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '\.(push_back|insert|erase|clear|resize|reserve|emplace_back|emplace)\(' -g '!third_party/**'
  ```
  Pass 3 looks within the surrounding ~30 lines for an iterator/reference acquired before this mutation and reused after.
- **false_positive_filters:**
  - Iterator is reassigned after the mutation.
  - Container type does not invalidate on the operation (`std::list::push_back` does not invalidate iterators).
- **verification:**
  1. Identify the iterator/reference and the mutation.
  2. Confirm the container type's invalidation rules (cppreference) match the operation.
  3. Confirm the iterator/reference is used after the mutation.
- **required_evidence:**
  - `iterator_acquired`, `mutation_site`, `subsequent_use`.
- **fix_suggestions:**
  - Capture index instead of iterator when mutating.
  - Re-acquire the iterator from the returned value (e.g. `it = v.erase(it);`).

---

## Resource

### `res-file-no-close`
- **name:** `fopen` without `fclose` on all paths
- **category:** resource
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '\bfopen\s*\(' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - File handle is wrapped in RAII (`fopen` immediately stored in a `unique_ptr<FILE, FCloser>` or `boost::scoped_array`-style).
  - `fp.test-code`
- **verification:**
  1. Identify the receiving variable and trace to all exits.
  2. Each exit must `fclose` (or transfer ownership).
- **required_evidence:**
  - `fopen_site`, `leaking_exit`, `ownership_search`.
- **fix_suggestions:**
  - Use `std::ifstream`/`std::ofstream`.
  - Wrap `FILE*` in a `unique_ptr` with custom deleter.

---

### `res-mutex-no-unlock`
- **name:** `mutex.lock()` without `unlock()` on all paths
- **category:** resource
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '\.lock\(\)\s*;' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - The lock is in fact a `std::lock_guard` / `std::unique_lock` constructor (the match was on a different `.lock()`).
  - `fp.dead-code`
- **verification:**
  1. Identify the mutex and the lock site.
  2. Confirm an explicit `unlock()` on every reachable exit, including exception paths (since `lock()` is not exception-safe).
- **required_evidence:**
  - `lock_site`, `leaking_exit`, `exception_path_check`.
- **fix_suggestions:**
  - Use `std::lock_guard<std::mutex> g(m);` or `std::unique_lock`.
  - Use `std::scoped_lock` for multiple mutexes.

---

### `res-fd-leak-on-error`
- **name:** Open fd / handle leaks on early-return error path
- **category:** resource
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(open|socket|epoll_create|eventfd|inotify_init|timerfd_create|dup|dup2)\s*\(' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - fd wrapped in RAII (e.g. `unique_fd`, `base::ScopedFD`).
  - Single exit path closes unconditionally.
- **verification:**
  1. Identify the fd-returning call.
  2. Walk all paths after the call to function exit.
  3. Each exit must `close(fd)` or transfer ownership.
- **required_evidence:**
  - `open_site`, `leaking_exit`, `ownership_search`.
- **fix_suggestions:**
  - Use a `unique_fd` RAII wrapper.
  - Consolidate cleanup with `goto cleanup` (idiomatic in C).

---

### `res-raii-broken-by-release`
- **name:** RAII guard `release()`d without manual cleanup
- **category:** resource
- **severity:** medium
- **detection_query:**
  ```bash
  rg -n --type cpp '\.release\(\)' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - `release()` immediately consumed by another owning sink (smart-pointer constructor, ownership-taking function).
- **verification:**
  1. The point of `release()` is to hand ownership somewhere. Confirm it lands in another owner on the same statement or shortly after.
  2. If not, a leak (or double-free) results.
- **required_evidence:**
  - `release_site`, `ownership_destination_or_absence`.
- **fix_suggestions:**
  - Pass `std::move(ptr)` instead of `release()` whenever possible.
  - If `release()` is necessary, immediately wrap the raw pointer in another owner.

---

## Concurrency

### `con-unsynchronized-shared-write`
- **name:** Mutation of shared data without consistent synchronization
- **category:** concurrency
- **severity:** critical
- **detection_query:**
  ```bash
  rg -n --type cpp '\b\w+_\s*(\+\+|--|\+=|-=|=)' -g '!third_party/**'
  ```
  Assumes the project-common `member_` trailing-underscore convention. If the project uses a different style (e.g. `m_member`), adjust the regex in Pass 1 (e.g. `\bm_\w+\s*(\+\+|--|\+=|-=|=)`).
- **false_positive_filters:**
  - `fp.concurrency.single-threaded`
  - `fp.concurrency.protected-by-lock`
  - `fp.concurrency.published-once`
  - `fp.concurrency.atomic-with-correct-order`
- **verification:** see `references/methodology.md#concurrency-deep-dive`. You **must** build a thread-affinity sketch and a lock-set sketch.
- **required_evidence:**
  - `field_declaration`: `<file:line>` of the field; type and storage class.
  - `writer_with_lock` or `writer_without_lock`: per-write site, with the lock-set held.
  - `reader_sites`: at least one reader and the lock-set held there.
  - `thread_affinity`: which threads can execute each path.
- **confidence_rubric:**
  - `high`: at least one writer or reader path provably runs on a different thread without holding the same lock.
  - `medium`: thread affinity unclear but project conventions suggest cross-thread access.
  - `low`: cannot determine thread affinity within audited scope.
- **bad_example:**
  ```cpp
  // Insert holds cache_mutex_; RemoveExpired does not, both run on different threads.
  void Insert(...) { std::lock_guard g(cache_mutex_); cache_size_ += s; ... }
  void RemoveExpired() { for (...) cache_size_ -= s; }   // race
  ```
- **fix_suggestions:**
  - Hold the same mutex on every read and write.
  - Or change the field to `std::atomic<T>` with the right memory order.

---

### `con-lock-ordering-deadlock`
- **name:** Inconsistent lock acquisition order across functions / threads
- **category:** concurrency
- **severity:** critical
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(std::(lock_guard|unique_lock|scoped_lock)|\.lock\(\))' -g '!third_party/**'
  ```
  Pass 3 enumerates functions that take ≥ 2 locks (look for two matches in the same function body) and builds the lock-acquisition graph.
- **false_positive_filters:**
  - `fp.deadlock.scoped-lock`
  - `fp.deadlock.no-cycle-observed`
  - All call sites in the cycle execute on the same thread (recursive_mutex or single-threaded).
- **verification:**
  1. For each function with two or more locks, record `(lock_set_at_entry, additional_locks_taken_in_order)`.
  2. Build a directed graph: edge `A → B` if any function takes `A` then `B`.
  3. A cycle that can simultaneously execute on different threads is a deadlock candidate.
  4. Confirm the threads of the two cycle endpoints can both be runnable concurrently.
- **required_evidence:**
  - `path_a`: `<file:line>` showing order `A`-then-`B`.
  - `path_b`: `<file:line>` showing order `B`-then-`A`.
  - `concurrent_threads`: how the two paths can run at the same time.
- **confidence_rubric:**
  - `high`: real cycle on independent threads with no try-lock backoff.
  - `medium`: cycle exists but one path is rare / behind feature flag.
  - `low`: lock-set partially unknown (callbacks).
- **fix_suggestions:**
  - Use `std::scoped_lock(mu1, mu2)` to acquire both atomically.
  - Establish a global lock order; document it next to the mutex declarations.

---

### `con-double-checked-locking`
- **name:** Double-checked locking on a non-atomic pointer
- **category:** concurrency
- **severity:** critical
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(if|while)\s*\(\s*!?\s*\w+\s*\)' -g '!third_party/**'
  ```
  Very noisy; in practice run this only after Pass 1 identifies likely lazy-init sites (singletons, caches). Pass 3 confirms the DCL pattern: outer null check, lock, inner null check, store.
- **false_positive_filters:**
  - The checked variable is `std::atomic<T*>` and the load uses `acquire` order (or default `seq_cst`).
  - The construction uses `std::call_once`.
- **verification:**
  1. Confirm the singleton-style pattern: outer null-check, lock, inner null-check, construct, store.
  2. Confirm the variable is **not** `std::atomic` or is loaded with `relaxed`.
- **required_evidence:**
  - `outer_check`, `lock_site`, `inner_check_and_store`, `variable_type`.
- **confidence_rubric:**
  - `high`: classic DCLP pattern with raw pointer.
  - `medium`: pattern matches but variable is `volatile` only (insufficient).
- **fix_suggestions:**
  - Use `std::call_once` with `std::once_flag`.
  - Or use `std::atomic<T*>` with `memory_order_acquire` load and `memory_order_release` store.

---

### `con-sleep-or-blocking-with-lock-held`
- **name:** Sleep / blocking I/O / wait while holding a mutex
- **category:** concurrency
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(std::this_thread::sleep|usleep|nanosleep|sleep\s*\(|recv\s*\(|send\s*\(|poll\s*\(|epoll_wait|select\s*\()' -g '!third_party/**'
  ```
  Pass 3 narrows to occurrences inside a function whose entry takes a lock that is still held at the call site.
- **false_positive_filters:**
  - The "lock" is a `unique_lock` that has been `unlock()`ed before the blocking call.
  - The blocking call is `cv.wait(lock, …)` which releases the lock during wait (correct).
- **verification:**
  1. Confirm the mutex is still held at the blocking call.
  2. Confirm the blocking call can take significant time.
- **required_evidence:**
  - `lock_site`, `blocking_call_site`, `still_held_proof`.
- **fix_suggestions:**
  - Release the lock before blocking; re-acquire after.
  - Use a finer-grained lock or move the blocking work out of the critical section.

---

### `con-callback-invoked-with-lock-held`
- **name:** External callback invoked while holding internal lock
- **category:** concurrency
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(callback_|cb_|listener_|observer_|on_\w+)\s*\(' -g '!third_party/**'
  ```
  Pass 3 narrows to call sites inside a critical section (lock taken at function entry and not released before the call).
- **false_positive_filters:**
  - The callback is documented to require the lock held (cite the doc comment).
  - The callback is project-internal and audited to take no locks.
- **verification:**
  1. Identify the callback type — is it user-supplied?
  2. Walk callers that supply the callback. If any callback might re-enter the locked subsystem, deadlock; if any callback might block, contention.
- **required_evidence:**
  - `lock_site`, `callback_site`, `callback_origin`.
- **fix_suggestions:**
  - Snapshot the data needed, release the lock, then invoke the callback.
  - Document and enforce a "no re-entry" contract on the callback.

---

### `con-missing-memory-order`
- **name:** `std::atomic` operations using `relaxed` where ordering is needed
- **category:** concurrency
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp 'std::memory_order_relaxed' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - The atomic is a pure counter (statistics) where transient skew is acceptable.
  - Surrounding code documents the relaxed choice.
- **verification:**
  1. Determine what the atomic protects or coordinates.
  2. If it publishes a pointer, signals readiness, or sequences other memory operations, `relaxed` is wrong.
- **required_evidence:**
  - `atomic_op_site`, `coordination_use`, `ordering_argument`.
- **fix_suggestions:**
  - Use `acquire`/`release` for handoff; `seq_cst` for full barriers.
  - Add a comment justifying any `relaxed` choice.

---

### `con-tocttou`
- **name:** Time-of-check-to-time-of-use race on a shared resource
- **category:** concurrency
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(stat|access|exists|contains|count|find)\s*\(' -g '!third_party/**'
  ```
  Pass 3 looks within ~10 lines after each match for an `open`/`create`/`insert`/`emplace`/`[]` on the same key.
- **false_positive_filters:**
  - The full check-then-act sequence is performed under a single lock that also gates the resource.
  - Filesystem case where atomicity is achieved via `O_CREAT | O_EXCL`.
- **verification:**
  1. Identify check site and act site.
  2. Confirm there is no synchronization that prevents concurrent modification between the two.
- **required_evidence:**
  - `check_site`, `act_site`, `concurrent_modifier`.
- **fix_suggestions:**
  - Use atomic check-and-act primitives (`map.emplace`, `O_CREAT|O_EXCL`).
  - Hold the appropriate lock spanning both operations.

---

### `con-condvar-no-predicate`
- **name:** `condition_variable::wait` without a predicate (spurious wakeup unsafe)
- **category:** concurrency
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '\.wait\s*\(\s*[A-Za-z_]\w*\s*\)\s*;' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - The match is on a `std::future::wait()` (different API).
- **verification:**
  1. Confirm the type is `std::condition_variable` (or `_any`).
  2. The predicate-less form must be inside a loop checking the predicate; if not, spurious wakeups can deliver a false-true.
- **required_evidence:**
  - `wait_site`, `enclosing_loop_or_absence`, `predicate_check_or_absence`.
- **fix_suggestions:**
  - Use `cv.wait(lock, [&]{ return predicate; });`.
  - Or wrap in `while (!predicate) cv.wait(lock);`.

---

## Logic / Integer

### `int-add-overflow`
- **name:** Signed integer addition without overflow check
- **category:** logic
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(int|long|int32_t|int64_t|ssize_t)\s+\w+\s*=\s*\w+\s*\+\s*\w+' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - `fp.integer.bounded-by-precondition`
  - `fp.signed-unsigned.deliberate-modular`
- **verification:**
  1. Determine the domain of each operand.
  2. If `max(a)+max(b)` exceeds the type, report.
- **required_evidence:**
  - `expression_site`, `operand_domains`, `overflow_path`.
- **fix_suggestions:**
  - `__builtin_add_overflow(a, b, &r)`.
  - Use wider intermediate type and clamp.

---

### `int-sub-underflow`
- Same shape as `int-add-overflow` for subtraction.
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(int|long|size_t|uint32_t|uint64_t)\s+\w+\s*=\s*\w+\s*-\s*\w+' -g '!third_party/**'
  ```
- Pay special attention to `size_t`/unsigned subtraction wrapping below zero.

---

### `int-mul-overflow-alloc-size`
- **name:** Multiplication used as allocation size without overflow check
- **category:** logic
- **severity:** critical
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(new\s+\w[\w:]*\s*\[[^\]]*\*|malloc\s*\([^)]*\*|calloc\s*\()' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - `fp.integer.allocator-already-checks`
- **verification:**
  1. Trace `count` to its origin.
  2. Confirm `count * sizeof(T)` cannot wrap (`count <= SIZE_MAX / sizeof(T)`).
- **required_evidence:**
  - `alloc_site`, `count_origin`, `bound_check_or_absence`.
- **fix_suggestions:**
  - Add `if (count > SIZE_MAX / sizeof(T)) throw std::bad_alloc();` before allocation.
  - Prefer `std::vector<T>(count)`.

---

### `int-shift-out-of-range`
- **name:** Shift amount ≥ type width
- **category:** logic
- **severity:** medium
- **detection_query:**
  ```bash
  rg -n --type cpp '<<|>>' -g '!third_party/**'
  ```
  (Noisy — narrow with `rg '<<\s*[A-Za-z_]\w*'`.)
- **false_positive_filters:**
  - Stream operators (`std::cout << x`).
  - Shift amount is a literal `< type width`.
- **verification:**
  1. Confirm the operand types and the variable shift amount's domain.
  2. Report if the amount can equal or exceed the type width.
- **required_evidence:**
  - `shift_site`, `type_width`, `amount_domain`.
- **fix_suggestions:**
  - Validate amount before shifting; mask with `(amount & (width-1))` if intentional rotation.

---

### `int-signed-unsigned-mix`
- **name:** Comparison or arithmetic between signed and unsigned types
- **category:** logic
- **severity:** medium
- **detection_query:**
  ```bash
  rg -n --type cpp 'for\s*\(\s*int\s+\w+\s*=\s*0\s*;\s*\w+\s*<\s*\w+\.size\(\)' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - `fp.signed-unsigned.deliberate-modular`
- **verification:**
  1. Identify the signed and unsigned operands.
  2. Confirm comparison or arithmetic happens with implicit conversion that can change semantics.
- **required_evidence:**
  - `expression_site`, `operand_types`, `breaking_value_example`.
- **fix_suggestions:**
  - Match types (`size_t i = 0; i < v.size()`).
  - Use `static_cast<T>(...)` with explicit bounds check.

---

### `int-narrowing-cast`
- **name:** Narrowing conversion without bounds check
- **category:** logic
- **severity:** low
- **detection_query:**
  ```bash
  rg -n --type cpp 'static_cast\s*<\s*(int|short|char|int8_t|int16_t|int32_t|uint8_t|uint16_t|uint32_t)\s*>' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - Source value is bounded.
- **verification:** confirm source domain fits target type.
- **required_evidence:** `cast_site`, `source_domain`, `target_range`.
- **fix_suggestions:** add bounds check; use `gsl::narrow` (throws on loss).

---

### `div-by-zero`
- **name:** Division or modulus without zero check
- **category:** logic
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '[/%]\s*\w' -g '!third_party/**'
  ```
  Pass 3 must determine that the divisor is a variable (not a literal) and could be zero.
- **false_positive_filters:** `fp.divbyzero.unreachable`
- **verification:** confirm divisor can be zero on some reachable path.
- **required_evidence:** `divide_site`, `divisor_origin`, `zero_path`.
- **fix_suggestions:** explicit zero check; pre-condition documented.

---

### `empty-container-front-back`
- **name:** `front()` / `back()` / `top()` on container without empty check
- **category:** logic
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '\.(front|back|top)\s*\(\s*\)' -g '!third_party/**'
  ```
- **false_positive_filters:** `fp.empty-container.checked`
- **verification:** confirm preceding `if (!c.empty())` / equivalent.
- **required_evidence:** `access_site`, `prior_check_search`, `container_origin`.
- **fix_suggestions:** guard with empty check; or use `c.at(0)` (throws) for vector.

---

## Adding New Templates

1. Pick a stable `id` (kebab-case, prefix by category).
2. Write the **detection_query** as a runnable `rg` invocation. Test it on the target repo before committing.
3. Write at least 2 `false_positive_filters` (template-specific or by reference to `references/false-positive-filters.md`).
4. Write the `verification` checklist with concrete steps. No "use judgement" — be specific.
5. Define `required_evidence` (≥ 3 items) and the `confidence_rubric`.
6. Provide `bad_example` (small, real-looking) and `good_example`.
7. Add the template to the index in `SKILL.md`.
8. Run `scripts/scan_candidates.py --template <id>` against a known-buggy repo to validate the query.
