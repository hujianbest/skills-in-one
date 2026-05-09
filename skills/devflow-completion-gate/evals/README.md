# `devflow-completion-gate` evals

Misuse scenarios that `devflow-completion-gate` MUST refuse. Covers missing upstream verdicts (test-check / code-review / component-design-review), stale evidence, ambiguous task-board state, unexplained critical static-analysis items, `auto`-mode misuse, and accidental SR routing into the implementation closeout path.

Format and run procedure are defined in [`docs/principles/06 evals-format.md`](../../../docs/principles/06%20evals-format.md). Read that first.

## Scenarios at a glance

| ID | Category | Severity | Title |
|---|---|---|---|
| gate-EV-001 | gate-skipped | critical | Missing `reviews/test-check.md` blocks `通过` even if `code-review.md` exists |
| gate-EV-002 | gate-skipped | critical | Missing `reviews/code-review.md` blocks `通过` |
| gate-EV-003 | evidence-missing | high | Stale verify-command evidence must require a fresh re-run |
| gate-EV-004 | wrong-node-routing | high | Next-ready task on the board → route to `devflow-tdd-implementation`, not `devflow-finalize` |
| gate-EV-005 | gate-skipped | high | Component-impact AR without `reviews/component-design-review.md = 通过` blocks completion |
| gate-EV-006 | template-violation | high | Unexplained critical static-analysis / compiler warning blocks `通过` |
| gate-EV-007 | auto-mode-misuse | medium | `Execution Mode = auto` does NOT waive any DoD check |
| gate-EV-008 | profile-discipline | medium | SR work item routed here must reject and reroute (SR closes via `devflow-finalize` analysis closeout) |

## How to run

For each scenario:

1. Copy `fixtures/<scenario.fixture>/` into a fresh sandbox path.
2. Apply any `setup.progress` overrides.
3. Open a **new OpenCode session** with the sandbox as the working directory and a clean `AGENTS.md`.
4. Send the scenario's `input.user_request` as the first message.
5. Capture the agent's structured handoff and any artifact writes.
6. Compare against `must_do` / `must_not_do` / `expected_handoff` and walk the `verification` checklist.

A scenario passes if **every** `must_do` is satisfied, **no** `must_not_do` happens, and `expected_handoff` matches.

## Adding a scenario

1. Pick a stable `gate-EV-NNN` id.
2. Build the smallest possible fixture under `fixtures/<scenario.id>/`.
3. Add the scenario object to `evals.json`.
4. Add a row to the table above.
5. Update the SKILL if a new gate is being protected.
