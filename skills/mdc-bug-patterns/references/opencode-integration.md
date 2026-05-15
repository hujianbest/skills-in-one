# 在 opencode 中跑 mdc-bug-patterns (含过夜审计)

> 把这个 skill 接进 [opencode](https://opencode.ai) 的具体步骤。重点回答："我有 N 千文件要审, 启动后想睡觉, 怎么保证早上起来要么跑完了, 要么至少跑了大半且能恢复"。

通用的长跑可恢复协议（每单元 checkpoint、原子写、heartbeat、partial 报告等）在 [`long-running-audits.md`](long-running-audits.md)。**本文只补充 opencode-specific 的部分**：怎么装 skill、怎么用 `opencode run --attach` 做 per-unit dispatch、怎么处理 opencode 的非交互权限。

---

## 1. 安装 skill 到 opencode

opencode 自动扫描 6 个 skills 目录（项目级 + 全局），任选其一：

| 路径 | 范围 | 用法 |
|---|---|---|
| `<project>/.opencode/skills/<name>/` | 仅当前项目 | `cp -r mdc-bug-patterns <project>/.opencode/skills/` |
| `<project>/.claude/skills/<name>/` | 仅当前项目（Claude Code 兼容路径） | 同上 |
| `<project>/.agents/skills/<name>/` | 仅当前项目（agents 通用路径） | 同上 |
| `~/.config/opencode/skills/<name>/` | **全局**（推荐，可在任意项目里用） | `cp -r mdc-bug-patterns ~/.config/opencode/skills/` |
| `~/.claude/skills/<name>/` | 全局（Claude Code 兼容） | 同上 |
| `~/.agents/skills/<name>/` | 全局 | 同上 |

或者在 `opencode.json` 自定义路径：

```json
{
  "skills": {
    "path": ["~/repos/devflow/skills"]
  }
}
```

这样直接用 git checkout 出来的 `skills/mdc-bug-patterns/` 即可，不用 copy。

**验证 opencode 找到了 skill：**

```bash
opencode run "list available skills and their descriptions"
# 应该能看到 mdc-bug-patterns
```

`SKILL.md` 的 frontmatter 已经带了 `description: "Use when reviewing C/C++ codebases..."`，opencode 会在你的 prompt 提到 C/C++ audit / 锁审计 / 内存安全 等关键词时**自动加载**这个 skill，不用手动 `--agent` 切换。

---

## 2. 架构选择

opencode 长跑有两条路。**强烈推荐 A**（其它任何 LLM CLI / cloud agent 通用）。

### 架构 A: tmux + opencode serve + 外部 driver (推荐)

```
┌──────────── tmux session "mdc-audit" ────────────┐
│                                                   │
│  pane 0: opencode serve --port 4096               │
│           (常驻 agent server, 不冷启)              │
│                                                   │
│  pane 1: bash driver loop:                        │
│           per unit:                               │
│             1. unit = run_audit.py next            │
│             2. opencode run --attach \            │
│                  http://localhost:4096 \          │
│                  --format json \                  │
│                  --prompt-file /tmp/prompt.md     │
│             3. parse output → save findings.json  │
│             4. run_audit.py record                 │
│                                                   │
│  pane 2 (按需): run_audit.py status               │
│                                                   │
└───────────────────────────────────────────────────┘
```

**为什么这样**：
- 每单元一次 `opencode run` = 每单元一个**全新的会话** = 上下文不会跨单元累积，不会爆。
- `opencode serve` 常驻避免每单元都冷启 model 客户端 / 工具索引。
- driver bash 在 tmux 里跑，SSH 断了不会杀它；driver 自己有 retry 逻辑，opencode 偶发失败可恢复。
- `run_audit.py` 做所有 checkpoint，挂了 re-launch driver 即可续跑。

### 架构 B: 单个长跑的 opencode 交互会话 (不推荐过夜)

```bash
opencode    # interactive TUI
> Use mdc-bug-patterns to audit src/ for lock-usage issues. Drive the workflow
> through scripts/run_audit.py with checkpoints in audit/. Continue running
> until complete.
```

**问题**：
- opencode 会话本身就是长跑那个东西。退出 TUI / 网络断 / context 爆，整个会话死。
- 上下文一直累积；> 1h 的审计大概率 token 超限。
- 适合 < 30 分钟的小审计，**不适合过夜**。

下面只覆盖架构 A。

---

## 3. 启动过夜审计 (架构 A 完整流程)

### 3.1 一次性: 初始化 audit 目录

```bash
cd /path/to/your/repo

# 决定审什么。最常见: 锁 + 并发
SKILL_DIR=~/.config/opencode/skills/mdc-bug-patterns
$SKILL_DIR/scripts/run_audit.py init \
    --scope src/ \
    --specialty lock-usage --specialty concurrency-and-isr \
    --repo "$(git remote get-url origin)" \
    --reviewer "auto-overnight" \
    --partial-every-units 50 \
    --partial-every-seconds 1800 \
    --out audit/
```

输出确认：
```
[init] candidates → audit/candidates.jsonl  (1247 lines)
[init] units → audit/units.jsonl  (412 units)
audit initialised at audit
  units: 412; specialties: ['lock-usage', 'concurrency-and-isr']
  resume: see audit/HOWTO_RESUME.md
```

### 3.2 启动 tmux + opencode serve + driver

把这个保存为 `audit-overnight-opencode.sh`（仓库里也提供了一份在 `scripts/audit-overnight-opencode.sh`）：

```bash
#!/usr/bin/env bash
# audit-overnight-opencode.sh — 单脚本启动过夜审计
# Usage: ./audit-overnight-opencode.sh <audit-dir> [opencode-port]
set -euo pipefail

AUDIT_DIR="${1:?usage: $0 <audit-dir> [port]}"
PORT="${2:-4096}"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"   # 假设脚本在 skills/.../scripts/
SESSION="mdc-audit-$(basename "$AUDIT_DIR")"

if [[ ! -f "$AUDIT_DIR/meta.json" ]]; then
    echo "ERR: $AUDIT_DIR/meta.json not found. Run 'run_audit.py init' first." >&2
    exit 2
fi

# pane 0: opencode serve
tmux new-session -d -s "$SESSION" -- bash -lc "
    echo '[serve] starting opencode serve on :$PORT'
    opencode serve --port $PORT 2>&1 | tee -a $AUDIT_DIR/opencode-serve.log
"

# 等 server 起来
sleep 5
for i in 1 2 3 4 5; do
    if curl -sf http://localhost:$PORT/ >/dev/null 2>&1; then break; fi
    sleep 2
done

# pane 1: driver loop
tmux split-window -t "$SESSION":0 -- bash -lc "
    cd '$PWD'
    SKILL_DIR='$SKILL_DIR'
    AUDIT_DIR='$AUDIT_DIR'
    PORT=$PORT

    # ---- Pass 3 driver loop ----
    while true; do
        UNIT_JSON=\$(\$SKILL_DIR/scripts/run_audit.py next --out \$AUDIT_DIR 2>/dev/null) || {
            echo '[driver] no more pending units → moving to Pass 3.5'
            break
        }
        UNIT_ID=\$(echo \"\$UNIT_JSON\" | python3 -c 'import json,sys; print(json.load(sys.stdin)[\"unit_id\"])')
        FILE=\$(echo \"\$UNIT_JSON\" | python3 -c 'import json,sys; print(json.load(sys.stdin)[\"file\"])')
        L1=\$(echo \"\$UNIT_JSON\" | python3 -c 'import json,sys; print(json.load(sys.stdin)[\"line_start\"])')
        L2=\$(echo \"\$UNIT_JSON\" | python3 -c 'import json,sys; print(json.load(sys.stdin)[\"line_end\"])')
        SPECIALTY=\$(echo \"\$UNIT_JSON\" | python3 -c '
import json, sys
d = json.load(sys.stdin)
sigs = [s.split(\":\")[0] for s in d.get(\"signals\", []) if not s.startswith(\"primitive:\") and not s.startswith(\"size:\")]
print(sigs[0].split(\"-\")[0] if sigs else \"memory-safety\")
')

        # 选 specialty 文件 (粗略: 按第一个 template 前缀; 复杂场景在 prompt 里加多个)
        case \"\$SPECIALTY\" in
            mem*|ptr*) SPEC_FILE=memory-safety ;;
            con*|isr*|rtos*) SPEC_FILE=concurrency-and-isr ;;
            res*) SPEC_FILE=resource-management ;;
            int*|div*|empty*) SPEC_FILE=logic-and-numeric ;;
            emb*) SPEC_FILE=embedded-hardware ;;
            *) SPEC_FILE=lock-usage ;;
        esac

        FINDINGS=/tmp/audit-findings-\$\$.json
        echo '[]' > \$FINDINGS

        cat > /tmp/audit-prompt.md <<EOF
You are doing Pass 3 of an mdc-bug-patterns C/C++ embedded audit.

UNIT TO REVIEW
  unit_id:   \$UNIT_ID
  file:      \$FILE
  lines:     \$L1..\$L2

INSTRUCTIONS
  1. Read \$FILE lines \$L1..\$L2 fully (and the enclosing class declaration if member state involved).
  2. Read up to 20 callers via 'rg -n' for context if caller invariants matter.
  3. Apply ALL relevant templates from the specialty checklist at:
       \$SKILL_DIR/references/templates/\$SPEC_FILE.md
  4. For each finding, follow the per-template 'verification' checklist; build the 'required_evidence'
     block; explicitly rule out the listed 'fp_filters' (see \$SKILL_DIR/references/false-positive-filters.md).
  5. Output a JSON array of findings to: \$FINDINGS
     Each finding MUST follow the schema in \$SKILL_DIR/references/reporting.md (id, template_id, name,
     category, severity, confidence, location, summary, required_evidence,
     false_positive_filters_ruled_out, fix_suggestions, context).
     If no findings, output '[]'.
  6. Reply with: 'OK: wrote N findings to \$FINDINGS'
EOF

        # opencode dispatch with retry/backoff
        SUCCESS=0
        for ATTEMPT in 1 2 3; do
            timeout 600 opencode run --attach http://localhost:\$PORT --format json \\
                < /tmp/audit-prompt.md \\
                >> \$AUDIT_DIR/opencode-run.log 2>&1 && { SUCCESS=1; break; }
            sleep \$((30 * ATTEMPT))
            echo \"[driver] retry \$ATTEMPT for \$UNIT_ID\"
        done

        if [[ \$SUCCESS -eq 1 && -f \$FINDINGS ]]; then
            \$SKILL_DIR/scripts/run_audit.py record --out \$AUDIT_DIR \\
                --unit-id \"\$UNIT_ID\" --findings \$FINDINGS
        else
            \$SKILL_DIR/scripts/run_audit.py mark --out \$AUDIT_DIR \\
                --unit-id \"\$UNIT_ID\" --status failed \\
                --reason 'opencode dispatch failed after 3 retries'
        fi
        rm -f \$FINDINGS
    done

    # ---- Pass 3.5 driver loop ----
    echo '[driver] starting Pass 3.5 (second-pass verdicts)'
    while true; do
        FINDING_JSON=\$(\$SKILL_DIR/scripts/run_audit.py next-verdict --out \$AUDIT_DIR 2>/dev/null) || {
            echo '[driver] all verdicts done → finalize'
            break
        }
        FID=\$(echo \"\$FINDING_JSON\" | python3 -c 'import json,sys; print(json.load(sys.stdin)[\"id\"])')
        VERDICT=/tmp/audit-verdict-\$\$.json
        echo \"\$FINDING_JSON\" > /tmp/audit-finding.json

        cat > /tmp/audit-verdict-prompt.md <<EOF
You are doing Pass 3.5 (independent second-pass review). YOU MUST NOT TRUST the first-pass agent's
reasoning. Re-read the source code and re-derive the verdict.

Repository root: \$PWD
Finding to review: see /tmp/audit-finding.json (single object, NOT an array).

Follow the procedure + output format in:
  \$SKILL_DIR/references/second-pass-review.md

Output a SINGLE verdict object (NOT an array) to: \$VERDICT
Reply with: 'OK: wrote verdict to \$VERDICT'
EOF

        timeout 600 opencode run --attach http://localhost:\$PORT --format json \\
            < /tmp/audit-verdict-prompt.md \\
            >> \$AUDIT_DIR/opencode-run.log 2>&1 || true

        if [[ -f \$VERDICT ]]; then
            \$SKILL_DIR/scripts/run_audit.py record-verdict --out \$AUDIT_DIR \\
                --finding-id \"\$FID\" --verdict \$VERDICT
        else
            \$SKILL_DIR/scripts/run_audit.py mark --out \$AUDIT_DIR \\
                --finding-id \"\$FID\" --status failed \\
                --reason 'opencode verdict dispatch failed'
        fi
        rm -f \$VERDICT /tmp/audit-finding.json
    done

    # ---- finalize ----
    \$SKILL_DIR/scripts/run_audit.py finalize --out \$AUDIT_DIR
    echo '[driver] DONE; final report at \$AUDIT_DIR/bug_report.xlsx'
"

echo "started overnight audit in tmux session: $SESSION"
echo "  attach:  tmux attach -t $SESSION"
echo "  status:  $SKILL_DIR/scripts/run_audit.py status --out $AUDIT_DIR"
echo "  partial: ls -lt $AUDIT_DIR/partial_reports/ | head"
```

### 3.3 启动

```bash
chmod +x ~/.config/opencode/skills/mdc-bug-patterns/scripts/audit-overnight-opencode.sh
~/.config/opencode/skills/mdc-bug-patterns/scripts/audit-overnight-opencode.sh /path/to/your/repo/audit/
```

输出：
```
started overnight audit in tmux session: mdc-audit-audit
  attach:  tmux attach -t mdc-audit-audit
  status:  .../run_audit.py status --out /path/.../audit/
  partial: ls -lt /path/.../audit/partial_reports/ | head
```

合上电脑去睡觉。

### 3.4 中途检查

任何时刻在另一个 shell：

```bash
# 进度
~/.config/opencode/skills/mdc-bug-patterns/scripts/run_audit.py status --out /path/.../audit/

# 最近的部分 Excel
ls -lt /path/.../audit/partial_reports/ | head -3

# driver 还活着吗
cat /path/.../audit/heartbeat.txt
kill -0 $(awk '{print $1}' /path/.../audit/heartbeat.txt) && echo OK || echo DEAD

# tmux 看实时日志
tmux attach -t mdc-audit-audit    # Ctrl+B, D 离开 (不杀)
```

---

## 4. 早上的工作流

### 情况 A: 跑完了

```bash
# 1. 最终报告应该已经生成
ls /path/.../audit/bug_report.xlsx

# 2. 关 tmux session
tmux kill-session -t mdc-audit-audit

# 3. 杀 opencode serve (可选; 没有也不太占资源)
pkill -f 'opencode serve --port 4096'  # 注意只杀这一个端口的

# 4. 打开 Excel 评审
libreoffice --calc /path/.../audit/bug_report.xlsx
```

### 情况 B: 还在跑

```bash
# 进度看一眼
~/.../scripts/run_audit.py status --out /path/.../audit/
#  units: pending=42 / done=370 / failed=0 / total=412
#  ETA: ~25m

# 不挂掉它就好。可以打开最新部分报告先看看
libreoffice --calc $(ls -t /path/.../audit/partial_reports/*.xlsx | head -1)
```

### 情况 C: driver 挂了 / heartbeat 死了 (resume)

```bash
# 1. 先确认确实死了
kill -0 $(awk '{print $1}' /path/.../audit/heartbeat.txt) || echo CONFIRMED DEAD

# 2. 杀残余 tmux session (如果 opencode serve 也死了)
tmux kill-session -t mdc-audit-audit 2>/dev/null

# 3. 重新启动 — driver 会自动从 audit/state.json 续跑, 已审单元不会重审
~/.../scripts/audit-overnight-opencode.sh /path/.../audit/
```

`run_audit.py next` 只返回 `status="pending"` 的单元；任何 `status="done"` 或 `status="in-progress"` 的都跳过。所以 resume 是无损的（最坏丢掉 1 个被 mark 成 in-progress 但没 record 的单元，可以用 `mark --status pending` 把它放回队列）。

### 情况 D: 想换审计专项 / 重头开始

```bash
~/.../scripts/run_audit.py init --force --scope src/ --specialty memory-safety --out audit-mem/
# 老的 audit/ 不动, 新建 audit-mem/
```

---

## 5. opencode-specific gotchas

### 5.1 非交互模式的权限规则

opencode 在 `opencode run` 非交互模式下默认对某些工具加 deny rules（防止意外破坏）。审计脚本需要写文件 (`/tmp/audit-findings-*.json`) — 默认应该是允许的，但如果遇到 `permission denied` 类错误，在 `~/.config/opencode/opencode.json` 里加：

```json
{
  "permissions": {
    "allow": ["bash", "write", "read", "rg"]
  }
}
```

或在 prompt 里明确："Write the findings JSON file without asking permission."

### 5.2 `opencode serve` 不一定保留状态

`--attach http://localhost:4096` 让每个 `opencode run` 共享 model 后端，**但每次仍然是新会话**（除非 `--continue` / `--session ID`）。这正是我们要的——单元间不串扰上下文。

如果你看到 driver 抱怨 "session expired" 或 connect refused：

```bash
# 重启 serve
pkill -f 'opencode serve --port 4096'
nohup opencode serve --port 4096 >> audit/opencode-serve.log 2>&1 &
```

driver 下次循环会重新连上。

### 5.3 model 选择 / 成本

driver 默认用 opencode 当前的 default model。给长跑指定一个性价比好的：

```bash
# 在 prompt 模板里加 --model:
opencode run --attach http://localhost:4096 \
    --model anthropic/claude-sonnet-4 \
    --format json < prompt.md
```

或在 `opencode.json` 全局设：

```json
{
  "model": "anthropic/claude-sonnet-4"
}
```

子代理 Pass 3.5 复核可以用稍弱/便宜的模型（评审者只是验证，不是创造）：

```bash
# Pass 3.5 prompt 那段加:
--model anthropic/claude-haiku-4
```

### 5.4 `opencode run` 超时

default 没有上限；脚本里我用了 `timeout 600`（10 分钟）。Pass 3 单单元如果 10 分钟没回来，driver retry；连续失败 3 次后 `mark --status failed`，继续下一个。这对应 [`long-running-audits.md`](long-running-audits.md) 里"no single unit may stall the queue"的契约。

### 5.5 `opencode run` 的输出格式

driver 用 `--format json` 让 opencode 把工具调用结果结构化输出，但 driver 实际只关心**它写到 `$FINDINGS` 文件里没有**。无论 opencode stdout 输出什么，只要文件存在就 record；不存在就视为失败。这是为了对 opencode 输出格式变化鲁棒。

---

## 6. 命令速查

| 想做什么 | 命令 |
|---|---|
| 装 skill 到全局 | `cp -r mdc-bug-patterns ~/.config/opencode/skills/` |
| 验证装了 | `opencode run "list available skills"` |
| 一次性 init 审计 | `run_audit.py init --scope src/ --specialty NAME --out audit/` |
| 启动过夜 driver | `audit-overnight-opencode.sh /path/to/audit/` |
| 查进度 | `run_audit.py status --out audit/` |
| 看最新部分报告 | `ls -t audit/partial_reports/ \| head` |
| 看 driver 是否活着 | `kill -0 $(awk '{print $1}' audit/heartbeat.txt) && echo OK \|\| echo DEAD` |
| Resume 已挂的 driver | `tmux kill-session -t mdc-audit-...; audit-overnight-opencode.sh /path/.../audit/` |
| 强制重头开始 | `run_audit.py init --force ...` |
| 单个失败单元放回队列 | `run_audit.py mark --out audit/ --unit-id ID --status pending` |
| 跑完后 attach session 看日志 | `tmux attach -t mdc-audit-...` |
| 杀干净所有相关进程 | `tmux kill-session -t mdc-audit-...; pkill -f 'opencode serve --port 4096'` |
