# 逻辑与数值专项 (logic-and-numeric)

> Specialty file for the C/C++ embedded **integer / arithmetic / portability** audit. Load this when the audit scope is integer overflow / signedness / shift / division / container access / endianness / bit-field / packed-struct portability. Per-template contract field definitions live in `references/templates.md` (the index).

This file holds the historical `int-*`, `div-by-zero`, and `empty-container-*` templates plus five embedded-flavoured additions covering 16-bit MCU promotion, bit-field portability, packed-struct misaligned access, endianness, and `char` signedness.

## 索引

| ID | 名称 | 严重 | 适用 |
|---|---|---|---|
| `int-add-overflow` | 有符号加法溢出未做检查 | high | C / C++ |
| `int-sub-underflow` | 减法/无符号下溢未做检查 | high | C / C++ |
| `int-mul-overflow-alloc-size` | 用作分配大小的乘法可能溢出 | critical | C / C++ |
| `int-shift-out-of-range` | 移位量 ≥ 类型宽度 | medium | C / C++ |
| `int-signed-unsigned-mix` | 有符号与无符号混合比较/运算 | medium | C / C++ |
| `int-narrowing-cast` | 窄化转换未做边界检查 | low | C / C++ |
| `div-by-zero` | 除/模未做零检查 | high | C / C++ |
| `empty-container-front-back` | 容器空时调 `front()`/`back()`/`top()` | high | C++ |
| `int-implicit-promotion-narrow-mcu` | 16-bit MCU 上 int 提升导致溢出/截断 | high | C / C++ embedded |
| `int-bitfield-portability` | 位域布局是 implementation-defined, 不可直接序列化 | medium | C / C++ embedded |
| `int-packed-struct-misaligned-access` | 在对齐严格的 ARM 上取 packed struct 字段地址 | high | C / C++ embedded |
| `int-endianness-no-conversion` | 序列化整数到字节流时未做字节序转换 | high | C / C++ embedded |
| `int-char-signedness` | 假定 `char` 有/无符号; 不同平台/编译器不一致 | medium | C / C++ embedded |

---

## Logic / integer

### `int-add-overflow`
- **name:** Signed integer addition without overflow check
- **category:** logic
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(int|long|int32_t|int64_t|ssize_t)\s+\w+\s*=\s*\w+\s*\+\s*\w+' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - `fp.integer.bounded-by-precondition`
  - `fp.signed-unsigned.deliberate-modular`
- **verification:**
  1. Determine the domain of each operand.
  2. If `max(a)+max(b)` exceeds the type, report.
- **required_evidence:**
  - `expression_site`, `operand_domains`, `overflow_path`.
- **fix_suggestions:**
  - `__builtin_add_overflow(a, b, &r)`.
  - Use wider intermediate type and clamp.

---

### `int-sub-underflow`
- **name:** Subtraction underflow (especially `size_t` / unsigned)
- **category:** logic
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(int|long|size_t|uint32_t|uint64_t)\s+\w+\s*=\s*\w+\s*-\s*\w+' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - `fp.integer.bounded-by-precondition`
- **verification:**
  1. Determine the domain. For `size_t` / unsigned types, any case where the right operand can exceed the left wraps to a huge value.
  2. The classic embedded bug: `if (avail - needed >= 0)` always true if `avail` is `size_t`.
- **required_evidence:**
  - `expression_site`, `operand_domains`, `underflow_path`.
- **fix_suggestions:**
  - `__builtin_sub_overflow(a, b, &r)`.
  - Re-write as `if (avail >= needed) { … = avail - needed; }`.

---

### `int-mul-overflow-alloc-size`
- **name:** Multiplication used as allocation size without overflow check
- **category:** logic
- **severity:** critical
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(new\s+\w[\w:]*\s*\[[^\]]*\*|malloc\s*\([^)]*\*|calloc\s*\()' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - `fp.integer.allocator-already-checks`
- **verification:**
  1. Trace `count` to its origin.
  2. Confirm `count * sizeof(T)` cannot wrap (`count <= SIZE_MAX / sizeof(T)`).
- **required_evidence:**
  - `alloc_site`, `count_origin`, `bound_check_or_absence`.
- **fix_suggestions:**
  - Add `if (count > SIZE_MAX / sizeof(T)) throw std::bad_alloc();` before allocation.
  - Prefer `std::vector<T>(count)`.

---

### `int-shift-out-of-range`
- **name:** Shift amount ≥ type width
- **category:** logic
- **severity:** medium
- **detection_query:**
  ```bash
  rg -n --type cpp '<<|>>' -g '!third_party/**'
  ```
  (Noisy — narrow with `rg '<<\s*[A-Za-z_]\w*'`.)
- **false_positive_filters:**
  - Stream operators (`std::cout << x`).
  - Shift amount is a literal `< type width`.
- **verification:**
  1. Confirm the operand types and the variable shift amount's domain.
  2. Report if the amount can equal or exceed the type width.
  3. On embedded: also check that left-shifting a signed type into the sign bit is avoided (UB in C/C++).
- **required_evidence:**
  - `shift_site`, `type_width`, `amount_domain`.
- **fix_suggestions:**
  - Validate amount before shifting; mask with `(amount & (width-1))` if intentional rotation.
  - Use unsigned types for bit manipulation.

---

### `int-signed-unsigned-mix`
- **name:** Comparison or arithmetic between signed and unsigned types
- **category:** logic
- **severity:** medium
- **detection_query:**
  ```bash
  rg -n --type cpp 'for\s*\(\s*int\s+\w+\s*=\s*0\s*;\s*\w+\s*<\s*\w+\.size\(\)' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - `fp.signed-unsigned.deliberate-modular`
- **verification:**
  1. Identify the signed and unsigned operands.
  2. Confirm comparison or arithmetic happens with implicit conversion that can change semantics.
- **required_evidence:**
  - `expression_site`, `operand_types`, `breaking_value_example`.
- **fix_suggestions:**
  - Match types (`size_t i = 0; i < v.size()`).
  - Use `static_cast<T>(...)` with explicit bounds check.

---

### `int-narrowing-cast`
- **name:** Narrowing conversion without bounds check
- **category:** logic
- **severity:** low
- **detection_query:**
  ```bash
  rg -n --type cpp 'static_cast\s*<\s*(int|short|char|int8_t|int16_t|int32_t|uint8_t|uint16_t|uint32_t)\s*>' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - Source value is bounded.
- **verification:** confirm source domain fits target type.
- **required_evidence:** `cast_site`, `source_domain`, `target_range`.
- **fix_suggestions:** add bounds check; use `gsl::narrow` (throws on loss).

---

### `div-by-zero`
- **name:** Division or modulus without zero check
- **category:** logic
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '[/%]\s*\w' -g '!third_party/**'
  ```
  Pass 3 must determine that the divisor is a variable (not a literal) and could be zero.
- **false_positive_filters:** `fp.divbyzero.unreachable`
- **verification:** confirm divisor can be zero on some reachable path.
- **required_evidence:** `divide_site`, `divisor_origin`, `zero_path`.
- **fix_suggestions:** explicit zero check; pre-condition documented.

---

### `empty-container-front-back`
- **name:** `front()` / `back()` / `top()` on container without empty check
- **category:** logic
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '\.(front|back|top)\s*\(\s*\)' -g '!third_party/**'
  ```
- **false_positive_filters:** `fp.empty-container.checked`
- **verification:** confirm preceding `if (!c.empty())` / equivalent.
- **required_evidence:** `access_site`, `prior_check_search`, `container_origin`.
- **fix_suggestions:** guard with empty check; or use `c.at(0)` (throws) for vector.

---

## Embedded portability / numeric

### `int-implicit-promotion-narrow-mcu`
- **name:** Implicit promotion to `int` causes overflow on a 16-bit MCU
- **category:** logic
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(uint8_t|int8_t|uint16_t|int16_t)\s+\w+\s*=\s*\w+\s*[\+\-\*]\s*\w+' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - The target architecture has 32-bit `int` (most ARM Cortex-M / RISC-V); operands ≤ 16-bit cannot overflow `int`.
  - Operand domains demonstrably cannot reach the boundary.
- **verification:**
  1. Identify the target MCU. AVR (ATmega/ATtiny) and MSP430 have 16-bit `int`. PIC18 typically 16-bit. Cortex-M / ESP32 / RISC-V use 32-bit `int`.
  2. For 16-bit `int` targets, `uint8_t a, b; uint16_t c = a + b;` does the addition in 16-bit `int` and is safe; but `uint16_t a, b; uint16_t c = a * b;` may overflow in 16-bit `int` before being assigned.
  3. Note the dual concern: assigning a wider expression to a narrow type (truncation), AND computing a wider expression in a possibly-narrow `int` (overflow before assignment).
- **required_evidence:**
  - `expression_site`, `target_int_width`, `operand_domains`, `overflow_or_truncation_path`.
- **bad_example (16-bit `int` target):**
  ```c
  uint16_t a = 30000, b = 30000;
  uint32_t product = a * b;     // computes in 16-bit int → overflow → garbage
  ```
- **good_example:**
  ```c
  uint16_t a = 30000, b = 30000;
  uint32_t product = (uint32_t)a * b;   // promote one operand explicitly
  ```
- **fix_suggestions:**
  - Cast at least one operand to the target type before multiplying.
  - Use `uint32_t` everywhere if the values can grow beyond 16 bits.

---

### `int-bitfield-portability`
- **name:** Bit-field used in a way that depends on layout (serialization / wire format)
- **category:** logic
- **severity:** medium
- **detection_query:**
  ```bash
  rg -nU --type cpp 'struct\s+\w+\s*\{[^}]*\b\w+\s*:\s*\d+\s*;' -g '!third_party/**'
  ```
  Find struct types containing bit-fields. Pass 3 narrows to whether their byte layout is exposed to wire / flash / hardware.
- **false_positive_filters:**
  - Bit-fields used purely for memory savings inside the program (never serialised).
  - Bit-fields explicitly aligned by `__attribute__((packed))` AND tested to match the wire format on the target compiler.
- **verification:**
  1. Identify struct types with bit-fields.
  2. Determine whether instances are written to flash / sent over UART/SPI/CAN / mapped over MMIO.
  3. C/C++ standards leave the **order** of bit-field allocation within a storage unit implementation-defined. Code that relies on a specific order is non-portable across compilers (GCC vs IAR vs Keil) and across endianness.
- **required_evidence:**
  - `struct_decl`, `serialization_site`, `assumption_about_layout`.
- **bad_example:**
  ```c
  struct CanFrame {
      uint16_t id : 11;
      uint16_t rtr : 1;
      uint16_t dlc : 4;
  };
  send_can(&frame, sizeof frame);   // wire format depends on compiler
  ```
- **fix_suggestions:**
  - Build wire frames byte-by-byte with explicit shift / mask, not bit-fields.
  - If you must keep bit-fields for ergonomics, copy field-by-field into a serialisation buffer.

---

### `int-packed-struct-misaligned-access`
- **name:** Taking address of a member in a `__attribute__((packed))` struct on alignment-strict ARM
- **category:** logic
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '__attribute__\(\(\s*packed\s*\)\)|#\s*pragma\s+pack' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - Target architecture supports unaligned access in hardware (Cortex-M3 and up generally do, with caveats for `STRD`/`LDRD`; older M0 does not).
  - Code only assigns/reads fields by value (compiler emits byte-wise access).
- **verification:**
  1. Find `packed` struct definitions.
  2. Search for code that takes the address of a member: `&pkt->field`, `memcpy(dst, &pkt->field, n)`, passing the field by reference / pointer.
  3. On Cortex-M0/M0+ and on Cortex-A under certain conditions, the resulting unaligned load/store traps; on newer M-profiles it may work but be slow.
- **required_evidence:**
  - `packed_struct_decl`, `member_address_site`, `target_arch`.
- **bad_example:**
  ```c
  struct __attribute__((packed)) Hdr { uint8_t a; uint32_t b; };
  void f(struct Hdr *h, uint32_t *out) {
      *out = *(&h->b);   // unaligned 32-bit load on Cortex-M0 → fault
  }
  ```
- **fix_suggestions:**
  - Read packed fields by value (compiler emits safe byte-wise access).
  - Or `memcpy` into an aligned local before reading.

---

### `int-endianness-no-conversion`
- **name:** Serializing / deserializing integers to bytes without endianness conversion
- **category:** logic
- **severity:** high
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(memcpy|memmove)\s*\([^,]+,\s*&\w+\s*,\s*sizeof' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - Both endpoints are the same architecture (single-MCU project, never moves data off-chip).
  - The code uses explicit conversion (`htonl`, `__builtin_bswap32`, `cpu_to_le32`, etc.).
- **verification:**
  1. Identify call sites that copy a multi-byte integer to/from a byte buffer that crosses an endianness boundary (network, file, cross-MCU bus).
  2. Confirm explicit byte-order handling.
  3. Without it, the same firmware running on big- vs little-endian sides will mis-interpret the value.
- **required_evidence:**
  - `serialization_site`, `wire_endianness`, `host_endianness`.
- **fix_suggestions:**
  - Use `htonl`/`htons` (network = big endian) or vendor `cpu_to_le32` / `cpu_to_be32`.
  - Build wire bytes with explicit shifts: `buf[0] = v >> 24; buf[1] = v >> 16; …`.

---

### `int-char-signedness`
- **name:** Code assumes `char` is signed (or unsigned) — undefined per platform
- **category:** logic
- **severity:** medium
- **detection_query:**
  ```bash
  rg -n --type cpp '\bchar\s+\w+\s*=' -g '!third_party/**'
  ```
- **false_positive_filters:**
  - Code uses `signed char` / `unsigned char` explicitly.
  - Code uses `int8_t` / `uint8_t` from `<stdint.h>`.
- **verification:**
  1. C standard leaves `char` signedness implementation-defined. ARM `gcc` defaults to **unsigned**; x86 `gcc` defaults to **signed**; some toolchains expose a flag (`-fsigned-char` / `-funsigned-char`).
  2. Look for code that compares `char` to `< 0` or stores a value > 127 into a `char` and reads it back; both are signedness-dependent.
  3. Especially watch for return values of `getchar()` / `read()`-style APIs where -1 (EOF) is conflated with 0xFF.
- **required_evidence:**
  - `char_use_site`, `signedness_assumption`, `target_default`.
- **fix_suggestions:**
  - Use `int8_t` / `uint8_t` from `<stdint.h>` for byte values.
  - Use `signed char` / `unsigned char` explicitly when signedness matters.
  - For `getchar`-style APIs, store the result in `int` first and only cast to `char` after the EOF check.
