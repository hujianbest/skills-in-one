# ar-design-draft.md (eval fixture)

## 1. Identity

- AR ID: AR54321
- Owning Component: example-component
- Profile: standard

## 2. Code-Level Design

- New module `foo_handler` with API `foo_handle(ctx, payload)`.
- Data flow: payload validated → state transition → emit event.
- Error paths: invalid payload → return `ERR_INVALID_PAYLOAD`; resource exhaustion → return `ERR_NO_RESOURCE`.

## 3. Defensive C/C++ Notes

- Memory: payload is borrowed; ownership stays with caller.
- Concurrency: `foo_handle` is callable only from the main task context.
- Error handling: all error codes propagate via return value; no silent failure.

## 4. Design Options Checkpoint

Single obvious option (incremental change to existing handler chain). Rationale: no alternative pattern matches the existing event flow.

## 5. Traceability

- FR-001 → §2 happy path
- FR-002 → §2 error path

---

NOTE: The "Test Design" section is **deliberately missing**. This is the misuse the eval is verifying.
