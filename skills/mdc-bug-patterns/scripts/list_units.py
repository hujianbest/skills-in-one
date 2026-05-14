#!/usr/bin/env python3
"""
list_units.py — Pass 2 helper for the mdc-bug-patterns skill.

Aggregates the candidate JSONL produced by scan_candidates.py into a
ranked list of code units (functions / methods / small files).

A "unit" is the smallest enclosing function or method that contains a
candidate. When function detection fails, the file itself becomes the
unit. Files larger than --file-unit-max LoC (default 200) are not used
as units; only their functions are.

Suspicion signals combined into the score:
  * count and severity of template hits inside the unit
  * presence of concurrency primitives (mutex, atomic, condvar, thread)
  * presence of raw memory primitives (new/delete/malloc/memcpy/...)
  * very small or very large units get a small bump (bug hiding spots)

Output (JSONL or human table):

    {
      "unit_id": "src/cache.cc::Cache::Insert",
      "file":    "src/cache.cc",
      "kind":    "function",
      "line_start": 80,
      "line_end":   110,
      "score":   17.5,
      "signals": ["mem-leak-new-no-delete::3",
                  "con-unsynchronized-shared-write::1",
                  "primitive:std::mutex",
                  "primitive:new",
                  "size:31"],
      "candidates": ["mem-leak-new-no-delete::src/cache.cc:88", ...]
    }

Usage:
    list_units.py --candidates candidates.jsonl --path . [--out units.jsonl]
                  [--templates-md PATH] [--top N] [--format jsonl|table]
                  [--file-unit-max LOC]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# Severity weights (template default; can be overridden by user later).
SEVERITY_WEIGHT = {"critical": 5.0, "high": 3.0, "medium": 2.0, "low": 1.0}
DEFAULT_SEVERITY = "high"

# Template metadata is optional — used to weight by severity.
TEMPLATE_HEADER_RE = re.compile(r"^###\s+`([^`]+)`\s*$", re.MULTILINE)
SEVERITY_FIELD_RE = re.compile(
    r"^\*\*severity:\*\*\s*([a-z]+)", re.MULTILINE | re.IGNORECASE
)

# Function definition heuristic: matches lines like
#   ReturnType Class::Method(...) {
#   void func(...) {
#   static inline T func(...)
# We capture the line number and the qualified name.
FUNC_DEF_RE = re.compile(
    r"""
    ^[ \t]*                              # indent
    (?:template\s*<[^>]*>\s*)?           # optional template<>
    (?:(?:static|inline|virtual|explicit|constexpr|friend|extern\s+"C"|\[\[[^\]]+\]\])\s+)*
    (?:[A-Za-z_][\w:<>,\s\*&]*?\s+)?     # return type (may be missing for ctor)
    ([A-Za-z_]\w*(?:::~?[A-Za-z_]\w*)*)  # qualified name
    \s*\([^;{}]*\)                       # parameter list
    (?:\s*(?:const|noexcept|override|final|=\s*default|=\s*delete|->\s*[A-Za-z_][\w:<>,\s\*&]*|:\s*[^{;]+))*
    \s*\{                                # opening brace on same line (or after init list)
    """,
    re.VERBOSE | re.MULTILINE,
)

CONCURRENCY_PRIMITIVES = (
    r"std::thread", r"pthread_create", r"std::async",
    r"std::mutex", r"std::shared_mutex", r"std::recursive_mutex",
    r"std::lock_guard", r"std::unique_lock", r"std::scoped_lock",
    r"std::atomic", r"std::condition_variable", r"absl::Mutex",
)
MEMORY_PRIMITIVES = (
    r"\bnew\b", r"\bdelete\b", r"\bmalloc\b", r"\bcalloc\b",
    r"\brealloc\b", r"\bfree\b", r"\bmemcpy\b", r"\bmemmove\b",
    r"\bmemset\b", r"\bstrcpy\b", r"\bstrcat\b", r"\bsprintf\b",
)
CONCURRENCY_RE = re.compile("|".join(CONCURRENCY_PRIMITIVES))
MEMORY_RE = re.compile("|".join(MEMORY_PRIMITIVES))


@dataclass
class Function:
    file: str
    name: str
    line_start: int
    line_end: int  # exclusive (next-line after closing brace)
    text: str = ""

    @property
    def size(self) -> int:
        return max(1, self.line_end - self.line_start)

    @property
    def unit_id(self) -> str:
        return f"{self.file}::{self.name}"


@dataclass
class Unit:
    unit_id: str
    file: str
    kind: str           # "function" or "file"
    line_start: int
    line_end: int
    score: float = 0.0
    signals: list[str] = field(default_factory=list)
    candidates: list[str] = field(default_factory=list)


def load_template_severity(md_path: Path | None) -> dict[str, str]:
    """Return {template_id: severity_lowercase}. Empty if md_path missing."""
    if not md_path or not md_path.exists():
        return {}
    text = md_path.read_text(encoding="utf-8")
    headers = list(TEMPLATE_HEADER_RE.finditer(text))
    out: dict[str, str] = {}
    for i, h in enumerate(headers):
        tid = h.group(1).strip()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        section = text[h.end():end]
        m = SEVERITY_FIELD_RE.search(section)
        if m:
            out[tid] = m.group(1).strip().lower()
    return out


def find_functions(file_path: Path) -> list[Function]:
    """Heuristic function-boundary extraction via brace counting."""
    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    lines = text.splitlines()
    funcs: list[Function] = []
    for m in FUNC_DEF_RE.finditer(text):
        start_off = m.start()
        line_start = text.count("\n", 0, start_off) + 1
        # Find the matching closing brace by counting braces from m.end()-1.
        depth = 0
        end_off = m.end()
        for i in range(m.end() - 1, len(text)):
            c = text[i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    end_off = i + 1
                    break
        line_end = text.count("\n", 0, end_off) + 1
        if line_end <= line_start:
            continue
        body = "\n".join(lines[line_start - 1: line_end])
        funcs.append(Function(
            file=str(file_path),
            name=m.group(1),
            line_start=line_start,
            line_end=line_end,
            text=body,
        ))
    return funcs


def load_candidates(path: Path) -> list[dict]:
    out = []
    with open(path, "r", encoding="utf-8") as fh:
        for ln, raw in enumerate(fh, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                out.append(json.loads(raw))
            except json.JSONDecodeError as e:
                sys.stderr.write(f"skip line {ln}: {e}\n")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--candidates", type=Path, required=True,
                    help="JSONL produced by scan_candidates.py.")
    ap.add_argument("--path", type=Path, default=Path("."),
                    help="Codebase root used to read source files.")
    ap.add_argument("--templates-md", type=Path,
                    default=Path(__file__).resolve().parent.parent /
                            "references" / "templates.md",
                    help="Templates markdown (used for severity weights).")
    ap.add_argument("--out", type=Path, help="Output JSONL (default: stdout).")
    ap.add_argument("--top", type=int, default=0,
                    help="Show only top-N units (0 = all).")
    ap.add_argument("--format", choices=("jsonl", "table"), default="jsonl",
                    help="Output format.")
    ap.add_argument("--file-unit-max", type=int, default=200,
                    help="Max LoC for file-as-unit fallback.")
    args = ap.parse_args(argv)

    if not args.candidates.exists():
        sys.stderr.write(f"candidates file not found: {args.candidates}\n")
        return 2
    if not args.path.exists():
        sys.stderr.write(f"codebase path not found: {args.path}\n")
        return 2

    candidates = load_candidates(args.candidates)
    if not candidates:
        sys.stderr.write("no candidates loaded\n")
        return 0

    severity = load_template_severity(args.templates_md)
    base = args.path.resolve()

    # Group candidates by file (relative path as written by rg).
    per_file: dict[str, list[dict]] = defaultdict(list)
    for c in candidates:
        f = c.get("file") or ""
        if f.startswith("./"):
            f = f[2:]
        per_file[f].append(c)

    units: dict[str, Unit] = {}

    for rel_file, cs in per_file.items():
        abs_file = (base / rel_file).resolve()
        if not abs_file.exists() or not abs_file.is_file():
            # File may have been excluded post-scan; treat as file-level unit.
            uid = rel_file
            units[uid] = Unit(unit_id=uid, file=rel_file, kind="file",
                              line_start=1, line_end=1)
            for c in cs:
                units[uid].candidates.append(c.get("candidate_id", ""))
            continue

        functions = find_functions(abs_file)
        try:
            n_lines = sum(1 for _ in open(abs_file, "r", encoding="utf-8",
                                          errors="replace"))
        except OSError:
            n_lines = 0

        if not functions:
            uid = rel_file
            kind = "file"
            ls, le = 1, n_lines or 1
            text = abs_file.read_text(encoding="utf-8", errors="replace")
            unit = units.setdefault(uid, Unit(unit_id=uid, file=rel_file,
                                              kind=kind,
                                              line_start=ls, line_end=le))
            _add_signals(unit, text, severity)
            for c in cs:
                _absorb_candidate(unit, c, severity)
            continue

        functions.sort(key=lambda f: f.line_start)
        for c in cs:
            line = int(c.get("line", 0) or 0)
            host = next(
                (f for f in functions if f.line_start <= line < f.line_end),
                None,
            )
            if host is None:
                # Out of any function: file-as-unit (only if small enough).
                if n_lines <= args.file_unit_max:
                    uid = rel_file
                    unit = units.setdefault(uid, Unit(
                        unit_id=uid, file=rel_file, kind="file",
                        line_start=1, line_end=n_lines or 1,
                    ))
                    if not unit.signals:
                        _add_signals(unit, abs_file.read_text(
                            encoding="utf-8", errors="replace"), severity)
                    _absorb_candidate(unit, c, severity)
                else:
                    # Too large to use as a unit; record as audit gap candidate.
                    uid = f"{rel_file}::<file-too-large>"
                    unit = units.setdefault(uid, Unit(
                        unit_id=uid, file=rel_file, kind="file",
                        line_start=1, line_end=n_lines or 1,
                    ))
                    _absorb_candidate(unit, c, severity)
            else:
                uid = host.unit_id
                unit = units.setdefault(uid, Unit(
                    unit_id=uid, file=rel_file, kind="function",
                    line_start=host.line_start, line_end=host.line_end,
                ))
                if not unit.signals:
                    _add_signals(unit, host.text, severity)
                _absorb_candidate(unit, c, severity)

    # Final size signal.
    for u in units.values():
        size = max(1, u.line_end - u.line_start)
        u.signals.append(f"size:{size}")
        if size <= 5:
            u.score += 0.5
        elif size >= 250:
            u.score += 1.0

    sorted_units = sorted(units.values(), key=lambda u: -u.score)
    if args.top > 0:
        sorted_units = sorted_units[: args.top]

    if args.format == "table":
        _render_table(sorted_units)
    else:
        _render_jsonl(sorted_units, args.out)

    sys.stderr.write(
        f"\n[list_units] {len(units)} unit(s); "
        f"{sum(1 for u in units.values() if u.kind == 'function')} function(s), "
        f"{sum(1 for u in units.values() if u.kind == 'file')} file-level\n"
    )
    return 0


def _absorb_candidate(unit: Unit, c: dict, severity: dict[str, str]) -> None:
    tid = c.get("template_id", "")
    cid = c.get("candidate_id", "")
    sev = severity.get(tid, DEFAULT_SEVERITY).lower()
    unit.candidates.append(cid)
    unit.score += SEVERITY_WEIGHT.get(sev, SEVERITY_WEIGHT[DEFAULT_SEVERITY])
    # Compress signals: count per template.
    existing = next(
        (i for i, s in enumerate(unit.signals) if s.startswith(tid + "::")),
        None,
    )
    if existing is None:
        unit.signals.append(f"{tid}::1")
    else:
        prev = unit.signals[existing]
        n = int(prev.split("::")[-1]) + 1
        unit.signals[existing] = f"{tid}::{n}"


def _add_signals(unit: Unit, text: str, severity: dict[str, str]) -> None:
    if CONCURRENCY_RE.search(text):
        unit.signals.append("primitive:concurrency")
        unit.score += 1.5
    if MEMORY_RE.search(text):
        unit.signals.append("primitive:memory")
        unit.score += 1.0


def _render_table(units: list[Unit]) -> None:
    print(f"{'score':>7}  {'kind':8}  {'lines':>10}  unit_id")
    print(f"{'-' * 7}  {'-' * 8}  {'-' * 10}  {'-' * 40}")
    for u in units:
        lines = f"{u.line_start}-{u.line_end}"
        print(f"{u.score:7.2f}  {u.kind:8}  {lines:>10}  {u.unit_id}")


def _render_jsonl(units: list[Unit], out_path: Path | None) -> None:
    fh = open(out_path, "w", encoding="utf-8") if out_path else sys.stdout
    try:
        for u in units:
            rec = {
                "unit_id": u.unit_id,
                "file": u.file,
                "kind": u.kind,
                "line_start": u.line_start,
                "line_end": u.line_end,
                "score": round(u.score, 2),
                "signals": u.signals,
                "candidates": u.candidates,
            }
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    finally:
        if fh is not sys.stdout:
            fh.close()


if __name__ == "__main__":
    sys.exit(main())
