# devflow Review Record

使用说明：

- 这是 devflow review 记录通用模板，可用于 spec-review / component-design-review / ar-design-review / tasks-review / test-check / code-review。
- **默认保存路径：`features/<Work Item Id>-<slug>/reviews/<kind>.md`**
  - `spec-review.md` / `component-design-review.md` / `ar-design-review.md` / `tasks-review.md` / `test-check.md` / `code-review.md`
- 若项目在 `AGENTS.md` 中声明了等价路径或专用模板，优先遵循项目约定。

## Metadata

- Review Type:                             # spec-review / component-design-review / ar-design-review / tasks-review / test-check / code-review
- Work Item Type:                          # AR / DTS / CHANGE
- Work Item ID:
- Owning Component:
- Reviewer:                                # 独立 reviewer 角色或 subagent
- Date:
- Record Path:

## Inputs Consumed

- Primary Artifact:                        # 被评审对象的路径与版本锚点
- Commit SHA:
- Branch:
- Changed Files / Diff Stat:
- Supporting Context:
  - Spec / Requirement:
  - Component Design:
  - AR Design:
  - Task Plan / Task Board:
  - Test Check Record:
  - Implementation Handoff（如适用）:
  - Evidence Paths（如适用）:
- AGENTS.md / Team Standards Refs:

## Change Analysis（code-review 适用）

逐个文件 / 函数分析关键变化。非 code-review 类型可写 N/A。

| File / Function | Change Summary | Review Notes |
|---|---|---|
|  |  |  |

## Multi-Dimension Scoring

| 维度 | 0-10 | 关键证据 |
|---|---|---|
| <按节点类型填入维度，如：可追溯性 / 可设计性 / 模板符合度 / 测试覆盖 / 代码安全 / 嵌入式风险 等> |  |  |

任一关键维度 < 6 不得给出 `通过`。

## Findings

每个问题必须包含：位置、问题描述、重要性、修复建议。code-review 问题位置优先写成 `file_path:line_number`；无法定位到行时，写函数 / 类 / diff hunk anchor。

| ID | Severity | Classification | Rule ID | Anchor / Location | 描述 | 重要性 | 建议修复 |
|---|---|---|---|---|---|---|---|
| F-001 | critical / important / minor | USER-INPUT / LLM-FIXABLE / TEAM-EXPERT | 例：S2、A4、CR3、TC2 |  |  |  |  |

分类约定：

- `USER-INPUT`：缺业务事实 / 外部决策 / 优先级冲突，需要团队负责人或需求负责人拍板
- `LLM-FIXABLE`：缺 wording、章节、示例、明显逻辑漏洞，可以由开发人员定向回修
- `TEAM-EXPERT`：需要模块架构师 / 资深工程师专业判断，例如组件边界、SOA 接口、嵌入式风险

## Verdict

- Conclusion: `通过` | `需修改` | `阻塞`
- Verdict Rationale:
- Next Action Or Recommended Skill:        # canonical devflow-* 节点
- reroute_via_router:                      # true / false（结论无法唯一映射下一步时为 true 并指向 devflow-router）

## Code Review Summary（code-review 适用）

### Strengths（优点）

- 

### Test Coverage Analysis

- 与 `devflow-test-checker` 结论是否一致:
- 覆盖的关键行为:
- 未覆盖或需补强的风险:
- Mock / Stub / Sim 边界是否合理:

### Embedded Risk Assessment

| 维度 | 结论 | 证据 / 说明 |
|---|---|---|
| 内存 / 资源生命周期 | clean / issue / N/A |  |
| 并发 / 实时性 | clean / issue / N/A |  |
| 错误处理 / 降级 | clean / issue / N/A |  |
| ABI / API 兼容 | clean / issue / N/A |  |
| SOA 边界 / 跨组件依赖 | clean / issue / N/A |  |
| 静态分析 / 编译告警 | clean / issue / N/A |  |

### Merge Readiness

- Merge Readiness: `Ready to merge` | `Ready to merge with fixes` | `Not ready`
- Reason:

映射规则：

| devflow Verdict | Merge Readiness |
|---|---|
| `通过` 且无 critical / important 未闭环 | `Ready to merge` |
| `通过` 但有需合并前处理的非阻塞项，或 `需修改` 可定向修复 | `Ready to merge with fixes` |
| `阻塞`，或存在安全 / 稳定性 / SOA 边界 / 嵌入式 critical 风险 | `Not ready` |

## Follow-up Actions

- Action:
- Owner:
- Status:

## Notes

- Additional Notes:
