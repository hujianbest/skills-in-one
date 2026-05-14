# 内存安全专项 (memory-safety)

> Specialty file for the C/C++ embedded **memory safety** audit. Load this file when the audit scope is heap / stack / buffer / pointer / DMA-buffer issues. See `references/templates.md` (the index) for the per-specialty decision tree.

Each template below is a **per-unit checklist**, not a prompt. During Pass 3 you read each prioritised code unit (function / method / small file) end-to-end and apply *all* relevant templates as a checklist on that single read. Roles of each template field — `detection_query`, `false_positive_filters`, `verification`, `required_evidence`, `confidence_rubric`, `bad_example`, `good_example`, `fix_suggestions` — are defined in `references/templates.md`.

This file holds the historical `mem-*` and `ptr-*` templates plus four embedded-flavoured additions: stack-overflow on a fixed-stack RTOS task, DMA-buffer alignment / lifetime, and MMIO-pointer must-be-volatile.

## 索引

| ID | 名称 | 严重 | 适用 |
|---|---|---|---|
| `mem-leak-new-no-delete` | 裸 `new` 在某些路径上未配对 `delete` | critical | C++ |
| `mem-array-new-mismatched-delete` | `new[]` 与 `delete` (而非 `delete[]`) 配对 | critical | C++ |
| `mem-double-free` | 同一指针被 `delete`/`free` 两次 | critical | C / C++ |
| `mem-use-after-free` | 释放后继续读写 | critical | C / C++ |
| `mem-uninitialized-read` | 读取未初始化的成员/局部变量 | high | C / C++ |
| `mem-rule-of-three-five` | 自定义析构但缺少拷贝/移动 | high | C++ |
| `mem-buffer-overflow-index` | 未做边界检查的缓冲区下标/拷贝 | critical | C / C++ |
| `mem-strncpy-no-terminator` | `strncpy` 未显式补 `\0` | high | C / C++ |
| `ptr-deref-no-check` | 解引用前未做空指针检查 | critical | C / C++ |
| `ptr-this-may-be-null-callback` | 回调中 `this` 可能已被销毁 | critical | C++ |
| `ptr-optional-value-no-check` | `optional::value()` 前未检查 | medium | C++ |
| `ptr-iterator-invalidated` | 容器被改动后旧迭代器仍被使用 | high | C++ |
| `mem-stack-overflow-large-local` | 在小栈环境 (ISR/RTOS task) 中分配大块栈对象 | high | C / C++ embedded |
| `mem-dma-buffer-stack-allocated` | DMA 缓冲建在栈上, 生命周期可能短于 DMA 传输 | critical | C / C++ embedded |
| `mem-dma-buffer-alignment-or-region` | DMA 缓冲未按 cache 行对齐 / 不在 DMA 可达区 | high | C / C++ embedded |
| `ptr-mmio-non-volatile` | 通过非 `volatile` 指针访问 MMIO 寄存器 | critical | C / C++ embedded |

---

## Memory safety (heap / stack / object)

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
  - If C++ smart pointers are unavailable (legacy / freestanding / no exceptions), wrap each path with explicit `delete` and use `goto cleanup` or a small RAII guard.

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
  - Pointer is set to `nullptr` immediately after first free (subsequent `delete nullptr` / `free(NULL)` is a no-op).
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
  - Iterator / reference invalidation falls under `ptr-iterator-invalidated`.
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

## Pointer / iterator

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

## Embedded-specific memory templates

### `mem-stack-overflow-large-local`
- **name:** Large stack-allocated object in a small-stack context (ISR / RTOS task)
- **category:** memory
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(char|uint8_t|int8_t|int)\s+\w+\s*\[\s*\d{3,}\s*\]' -g '!third_party/**'
  ```
  Matches stack arrays ≥ 3 digits in declared size. Pass 3 narrows by determining whether the enclosing function runs on a low-stack context (ISR, RTOS task with small stack, deeply recursive call chain).
- **false_positive_filters:**
  - The enclosing function only runs on the main thread / has documented adequate stack.
  - The array is `static` / `constexpr` (not on the stack).
  - The array is declared in a function that runs once at boot (ample stack).
- **verification:**
  1. Compute the approximate stack footprint of the function (sum of large locals + reasonable nesting).
  2. Identify all callers and the calling thread / ISR context.
  3. Cross-reference the project's task stack sizes (`xTaskCreate` `uxStackDepth`, FreeRTOS / Zephyr / RT-Thread config); ISR uses the MSP (main stack) on Cortex-M, which is often small.
  4. If the footprint is > ~25% of the smallest reachable stack, report.
- **required_evidence:**
  - `large_local_site`: `<file:line>` of the local declaration with computed size.
  - `caller_context`: which task / ISR can execute this function, and that task's stack size if known.
  - `stack_budget`: smallest stack that reaches this function vs. computed footprint.
- **confidence_rubric:**
  - `high`: footprint > 50% of a known small stack (e.g. 1 KB FreeRTOS task with 512 B local).
  - `medium`: footprint significant but smallest stack unknown.
  - `low`: footprint moderate; only the largest stack reaches this function.
- **bad_example:**
  ```c
  void on_uart_rx_isr(void) {
      char line_buf[1024];   // ISR runs on MSP (often ≤ 1 KB) — overflow risk
      copy_uart_into(line_buf, sizeof line_buf);
      ...
  }
  ```
- **good_example:**
  ```c
  static char line_buf[1024];   // .bss instead of stack
  void on_uart_rx_isr(void) {
      copy_uart_into(line_buf, sizeof line_buf);
      ...
  }
  ```
- **fix_suggestions:**
  - Move large locals to `static` storage (`.bss`) or to a dedicated buffer pool.
  - Pre-allocate at boot and pass a buffer pointer down the call chain.
  - For RTOS tasks, raise `uxStackDepth` and re-measure with `uxTaskGetStackHighWaterMark`.

---

### `mem-dma-buffer-stack-allocated`
- **name:** DMA buffer allocated on the stack
- **category:** memory
- **severity:** critical
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(HAL_(SPI|UART|I2C|DMA)_\w+|HAL_DMA_Start|LL_DMA_\w+|nrf_drv_\w+|hal_dma_\w+|dma_(start|transfer|begin)\w*)\s*\(' -g '!third_party/**'
  ```
  Matches calls to typical HAL/LL DMA APIs. Pass 3 inspects the buffer argument's storage class.
- **false_positive_filters:**
  - The buffer is `static` / global / heap-allocated (lifetime independent of caller).
  - The function blocks on DMA completion before returning (e.g. `HAL_SPI_TransmitReceive` polling mode).
- **verification:**
  1. Identify the buffer pointer passed to the DMA API.
  2. Trace its declaration. If it is a function-local (stack) array, the bug exists.
  3. Confirm the DMA API is asynchronous (does not block on transfer complete) — check the function name (`*_DMA`, `*_IT`, `*_async`) or the docs.
- **required_evidence:**
  - `dma_call_site`: `<file:line>`.
  - `buffer_declaration`: `<file:line>` of the buffer declaration with storage class.
  - `async_proof`: the API is async (cite the API name or doc).
- **confidence_rubric:**
  - `high`: stack-allocated buffer + clearly async DMA call (`*_DMA_Start`, `*_IT`).
  - `medium`: API may block; cannot rule out without reading API docs.
- **bad_example:**
  ```c
  void send_packet(void) {
      uint8_t pkt[64];
      build_packet(pkt);
      HAL_SPI_Transmit_DMA(&hspi1, pkt, sizeof pkt);   // returns immediately;
                                                       // pkt is freed when send_packet returns
  }
  ```
- **fix_suggestions:**
  - Use a `static` or globally-managed buffer.
  - Or block until DMA completes (use the polling variant or wait on a completion semaphore).

---

### `mem-dma-buffer-alignment-or-region`
- **name:** DMA buffer not aligned to cache line or not in DMA-capable memory region
- **category:** memory
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(HAL_(SPI|UART|I2C|DMA)_\w+|HAL_DMA_Start|LL_DMA_\w+|hal_dma_\w+|dma_(start|transfer|begin))\w*\s*\(' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - Buffer declared with `__attribute__((aligned(32)))` or via a project macro that places it in DMA SRAM (`__dma_buf__`).
  - Target MCU has no data cache (e.g. Cortex-M0/M3/M4); cache coherency is not a concern (alignment may still be).
- **verification:**
  1. Identify the MCU and whether it has a data cache (Cortex-M7 / M55 / A-class do; M0/M3/M4 do not).
  2. If cache exists, the buffer must be aligned to the cache line size (typically 32 bytes) AND either non-cacheable region OR explicitly cleaned/invalidated around the transfer.
  3. Confirm the buffer's memory region is reachable by the DMA controller (some MCUs can't DMA into core-coupled SRAM / TCM).
- **required_evidence:**
  - `dma_call_site`, `buffer_declaration`, `mcu_or_cache_assumption`.
- **confidence_rubric:**
  - `high`: cache present, buffer in cacheable RAM, no alignment / no clean-invalidate.
  - `medium`: alignment unclear; cache may or may not be on.
- **fix_suggestions:**
  - Place DMA buffers in a dedicated non-cacheable region with the linker script.
  - Or align to cache line and call `SCB_CleanDCache_by_Addr` / `SCB_InvalidateDCache_by_Addr` around the transfer.
  - Verify the region against the MCU memory map (some peripherals can't DMA into TCM).

---

### `ptr-mmio-non-volatile`
- **name:** MMIO register accessed via non-`volatile` pointer
- **category:** null
- **severity:** critical
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(uint32_t|uint16_t|uint8_t)\s*\*\s*\w+\s*=\s*\(' -g '!third_party/**'
  ```
  Pass 3 narrows to casts of fixed addresses (e.g. `0x40020000`, `GPIOA_BASE`) into pointer types.
- **false_positive_filters:**
  - The pointer is declared `volatile uint32_t *` or via vendor headers (`__IO`, `__I`, `__O` macros from CMSIS) that expand to `volatile`.
- **verification:**
  1. Identify pointer expressions that target a known MMIO address (peripheral base, SCB, NVIC, vendor `*_BASE` macros).
  2. Confirm the pointer / typedef carries a `volatile` qualifier all the way to the dereference.
  3. Without `volatile`, the compiler may cache reads in registers, drop redundant writes, or reorder MMIO accesses across non-MMIO code — causing silent peripheral misbehaviour.
- **required_evidence:**
  - `mmio_pointer_decl`: `<file:line>` of the pointer or typedef.
  - `target_address`: which peripheral base it targets.
  - `missing_volatile`: explicit citation that `volatile` is absent.
- **confidence_rubric:**
  - `high`: pointer cast from a hardcoded peripheral address with no `volatile`.
  - `medium`: typedef is several layers deep; `volatile` may be on an inner type.
- **bad_example:**
  ```c
  uint32_t* gpio_odr = (uint32_t*) 0x40020014;   // missing volatile!
  *gpio_odr = 0x1;
  *gpio_odr = 0x2;   // compiler may drop the first write
  ```
- **good_example:**
  ```c
  volatile uint32_t* gpio_odr = (volatile uint32_t*) 0x40020014;
  *gpio_odr = 0x1;
  *gpio_odr = 0x2;
  ```
- **fix_suggestions:**
  - Always declare MMIO pointers / register-struct fields as `volatile`.
  - Prefer vendor-supplied register definitions (CMSIS device headers use `__IO` / `__I` / `__O` which expand to `volatile`).
