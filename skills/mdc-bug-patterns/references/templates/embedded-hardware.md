# 嵌入式硬件专项 (embedded-hardware)

> Specialty file for **purely hardware-domain** concerns in C/C++ embedded firmware that don't fit cleanly into memory / concurrency / resource / numeric. Load this when the audit scope is watchdog timing, low-power mode pairing, MMIO bit-field RMW, in-flash code execution, long IRQ-disable critical sections, or fixed-stack recursion.

Per-template contract field definitions live in `references/templates.md` (the index).

This file holds 6 hardware-flavoured templates. Some reference patterns also exist in other specialty files (e.g. `con-callback-with-lock-held` is concurrency, but `emb-irq-disabled-too-long` is real-time-correctness and lives here). Load this file alongside the others when the codebase is bare-metal or RTOS firmware on resource-constrained MCUs.

## 索引

| ID | 名称 | 严重 | 适用 |
|---|---|---|---|
| `emb-watchdog-not-fed-long-loop` | 长循环未在 WDT 超时前喂狗 | high | C / C++ embedded |
| `emb-power-mode-enter-no-exit` | 进入低功耗模式但缺少配对的 exit | high | C / C++ embedded |
| `emb-bitfield-write-volatile-rmw` | 写 volatile struct 的位域触发整字 RMW, 干扰其它字段 | high | C / C++ embedded |
| `emb-flash-write-blocks-execution` | 在执行 flash 同 bank 上做 erase/program, 阻塞 CPU 取指 | high | C / C++ embedded |
| `emb-irq-disabled-too-long` | 关中断的临界区过长, 影响实时性与 ISR 抖动 | high | C / C++ embedded |
| `emb-recursion-in-task-fixed-stack` | 在固定栈的 RTOS 任务里使用递归 | high | C / C++ embedded |

---

### `emb-watchdog-not-fed-long-loop`
- **name:** Long loop / blocking call exceeds the watchdog timeout without refresh
- **category:** embedded-hardware
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(while|for|do)\s*\(' -g '!third_party/**'
  ```
  Pass 3 narrows to long-running loops in functions that run while the WDT is enabled, and checks for `IWDG_Refresh` / `HAL_IWDG_Refresh` / `kick_watchdog` / `wdt_reset` calls.
- **false_positive_filters:**
  - The loop bound is small and trivially fits within the WDT period.
  - The loop calls a RTOS-yielding API (`vTaskDelay`, `osDelay`); some watchdog frameworks reset on idle hook.
  - Project does not enable the watchdog at all (deduce from boot / init code).
- **verification:**
  1. Determine WDT period from `HAL_IWDG_Init` / `LL_IWDG_Init` configuration (prescaler + reload).
  2. Estimate loop duration (number of iterations × per-iteration latency, including blocking calls inside).
  3. If estimate ≥ WDT period and no refresh happens inside, the device will reset.
- **required_evidence:**
  - `loop_site`, `wdt_period_estimate`, `refresh_or_absence`.
- **fix_suggestions:**
  - Refresh the watchdog inside the loop body (every iteration or every N iterations).
  - Or move the long work to a separate task and let the idle hook refresh.
  - Or temporarily disable the watchdog around the operation if the design allows (rarely a good idea on safety-critical devices).

---

### `emb-power-mode-enter-no-exit`
- **name:** Entered low-power mode without matching exit / restoration
- **category:** embedded-hardware
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(HAL_PWR_EnterSTOPMode|HAL_PWR_EnterSLEEPMode|HAL_PWR_EnterSTANDBYMode|__WFI|__WFE|nrf_pwr_mgmt_run|sleep_enter|deepsleep)\b' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - The "exit" is implicit (CPU wakes naturally on interrupt and continues).
  - The function is documented as a pure idle hook (mode entry + wake = same statement).
- **verification:**
  1. Identify the entry call.
  2. Determine whether the post-wake code path correctly re-enables peripherals that were disabled before sleep (PLL re-lock, peripheral clocks, DMA re-arm, GPIO re-configure if changed).
  3. A common bug: enter STOP, peripherals disabled, wake-on-interrupt fires; ISR runs but the interrupt source is now unconfigured.
- **required_evidence:**
  - `enter_site`, `exit_path`, `peripherals_re-enabled` (list).
- **fix_suggestions:**
  - Symmetric pre-sleep / post-wake routines that snapshot and restore peripheral state.
  - Use the vendor's "tickless idle" framework which usually handles the pairing.

---

### `emb-bitfield-write-volatile-rmw`
- **name:** Writing a single bit-field in a `volatile` register struct triggers RMW that disturbs other fields
- **category:** embedded-hardware
- **severity:** high
- **detection_query:**
  ```bash
  rg -nU --type cpp 'volatile\s+struct[\s\S]{0,200}\b\w+\s*:\s*\d+\s*;' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - The peripheral provides separate set / clear bit-set registers (STM32 `BSRR`, NRF `OUTSET`/`OUTCLR`).
  - The whole register is owned by a single context (no concurrent writer).
- **verification:**
  1. Identify peripheral register typedefs that mix bit-fields under a `volatile` struct.
  2. Find code that writes ONE bit-field (`reg->FIELD = value;`).
  3. The compiler emits a load-modify-store of the WHOLE word. If another bit-field in the same word is set by an ISR or peripheral hardware between load and store, that bit is silently cleared.
- **required_evidence:**
  - `register_typedef`, `bitfield_write_site`, `concurrent_modifier`.
- **bad_example:**
  ```c
  volatile struct {
      uint32_t enable : 1;
      uint32_t flag   : 1;   // hardware sets this asynchronously
      uint32_t pad    : 30;
  } *REG;
  REG->enable = 1;   // RMW: reads flag, writes back; if hw set flag in between, it's lost
  ```
- **fix_suggestions:**
  - Use the dedicated set/clear/toggle register the peripheral provides.
  - Or compose a full-word value in a local and write it once.

---

### `emb-flash-write-blocks-execution`
- **name:** Writing / erasing flash from code that executes from the same flash bank
- **category:** embedded-hardware
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(HAL_FLASH_Program|HAL_FLASH_Erase|FLASH_PageErase|FLASH_Program|nrf_nvmc_\w+|flash_write|flash_erase)\s*\(' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - The write/erase function is linked into RAM (e.g. `__attribute__((section(".RamFunc")))`) so execution doesn't fetch from flash during the operation.
  - The MCU has dual-bank flash and the code runs from the other bank.
- **verification:**
  1. Find flash program/erase APIs.
  2. Determine whether the calling function is in flash or RAM (linker section, `__attribute__((section))`, or vendor RAM-funcs file).
  3. If flash, every CPU instruction fetch during program/erase stalls; ISRs may not run on time → real-time failure.
  4. Some MCUs additionally REQUIRE the operation to run from RAM (or fault).
- **required_evidence:**
  - `flash_op_site`, `caller_section`, `mcu_constraint`.
- **fix_suggestions:**
  - Mark the flash-program function as RAM-resident (`.RamFunc`) and verify the linker places it there.
  - Disable interrupts around the operation OR ensure all critical ISRs are also in RAM.
  - If supported, use dual-bank flash and execute from the alternate bank.

---

### `emb-irq-disabled-too-long`
- **name:** Critical section disables IRQs for too many cycles, hurting real-time response
- **category:** embedded-hardware
- **severity:** high
- **detection_query:**
  ```bash
  rg -nU --type cpp '__disable_irq\s*\(\s*\)' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - The protected operation is a few instructions (single RMW).
  - The system has no time-critical IRQ that could miss its deadline.
- **verification:**
  1. Find each `__disable_irq()` (or `taskENTER_CRITICAL`, `portDISABLE_INTERRUPTS`) and its matching enable.
  2. Estimate the number of cycles between them: any loop, function call, or memory access counts.
  3. Compare to the strictest IRQ deadline in the system (e.g. UART RX on a 1 Mbaud line is ~10 µs per byte ⇒ ~1600 cycles at 168 MHz).
  4. If the critical section is comparable to or exceeds the deadline, real-time bugs are possible.
- **required_evidence:**
  - `disable_site`, `enable_site`, `cycles_between`, `tightest_deadline`.
- **fix_suggestions:**
  - Shrink the critical section: only the actual RMW needs protection.
  - Mask only the relevant interrupts (`NVIC_DisableIRQ(IRQn)`) instead of all.
  - Use lock-free data structures (single-producer / single-consumer ring buffers).

---

### `emb-recursion-in-task-fixed-stack`
- **name:** Recursive function invoked from a fixed-stack RTOS task
- **category:** embedded-hardware
- **severity:** high
- **detection_query:**
  ```bash
  rg -nU --type cpp 'void\s+(\w+)\s*\([^)]*\)\s*\{' -g '!third_party/**'
  ```
  Pass 3 walks the call graph and flags any function reachable from an RTOS task body whose body calls itself (or transitively forms a cycle).
- **false_positive_filters:**
  - Tail-call optimisation is guaranteed by the toolchain AND the recursion is genuinely tail-call.
  - Recursion depth is bounded by a small constant verified at compile time.
- **verification:**
  1. Identify each task entry point (`xTaskCreate(..., &TaskFunc, ..., uxStackDepth, ...)`).
  2. Walk the call graph from the task; flag any cycle.
  3. Estimate worst-case recursion depth and per-frame stack usage; compare to `uxStackDepth`.
- **required_evidence:**
  - `task_entry`, `recursive_function`, `depth_estimate`, `task_stack_size`.
- **fix_suggestions:**
  - Convert recursion to iteration with an explicit work queue.
  - Bound the recursion depth at compile time and assert at runtime.
  - Increase `uxStackDepth` and re-measure with `uxTaskGetStackHighWaterMark`.
