# Bug-Pattern Templates — Specialty Index

> This file is a **thin index** of the C/C++ embedded specialty templates. The actual per-template detection contracts live in `references/templates/<specialty>.md`. **Load only the specialty file(s) relevant to the current audit scope** — do NOT load all of them blindly. The intent is that one audit costs ~16 KB of specialty content (this index + 1 specialty file), not the ~50 KB of loading the full catalogue.

## How to choose a specialty

```
What is the audit scope?
├── 内存/堆/栈/缓冲区/指针/DMA buffer 问题   ⇒ load templates/memory-safety.md
├── 并发 / ISR / RTOS 同步 / 锁顺序 / 内存序  ⇒ load templates/concurrency-and-isr.md
├── 资源/外设生命周期 (mutex/fd/外设时钟/RTOS 任务/HW 定时器)
│                                            ⇒ load templates/resource-management.md
├── 整数/逻辑/可移植性 (溢出/截断/位域/字节序/packed struct)
│                                            ⇒ load templates/logic-and-numeric.md
├── 纯硬件域 (看门狗/低功耗模式/MMIO RMW/Flash 写时执行)
│                                            ⇒ load templates/embedded-hardware.md
└── 综合代码评审 / 没有明确范围                ⇒ load all 5 specialty files (rare)
```

If unsure, ask the user to narrow scope first. A 50 KB context dump is the failure mode this index is here to prevent.

## Per-template-contract format

Every template across every specialty file uses the same structured contract. Roles of each field:

- `detection_query` — a `rg` (ripgrep) invocation used in Pass 2 only. It is a **prior / ranking signal**, not a finding gate. The query intentionally over-matches; the LLM decides whether there is a bug by reading the code.
- `false_positive_filters` — filters from `references/false-positive-filters.md` that the LLM must explicitly rule out before promoting a finding.
- `verification` — the procedural checklist the LLM executes on each unit where the template might apply.
- `required_evidence` — the exact pieces of code / data flow that must be cited in the report. **A finding is invalid if any item is missing.**
- `confidence_rubric` — how to rate `high` / `medium` / `low` for this template.
- `bad_example` / `good_example` — calibration examples.
- `fix_suggestions` — recommended fixes.

Reminder of the philosophy: **trade tokens for code quality**. Pattern matching tells you *where to look first*; the LLM decides *whether there is a bug* by actually reading and understanding the code.

## Specialty index

### `templates/memory-safety.md` — 内存安全专项 (16 templates)

Heap / stack / object lifetime / buffer / pointer + embedded-flavoured: stack-overflow on a small-stack RTOS task, DMA-buffer alignment / lifetime, MMIO-pointer must-be-volatile.

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

### `templates/concurrency-and-isr.md` — 并发与中断专项 (14 templates)

Multi-thread races / lock ordering / memory ordering + embedded-flavoured: ISR-shared variables, ISR-API misuse, MMIO RMW races, RTOS priority inversion.

| ID | severity |
|---|---|
| `con-unsynchronized-shared-write` | critical |
| `con-lock-ordering-deadlock` | critical |
| `con-double-checked-locking` | critical |
| `con-sleep-or-blocking-with-lock-held` | high |
| `con-callback-invoked-with-lock-held` | high |
| `con-missing-memory-order` | high |
| `con-tocttou` | high |
| `con-condvar-no-predicate` | high |
| `isr-shared-non-atomic` | critical |
| `isr-non-volatile-shared` | critical |
| `isr-blocking-rtos-call` | critical |
| `isr-malloc-or-printf` | critical |
| `isr-rmw-mmio-no-exclusive` | high |
| `rtos-priority-inversion-no-protocol` | high |

### `templates/resource-management.md` — 资源与外设管理专项 (8 templates)

RAII / handle / fd lifecycle + embedded-flavoured: peripheral clock pairing, RTOS task lifecycle, HW timer / DMA channel, NVIC IRQ deinit.

| ID | severity |
|---|---|
| `res-file-no-close` | high |
| `res-mutex-no-unlock` | high |
| `res-fd-leak-on-error` | high |
| `res-raii-broken-by-release` | medium |
| `res-peripheral-clock-not-disabled` | high |
| `res-rtos-task-not-deleted` | medium |
| `res-timer-or-dma-not-stopped` | high |
| `res-irq-not-disabled-on-deinit` | high |

### `templates/logic-and-numeric.md` — 逻辑与数值专项 (13 templates)

Integer overflow / signedness / shift / division / container-empty + embedded-flavoured: 16-bit MCU promotion, bit-field portability, packed struct misaligned access, endianness, char signedness.

| ID | severity |
|---|---|
| `int-add-overflow` | high |
| `int-sub-underflow` | high |
| `int-mul-overflow-alloc-size` | critical |
| `int-shift-out-of-range` | medium |
| `int-signed-unsigned-mix` | medium |
| `int-narrowing-cast` | low |
| `div-by-zero` | high |
| `empty-container-front-back` | high |
| `int-implicit-promotion-narrow-mcu` | high |
| `int-bitfield-portability` | medium |
| `int-packed-struct-misaligned-access` | high |
| `int-endianness-no-conversion` | high |
| `int-char-signedness` | medium |

### `templates/embedded-hardware.md` — 嵌入式硬件专项 (6 templates)

Pure hardware-domain checks: watchdog timing, low-power mode pairing, MMIO bit-field RMW, in-flash code-execution conflicts, long IRQ-disable critical sections, fixed-stack recursion.

| ID | severity |
|---|---|
| `emb-watchdog-not-fed-long-loop` | high |
| `emb-power-mode-enter-no-exit` | high |
| `emb-bitfield-write-volatile-rmw` | high |
| `emb-flash-write-blocks-execution` | high |
| `emb-irq-disabled-too-long` | high |
| `emb-recursion-in-task-fixed-stack` | high |

## Operating with specialty files

- `scripts/scan_candidates.py` accepts `--specialty NAME` (loads `references/templates/NAME.md`) or `--templates-dir DIR` (default: `references/templates/`, loads every `.md` under it).
- The `template_id` strings are stable across the split: existing `coverage.json` entries from before the split still merge.
- Template ids are prefixed by the original category convention (`mem-*`, `ptr-*`, `res-*`, `con-*`, `int-*`) plus three new embedded prefixes (`isr-*`, `rtos-*`, `emb-*`).

## Adding a new template

1. Decide which specialty file it belongs in (or whether it warrants a new specialty file).
2. Pick a stable `id` (kebab-case, prefix by category — `mem-*`, `ptr-*`, `res-*`, `con-*`, `int-*`, `isr-*`, `rtos-*`, `emb-*`).
3. Write the **detection_query** as a runnable `rg` invocation. Test it on the target repo before committing.
4. Write at least 2 `false_positive_filters` (template-specific or by reference to `references/false-positive-filters.md`).
5. Write the `verification` checklist with concrete steps. No "use judgement" — be specific.
6. Define `required_evidence` (≥ 3 items) and the `confidence_rubric`.
7. Provide `bad_example` (small, real-looking) and ideally a `good_example`.
8. Add the template id to the corresponding specialty's index table AND to this file's specialty index.
9. Run `scripts/scan_candidates.py --specialty <specialty> --template <id>` against a known-buggy repo to validate the query.
