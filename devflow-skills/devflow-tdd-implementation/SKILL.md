---
name: devflow-tdd-implementation
description: Use when devflow-ar-design-review has passed and the approved AR design must be mapped into a task queue and implemented via C/C++ TDD, when continuing the Current Active Task, when fixing implementation after devflow-test-checker or devflow-code-review requested changes, or when devflow-problem-fix has handed off a confirmed reproducer and fix boundary. Not for writing AR design, changing component design, test effectiveness review, code review, or route recovery.
---

# DevFlow TDD Implementation

This skill turns an approved AR design into a task queue, locks one Current Active Task, dispatches a focused implementer subagent when implementation context would be large, and records fresh evidence. Task planning is now an internal preflight of this skill, not a standalone workflow node.

This skill does not write AR design, change AR scope, review its own tests, or review its own code. Those responsibilities remain with `devflow-ar-design`, `devflow-test-checker`, and `devflow-code-review`.

## When To Use

Use when:

- `devflow-ar-design-review` has passed and the implementation needs task queue setup plus TDD execution.
- `tasks.md` / `task-board.md` already exist and the work item needs to continue the Current Active Task.
- `devflow-test-checker` or `devflow-code-review` returned `needs changes` for implementation work.
- `devflow-problem-fix` has handed off a reproducer, root cause, and safe fix boundary.

Do not use when:

- AR design is missing, not reviewed, or lacks test design: use `devflow-ar-design`.
- The change affects component boundary, SOA interface, dependency, or state machine: use `devflow-router` / `devflow-component-design`.
- Tests need independent effectiveness review: use `devflow-test-checker`.
- Code needs independent review: use `devflow-code-review`.

## Hard Gates

- Do not start before `devflow-ar-design-review` has passed.
- Do not enter RED before task queue preflight has passed.
- `Current Active Task` must be unique and match `task-board.md`.
- Every task must have Test Design Case IDs, Verify, and Definition of Done.
- Do not invent tests or business facts that are not in the approved AR design.
- Do not skip RED.
- Do not do cleanup during GREEN.
- REFACTOR must stay inside the current task boundary.
- Do not claim test effectiveness or code quality; dispatch `devflow-test-checker` next.

## Object Contract

- Primary Object: task-scoped implementation slice.
- Frontend Input Object: approved `ar-design-draft.md`, `ar-design-review.md`, `requirement.md`, `traceability.md`, optional existing `tasks.md` / `task-board.md`, component design, current code, `AGENTS.md`, and `progress.md`.
- Backend Output Object: `tasks.md`, `task-board.md`, C/C++ code changes, test code changes, `implementation-log.md`, fresh evidence, traceability updates, and progress updates.
- Boundaries: no component boundary changes, no AR scope changes, no self-review.

## Methodology

- **Task Queue As Execution Index**: `tasks.md` and `task-board.md` map approved design into executable TDD slices.
- **Design-Case Mapping**: every task references requirement rows, AR design anchors, and Test Design Case IDs.
- **Single Active Task**: exactly one task may be active or in progress.
- **Embedded TDD**: RED -> GREEN -> REFACTOR.
- **Two Hats**: implementation and refactoring stay separate.
- **Fresh Evidence**: RED / GREEN / REFACTOR evidence is generated in the current session.
- **Fresh Implementer Context**: the controller gives each implementer subagent only the current task context pack, not the whole session history.

## Subagent Execution Mode

Use this mode by default when implementing the Current Active Task, especially when code reading or editing would pull substantial context into the controller session. The controller remains responsible for routing, task queue state, evidence paths, and final handoff.

Do not make the implementer subagent read the whole plan, prior chat, or broad repository context. Build a context pack and paste the required facts directly into the dispatch prompt.

### Implementer Context Pack

Before dispatching an implementer subagent, write or assemble this context pack from approved artifacts:

```markdown
## Implementer Context Pack
- Work Item Type / ID:
- Owning Component:
- Current Active Task:
- Task Goal:
- Acceptance:
- Files allowed to inspect/edit:
- Files explicitly out of scope:
- Requirement Rows:
- AR Design Anchors:
- Test Design Case IDs:
- Existing Test Harness / Commands:
- Verify Commands:
- Evidence Paths To Write:
- Component Boundary Constraints:
- Hard Stops:
  - ask if requirements, acceptance, approach, or dependencies are unclear
  - stop if task requires component-boundary or architecture decisions
  - do not add tests or behavior not present in approved AR design
```

### Implementer Status Handling

The implementer subagent reports one status:

- `DONE`: implementation and fresh evidence are ready; controller records report and dispatches `devflow-test-checker`.
- `DONE_WITH_CONCERNS`: implementation exists but the subagent flagged uncertainty; controller resolves concerns before test-checker.
- `NEEDS_CONTEXT`: controller supplies missing context and re-dispatches with a tighter context pack.
- `BLOCKED`: controller decides whether to route to `devflow-ar-design`, `devflow-router`, or split the task further.

The implementer self-review is useful but never replaces `devflow-test-checker` or `devflow-code-review`.

## Workflow

### 1. Align Inputs And Work Item

Read approved AR design, AR design review, requirement, traceability, existing task queue artifacts if present, component design, AGENTS.md, code context, and progress.md.

Stop if AR design review has not passed, test design is missing, or the work item identity is ambiguous.

### 2. Create Or Validate Task Queue

If `features/<id>/tasks.md` or `task-board.md` is missing, create them from the approved AR design using `references/task-plan-template.md` and `references/task-board-template.md`. If they already exist, validate them against the current approved AR design and requirement without unrelated rewrites.

Each task must include Task ID, Goal, Acceptance, Files, Covers Requirement, AR Design Anchor, Test Design Case IDs, Dependencies, Verify, Definition of Done, Expected Evidence Paths, and notes/assumptions.

Task queue preflight checks:

- TR1 Executability: each task can be started cold and is not too large.
- TR2 Contract: Acceptance, Files, Verify, and DoD are complete.
- TR3 Verification Seeds: Verify supports fail-first RED/GREEN work.
- TR4 Dependency: dependencies are clear and acyclic.
- TR5 Traceability: task maps to requirement row, AR design, and test case.
- TR6 Router Readiness: task-board can select exactly one Current Active Task or next-ready task.

If preflight fails because information is missing from the AR design, route to `devflow-ar-design`. If queue state is ambiguous, route to `devflow-router`.

### 3. Check Component Boundary

Compare planned changes with component design. If the task touches component interfaces, dependencies, state machines, or SOA boundary, stop and route to `devflow-router` for component-impact handling.

### 4. Prepare Implementer Context Pack

Create the Implementer Context Pack for the Current Active Task. Record its path or summary in `task-board.md` before dispatch. If the pack cannot be made small and precise, the task is too broad; split or refine the task before implementation.

### 5. Dispatch Implementer Subagent

Dispatch a fresh implementer subagent with only the context pack, allowed file scope, and expected evidence paths. The implementer performs steps 6-10 below inside that limited context. If the subagent asks questions, answer them in the controller session and re-dispatch with the clarified context pack.

For trivial, single-file edits with already-small context, the controller may implement directly, but it must still follow the same RED / GREEN / REFACTOR evidence rules.

### 6. Materialize Tests From Test Design

Discover existing test harnesses, build scripts, CI config, nearby component tests, and team mock/fixture style. If no runnable harness exists for this target, build the smallest smoke-tested harness first and record bootstrap evidence. Harness failure is not business RED.

Implement only tests for the Current Active Task's Test Design Case IDs. Preserve Task ID and Case ID anchors in names or comments.

### 7. RED

Run the new test and record valid RED evidence under `features/<id>/evidence/unit/` or `evidence/integration/`. Evidence includes command, exit code, failure summary, why the failure matches the intended behavior gap, and freshness anchor.

### 8. GREEN

Write the smallest implementation that turns RED green. Record GREEN evidence with command, exit code, pass summary, key result, and freshness anchor. Do not refactor in GREEN.

### 9. REFACTOR

Only after tests are green, perform task-scoped cleanup if needed. Follow `references/red-green-refactor-discipline.md`. Rerun tests after every cleanup and record REFACTOR evidence if cleanup occurred.

### 10. Static And Dynamic Evidence

Run build, static analysis, and relevant regression checks. Follow `references/embedded-evidence-checklist.md`. Critical unexplained issues block handoff.

### 11. Implementation Log And Traceability

Write Current Active Task, implementer status/report, changed files, decisions, RED/GREEN/REFACTOR evidence, test results, and open risks to `implementation-log.md`. Update traceability with Task ID, Code File, Test Code File, and Verification Evidence.

### 12. Progress And Handoff

Update progress fields: Current Stage, Task Plan Path, Task Board Path, Current Active Task, Pending Reviews And Gates, and Next Action Or Recommended Skill = `devflow-test-checker`. Update `task-board.md` with dispatch status, context pack location/summary, implementation report, evidence paths, and any blocked reason.

Dispatch an independent reviewer subagent for `devflow-test-checker`; do not run test review inline.

## Output Contract

- `features/<id>/tasks.md` and `task-board.md` created or validated.
- Implementer Context Pack recorded for Current Active Task when subagent mode is used.
- C/C++ code and test code for Current Active Task.
- `implementation-log.md` with handoff block.
- Fresh evidence under `evidence/{unit,integration,static-analysis,build}/`.
- Updated traceability and progress.
- Next action: `devflow-test-checker`.

## Red Flags

- Starting implementation before task queue preflight passes.
- Dispatching an implementer subagent with broad chat history instead of a curated context pack.
- Making the implementer discover the whole plan or unrestricted repository context.
- Multiple active or in-progress tasks.
- Adding tests not present in AR design.
- Treating harness setup failure as business RED.
- Writing implementation before RED.
- Refactoring during GREEN.
- Changing component boundary inside implementation.
- Reusing stale evidence.
- Self-approving tests or code.

## Verification

- [ ] Work item identity is stable.
- [ ] Task queue preflight passed.
- [ ] Current Active Task is unique and matches task-board.
- [ ] Implementer Context Pack is small, explicit, and recorded when subagent mode is used.
- [ ] Implementer status is DONE or DONE_WITH_CONCERNS with concerns resolved before review.
- [ ] Test Design Case IDs drive the work.
- [ ] RED, GREEN, and optional REFACTOR evidence are fresh.
- [ ] Build/static/regression evidence is recorded.
- [ ] implementation-log.md has handoff information.
- [ ] traceability.md is updated.
- [ ] progress.md routes to `devflow-test-checker`.

## Local Test Design Contract Excerpt

Each test design case used by this skill needs: case id, requirement row or design anchor, behavior under test, preconditions, inputs/stimuli, expected output or observable effect, mock/stub/simulation boundary, verification command or evidence path, and embedded risk covered. DevFlow does not use a separate test-design.md; test design lives in AR design.

## Local DevFlow Conventions

This section is owned by this skill. Do not load a shared conventions file. Project AGENTS.md may override equivalent paths or templates.

### Progress Fields

Use canonical progress fields when this skill reads or writes `features/<id>/progress.md`:

- Work Item Type
- Work Item ID
- Owning Component / Owning Subsystem
- Workflow Profile
- Execution Mode
- Current Stage
- Pending Reviews And Gates
- Task Plan Path
- Task Board Path
- Current Active Task
- Implementer Dispatch Status
- Implementer Context Pack
- Implementation Report
- Next Action Or Recommended Skill
- Blockers
- Last Updated

### Handoff Fields

Return current_node, work_item_id, owning_component, artifact_paths, evidence_summary, traceability_links, blockers, next_action_or_recommended_skill, and reroute_via_router.

Do not set next_action_or_recommended_skill to using-devflow or free text.

## Supporting References

| File | Purpose |
|---|---|
| `references/task-plan-template.md` | Task queue plan template |
| `references/task-board-template.md` | Task board state projection template |
| `references/red-green-refactor-discipline.md` | RED / GREEN / REFACTOR discipline |
| `references/embedded-evidence-checklist.md` | Evidence capture checklist |
| Local Test Design Contract Excerpt | Test design field contract |
