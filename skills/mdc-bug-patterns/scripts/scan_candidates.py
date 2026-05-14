#!/usr/bin/env python3
"""
scan_candidates.py — Pass 2 helper for the mdc-bug-patterns skill.

Parses references/templates.md, extracts the `detection_query` shell snippet
for each template, runs them against a target path, and emits a JSONL stream
of candidates that Pass 3 verifies.

Usage:
    scan_candidates.py [--templates-md PATH] [--path SUBDIR]
                       [--template ID]... [--out FILE]
                       [--list] [--dry-run]

Each line of the output JSONL has the shape:
    {"candidate_id": "<template_id>::<file>:<line>",
     "template_id":  "<template_id>",
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

DEFAULT_TEMPLATES_MD = (
    Path(__file__).resolve().parent.parent / "references" / "templates.md"
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
    queries: list[str] = field(default_factory=list)


def parse_templates(md_path: Path) -> list[Template]:
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
            out.append(Template(template_id=tid, queries=queries))
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
    ap.add_argument("--templates-md", type=Path, default=DEFAULT_TEMPLATES_MD,
                    help="Path to templates.md (default: alongside the skill).")
    ap.add_argument("--path", type=Path, default=Path("."),
                    help="Target codebase path (default: cwd).")
    ap.add_argument("--template", action="append", default=[],
                    help="Template id to run (repeatable). Default: all.")
    ap.add_argument("--out", type=Path, default=None,
                    help="Output JSONL file. Default: stdout.")
    ap.add_argument("--list", action="store_true",
                    help="List parsed templates and exit.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print queries that would run, then exit.")
    args = ap.parse_args(argv)

    if not args.templates_md.exists():
        sys.stderr.write(f"templates.md not found: {args.templates_md}\n")
        return 2

    templates = parse_templates(args.templates_md)
    if args.template:
        wanted = set(args.template)
        templates = [t for t in templates if t.template_id in wanted]
        missing = wanted - {t.template_id for t in templates}
        if missing:
            sys.stderr.write(f"unknown template(s): {sorted(missing)}\n")
            return 2

    if args.list:
        for t in templates:
            print(f"{t.template_id}\t{len(t.queries)} query/queries")
        return 0

    if args.dry_run:
        for t in templates:
            for q in t.queries:
                print(f"# {t.template_id}\n{q}\n")
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
