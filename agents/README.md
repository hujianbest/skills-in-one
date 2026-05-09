# DevFlow Reviewer Personas

Specialist personas that play a single review role with a single perspective. Each persona is a Markdown file consumed as a system prompt by the reviewer subagent that `devflow-router` dispatches.

| Persona | Role | Best for |
|---------|------|----------|
| [devflow-spec-reviewer](devflow-spec-reviewer.md) | Independent Spec Reviewer | EARS / BDD / MoSCoW / NFR-QAS audit of `requirement.md` (SR or AR/DTS/CHANGE) |
| [devflow-component-design-reviewer](devflow-component-design-reviewer.md) | Independent Component Design Reviewer | SOA boundary / interface / dependency / state-machine audit of `component-design-draft.md` |
| [devflow-ar-design-reviewer](devflow-ar-design-reviewer.md) | Independent AR Implementation Design Reviewer | AR design + embedded test-design section audit of `ar-design-draft.md` |
| [devflow-code-reviewer](devflow-code-reviewer.md) | Independent C / C++ Code Reviewer | Eight-axis embedded code inspection of the diff produced by `devflow-tdd-implementation` |

`devflow-test-checker` is also a reviewer skill but does not have a separate persona — its `SKILL.md` is already structured as a reviewer prompt and is dispatched directly.

## How personas relate to skills and the router

Three layers, each with a distinct job:

| Layer | What it is | Example | Composition role |
|-------|-----------|---------|------------------|
| **Skill** | A workflow with hard gates, object contract, steps, and exit criteria | `devflow-ar-design-review` | The *how* — the persona MUST follow the skill body verbatim |
| **Persona** | A role with a perspective and an output format | `devflow-ar-design-reviewer` | The *who* — adopts a viewpoint, produces a structured verdict |
| **Router** | The runtime dispatcher | `devflow-router` | The *when* — decides which review to run, seeds the persona, consumes the verdict |

`devflow-router` is the orchestrator. **Personas do not call other personas.** Skills are mandatory hops inside a persona's workflow.

## When each is invoked

- `devflow-router` reaches a review node → it dispatches a fresh subagent seeded with the corresponding persona file in this directory.
- The subagent loads the matching `skills/devflow-*-review/SKILL.md` (or `skills/devflow-code-review/SKILL.md`) and executes the workflow defined there.
- The subagent returns a structured handoff (verdict + findings + single canonical next node) to `devflow-router`.

The persona never decides which review to run. The router does. The persona never decides what comes next; it returns a verdict, and the router routes.

## What a DevFlow persona does and does not duplicate

A persona file in this directory contains:

- **Role identity** — "You are an independent X."
- **Review scope** — the high-level dimensions the reviewer evaluates (one bullet list per dimension).
- **Verdict scale** — the three legal verdicts (`通过 | 需修改 | 阻塞`) with one-line definitions.
- **Output format** — the markdown record template + the structured handoff fields.
- **Rules of the role** — short numbered list of things the reviewer must / must not do.
- **Composition** — when invoked directly, when invoked via the router, and what it must not do.

A persona file does **not** duplicate:

- Hard gates → see the parent skill's `## 硬性门禁`.
- Object contract / inputs / outputs → see the parent skill's `## 对象契约`.
- Step-by-step workflow → see the parent skill's `## 工作流`.
- Rubric scoring thresholds (e.g. "embedded-core dimension < 7 blocks 通过") → see the parent skill's rubric reference.
- Common rationalizations / counter-arguments → see the parent skill's `## 反向理由化（Common Rationalizations）`.

The skill is the contract. The persona is the system prompt that adopts the role and emits the report.

## Adding or editing a persona

1. Keep persona files thin — role + scope + output format + rules + composition. Push contract details into the skill, not the persona.
2. Address the agent in second person ("You are…").
3. Mirror the verdict scale and handoff field names exactly as the parent skill defines them.
4. End with a `## Composition` block: how the router invokes you, what you must defer to the skill, and that you do not invoke other personas.
5. Update the table at the top of this file.
