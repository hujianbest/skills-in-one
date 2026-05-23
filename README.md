# DevFlow

[English](README.md) | [中文](README.zh-CN.md)

**Artifact-first SDD, gated TDD, and role-separated reviews for AI coding agents.**

DevFlow is a development-stage workflow for AI coding agents. It takes an accepted SR / AR / DTS / CHANGE work item through specification, design, TDD implementation, independent review, completion gating, and closeout. The next step is recovered from durable artifacts, not chat memory.

DevFlow is intentionally narrower than an idea-to-product workflow. It does not own product discovery, release operations, system / integration / acceptance testing, or runtime incident management. It starts after the team has accepted the requirement or problem report.

> **Status - v1.0.0**: first official release, scoped to **OpenCode**. Multi-tool integrations such as Claude Code, Cursor, Gemini, Copilot, Windsurf, and Kiro are outside this release.

---

## Command Intents

OpenCode v1 uses natural language plus automatic skill discovery. The `commands/` directory documents slash-style intents that teams can wire into their client, but every command is a bias, not a bypass: `using-devflow` and `devflow-router` still check repository evidence before choosing the next canonical node.

| What you're doing | Command intent | Key principle |
|---|---|---|
| Enter or resume DevFlow | [`/devflow`](commands/devflow.md) | Route from artifacts |
| Define what to build | [`/devflow-specify`](commands/devflow-specify.md) | Spec before design or code |
| Plan how to build it | [`/devflow-design`](commands/devflow-design.md) | Design options before a chosen design |
| Build one active task | [`/devflow-build`](commands/devflow-build.md) | RED -> GREEN -> REFACTOR with fresh evidence |
| Close engineering work | [`/devflow-ship`](commands/devflow-ship.md) | Reviews and gates before closeout |
| Fix a DTS / hotfix | [`/devflow-fix`](commands/devflow-fix.md) | Reproduce, root-cause, then make the minimal safe fix |

Reviews are not user-invoked shortcuts. `devflow-router` dispatches independent reviewer subagents for spec, component-design, AR-design, test, and code reviews.

---

## Quick Start

### OpenCode

DevFlow v1.0 is OpenCode-only. You can keep the skill pack as a sibling repository or vendor it into the component repository where work items live.

#### Option A - Sibling Skill Pack

```bash
git clone https://github.com/hujianbest/devflow.git ~/devflow
cd /path/to/your-component-repo
ln -s ~/devflow/skills .opencode-skills
cp ~/devflow/AGENTS.md ./AGENTS.md
```

Then edit the copied `AGENTS.md` `## Project overrides` section for your component paths, templates, and coding standards.

#### Option B - Vendored

```bash
cd /path/to/your-component-repo
git subtree add --prefix .devflow https://github.com/hujianbest/devflow.git v1.0.0 --squash
cp .devflow/AGENTS.md ./AGENTS.md
```

Then point OpenCode at `.devflow/skills/`.

More setup detail: [`docs/guides/opencode-setup.md`](docs/guides/opencode-setup.md).

### Try It

```text
Use DevFlow from this repo. Start with using-devflow.
I want to clarify AR12345 for the notifications component.
Do not jump straight to code.
```

If process artifacts already exist:

```text
Continue AR12345 with DevFlow. Read features/AR12345-*/progress.md and route me to the next step.
```

---

## See It Work

```text
You:       Use DevFlow to clarify AR12345.

DevFlow:   Enters through using-devflow, writes or revises the requirement
           artifact, and routes to independent spec review.

You:       Use DevFlow to design the approved AR.

DevFlow:   Checks whether component-impact design is required, records design
           options, writes the AR implementation design with embedded test
           design, and routes both designs through independent reviews.

You:       Use DevFlow to build the current active task.

DevFlow:   Locks one Current Active Task, prepares an Implementer Context Pack,
           runs RED -> GREEN -> REFACTOR, and records evidence in task-board,
           implementation-log, and evidence paths.

You:       Use DevFlow to verify and close this work.

DevFlow:   Dispatches test review, code review, completion gate, and finalize.
           It promotes long-term AR assets only during closeout.
```

For a DTS or hotfix, DevFlow first reproduces the issue and records root cause in `devflow-problem-fix`, then returns to the same design / build / review / gate chain as needed.

---

## Skill Catalog

DevFlow ships one public entry skill plus 13 canonical `devflow-*` runtime nodes.

### Meta And Routing

| Skill | What it does | Use when |
|---|---|---|
| [`using-devflow`](skills/using-devflow/SKILL.md) | Public entry shell for direct-invoke vs route-first | Starting a session or expressing a high-level DevFlow intent |
| [`devflow-router`](skills/devflow-router/SKILL.md) | Evidence-based runtime router and recovery controller | Continuing from artifacts or consuming review / gate outcomes |

### Define

| Skill | What it does | Use when |
|---|---|---|
| [`devflow-specify`](skills/devflow-specify/SKILL.md) | Turns SR / AR / DTS / CHANGE intent into testable requirements | Writing or revising a reviewable spec |
| [`devflow-spec-review`](skills/devflow-spec-review/SKILL.md) | Reviews specs for clarity, completeness, and testability | A spec artifact is ready for independent review |

### Plan

| Skill | What it does | Use when |
|---|---|---|
| [`devflow-component-design`](skills/devflow-component-design/SKILL.md) | Writes or revises component implementation design | The work has component-impact or SR analysis needs component design |
| [`devflow-component-design-review`](skills/devflow-component-design-review/SKILL.md) | Reviews component design with role separation | Component design needs an independent verdict |
| [`devflow-ar-design`](skills/devflow-ar-design/SKILL.md) | Produces AR implementation design with embedded test design | Approved requirements need code-level design before TDD |
| [`devflow-ar-design-review`](skills/devflow-ar-design-review/SKILL.md) | Reviews AR design and test design | AR design is ready for independent review |

### Build, Verify, And Close

| Skill | What it does | Use when |
|---|---|---|
| [`devflow-tdd-implementation`](skills/devflow-tdd-implementation/SKILL.md) | Implements one active task with task preflight, RED/GREEN/REFACTOR, and evidence | A reviewed design is ready for TDD implementation |
| [`devflow-test-review`](skills/devflow-test-review/SKILL.md) | Reviews test effectiveness and fail-first evidence | TDD evidence is ready for independent test review |
| [`devflow-code-review`](skills/devflow-code-review/SKILL.md) | Reviews implementation quality and C / C++ risks | Code is ready for independent review |
| [`devflow-completion-gate`](skills/devflow-completion-gate/SKILL.md) | Decides whether evidence is sufficient to complete or continue | Reviews are present and a completion decision is needed |
| [`devflow-finalize`](skills/devflow-finalize/SKILL.md) | Writes closeout and promotes long-term assets | Completion gate allows closeout |
| [`devflow-problem-fix`](skills/devflow-problem-fix/SKILL.md) | Reproduces, root-causes, and scopes DTS / hotfix work | A shipped-behavior defect or urgent problem needs controlled recovery |

---

## The DevFlow Method

DevFlow is not a prompt collection. It is a controlled engineering workflow for agents.

| Layer | DevFlow method | Why it matters |
|---|---|---|
| Intent | Spec-anchored SDD | Keeps scope, constraints, and acceptance criteria in reviewable files |
| Planning | Design options and review gates | Makes architecture, interfaces, risks, and test design explicit before code |
| Execution | Gated TDD | Requires fail-first evidence, GREEN verification, and one active task at a time |
| Routing | Artifact-based recovery | Lets another agent resume from `progress.md`, reviews, evidence, and completion records |
| Review | Role-separated subagents | Prevents authoring and approval from collapsing into one session |
| Verification | Test review, code review, completion gate | Separates "tests ran" from "evidence is sufficient" |
| Closeout | Long-term asset promotion | Syncs accepted specs and designs into `docs/` only when the gate allows it |

---

## How Skills Work

Each skill is a self-contained operating procedure:

```text
SKILL.md
├── Frontmatter classifier
├── Overview and trigger conditions
├── Hard gates and object contract
├── Step-by-step workflow
├── Required artifacts and evidence
├── Review or gate contract
├── Red flags and common rationalizations
├── Verification checklist
└── Local DevFlow conventions
```

Key design choices:

- **Evidence over memory.** Routing reads files such as `features/<id>/progress.md`, reviews, approvals, evidence, and completion records.
- **Canonical names only.** `Next Action Or Recommended Skill` must be one of the canonical `devflow-*` nodes; `using-devflow` is a public entry and is never written into runtime handoff fields.
- **Controlled subagents.** `devflow-router` is the only reviewer dispatcher; `devflow-tdd-implementation` is the only implementer dispatcher.
- **No self-verification.** Authoring skills write artifacts and hand off; independent reviewers return verdicts and do not edit production artifacts.
- **Local references.** Each skill owns its `references/` and, where needed, `evals/`; there is no shared `skills/docs/` dependency.

---

## Artifact Model

Default process artifacts live under the component repository's `features/<id>/` directory:

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

Long-term assets live under the component repository's `docs/` directory:

```text
docs/
  component-design.md
  ar-specs/                  # AR requirement specs promoted from features/<id>/requirement.md
  ar-designs/                # AR implementation designs promoted from features/<id>/ar-design-draft.md
  interfaces.md              # optional, read-on-presence
  dependencies.md            # optional, read-on-presence
  runtime-behavior.md        # optional, read-on-presence
```

Project-level `AGENTS.md` may override equivalent paths and templates. Closed work items stay under `features/<id>/` so traceability links remain stable.

---

## Project Structure

```text
devflow/
├── AGENTS.md                         # OpenCode hard contract
├── commands/                         # Slash-style command intent definitions
├── agents/                           # Reviewer / implementer role mirrors
├── skills/                           # Entry skill + 13 canonical devflow-* nodes
│   ├── using-devflow/
│   ├── devflow-router/
│   ├── devflow-specify/
│   ├── devflow-spec-review/
│   ├── devflow-component-design/
│   ├── devflow-component-design-review/
│   ├── devflow-ar-design/
│   ├── devflow-ar-design-review/
│   ├── devflow-tdd-implementation/
│   ├── devflow-test-review/
│   ├── devflow-code-review/
│   ├── devflow-completion-gate/
│   ├── devflow-finalize/
│   └── devflow-problem-fix/
├── docs/
│   ├── guides/
│   │   └── opencode-setup.md
│   └── principles/
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
└── README.zh-CN.md
```

High-risk skills such as `devflow-router`, `devflow-tdd-implementation`, `devflow-test-review`, and `devflow-completion-gate` carry `evals/` directories that enumerate misuse scenarios they must refuse.

---

## Why DevFlow?

AI coding agents often jump from request to implementation. DevFlow gives them a narrower, harder path: clarify the accepted work item, design before slicing work, prove behavior with TDD, separate reviewers from authors, and close the loop with durable evidence.

DevFlow also draws a clear boundary around shipping. It can close engineering work and produce traceable handoff artifacts, but deployment, rollout, monitoring, rollback, and post-launch operations stay with the project's production systems.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Keep skills specific, verifiable, artifact-first, independently installable, and role-separated.

## License

[MIT](LICENSE) - use these skills in your projects, teams, and tools.
