# Review 记录模板

## 保存路径

| review_type | 默认路径 |
|---|---|
| spec | `features/<active>/reviews/spec-review-YYYY-MM-DD.md` |
| arch-design | `features/<active>/reviews/arch-design-review-YYYY-MM-DD.md` |
| ar-design | `features/<active>/reviews/ar-design-review-YYYY-MM-DD.md` |
| tasks | `features/<active>/reviews/tasks-review-YYYY-MM-DD.md` |

若 `AGENTS.md` 声明了等价路径，按映射保存。

## 结论字段映射

若使用英文字段：
- `通过` → `PASS`
- `需修改` → `REVISE`
- `阻塞` → `BLOCKED`

## 记录结构

```markdown
## 结论

通过 | 需修改 | 阻塞

## 发现项

- [critical|important|minor][USER-INPUT|LLM-FIXABLE][rule_id] 问题

rule_id 按 review_type 对应：
- spec: Q1-Q8, A1-A6, C1-C5, G1-G3, GS1-GS6
- arch-design: AD1-AD8, AA1-AA9
- ar-design: AR1-AR9, RA1-RA13
- tasks: TR1-TR6

## 缺失或薄弱项

- 条目

## 下一步

- `通过`：对应真人确认（规格/架构设计/AR设计/任务）
- `需修改`：对应 authoring skill（`mdc-specify`/`mdc-arch-design`/`mdc-ar-design`/`mdc-tasks`）
- `阻塞`：对应 authoring skill 或 `using-mdc-workflow`

## 记录位置

- 按上方保存路径表

## 交接说明

- 真人确认：仅当结论为 `通过`；interactive 下等待真人，auto 下写 approval record
- authoring skill：用于所有需要回修内容的场景
- `using-mdc-workflow`：仅在 route / stage / 证据链冲突时使用
```

## 结构化返回 JSON

正常返回示例：

```json
{
  "conclusion": "需修改",
  "next_action_or_recommended_skill": "mdc-specify",
  "record_path": "实际写入的 review 记录路径",
  "key_findings": ["[important][USER-INPUT][Q2] 响应时间缺少可验证阈值"],
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "finding_breakdown": [
    {
      "severity": "important",
      "classification": "USER-INPUT",
      "rule_id": "Q2",
      "summary": "响应时间缺少可验证阈值"
    }
  ]
}
```

Precheck blocked 示例：

```json
{
  "conclusion": "阻塞",
  "next_action_or_recommended_skill": "using-mdc-workflow",
  "record_path": "实际写入的 review 记录路径",
  "key_findings": ["当前没有稳定 spec draft，且 stage/approval evidence 冲突，需先回到 using-mdc-workflow 重判"],
  "needs_human_confirmation": false,
  "reroute_via_router": true
}
```

## 返回规则

| review_type | 结论 | next_action | needs_human_confirmation | reroute_via_router |
|---|------|------------|------------------------|-------------------|
| spec | `通过` | `规格真人确认` | true | false |
| spec | `需修改` | `mdc-specify` | false | false |
| spec | `阻塞`(内容回修) | `mdc-specify` | false | false |
| arch-design | `通过` | `架构设计真人确认` | true | false |
| arch-design | `需修改` | `mdc-arch-design` | false | false |
| arch-design | `阻塞`(内容回修) | `mdc-arch-design` | false | false |
| ar-design | `通过` | `AR设计真人确认` | true | false |
| ar-design | `需修改` | `mdc-ar-design` | false | false |
| ar-design | `阻塞`(内容回修) | `mdc-ar-design` | false | false |
| tasks | `通过` | `任务真人确认` | true | false |
| tasks | `需修改` | `mdc-tasks` | false | false |
| tasks | `阻塞`(内容回修) | `mdc-tasks` | false | false |
| any | `阻塞`(route/stage冲突) | `using-mdc-workflow` | false | true |

Precheck blocked 沿用 `阻塞` 返回规则，区别只是跳过正式 rubric。

## 状态同步

若使用 `progress.md` 且 approval step 已完成，同步更新：
- 对应文档状态字段
- `progress.md` Current Stage
- `progress.md` Next Action Or Recommended Skill

这些更新由父会话在 approval step 完成后执行；reviewer subagent 不代替父会话写入批准结论。
