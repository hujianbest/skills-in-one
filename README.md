# HarnessFlow

[English](README.md) | [Chinese](README.zh-CN.md)

HarnessFlow is a workspace for building agent workflow skills. The active skill family in this repository is **DevFlow**: a development-stage workflow for taking an accepted SR / AR / DTS / CHANGE item through specification, design, TDD implementation, independent review, completion gating, and closeout.

DevFlow is intentionally narrower than the older idea-to-product HarnessFlow direction. It does not own product discovery, release operations, or runtime incident management. It starts after the team has an accepted requirement or problem report, and it focuses on making engineering work traceable, reviewable, and recoverable from artifacts.

## Active Skill Family

The active pack lives in `devflow-skills/`.

```text
devflow-skills/
  using-devflow/
  devflow-router/
  devflow-specify/
  devflow-spec-review/
  devflow-component-design/
  devflow-component-design-review/
  devflow-ar-design/
  devflow-ar-design-review/
  devflow-tdd-implementation/
  devflow-test-checker/
  devflow-code-review/
  devflow-completion-gate/
  devflow-finalize/
  devflow-problem-fix/
```

Each skill is packaged to be usable on its own. Shared conventions and templates have been pulled into each skill's own `SKILL.md` or local `references/` directory. There is no required `devflow-skills/docs/` or `devflow-skills/templates/` dependency.

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
  -> devflow-test-checker
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
  -> devflow-test-checker
  -> devflow-code-review
  -> devflow-completion-gate
  -> devflow-finalize
```

## Important Current Decisions

DevFlow has recently been simplified around a few strong choices:

- `devflow-tasks` and `devflow-tasks-review` were merged into `devflow-tdd-implementation`.
- Task planning is now an internal task queue setup / preflight step before TDD.
- `tasks.md` and `task-board.md` still exist as artifacts, but not as separate workflow nodes.
- `devflow-tdd-implementation` can dispatch a fresh implementer subagent with a curated context pack to reduce controller context usage.
- Review nodes remain independent reviewer subagents: spec review, component design review, AR design review, test checker, and code review.
- Design nodes now require a design options checkpoint before drafting the full design.
- Each DevFlow skill owns its local conventions and references instead of depending on a shared pack-level docs folder.

## Methodology By Stage

| Stage | Skill | Methods |
|---|---|---|
| Entry | `using-devflow` | Front controller, direct-invoke vs route-first decision |
| Routing | `devflow-router` | Evidence-based finite-state routing, profile selection, recovery from artifacts |
| Specification | `devflow-specify` | EARS, BDD acceptance, MoSCoW, INVEST, NFR quality attribute scenarios |
| Spec review | `devflow-spec-review` | Structured walkthrough, checklist review, author/reviewer separation |
| Component design | `devflow-component-design` | SOA boundary analysis, clean architecture boundaries, interface segregation, design options checkpoint |
| Component design review | `devflow-component-design-review` | Structured component design review, role-separated verdict |
| AR design | `devflow-ar-design` | Code-level design, defensive C/C++ design, embedded test design, design options checkpoint |
| AR design review | `devflow-ar-design-review` | Independent AR design and test-design review |
| TDD implementation | `devflow-tdd-implementation` | Task queue setup, single active task, RED/GREEN/REFACTOR, fresh evidence, implementer subagent context pack |
| Test review | `devflow-test-checker` | Test effectiveness, coverage, mock/stub boundary, evidence freshness |
| Code review | `devflow-code-review` | Fagan-style inspection, embedded C/C++ risk review, SOA boundary review |
| Completion | `devflow-completion-gate` | Definition of Done, evidence bundle, next-task vs finalize decision |
| Closeout | `devflow-finalize` | Closeout pack, long-term asset promotion, handoff |
| Problem fix | `devflow-problem-fix` | Reproduction, root cause analysis, minimal safe fix boundary |

## Artifact Model

DevFlow is artifact-first. It recovers the next step from files, not chat memory.

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

The controller records the status in `task-board.md` / `implementation-log.md`, resolves concerns, and then dispatches `devflow-test-checker`. Implementer self-review never replaces test review or code review.

## Design Options Checkpoint

Design authoring skills do not jump straight to one hidden solution.

`devflow-component-design` and `devflow-ar-design` both require a `Design Options` checkpoint before drafting the full design:

- propose 2-3 options
- show trade-offs
- recommend one option
- record confirmation status
- allow `Single obvious option` only with a reason

Review rubrics check that this checkpoint exists and was not used to hide a real decision.

## Quick Start

Use natural language. There are no public command wrappers required.

```text
Use DevFlow from this repo. Start with using-devflow.
Continue this AR from the current artifacts and route me to the correct next step.
```

Other useful prompts:

```text
Use DevFlow to clarify this AR requirement.
Use DevFlow to review this requirement.md.
Use DevFlow to write the AR implementation design.
Use DevFlow to implement the current active task with TDD and fresh evidence.
Use DevFlow to review the tests and then the code.
Use DevFlow to decide whether this AR can be completed.
Use DevFlow to finalize the work item.
```

## Repository Notes

- `devflow-skills/` is the active skill family.
- `docs/devflow-principles/` contains design rationale for maintaining the DevFlow skills.
- Older `skills/hf-*` and temporary dry-run materials may still exist as historical assets, but the current workflow described here is DevFlow.
- Skill references are intentionally local to each skill to preserve independent installability.

## Status

DevFlow is in active development. The current shape is focused on embedded / component-oriented software development with C/C++ review concerns, but the workflow patterns are intentionally expressed as portable engineering controls: artifact-first routing, explicit design trade-offs, single-task TDD, independent reviews, and evidence-based completion.
