# 资源与外设管理专项 (resource-management)

> Specialty file for the C/C++ embedded **resource and peripheral lifecycle** audit. Load this when the audit scope is RAII / handle leaks / fd leaks / RTOS task or timer or DMA channel cleanup / peripheral deinit.

> **Boundary**: mutex lock-leak is **not** in this file — `res-mutex-no-unlock` lives in `lock-usage.md` together with the rest of the lock-usage templates. Per-template contract field definitions live in `references/templates.md` (the index).

## 索引

| ID | 名称 | 严重 | 适用 |
|---|---|---|---|
| `res-file-no-close` | `fopen` 未在所有路径上 `fclose` | high | C / C++ |
| `res-fd-leak-on-error` | 错误路径上 fd / handle 未关闭 | high | C / C++ |
| `res-raii-broken-by-release` | RAII 守卫被 `release()` 但未接收为新 owner | medium | C++ |
| `res-peripheral-clock-not-disabled` | RCC 时钟使能后未在 deinit 路径上 disable | high | C / C++ embedded |
| `res-rtos-task-not-deleted` | `xTaskCreate` 等创建任务后无 `vTaskDelete` 等清理 | medium | C / C++ embedded |
| `res-timer-or-dma-not-stopped` | HW timer / DMA 通道启动后未在错误路径上停止 | high | C / C++ embedded |
| `res-irq-not-disabled-on-deinit` | NVIC IRQ enable 后 deinit 未做 `NVIC_DisableIRQ` 配对 | high | C / C++ embedded |

---

## Resource (RAII / handles / fds)

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
  - Use `std::ifstream` / `std::ofstream`.
  - Wrap `FILE*` in a `unique_ptr` with custom deleter.

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

## Embedded peripheral lifecycle

### `res-peripheral-clock-not-disabled`
- **name:** Peripheral clock enabled but never disabled in deinit / error path
- **category:** resource
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(__HAL_RCC_\w+_CLK_ENABLE|RCC_AHB1PeriphClockCmd|RCC_APB[12]PeriphClockCmd|nrf_clock_\w+_request|clk_enable)\s*\(' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - The peripheral remains in use for the lifetime of the system (e.g. main UART) and there is no deinit path.
  - The project uses a higher-level driver framework that manages clocks (e.g. Linux `clk_get` + `clk_put`).
- **verification:**
  1. Identify each peripheral clock-enable call and the peripheral instance (`SPI1`, `GPIOA`).
  2. Find the corresponding deinit / error-path code.
  3. Confirm a matching disable (`__HAL_RCC_xxx_CLK_DISABLE`) on every path that abandons the peripheral.
  4. Note that an unused-but-clocked peripheral wastes power — important for battery devices.
- **required_evidence:**
  - `clock_enable_site`, `deinit_path`, `disable_or_absence`.
- **confidence_rubric:**
  - `high`: clear init/deinit pair where deinit forgets to disable the clock.
  - `medium`: no deinit exists yet but an error path leaves the clock on.
- **bad_example:**
  ```c
  void spi1_init(void) {
      __HAL_RCC_SPI1_CLK_ENABLE();
      if (HAL_SPI_Init(&hspi1) != HAL_OK) {
          return;             // clock left on; peripheral half-init'd
      }
  }
  ```
- **fix_suggestions:**
  - Pair every `*_CLK_ENABLE` with `*_CLK_DISABLE` on every error/deinit path.
  - Consider a small helper like `spi1_deinit()` that does the inverse of `spi1_init()`.

---

### `res-rtos-task-not-deleted`
- **name:** RTOS task created without `vTaskDelete` / equivalent on shutdown path
- **category:** resource
- **severity:** medium
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(xTaskCreate(Static)?|osThreadNew|k_thread_create|tx_thread_create)\s*\(' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - Task is intentionally permanent (main control loop) — there's no shutdown path to leak on.
  - Project never tears down (firmware that runs until reset).
- **verification:**
  1. For each task creation, find whether a deinit / shutdown path exists.
  2. If yes, confirm the task is deleted (and any resources owned by it freed).
  3. Note that even if no shutdown exists, transient task creation in error paths is a leak (TCB / stack memory).
- **required_evidence:**
  - `task_create_site`, `shutdown_path_or_absence`, `delete_or_absence`.
- **fix_suggestions:**
  - Pair `xTaskCreate` with `vTaskDelete(handle)` in the deinit path.
  - For one-shot work, consider deferring to a queued worker task instead of creating tasks dynamically.

---

### `res-timer-or-dma-not-stopped`
- **name:** Hardware timer / DMA channel started but not stopped on error path
- **category:** resource
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(HAL_TIM_\w+_Start\w*|HAL_DMA_Start\w*|LL_DMA_EnableChannel|HAL_(SPI|UART|I2C|ADC)_\w+_DMA)\s*\(' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - The peripheral is intentionally permanent (system tick).
  - The function is documented as "fire-and-forget" with the cleanup happening in a completion callback.
- **verification:**
  1. For each start call, walk all error paths after it.
  2. Each error path must call the corresponding stop API (`HAL_TIM_*_Stop*`, `HAL_DMA_Abort`, `LL_DMA_DisableChannel`).
  3. Note that a timer left running can keep firing IRQs on freed objects → use-after-free style crash.
- **required_evidence:**
  - `start_site`, `error_path`, `stop_or_absence`.
- **bad_example:**
  ```c
  HAL_TIM_Base_Start_IT(&htim2);
  if (subscribe_callback() != OK) {
      return;     // timer keeps firing; ISR may race with caller cleanup
  }
  ```
- **fix_suggestions:**
  - Pair every `*_Start*` with `*_Stop*` on every error path.
  - Use a small RAII-ish helper or `goto cleanup` style for C.

---

### `res-irq-not-disabled-on-deinit`
- **name:** NVIC IRQ enabled but not disabled on deinit
- **category:** resource
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(HAL_NVIC_EnableIRQ|NVIC_EnableIRQ|nrf_drv_\w+_init|irq_enable)\s*\(' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - IRQ remains enabled for the lifetime of the system; no deinit exists.
  - The IRQ is disabled by a higher-level driver framework on shutdown.
- **verification:**
  1. Find each `HAL_NVIC_EnableIRQ(IRQn)` and the matching deinit path.
  2. Confirm `HAL_NVIC_DisableIRQ(IRQn)` runs before the resources used by the ISR are freed.
  3. If not, the ISR can fire on freed memory after deinit — a UAF that's hard to debug because timing is non-deterministic.
- **required_evidence:**
  - `enable_site`, `deinit_path`, `disable_or_absence`.
- **fix_suggestions:**
  - Always disable the IRQ in NVIC before tearing down the resources it touches.
  - Order on deinit: `NVIC_DisableIRQ` → `peripheral_disable` → free buffers / TCBs.
