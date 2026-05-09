# Changelog

All notable changes to DevFlow are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] — 2026-05-09

First official DevFlow release. Scope: development-stage workflow on **OpenCode**, biased toward embedded C / C++ teams.

### Added

- 13 active DevFlow skills under `skills/`:
  - Entry: `using-devflow`
  - Routing: `devflow-router`
  - Specification: `devflow-specify`, `devflow-spec-review`
  - Component design: `devflow-component-design`, `devflow-component-design-review`
  - AR design: `devflow-ar-design`, `devflow-ar-design-review`
  - Implementation: `devflow-tdd-implementation`
  - Verification: `devflow-test-checker`, `devflow-code-review`
  - Gate / closeout: `devflow-completion-gate`, `devflow-finalize`
  - Problem fix: `devflow-problem-fix`
- Repository-root `AGENTS.md` documenting the OpenCode hard contract for DevFlow agents (entry through `using-devflow`, evidence-first routing, role-separated reviewers, no self-verification, no profile downgrade, etc.).
- `docs/guides/opencode-setup.md` — installation, skill discovery, automatic invocation, agent expectations, limitations.
- `docs/guides/devflow-usage-guide.md` — usage scenarios and FAQ for end users.
- `docs/principles/00-05` — internal principle docs (DevFlow soul, skill-node contract, skill anatomy, artifact layout, workflow architecture, coding principles).
- `evals/` directory on the four high-risk skills — `devflow-router`, `devflow-tdd-implementation`, `devflow-test-checker`, `devflow-completion-gate`. Each `evals/` carries a `README.md`, an `evals.json` enumerating misuse scenarios the skill MUST refuse (wrong-node routing, profile silent downgrade, cross-subgraph switching, missing test design before TDD, reviewer overreach, missing upstream verdict at completion gate, etc.), and a `fixtures/` directory of minimal artifact snapshots used as scenario inputs. The eval format is documented in `docs/principles/06 evals-format.md`.
- Per-skill `## 反向理由化（Common Rationalizations）` table on every leaf skill, listing the most common LLM excuses with pre-written counter-arguments.
- `LICENSE` (MIT) and `CONTRIBUTING.md`.
- User-perspective skills directory table and lifecycle diagram in both English and Chinese READMEs.

### Changed

- Brand unified to **DevFlow** (was inconsistently "HarnessFlow" in README, "DevFlow" elsewhere). Repository, product, and skill prefix all match.
- `devflow-tasks` and `devflow-tasks-review` workflow nodes folded into `devflow-tdd-implementation` (task planning is now an internal preflight; `tasks.md` / `task-board.md` remain as artifacts).
- Design authoring skills (`devflow-component-design`, `devflow-ar-design`) require an explicit **Design Options** checkpoint before drafting the full design.
- Each skill now owns its local conventions and references; there is no shared `skills/docs/` or `skills/templates/` folder.
- README, `docs/principles/`, and skill body references corrected from `devflow-skills/` and `docs/devflow-principles/` to the actual paths `skills/` and `docs/principles/`.

### Removed

- The placeholder reference to `devflow-skills/docs/devflow-shared-conventions.md` (the doc never existed; equivalent rules are now self-contained in each skill's `## 本地 DevFlow 约定` section).

### Out of scope

- Multi-agent-runtime integrations (Claude Code, Cursor, Gemini, Copilot, Windsurf, Kiro). v1.0 is OpenCode-only.
- System / integration / acceptance test workflows (belong to a future `test-flow` family).
- Product discovery and runtime incident management (belong to upstream `design-flow` / downstream operations workflows).

[Unreleased]: https://github.com/hujianbest/devflow/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/hujianbest/devflow/releases/tag/v1.0.0
