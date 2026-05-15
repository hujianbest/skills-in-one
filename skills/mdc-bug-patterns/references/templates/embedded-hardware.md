# 嵌入式硬件专项 (embedded-hardware)

> Specialty file for **purely hardware-domain** concerns in C/C++ embedded firmware: watchdog timing, low-power mode pairing, MMIO bit-field RMW, in-flash code execution conflicts, long IRQ-disable critical sections, fixed-stack recursion.

Per-template slim format: see `references/templates.md`.

## 索引

| ID | severity |
|---|---|
| `emb-watchdog-not-fed-long-loop` | high |
| `emb-power-mode-enter-no-exit` | high |
| `emb-bitfield-write-volatile-rmw` | high |
| `emb-flash-write-blocks-execution` | high |
| `emb-irq-disabled-too-long` | high |
| `emb-recursion-in-task-fixed-stack` | high |

---

### `emb-watchdog-not-fed-long-loop`
- **severity:** high
- **what:** Long loop / blocking call exceeds the WDT timeout without refresh; device resets mid-operation.
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(while|for|do)\s*\(' -g '!third_party/**'
  ```
- **fp_filters:** loop bound trivially fits within WDT period; loop calls a yielding API (`vTaskDelay`, `osDelay`); WDT not enabled at all.
- **verification:**
  1. Determine WDT period (`HAL_IWDG_Init` / `LL_IWDG_Init` prescaler + reload).
  2. Estimate loop duration (iterations × per-iteration latency including blocking calls).
  3. If estimate ≥ WDT period and no refresh inside → bug.
- **required_evidence:** `loop_site`, `wdt_period_estimate`, `refresh_or_absence`.
- **confidence:** `high` if duration provably exceeds WDT period.
- **fix:** refresh WDT inside the loop; move long work to a separate task with idle-hook refresh.

---

### `emb-power-mode-enter-no-exit`
- **severity:** high
- **what:** Entered low-power mode (STOP / SLEEP / STANDBY / `__WFI`) without correctly restoring peripherals on wake.
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(HAL_PWR_EnterSTOPMode|HAL_PWR_EnterSLEEPMode|HAL_PWR_EnterSTANDBYMode|__WFI|__WFE|nrf_pwr_mgmt_run|sleep_enter|deepsleep)\b' -g '!third_party/**'
  ```
- **fp_filters:** "exit" is implicit (CPU wakes naturally and continues); function is a documented idle hook.
- **verification:**
  1. Identify entry call.
  2. Determine post-wake path correctly re-enables peripherals disabled before sleep (PLL re-lock, peripheral clocks, DMA re-arm, GPIO re-config).
- **required_evidence:** `enter_site`, `exit_path`, `peripherals_re-enabled` (list).
- **confidence:** `high` if peripherals are reconfigured before sleep but not restored on wake.
- **fix:** symmetric pre-sleep / post-wake routines; vendor "tickless idle" framework.

---

### `emb-bitfield-write-volatile-rmw`
- **severity:** high
- **what:** Writing a single bit-field in a `volatile` register struct emits load-modify-store of the whole word; if hardware sets another bit-field in the same word between load and store, that bit is silently cleared.
- **detection_query:**
  ```bash
  rg -nU --type cpp 'volatile\s+struct[\s\S]{0,200}\b\w+\s*:\s*\d+\s*;' -g '!third_party/**'
  ```
- **fp_filters:** peripheral provides separate set/clear bit-set registers (STM32 `BSRR`, NRF `OUTSET`/`OUTCLR`); whole register owned by single context.
- **verification:**
  1. Identify peripheral register typedefs mixing bit-fields under `volatile struct`.
  2. Find code writing ONE bit-field (`reg->FIELD = value;`).
  3. Identify other bit-fields in same word that hardware/ISR sets asynchronously.
- **required_evidence:** `register_typedef`, `bitfield_write_site`, `concurrent_modifier`.
- **confidence:** `high` if hardware-set bit shares the storage word.
- **fix:** dedicated set/clear/toggle register the peripheral provides; compose full-word value in a local and write once.

---

### `emb-flash-write-blocks-execution`
- **severity:** high
- **what:** Flash erase / program from code that executes from the same flash bank stalls all instruction fetch; ISRs miss deadlines; on some MCUs the operation faults if not in RAM.
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(HAL_FLASH_Program|HAL_FLASH_Erase|FLASH_PageErase|FLASH_Program|nrf_nvmc_\w+|flash_write|flash_erase)\s*\(' -g '!third_party/**'
  ```
- **fp_filters:** function is RAM-resident (`__attribute__((section(".RamFunc")))`); MCU has dual-bank flash and code runs from the other bank.
- **verification:**
  1. Find flash program/erase APIs.
  2. Determine whether the calling function is in flash or RAM (linker section / RAM-funcs file).
  3. If flash, every CPU fetch during program/erase stalls; check critical ISR deadlines.
- **required_evidence:** `flash_op_site`, `caller_section`, `mcu_constraint`.
- **confidence:** `high` if caller is in flash and time-critical ISR deadlines exist.
- **fix:** mark flash-program function `.RamFunc`; disable interrupts around the operation OR ensure critical ISRs are also in RAM; use dual-bank flash with execute-from-other-bank.

---

### `emb-irq-disabled-too-long`
- **severity:** high
- **what:** Critical section (`__disable_irq` / `taskENTER_CRITICAL` / `portDISABLE_INTERRUPTS`) covers too many cycles → ISR jitter exceeds real-time deadline.
- **detection_query:**
  ```bash
  rg -nU --type cpp '__disable_irq\s*\(\s*\)' -g '!third_party/**'
  ```
- **fp_filters:** protected operation is a few instructions (single RMW); system has no time-critical IRQ that could miss its deadline.
- **verification:**
  1. Find each `__disable_irq()` and matching enable.
  2. Estimate cycles between (loops, function calls, memory accesses count).
  3. Compare to strictest IRQ deadline (e.g. UART RX at 1 Mbaud is ~10 µs ≈ 1600 cycles at 168 MHz).
- **required_evidence:** `disable_site`, `enable_site`, `cycles_between`, `tightest_deadline`.
- **confidence:** `high` if critical section comparable to or exceeds deadline.
- **fix:** shrink critical section to the actual RMW; mask only the relevant IRQ (`NVIC_DisableIRQ(IRQn)`); lock-free SPSC ring buffers.

---

### `emb-recursion-in-task-fixed-stack`
- **severity:** high
- **what:** Recursive function reachable from a fixed-stack RTOS task; depth-times-frame can overflow the task stack.
- **detection_query:**
  ```bash
  rg -nU --type cpp 'void\s+(\w+)\s*\([^)]*\)\s*\{' -g '!third_party/**'
  ```
  Pass 3 walks the call graph and flags any function reachable from an RTOS task that calls itself or transitively forms a cycle.
- **fp_filters:** tail-call optimisation guaranteed by toolchain AND recursion is genuinely tail-call; recursion depth bounded by small constant verified at compile time.
- **verification:**
  1. Identify each task entry point (`xTaskCreate(..., &TaskFunc, ..., uxStackDepth, ...)`).
  2. Walk call graph from the task; flag any cycle.
  3. Estimate worst-case recursion depth × per-frame stack usage; compare to `uxStackDepth`.
- **required_evidence:** `task_entry`, `recursive_function`, `depth_estimate`, `task_stack_size`.
- **confidence:** `high` if depth × frame > 50% of `uxStackDepth`.
- **fix:** convert recursion to iteration with explicit work queue; bound recursion depth at compile time + assert at runtime; raise `uxStackDepth` and re-measure with `uxTaskGetStackHighWaterMark`.
