# Find My Skills Reference

## Config Keys

The default config lives in `.cursor/skills/find-my-skills/config.json`.

```json
{
  "repo_list_path": "REPO_LSIT.md",
  "clone_root": "~/.cursor/managed-skill-repos/repos",
  "state_root": "~/.cursor/managed-skill-repos/state",
  "scan_files": ["SKILL.md", "AGENTS.md"],
  "include_root_readme": true,
  "recommend_top_k": 6,
  "max_file_bytes": 20000
}
```

## What Each Key Means

- `repo_list_path`: Markdown file that contains the repo table. Relative paths are resolved from the workspace root.
- `clone_root`: External directory where repositories are cloned or updated.
- `state_root`: External directory where generated catalog files are written.
- `scan_files`: File names treated as skill definitions during indexing.
- `include_root_readme`: If true, root `README` files become fallback catalog entries when no skill files are found.
- `recommend_top_k`: Default number of recommendation candidates.
- `max_file_bytes`: Read limit for metadata extraction from discovered files.

## Generated Files

The script writes two files under `state_root`:

- `skill-catalog.json`: machine-readable catalog
- `skill-catalog.md`: quick human summary

## Supported Commands

```bash
python ".cursor/skills/find-my-skills/scripts/skill_manager.py" status
python ".cursor/skills/find-my-skills/scripts/skill_manager.py" sync
python ".cursor/skills/find-my-skills/scripts/skill_manager.py" index
python ".cursor/skills/find-my-skills/scripts/skill_manager.py" recommend --query "ppt corporate presentation deck"
```

## Repo List Format

The default parser expects a markdown table with at least two columns: repo name and repo URL.

```markdown
| skill-repo        | link                                 |
|-------------------|--------------------------------------|
| example-skills    | https://github.com/example/skills    |
| another-collection| https://github.com/acme/agent-skills |
```

Blank rows are ignored.
