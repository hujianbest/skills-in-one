#!/usr/bin/env python3
"""
coverage_tracker.py — Pass 2/3/4 bookkeeping for the mdc-bug-patterns skill.

Maintains a single JSON file (default: coverage.json) tracking every candidate
discovered in Pass 2 and the verification outcome assigned in Pass 3.

Subcommands:
    register   --candidates FILE         Add Pass 2 candidates (JSONL).
    mark       --id ID --status STATUS   Mark a candidate as
                                         confirmed | suppressed | inconclusive.
                                         Optional: --filter ID, --reason TEXT,
                                                   --confidence high|medium|low,
                                                   --note TEXT.
    summary                              Print a per-template coverage table
                                         + totals to stdout.
    audit-gaps                           Print inconclusive + un-marked
                                         candidates (these are the gaps in
                                         Pass 4 reporting).
    findings   --out FILE                Dump confirmed candidates as JSON
                                         (a starting point for Pass 4).

Each candidate is keyed by `candidate_id` ("<template_id>::<file>:<line>").
Statuses are open by default (i.e. recorded by `register` but not yet marked).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

DEFAULT_DB = Path("coverage.json")
VALID_STATUS = {"open", "confirmed", "suppressed", "inconclusive"}
VALID_CONFIDENCE = {"high", "medium", "low"}


def load(db_path: Path) -> dict[str, Any]:
    if db_path.exists():
        return json.loads(db_path.read_text(encoding="utf-8"))
    return {"candidates": {}}


def save(db_path: Path, data: dict[str, Any]) -> None:
    db_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")


def cmd_register(args: argparse.Namespace) -> int:
    data = load(args.db)
    new_count = 0
    with open(args.candidates, "r", encoding="utf-8") as fh:
        for ln, raw in enumerate(fh, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError as e:
                sys.stderr.write(f"skip line {ln}: {e}\n")
                continue
            cid = rec.get("candidate_id")
            if not cid:
                sys.stderr.write(f"skip line {ln}: missing candidate_id\n")
                continue
            if cid in data["candidates"]:
                continue
            data["candidates"][cid] = {
                "template_id": rec.get("template_id"),
                "file": rec.get("file"),
                "line": rec.get("line"),
                "match": rec.get("match"),
                "status": "open",
            }
            new_count += 1
    save(args.db, data)
    print(f"registered {new_count} new candidate(s); "
          f"total {len(data['candidates'])}")
    return 0


def cmd_mark(args: argparse.Namespace) -> int:
    data = load(args.db)
    if args.id not in data["candidates"]:
        sys.stderr.write(f"unknown candidate_id: {args.id}\n")
        return 2
    if args.status not in VALID_STATUS:
        sys.stderr.write(f"status must be one of {sorted(VALID_STATUS)}\n")
        return 2
    if args.status == "suppressed" and not args.filter:
        sys.stderr.write(
            "suppressed status REQUIRES --filter (the FP filter id from "
            "references/false-positive-filters.md)\n"
        )
        return 2
    if args.confidence and args.confidence not in VALID_CONFIDENCE:
        sys.stderr.write(f"confidence must be one of {sorted(VALID_CONFIDENCE)}\n")
        return 2

    entry = data["candidates"][args.id]
    entry["status"] = args.status
    if args.filter:
        entry["filter"] = args.filter
    if args.reason:
        entry["reason"] = args.reason
    if args.confidence:
        entry["confidence"] = args.confidence
    if args.note:
        entry["note"] = args.note
    save(args.db, data)
    print(f"marked {args.id} as {args.status}")
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    data = load(args.db)
    per_t: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for c in data["candidates"].values():
        t = c.get("template_id") or "<unknown>"
        per_t[t][c.get("status", "open")] += 1

    cols = ("template_id", "candidates", "confirmed",
            "suppressed", "inconclusive", "open", "coverage")
    rows = []
    totals = defaultdict(int)
    for t, counts in sorted(per_t.items()):
        candidates = sum(counts.values())
        confirmed = counts.get("confirmed", 0)
        suppressed = counts.get("suppressed", 0)
        inconclusive = counts.get("inconclusive", 0)
        open_ = counts.get("open", 0)
        coverage = ((confirmed + suppressed) / candidates * 100.0) if candidates else 0
        rows.append((t, candidates, confirmed, suppressed,
                     inconclusive, open_, f"{coverage:5.1f}%"))
        totals["candidates"] += candidates
        totals["confirmed"] += confirmed
        totals["suppressed"] += suppressed
        totals["inconclusive"] += inconclusive
        totals["open"] += open_

    if not rows:
        print("(no candidates registered)")
        return 0

    widths = [max(len(str(r[i])) for r in rows + [cols]) for i in range(len(cols))]
    fmt = "  ".join(f"{{:{w}}}" for w in widths)
    print(fmt.format(*cols))
    print("  ".join("-" * w for w in widths))
    for r in rows:
        print(fmt.format(*[str(x) for x in r]))
    print()
    cov_total = ((totals["confirmed"] + totals["suppressed"]) /
                 totals["candidates"] * 100.0) if totals["candidates"] else 0
    print(f"TOTAL candidates={totals['candidates']} "
          f"confirmed={totals['confirmed']} "
          f"suppressed={totals['suppressed']} "
          f"inconclusive={totals['inconclusive']} "
          f"open={totals['open']} "
          f"coverage={cov_total:.1f}%")
    return 0


def cmd_audit_gaps(args: argparse.Namespace) -> int:
    data = load(args.db)
    gaps = [(cid, c) for cid, c in data["candidates"].items()
            if c.get("status") in ("inconclusive", "open")]
    if not gaps:
        print("(no audit gaps)")
        return 0
    print(f"# {len(gaps)} audit gap(s)\n")
    for cid, c in sorted(gaps):
        print(f"- [{c.get('status')}] {cid}")
        if c.get("reason"):
            print(f"    reason: {c['reason']}")
        if c.get("note"):
            print(f"    note:   {c['note']}")
    return 0


def cmd_findings(args: argparse.Namespace) -> int:
    data = load(args.db)
    confirmed = [
        {"candidate_id": cid, **c}
        for cid, c in data["candidates"].items()
        if c.get("status") == "confirmed"
    ]
    out = json.dumps(confirmed, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(out + "\n", encoding="utf-8")
        print(f"wrote {len(confirmed)} confirmed candidate(s) to {args.out}")
    else:
        print(out)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB,
                    help="Coverage DB JSON file (default: coverage.json).")
    sp = ap.add_subparsers(dest="cmd", required=True)

    p = sp.add_parser("register", help="Add Pass 2 candidates.")
    p.add_argument("--candidates", type=Path, required=True,
                   help="JSONL file from scan_candidates.py.")
    p.set_defaults(func=cmd_register)

    p = sp.add_parser("mark", help="Mark a candidate's verification outcome.")
    p.add_argument("--id", required=True, help="candidate_id.")
    p.add_argument("--status", required=True,
                   choices=sorted(VALID_STATUS - {"open"}),
                   help="Verification outcome.")
    p.add_argument("--filter", help="FP filter id (required for suppressed).")
    p.add_argument("--reason", help="Short justification.")
    p.add_argument("--confidence", choices=sorted(VALID_CONFIDENCE),
                   help="Required for confirmed.")
    p.add_argument("--note", help="Optional free-form note.")
    p.set_defaults(func=cmd_mark)

    p = sp.add_parser("summary", help="Print per-template coverage table.")
    p.set_defaults(func=cmd_summary)

    p = sp.add_parser("audit-gaps", help="List inconclusive + un-marked items.")
    p.set_defaults(func=cmd_audit_gaps)

    p = sp.add_parser("findings", help="Dump confirmed candidates as JSON.")
    p.add_argument("--out", help="Output file (default: stdout).")
    p.set_defaults(func=cmd_findings)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
