#!/usr/bin/env bash
# audit-overnight-opencode.sh — start an unattended overnight mdc-bug-patterns audit
# driven by `opencode run --attach`.
#
# Architecture: tmux session containing
#   pane 0:  opencode serve --port <PORT>   (long-lived agent backend)
#   pane 1:  Pass 3 driver loop (next → opencode run → record), then
#            Pass 3.5 driver loop (next-verdict → opencode run → record-verdict),
#            then finalize.
#
# All checkpoints are persisted by run_audit.py (atomic per-unit writes); a
# crash mid-run can be resumed by simply re-launching this script on the same
# audit directory.
#
# Usage:
#     audit-overnight-opencode.sh <audit-dir> [--port N] [--model M] [--verdict-model M]
#
# Pre-requisites:
#     1. run_audit.py init … --out <audit-dir>     # one-time, before this script
#     2. opencode in $PATH                         # `opencode --version`
#     3. tmux in $PATH
#
# See references/opencode-integration.md for the full guide.

set -euo pipefail

AUDIT_DIR=""
PORT=4096
MODEL=""
VERDICT_MODEL=""
RETRY_MAX=3
TIMEOUT_SEC=600

while [[ $# -gt 0 ]]; do
    case "$1" in
        --port)         PORT="$2"; shift 2 ;;
        --model)        MODEL="$2"; shift 2 ;;
        --verdict-model) VERDICT_MODEL="$2"; shift 2 ;;
        --retry-max)    RETRY_MAX="$2"; shift 2 ;;
        --timeout-sec)  TIMEOUT_SEC="$2"; shift 2 ;;
        -h|--help)
            sed -n '2,/^$/p' "$0" | sed 's/^# *//'
            exit 0 ;;
        *)
            if [[ -z "$AUDIT_DIR" ]]; then AUDIT_DIR="$1"; shift
            else echo "unexpected arg: $1" >&2; exit 2; fi ;;
    esac
done

[[ -n "$AUDIT_DIR" ]] || { echo "usage: $0 <audit-dir> [--port N] [--model M] [--verdict-model M]" >&2; exit 2; }
[[ -f "$AUDIT_DIR/meta.json" ]] || {
    echo "ERR: $AUDIT_DIR/meta.json not found." >&2
    echo "     Run 'run_audit.py init --out $AUDIT_DIR …' first." >&2
    exit 2
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
RUN_AUDIT="$SCRIPT_DIR/run_audit.py"
SESSION="mdc-audit-$(basename "$AUDIT_DIR" | tr '/' '_')"
AUDIT_DIR_ABS="$(cd "$AUDIT_DIR" && pwd)"

command -v tmux    >/dev/null || { echo "tmux not found" >&2; exit 2; }
command -v opencode >/dev/null || { echo "opencode not found in PATH" >&2; exit 2; }

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "ERR: tmux session '$SESSION' already exists." >&2
    echo "     attach: tmux attach -t $SESSION" >&2
    echo "     kill:   tmux kill-session -t $SESSION" >&2
    exit 2
fi

# Build the model flag fragments.
MODEL_FLAG=""
if [[ -n "$MODEL" ]]; then MODEL_FLAG="--model '$MODEL'"; fi
VERDICT_MODEL_FLAG=""
if [[ -n "$VERDICT_MODEL" ]]; then VERDICT_MODEL_FLAG="--model '$VERDICT_MODEL'"; fi

# pane 0: opencode serve.
tmux new-session -d -s "$SESSION" -- bash -lc "
    echo '[serve] opencode serve --port $PORT' | tee -a '$AUDIT_DIR_ABS/opencode-serve.log'
    exec opencode serve --port $PORT 2>&1 | tee -a '$AUDIT_DIR_ABS/opencode-serve.log'
"

# Wait until the server responds.
echo "[boot] waiting for opencode serve on :$PORT ..."
for _ in 1 2 3 4 5 6 7 8 9 10; do
    if curl -sf "http://localhost:$PORT/" >/dev/null 2>&1; then break; fi
    sleep 2
done
if ! curl -sf "http://localhost:$PORT/" >/dev/null 2>&1; then
    echo "WARN: opencode serve did not respond on :$PORT in 20s; driver will retry." >&2
fi

# pane 1: driver loop (Pass 3 then Pass 3.5 then finalize).
tmux split-window -t "$SESSION":0 -h -- bash -lc "
    set -uo pipefail
    PORT=$PORT
    AUDIT='$AUDIT_DIR_ABS'
    SKILL='$SKILL_DIR'
    RUN_AUDIT='$RUN_AUDIT'
    RETRY_MAX=$RETRY_MAX
    TIMEOUT_SEC=$TIMEOUT_SEC

    log() { printf '[%s] %s\n' \"\$(date -u +%FT%TZ)\" \"\$*\" | tee -a \"\$AUDIT/driver.log\"; }

    # Decide which specialty file to load based on the unit's signals.
    pick_specialty() {
        python3 - <<'PY'
import json, sys
d = json.loads(sys.stdin.read())
sigs = [s.split('::')[0] for s in d.get('signals', [])
        if not s.startswith('primitive:') and not s.startswith('size:')]
if not sigs:
    print('memory-safety'); sys.exit(0)
prefix = sigs[0].split('-')[0]
print({
    'mem': 'memory-safety',  'ptr': 'memory-safety',
    'res': 'resource-management',
    'con': 'lock-usage',     'isr': 'concurrency-and-isr',
    'rtos': 'lock-usage',
    'int': 'logic-and-numeric', 'div': 'logic-and-numeric', 'empty': 'logic-and-numeric',
    'emb': 'embedded-hardware',
}.get(prefix, 'memory-safety'))
PY
    }

    log '======================================================'
    log 'Pass 3 driver loop start'
    log '======================================================'

    while true; do
        UNIT_JSON=\$(\"\$RUN_AUDIT\" next --out \"\$AUDIT\" 2>/dev/null) || {
            log 'no more pending units → moving to Pass 3.5'
            break
        }
        UNIT_ID=\$(echo \"\$UNIT_JSON\" | python3 -c 'import json,sys;print(json.load(sys.stdin)[\"unit_id\"])')
        FILE=\$(echo \"\$UNIT_JSON\" | python3 -c 'import json,sys;print(json.load(sys.stdin)[\"file\"])')
        L1=\$(echo \"\$UNIT_JSON\" | python3 -c 'import json,sys;print(json.load(sys.stdin)[\"line_start\"])')
        L2=\$(echo \"\$UNIT_JSON\" | python3 -c 'import json,sys;print(json.load(sys.stdin)[\"line_end\"])')
        SPEC=\$(echo \"\$UNIT_JSON\" | pick_specialty)

        FINDINGS=\"/tmp/audit-findings-\$\$.\$RANDOM.json\"
        echo '[]' > \"\$FINDINGS\"

        cat > /tmp/audit-prompt.\$\$.md <<EOF
You are doing Pass 3 of an mdc-bug-patterns C/C++ embedded audit.

UNIT TO REVIEW
  unit_id:  \$UNIT_ID
  file:     \$FILE
  lines:    \$L1..\$L2

INSTRUCTIONS
  1. Read \$FILE lines \$L1..\$L2 fully (and the enclosing class declaration if member state is involved).
  2. Read up to 20 callers via 'rg -n' for context if caller invariants matter.
  3. Apply ALL relevant templates from the specialty checklist at:
       \$SKILL/references/templates/\$SPEC.md
  4. For each finding, follow the per-template 'verification' checklist; build the 'required_evidence'
     block; explicitly rule out the listed 'fp_filters' (see \$SKILL/references/false-positive-filters.md).
  5. Write a JSON array of findings to: \$FINDINGS
     Each finding MUST follow the schema in \$SKILL/references/reporting.md (id, template_id, name,
     category, severity, confidence, location, summary, required_evidence,
     false_positive_filters_ruled_out, fix_suggestions, context).
     If no findings, leave the file as '[]'.
  6. Reply with: 'OK: wrote N findings to \$FINDINGS'
EOF

        log \"unit \$UNIT_ID  spec=\$SPEC  lines=\$L1..\$L2\"

        SUCCESS=0
        for ATTEMPT in \$(seq 1 \$RETRY_MAX); do
            timeout \$TIMEOUT_SEC opencode run --attach http://localhost:\$PORT $MODEL_FLAG --format json \\
                < /tmp/audit-prompt.\$\$.md \\
                >> \"\$AUDIT/opencode-run.log\" 2>&1 && { SUCCESS=1; break; }
            BACKOFF=\$((30 * ATTEMPT))
            log \"  attempt \$ATTEMPT failed; retrying in \${BACKOFF}s\"
            sleep \$BACKOFF
        done

        if [[ \$SUCCESS -eq 1 && -f \"\$FINDINGS\" ]]; then
            \"\$RUN_AUDIT\" record --out \"\$AUDIT\" --unit-id \"\$UNIT_ID\" --findings \"\$FINDINGS\" \\
                | tee -a \"\$AUDIT/driver.log\"
        else
            log \"  FAILED after \$RETRY_MAX attempts; marking 'failed'\"
            \"\$RUN_AUDIT\" mark --out \"\$AUDIT\" --unit-id \"\$UNIT_ID\" \\
                --status failed --reason 'opencode dispatch failed after retries' \\
                | tee -a \"\$AUDIT/driver.log\"
        fi
        rm -f \"\$FINDINGS\" /tmp/audit-prompt.\$\$.md
    done

    log '======================================================'
    log 'Pass 3.5 driver loop start (second-pass verdicts)'
    log '======================================================'

    while true; do
        FINDING_JSON=\$(\"\$RUN_AUDIT\" next-verdict --out \"\$AUDIT\" 2>/dev/null) || {
            log 'all verdicts done → finalizing'
            break
        }
        FID=\$(echo \"\$FINDING_JSON\" | python3 -c 'import json,sys;print(json.load(sys.stdin)[\"id\"])')
        VERDICT=\"/tmp/audit-verdict-\$\$.\$RANDOM.json\"
        echo \"\$FINDING_JSON\" > /tmp/audit-finding.\$\$.json

        cat > /tmp/audit-verdict-prompt.\$\$.md <<EOF
You are doing Pass 3.5 (independent second-pass review). YOU MUST NOT TRUST the first-pass agent's
reasoning. Re-read the source code and re-derive the verdict.

Repository root: \$PWD
Finding to review: see /tmp/audit-finding.\$\$.json (single object, NOT an array).

Follow the procedure + output format in:
  \$SKILL/references/second-pass-review.md

Write a SINGLE verdict object (NOT an array) to: \$VERDICT
Reply with: 'OK: wrote verdict to \$VERDICT'
EOF

        log \"verdict for \$FID\"

        SUCCESS=0
        for ATTEMPT in \$(seq 1 \$RETRY_MAX); do
            timeout \$TIMEOUT_SEC opencode run --attach http://localhost:\$PORT $VERDICT_MODEL_FLAG --format json \\
                < /tmp/audit-verdict-prompt.\$\$.md \\
                >> \"\$AUDIT/opencode-run.log\" 2>&1 && { SUCCESS=1; break; }
            BACKOFF=\$((30 * ATTEMPT))
            log \"  attempt \$ATTEMPT failed; retrying in \${BACKOFF}s\"
            sleep \$BACKOFF
        done

        if [[ \$SUCCESS -eq 1 && -f \"\$VERDICT\" ]]; then
            \"\$RUN_AUDIT\" record-verdict --out \"\$AUDIT\" --finding-id \"\$FID\" --verdict \"\$VERDICT\" \\
                | tee -a \"\$AUDIT/driver.log\"
        else
            log \"  FAILED; marking verdict 'failed' (renders as 未复核 in Excel)\"
            \"\$RUN_AUDIT\" mark --out \"\$AUDIT\" --finding-id \"\$FID\" \\
                --status failed --reason 'opencode verdict dispatch failed' \\
                | tee -a \"\$AUDIT/driver.log\"
        fi
        rm -f \"\$VERDICT\" /tmp/audit-finding.\$\$.json /tmp/audit-verdict-prompt.\$\$.md
    done

    log 'finalizing → bug_report.xlsx'
    \"\$RUN_AUDIT\" finalize --out \"\$AUDIT\" | tee -a \"\$AUDIT/driver.log\"
    log 'DONE'
"

cat <<DONE

started overnight audit in tmux session: $SESSION

  attach session:    tmux attach -t $SESSION       (Ctrl+B D to detach without killing)
  status anytime:    $RUN_AUDIT status --out $AUDIT_DIR_ABS
  latest partial:    ls -lt $AUDIT_DIR_ABS/partial_reports/ | head
  driver logs:       tail -f $AUDIT_DIR_ABS/driver.log
  is driver alive:   kill -0 \$(awk '{print \$1}' $AUDIT_DIR_ABS/heartbeat.txt) && echo OK || echo DEAD

When done (or to abandon):
  tmux kill-session -t $SESSION

DONE
