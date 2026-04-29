# Verification Record Template

> 配套 `devflow-completion-gate/SKILL.md`。本模板继承旧 MDC 通用验证记录结构，用于保存命令、结果摘要、新鲜度锚点和门禁结论。

## Metadata

- Verification Type:                       # unit / integration / simulation / build / static-analysis / regression / completion
- Work Item Type:                          # AR / DTS / CHANGE
- Work Item ID:
- Current Active Task:
- Scope:
- Date:
- Record Path:
- Worktree Path / Worktree Branch（若适用）:

## Upstream Evidence Consumed

- Implementation Handoff:
- Review / Gate Records:
  - Spec Review:
  - Component Design Review:
  - AR Design Review:
  - Task Queue Preflight:
  - Test Check:
  - Code Review:
- Task / Progress Anchors:
  - Task Plan:
  - Task Board:
  - Progress:
- Traceability:

## Claim Being Verified

- Claim:
- Claim Type: task-level completion / work-item completion / regression / environment recovery

## Verification Scope

- Included Coverage:
- Uncovered Areas:
- Rationale For Scope:

## Commands And Results

### Command 1

```text
<command>
```

- Exit Code:
- Summary:
- Notable Output:
- Evidence Path:

### Command 2（如适用）

```text
<command>
```

- Exit Code:
- Summary:
- Notable Output:
- Evidence Path:

## Freshness Anchor

- Commit / Build ID:
- Toolchain / Target:
- Configuration:
- Why this evidence is for the latest relevant code state:
- Output Log / Terminal / Artifact:

## Embedded Risk Audit

| 维度 | 状态 | 证据 / 说明 |
|---|---|---|
| 内存（边界 / 池化 / 栈 / 生命周期） | clean / documented-debt / critical-open / N/A |  |
| 并发（中断 / 锁 / 临界区 / 竞态） | clean / documented-debt / critical-open / N/A |  |
| 实时性（latency / deadline / 调度） | clean / documented-debt / critical-open / N/A |  |
| 资源生命周期（句柄 / 文件 / 缓冲区） | clean / documented-debt / critical-open / N/A |  |
| 错误处理（输入校验 / 错误码 / 降级） | clean / documented-debt / critical-open / N/A |  |
| ABI / API 兼容 | clean / documented-debt / critical-open / N/A |  |
| SOA 边界 / 跨组件依赖 | clean / documented-debt / critical-open / N/A |  |

## Conclusion

- Conclusion: `通过` | `需修改` | `阻塞`
- Verdict Rationale:
- Next Action Or Recommended Skill:
- reroute_via_router: true / false

## Scope / Remaining Work Notes

- Remaining Task Decision（若适用）:
- If unique next-ready task exists:
- If no ready / pending tasks remain:
- If task-board state conflicts:
- Notes:

## Related Artifacts

- Related Artifacts:
