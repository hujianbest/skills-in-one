# DevFlow

[English](README.md) | [中文](README.zh-CN.md)

**DevFlow** is a development-stage skill family for AI coding agents. It takes an accepted SR / AR / DTS / CHANGE work item through specification, design, TDD implementation, independent review, completion gating, and closeout — with artifact-first recovery and strict role separation.

DevFlow is intentionally narrower than an idea-to-product workflow. It does not own product discovery, release operations, or runtime incident management. It starts after the team has an accepted requirement or problem report, and it focuses on making engineering work traceable, reviewable, and recoverable from artifacts.

> **Status — v1.0.0**: First official release, scoped to **OpenCode**. Multi-tool integrations (Claude Code, Cursor, Gemini, Copilot, Windsurf, Kiro) are not in scope for this release.

---

## Lifecycle

```
  CLARIFY        DESIGN          BUILD          VERIFY         GATE         CLOSE
 ┌──────┐      ┌────────┐     ┌───────┐     ┌───────────┐    ┌──────┐    ┌───────┐
 │ Spec │ ───▶ │ AR /   │ ──▶ │  TDD  │ ──▶ │   Test-   │ ─▶ │ Done │ ─▶ │ Final │
 │Review│      │Component│    │ R/G/R │     │  Check  / │    │ Gate │    │  ize  │
 └──────┘      │ Design │     └───────┘     │CodeReview │    └──────┘    └───────┘
               └────────┘                   └───────────┘
```

Every transition is **evidence-driven** — the next step is recovered from disk artifacts (`features/<id>/progress.md`, `reviews/`, `evidence/`), not from chat memory. Reviews are dispatched as **independent subagents**, never inlined.

---

## Quick Start (OpenCode)

1. Clone this repo somewhere your OpenCode workspace can reach:

   ```bash
   git clone https://github.com/hujianbest/devflow.git
   ```

2. Make `skills/` discoverable to OpenCode and copy the [`AGENTS.md`](AGENTS.md) into your **component repo** (the repo where the work item lives).

3. Talk to the agent in natural language — DevFlow routes itself:

   ```text
   Use DevFlow to clarify AR12345 in this repo. Start from using-devflow.
   ```

   Or, if there are already process artifacts under `features/<id>/`:

   ```text
   Continue AR12345 with DevFlow. Read the artifacts and route me to the next step.
   ```

Detailed setup is in [`docs/guides/opencode-setup.md`](docs/guides/opencode-setup.md).

---

## Skills (User View)

Pick by what you're trying to do — DevFlow auto-routes from the entry skill.

| You want to… | Skill | Key principle |
|---|---|---|
| Decide where to start | [`using-devflow`](skills/using-devflow/SKILL.md) | Front controller, direct-invoke vs route-first |
| Let the agent pick the next node from artifacts | [`devflow-router`](skills/devflow-router/SKILL.md) | Evidence-based FSM routing |
| Clarify an SR / AR / DTS / CHANGE into a reviewable spec | [`devflow-specify`](skills/devflow-specify/SKILL.md) | EARS, BDD acceptance, MoSCoW, INVEST, NFR QAS |
| Independently review a spec | [`devflow-spec-review`](skills/devflow-spec-review/SKILL.md) | Author/reviewer separation, structured walkthrough |
| Write or revise a component implementation design | [`devflow-component-design`](skills/devflow-component-design/SKILL.md) | SOA boundary + Design Options checkpoint |
| Independently review a component design | [`devflow-component-design-review`](skills/devflow-component-design-review/SKILL.md) | Role-separated verdict |
| Write an AR implementation design (with embedded test design) | [`devflow-ar-design`](skills/devflow-ar-design/SKILL.md) | Code-level design + defensive C/C++ + test design |
| Independently review an AR design + test design | [`devflow-ar-design-review`](skills/devflow-ar-design-review/SKILL.md) | Independent design + test-design review |
| Implement with TDD (single active task, fresh evidence) | [`devflow-tdd-implementation`](skills/devflow-tdd-implementation/SKILL.md) | Task queue setup, RED/GREEN/REFACTOR, implementer subagent |
| Check whether the tests are actually effective | [`devflow-test-review`](skills/devflow-test-review/SKILL.md) | Post-TDD test effectiveness review |
| Review the C / C++ code | [`devflow-code-review`](skills/devflow-code-review/SKILL.md) | Fagan-style + embedded C/C++ risks + SOA boundary |
| Decide if the work item can be completed | [`devflow-completion-gate`](skills/devflow-completion-gate/SKILL.md) | Definition of Done + evidence bundle |
| Close out, sync long-term assets, hand off | [`devflow-finalize`](skills/devflow-finalize/SKILL.md) | Closeout pack + long-term asset promotion |
| Reproduce, root-cause, scope a hotfix / DTS | [`devflow-problem-fix`](skills/devflow-problem-fix/SKILL.md) | Reproduction + root cause + minimal safe fix |

Reviews are dispatched as **independent subagents** by `devflow-router`, each seeded with the matching `devflow-*-review` skill (or `devflow-test-review` / `devflow-code-review`). The reviewer subagent reads only the artifact under review and returns a structured verdict — it never edits the artifact.

---

## Skill Family Layout

```text
skills/
  using-devflow/
  devflow-router/
  devflow-specify/
  devflow-spec-review/
  devflow-component-design/
  devflow-component-design-review/
  devflow-ar-design/
  devflow-ar-design-review/
  devflow-tdd-implementation/
  devflow-test-review/
  devflow-code-review/
  devflow-completion-gate/
  devflow-finalize/
  devflow-problem-fix/
docs/
  guides/
    devflow-usage-guide.md
    opencode-setup.md
  principles/
    00 soul.md
    01 skill-node-define.md
    02 skill-anatomy.md
    03 artifact-layout.md
    04 workflow-architecture.md
    05 coding-principles.md
AGENTS.md
LICENSE
CONTRIBUTING.md
CHANGELOG.md
```

Each skill is packaged to be usable on its own. Shared conventions and templates have been pulled into each skill's own `SKILL.md` or local `references/` directory. There is no required `skills/docs/` or `skills/templates/` cross-skill dependency.

---

## Core Workflow

Typical implementation flow:

```text
using-devflow
  -> devflow-router
  -> devflow-specify
  -> devflow-spec-review
  -> (optional) devflow-component-design
  -> (optional) devflow-component-design-review
  -> devflow-ar-design
  -> devflow-ar-design-review
  -> devflow-tdd-implementation
  -> devflow-test-review
  -> devflow-code-review
  -> devflow-completion-gate
  -> (next-ready task ? devflow-tdd-implementation : devflow-finalize)
```

SR analysis flow:

```text
using-devflow
  -> devflow-router
  -> devflow-specify
  -> devflow-spec-review
  -> (optional) devflow-component-design
  -> (optional) devflow-component-design-review
  -> devflow-finalize
```

Hotfix / problem-fix flow:

```text
using-devflow
  -> devflow-router
  -> devflow-problem-fix
  -> (optional) devflow-ar-design
  -> (optional) devflow-ar-design-review
  -> devflow-tdd-implementation
  -> devflow-test-review
  -> devflow-code-review
  -> devflow-completion-gate
  -> devflow-finalize
```

---

## Important Current Decisions

DevFlow is built around a few strong choices:

- `devflow-tasks` and `devflow-tasks-review` were merged into `devflow-tdd-implementation`. Task planning is an internal preflight step before TDD; `tasks.md` and `task-board.md` still exist as artifacts but not as separate workflow nodes.
- `devflow-tdd-implementation` can dispatch a fresh implementer subagent with a curated context pack to keep controller context small.
- Review nodes are independent reviewer subagents: spec review, component-design review, AR-design review, test-check, code-review.
- Design nodes require a Design Options checkpoint before drafting the full design.
- Each DevFlow skill owns its local conventions and references rather than depending on a shared pack-level docs folder.

---

## Methodology By Stage

| Stage | Skill | Methods |
|---|---|---|
| Entry | `using-devflow` | Front controller, direct-invoke vs route-first decision |
| Routing | `devflow-router` | Evidence-based FSM routing, profile selection, recovery from artifacts |
| Specification | `devflow-specify` | EARS, BDD acceptance, MoSCoW, INVEST, NFR quality attribute scenarios |
| Spec review | `devflow-spec-review` | Structured walkthrough, checklist review, author/reviewer separation |
| Component design | `devflow-component-design` | SOA boundary analysis, clean architecture boundaries, interface segregation, design options checkpoint |
| Component design review | `devflow-component-design-review` | Structured component design review, role-separated verdict |
| AR design | `devflow-ar-design` | Code-level design, defensive C/C++ design, embedded test design, design options checkpoint |
| AR design review | `devflow-ar-design-review` | Independent AR design and test-design review |
| TDD implementation | `devflow-tdd-implementation` | Task queue setup, single active task, RED/GREEN/REFACTOR, fresh evidence, implementer subagent context pack |
| Test review | `devflow-test-review` | Test effectiveness, coverage, mock/stub boundary, evidence freshness |
| Code review | `devflow-code-review` | Fagan-style inspection, embedded C/C++ risk review, SOA boundary review |
| Completion | `devflow-completion-gate` | Definition of Done, evidence bundle, next-task vs finalize decision |
| Closeout | `devflow-finalize` | Closeout pack, long-term asset promotion, handoff |
| Problem fix | `devflow-problem-fix` | Reproduction, root cause analysis, minimal safe fix boundary |

---

## Artifact Model

DevFlow is artifact-first. The next step is recovered from files, not chat memory.

Default process artifacts live under a component repository's `features/<id>/` directory:

```text
features/<id>/
  README.md
  progress.md
  requirement.md
  ar-design-draft.md
  component-design-draft.md
  tasks.md
  task-board.md
  traceability.md
  implementation-log.md
  reviews/
  evidence/
  completion.md
  closeout.md
```

Long-term assets live in the component repository's `docs/` directory:

```text
docs/
  component-design.md
  ar-designs/
  interfaces.md              # optional, read-on-presence
  dependencies.md            # optional, read-on-presence
  runtime-behavior.md        # optional, read-on-presence
```

Project `AGENTS.md` may override equivalent paths and templates.

---

## Subagent Context Strategy

The controller session should stay small. Heavy code context belongs in subagents.

`devflow-tdd-implementation` uses an **Implementer Context Pack** for each Current Active Task:

```text
Work Item Type / ID
Owning Component
Current Active Task
Task Goal and Acceptance
Allowed files
Out-of-scope files
Requirement rows
AR design anchors
Test Design Case IDs
Verify commands
Evidence paths
Hard stops
```

The implementer subagent receives that pack rather than the full chat history or broad repository context. It reports one of:

- `DONE`
- `DONE_WITH_CONCERNS`
- `NEEDS_CONTEXT`
- `BLOCKED`

The controller records the status in `task-board.md` / `implementation-log.md`, resolves concerns, and then dispatches `devflow-test-review`. Implementer self-review never replaces test review or code review.

---

## Design Options Checkpoint

Design authoring skills do not jump straight to one hidden solution.

`devflow-component-design` and `devflow-ar-design` both require a `Design Options` checkpoint before drafting the full design:

- propose 2-3 options
- show trade-offs
- recommend one option
- record confirmation status
- allow `Single obvious option` only with a reason

Review rubrics check that this checkpoint exists and was not used to hide a real decision.

---

## Repository Notes

- `skills/` holds the active DevFlow skill family. High-risk skills (`devflow-router`, `devflow-tdd-implementation`, `devflow-test-review`, `devflow-completion-gate`) carry an `evals/` directory enumerating the misuse scenarios they MUST refuse.
- `docs/principles/` contains design rationale for maintaining the DevFlow skills (not consumed by skills at runtime).
- `docs/guides/` contains user-facing usage and setup guides.
- Skill references are intentionally local to each skill to preserve independent installability.

---

## License

[MIT](LICENSE) — use these skills in your projects, teams, and tools.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Skills should be **specific** (actionable steps), **verifiable** (evidence requirements), **artifact-first** (recovery from disk), and **role-separated** (no self-verification).
