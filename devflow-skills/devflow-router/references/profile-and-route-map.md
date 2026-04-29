# DevFlow Profile And Route Map

This reference belongs to `devflow-router`. It defines legal profile paths, route upgrades, and hard stops.

DevFlow has two sub-streams:

- requirement-analysis: SR work items; no implementation nodes.
- implementation: standard / component-impact / hotfix / lightweight profiles for AR / DTS / CHANGE work items.

Do not switch between SR analysis and implementation inside the same work item. SR closeout may list AR candidates; a requirement owner creates new AR work items separately.

## Requirement-Analysis Route

```text
using-devflow
  -> devflow-router
  -> devflow-specify
  -> devflow-spec-review
  -> (optional) devflow-component-design
  -> (optional) devflow-component-design-review
  -> devflow-finalize
```

Legal nodes: `devflow-specify`, `devflow-spec-review`, `devflow-component-design`, `devflow-component-design-review`, `devflow-finalize`.

Implementation nodes are illegal in this profile.

## Standard Route

```text
using-devflow
  -> devflow-router
  -> devflow-specify
  -> devflow-spec-review
  -> devflow-ar-design
  -> devflow-ar-design-review
  -> devflow-tdd-implementation        # includes task queue setup/preflight
  -> devflow-test-checker
  -> devflow-code-review
  -> devflow-completion-gate
  -> (next-ready task ? devflow-tdd-implementation : devflow-finalize)
```

## Component-Impact Route

```text
using-devflow
  -> devflow-router
  -> devflow-specify
  -> devflow-spec-review
  -> devflow-component-design
  -> devflow-component-design-review
  -> devflow-ar-design
  -> devflow-ar-design-review
  -> devflow-tdd-implementation        # includes task queue setup/preflight
  -> devflow-test-checker
  -> devflow-code-review
  -> devflow-completion-gate
  -> (next-ready task ? devflow-tdd-implementation : devflow-finalize)
```

Use component-impact for new components, SOA/interface/error-code/timing changes, dependency or state-machine changes, cross-component coordination, or missing/stale component design.

## Hotfix / Problem-Fix Route

```text
using-devflow
  -> devflow-router
  -> devflow-problem-fix
  -> (optional) devflow-ar-design -> devflow-ar-design-review
  -> devflow-tdd-implementation        # includes task queue setup/preflight when needed
  -> devflow-test-checker
  -> devflow-code-review
  -> devflow-completion-gate
  -> devflow-finalize
```

Hotfix can compress document volume, but cannot skip test-checker, code-review, or completion-gate.

## Lightweight Route

```text
using-devflow
  -> devflow-router
  -> devflow-specify (minimal)
  -> devflow-spec-review
  -> devflow-ar-design (minimal, still includes test design section)
  -> devflow-ar-design-review
  -> devflow-tdd-implementation        # includes minimal task queue setup/preflight
  -> devflow-test-checker
  -> devflow-code-review
  -> devflow-completion-gate
  -> devflow-finalize
```

Lightweight compresses document volume only; it does not remove quality gates.

## Hard Stops

Any hit must stop and set `reroute_via_router=true`:

1. Requirement input is unclear for scope / acceptance / direction.
2. IR / SR / AR traceability conflicts.
3. AR / DTS / CHANGE lacks one owning component.
4. SR lacks owning subsystem.
5. SR work item tries to enter implementation nodes.
6. Component design is missing/stale while the change affects component boundaries.
7. AR design lacks embedded test design.
8. Task queue preflight cannot produce complete tasks or a unique Current Active Task.
9. `task-board.md` has multiple in_progress tasks, ambiguous next-ready tasks, or conflicts with progress.md.
10. TDD is complete but tests have not passed `devflow-test-checker`.
11. Code change breaks SOA boundary or adds unexplained cross-component dependency.
12. Critical static-analysis / build / coding-standard issue remains unexplained.
13. Review / gate verdict cannot map to exactly one next action.

## Reviewer Dispatch Anchor

Review nodes must be dispatched as independent reviewer subagents:

| Source node | Dispatch node |
|---|---|
| `devflow-specify` | `devflow-spec-review` |
| `devflow-component-design` | `devflow-component-design-review` |
| `devflow-ar-design` | `devflow-ar-design-review` |
| `devflow-tdd-implementation` | `devflow-test-checker` |
| `devflow-test-checker` pass | `devflow-code-review` |

Task queue preflight is internal to `devflow-tdd-implementation`; it is not a dispatched review node.
