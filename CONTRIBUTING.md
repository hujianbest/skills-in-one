# Contributing to DevFlow

Thanks for your interest in DevFlow. This document describes how to contribute to the skill family, what makes a good change, and how to keep skills mutually consistent.

## Scope of v1.0

DevFlow v1.0 is intentionally narrow:

- It targets the **development stage**: from accepted SR / AR / DTS / CHANGE through specification, design, TDD, review, completion gate, and closeout.
- It is biased toward **embedded C / C++** teams. The workflow shape is portable, but reviewer rubrics emphasise memory / concurrency / real-time / resource / error-handling concerns.
- It targets the **OpenCode** integration. Other agent runtimes (Claude Code, Cursor, Gemini, Copilot, Windsurf, Kiro) are not in scope for v1.0; PRs that add them are welcome but should not change the existing OpenCode contract.
- It does **not** cover product discovery, system / integration / acceptance testing, release operations, or runtime incident response. These belong to other `*-flow` families.

If you are unsure whether your change fits, open an issue first.

## What a good DevFlow skill looks like

Every `skills/devflow-*/SKILL.md` should be:

- **Specific** — actionable steps, not vague advice. Each workflow step says *what to read*, *what to write*, and *when to stop*.
- **Verifiable** — the `## 验证清单` (Verification) section enumerates exit conditions in terms of artifacts on disk and review verdicts, not "it looks right".
- **Artifact-first** — the next step must be recoverable from `features/<id>/` files (`progress.md`, `reviews/`, `evidence/`), not from chat memory.
- **Role-separated** — author, reviewer, gate, and finalizer are distinct skills. No skill self-verifies its own output.
- **Independently installable** — references live under each skill's own `references/`. Avoid creating a shared `skills/docs/` or `skills/templates/` that other skills must load.

The full anatomy spec is in [`docs/principles/02 skill-anatomy.md`](docs/principles/02%20skill-anatomy.md).

## Required skill sections

A `SKILL.md` MUST contain (in order):

1. YAML frontmatter with `name` (= directory name, `devflow-*` prefix) and `description` (a classifier — *not* a workflow summary).
2. `# Title` + a 1–2 line statement of "what this skill does and what it does not".
3. `## 适用场景` — when to use, when to redirect.
4. `## 硬性门禁` — non-negotiable stop conditions (Hard Gates).
5. `## 对象契约` — Object Contract (Primary / Frontend Input / Backend Output / Transformation / Boundaries / Invariants).
6. `## 方法原则` — Methodology, with each method tied to a workflow step.
7. `## 工作流` — numbered steps, prose-style, each with method / input / output / stop rule.
8. `## 输出契约` — what is written, where, with which trace links and evidence.
9. `## 风险信号` — runtime stop signs.
10. `## 反向理由化（Common Rationalizations）` — common LLM-style excuses + counter-arguments.
11. `## 常见错误` — error → fix table.
12. `## 验证清单` — exit conditions.
13. `## 本地 DevFlow 约定` — artifact layout, progress fields, handoff fields, plus skill-specific local rules.
14. `## 支撑参考` — table of `references/*.md` files.

References belong in `references/` under each skill, not at the repository top level.

## Writing the `description` field

The `description` is a **classifier**, not a flow summary. It only answers "should this skill be loaded for the current request?".

- ✅ Good: `Use when independently reviewing a C/C++ code change produced by devflow-tdd-implementation against an approved AR design. Not for writing tests, modifying production code, or test effectiveness review.`
- ❌ Bad: `Use when reviewing code — read the diff, score it, write findings, hand off.`

Front-load triggering keywords (`spec review`, `AR implementation design`, `component design`, `test review`, `C/C++ code review`) so OpenCode's automatic skill discovery can match them.

## Anti-rationalization

Each leaf skill carries a `## 反向理由化（Common Rationalizations）` table. The point is not to be polite — it is to give the agent a pre-written rebuttal for the most common LLM excuses (e.g., *"I'll add the test design after TDD"*, *"the design is obvious so I can skip the Design Options checkpoint"*). Keep the table short (3–6 rows) and tightly scoped to the skill's actual decision points.

## Profile and routing changes

`devflow-router` is the runtime authority for Workflow Profile, Execution Mode, the canonical next node, reviewer dispatch, and review / gate recovery. Changes to:

- the legal profile set (`requirement-analysis`, `standard`, `component-impact`, `hotfix`, `lightweight`),
- subgraph membership (which skills each profile may route to),
- escalation rules,
- handoff / progress field schema,

MUST be proposed against `devflow-router/SKILL.md` and `devflow-router/references/profile-and-route-map.md` first, with each affected leaf updated in the same PR.

## Reviewer dispatch

Reviewer behaviour is encoded entirely in the `devflow-*-review` / `devflow-test-review` / `devflow-code-review` SKILL files. When `devflow-router` reaches a review node, it dispatches an independent subagent seeded with the corresponding skill body as its system prompt — the skill IS the reviewer prompt. Do not introduce a separate persona layer that paraphrases the skill.

## Skill `evals/`

High-risk skills (currently `devflow-router`, `devflow-tdd-implementation`, `devflow-test-review`, `devflow-completion-gate`) carry an `evals/` directory that enumerates the misuse scenarios the skill MUST refuse, in the format defined by [`docs/principles/06 evals-format.md`](docs/principles/06%20evals-format.md):

```
skills/devflow-<name>/evals/
  README.md
  evals.json
  fixtures/
```

When you change a hard gate, profile rule, or a key workflow step on one of these skills, update the matching `evals.json` scenario or add a new one in the same PR. Scenarios are reviewed against the skill body to ensure the skill actually refuses what the eval asserts.

## Pull request expectations

- One logical change per PR. Don't batch unrelated edits (a brand rename + a router refactor + a new skill).
- Update both `README.md` and `README.zh-CN.md` when you change user-facing surface area.
- Update `CHANGELOG.md` under the `Unreleased` heading.
- If you change canonical field names (`Workflow Profile`, `Current Active Task`, etc.), grep the entire repo and update every skill that reads or writes them.

## Repository hygiene

- File naming: skill directories are `devflow-<noun>`. Reference files are `kebab-case.md`. Persona files are `devflow-<role>-reviewer.md` (or equivalent).
- Don't add `.cursor/`, `.opencode/`, `.claude/` editor-specific directories at the repository root unless they are part of a deliberate integration release.
- Don't introduce a `skills/docs/` or `skills/templates/` shared folder. References live per-skill.

## License

By contributing, you agree your contributions are licensed under the [MIT License](LICENSE).
