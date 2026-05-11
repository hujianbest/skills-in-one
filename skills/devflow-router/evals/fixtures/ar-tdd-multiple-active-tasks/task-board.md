# task-board.md (eval fixture)

| Task | Status | Notes |
|---|---|---|
| T-001 | done | initial slice |
| T-002 | in_progress | started by implementer A |
| T-003 | ready | |
| T-004 | ready | |
| T-005 | in_progress | started by implementer B (concurrent — invalid state) |

NOTE: Two `in_progress` tasks is an invalid state. The router MUST NOT silently pick one to dispatch.
