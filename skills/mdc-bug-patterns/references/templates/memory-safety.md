# 内存安全专项 (memory-safety)

> Specialty file for the C/C++ embedded **memory safety** audit. Load when audit scope is heap / stack / object lifetime / buffer / pointer / DMA-buffer issues. See `references/templates.md` (the index) for the per-specialty decision tree.

Per-template slim format: `id` is the per-template tag; `severity` + `what` are one-liners for triage; `detection_query` is the rg prior consumed by `scan_candidates.py`; `fp_filters` / `verification` / `required_evidence` / `confidence` / `fix` are the discipline contract — the LLM uses its own knowledge of the pattern, the contract just enforces auditable output.

## 索引

| ID | severity |
|---|---|
| `mem-leak-new-no-delete` | critical |
| `mem-array-new-mismatched-delete` | critical |
| `mem-double-free` | critical |
| `mem-use-after-free` | critical |
| `mem-uninitialized-read` | high |
| `mem-rule-of-three-five` | high |
| `mem-buffer-overflow-index` | critical |
| `mem-strncpy-no-terminator` | high |
| `ptr-deref-no-check` | critical |
| `ptr-this-may-be-null-callback` | critical |
| `ptr-optional-value-no-check` | medium |
| `ptr-iterator-invalidated` | high |
| `mem-stack-overflow-large-local` | high |
| `mem-dma-buffer-stack-allocated` | critical |
| `mem-dma-buffer-alignment-or-region` | high |
| `ptr-mmio-non-volatile` | critical |

---

### `mem-leak-new-no-delete`
- **severity:** critical
- **what:** Raw `new` whose pointer is not deleted / not transferred to an owning sink on every reachable exit (return / throw / goto).
- **detection_query:**
  ```bash
  rg -n --type cpp '\bnew\s+[A-Za-z_]' -g '!third_party/**' -g '!build/**'
  ```
- **fp_filters:** `fp.ownership.smart-pointer`, `fp.ownership.transfer-to-sink`, `fp.ownership.container-with-destructor`, `fp.generated-code`, `fp.test-code`.
- **verification:**
  1. Identify the receiving variable / expression.
  2. Enumerate every reachable exit.
  3. For each exit confirm: deleted, transferred to sink, stored in container with releasing dtor, or wrapped in smart pointer.
  4. Throw paths between `new` and wrap also count as leaks.
- **required_evidence:** `allocation_site`, `leaking_exit`, `ownership_search`.
- **confidence:** `high` if a concrete leaking exit cited and ownership search ruled out a wrap; `medium` if escapes to sink with unclear semantics; `low` if ownership trace incomplete in audited scope.
- **fix:** `std::make_unique` / `std::make_shared`; or `goto cleanup` + small RAII guard for legacy / freestanding / no-exceptions code.

---

### `mem-array-new-mismatched-delete`
- **severity:** critical
- **what:** `new T[n]` paired with `delete` (not `delete[]`), or vice versa — UB.
- **detection_query:**
  ```bash
  rg -n --type cpp '\bnew\s+[A-Za-z_][\w:]*\s*\[' -g '!third_party/**' -g '!build/**'
  ```
- **fp_filters:** `fp.ownership.smart-pointer` (`std::unique_ptr<T[]>` is correct).
- **verification:**
  1. For each `new T[n]` site, find the freeing site (same scope or owning destructor).
  2. Confirm freeing form is `delete[]` (not `delete`).
- **required_evidence:** `allocation_site`, `freeing_site`, `mismatch` (operator forms quoted).
- **confidence:** `high` if both sites located with mismatched forms; `medium` if freeing chain is ambiguous (virtual dtor); `low` if freeing site not located.
- **fix:** `std::vector<T>` / `std::unique_ptr<T[]>`; or match `new[]` with `delete[]`.

---

### `mem-double-free`
- **severity:** critical
- **what:** Same logical object freed twice (parent destroys child + child dtor frees, shallow copy without Rule-of-Three, etc.).
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(delete|free)\s*\(?[A-Za-z_][\w\.\->]*\)?\s*;' -g '!third_party/**'
  ```
- **fp_filters:** `fp.dead-code`; pointer set to `nullptr` immediately after first free (subsequent `delete nullptr` / `free(NULL)` is no-op).
- **verification:**
  1. For each free site, find other free sites of the same pointer expression in reachable scopes.
  2. Determine if two frees can hit the same object (copy, alias, container).
  3. Rule-of-Three/Five check: custom dtor `delete`s a member but no copy ctor / assign → copies double-free.
- **required_evidence:** `first_free`, `second_free` (with reaching path), `aliasing_proof`.
- **confidence:** `high` if two concrete sites with reaching path; `medium` if Rule-of-3 violation but no concrete copy site; `low` if aliasing speculative across TUs.
- **fix:** Rule of Five (or `=delete` copies); `std::unique_ptr<char[]>`; null pointers after free.

---

### `mem-use-after-free`
- **severity:** critical
- **what:** Read or write of a pointer / iterator / reference after its referent is freed or invalidated.
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(delete|free|reset|clear|pop_back|erase)\b' -g '!third_party/**'
  ```
- **fp_filters:** subsequent use is on a different object; iterator invalidation falls under `ptr-iterator-invalidated`; `fp.dead-code`.
- **verification:**
  1. Identify the freeing call and the dereference; confirm same object.
  2. For container ops (`erase`, `pop_back`, `clear`, `reset`), check whether iterators / refs / ptrs obtained before the call are reused after.
  3. For owner-managed lifetimes, any later use of a stale raw pointer is UAF.
- **required_evidence:** `free_site`, `use_site`, `reachability` (control-flow path or callgraph).
- **confidence:** `high` if same-function use after free with no rebinding, OR iterator use after documented invalidation; `medium` cross-function with implicit lifetime contract; `low` async callback with no static lifetime proof.
- **fix:** re-acquire iterators after mutation; `std::weak_ptr` for non-owning refs; `shared_ptr` capture or `weak_ptr::lock()` in async callbacks.

---

### `mem-uninitialized-read`
- **severity:** high
- **what:** Member or local read on a path that does not write first; common after refactor that adds a new member without updating all constructors.
- **detection_query:**
  ```bash
  rg -n --type cpp '^\s*(class|struct)\s+\w+' -g '!third_party/**'
  ```
- **fp_filters:** all constructors initialize the member; in-class member initializer (`int x = 0;`); `std::optional<T>` (default-constructs to empty).
- **verification:**
  1. Locate every constructor (including defaulted).
  2. For each scalar / pointer member confirm init via in-class / member-init list / ctor body before any return.
  3. Locate ≥ 1 read site reached on a path with no prior write.
- **required_evidence:** `class_declaration`, `uninitialized_members`, `unsafe_read`.
- **confidence:** `high` if uninit member read on the very first method call after construction; `medium` if read happens after some methods that may init; `low` if no reachable read found.
- **fix:** in-class member initializers (`int x{};`, `T* p = nullptr;`); `=default` ctors only when all members have in-class init.

---

### `mem-rule-of-three-five`
- **severity:** high
- **what:** Class with custom destructor that releases a resource, but no explicit copy/move (or `=delete`) — copies will double-free.
- **detection_query:**
  ```bash
  rg -n --type cpp '~\w+\s*\(' -g '!third_party/**'
  ```
- **fp_filters:** explicit `=delete` for copy/assign/move; class inherits a project `Noncopyable` mixin.
- **verification:**
  1. From dtor match, find the class declaration.
  2. Check explicit copy ctor, copy assign, move ctor, move assign — at least `=delete` or custom for each.
- **required_evidence:** `class_declaration`, `destructor`, `missing_methods` (list).
- **confidence:** `high` if class is copy-constructed / assigned somewhere in the codebase; `medium` if class is value-typed and could be copied; `low` if class only ever stored via pointer.
- **fix:** Rule of Five (or `=delete` copies); replace raw resource with `std::unique_ptr` to inherit correct defaults.

---

### `mem-buffer-overflow-index`
- **severity:** critical
- **what:** Buffer indexed / `memcpy`'d / `strcpy`'d with a count not bounded ≤ buffer size.
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(memcpy|memmove|memset|strcpy|strcat|sprintf|snprintf|gets)\s*\(' -g '!third_party/**'
  ```
- **fp_filters:** index bounded by immediately preceding `if` / `assert` / for-loop bound; `fp.integer.bounded-by-precondition`.
- **verification:**
  1. For each call confirm destination size ≥ count.
  2. For raw indexing confirm index ≤ buffer size on every path.
  3. For `snprintf` confirm size argument equals or exceeds the buffer size.
- **required_evidence:** `call_or_access_site`, `buffer_size`, `index_or_count_source`.
- **confidence:** `high` if count provably from untrusted input without bound check; `medium` if count is parameter with no documented precondition; `low` if bound is not verified within audited scope.
- **fix:** `std::array` / `std::vector` + `.at()`; `std::span` for size-carrying parameters; `snprintf` over `sprintf`.

---

### `mem-strncpy-no-terminator`
- **severity:** high
- **what:** `strncpy(dst, src, n)` with `n ≤ strlen(src)` does NOT null-terminate; `strlen` / `printf("%s")` over `dst` reads past the buffer.
- **detection_query:**
  ```bash
  rg -n --type cpp '\bstrncpy\s*\(' -g '!third_party/**'
  ```
- **fp_filters:** explicit `dst[N-1] = '\0';` follows; destination zero-initialized AND `n < dst_size`.
- **verification:**
  1. Confirm `n ≤ strlen(src)` is reachable.
  2. Confirm no explicit null-termination after.
- **required_evidence:** `strncpy_site`, `termination_check_or_absence`.
- **confidence:** `high` if unterminated buffer is later read by `strlen` / `printf("%s")`.
- **fix:** `snprintf(dst, dst_size, "%s", src)`; or explicit terminator after `strncpy`.

---

### `ptr-deref-no-check`
- **severity:** critical
- **what:** Pointer dereferenced (`*p` / `p->`) without prior null check, when the pointer can plausibly be null.
- **detection_query:**
  ```bash
  rg -n --type cpp -e '->' -g '!third_party/**'
  ```
- **fp_filters:** `fp.null.proven-non-null`, `fp.dead-code`, `fp.test-code`.
- **verification:**
  1. Find pointer's definition / parameter source.
  2. Walk from entry to deref — any check (`if (p)`, `assert(p)`, `CHECK`, project macro) without rebinding → suppress.
  3. Else examine ≤ 20 callers; if all pass non-null → suppress with `fp.null.proven-non-null`.
- **required_evidence:** `deref_site`, `pointer_origin`, `caller_audit`.
- **confidence:** `high` if at least one caller demonstrably passes / returns nullptr; `medium` if public API with no caller audit; `low` if private helper with all-non-null callers but no enforcement.
- **fix:** explicit null check; change parameter to `T&`; `gsl::not_null<T*>`.

---

### `ptr-this-may-be-null-callback`
- **severity:** critical
- **what:** Async callback captures `[this]` and accesses members; if the owner can be destroyed before the callback fires, member access is UAF.
- **detection_query:**
  ```bash
  rg -n --type cpp '\[\s*(this|=)\s*[,\]]' -g '!third_party/**'
  ```
- **fp_filters:** callback captured via `shared_ptr` of owner; callback unregistered in `~Class()`; class uses `WeakPtrFactory` cancellation.
- **verification:**
  1. Identify what the callback is registered with.
  2. Determine whether registration is unregistered in dtor.
  3. Determine whether the dispatcher outlives `this`.
- **required_evidence:** `callback_site`, `owner_lifetime`, `registration_site`.
- **confidence:** `high` if dispatcher outlives `this` and no unregister; `medium` if dispatcher lifetime unclear; `low` if same-thread synchronous callback.
- **fix:** capture `weak_ptr<Self>` + `lock()`; unregister in dtor; `WeakPtrFactory` / cancellation token.

---

### `ptr-optional-value-no-check`
- **severity:** medium
- **what:** `optional::value()` / `*opt` without prior `has_value()` / `if (opt)` / `value_or`.
- **detection_query:**
  ```bash
  rg -n --type cpp '\.value\(\)' -g '!third_party/**'
  ```
- **fp_filters:** `fp.null.optional-with-value-or`.
- **verification:**
  1. Confirm receiver type is `std::optional` / compatible.
  2. Check for prior `has_value()` / `if (opt)` / `value_or` on same variable.
- **required_evidence:** `value_site`, `optional_declaration`, `prior_check_search`.
- **confidence:** `high` if no prior check on same variable.
- **fix:** `value_or(default)`; `if (opt) { auto v = *opt; }`.

---

### `ptr-iterator-invalidated`
- **severity:** high
- **what:** Iterator / reference acquired before a container-mutating call is reused after.
- **detection_query:**
  ```bash
  rg -n --type cpp '\.(push_back|insert|erase|clear|resize|reserve|emplace_back|emplace)\(' -g '!third_party/**'
  ```
- **fp_filters:** iterator reassigned after mutation; container type does not invalidate on this op (`std::list::push_back`).
- **verification:**
  1. Identify iterator/ref + mutation site.
  2. Confirm container type's invalidation rules (cppreference) match the op.
  3. Confirm subsequent use.
- **required_evidence:** `iterator_acquired`, `mutation_site`, `subsequent_use`.
- **confidence:** `high` if matches a documented invalidating op.
- **fix:** capture index; re-acquire from return value (`it = v.erase(it);`).

---

### `mem-stack-overflow-large-local`
- **severity:** high
- **what:** Large stack-allocated array / struct in a function reachable from a low-stack context (ISR / RTOS task with small `uxStackDepth`); stack overflow → memory corruption.
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(char|uint8_t|int8_t|int)\s+\w+\s*\[\s*\d{3,}\s*\]' -g '!third_party/**'
  ```
- **fp_filters:** function only runs on the main thread / has documented adequate stack; array is `static` / `constexpr` (not on stack); function runs once at boot.
- **verification:**
  1. Compute approximate stack footprint of the function.
  2. Identify all callers + their thread / ISR context.
  3. Cross-reference project task stack sizes (`xTaskCreate uxStackDepth`, FreeRTOS / Zephyr / RT-Thread config); ISR uses MSP on Cortex-M (often small).
  4. If footprint > ~25% of smallest reachable stack → report.
- **required_evidence:** `large_local_site` (with size), `caller_context` (task / ISR), `stack_budget`.
- **confidence:** `high` if footprint > 50% of a known small stack; `medium` if smallest stack unknown; `low` if footprint moderate and only the largest stack reaches the function.
- **fix:** move large locals to `static` storage; pre-allocate at boot; raise `uxStackDepth` and re-measure with `uxTaskGetStackHighWaterMark`.

---

### `mem-dma-buffer-stack-allocated`
- **severity:** critical
- **what:** DMA buffer allocated on stack passed to an async DMA API; when the function returns the buffer is reused while DMA still writes / reads it → memory corruption.
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(HAL_(SPI|UART|I2C|DMA)_\w+|HAL_DMA_Start|LL_DMA_\w+|nrf_drv_\w+|hal_dma_\w+|dma_(start|transfer|begin)\w*)\s*\(' -g '!third_party/**'
  ```
- **fp_filters:** buffer is `static` / global / heap-allocated; function blocks on DMA completion before returning (polling-mode HAL).
- **verification:**
  1. Identify buffer pointer passed to DMA API.
  2. Trace declaration — function-local array → bug.
  3. Confirm DMA API is async (name suffix `_DMA` / `_IT` / `_async` or read docs).
- **required_evidence:** `dma_call_site`, `buffer_declaration` (with storage class), `async_proof`.
- **confidence:** `high` if stack buffer + clearly async DMA call; `medium` if API may block.
- **fix:** `static` / globally-managed buffer; or block until DMA completion (polling variant or completion semaphore).

---

### `mem-dma-buffer-alignment-or-region`
- **severity:** high
- **what:** DMA buffer not aligned to cache line (Cortex-M7 / M55 / A) or not in a DMA-reachable memory region (some MCUs can't DMA into TCM).
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(HAL_(SPI|UART|I2C|DMA)_\w+|HAL_DMA_Start|LL_DMA_\w+|hal_dma_\w+|dma_(start|transfer|begin))\w*\s*\(' -g '!third_party/**'
  ```
- **fp_filters:** buffer declared `__attribute__((aligned(32)))` / placed in DMA SRAM via project macro; target MCU has no D-cache (Cortex-M0/M3/M4).
- **verification:**
  1. Identify MCU + cache presence.
  2. If cache present, buffer must be cache-line aligned AND non-cacheable region OR explicitly cleaned/invalidated around the transfer.
  3. Confirm buffer's region is DMA-reachable (some MCUs can't DMA into core-coupled SRAM / TCM).
- **required_evidence:** `dma_call_site`, `buffer_declaration`, `mcu_or_cache_assumption`.
- **confidence:** `high` if cache present + cacheable RAM + no alignment / no clean-invalidate.
- **fix:** linker-script non-cacheable region; or cache-line align + `SCB_CleanDCache_by_Addr` / `SCB_InvalidateDCache_by_Addr` around transfer.

---

### `ptr-mmio-non-volatile`
- **severity:** critical
- **what:** Pointer or typedef to MMIO peripheral register lacks `volatile`; compiler may cache reads, drop redundant writes, or reorder accesses → silent peripheral misbehaviour.
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(uint32_t|uint16_t|uint8_t)\s*\*\s*\w+\s*=\s*\(' -g '!third_party/**'
  ```
- **fp_filters:** pointer declared `volatile T*` or via vendor CMSIS macros (`__IO`, `__I`, `__O`) which expand to `volatile`.
- **verification:**
  1. Identify pointer expressions targeting a known peripheral address (peripheral base, SCB, NVIC, vendor `*_BASE`).
  2. Confirm `volatile` propagates all the way to the dereference (typedef chains can drop it).
- **required_evidence:** `mmio_pointer_decl`, `target_address`, `missing_volatile`.
- **confidence:** `high` if cast from hardcoded peripheral address with no `volatile`; `medium` if typedef chain might add it.
- **fix:** declare MMIO pointers `volatile`; prefer vendor CMSIS register definitions.
