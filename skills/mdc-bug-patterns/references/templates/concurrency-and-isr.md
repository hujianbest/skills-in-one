# 并发与中断专项 (concurrency-and-isr)

> Specialty file for the C/C++ embedded **concurrency, ISR, and RTOS** audit. Load this when the audit scope is data races, deadlocks, lock misuse, ISR safety, or RTOS API misuse. Per-template contract field definitions live in `references/templates.md` (the index).

This file holds the historical `con-*` templates plus six embedded-flavoured additions covering ISR-shared data, ISR-API misuse, MMIO read-modify-write races, and RTOS priority-inversion.

## 索引

| ID | 名称 | 严重 | 适用 |
|---|---|---|---|
| `con-unsynchronized-shared-write` | 共享数据未一致同步 | critical | C / C++ |
| `con-lock-ordering-deadlock` | 锁获取顺序不一致 | critical | C / C++ |
| `con-double-checked-locking` | 非原子指针上的双重检查锁 | critical | C++ |
| `con-sleep-or-blocking-with-lock-held` | 持锁时 sleep / 阻塞 I/O | high | C / C++ |
| `con-callback-invoked-with-lock-held` | 持锁时回调外部代码 | high | C / C++ |
| `con-missing-memory-order` | `std::atomic` 用 relaxed 但需要 ordering | high | C++ |
| `con-tocttou` | 检查-使用之间存在并发修改 | high | C / C++ |
| `con-condvar-no-predicate` | `cv.wait` 无谓词, 无法应对 spurious wakeup | high | C++ |
| `isr-shared-non-atomic` | ISR 与线程共享变量未做原子/临界区保护 | critical | C / C++ embedded |
| `isr-non-volatile-shared` | ISR 与线程共享变量未声明 `volatile` | critical | C / C++ embedded |
| `isr-blocking-rtos-call` | 在 ISR 中调用阻塞型或非 ISR-safe 的 RTOS API | critical | C / C++ embedded |
| `isr-malloc-or-printf` | 在 ISR 中调用 `malloc` / `printf` / 其它非 ISR-safe 库 | critical | C / C++ embedded |
| `isr-rmw-mmio-no-exclusive` | 寄存器读-改-写未做原子保护 (临界区/LDREX-STREX) | high | C / C++ embedded |
| `rtos-priority-inversion-no-protocol` | RTOS mutex 未启用优先级继承协议 | high | C / C++ embedded |

---

## Concurrency (multi-thread)

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

## ISR / interrupt safety

### `isr-shared-non-atomic`
- **name:** Variable shared between an ISR and a thread accessed non-atomically
- **category:** concurrency
- **severity:** critical
- **detection_query:**
  ```bash
  rg -nU --type cpp '__attribute__\(\(\s*interrupt\s*\)\)|^\s*(void|ISR|IRQHandler)\s+\w*(IRQHandler|_Handler|_isr|_ISR)\s*\(' -g '!third_party/**'
  ```
  First find ISR functions, then for each ISR collect the global / `static` variables it touches; cross-check those variables for non-atomic access from non-ISR contexts.
- **false_positive_filters:**
  - The variable is read/written **only** from a single context (ISR-only or thread-only).
  - The variable is `_Atomic` (C11) / `std::atomic<T>` and the access is whole-word.
  - The variable is read/written under a critical section that disables the relevant IRQ (e.g. `taskENTER_CRITICAL`, `__disable_irq`, `NVIC_DisableIRQ`).
  - The variable is a single byte and the architecture guarantees atomic byte access (still risky with concurrent RMW).
- **verification:**
  1. Identify each global / `static` variable touched in the ISR body.
  2. Find non-ISR readers/writers via `rg -n '\b<var>\b'`.
  3. For each non-ISR access, confirm protection: critical section, atomic op, or interrupt disabled.
  4. The bug exists if the same variable is written non-atomically without disabling the IRQ that runs the ISR.
- **required_evidence:**
  - `isr_function`: `<file:line>` of the ISR.
  - `shared_variable`: declaration and which contexts access it.
  - `unprotected_access`: `<file:line>` of the non-ISR access without protection.
- **confidence_rubric:**
  - `high`: variable is multi-byte / RMW / pointer, accessed without critical section from both contexts.
  - `medium`: single-byte access; arch may give natural atomicity but RMW still races.
  - `low`: cannot conclusively identify the ISR context for this variable.
- **bad_example:**
  ```c
  static uint32_t g_counter;
  void TIM2_IRQHandler(void) {
      g_counter++;                 // RMW from ISR
  }
  uint32_t read_count(void) {
      return g_counter;            // 32-bit read; on M0 this is single-instr,
                                   // but the ISR's RMW races with concurrent thread RMW
  }
  ```
- **good_example:**
  ```c
  static volatile uint32_t g_counter;   // volatile + critical-section guard
  void TIM2_IRQHandler(void) { g_counter++; }
  uint32_t read_count(void) {
      uint32_t v;
      __disable_irq(); v = g_counter; __enable_irq();
      return v;
  }
  ```
- **fix_suggestions:**
  - Use `_Atomic` / `std::atomic` for whole-word counters (and `volatile` for ISR/thread sharing).
  - Wrap multi-step accesses in `taskENTER_CRITICAL` / `__disable_irq` ↔ `__enable_irq`.
  - For data structures, use lock-free single-producer single-consumer queues and document the producer/consumer contexts.

---

### `isr-non-volatile-shared`
- **name:** Variable shared with an ISR not declared `volatile` (compiler may optimise reads)
- **category:** concurrency
- **severity:** critical
- **detection_query:**
  ```bash
  rg -nU --type cpp '__attribute__\(\(\s*interrupt\s*\)\)|^\s*(void|ISR|IRQHandler)\s+\w*(IRQHandler|_Handler|_isr|_ISR)\s*\(' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - Variable is `_Atomic` / `std::atomic` (already implies the right semantics).
  - Variable is wrapped in critical-section accessors that include compiler memory barriers.
- **verification:**
  1. Identify ISR-touched globals.
  2. For each, confirm `volatile` qualifier on the declaration.
  3. Without `volatile`, the compiler may hoist a read out of a polling loop (`while (!flag) {}` becomes infinite loop).
- **required_evidence:**
  - `isr_writer`, `non_isr_reader`, `declaration_missing_volatile`.
- **confidence_rubric:**
  - `high`: classic `while (!flag) {}` polling loop on a non-`volatile` flag set in an ISR.
- **bad_example:**
  ```c
  static int rx_done;          // not volatile!
  void USART1_IRQHandler(void) { rx_done = 1; }
  void wait_rx(void) {
      while (!rx_done) {}      // compiler may load rx_done once and loop forever
  }
  ```
- **fix_suggestions:**
  - Declare ISR-shared flags `volatile uint8_t` (or `_Atomic`).
  - For RTOS, prefer event-group / semaphore-from-ISR primitives.

---

### `isr-blocking-rtos-call`
- **name:** Calling blocking or non-ISR-safe RTOS API from an ISR
- **category:** concurrency
- **severity:** critical
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(vTaskDelay|xQueueSend\b|xQueueReceive\b|xSemaphoreTake\b|xSemaphoreGive\b|osDelay|osMessageQueuePut|osMutex(Acquire|Release)|k_(sleep|sem_take|msgq_put))\s*\(' -g '!third_party/**'
  ```
  These are the BLOCKING / non-FromISR variants. Pass 3 narrows to call sites inside an ISR function.
- **false_positive_filters:**
  - The call is the FromISR variant (`xQueueSendFromISR`, `xSemaphoreGiveFromISR`, `osMessageQueuePutFromISR`).
  - The function is not in fact called from an ISR (verify call graph).
- **verification:**
  1. Identify ISR functions (handler naming convention or `__attribute__((interrupt))`).
  2. Walk the call tree from each ISR; flag any call to a blocking/non-FromISR API.
  3. Note that some FromISR APIs require a `pxHigherPriorityTaskWoken` argument and a `portYIELD_FROM_ISR` at the end of the ISR.
- **required_evidence:**
  - `isr_function`, `blocking_call`, `recommended_fromisr_variant`.
- **confidence_rubric:**
  - `high`: clear blocking call inside an ISR handler.
- **bad_example:**
  ```c
  void EXTI0_IRQHandler(void) {
      xQueueSend(q, &msg, portMAX_DELAY);   // blocks; never legal in an ISR
  }
  ```
- **good_example:**
  ```c
  void EXTI0_IRQHandler(void) {
      BaseType_t hpw = pdFALSE;
      xQueueSendFromISR(q, &msg, &hpw);
      portYIELD_FROM_ISR(hpw);
  }
  ```
- **fix_suggestions:**
  - Switch to the FromISR variant and pass `pxHigherPriorityTaskWoken` correctly.
  - For non-time-critical work, set a flag in the ISR and have a task drain it.

---

### `isr-malloc-or-printf`
- **name:** `malloc` / `free` / `printf` / other non-ISR-safe library calls in an ISR
- **category:** concurrency
- **severity:** critical
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(malloc|calloc|realloc|free|new\b|delete\b|printf|fprintf|snprintf|sprintf|vprintf|fopen)\s*\(' -g '!third_party/**'
  ```
  Pass 3 narrows to occurrences inside ISR functions.
- **false_positive_filters:**
  - The function is provably not on any ISR call path.
  - The toolchain provides an ISR-safe heap (rare; document it).
- **verification:**
  1. Identify ISR functions; build the call graph.
  2. Any reachable call to the listed APIs is a finding.
  3. `printf` typically takes an internal lock on `stdout`, can block on UART tx, and uses heap; all of these are ISR-hostile.
- **required_evidence:**
  - `isr_function`, `unsafe_call`, `reason` (lock-takes / heap / blocking I/O).
- **fix_suggestions:**
  - Replace `printf` with a lock-free ring buffer; flush from a task.
  - Replace `malloc` with a fixed-size pool allocator.
  - Forbid C++ `new`/`delete` on the ISR path.

---

### `isr-rmw-mmio-no-exclusive`
- **name:** Read-modify-write of a peripheral register without exclusive access
- **category:** concurrency
- **severity:** high
- **detection_query:**
  ```bash
  rg -nU --type cpp '\bGPIO\w+->ODR\s*[|^&]?=' -g '!third_party/**'
  ```
  Generally: `<peripheral>->REG |= …` / `&= ~…` / `^= …` patterns. Adapt the regex per vendor naming convention.
- **false_positive_filters:**
  - The register is per-CPU and only ever touched by one execution context.
  - The peripheral provides set/clear/toggle bit-set registers (e.g. STM32 `BSRR`) and the code uses them instead of RMW.
  - The RMW is wrapped in a critical section that masks the relevant interrupts.
- **verification:**
  1. Identify each `*REG |= …` / `&= ~…` line.
  2. Determine other contexts that may write the same register (other tasks, ISRs).
  3. Without exclusive access, concurrent RMW loses one update.
- **required_evidence:**
  - `rmw_site`, `concurrent_writer`, `protection_or_absence`.
- **fix_suggestions:**
  - Use bit-band / dedicated set/clear registers (e.g. STM32 `GPIOx->BSRR`).
  - Wrap the RMW in `__disable_irq()` / `taskENTER_CRITICAL()` paired with re-enable.
  - On Cortex-M with exclusive monitor, use LDREX/STREX patterns from CMSIS `__atomic_*` builtins.

---

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
