# progress.md (shared template for test-review eval fixtures)

Each fixture under `fixtures/<scenario.id>/` reuses this template's field shape:

- Work Item Type: AR
- Work Item ID: AR12345
- Owning Component: example-component
- Workflow Profile: standard
- Execution Mode: interactive
- Current Stage: devflow-tdd-implementation
- Current Active Task: T-001
- Task Plan Path: features/AR12345-eval/tasks.md
- Task Board Path: features/AR12345-eval/task-board.md
- Pending Reviews And Gates: test-check, code-review, completion-gate
- Next Action Or Recommended Skill: devflow-test-review
- Blockers:
- Last Updated: 2026-05-09T00:00:00Z

The per-scenario fixture's own `progress.md` may override `Current Active Task`, `Workflow Profile`, etc.; the rest are stable across all test-review eval scenarios.
