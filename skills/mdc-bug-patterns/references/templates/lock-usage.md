# 锁使用专项 (lock-usage)

> Specialty file for **mutex / critical-section / lock-guard misuse** in C/C++ embedded firmware. Load this when the audit scope is "锁使用是否正确" — covers lock leaks, lock-guard temporaries, recursive locking on non-recursive mutexes, lock-protected-data inconsistencies, lock ordering / deadlock, condition-variable patterns, blocking-while-locked, callback-while-locked, double-checked locking, try_lock misuse, and RTOS priority inversion.

> **Boundary**: this file is about correct **use** of mutexes and lock guards. Broader synchronization concerns (atomic, volatile, ISR sharing, MMIO RMW, memory order) live in `concurrency-and-isr.md`. The cross-reference table in `references/templates.md` maps every lock-related pattern to its template id and home file.

Per-template contract field definitions live in `references/templates.md` (the index).

## 索引

| ID | 名称 | 严重 | 适用 |
|---|---|---|---|
| `res-mutex-no-unlock` | `mutex.lock()` 未在所有路径上 `unlock` (锁泄漏) | high | C / C++ |
| `con-lock-guard-temporary-unnamed` | 未命名 `std::lock_guard(m);` 临时对象立即析构, 实际未持锁 | critical | C++ |
| `con-recursive-lock-on-non-recursive-mutex` | 已持锁状态下再次获取同一非递归 mutex | critical | C / C++ |
| `con-wrong-mutex-guards-data` | 同一字段在不同路径上被不同 mutex 保护 | critical | C / C++ |
| `con-try-lock-no-check` | `m.try_lock()` 返回值被忽略 | high | C / C++ |
| `con-lock-ordering-deadlock` | 锁获取顺序不一致 → 死锁 | critical | C / C++ |
| `con-sleep-or-blocking-with-lock-held` | 持锁时 sleep / I-O / wait | high | C / C++ |
| `con-callback-invoked-with-lock-held` | 持锁时回调外部代码 | high | C / C++ |
| `con-double-checked-locking` | 非原子指针上的 DCLP | critical | C++ |
| `con-condvar-no-predicate` | `cv.wait` 无谓词 | high | C++ |
| `rtos-priority-inversion-no-protocol` | RTOS mutex 缺优先级继承 → 优先级反转 | high | C / C++ embedded |

---

## Lock leak

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

## Lock construction misuse

### `con-lock-guard-temporary-unnamed`
- **name:** `std::lock_guard` / `std::scoped_lock` constructed as an unnamed temporary (releases immediately)
- **category:** concurrency
- **severity:** critical
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(std::)?(lock_guard|scoped_lock|unique_lock)\s*<' -g '!third_party/**'
  ```
  Pass 3 narrows to lines where the guard is built without binding to a named local — e.g. `std::lock_guard<std::mutex>(m);` or `std::scoped_lock(m1, m2);` as a statement.
- **false_positive_filters:**
  - The match is a typedef / `using` alias.
  - The match is a function parameter (`void f(std::unique_lock<std::mutex> g)`).
  - The match is followed by `=` or `(...) <name>` binding it to a variable.
- **verification:**
  1. For each match, confirm the syntactic form: `<guard><...>(<args>);` with **no** identifier between `<...>` and `(`.
  2. C++ rules: an unnamed temporary is destroyed at the end of the *full-expression* (the `;`), so the lock is released immediately. The code that follows is unprotected even though it visually appears to be inside a critical section.
  3. The most common typo is forgetting the variable name: `std::lock_guard<std::mutex>(m);` instead of `std::lock_guard<std::mutex> g(m);`.
- **required_evidence:**
  - `guard_construction_site`: `<file:line>` of the unnamed-temporary construction.
  - `intended_critical_section`: `<file:line range>` of the code that the author *intended* to protect.
  - `mutex_identity`: which mutex was passed in.
- **confidence_rubric:**
  - `high`: clearly an unnamed `lock_guard<T>(m);` statement followed by accesses to data the mutex protects.
  - `medium`: unnamed guard but the surrounding code does not obviously touch protected data (still wrong, but lower blast radius).
- **bad_example:**
  ```cpp
  void Cache::Insert(const Entry& e) {
    std::lock_guard<std::mutex>(cache_mutex_);   // BUG: unnamed; releases now
    entries_.push_back(e);                       // unprotected!
    cache_size_ += e.size;                       // unprotected!
  }
  ```
- **good_example:**
  ```cpp
  void Cache::Insert(const Entry& e) {
    std::lock_guard<std::mutex> g(cache_mutex_); // named; lives until '}'
    entries_.push_back(e);
    cache_size_ += e.size;
  }
  ```
- **fix_suggestions:**
  - Always bind the guard to a named local. Modern compilers warn (`-Wunused-value` / Clang `-Wunused-lock`) — enable them.
  - Prefer C++17 CTAD: `std::lock_guard g{cache_mutex_};` (still requires a name).

---

### `con-recursive-lock-on-non-recursive-mutex`
- **name:** Re-acquiring a non-recursive mutex while already holding it
- **category:** concurrency
- **severity:** critical
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(std::mutex|pthread_mutex_t|os_mutex_t|SemaphoreHandle_t)\b' -g '!third_party/**'
  ```
  Pass 3 enumerates each mutex variable and the functions that take it; then walks the in-scope call graph from inside each critical section to find any callee that re-takes the same mutex.
- **false_positive_filters:**
  - The mutex is a `std::recursive_mutex` / `pthread_mutex_t` initialised with `PTHREAD_MUTEX_RECURSIVE` / FreeRTOS `xSemaphoreCreateRecursiveMutex`. Recursive mutexes by design accept re-entry from the same thread.
  - The "re-take" is on a *different instance* (e.g. `obj1.mu_` vs `obj2.mu_`).
- **verification:**
  1. Identify the mutex type. `std::mutex`, default-initialised `pthread_mutex_t`, `xSemaphoreCreateMutex` are all NON-recursive.
  2. For each function that takes this mutex, walk its body and the bodies of every function it calls (within audited scope). Flag any recursive acquisition of the same mutex.
  3. Outcome: on `std::mutex` → undefined behaviour (typically deadlock or assertion). On default `pthread_mutex_t` → deadlock. On FreeRTOS non-recursive mutex → assertion / deadlock.
- **required_evidence:**
  - `mutex_declaration`: `<file:line>` of the mutex with its type.
  - `outer_lock_site`, `inner_lock_site`: the two acquisitions on the same call stack.
  - `call_path`: the sequence of calls from outer to inner.
- **confidence_rubric:**
  - `high`: a single function calls another function that locks the same mutex, with no `unlock` between them.
  - `medium`: re-entry happens through a longer call chain; one of the intermediate calls might in fact unlock first.
  - `low`: re-entry possible only via a callback that the auditor cannot enumerate.
- **bad_example:**
  ```cpp
  std::mutex m_;
  void Foo() { std::lock_guard g(m_); Bar(); }
  void Bar() { std::lock_guard g(m_); /* deadlock if called from Foo */ }
  ```
- **fix_suggestions:**
  - Refactor to release the lock before calling the callee, OR have the callee accept a "lock already held" overload (cite the precondition).
  - If recursive locking is genuinely desired, use `std::recursive_mutex` (and document why).
  - For RTOS, `xSemaphoreCreateRecursiveMutex` accepts re-entry; be explicit about the choice.

---

### `con-wrong-mutex-guards-data`
- **name:** Same field protected by different mutexes on different paths (inconsistent guard)
- **category:** concurrency
- **severity:** critical
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(std::)?(lock_guard|scoped_lock|unique_lock)\s*<' -g '!third_party/**'
  ```
  Pass 3 enumerates each shared field's accesses and collects the lock-set held at each access site; flags fields where the lock-set differs across writers.
- **false_positive_filters:**
  - The differing lock-set is intentional and one of them is documented as a SUPERSET of the other (e.g. `big_lock_` always implies `small_lock_`).
  - One access site is provably single-threaded (init / shutdown).
- **verification:**
  1. Pick a shared field (typically a non-`const` data member touched by ≥ 2 functions).
  2. For each access (read or write), determine the lock-set held.
  3. If the set differs across access sites and neither is a superset, the field has inconsistent protection — equivalent to no protection at all on the divergent paths.
  4. Common project pattern: a refactor moved code from class A (protected by `a_mu_`) to class B (protected by `b_mu_`), but one access path still uses the old mutex.
- **required_evidence:**
  - `field_declaration`: `<file:line>`.
  - `access_site_with_lock_a`: `<file:line>` and the mutex held.
  - `access_site_with_lock_b`: `<file:line>` and the (different) mutex held.
  - `proof_paths_can_concurrently_execute`: thread-affinity sketch showing both paths can run together.
- **confidence_rubric:**
  - `high`: same field written under `mu1_` in one method and under `mu2_` in another, with no superset relation.
  - `medium`: field accessed under different locks but the access pattern suggests a refactor in progress.
- **bad_example:**
  ```cpp
  class Cache {
    std::mutex insert_mu_, evict_mu_;
    size_t size_;
    void Insert(...) { std::lock_guard g(insert_mu_); size_ += s; ... }
    void Evict (...) { std::lock_guard g(evict_mu_);  size_ -= s; ... }   // races with Insert
  };
  ```
- **fix_suggestions:**
  - Pick ONE mutex per piece of state and use it everywhere the state is touched.
  - Document the mutex/state mapping in a comment next to the data declarations.
  - Use Clang `-Wthread-safety` annotations (`GUARDED_BY(mu_)`) — the compiler will catch most of these statically.

---

### `con-try-lock-no-check`
- **name:** `try_lock()` return value ignored
- **category:** concurrency
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '\.try_lock\s*\(\s*\)\s*;' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - The very next line is `if (!locked) { … }` style on a previously-captured value.
  - The call is inside a `static_cast<void>(...)` / `(void) m.try_lock();` deliberately discarding the result (still wrong, but the developer was explicit — flag it).
- **verification:**
  1. Locate the `try_lock` call.
  2. Confirm its return value is not consumed (no `if`, no assignment, no `[[nodiscard]]` warning suppression with a use).
  3. Without the check, the subsequent code runs whether or not the lock was actually acquired — same as no lock at all on the contention path.
- **required_evidence:**
  - `try_lock_site`: `<file:line>`.
  - `subsequent_use_of_protected_data`: `<file:line>` of the unprotected access.
- **confidence_rubric:**
  - `high`: `try_lock` followed by accesses to a field the corresponding mutex protects.
- **bad_example:**
  ```cpp
  void Process() {
    cache_mutex_.try_lock();    // return ignored
    entries_.push_back(...);    // may execute without holding the lock
    cache_mutex_.unlock();      // UB: unlock without lock
  }
  ```
- **fix_suggestions:**
  - Use `std::unique_lock<std::mutex> g(cache_mutex_, std::try_to_lock); if (!g.owns_lock()) return;`.
  - Or `if (cache_mutex_.try_lock()) { …; cache_mutex_.unlock(); }`.

---

## Lock ordering / deadlock

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

## Behaviour while locked

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

## Lazy init / DCLP

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

## Condition variable

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

## RTOS-specific

### `rtos-priority-inversion-no-protocol`
- **name:** RTOS mutex without a priority-inheritance / ceiling protocol
- **category:** concurrency
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(xSemaphoreCreateMutex|xSemaphoreCreateBinary|osMutexNew|k_mutex_init)\b' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - The RTOS mutex is created with priority inheritance enabled (FreeRTOS `xSemaphoreCreateMutex` does include PI; `xSemaphoreCreateBinary` does NOT).
  - All tasks contending the mutex have equal priority.
  - The mutex is only contended on rare paths and a documented worst-case bound is acceptable.
- **verification:**
  1. Identify each mutex / binary semaphore creation.
  2. Determine the priority spread of contending tasks (use `xTaskCreate` priority arguments).
  3. If a low-priority task can hold the mutex while a higher-priority task waits, **and** an unrelated mid-priority task can preempt the holder, you have priority inversion.
- **required_evidence:**
  - `mutex_creation`: `<file:line>` and creation API.
  - `low_prio_holder`, `high_prio_waiter`, `mid_prio_preempter`: cite at least one task at each level.
  - `protocol_in_use`: which protocol, or "none".
- **fix_suggestions:**
  - Use `xSemaphoreCreateMutex` (FreeRTOS) which provides priority inheritance, instead of binary semaphores for mutual exclusion.
  - Use ceiling priority by raising the holder's priority before taking the mutex.
  - Reduce the priority spread or shorten critical sections.
