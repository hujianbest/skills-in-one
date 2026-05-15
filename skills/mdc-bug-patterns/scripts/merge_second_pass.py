#!/usr/bin/env python3
"""
merge_second_pass.py — Pass 3.5 helper for the mdc-bug-patterns skill.

Merges second-pass subagent verdicts into the findings JSON.

Inputs:
  --findings PATH    findings.json  (list of finding objects, see
                                     references/reporting.md)
  --verdicts PATH    verdicts.jsonl OR verdicts.json
                     each verdict object MUST contain:
                       id        (matches finding.id)
                       verdict   ("agree" | "disagree" | "uncertain")
                       rationale string
                     and SHOULD contain:
                       evidence_check {...}
                       supporting_evidence [...]
                       reviewer  string

Output:
  --out PATH         writes the merged findings JSON. Each finding gets
                     a `second_pass_review` block. Findings without a
                     verdict get verdict="missing" so the human reviewer
                     sees the gap explicitly.

The script is idempotent: running it twice with the same verdicts file
produces the same output. If a finding already has a `second_pass_review`
block, it is overwritten by the matching verdict (or kept if no
matching verdict is provided).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VALID_VERDICTS = {"agree", "disagree", "uncertain"}


def _load_verdicts(path: Path) -> dict[str, dict[str, Any]]:
    """Accept either a JSON list or a JSONL stream of verdict objects."""
    text = path.read_text(encoding="utf-8").strip()
    out: dict[str, dict[str, Any]] = {}
    if not text:
        return out
    try:
        # JSON list?
        data = json.loads(text)
        if isinstance(data, list):
            for v in data:
                _ingest_verdict(v, out, source=path)
            return out
        if isinstance(data, dict):
            # Single verdict?
            _ingest_verdict(data, out, source=path)
            return out
    except json.JSONDecodeError:
        pass
    # Fall back to JSONL.
    for ln, raw in enumerate(text.splitlines(), 1):
        raw = raw.strip()
        if not raw:
            continue
        try:
            v = json.loads(raw)
        except json.JSONDecodeError as e:
            sys.stderr.write(f"{path}:{ln}: invalid JSON, skipped ({e})\n")
            continue
        _ingest_verdict(v, out, source=path, line=ln)
    return out


def _ingest_verdict(v: Any, out: dict[str, dict[str, Any]],
                    *, source: Path, line: int | None = None) -> None:
    if not isinstance(v, dict):
        sys.stderr.write(f"{source}{f':{line}' if line else ''}: "
                         f"verdict must be an object, got {type(v).__name__}; "
                         f"skipped\n")
        return
    fid = v.get("id")
    verdict = v.get("verdict")
    if not fid or not isinstance(fid, str):
        sys.stderr.write(f"{source}{f':{line}' if line else ''}: "
                         f"verdict missing string `id`; skipped\n")
        return
    if verdict not in VALID_VERDICTS:
        sys.stderr.write(f"{source}{f':{line}' if line else ''}: "
                         f"verdict for {fid!r} must be one of {sorted(VALID_VERDICTS)}, "
                         f"got {verdict!r}; skipped\n")
        return
    if fid in out:
        sys.stderr.write(f"{source}{f':{line}' if line else ''}: "
                         f"duplicate verdict for {fid!r}; later one wins\n")
    out[fid] = v


def _normalise_review_block(verdict_obj: dict[str, Any]) -> dict[str, Any]:
    block = {
        "verdict":   verdict_obj["verdict"],
        "rationale": verdict_obj.get("rationale", ""),
        "evidence_check": _normalise_evidence_check(
            verdict_obj.get("evidence_check") or {}
        ),
        "supporting_evidence":
            list(verdict_obj.get("supporting_evidence") or []),
        "reviewed_at":
            verdict_obj.get("reviewed_at")
            or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "reviewer":
            verdict_obj.get("reviewer") or "subagent",
    }
    return block


def _normalise_evidence_check(ec: Any) -> dict[str, Any]:
    if not isinstance(ec, dict):
        return {
            "all_cited_lines_exist": None,
            "all_cited_lines_match_excerpts": None,
            "fp_filters_actually_ruled_out": None,
            "additional_fp_filters_found": [],
        }
    return {
        "all_cited_lines_exist":
            _as_bool(ec.get("all_cited_lines_exist")),
        "all_cited_lines_match_excerpts":
            _as_bool(ec.get("all_cited_lines_match_excerpts")),
        "fp_filters_actually_ruled_out":
            _as_bool(ec.get("fp_filters_actually_ruled_out")),
        "additional_fp_filters_found":
            list(ec.get("additional_fp_filters_found") or []),
    }


def _as_bool(x: Any) -> bool | None:
    if x is True or x is False:
        return x
    if isinstance(x, str):
        s = x.strip().lower()
        if s in ("true", "yes", "y", "1"):
            return True
        if s in ("false", "no", "n", "0"):
            return False
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--findings", type=Path, required=True,
                    help="findings.json (list of finding objects)")
    ap.add_argument("--verdicts", type=Path, required=True,
                    help="verdicts.jsonl or verdicts.json")
    ap.add_argument("--out", type=Path, required=True,
                    help="output path for merged findings JSON")
    args = ap.parse_args(argv)

    if not args.findings.exists():
        sys.stderr.write(f"findings file not found: {args.findings}\n")
        return 2
    if not args.verdicts.exists():
        sys.stderr.write(f"verdicts file not found: {args.verdicts}\n")
        return 2

    findings = json.loads(args.findings.read_text(encoding="utf-8"))
    if not isinstance(findings, list):
        sys.stderr.write("findings file must contain a JSON list\n")
        return 2

    verdicts = _load_verdicts(args.verdicts)

    n_agree = n_disagree = n_uncertain = n_missing = 0
    used: set[str] = set()
    for f in findings:
        if not isinstance(f, dict):
            continue
        fid = f.get("id") or ""
        v = verdicts.get(fid)
        if v is None:
            f["second_pass_review"] = {
                "verdict": "missing",
                "rationale": "未收到子代理复核结论 (subagent 未返回或返回格式错误)。",
                "evidence_check": _normalise_evidence_check({}),
                "supporting_evidence": [],
                "reviewed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "reviewer": "merge_second_pass.py",
            }
            n_missing += 1
            continue
        used.add(fid)
        f["second_pass_review"] = _normalise_review_block(v)
        verdict = v["verdict"]
        if verdict == "agree":
            n_agree += 1
        elif verdict == "disagree":
            n_disagree += 1
        elif verdict == "uncertain":
            n_uncertain += 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(findings, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"已合并 {len(used)}/{len(findings)} 条子代理复核结论 → {args.out}")
    print(f"  同意 (agree):     {n_agree}")
    print(f"  反对 (disagree):  {n_disagree}")
    print(f"  不确定 (uncertain): {n_uncertain}")
    print(f"  缺失 (missing):   {n_missing}")

    orphans = sorted(set(verdicts) - used)
    if orphans:
        sys.stderr.write(
            f"\n[merge_second_pass] {len(orphans)} 条 verdict 未匹配到任何 finding "
            f"(可能是 id 拼写问题):\n"
        )
        for fid in orphans[:20]:
            sys.stderr.write(f"  - {fid}\n")
        if len(orphans) > 20:
            sys.stderr.write(f"  ... ({len(orphans) - 20} more)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
