# 并发与中断专项 (concurrency-and-isr)

> Specialty file for the C/C++ embedded **non-mutex concurrency, ISR, and RTOS-API misuse** audit. Load when audit scope is data races on atomics / volatiles, memory ordering, TOCTTOU, ISR-thread sharing, or non-ISR-safe API calls from ISR.

> **Boundary**: mutex / lock-guard / critical-section misuse lives in `lock-usage.md`. If your audit touches both, load both.

Per-template slim format (see `references/templates.md`).

## 索引

| ID | severity |
|---|---|
| `con-unsynchronized-shared-write` | critical |
| `con-missing-memory-order` | high |
| `con-tocttou` | high |
| `isr-shared-non-atomic` | critical |
| `isr-non-volatile-shared` | critical |
| `isr-blocking-rtos-call` | critical |
| `isr-malloc-or-printf` | critical |
| `isr-rmw-mmio-no-exclusive` | high |

---

### `con-unsynchronized-shared-write`
- **severity:** critical
- **what:** Mutation of shared data without consistent synchronization across all readers and writers.
- **detection_query:**
  ```bash
  rg -n --type cpp '\b\w+_\s*(\+\+|--|\+=|-=|=)' -g '!third_party/**'
  ```
  Assumes `member_` trailing-underscore convention; adjust per project (e.g. `m_member`).
- **fp_filters:** `fp.concurrency.single-threaded`, `fp.concurrency.protected-by-lock`, `fp.concurrency.published-once`, `fp.concurrency.atomic-with-correct-order`.
- **verification:** see `references/methodology.md#concurrency-deep-dive` — you MUST build a thread-affinity sketch + a lock-set sketch; cite both.
- **required_evidence:** `field_declaration`, `writer_with_lock` and / or `writer_without_lock`, `reader_sites`, `thread_affinity`.
- **confidence:** `high` if a writer / reader path provably runs on a different thread without holding the same lock; `medium` if thread affinity unclear; `low` if affinity undeterminable in scope.
- **fix:** consistent mutex on every read and write (audited by `lock-usage.md` templates); or `std::atomic<T>` with correct memory order. (If the wrong mutex is held, see `con-wrong-mutex-guards-data` in `lock-usage.md`.)

---

### `con-missing-memory-order`
- **severity:** high
- **what:** `std::atomic` op uses `memory_order_relaxed` where ordering (publication, handoff, read-after-write) is needed.
- **detection_query:**
  ```bash
  rg -n --type cpp 'std::memory_order_relaxed' -g '!third_party/**'
  ```
- **fp_filters:** atomic is a pure counter (statistics / metrics) where transient skew is acceptable; surrounding code documents the relaxed choice.
- **verification:**
  1. Determine what the atomic protects or coordinates.
  2. If it publishes a pointer / signals readiness / sequences other memory operations, `relaxed` is wrong.
- **required_evidence:** `atomic_op_site`, `coordination_use`, `ordering_argument`.
- **confidence:** `high` if relaxed publishes a pointer or coordinates handoff.
- **fix:** `acquire`/`release` for handoff; `seq_cst` for full barriers; comment the chosen order.

---

### `con-tocttou`
- **severity:** high
- **what:** Time-of-check-to-time-of-use race: existence/contains check followed by act on the same key, with no synchronization spanning both.
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(stat|access|exists|contains|count|find)\s*\(' -g '!third_party/**'
  ```
- **fp_filters:** check-then-act runs under a single lock that gates the resource; filesystem case uses `O_CREAT | O_EXCL`.
- **verification:**
  1. Identify check site + act site.
  2. Confirm no synchronization prevents concurrent modification between the two.
- **required_evidence:** `check_site`, `act_site`, `concurrent_modifier`.
- **confidence:** `high` if no lock spans the two and a concurrent modifier is plausible.
- **fix:** atomic check-and-act primitives (`map.emplace`, `O_CREAT|O_EXCL`); span both ops with one lock.

---

### `isr-shared-non-atomic`
- **severity:** critical
- **what:** Variable touched by an ISR is read/written non-atomically from a thread without disabling the corresponding IRQ.
- **detection_query:**
  ```bash
  rg -nU --type cpp '__attribute__\(\(\s*interrupt\s*\)\)|^\s*(void|ISR|IRQHandler)\s+\w*(IRQHandler|_Handler|_isr|_ISR)\s*\(' -g '!third_party/**'
  ```
  First find ISR functions; then collect globals/`static` they touch; cross-check non-ISR access for atomicity / critical section.
- **fp_filters:** variable read/written only from a single context; `_Atomic` / `std::atomic` whole-word access; access wrapped in critical section disabling the relevant IRQ; single-byte access on arch with byte atomicity (still risky for RMW).
- **verification:**
  1. Identify each global / `static` touched in the ISR body.
  2. Find non-ISR accesses (`rg`).
  3. Confirm protection on each: critical section / atomic op / IRQ disabled.
- **required_evidence:** `isr_function`, `shared_variable`, `unprotected_access`.
- **confidence:** `high` if multi-byte / RMW / pointer accessed without critical section from both contexts; `medium` if single-byte but RMW; `low` if ISR context cannot be conclusively identified.
- **fix:** `_Atomic` / `std::atomic` for whole-word counters (still `volatile` for ISR/thread sharing); `taskENTER_CRITICAL` / `__disable_irq` ↔ `__enable_irq` around multi-step accesses; lock-free SPSC ring buffer for data structures.

---

### `isr-non-volatile-shared`
- **severity:** critical
- **what:** Variable shared with an ISR is not declared `volatile`; compiler hoists reads out of polling loops (`while (!flag) {}` becomes infinite loop).
- **detection_query:**
  ```bash
  rg -nU --type cpp '__attribute__\(\(\s*interrupt\s*\)\)|^\s*(void|ISR|IRQHandler)\s+\w*(IRQHandler|_Handler|_isr|_ISR)\s*\(' -g '!third_party/**'
  ```
- **fp_filters:** variable is `_Atomic` / `std::atomic` (already implies the right semantics); accessor wraps include compiler memory barriers.
- **verification:**
  1. Identify ISR-touched globals.
  2. Confirm `volatile` qualifier on declaration.
- **required_evidence:** `isr_writer`, `non_isr_reader`, `declaration_missing_volatile`.
- **confidence:** `high` if classic `while (!flag) {}` polling loop on a non-`volatile` flag.
- **fix:** `volatile uint8_t` (or `_Atomic`); for RTOS prefer event-group / semaphore-from-ISR primitives.

---

### `isr-blocking-rtos-call`
- **severity:** critical
- **what:** ISR calls a blocking / non-FromISR RTOS API (`xQueueSend`, `vTaskDelay`, `xSemaphoreTake`); ISR may sleep forever or corrupt RTOS state.
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(vTaskDelay|xQueueSend\b|xQueueReceive\b|xSemaphoreTake\b|xSemaphoreGive\b|osDelay|osMessageQueuePut|osMutex(Acquire|Release)|k_(sleep|sem_take|msgq_put))\s*\(' -g '!third_party/**'
  ```
- **fp_filters:** call is the FromISR variant; function not on any ISR call path.
- **verification:**
  1. Identify ISR functions (handler naming or `__attribute__((interrupt))`).
  2. Walk call tree from each ISR; flag any call to a blocking / non-FromISR API.
  3. Note FromISR APIs require `pxHigherPriorityTaskWoken` + `portYIELD_FROM_ISR`.
- **required_evidence:** `isr_function`, `blocking_call`, `recommended_fromisr_variant`.
- **confidence:** `high` if clear blocking call inside ISR handler.
- **fix:** FromISR variant + `pxHigherPriorityTaskWoken`; or set a flag in ISR + drain in a task.

---

### `isr-malloc-or-printf`
- **severity:** critical
- **what:** ISR calls non-ISR-safe library: `malloc` / `free` / `printf` / `fopen` (heap, internal locks, blocking I/O).
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(malloc|calloc|realloc|free|new\b|delete\b|printf|fprintf|snprintf|sprintf|vprintf|fopen)\s*\(' -g '!third_party/**'
  ```
- **fp_filters:** function not on any ISR call path; toolchain provides ISR-safe heap (rare; document).
- **verification:**
  1. Identify ISR functions; build call graph.
  2. Any reachable call to listed APIs is a finding.
  3. `printf` typically takes `stdout` lock + can block on UART tx + uses heap.
- **required_evidence:** `isr_function`, `unsafe_call`, `reason` (lock/heap/blocking I/O).
- **confidence:** `high` if call is on a direct ISR path.
- **fix:** lock-free ring buffer for logging (drain in task); fixed-size pool allocator; forbid `new`/`delete` on ISR path.

---

### `isr-rmw-mmio-no-exclusive`
- **severity:** high
- **what:** Read-modify-write of a peripheral register (`reg |=`, `&= ~`, `^=`) without exclusive access; concurrent RMW from another context loses one update.
- **detection_query:**
  ```bash
  rg -nU --type cpp '\bGPIO\w+->ODR\s*[|^&]?=' -g '!third_party/**'
  ```
  Generally `<peripheral>->REG |= …` / `&= ~…` / `^= …`; adapt regex per vendor.
- **fp_filters:** register is per-CPU and only one execution context touches it; peripheral provides set/clear/toggle bit-set registers (STM32 `BSRR`) and code uses them; RMW wrapped in critical section masking the relevant interrupts.
- **verification:**
  1. Identify each `*REG |= …` / `&= ~…` line.
  2. Determine other contexts that may write the same register.
  3. Without exclusive access, concurrent RMW loses one update.
- **required_evidence:** `rmw_site`, `concurrent_writer`, `protection_or_absence`.
- **confidence:** `high` if same register is written from another context with no protection.
- **fix:** dedicated set/clear registers (STM32 `BSRR`); critical section around RMW; LDREX/STREX / CMSIS `__atomic_*` builtins on Cortex-M.
