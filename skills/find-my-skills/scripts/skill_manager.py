#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parents[1]
DEFAULT_CONFIG_PATH = SKILL_ROOT / "config.json"

DEFAULT_CONFIG: dict[str, Any] = {
    "repo_list_path": "REPO_LSIT.md",
    "clone_root": "~/.cursor/managed-skill-repos/repos",
    "state_root": "~/.cursor/managed-skill-repos/state",
    "scan_files": ["SKILL.md", "AGENTS.md"],
    "include_root_readme": True,
    "recommend_top_k": 6,
    "max_file_bytes": 20000,
}

IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "out",
    "coverage",
}

TOKEN_STOPWORDS = {
    "and",
    "the",
    "for",
    "with",
    "from",
    "this",
    "that",
    "into",
    "your",
    "their",
    "repo",
    "repos",
    "skill",
    "skills",
    "agent",
    "agents",
    "use",
    "using",
    "user",
    "when",
    "what",
    "which",
    "task",
    "tasks",
}


def detect_workspace_root() -> Path:
    candidates: list[Path] = []
    parents = SCRIPT_PATH.parents

    # Source repo layout: <repo>/skills/find-my-skills/scripts/skill_manager.py
    if len(parents) >= 4 and parents[1].name == "find-my-skills" and parents[2].name == "skills":
        candidates.append(parents[3])

    # Installed project skill layout: <workspace>/.cursor/skills/find-my-skills/scripts/skill_manager.py
    if (
        len(parents) >= 5
        and parents[1].name == "find-my-skills"
        and parents[2].name == "skills"
        and parents[3].name == ".cursor"
    ):
        candidates.append(parents[4])

    candidates.append(Path.cwd().resolve())

    seen: set[Path] = set()
    unique_candidates: list[Path] = []
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        unique_candidates.append(candidate)

    for candidate in unique_candidates:
        if (candidate / "REPO_LSIT.md").exists():
            return candidate

    return unique_candidates[0]


WORKSPACE_ROOT = detect_workspace_root()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def eprint(message: str) -> None:
    print(message, file=sys.stderr)


def resolve_workspace_path(raw_path: str | Path) -> Path:
    path = Path(os.path.expandvars(os.path.expanduser(str(raw_path))))
    if not path.is_absolute():
        path = WORKSPACE_ROOT / path
    return path.resolve()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_config(config_arg: str | None) -> dict[str, Any]:
    config_path = resolve_workspace_path(config_arg) if config_arg else DEFAULT_CONFIG_PATH
    config_data: dict[str, Any] = {}
    if config_path.exists():
        config_data = load_json(config_path)

    config: dict[str, Any] = {**DEFAULT_CONFIG, **config_data}
    config["config_path"] = config_path
    config["repo_list_path"] = resolve_workspace_path(config["repo_list_path"])
    config["clone_root"] = resolve_workspace_path(config["clone_root"])
    config["state_root"] = resolve_workspace_path(config["state_root"])
    config["catalog_json_path"] = config["state_root"] / "skill-catalog.json"
    config["catalog_markdown_path"] = config["state_root"] / "skill-catalog.md"
    config["scan_files"] = [str(name).strip() for name in config.get("scan_files", []) if str(name).strip()]
    config["include_root_readme"] = bool(config.get("include_root_readme", True))
    config["recommend_top_k"] = int(config.get("recommend_top_k", 6))
    config["max_file_bytes"] = int(config.get("max_file_bytes", 20000))
    return config


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip().lower())
    value = value.strip("-.")
    return value or "repo"


def parse_repo_list(repo_list_path: Path) -> list[dict[str, str]]:
    if not repo_list_path.exists():
        raise FileNotFoundError(f"Repo list not found: {repo_list_path}")

    repos: list[dict[str, str]] = []
    seen: dict[str, int] = {}

    for raw_line in repo_list_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line.startswith("|"):
            continue

        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2:
            continue

        display_name, url = cells[0], cells[1]
        if not display_name or not url:
            continue
        if display_name.lower() == "skill-repo" or url.lower() == "link":
            continue
        if set(display_name.replace(" ", "")) == {"-"}:
            continue
        if not re.match(r"https?://", url):
            continue

        base_slug = slugify(display_name)
        seen[base_slug] = seen.get(base_slug, 0) + 1
        dir_name = base_slug if seen[base_slug] == 1 else f"{base_slug}-{seen[base_slug]}"
        repos.append(
            {
                "display_name": display_name,
                "url": url,
                "dir_name": dir_name,
            }
        )

    return repos


def run_git(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        check=False,
    )


def shorten_output(text: str, max_lines: int = 8) -> str:
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    if len(lines) <= max_lines:
        return "\n".join(lines)
    return "\n".join(lines[:max_lines] + ["..."])


def read_limited_text(path: Path, max_bytes: int) -> str:
    raw = path.read_bytes()[:max_bytes]
    return raw.decode("utf-8", errors="ignore")


def split_frontmatter(text: str) -> tuple[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return "", text

    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            frontmatter = "\n".join(lines[1:index])
            body = "\n".join(lines[index + 1 :])
            return frontmatter, body

    return "", text


def strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def parse_simple_frontmatter(frontmatter: str) -> dict[str, str]:
    data: dict[str, str] = {}
    lines = frontmatter.splitlines()
    index = 0

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in line:
            index += 1
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if value in {">", ">-", "|", "|-"}:
            index += 1
            block: list[str] = []
            while index < len(lines):
                nested = lines[index]
                if nested.startswith(" ") or nested.startswith("\t"):
                    block.append(nested.strip())
                    index += 1
                    continue
                break
            data[key] = " ".join(block).strip()
            continue

        data[key] = strip_quotes(value)
        index += 1

    return data


def extract_title(body: str, metadata: dict[str, str], file_path: Path) -> str:
    for key in ("title", "name"):
        value = metadata.get(key, "").strip()
        if value:
            return value

    for raw_line in body.splitlines():
        line = raw_line.strip()
        if line.startswith("# "):
            return line[2:].strip()

    if file_path.name.lower() in {"skill.md", "agents.md"}:
        return file_path.parent.name
    return file_path.stem


def extract_summary(body: str, metadata: dict[str, str]) -> str:
    description = metadata.get("description", "").strip()
    if description:
        return description[:320]

    lines: list[str] = []
    in_code_block = False
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if line.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block or not line:
            if lines:
                break
            continue
        if line.startswith("#"):
            continue
        if line.startswith(("- ", "* ")):
            line = line[2:].strip()
        lines.append(line)
        if len(" ".join(lines)) >= 320:
            break

    return " ".join(lines)[:320]


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for raw in re.findall(r"[a-z0-9][a-z0-9+._/-]*", text.lower()):
        for piece in re.split(r"[+._/\-]", raw):
            piece = piece.strip()
            if len(piece) < 3 or piece in TOKEN_STOPWORDS:
                continue
            tokens.append(piece)

    deduped: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        if token in seen:
            continue
        seen.add(token)
        deduped.append(token)
    return deduped


def build_entry(repo: dict[str, str], repo_path: Path, file_path: Path, max_file_bytes: int) -> dict[str, Any]:
    text = read_limited_text(file_path, max_file_bytes)
    frontmatter, body = split_frontmatter(text)
    metadata = parse_simple_frontmatter(frontmatter)
    title = extract_title(body, metadata, file_path)
    description = extract_summary(body, metadata)
    relative_path = file_path.relative_to(repo_path).as_posix()
    kind = "readme"
    lower_name = file_path.name.lower()
    if lower_name == "skill.md":
        kind = "skill"
    elif lower_name == "agents.md":
        kind = "agents"

    keywords = tokenize(" ".join([repo["display_name"], title, description, relative_path]))

    return {
        "repo_name": repo["display_name"],
        "repo_url": repo["url"],
        "repo_dir": repo["dir_name"],
        "repo_path": str(repo_path),
        "kind": kind,
        "title": title,
        "description": description,
        "relative_path": relative_path,
        "file_path": str(file_path),
        "keywords": keywords,
    }


def discover_files(repo_path: Path, scan_files: list[str], include_root_readme: bool) -> tuple[list[Path], Path | None]:
    wanted = {name.lower() for name in scan_files}
    skill_files: list[Path] = []
    root_readme: Path | None = None

    for current_root, dirnames, filenames in os.walk(repo_path):
        dirnames[:] = [name for name in dirnames if name not in IGNORE_DIRS]
        current_path = Path(current_root)

        for filename in filenames:
            lower_name = filename.lower()
            full_path = current_path / filename
            if lower_name in wanted:
                skill_files.append(full_path)
            if include_root_readme and current_path == repo_path and lower_name.startswith("readme") and root_readme is None:
                root_readme = full_path

    return skill_files, root_readme


def index_repo(repo: dict[str, str], config: dict[str, Any]) -> list[dict[str, Any]]:
    repo_path = config["clone_root"] / repo["dir_name"]
    if not repo_path.exists():
        return []

    skill_files, root_readme = discover_files(
        repo_path=repo_path,
        scan_files=config["scan_files"],
        include_root_readme=config["include_root_readme"],
    )

    entries = [
        build_entry(repo, repo_path, file_path, config["max_file_bytes"])
        for file_path in sorted(skill_files)
    ]

    if not entries and root_readme:
        entries.append(build_entry(repo, repo_path, root_readme, config["max_file_bytes"]))

    return entries


def write_catalog(config: dict[str, Any], repos: list[dict[str, str]], entries: list[dict[str, Any]]) -> None:
    config["state_root"].mkdir(parents=True, exist_ok=True)

    payload = {
        "generated_at": utc_now(),
        "workspace_root": str(WORKSPACE_ROOT),
        "repo_list_path": str(config["repo_list_path"]),
        "repo_count": len(repos),
        "entry_count": len(entries),
        "entries": entries,
    }

    config["catalog_json_path"].write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    markdown_lines = [
        "# Skill Catalog",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Repo count: `{payload['repo_count']}`",
        f"- Entry count: `{payload['entry_count']}`",
        "",
    ]

    for entry in entries:
        markdown_lines.extend(
            [
                f"## {entry['title']}",
                "",
                f"- Repo: `{entry['repo_name']}`",
                f"- Kind: `{entry['kind']}`",
                f"- File: `{entry['relative_path']}`",
                f"- URL: {entry['repo_url']}",
                f"- Summary: {entry['description'] or 'No summary extracted.'}",
                "",
            ]
        )

    config["catalog_markdown_path"].write_text("\n".join(markdown_lines), encoding="utf-8")


def load_catalog(config: dict[str, Any]) -> dict[str, Any] | None:
    catalog_path = config["catalog_json_path"]
    if not catalog_path.exists():
        return None
    return load_json(catalog_path)


def command_status(config: dict[str, Any]) -> int:
    repos = parse_repo_list(config["repo_list_path"])
    cloned = 0
    missing = 0

    for repo in repos:
        repo_path = config["clone_root"] / repo["dir_name"]
        if repo_path.exists():
            cloned += 1
        else:
            missing += 1

    print(f"Workspace root: {WORKSPACE_ROOT}")
    print(f"Config path: {config['config_path']}")
    print(f"Repo list: {config['repo_list_path']}")
    print(f"Clone root: {config['clone_root']}")
    print(f"State root: {config['state_root']}")
    print(f"Configured repos: {len(repos)}")
    print(f"Cloned repos: {cloned}")
    print(f"Missing repos: {missing}")

    catalog = load_catalog(config)
    if catalog:
        print(f"Catalog generated at: {catalog.get('generated_at', 'unknown')}")
        print(f"Catalog entries: {catalog.get('entry_count', 0)}")
        print(f"Catalog JSON: {config['catalog_json_path']}")
        print(f"Catalog Markdown: {config['catalog_markdown_path']}")
    else:
        print("Catalog: missing")

    return 0


def command_sync(config: dict[str, Any]) -> int:
    repos = parse_repo_list(config["repo_list_path"])
    config["clone_root"].mkdir(parents=True, exist_ok=True)

    cloned = 0
    updated = 0
    failed = 0
    skipped = 0

    for repo in repos:
        repo_path = config["clone_root"] / repo["dir_name"]
        if repo_path.exists():
            if not (repo_path / ".git").exists():
                print(f"[skip] {repo['display_name']}: existing directory is not a git repo -> {repo_path}")
                skipped += 1
                continue

            result = run_git(["-C", str(repo_path), "pull", "--ff-only"])
            if result.returncode == 0:
                print(f"[updated] {repo['display_name']} -> {repo_path}")
                updated += 1
            else:
                print(f"[failed] {repo['display_name']} -> {repo_path}")
                details = shorten_output(result.stderr or result.stdout)
                if details:
                    print(details)
                failed += 1
            continue

        result = run_git(["clone", "--depth", "1", repo["url"], str(repo_path)])
        if result.returncode == 0:
            print(f"[cloned] {repo['display_name']} -> {repo_path}")
            cloned += 1
        else:
            print(f"[failed] {repo['display_name']} -> {repo_path}")
            details = shorten_output(result.stderr or result.stdout)
            if details:
                print(details)
            failed += 1

    print("")
    print(f"Sync summary: cloned={cloned}, updated={updated}, skipped={skipped}, failed={failed}")
    return 1 if failed else 0


def command_index(config: dict[str, Any]) -> int:
    repos = parse_repo_list(config["repo_list_path"])
    entries: list[dict[str, Any]] = []
    indexed_repos = 0
    missing_repos: list[str] = []

    for repo in repos:
        repo_path = config["clone_root"] / repo["dir_name"]
        if not repo_path.exists():
            missing_repos.append(repo["display_name"])
            continue

        repo_entries = index_repo(repo, config)
        entries.extend(repo_entries)
        indexed_repos += 1
        print(f"[indexed] {repo['display_name']}: {len(repo_entries)} entries")

    write_catalog(config, repos, entries)

    print("")
    print(f"Index summary: indexed_repos={indexed_repos}, missing_repos={len(missing_repos)}, entries={len(entries)}")
    print(f"Catalog JSON: {config['catalog_json_path']}")
    print(f"Catalog Markdown: {config['catalog_markdown_path']}")

    if missing_repos:
        print("Missing repos:")
        for name in missing_repos:
            print(f"- {name}")

    return 0


def rank_entries(entries: list[dict[str, Any]], query_tokens: list[str]) -> list[tuple[int, dict[str, Any], list[str]]]:
    scored_entries: list[tuple[int, dict[str, Any], list[str]]] = []
    for entry in entries:
        score, reasons = score_entry(entry, query_tokens)
        if score > 0:
            scored_entries.append((score, entry, reasons))

    scored_entries.sort(key=lambda item: (-item[0], item[1].get("repo_name", ""), item[1].get("title", "")))
    return scored_entries


def command_find_skills(config: dict[str, Any], query: str | None, top_k: int | None) -> int:
    catalog = load_catalog(config)
    if not catalog:
        eprint("Catalog missing. Run the index command first.")
        return 1

    entries = list(catalog.get("entries", []))
    if not entries:
        eprint("Catalog is empty. Run the index command again after syncing repos.")
        return 1

    if query:
        query_tokens = tokenize(query)
        if not query_tokens:
            eprint("No searchable English keywords were found in the query.")
            return 1

        ranked_entries = rank_entries(entries, query_tokens)
        if not ranked_entries:
            eprint("No matching skills found in the local catalog.")
            return 0

        limit = top_k or config["recommend_top_k"]
        for _, entry, _ in ranked_entries[:limit]:
            print(entry["file_path"])
        return 0

    entries.sort(key=lambda entry: (entry.get("repo_name", ""), entry.get("relative_path", ""), entry.get("title", "")))
    if top_k:
        entries = entries[:top_k]

    for entry in entries:
        print(entry["file_path"])

    return 0


def score_entry(entry: dict[str, Any], query_tokens: list[str]) -> tuple[int, list[str]]:
    title = entry.get("title", "").lower()
    description = entry.get("description", "").lower()
    relative_path = entry.get("relative_path", "").lower()
    repo_name = entry.get("repo_name", "").lower()
    keywords = set(entry.get("keywords", []))

    score = 0
    reasons: list[str] = []

    for token in query_tokens:
        if token in title:
            score += 6
            reasons.append(f"title:{token}")
        if token in repo_name:
            score += 4
            reasons.append(f"repo:{token}")
        if token in relative_path:
            score += 3
            reasons.append(f"path:{token}")
        if token in description:
            score += 2
            reasons.append(f"summary:{token}")
        if token in keywords:
            score += 2

    deduped_reasons: list[str] = []
    seen: set[str] = set()
    for reason in reasons:
        if reason in seen:
            continue
        seen.add(reason)
        deduped_reasons.append(reason)

    return score, deduped_reasons


def command_recommend(config: dict[str, Any], query: str, top_k: int | None) -> int:
    catalog = load_catalog(config)
    if not catalog:
        eprint("Catalog missing. Run the index command first.")
        return 1

    query_tokens = tokenize(query)
    if not query_tokens:
        eprint("No searchable English keywords were found in the query.")
        return 1

    scored_entries = rank_entries(list(catalog.get("entries", [])), query_tokens)
    limit = top_k or config["recommend_top_k"]

    print(f"Query tokens: {', '.join(query_tokens)}")

    if not scored_entries:
        print("No strong local match found.")
        print("Try broader English keywords or sync more repos before recommending again.")
        return 0

    for rank, (score, entry, reasons) in enumerate(scored_entries[:limit], start=1):
        print(f"{rank}. {entry['title']} | repo={entry['repo_name']} | kind={entry['kind']} | score={score}")
        print(f"   file: {entry['relative_path']}")
        if entry.get("description"):
            print(f"   summary: {entry['description']}")
        if reasons:
            print(f"   matched: {', '.join(reasons)}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage and recommend external skill repositories.")
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to the config JSON file. Relative paths resolve from the workspace root.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status", help="Show current repo and catalog status.")
    subparsers.add_parser("sync", help="Clone missing repos and pull existing repos.")
    subparsers.add_parser("index", help="Build the local skill catalog from cloned repos.")
    find_skills = subparsers.add_parser(
        "find-skills",
        help="Print full local skill paths, optionally filtered by query.",
    )
    find_skills.add_argument(
        "--query",
        default=None,
        help="Optional English search keywords to filter matching skill paths.",
    )
    find_skills.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Limit the number of printed paths.",
    )

    recommend = subparsers.add_parser("recommend", help="Recommend skills from the local catalog.")
    recommend.add_argument("--query", required=True, help="English search keywords for the desired task.")
    recommend.add_argument("--top-k", type=int, default=None, help="Override the configured result count.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
        if args.command == "status":
            return command_status(config)
        if args.command == "sync":
            return command_sync(config)
        if args.command == "index":
            return command_index(config)
        if args.command == "find-skills":
            return command_find_skills(config, args.query, args.top_k)
        if args.command == "recommend":
            return command_recommend(config, args.query, args.top_k)
        parser.error(f"Unknown command: {args.command}")
        return 2
    except FileNotFoundError as exc:
        eprint(str(exc))
        return 1
    except json.JSONDecodeError as exc:
        eprint(f"Invalid JSON: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
