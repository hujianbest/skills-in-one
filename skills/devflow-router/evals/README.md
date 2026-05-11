# `devflow-router` evals

Misuse scenarios that `devflow-router` MUST refuse. These cover the highest-cost router failures: wrong canonical next node, profile silent escalation/downgrade, cross-subgraph switching, missing upstream evidence, and `auto`-mode misuse.

Format and run procedure are defined in [`docs/principles/06 evals-format.md`](../../../docs/principles/06%20evals-format.md). Read that first.

## Scenarios at a glance

| ID | Category | Severity | Title |
|---|---|---|---|
| router-EV-001 | gate-skipped | critical | TDD complete → never skip `devflow-test-review` before `devflow-code-review` |
| router-EV-002 | profile-discipline | critical | SR work item must not cross into implementation subgraph |
| router-EV-003 | evidence-missing | critical | Component-impact AR with missing `docs/component-design.md` must block `devflow-ar-design` |
| router-EV-004 | profile-discipline | high | AR design that changes a SOA interface must escalate to `component-impact` |
| router-EV-005 | auto-mode-misuse | high | `Execution Mode = auto` must NOT skip review / gate / approval |
| router-EV-006 | wrong-node-routing | high | Multiple `in_progress` tasks → `reroute_via_router=true`, never silently pick one |
| router-EV-007 | template-violation | medium | Free-text `Next Action` from a leaf must be ignored, fall back to migration table |
| router-EV-008 | wrong-node-routing | medium | After `devflow-completion-gate = 通过` with a next-ready task, route to `devflow-tdd-implementation`, not `devflow-finalize` |

## How to run

For each scenario:

1. Copy `fixtures/<scenario.fixture>/` into a fresh sandbox path, e.g. `/tmp/devflow-eval/<scenario.id>/`.
2. Apply any `setup.progress` overrides on top of the fixture's `progress.md`.
3. Open a **new OpenCode session** (no chat memory carry-over) with the sandbox as the working directory and a clean `AGENTS.md` matching this repo's root `AGENTS.md`.
4. Send the scenario's `input.user_request` as the first message.
5. Capture the agent's structured handoff and any artifact writes.
6. Compare against `must_do` / `must_not_do` / `expected_handoff` and walk the `verification` checklist.

A scenario passes if **every** `must_do` is satisfied, **no** `must_not_do` happens, and `expected_handoff` matches.

## Adding a scenario

1. Pick a stable `router-EV-NNN` id (next available).
2. Build the smallest possible fixture under `fixtures/<scenario.id>/` — only the artifacts the router needs to read for this decision.
3. Add the scenario object to `evals.json`.
4. Add a row to the table above.
5. If the new scenario protects a hard gate that doesn't yet exist in `SKILL.md`, add the gate to the SKILL in the same PR.
