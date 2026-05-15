# Long-Running Audits — Resume-Safe Protocol

> Operational protocol for audits that run for hours overnight and MUST survive context overflow, VM restart, network drops, rate limits, and subagent failures **without losing any per-unit work already done**.

The mechanism is a **disk-driven resumable state machine** managed by `scripts/run_audit.py`. Every per-unit operation is checkpointed atomically; a re-invocation reads the state and picks up where the previous run left off.

## Directory layout

Every audit lives under a single `--out` directory (default `audit/`) with this layout:

```
audit/
  meta.json              # repo / scope / specialties / timestamps (one-time, written by `init`)
  candidates.jsonl       # Pass 2 raw candidates (input to list_units)
  units.jsonl            # Pass 2 ranked unit work-queue (input to Pass 3)
  state.json             # per-unit + per-finding status (atomic writes)
  findings/<unit>.json   # one file per reviewed unit
  verdicts/<id>.json     # one file per second-pass-reviewed finding
  heartbeat.txt          # `<pid> <iso-timestamp> <last-action>` updated on every checkpoint
  runner.log             # append-only log
  partial_reports/       # rolling Excel snapshots
  bug_report.xlsx        # final Excel report (written by `finalize`)
  HOWTO_RESUME.md        # auto-generated; tells a fresh agent how to pick up
```

**Atomic writes are mandatory**: the conductor writes to `<path>.tmp`, `fsync`s, then `os.replace(<path>.tmp, <path>)`. A power-cut mid-write leaves the previous file intact; never a half-written `state.json`.

## The Iron Rule

> **Checkpoint after EVERY unit, not every batch.**

The discipline is "lose at most 1 unit on a crash". Batched checkpoints (e.g., every 20 units) are forbidden — the worst case becomes 20 units of lost LLM work, and 20 units overnight could be 30+ minutes wasted.

## The five subcommands

### `run_audit.py init`

One-time setup. Runs `scan_candidates.py` (Pass 2 candidate enumeration) + `list_units.py` (Pass 2 ranking) and writes the work queue to `units.jsonl` + initial `state.json` (all units `status="pending"`). Also generates `HOWTO_RESUME.md` so a fresh agent can recover.

```bash
run_audit.py init \
  --scope src/ \
  --specialty lock-usage --specialty concurrency-and-isr \
  --repo "myorg/myrepo" --reviewer "auto-overnight" \
  --out audit/
```

Idempotent: re-running `init` on an existing `--out` directory **refuses** to overwrite (use `--force` to discard and start over).

### `run_audit.py next`

Prints the next pending unit as JSON (file, line range, signals, suggested specialty file to load). The cloud agent reads this, performs the unit review, writes the findings to a temp file, then calls `record`.

Returns exit 1 + empty output when no units remain.

### `run_audit.py record --unit-id ID --findings PATH`

Atomic checkpoint:
1. Copies `PATH` into `audit/findings/<unit-id>.json`.
2. Updates `state.json` with `status="done"`, `finished_at`, `duration_seconds`, `findings_count`.
3. Writes heartbeat.
4. If `audit/state.json` shows ≥ K units done since the last partial report (default K=50) **OR** ≥ T seconds since the last partial report (default T=1800s = 30 min), automatically generates a fresh `partial_reports/bug_report-<timestamp>.xlsx`.

Idempotent: re-running with the same `--unit-id` overwrites the per-unit findings file (use case: a unit was reviewed, then the human / second-pass found an issue and the cloud agent re-reviews).

### `run_audit.py next-verdict` / `record-verdict`

Same shape as `next` / `record` but for Pass 3.5 second-pass review. `next-verdict` returns the next finding lacking a `second_pass_review` block; `record-verdict --finding-id ID --verdict PATH` writes to `audit/verdicts/<id>.json` and updates `state.json`.

### `run_audit.py status`

Prints progress + ETA based on per-unit timing stats:

```
audit/  (started 2026-05-14 22:13)
  units:    pending=183 / in-progress=1 / done=412 / failed=4 / total=600
  verdicts: pending= 87 / in-progress=0 / done=329 / missing=0 / total=416
  duration: 6h 47m
  ETA:      ~2h 30m  (median 22.4s/unit; based on last 200 units)
  partial:  audit/partial_reports/bug_report-2026-05-15T03-12-44Z.xlsx (12 min ago)
```

### `run_audit.py partial` / `finalize`

`partial` regenerates the partial Excel snapshot on demand (also called automatically by `record`). `finalize` produces the final `bug_report.xlsx` once all pending units are processed.

## Cloud-agent loop (pseudocode)

```python
# After init has been called once:
while True:
    unit = run("run_audit.py next --out audit/")
    if unit is None:                      # all done
        break

    # 1. Construct the review prompt from:
    #    - the chosen specialty file (e.g. lock-usage.md)
    #    - the unit body (read the file at unit["file"], lines unit["line_start"]..unit["line_end"])
    #    - up to 20 callers (rg)
    # 2. Dispatch a Task subagent (or do the review in the current context).
    # 3. The review produces a JSON list of findings (possibly empty) per the schema in references/reporting.md.

    findings_path = "audit/.tmp/unit-findings.json"
    write_findings(findings_path, findings)

    run(f"run_audit.py record --out audit/ --unit-id {unit['unit_id']} --findings {findings_path}")

# Then Pass 3.5:
while True:
    finding = run("run_audit.py next-verdict --out audit/")
    if finding is None:
        break
    verdict = dispatch_second_pass_subagent(finding)   # see references/second-pass-review.md
    verdict_path = "audit/.tmp/verdict.json"
    write_verdict(verdict_path, verdict)
    run(f"run_audit.py record-verdict --out audit/ --finding-id {finding['id']} --verdict {verdict_path}")

# Finally:
run("run_audit.py finalize --out audit/")
```

## Subagent dispatch — retry / timeout / failure

The cloud agent wraps every subagent dispatch (Pass 3 review and Pass 3.5 verdict) with retry + timeout:

- **Per-unit timeout**: 10 minutes. If the subagent does not return within that, the conductor records `status="timeout"` for the unit and moves on. The unit goes to the audit-gaps section in the final report.
- **Retry policy**: on subagent error (rate limit / network / malformed JSON), retry 3 times with exponential backoff (30s, 60s, 120s). After 3 failures, record `status="failed"` with the last error message and continue.
- **No single unit may stall the queue.** Bounded effort beats perfectionism; the failed / inconclusive units are visible in the partial report and can be re-driven manually.

## Liveness — heartbeat + tmux

`audit/heartbeat.txt` is updated on every checkpoint with `<pid> <iso-ts> <last-action>`. To check whether a long-running audit is still alive:

```bash
# from another shell:
cat audit/heartbeat.txt
# 12345 2026-05-15T03:42:11Z record unit_id=src/io/server.cc::Server::OnEvent

# is the conductor still running?
kill -0 $(awk '{print $1}' audit/heartbeat.txt) && echo OK || echo DEAD
```

Run the conductor inside `tmux` so an SSH drop / cloud-agent restart does not kill it:

```bash
tmux -f /exec-daemon/tmux.portal.conf new-session -d -s mdc-audit -c "$PWD" -- bash -lc '
    while true; do
        run_audit.py loop --out audit/                          # cloud-agent driven loop
        echo "[$(date -Is)] conductor exited, restarting in 30s" | tee -a audit/runner.log
        sleep 30
    done
'

# attach when needed:
tmux -f /exec-daemon/tmux.portal.conf attach -t mdc-audit
```

(`run_audit.py loop` is a thin wrapper that runs `next` → cloud-agent dispatch → `record` repeatedly; you can also invoke `next` / `record` directly from any other driver.)

## Cloud-agent restart contract

If a fresh cloud-agent instance is invoked on a workspace that already contains an `audit/` directory:

1. **Do NOT restart Pass 1 / Pass 2.** Read `audit/HOWTO_RESUME.md` first.
2. Run `run_audit.py status --out audit/` to see what's done.
3. Continue the cloud-agent loop above (`next` → review → `record`).
4. Any unit whose `audit/findings/<unit>.json` exists is **finished**; do not re-review it.
5. After all units are done, dispatch second-pass; after all verdicts in, run `finalize`.

`HOWTO_RESUME.md` is auto-generated by `init` and contains the exact commands to run, scoped to the audit's specialty selection.

## Optional: auto-commit checkpoints

For paranoid runs (workspace itself might be lost, not just the agent), add `--auto-commit` to `init`:

```bash
run_audit.py init … --out audit/ --auto-commit --commit-every 50
```

This makes `record` invoke `git add audit/ && git commit -m "audit checkpoint: <unit-id>"` after every K records. Default OFF — pollutes git history; turn on only when remote-only persistence matters.

## Rolling partial reports — the "wake up at 7am" guarantee

If you start the audit at 8pm and crawl out of bed at 7am to find the conductor died at 4am, you still want the 8pm-4am work in a usable form. Hence:

- Every K=50 units OR T=30 minutes (whichever first), `record` regenerates `audit/partial_reports/bug_report-<ts>.xlsx`.
- The partial report uses the same Chinese 4-sheet layout as the final report; the audit-gaps sheet calls out un-reviewed units as "本次审计未抵达" so the reviewer knows the boundary.
- Tune cadence with `--partial-every-units N --partial-every-seconds S` on `init`.

## Anti-patterns to refuse

- **Batched checkpoints** ("checkpoint every 20 units to save IO"): no. Per-unit checkpoint is the contract.
- **Skipping `record` after a unit "trivially had no findings"**: no. An empty findings list is a real outcome and must still be recorded — otherwise the unit is forever marked pending and rescanned on every restart.
- **Manually editing `state.json`**: don't. Use `run_audit.py mark --unit-id ID --status STATUS --reason "..."` for surgical interventions.
- **Re-running `init --force` to "start clean"**: only if you truly want to discard hours of work. Prefer `run_audit.py reset-unit --unit-id ID` to re-queue a single unit.
