# AGENTS.md

## Cursor Cloud specific instructions

This is a **pure documentation/markdown repository** containing AI agent workflow skills (DevFlow). There is no application code, package manager, build system, or test framework.

### What this repo contains

- `skills/` — 14 DevFlow workflow skill nodes (markdown + references)
- `.cursor/skills/` — 2 meta-skills: `brainstorming` (with a Node.js visual companion server) and `writing-skills` (with a graphviz renderer)
- `docs/` — Design principles and usage guides

### Runnable utilities

Two Node.js utilities exist in `.cursor/skills/`:

1. **Brainstorm companion server** (`.cursor/skills/brainstorming/scripts/server.cjs`):
   - Start: `bash .cursor/skills/brainstorming/scripts/start-server.sh --host 0.0.0.0`
   - Stop: `bash .cursor/skills/brainstorming/scripts/stop-server.sh <screen_dir>`
   - Serves HTML mockups over HTTP + WebSocket; no npm dependencies needed (uses Node built-ins only)

2. **Diagram renderer** (`.cursor/skills/writing-skills/render-graphs.js`):
   - Usage: `node .cursor/skills/writing-skills/render-graphs.js <skill-directory>`
   - Requires `graphviz` system package (`dot` command)

### Lint / Test / Build

- No lint configuration, test framework, or build system exists in this repo.
- The "product" is the markdown skill files themselves — validate by reading and following them.
- `render-graphs.js` can verify that `dot` blocks in SKILL.md files are valid graphviz syntax.

### Development notes

- Node.js (any recent LTS) is sufficient for all utilities — no `npm install` needed.
- Graphviz must be installed for diagram rendering: `sudo apt-get install -y graphviz`
- Generated diagram files (`diagrams/` directories) are gitignored artifacts.
