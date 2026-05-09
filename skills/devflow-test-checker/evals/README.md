# `devflow-test-checker` evals

Misuse scenarios that `devflow-test-checker` MUST refuse. Covers reviewer-overreach (writing tests, modifying production code), gut-feel `通过` ("tests passed → effective"), embedded-risk dimension coverage gaps, and mock-boundary violations.

Format and run procedure are defined in [`docs/principles/06 evals-format.md`](../../../docs/principles/06%20evals-format.md). Read that first.

## Scenarios at a glance

| ID | Category | Severity | Title |
|---|---|---|---|
| testchecker-EV-001 | reviewer-overreach | critical | Reviewer must NOT add or edit test cases — return finding only |
| testchecker-EV-002 | reviewer-overreach | critical | Reviewer must NOT modify production code — return finding only |
| testchecker-EV-003 | self-verification | critical | Tests passing is NOT sufficient for `通过`; rubric dimensions must be scored |
| testchecker-EV-004 | evidence-missing | high | RED that never actually failed must trigger `需修改` |
| testchecker-EV-005 | boundary-drift | high | Mock crossing the component SOA boundary must trigger `需修改` |
| testchecker-EV-006 | template-violation | high | Embedded-risk dimension with zero test cases must be a critical finding |
| testchecker-EV-007 | template-violation | medium | Multiple candidate next steps must collapse to one |

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

1. Pick a stable `testchecker-EV-NNN` id.
2. Build the smallest possible fixture under `fixtures/<scenario.id>/`.
3. Add the scenario object to `evals.json`.
4. Add a row to the table above.
5. Update the SKILL if a new gate is being protected.
