# `devflow-tdd-implementation` evals

Misuse scenarios that `devflow-tdd-implementation` MUST refuse. Covers TDD discipline (RED-first, single active task, no self-approval), Implementer Context Pack discipline, Refactor Note discipline, and the boundary between "needs more context" (stays in this skill) vs "scope/profile blocker" (escalates to `devflow-router`).

Format and run procedure are defined in [`docs/principles/06 evals-format.md`](../../../docs/principles/06%20evals-format.md). Read that first.

## Scenarios at a glance

| ID | Category | Severity | Title |
|---|---|---|---|
| tdd-EV-001 | gate-skipped | critical | AR design without an embedded test-design section MUST NOT enter TDD |
| tdd-EV-002 | self-verification | critical | Implementer must NOT skip `devflow-test-checker` and hand off to `devflow-code-review` |
| tdd-EV-003 | wrong-node-routing | high | Multiple `in_progress` tasks must be collapsed to one before any RED is written |
| tdd-EV-004 | subagent-context-discipline | high | Implementer subagent must receive a Context Pack, not the controller's chat history |
| tdd-EV-005 | gate-skipped | high | Refactor must happen in REFACTOR phase, not GREEN; cleanup beyond cleanup must be escalated |
| tdd-EV-006 | template-violation | medium | Missing Refactor Note in `implementation-log.md` must block handoff to test-checker |
| tdd-EV-007 | wrong-node-routing | medium | `NEEDS_CONTEXT` from implementer must NOT bubble up to `devflow-router` |
| tdd-EV-008 | boundary-drift | high | Implementation that adds an out-of-scope file must stop and escalate, not silently expand the diff |

## How to run

For each scenario:

1. Copy `fixtures/<scenario.fixture>/` into a fresh sandbox path, e.g. `/tmp/devflow-eval/<scenario.id>/`.
2. Apply any `setup.progress` overrides on top of the fixture's `progress.md`.
3. Open a **new OpenCode session** with the sandbox as the working directory and a clean `AGENTS.md` matching this repo's root `AGENTS.md`.
4. Send the scenario's `input.user_request` as the first message.
5. Capture the agent's structured handoff and any artifact writes.
6. Compare against `must_do` / `must_not_do` / `expected_handoff` and walk the `verification` checklist.

A scenario passes if **every** `must_do` is satisfied, **no** `must_not_do` happens, and `expected_handoff` matches.

## Adding a scenario

1. Pick a stable `tdd-EV-NNN` id (next available).
2. Build the smallest possible fixture under `fixtures/<scenario.id>/`.
3. Add the scenario object to `evals.json`.
4. Add a row to the table above.
5. If the new scenario protects a workflow rule that doesn't yet exist in `SKILL.md`, add the rule to the SKILL in the same PR.
