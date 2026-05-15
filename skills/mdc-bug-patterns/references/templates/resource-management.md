# 资源与外设管理专项 (resource-management)

> Specialty file for the C/C++ embedded **non-mutex resource and peripheral lifecycle** audit. Load when audit scope is RAII / fd / handle leaks / peripheral clock pairing / RTOS task lifecycle / HW timer / DMA channel / NVIC IRQ deinit.

> **Boundary**: mutex unlock pairing (`res-mutex-no-unlock`) lives in `lock-usage.md`. Per-template slim format: see `references/templates.md`.

## 索引

| ID | severity |
|---|---|
| `res-file-no-close` | high |
| `res-fd-leak-on-error` | high |
| `res-raii-broken-by-release` | medium |
| `res-peripheral-clock-not-disabled` | high |
| `res-rtos-task-not-deleted` | medium |
| `res-timer-or-dma-not-stopped` | high |
| `res-irq-not-disabled-on-deinit` | high |

---

### `res-file-no-close`
- **severity:** high
- **what:** `fopen` not paired with `fclose` on every reachable exit (return / throw).
- **detection_query:**
  ```bash
  rg -n --type cpp '\bfopen\s*\(' -g '!third_party/**'
  ```
- **fp_filters:** wrapped in RAII (`unique_ptr<FILE, FCloser>` etc.); `fp.test-code`.
- **verification:**
  1. Identify receiving variable; trace to all exits.
  2. Each exit must `fclose` or transfer ownership.
- **required_evidence:** `fopen_site`, `leaking_exit`, `ownership_search`.
- **confidence:** `high` if a concrete leaking exit cited.
- **fix:** `std::ifstream` / `std::ofstream`; `unique_ptr<FILE, FCloser>`.

---

### `res-fd-leak-on-error`
- **severity:** high
- **what:** fd / handle returned by `open` / `socket` / `epoll_create` etc. leaks on early-return error path.
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(open|socket|epoll_create|eventfd|inotify_init|timerfd_create|dup|dup2)\s*\(' -g '!third_party/**'
  ```
- **fp_filters:** fd wrapped in RAII (`unique_fd`, `base::ScopedFD`); single exit closes unconditionally.
- **verification:**
  1. Identify the fd-returning call.
  2. Walk all paths after; each exit must `close(fd)` or transfer ownership.
- **required_evidence:** `open_site`, `leaking_exit`, `ownership_search`.
- **confidence:** `high` if early-return after fd acquired with no close.
- **fix:** `unique_fd` RAII; `goto cleanup` (idiomatic C).

---

### `res-raii-broken-by-release`
- **severity:** medium
- **what:** RAII guard `release()`d but the raw pointer is not immediately wrapped in another owner — leak (or downstream double-free).
- **detection_query:**
  ```bash
  rg -n --type cpp '\.release\(\)' -g '!third_party/**'
  ```
- **fp_filters:** `release()` immediately consumed by another owning sink (smart-pointer ctor, ownership-taking function).
- **verification:**
  1. Confirm the `release()` lands in another owner on the same statement or shortly after.
- **required_evidence:** `release_site`, `ownership_destination_or_absence`.
- **confidence:** `high` if no destination owner identified.
- **fix:** prefer `std::move(ptr)` over `release()`; if `release()` necessary, immediately wrap in another owner.

---

### `res-peripheral-clock-not-disabled`
- **severity:** high
- **what:** Peripheral clock enabled (`__HAL_RCC_xxx_CLK_ENABLE` / `RCC_AHBxPeriphClockCmd`) but no matching disable on deinit / error path; wastes power on battery devices.
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(__HAL_RCC_\w+_CLK_ENABLE|RCC_AHB1PeriphClockCmd|RCC_APB[12]PeriphClockCmd|nrf_clock_\w+_request|clk_enable)\s*\(' -g '!third_party/**'
  ```
- **fp_filters:** peripheral remains in use for system lifetime (no deinit path); higher-level driver framework manages clocks (Linux `clk_get` + `clk_put`).
- **verification:**
  1. Identify each clock-enable + the peripheral instance.
  2. Find corresponding deinit / error-path.
  3. Confirm matching disable on every path that abandons the peripheral.
- **required_evidence:** `clock_enable_site`, `deinit_path`, `disable_or_absence`.
- **confidence:** `high` if init / deinit pair exists and deinit forgets disable; `medium` if no deinit yet but error path leaves clock on.
- **fix:** pair every `*_CLK_ENABLE` with `*_CLK_DISABLE` on every error / deinit path; provide `<peri>_deinit()` helper that's the inverse of init.

---

### `res-rtos-task-not-deleted`
- **severity:** medium
- **what:** `xTaskCreate` / `osThreadNew` / `k_thread_create` without matching `vTaskDelete` on shutdown path; transient task creation in error paths is a TCB / stack leak.
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(xTaskCreate(Static)?|osThreadNew|k_thread_create|tx_thread_create)\s*\(' -g '!third_party/**'
  ```
- **fp_filters:** task is intentionally permanent (main control loop) with no shutdown path; firmware never tears down.
- **verification:**
  1. For each task creation, check whether a deinit / shutdown path exists.
  2. If yes, confirm the task is deleted and its resources freed.
- **required_evidence:** `task_create_site`, `shutdown_path_or_absence`, `delete_or_absence`.
- **confidence:** `high` if shutdown path exists but skips `vTaskDelete`.
- **fix:** pair `xTaskCreate` with `vTaskDelete(handle)` in deinit; for one-shot work prefer queued worker tasks over dynamic creation.

---

### `res-timer-or-dma-not-stopped`
- **severity:** high
- **what:** HW timer / DMA channel started but not stopped on error path; a still-running timer can fire IRQs on freed objects → UAF-style crash.
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(HAL_TIM_\w+_Start\w*|HAL_DMA_Start\w*|LL_DMA_EnableChannel|HAL_(SPI|UART|I2C|ADC)_\w+_DMA)\s*\(' -g '!third_party/**'
  ```
- **fp_filters:** peripheral is intentionally permanent (system tick); function is fire-and-forget with cleanup in a completion callback.
- **verification:**
  1. For each start call, walk all error paths after.
  2. Each error path must call the corresponding stop API (`*_Stop*`, `HAL_DMA_Abort`, `LL_DMA_DisableChannel`).
- **required_evidence:** `start_site`, `error_path`, `stop_or_absence`.
- **confidence:** `high` if error path leaves timer running while caller frees state the ISR uses.
- **fix:** pair every `*_Start*` with `*_Stop*` on every error path; small RAII helper or `goto cleanup` (C).

---

### `res-irq-not-disabled-on-deinit`
- **severity:** high
- **what:** NVIC IRQ enabled (`HAL_NVIC_EnableIRQ`) but not disabled before the resources its ISR touches are freed; ISR can fire on freed memory afterwards.
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(HAL_NVIC_EnableIRQ|NVIC_EnableIRQ|nrf_drv_\w+_init|irq_enable)\s*\(' -g '!third_party/**'
  ```
- **fp_filters:** IRQ remains enabled for system lifetime; higher-level framework disables on shutdown.
- **verification:**
  1. Find each `HAL_NVIC_EnableIRQ(IRQn)` + matching deinit path.
  2. Confirm `HAL_NVIC_DisableIRQ(IRQn)` runs BEFORE the resources used by the ISR are freed.
- **required_evidence:** `enable_site`, `deinit_path`, `disable_or_absence`.
- **confidence:** `high` if deinit frees ISR-used resources without first disabling NVIC.
- **fix:** order: `NVIC_DisableIRQ` → `peripheral_disable` → free buffers / TCBs.
