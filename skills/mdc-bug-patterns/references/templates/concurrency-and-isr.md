# 并发与中断专项 (concurrency-and-isr)

> Specialty file for the C/C++ embedded **non-mutex concurrency, ISR, and RTOS-API misuse** audit. Load this when the audit scope is data races on atomics / volatiles, memory ordering, TOCTTOU, ISR-thread sharing, or non-ISR-safe API calls from ISR.

> **Boundary**: this file does NOT include mutex / lock-guard / critical-section misuse — those have moved to **`lock-usage.md`**. See the cross-reference table in `references/templates.md` for the full lock-usage roster. If your audit touches both, load both files.

Per-template contract field definitions live in `references/templates.md` (the index).

## 索引

| ID | 名称 | 严重 | 适用 |
|---|---|---|---|
| `con-unsynchronized-shared-write` | 共享数据未一致同步 | critical | C / C++ |
| `con-missing-memory-order` | `std::atomic` 用 relaxed 但需要 ordering | high | C++ |
| `con-tocttou` | 检查-使用之间存在并发修改 | high | C / C++ |
| `isr-shared-non-atomic` | ISR 与线程共享变量未做原子/临界区保护 | critical | C / C++ embedded |
| `isr-non-volatile-shared` | ISR 与线程共享变量未声明 `volatile` | critical | C / C++ embedded |
| `isr-blocking-rtos-call` | 在 ISR 中调用阻塞型或非 ISR-safe 的 RTOS API | critical | C / C++ embedded |
| `isr-malloc-or-printf` | 在 ISR 中调用 `malloc` / `printf` / 其它非 ISR-safe 库 | critical | C / C++ embedded |
| `isr-rmw-mmio-no-exclusive` | 寄存器读-改-写未做原子保护 (临界区/LDREX-STREX) | high | C / C++ embedded |

---

## Concurrency (non-mutex)

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
  - Hold the same mutex on every read and write (see `lock-usage.md` for `con-wrong-mutex-guards-data` if the wrong mutex is held).
  - Or change the field to `std::atomic<T>` with the right memory order.

> **Note**: if the fix is "use a mutex", the *correct usage* of that mutex is audited by the templates in `lock-usage.md`. This template only flags the missing-or-inconsistent-synchronization symptom.

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
