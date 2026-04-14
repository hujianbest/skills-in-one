---
name: find-my-skills
description: Manage curated external skill repositories: clone or pull them outside the workspace, build a local catalog, and recommend matching skills for a described task. Use when the user mentions skill repos, syncing or updating skills, organizing many skills, 推荐 skill, 找 skill, or asks which skill fits a task.
---

# Find My Skills

## Purpose

Use this skill to keep a curated skill library usable over time:

1. Read a markdown repo list from `REPO_LSIT.md` by default.
2. Clone missing skill repositories to an external directory.
3. Update cloned repositories only when the user explicitly asks.
4. Build a local catalog of discovered skills and repo overviews.
5. Recommend the most relevant skills for a task the user describes.

## First Step

Always read `.cursor/skills/find-my-skills/config.json` before running commands.

## Rules

- Respect manual update mode. Do not pull remote repositories unless the user explicitly asks to sync, update, refresh, or clone the skill library.
- Keeping the catalog fresh is allowed without network access. If local repos changed, you may rebuild the catalog.
- Treat `REPO_LSIT.md` as the default canonical source list unless the user points to another file.
- Keep cloned repositories outside the workspace by using the configured `clone_root`.
- Prefer the provided script over ad-hoc shell logic so the workflow stays repeatable.

## Workflow

Copy this checklist when the task is more than a quick lookup:

```text
Task Progress:
- [ ] Confirm the intent: sync, index, recommend, or status
- [ ] Read config.json
- [ ] Run the matching script command
- [ ] Summarize results or recommendations
```

### 1. Sync Or Update Repos

Use this only when the user explicitly wants network changes.

```bash
python ".cursor/skills/find-my-skills/scripts/skill_manager.py" sync
```

After syncing, rebuild the catalog if the user wants the library organized or wants recommendations from the new repos:

```bash
python ".cursor/skills/find-my-skills/scripts/skill_manager.py" index
```

### 2. Rebuild The Local Catalog

Use this after local repo changes or when the catalog is missing:

```bash
python ".cursor/skills/find-my-skills/scripts/skill_manager.py" index
```

### 3. Check Current State

Use this to see whether repos are cloned and whether the catalog exists:

```bash
python ".cursor/skills/find-my-skills/scripts/skill_manager.py" status
```

### 4. Recommend Skills

When the user describes a task:

1. Distill the task into 3-6 short English search terms.
2. Run the recommender with those terms.
3. Explain the best matches in plain language.

```bash
python ".cursor/skills/find-my-skills/scripts/skill_manager.py" recommend --query "ppt corporate presentation deck"
```

If the catalog is missing, rebuild it first. Do not sync repos unless the user asked for syncing.

## Recommendation Format

When you reply with recommendations:

1. Give 2-5 candidates.
2. For each candidate, mention why it matches.
3. Include the source repo and the discovered file path.
4. Say clearly if the match is weak or if the local library needs syncing.

Use this shape:

```markdown
Recommended skills:
- `skill-or-repo-name`: why it matches the task. Source: `repo-name/path`
- `skill-or-repo-name`: why it is a fallback or complementary option. Source: `repo-name/path`
```

## Additional Resources

- Config reference: [reference.md](reference.md)
- Prompt examples: [examples.md](examples.md)
