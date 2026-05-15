#!/usr/bin/env python3
"""
scan_candidates.py — Pass 2 helper for the mdc-bug-patterns skill.

Walks the specialty-template directory (default: references/templates/),
parses every <specialty>.md file, extracts each template's detection_query
shell snippet, runs them against a target path, and emits a JSONL stream
of candidates that Pass 3 verifies.

Source-of-templates resolution (in order):
  --specialty NAME   → references/templates/NAME.md only
  --templates-md PATH→ a single .md file
  --templates-dir DIR→ every *.md inside DIR (default: references/templates/)

Usage:
    scan_candidates.py [--templates-dir DIR] [--specialty NAME]
                       [--templates-md PATH]
                       [--path SUBDIR] [--template ID]... [--out FILE]
                       [--list] [--dry-run]

Each line of the output JSONL has the shape:
    {"candidate_id": "<template_id>::<file>:<line>",
     "template_id":  "<template_id>",
     "specialty":    "<specialty-name (file stem) or '_root_' for top-level templates.md>",
     "file":         "<file>",
     "line":         <int>,
     "match":        "<matched line>",
     "rg_command":   "<the rg command that produced this hit>"}

The detection queries intentionally over-match (Pass 2 produces candidates,
not findings); Pass 3 narrows via the verification contract.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

DEFAULT_TEMPLATES_DIR = (
    Path(__file__).resolve().parent.parent / "references" / "templates"
)

# Matches "### `template-id`" headers and following body up to next "### " or H2.
TEMPLATE_HEADER_RE = re.compile(r"^###\s+`([^`]+)`\s*$", re.MULTILINE)
# A `**detection_query:**` line followed by one or more ```bash ... ``` blocks.
DETECTION_QUERY_RE = re.compile(
    r"(?m)^[ \t-]*\*\*detection_query:\*\*[ \t]*\n"
    r"((?:[ \t]*\n)?(?:[ \t]*```bash[ \t]*\n[\s\S]*?\n[ \t]*```[ \t]*\n?)+)"
)
BASH_BLOCK_RE = re.compile(r"```bash[ \t]*\n([\s\S]*?)\n[ \t]*```", re.MULTILINE)
# rg output line: "<file>:<line>:<text>"
RG_LINE_RE = re.compile(r"^([^:]+):(\d+):(.*)$")


@dataclass
class Template:
    template_id: str
    specialty: str  # file stem (e.g. "memory-safety") or "_root_"
    queries: list[str] = field(default_factory=list)


def parse_templates_in_file(md_path: Path, specialty: str) -> list[Template]:
    text = md_path.read_text(encoding="utf-8")
    headers = list(TEMPLATE_HEADER_RE.finditer(text))
    out: list[Template] = []
    for i, h in enumerate(headers):
        tid = h.group(1).strip()
        section_start = h.end()
        section_end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        section = text[section_start:section_end]

        m = DETECTION_QUERY_RE.search(section)
        queries: list[str] = []
        if m:
            for blk in BASH_BLOCK_RE.finditer(m.group(1)):
                snippet = blk.group(1).strip()
                # Collapse multi-line backslash-continued shell into one line.
                snippet = re.sub(r"\\\s*\n\s*", " ", snippet)
                queries.append(snippet)

        if queries:
            out.append(Template(template_id=tid, specialty=specialty, queries=queries))
    return out


def collect_templates(
    *,
    templates_md: Path | None,
    templates_dir: Path | None,
    specialty: str | None,
) -> list[Template]:
    """Resolve where templates come from based on the CLI flags."""
    if specialty:
        if templates_md or (templates_dir and not templates_dir.samefile(DEFAULT_TEMPLATES_DIR)):
            sys.stderr.write(
                "warn: --specialty is set; ignoring --templates-md / --templates-dir\n"
            )
        path = (templates_dir or DEFAULT_TEMPLATES_DIR) / f"{specialty}.md"
        if not path.exists():
            sys.stderr.write(f"specialty file not found: {path}\n")
            return []
        return parse_templates_in_file(path, specialty=specialty)

    if templates_md:
        return parse_templates_in_file(templates_md, specialty="_root_")

    dir_ = templates_dir or DEFAULT_TEMPLATES_DIR
    if not dir_.exists():
        sys.stderr.write(f"templates dir not found: {dir_}\n")
        return []
    out: list[Template] = []
    for path in sorted(dir_.glob("*.md")):
        out.extend(parse_templates_in_file(path, specialty=path.stem))
    return out


def run_query(query: str, target_path: Path) -> Iterable[tuple[str, int, str]]:
    """Run a shell rg query in `target_path`. Yields (file, line, text)."""
    # The query is the literal command from templates.md (e.g. starts with `rg`).
    # Run via /bin/sh so quoting/pipes work as written.
    proc = subprocess.run(
        query,
        shell=True,
        cwd=str(target_path),
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
    )
    # rg exit codes: 0 (matches), 1 (no matches), 2 (error).
    if proc.returncode not in (0, 1):
        sys.stderr.write(
            f"[scan_candidates] rg failed (exit {proc.returncode}) for query:\n"
            f"  {query}\nstderr:\n{proc.stderr}\n"
        )
        return
    for raw in proc.stdout.splitlines():
        m = RG_LINE_RE.match(raw)
        if not m:
            continue
        file_, line_s, text = m.group(1), m.group(2), m.group(3)
        try:
            line = int(line_s)
        except ValueError:
            continue
        yield file_, line, text


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--templates-dir", type=Path, default=DEFAULT_TEMPLATES_DIR,
                    help="Directory of specialty .md files (default: references/templates/).")
    ap.add_argument("--templates-md", type=Path, default=None,
                    help="Single .md file (back-compat / overrides --templates-dir).")
    ap.add_argument("--specialty", type=str, default=None,
                    help="Load only references/templates/<NAME>.md "
                         "(e.g. memory-safety, concurrency-and-isr, "
                         "resource-management, logic-and-numeric, "
                         "embedded-hardware).")
    ap.add_argument("--path", type=Path, default=Path("."),
                    help="Target codebase path (default: cwd).")
    ap.add_argument("--template", action="append", default=[],
                    help="Template id to run (repeatable). Default: all.")
    ap.add_argument("--out", type=Path, default=None,
                    help="Output JSONL file. Default: stdout.")
    ap.add_argument("--list", action="store_true",
                    help="List parsed templates (with specialty) and exit.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print queries that would run, then exit.")
    args = ap.parse_args(argv)

    templates = collect_templates(
        templates_md=args.templates_md,
        templates_dir=args.templates_dir,
        specialty=args.specialty,
    )
    if not templates:
        sys.stderr.write("no templates found\n")
        return 2

    if args.template:
        wanted = set(args.template)
        templates = [t for t in templates if t.template_id in wanted]
        missing = wanted - {t.template_id for t in templates}
        if missing:
            sys.stderr.write(f"unknown template(s): {sorted(missing)}\n")
            return 2

    if args.list:
        # Group by specialty for readability.
        from collections import defaultdict
        by_spec: dict[str, list[Template]] = defaultdict(list)
        for t in templates:
            by_spec[t.specialty].append(t)
        for spec in sorted(by_spec):
            print(f"# {spec}  ({len(by_spec[spec])} templates)")
            for t in by_spec[spec]:
                print(f"  {t.template_id}\t{len(t.queries)} query/queries")
        return 0

    if args.dry_run:
        for t in templates:
            for q in t.queries:
                print(f"# {t.specialty} :: {t.template_id}\n{q}\n")
        return 0

    target = args.path.resolve()
    if not target.exists():
        sys.stderr.write(f"target path does not exist: {target}\n")
        return 2

    out_fh = open(args.out, "w", encoding="utf-8") if args.out else sys.stdout
    total = 0
    per_template_counts: dict[str, int] = {}
    try:
        for t in templates:
            count = 0
            for q in t.queries:
                for file_, line, text in run_query(q, target):
                    rec = {
                        "candidate_id": f"{t.template_id}::{file_}:{line}",
                        "template_id": t.template_id,
                        "specialty": t.specialty,
                        "file": file_,
                        "line": line,
                        "match": text,
                        "rg_command": q,
                    }
                    out_fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    count += 1
                    total += 1
            per_template_counts[t.template_id] = count
    finally:
        if out_fh is not sys.stdout:
            out_fh.close()

    sys.stderr.write(
        f"\n[scan_candidates] {total} candidate(s) across "
        f"{len(per_template_counts)} template(s):\n"
    )
    for tid, n in sorted(per_template_counts.items(), key=lambda x: -x[1]):
        sys.stderr.write(f"  {n:6d}  {tid}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
