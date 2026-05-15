# 锁使用专项 (lock-usage)

> Specialty file for **mutex / lock-guard / critical-section misuse** in C/C++ embedded firmware. Load when audit scope is "锁使用是否正确".

> **Boundary**: this file is about correct **use** of mutexes and lock guards. Broader synchronization (atomic, volatile, ISR sharing, MMIO RMW, memory order) lives in `concurrency-and-isr.md`. See the cross-reference table in `references/templates.md` for the full lock-usage roster.

Per-template slim format (see `references/templates.md` for field roles): `id` is the per-template tag; `severity` + `what` are one-liners for triage; `detection_query` is the rg prior consumed by `scan_candidates.py`; `fp_filters` / `verification` / `required_evidence` / `confidence` / `fix` are the discipline contract — the LLM uses its own knowledge of the pattern, the contract just enforces auditable output.

## 索引

| ID | severity |
|---|---|
| `res-mutex-no-unlock` | high |
| `con-lock-guard-temporary-unnamed` | critical |
| `con-recursive-lock-on-non-recursive-mutex` | critical |
| `con-wrong-mutex-guards-data` | critical |
| `con-try-lock-no-check` | high |
| `con-lock-ordering-deadlock` | critical |
| `con-sleep-or-blocking-with-lock-held` | high |
| `con-callback-invoked-with-lock-held` | high |
| `con-double-checked-locking` | critical |
| `con-condvar-no-predicate` | high |
| `rtos-priority-inversion-no-protocol` | high |

---

### `res-mutex-no-unlock`
- **severity:** high
- **what:** `mutex.lock()` not paired with `unlock()` on every reachable exit (return / throw / goto). RAII-managed locks are correct.
- **detection_query:**
  ```bash
  rg -n --type cpp '\.lock\(\)\s*;' -g '!third_party/**'
  ```
- **fp_filters:** match is on `std::lock_guard` / `std::unique_lock` constructor (not a `lock()` call); `fp.dead-code`.
- **verification:**
  1. Identify the mutex variable.
  2. Walk every reachable exit — confirm explicit `unlock()` on each (including throw paths since `lock()` is not exception-safe).
- **required_evidence:** `lock_site`, `leaking_exit`, `exception_path_check`.
- **confidence:** `high` if a concrete leaking exit cited; `medium` if exception path is the only unhandled exit.
- **fix:** use `std::lock_guard` / `std::unique_lock` / `std::scoped_lock` (RAII).

---

### `con-lock-guard-temporary-unnamed`
- **severity:** critical
- **what:** `std::lock_guard<std::mutex>(m);` (no variable name) creates an unnamed temporary; the destructor releases the lock at the end of the same statement, so the "protected" code that follows runs unlocked.
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(std::)?(lock_guard|scoped_lock|unique_lock)\s*<' -g '!third_party/**'
  ```
- **fp_filters:** match is a typedef / `using` alias; match is a function-parameter type; match is followed by `=` or `(...)` with a binding name.
- **verification:**
  1. Confirm the form `<guard><…>(<args>);` with NO identifier between `>` and `(`.
  2. List the data accesses immediately after the construction the author intended to protect.
- **required_evidence:** `guard_construction_site`, `intended_critical_section`, `mutex_identity`.
- **confidence:** `high` if unnamed guard followed by writes to data the mutex protects; `medium` if surrounding code does not touch protected data.
- **fix:** bind to a named local; enable `-Wunused-value` / Clang `-Wunused-lock`.

---

### `con-recursive-lock-on-non-recursive-mutex`
- **severity:** critical
- **what:** Re-acquiring `std::mutex` / default `pthread_mutex_t` / FreeRTOS non-recursive mutex while already holding it — UB or deadlock.
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(std::mutex|pthread_mutex_t|os_mutex_t|SemaphoreHandle_t)\b' -g '!third_party/**'
  ```
- **fp_filters:** mutex is `std::recursive_mutex` / `pthread_mutex_t` with `PTHREAD_MUTEX_RECURSIVE` / `xSemaphoreCreateRecursiveMutex`; the "re-take" is on a different instance.
- **verification:**
  1. Identify the mutex type (non-recursive vs recursive).
  2. From inside each critical section, walk the in-scope call graph; flag any callee that re-takes the same mutex without `unlock` between.
- **required_evidence:** `mutex_declaration`, `outer_lock_site`, `inner_lock_site`, `call_path`.
- **confidence:** `high` if outer→inner is a single direct call; `medium` if path is multi-hop; `low` if re-entry only via a callback the auditor cannot enumerate.
- **fix:** restructure to release the lock before the inner call, OR use `std::recursive_mutex` (document why).

---

### `con-wrong-mutex-guards-data`
- **severity:** critical
- **what:** Same field protected by mutex A on one path and mutex B on another — equivalent to no protection on the divergent paths. Often appears mid-refactor.
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(std::)?(lock_guard|scoped_lock|unique_lock)\s*<' -g '!third_party/**'
  ```
- **fp_filters:** the differing lock-set is intentional (one mutex is a documented superset of the other); one access site is provably single-threaded.
- **verification:**
  1. Pick a shared field (non-`const` data member touched by ≥ 2 functions).
  2. For each access, record the lock-set held.
  3. Inconsistent lock-sets across writers → bug.
- **required_evidence:** `field_declaration`, `access_site_with_lock_a`, `access_site_with_lock_b`, `proof_paths_can_concurrently_execute`.
- **confidence:** `high` if same field written under `mu1_` and `mu2_` with no superset relation; `medium` if pattern suggests in-flight refactor.
- **fix:** pick ONE mutex per piece of state; use Clang `-Wthread-safety` `GUARDED_BY(mu_)` annotations.

---

### `con-try-lock-no-check`
- **severity:** high
- **what:** `m.try_lock();` return value ignored; subsequent code runs whether or not the lock was acquired.
- **detection_query:**
  ```bash
  rg -n --type cpp '\.try_lock\s*\(\s*\)\s*;' -g '!third_party/**'
  ```
- **fp_filters:** result captured in a previously-declared bool; `(void) m.try_lock();` deliberate (still wrong — flag).
- **verification:**
  1. Confirm return value is not consumed (no `if`, no assignment).
  2. Identify subsequent accesses to data the mutex protects.
- **required_evidence:** `try_lock_site`, `subsequent_use_of_protected_data`.
- **confidence:** `high` if `try_lock` followed by accesses to protected data.
- **fix:** `std::unique_lock<std::mutex> g(m, std::try_to_lock); if (!g.owns_lock()) return;`.

---

### `con-lock-ordering-deadlock`
- **severity:** critical
- **what:** Two functions take locks A and B in opposite orders; if both run on different threads they deadlock.
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(std::(lock_guard|unique_lock|scoped_lock)|\.lock\(\))' -g '!third_party/**'
  ```
- **fp_filters:** `fp.deadlock.scoped-lock` (multi-mutex `std::scoped_lock` is deadlock-avoiding); `fp.deadlock.no-cycle-observed`; both endpoints execute on the same thread.
- **verification:**
  1. For each function with ≥ 2 locks, record `(entry_lock_set, additional_locks_in_order)`.
  2. Build a directed graph `A→B` per function. Cycle reachable from independent threads = deadlock candidate.
- **required_evidence:** `path_a` (A-then-B), `path_b` (B-then-A), `concurrent_threads`.
- **confidence:** `high` if real cycle on independent threads with no try-lock backoff; `medium` if one path is rare / behind a flag; `low` if lock-set partially unknown (callback).
- **fix:** `std::scoped_lock(mu1, mu2)`; document a global lock order.

---

### `con-sleep-or-blocking-with-lock-held`
- **severity:** high
- **what:** sleep / blocking I/O / wait while a mutex is held — pinned-down critical section, contention spike.
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(std::this_thread::sleep|usleep|nanosleep|sleep\s*\(|recv\s*\(|send\s*\(|poll\s*\(|epoll_wait|select\s*\()' -g '!third_party/**'
  ```
- **fp_filters:** `unique_lock` was `unlock()`ed before the call; the call is `cv.wait(lock, …)` (releases lock during wait — correct).
- **verification:**
  1. Confirm the mutex is still held at the blocking call.
  2. Confirm the call can take significant time.
- **required_evidence:** `lock_site`, `blocking_call_site`, `still_held_proof`.
- **confidence:** `high` if blocking call is unbounded I/O.
- **fix:** release the lock before blocking; re-acquire after.

---

### `con-callback-invoked-with-lock-held`
- **severity:** high
- **what:** External / user-supplied callback invoked while internal lock is held — re-entrant deadlock if callback takes the same subsystem's lock.
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(callback_|cb_|listener_|observer_|on_\w+)\s*\(' -g '!third_party/**'
  ```
- **fp_filters:** callback is documented to require the lock (cite the doc); callback is project-internal and audited to take no locks.
- **verification:**
  1. Confirm the callback is user-supplied (not a fixed internal helper).
  2. Walk callers that supply the callback; flag any that may re-enter the locked subsystem or block.
- **required_evidence:** `lock_site`, `callback_site`, `callback_origin`.
- **confidence:** `high` if callback type is `std::function` from a public API.
- **fix:** snapshot needed data, release the lock, then invoke; or document a "no re-entry" callback contract.

---

### `con-double-checked-locking`
- **severity:** critical
- **what:** Singleton-style outer-null-check / lock / inner-null-check / store, where the variable is NOT `std::atomic` (or is loaded with `relaxed`).
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(if|while)\s*\(\s*!?\s*\w+\s*\)' -g '!third_party/**'
  ```
- **fp_filters:** variable is `std::atomic<T*>` with default / acquire load; construction uses `std::call_once`.
- **verification:**
  1. Confirm the DCL pattern: outer null-check, lock, inner null-check, construct, store.
  2. Confirm the variable is not atomic (or uses `relaxed`).
- **required_evidence:** `outer_check`, `lock_site`, `inner_check_and_store`, `variable_type`.
- **confidence:** `high` for classic DCLP with raw pointer; `medium` if variable is `volatile` only.
- **fix:** `std::call_once`; or `std::atomic<T*>` with acquire/release.

---

### `con-condvar-no-predicate`
- **severity:** high
- **what:** `cv.wait(lock)` without a predicate — spurious wakeup delivers a false-true.
- **detection_query:**
  ```bash
  rg -n --type cpp '\.wait\s*\(\s*[A-Za-z_]\w*\s*\)\s*;' -g '!third_party/**'
  ```
- **fp_filters:** match is on `std::future::wait()` (different API).
- **verification:**
  1. Confirm receiver is `std::condition_variable` / `_any`.
  2. Predicate-less form must be inside a `while (!predicate)` loop.
- **required_evidence:** `wait_site`, `enclosing_loop_or_absence`, `predicate_check_or_absence`.
- **confidence:** `high` if no enclosing loop.
- **fix:** `cv.wait(lock, [&]{ return predicate; });` or `while (!predicate) cv.wait(lock);`.

---

### `rtos-priority-inversion-no-protocol`
- **severity:** high
- **what:** RTOS mutex created without priority-inheritance protocol; low-prio task can be preempted while a high-prio task waits, mid-prio task delays both.
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(xSemaphoreCreateMutex|xSemaphoreCreateBinary|osMutexNew|k_mutex_init)\b' -g '!third_party/**'
  ```
- **fp_filters:** mutex created with PI enabled (FreeRTOS `xSemaphoreCreateMutex` does include PI; `xSemaphoreCreateBinary` does NOT); all contending tasks have equal priority.
- **verification:**
  1. Identify each mutex creation.
  2. Determine the priority spread of contending tasks.
  3. Low-prio holder + high-prio waiter + mid-prio preempter that can run = inversion.
- **required_evidence:** `mutex_creation`, `low_prio_holder`, `high_prio_waiter`, `mid_prio_preempter`, `protocol_in_use`.
- **confidence:** `high` if all three task levels exist and the mid-prio task can preempt.
- **fix:** use `xSemaphoreCreateMutex` (has PI); raise holder's priority; reduce priority spread.
