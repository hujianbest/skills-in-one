# 逻辑与数值专项 (logic-and-numeric)

> Specialty file for the C/C++ embedded **integer / arithmetic / portability** audit. Load when audit scope is integer overflow / signedness / shift / division / container access / endianness / bit-field / packed-struct portability.

Per-template slim format: see `references/templates.md`.

## 索引

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

---

### `int-add-overflow`
- **severity:** high
- **what:** Signed integer addition without overflow check; UB on overflow per C/C++ standard.
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(int|long|int32_t|int64_t|ssize_t)\s+\w+\s*=\s*\w+\s*\+\s*\w+' -g '!third_party/**'
  ```
- **fp_filters:** `fp.integer.bounded-by-precondition`, `fp.signed-unsigned.deliberate-modular`.
- **verification:**
  1. Determine domain of each operand.
  2. If `max(a) + max(b)` exceeds the type → report.
- **required_evidence:** `expression_site`, `operand_domains`, `overflow_path`.
- **confidence:** `high` if domain demonstrably reaches overflow; `medium` if domain unbounded.
- **fix:** `__builtin_add_overflow`; wider intermediate type with clamp.

---

### `int-sub-underflow`
- **severity:** high
- **what:** Subtraction underflow; for `size_t` / unsigned this wraps to a huge value (`if (avail - needed >= 0)` is always true).
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(int|long|size_t|uint32_t|uint64_t)\s+\w+\s*=\s*\w+\s*-\s*\w+' -g '!third_party/**'
  ```
- **fp_filters:** `fp.integer.bounded-by-precondition`.
- **verification:**
  1. Determine domain — for unsigned types, any case where `b > a` wraps.
  2. Look for the `avail - needed >= 0` anti-pattern in particular.
- **required_evidence:** `expression_site`, `operand_domains`, `underflow_path`.
- **confidence:** `high` for unsigned subtraction without prior `>=` guard.
- **fix:** `__builtin_sub_overflow`; restructure as `if (avail >= needed) { ... = avail - needed; }`.

---

### `int-mul-overflow-alloc-size`
- **severity:** critical
- **what:** Multiplication used as allocation size without overflow check; `count * sizeof(T)` wraps to small value, allocation succeeds, subsequent indexing OOB.
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(new\s+\w[\w:]*\s*\[[^\]]*\*|malloc\s*\([^)]*\*|calloc\s*\()' -g '!third_party/**'
  ```
- **fp_filters:** `fp.integer.allocator-already-checks`.
- **verification:**
  1. Trace `count` to its origin.
  2. Confirm `count <= SIZE_MAX / sizeof(T)`.
- **required_evidence:** `alloc_site`, `count_origin`, `bound_check_or_absence`.
- **confidence:** `high` if `count` is from untrusted input.
- **fix:** check `count > SIZE_MAX / sizeof(T)` before allocation; prefer `std::vector<T>(count)`.

---

### `int-shift-out-of-range`
- **severity:** medium
- **what:** Shift amount ≥ type width is UB; left-shifting a signed value into the sign bit is also UB.
- **detection_query:**
  ```bash
  rg -n --type cpp '<<|>>' -g '!third_party/**'
  ```
- **fp_filters:** stream operators (`std::cout << x`); shift amount is a literal `< type width`.
- **verification:**
  1. Confirm operand types and the variable shift amount's domain.
  2. Report if amount can equal or exceed the type width.
  3. For signed: also flag shifts into the sign bit.
- **required_evidence:** `shift_site`, `type_width`, `amount_domain`.
- **confidence:** `high` if amount is unvalidated user input.
- **fix:** validate amount; mask with `(amount & (width - 1))` if intentional rotation; use unsigned types for bit manipulation.

---

### `int-signed-unsigned-mix`
- **severity:** medium
- **what:** Comparison or arithmetic between signed and unsigned types; implicit conversion can change semantics (`for (int i = 0; i < v.size(); ...)` — `i` becomes huge if `size()` is small).
- **detection_query:**
  ```bash
  rg -n --type cpp 'for\s*\(\s*int\s+\w+\s*=\s*0\s*;\s*\w+\s*<\s*\w+\.size\(\)' -g '!third_party/**'
  ```
- **fp_filters:** `fp.signed-unsigned.deliberate-modular`.
- **verification:**
  1. Identify the signed and unsigned operands.
  2. Confirm implicit conversion can change semantics.
- **required_evidence:** `expression_site`, `operand_types`, `breaking_value_example`.
- **confidence:** `high` if breaking value is reachable.
- **fix:** match types (`size_t i = 0; i < v.size()`); explicit `static_cast` with bounds check.

---

### `int-narrowing-cast`
- **severity:** low
- **what:** `static_cast<T>` to a narrower type without bounds check; silently truncates.
- **detection_query:**
  ```bash
  rg -n --type cpp 'static_cast\s*<\s*(int|short|char|int8_t|int16_t|int32_t|uint8_t|uint16_t|uint32_t)\s*>' -g '!third_party/**'
  ```
- **fp_filters:** source value is bounded.
- **verification:** confirm source domain fits target type.
- **required_evidence:** `cast_site`, `source_domain`, `target_range`.
- **confidence:** `medium` if domain unbounded.
- **fix:** add bounds check; `gsl::narrow` (throws on loss).

---

### `div-by-zero`
- **severity:** high
- **what:** Division or modulus where the divisor is a variable that can reach zero on some path.
- **detection_query:**
  ```bash
  rg -n --type cpp '[/%]\s*\w' -g '!third_party/**'
  ```
- **fp_filters:** `fp.divbyzero.unreachable`.
- **verification:**
  1. Confirm divisor is a variable (not literal).
  2. Confirm divisor can be zero on some reachable path.
- **required_evidence:** `divide_site`, `divisor_origin`, `zero_path`.
- **confidence:** `high` if zero path demonstrably reachable.
- **fix:** explicit zero check; documented precondition.

---

### `empty-container-front-back`
- **severity:** high
- **what:** `front()` / `back()` / `top()` on a container that may be empty → UB.
- **detection_query:**
  ```bash
  rg -n --type cpp '\.(front|back|top)\s*\(\s*\)' -g '!third_party/**'
  ```
- **fp_filters:** `fp.empty-container.checked`.
- **verification:** confirm preceding `if (!c.empty())` / equivalent.
- **required_evidence:** `access_site`, `prior_check_search`, `container_origin`.
- **confidence:** `high` if no prior empty check.
- **fix:** guard with empty check; use `c.at(0)` (throws) for vector.

---

### `int-implicit-promotion-narrow-mcu`
- **severity:** high
- **what:** On 16-bit `int` targets (AVR / MSP430 / PIC18), `uint16_t a, b; uint32_t c = a * b;` computes in 16-bit `int` and overflows BEFORE assignment.
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(uint8_t|int8_t|uint16_t|int16_t)\s+\w+\s*=\s*\w+\s*[\+\-\*]\s*\w+' -g '!third_party/**'
  ```
- **fp_filters:** target arch has 32-bit `int` (most ARM Cortex-M / RISC-V); operand domains demonstrably cannot reach the boundary.
- **verification:**
  1. Identify target MCU + `int` width.
  2. For 16-bit `int` targets, both narrow→wide assignment AND wide computation in narrow `int` are concerns.
- **required_evidence:** `expression_site`, `target_int_width`, `operand_domains`, `overflow_or_truncation_path`.
- **confidence:** `high` if target is 16-bit `int` and operands can reach boundary.
- **fix:** cast at least one operand to target type before multiplying; use `uint32_t` everywhere if values can grow > 16 bits.

---

### `int-bitfield-portability`
- **severity:** medium
- **what:** Bit-field layout within a storage unit is implementation-defined; serialising bit-field structs over wire / flash / hardware breaks across compilers (GCC vs IAR vs Keil) and endianness.
- **detection_query:**
  ```bash
  rg -nU --type cpp 'struct\s+\w+\s*\{[^}]*\b\w+\s*:\s*\d+\s*;' -g '!third_party/**'
  ```
- **fp_filters:** bit-fields used purely for in-memory savings (never serialised); explicitly tested `__attribute__((packed))` matches wire format on the target compiler.
- **verification:**
  1. Identify struct types with bit-fields.
  2. Determine whether instances are written to flash / sent over UART/SPI/CAN / mapped over MMIO.
- **required_evidence:** `struct_decl`, `serialization_site`, `assumption_about_layout`.
- **confidence:** `high` if the struct is sent over wire as-is.
- **fix:** build wire frames byte-by-byte with explicit shift / mask, not bit-fields; or copy field-by-field into a serialisation buffer.

---

### `int-packed-struct-misaligned-access`
- **severity:** high
- **what:** Taking the address of a member of a `__attribute__((packed))` struct; the resulting unaligned load/store can fault on Cortex-M0/M0+ and is slow on newer M-profiles.
- **detection_query:**
  ```bash
  rg -n --type cpp '__attribute__\(\(\s*packed\s*\)\)|#\s*pragma\s+pack' -g '!third_party/**'
  ```
- **fp_filters:** target arch supports unaligned access (Cortex-M3+ generally do, with caveats); code only assigns/reads fields by value (compiler emits byte-wise).
- **verification:**
  1. Find packed struct definitions.
  2. Search for `&pkt->field` / `memcpy(dst, &pkt->field, n)` / passing the field by reference / pointer.
- **required_evidence:** `packed_struct_decl`, `member_address_site`, `target_arch`.
- **confidence:** `high` if Cortex-M0 target + member-address taken.
- **fix:** read packed fields by value (compiler emits safe byte-wise access); `memcpy` into an aligned local before reading.

---

### `int-endianness-no-conversion`
- **severity:** high
- **what:** Multi-byte integer copied to/from a byte buffer crossing an endianness boundary (network, file, cross-MCU bus) without explicit `htonl` / `cpu_to_le32`.
- **detection_query:**
  ```bash
  rg -n --type cpp '\b(memcpy|memmove)\s*\([^,]+,\s*&\w+\s*,\s*sizeof' -g '!third_party/**'
  ```
- **fp_filters:** both endpoints same arch (single-MCU, never moves data off-chip); explicit `htonl` / `__builtin_bswap32` / `cpu_to_le32`.
- **verification:**
  1. Identify call sites copying multi-byte integers across an endianness boundary.
  2. Confirm explicit byte-order handling.
- **required_evidence:** `serialization_site`, `wire_endianness`, `host_endianness`.
- **confidence:** `high` if wire spec is one endianness and host is the other.
- **fix:** `htonl` / `htons`; vendor `cpu_to_le32` / `cpu_to_be32`; explicit byte shifts (`buf[0] = v >> 24;` …).

---

### `int-char-signedness`
- **severity:** medium
- **what:** Code assumes `char` is signed (or unsigned); ARM `gcc` defaults to unsigned, x86 `gcc` to signed; `getchar()` returning -1 EOF can be conflated with 0xFF.
- **detection_query:**
  ```bash
  rg -n --type cpp '\bchar\s+\w+\s*=' -g '!third_party/**'
  ```
- **fp_filters:** code uses `signed char` / `unsigned char` explicitly; uses `int8_t` / `uint8_t` from `<stdint.h>`.
- **verification:**
  1. Look for `char` compared to `< 0` or storing > 127 into `char` then reading back.
  2. `getchar()` / `read()` results stored in `char` before EOF check.
- **required_evidence:** `char_use_site`, `signedness_assumption`, `target_default`.
- **confidence:** `high` if code compares `char` to `< 0` and target's `char` is unsigned.
- **fix:** `int8_t` / `uint8_t` from `<stdint.h>`; explicit `signed char` / `unsigned char`; store `getchar` result in `int` first.
