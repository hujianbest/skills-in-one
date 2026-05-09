# DevFlow Reviewer Personas

This directory holds the **minimum prompt contracts** for the independent reviewer subagents that `devflow-router` dispatches.

| Persona | Implements skill | Dispatched when |
|---|---|---|
| [`devflow-spec-reviewer`](devflow-spec-reviewer.md) | `devflow-spec-review` | `requirement.md` needs a verdict |
| [`devflow-component-design-reviewer`](devflow-component-design-reviewer.md) | `devflow-component-design-review` | `component-design-draft.md` needs a verdict |
| [`devflow-ar-design-reviewer`](devflow-ar-design-reviewer.md) | `devflow-ar-design-review` | `ar-design-draft.md` (incl. embedded test design) needs a verdict |
| [`devflow-code-reviewer`](devflow-code-reviewer.md) | `devflow-code-review` | C / C++ change needs an independent inspection (after `devflow-test-checker = 通过`) |

`devflow-test-checker` is also a reviewer skill but does not have a separate persona — it is dispatched directly via [`skills/devflow-test-checker/SKILL.md`](../skills/devflow-test-checker/SKILL.md), which is already structured as a reviewer prompt.

## How they are used

- The full workflow contract for each reviewer lives in the corresponding `skills/devflow-*-review/SKILL.md`. The persona file is the **seed prompt** the controller passes to the dispatched subagent so it does not inherit the controller's chat history.
- Personas are read-only on the artifact under review. They return `verdict` + `findings` + a single canonical `next_action_or_recommended_skill`. They never edit production artifacts.
- Personas mirror the parent skill's hard gates and rationalization-refutation list. When you change the skill, update the persona in the same PR.

## See also

- [`AGENTS.md`](../AGENTS.md) — repository-level OpenCode contract, including the reviewer-dispatch protocol.
- [`docs/guides/opencode-setup.md`](../docs/guides/opencode-setup.md) — how OpenCode discovers and dispatches these personas.
