# progress.md (eval fixture: completion-stale-evidence)

- Work Item Type: AR
- Work Item ID: AR12345
- Owning Component: example-component
- Workflow Profile: standard
- Execution Mode: interactive
- Current Stage: devflow-code-review
- Current Active Task: T-001
- Pending Reviews And Gates: completion-gate
- Next Action Or Recommended Skill: devflow-completion-gate
- Blockers:
- Last Updated: 2026-05-09T00:00:00Z

## Evidence freshness state (synthetic)

- foo_handler.c last modified: 2026-05-09T05:30:00Z
- evidence/unit/T-001-green.log produced: 2026-05-09T03:15:00Z (BEFORE source change)
- evidence/build/T-001-build.log produced: 2026-05-09T03:15:00Z (BEFORE source change)

## Notes

All upstream review records are 通过. The verify-command evidence pre-dates the most recent source change to `foo_handler.c`. The gate MUST detect the timestamp gap and require a fresh re-run.
