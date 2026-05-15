#!/usr/bin/env python3
"""
run_audit.py — long-running audit conductor for the mdc-bug-patterns skill.

Implements the disk-driven resumable state machine documented in
references/long-running-audits.md. Every per-unit operation is checkpointed
atomically; a re-invocation reads state and picks up where the previous
run left off.

Subcommands:
    init           Initialise an audit directory (Pass 1+2).
    status         Print progress + ETA.
    next           Print the next pending unit (JSON).
    record         Record findings for a reviewed unit (atomic, idempotent).
    next-verdict   Print the next finding awaiting second-pass review (JSON).
    record-verdict Record a subagent verdict for a finding.
    partial        Generate a partial Excel report from current findings.
    finalize       Generate the final Excel report.
    mark           Surgical state intervention (set unit/finding status manually).
    reset-unit     Re-queue a single unit for re-review.

File layout under --out: see references/long-running-audits.md.

Resume protocol: re-running ANY subcommand on the same --out directory
picks up where the previous run left off.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
DEFAULT_TEMPLATES_DIR = SKILL_ROOT / "references" / "templates"

VALID_UNIT_STATUS = {"pending", "in-progress", "done", "failed", "timeout"}
VALID_FINDING_STATUS = {"pending", "in-progress", "done", "failed", "missing"}


# ---------- atomic IO ---------------------------------------------------------


def atomic_write(path: Path, content: str) -> None:
    """Write content to path atomically (write to .tmp, fsync, rename)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(content)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def atomic_write_json(path: Path, obj: Any) -> None:
    atomic_write(path, json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------- audit dir helpers ------------------------------------------------


class AuditDir:
    def __init__(self, root: Path):
        self.root = root
        self.meta = root / "meta.json"
        self.candidates = root / "candidates.jsonl"
        self.units = root / "units.jsonl"
        self.state = root / "state.json"
        self.findings_dir = root / "findings"
        self.verdicts_dir = root / "verdicts"
        self.heartbeat = root / "heartbeat.txt"
        self.runner_log = root / "runner.log"
        self.partial_dir = root / "partial_reports"
        self.final_report = root / "bug_report.xlsx"
        self.howto = root / "HOWTO_RESUME.md"

    def exists(self) -> bool:
        return self.meta.exists()

    def load_meta(self) -> dict:
        return json.loads(self.meta.read_text(encoding="utf-8"))

    def load_state(self) -> dict:
        if not self.state.exists():
            return {"units": {}, "findings": {}, "last_partial_at": None,
                    "last_partial_done_count": 0}
        return json.loads(self.state.read_text(encoding="utf-8"))

    def save_state(self, state: dict) -> None:
        atomic_write_json(self.state, state)

    def write_heartbeat(self, action: str) -> None:
        atomic_write(self.heartbeat,
                     f"{os.getpid()} {now_iso()} {action}\n")

    def append_log(self, line: str) -> None:
        with open(self.runner_log, "a", encoding="utf-8") as fh:
            fh.write(f"[{now_iso()}] {line}\n")

    def units_iter(self):
        if not self.units.exists():
            return
        for raw in self.units.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if raw:
                yield json.loads(raw)


# ---------- subcommand: init -------------------------------------------------


def cmd_init(args: argparse.Namespace) -> int:
    audit = AuditDir(args.out)
    if audit.exists() and not args.force:
        sys.stderr.write(
            f"refuse: {audit.meta} already exists; pass --force to discard\n"
        )
        return 2
    if args.force and audit.root.exists():
        shutil.rmtree(audit.root)
    audit.root.mkdir(parents=True, exist_ok=True)
    audit.findings_dir.mkdir(exist_ok=True)
    audit.verdicts_dir.mkdir(exist_ok=True)
    audit.partial_dir.mkdir(exist_ok=True)

    # Pass 2: scan candidates for each requested specialty (or all).
    sys.stderr.write("[init] running scan_candidates.py ...\n")
    scan_args = [
        sys.executable, str(SCRIPT_DIR / "scan_candidates.py"),
        "--path", str(args.scope),
        "--out", str(audit.candidates),
    ]
    specialties_used: list[str] = []
    if args.specialty:
        for s in args.specialty:
            specialties_used.append(s)
            spec_path = DEFAULT_TEMPLATES_DIR / f"{s}.md"
            if not spec_path.exists():
                sys.stderr.write(f"specialty file not found: {spec_path}\n")
                return 2
        # Run scan once per specialty and concat (scan_candidates supports one
        # specialty per invocation).
        all_lines: list[str] = []
        for s in args.specialty:
            tmp = audit.root / f".tmp_candidates_{s}.jsonl"
            inv = scan_args[:-1] + [str(tmp), "--specialty", s]
            r = subprocess.run(inv, capture_output=True, text=True)
            if r.returncode not in (0,):
                sys.stderr.write(
                    f"scan failed for specialty={s}: {r.stderr}\n"
                )
                return 2
            if tmp.exists():
                all_lines.extend(tmp.read_text(encoding="utf-8").splitlines())
                tmp.unlink()
        atomic_write(audit.candidates, "\n".join(all_lines) + "\n")
    else:
        specialties_used = sorted(p.stem for p in DEFAULT_TEMPLATES_DIR.glob("*.md"))
        r = subprocess.run(scan_args, capture_output=True, text=True)
        if r.returncode not in (0,):
            sys.stderr.write(f"scan failed: {r.stderr}\n")
            return 2
    sys.stderr.write(
        f"[init] candidates → {audit.candidates}  "
        f"({sum(1 for _ in audit.candidates.open(encoding='utf-8'))} lines)\n"
    )

    # Pass 2: list_units → ranked work-queue.
    sys.stderr.write("[init] running list_units.py ...\n")
    r = subprocess.run([
        sys.executable, str(SCRIPT_DIR / "list_units.py"),
        "--candidates", str(audit.candidates),
        "--path", str(args.scope),
        "--out", str(audit.units),
    ], capture_output=True, text=True)
    if r.returncode not in (0,):
        sys.stderr.write(f"list_units failed: {r.stderr}\n")
        return 2
    n_units = sum(1 for _ in audit.units.open(encoding="utf-8"))
    sys.stderr.write(f"[init] units → {audit.units}  ({n_units} units)\n")

    # meta.json + initial state.json.
    meta = {
        "audit_id": now_iso().replace(":", "").replace("-", ""),
        "repo": args.repo,
        "scope": str(args.scope),
        "specialties": specialties_used,
        "reviewer": args.reviewer,
        "started_at": now_iso(),
        "partial_every_units": args.partial_every_units,
        "partial_every_seconds": args.partial_every_seconds,
        "auto_commit": args.auto_commit,
        "commit_every": args.commit_every,
    }
    atomic_write_json(audit.meta, meta)

    state = {
        "units": {u["unit_id"]: {"status": "pending"} for u in audit.units_iter()},
        "findings": {},
        "last_partial_at": None,
        "last_partial_done_count": 0,
    }
    audit.save_state(state)
    audit.write_heartbeat("init")
    audit.append_log(
        f"init repo={args.repo} scope={args.scope} "
        f"specialties={specialties_used} units={n_units}"
    )

    # HOWTO_RESUME.md
    howto = f"""# How to resume this audit

This `audit/` directory was initialised by `run_audit.py init` at
{meta['started_at']}.

If you are a fresh agent picking up this audit:

1. **Do NOT re-run `init`.** That would discard the existing work.
2. Run status to see progress:
   ```bash
   {SCRIPT_DIR.relative_to(SKILL_ROOT.parent.parent) if SKILL_ROOT.parent.parent in SCRIPT_DIR.parents else SCRIPT_DIR}/run_audit.py status --out {audit.root}
   ```
3. Continue the cloud-agent loop:
   ```python
   while True:
       unit = run("run_audit.py next --out {audit.root}")
       if unit is None: break
       findings = review_unit(unit)              # call the LLM (or a Task subagent)
       write_json("audit/.tmp/f.json", findings)
       run(f"run_audit.py record --out {audit.root} --unit-id {{unit['unit_id']}} --findings audit/.tmp/f.json")
   ```
4. After all units done, run Pass 3.5 in the same shape via `next-verdict` / `record-verdict`.
5. Finally: `run_audit.py finalize --out {audit.root}`.

Specialties for this audit: **{', '.join(specialties_used)}**

For each unit review, load the corresponding specialty file(s) under
`{DEFAULT_TEMPLATES_DIR}/`. See `{SKILL_ROOT}/references/long-running-audits.md`
for the full operational protocol.

> **Each `audit/findings/<unit-id>.json` that already exists is a
> finished unit — never re-review it.**
"""
    atomic_write(audit.howto, howto)
    print(f"audit initialised at {audit.root}")
    print(f"  units: {n_units}; specialties: {specialties_used}")
    print(f"  resume: see {audit.howto}")
    return 0


# ---------- subcommand: status ----------------------------------------------


def cmd_status(args: argparse.Namespace) -> int:
    audit = AuditDir(args.out)
    if not audit.exists():
        sys.stderr.write(f"no audit at {audit.root}\n")
        return 2
    meta = audit.load_meta()
    state = audit.load_state()

    n_unit_status: dict[str, int] = {s: 0 for s in VALID_UNIT_STATUS}
    durations: list[float] = []
    for u in state["units"].values():
        n_unit_status[u.get("status", "pending")] = (
            n_unit_status.get(u.get("status", "pending"), 0) + 1
        )
        if u.get("status") == "done" and u.get("duration_seconds"):
            durations.append(u["duration_seconds"])
    n_total = sum(n_unit_status.values())
    n_done = n_unit_status["done"]

    n_finding_status: dict[str, int] = {s: 0 for s in VALID_FINDING_STATUS}
    for f in state["findings"].values():
        n_finding_status[f.get("status", "pending")] = (
            n_finding_status.get(f.get("status", "pending"), 0) + 1
        )

    started = datetime.fromisoformat(meta["started_at"])
    elapsed_s = (datetime.now(timezone.utc) - started).total_seconds()
    eta_str = "n/a"
    if durations and n_unit_status["pending"] > 0:
        per_unit = median(durations[-200:] if len(durations) > 200 else durations)
        eta_s = per_unit * n_unit_status["pending"]
        eta_str = f"~{int(eta_s // 3600)}h {int((eta_s % 3600) // 60)}m  (median {per_unit:.1f}s/unit)"

    print(f"audit/  (started {meta['started_at']}; specialties: {', '.join(meta['specialties'])})")
    print(f"  units:    pending={n_unit_status['pending']} / "
          f"in-progress={n_unit_status['in-progress']} / "
          f"done={n_unit_status['done']} / "
          f"failed={n_unit_status['failed']} / "
          f"timeout={n_unit_status['timeout']} / "
          f"total={n_total}")
    print(f"  verdicts: pending={n_finding_status['pending']} / "
          f"in-progress={n_finding_status['in-progress']} / "
          f"done={n_finding_status['done']} / "
          f"failed={n_finding_status['failed']} / "
          f"missing={n_finding_status['missing']} / "
          f"total={sum(n_finding_status.values())}")
    print(f"  duration: {int(elapsed_s // 3600)}h {int((elapsed_s % 3600) // 60)}m")
    print(f"  ETA:      {eta_str}")
    if state.get("last_partial_at"):
        print(f"  partial:  last at {state['last_partial_at']}")
    return 0


# ---------- subcommand: next -------------------------------------------------


def cmd_next(args: argparse.Namespace) -> int:
    audit = AuditDir(args.out)
    if not audit.exists():
        sys.stderr.write(f"no audit at {audit.root}\n")
        return 2
    state = audit.load_state()
    units_index = {u["unit_id"]: u for u in audit.units_iter()}
    for uid, st in state["units"].items():
        if st.get("status") == "pending":
            unit = units_index.get(uid, {"unit_id": uid})
            # Mark in-progress (so two parallel cloud agents don't pick the same unit).
            st["status"] = "in-progress"
            st["started_at"] = now_iso()
            audit.save_state(state)
            audit.write_heartbeat(f"next unit_id={uid}")
            print(json.dumps(unit, ensure_ascii=False))
            return 0
    # No pending units left.
    return 1


# ---------- subcommand: record -----------------------------------------------


def cmd_record(args: argparse.Namespace) -> int:
    audit = AuditDir(args.out)
    if not audit.exists():
        sys.stderr.write(f"no audit at {audit.root}\n")
        return 2
    state = audit.load_state()
    if args.unit_id not in state["units"]:
        sys.stderr.write(f"unknown unit_id: {args.unit_id}\n")
        return 2

    findings = json.loads(Path(args.findings).read_text(encoding="utf-8"))
    if not isinstance(findings, list):
        sys.stderr.write("findings file must contain a JSON list\n")
        return 2

    # Atomic per-unit findings file.
    safe_name = args.unit_id.replace("/", "__").replace(":", "_")
    findings_path = audit.findings_dir / f"{safe_name}.json"
    atomic_write_json(findings_path, findings)

    # Update state.
    started_at = state["units"][args.unit_id].get("started_at") or now_iso()
    duration = 0.0
    try:
        duration = (
            datetime.fromisoformat(now_iso())
            - datetime.fromisoformat(started_at)
        ).total_seconds()
    except (ValueError, TypeError):
        pass
    state["units"][args.unit_id] = {
        "status": "done",
        "started_at": started_at,
        "finished_at": now_iso(),
        "duration_seconds": round(duration, 1),
        "findings_count": len(findings),
        "findings_path": str(findings_path.relative_to(audit.root)),
    }
    # Register each finding for Pass 3.5.
    for f in findings:
        fid = f.get("id")
        if fid and fid not in state["findings"]:
            state["findings"][fid] = {
                "status": "pending",
                "unit_id": args.unit_id,
                "findings_path": str(findings_path.relative_to(audit.root)),
            }
    audit.save_state(state)
    audit.write_heartbeat(f"record unit_id={args.unit_id} findings={len(findings)}")
    audit.append_log(
        f"record unit_id={args.unit_id} findings={len(findings)} duration_s={duration:.1f}"
    )

    # Maybe roll a partial report.
    _maybe_partial(audit, state)
    # Maybe auto-commit.
    _maybe_autocommit(audit, args.unit_id)

    print(f"recorded {len(findings)} finding(s) for {args.unit_id} "
          f"({duration:.1f}s)")
    return 0


# ---------- subcommand: next-verdict / record-verdict ------------------------


def cmd_next_verdict(args: argparse.Namespace) -> int:
    audit = AuditDir(args.out)
    if not audit.exists():
        sys.stderr.write(f"no audit at {audit.root}\n")
        return 2
    state = audit.load_state()
    for fid, st in state["findings"].items():
        if st.get("status") == "pending":
            findings_path = audit.root / st["findings_path"]
            findings = json.loads(findings_path.read_text(encoding="utf-8"))
            target = next((f for f in findings if f.get("id") == fid), None)
            if not target:
                sys.stderr.write(f"warn: finding {fid} not in {findings_path}\n")
                continue
            st["status"] = "in-progress"
            st["started_at"] = now_iso()
            audit.save_state(state)
            audit.write_heartbeat(f"next-verdict id={fid}")
            print(json.dumps(target, ensure_ascii=False))
            return 0
    return 1


def cmd_record_verdict(args: argparse.Namespace) -> int:
    audit = AuditDir(args.out)
    if not audit.exists():
        sys.stderr.write(f"no audit at {audit.root}\n")
        return 2
    state = audit.load_state()
    if args.finding_id not in state["findings"]:
        sys.stderr.write(f"unknown finding id: {args.finding_id}\n")
        return 2

    verdict = json.loads(Path(args.verdict).read_text(encoding="utf-8"))
    if not isinstance(verdict, dict):
        sys.stderr.write("verdict file must contain a JSON object\n")
        return 2

    safe_name = args.finding_id.replace("/", "__").replace(":", "_")
    verdict_path = audit.verdicts_dir / f"{safe_name}.json"
    atomic_write_json(verdict_path, verdict)

    started_at = state["findings"][args.finding_id].get("started_at") or now_iso()
    state["findings"][args.finding_id].update({
        "status": "done",
        "verdict": verdict.get("verdict", "unknown"),
        "started_at": started_at,
        "finished_at": now_iso(),
        "verdict_path": str(verdict_path.relative_to(audit.root)),
    })
    audit.save_state(state)
    audit.write_heartbeat(f"record-verdict id={args.finding_id} "
                          f"verdict={verdict.get('verdict', '?')}")
    audit.append_log(
        f"record-verdict id={args.finding_id} verdict={verdict.get('verdict', '?')}"
    )
    print(f"recorded verdict={verdict.get('verdict', '?')} for {args.finding_id}")
    return 0


# ---------- partial / finalize -----------------------------------------------


def _assemble_findings(audit: AuditDir, *, with_review: bool = True) -> list[dict]:
    state = audit.load_state()
    out: list[dict] = []
    for uid, st in state["units"].items():
        if st.get("status") != "done" or not st.get("findings_path"):
            continue
        findings_path = audit.root / st["findings_path"]
        if not findings_path.exists():
            continue
        for f in json.loads(findings_path.read_text(encoding="utf-8")):
            if with_review:
                fid = f.get("id")
                fst = state["findings"].get(fid, {})
                if fst.get("verdict_path"):
                    vp = audit.root / fst["verdict_path"]
                    if vp.exists():
                        v = json.loads(vp.read_text(encoding="utf-8"))
                        f["second_pass_review"] = v
            out.append(f)
    return out


def _render_excel(audit: AuditDir, output: Path) -> None:
    findings = _assemble_findings(audit, with_review=True)
    findings_path = audit.root / ".tmp_findings.json"
    atomic_write_json(findings_path, findings)
    meta = audit.load_meta()
    cmd = [
        sys.executable, str(SCRIPT_DIR / "excel_helper.py"),
        "--bugs-file", str(findings_path),
        "--repo", meta.get("repo", ""),
        "--scope", meta.get("scope", ""),
        "--reviewer", meta.get("reviewer", "auto-overnight"),
        "--output", str(output),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    findings_path.unlink(missing_ok=True)
    if r.returncode not in (0,):
        sys.stderr.write(f"excel_helper failed: {r.stderr}\n")
        raise SystemExit(2)


def _maybe_partial(audit: AuditDir, state: dict) -> None:
    meta = audit.load_meta()
    every_units = int(meta.get("partial_every_units", 50))
    every_seconds = int(meta.get("partial_every_seconds", 1800))
    n_done = sum(1 for u in state["units"].values()
                 if u.get("status") == "done")
    last_count = state.get("last_partial_done_count", 0)
    last_at_str = state.get("last_partial_at")
    seconds_since = float("inf") if not last_at_str else (
        (datetime.now(timezone.utc) - datetime.fromisoformat(last_at_str))
        .total_seconds()
    )
    if (n_done - last_count) < every_units and seconds_since < every_seconds:
        return
    ts = now_iso().replace(":", "-")
    out = audit.partial_dir / f"bug_report-{ts}.xlsx"
    try:
        _render_excel(audit, out)
        state["last_partial_at"] = now_iso()
        state["last_partial_done_count"] = n_done
        audit.save_state(state)
        audit.append_log(f"partial report → {out}")
    except SystemExit:
        audit.append_log("partial report FAILED (continuing)")


def _maybe_autocommit(audit: AuditDir, unit_id: str) -> None:
    meta = audit.load_meta()
    if not meta.get("auto_commit"):
        return
    every = int(meta.get("commit_every", 50))
    state = audit.load_state()
    n_done = sum(1 for u in state["units"].values()
                 if u.get("status") == "done")
    if n_done % every != 0:
        return
    try:
        subprocess.run(["git", "add", str(audit.root)], check=True,
                       cwd=audit.root.parent)
        subprocess.run(
            ["git", "commit", "-m", f"audit checkpoint: {n_done} units done"],
            check=True, cwd=audit.root.parent,
        )
        audit.append_log(f"auto-commit at n_done={n_done}")
    except subprocess.CalledProcessError as e:
        audit.append_log(f"auto-commit FAILED: {e}")


def cmd_partial(args: argparse.Namespace) -> int:
    audit = AuditDir(args.out)
    if not audit.exists():
        sys.stderr.write(f"no audit at {audit.root}\n")
        return 2
    ts = now_iso().replace(":", "-")
    out = audit.partial_dir / f"bug_report-{ts}.xlsx"
    _render_excel(audit, out)
    state = audit.load_state()
    state["last_partial_at"] = now_iso()
    state["last_partial_done_count"] = sum(
        1 for u in state["units"].values() if u.get("status") == "done"
    )
    audit.save_state(state)
    audit.write_heartbeat(f"partial → {out}")
    print(f"partial report → {out}")
    return 0


def cmd_finalize(args: argparse.Namespace) -> int:
    audit = AuditDir(args.out)
    if not audit.exists():
        sys.stderr.write(f"no audit at {audit.root}\n")
        return 2
    _render_excel(audit, audit.final_report)
    audit.write_heartbeat("finalize")
    audit.append_log(f"finalize → {audit.final_report}")
    print(f"final report → {audit.final_report}")
    return 0


# ---------- subcommand: mark / reset-unit ------------------------------------


def cmd_mark(args: argparse.Namespace) -> int:
    audit = AuditDir(args.out)
    if not audit.exists():
        sys.stderr.write(f"no audit at {audit.root}\n")
        return 2
    state = audit.load_state()
    if args.unit_id:
        if args.unit_id not in state["units"]:
            sys.stderr.write(f"unknown unit_id: {args.unit_id}\n")
            return 2
        if args.status not in VALID_UNIT_STATUS:
            sys.stderr.write(f"unit status must be one of {sorted(VALID_UNIT_STATUS)}\n")
            return 2
        state["units"][args.unit_id]["status"] = args.status
        if args.reason:
            state["units"][args.unit_id]["reason"] = args.reason
    elif args.finding_id:
        if args.finding_id not in state["findings"]:
            sys.stderr.write(f"unknown finding_id: {args.finding_id}\n")
            return 2
        if args.status not in VALID_FINDING_STATUS:
            sys.stderr.write(
                f"finding status must be one of {sorted(VALID_FINDING_STATUS)}\n"
            )
            return 2
        state["findings"][args.finding_id]["status"] = args.status
        if args.reason:
            state["findings"][args.finding_id]["reason"] = args.reason
    else:
        sys.stderr.write("either --unit-id or --finding-id required\n")
        return 2
    audit.save_state(state)
    audit.write_heartbeat(
        f"mark {'unit' if args.unit_id else 'finding'}={args.unit_id or args.finding_id} "
        f"status={args.status}"
    )
    print(f"marked {args.unit_id or args.finding_id} as {args.status}")
    return 0


def cmd_reset_unit(args: argparse.Namespace) -> int:
    audit = AuditDir(args.out)
    if not audit.exists():
        sys.stderr.write(f"no audit at {audit.root}\n")
        return 2
    state = audit.load_state()
    if args.unit_id not in state["units"]:
        sys.stderr.write(f"unknown unit_id: {args.unit_id}\n")
        return 2
    safe_name = args.unit_id.replace("/", "__").replace(":", "_")
    findings_path = audit.findings_dir / f"{safe_name}.json"
    if findings_path.exists():
        findings = json.loads(findings_path.read_text(encoding="utf-8"))
        for f in findings:
            fid = f.get("id")
            if fid in state["findings"]:
                state["findings"].pop(fid)
        findings_path.unlink()
    state["units"][args.unit_id] = {"status": "pending"}
    audit.save_state(state)
    audit.write_heartbeat(f"reset-unit {args.unit_id}")
    print(f"reset {args.unit_id} to pending")
    return 0


# ---------- main / argparse ---------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sp = ap.add_subparsers(dest="cmd", required=True)

    def add_out(p_):
        p_.add_argument("--out", type=Path, default=Path("audit"),
                        help="audit directory (default: audit/)")

    p = sp.add_parser("init", help="Initialise an audit directory")
    add_out(p)
    p.add_argument("--scope", type=Path, required=True,
                   help="codebase root to scan")
    p.add_argument("--specialty", action="append", default=[],
                   help="specialty file name (repeatable; default: all)")
    p.add_argument("--repo", default="",
                   help="repo identifier (written to meta.json)")
    p.add_argument("--reviewer", default="auto-overnight",
                   help="reviewer name (written to meta.json)")
    p.add_argument("--force", action="store_true",
                   help="discard existing audit directory and re-init")
    p.add_argument("--partial-every-units", type=int, default=50,
                   help="rolling partial Excel cadence (units, default 50)")
    p.add_argument("--partial-every-seconds", type=int, default=1800,
                   help="rolling partial Excel cadence (seconds, default 1800)")
    p.add_argument("--auto-commit", action="store_true",
                   help="git commit audit/ every K records")
    p.add_argument("--commit-every", type=int, default=50,
                   help="auto-commit cadence (default 50)")
    p.set_defaults(func=cmd_init)

    p = sp.add_parser("status", help="Print progress + ETA")
    add_out(p)
    p.set_defaults(func=cmd_status)

    p = sp.add_parser("next", help="Print the next pending unit (JSON)")
    add_out(p)
    p.set_defaults(func=cmd_next)

    p = sp.add_parser("record",
                      help="Record findings for a reviewed unit")
    add_out(p)
    p.add_argument("--unit-id", required=True)
    p.add_argument("--findings", type=Path, required=True,
                   help="JSON list of finding objects")
    p.set_defaults(func=cmd_record)

    p = sp.add_parser("next-verdict",
                      help="Print the next finding awaiting second-pass review (JSON)")
    add_out(p)
    p.set_defaults(func=cmd_next_verdict)

    p = sp.add_parser("record-verdict",
                      help="Record a subagent verdict for a finding")
    add_out(p)
    p.add_argument("--finding-id", required=True)
    p.add_argument("--verdict", type=Path, required=True,
                   help="JSON verdict object (see references/second-pass-review.md)")
    p.set_defaults(func=cmd_record_verdict)

    p = sp.add_parser("partial",
                      help="Generate a partial Excel report on demand")
    add_out(p)
    p.set_defaults(func=cmd_partial)

    p = sp.add_parser("finalize",
                      help="Generate the final Excel report")
    add_out(p)
    p.set_defaults(func=cmd_finalize)

    p = sp.add_parser("mark",
                      help="Surgical state intervention "
                           "(set unit/finding status manually)")
    add_out(p)
    p.add_argument("--unit-id")
    p.add_argument("--finding-id")
    p.add_argument("--status", required=True)
    p.add_argument("--reason")
    p.set_defaults(func=cmd_mark)

    p = sp.add_parser("reset-unit",
                      help="Re-queue a single unit (drop its findings)")
    add_out(p)
    p.add_argument("--unit-id", required=True)
    p.set_defaults(func=cmd_reset_unit)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
