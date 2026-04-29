# 工作项：<工作项ID>-<slug>

使用说明：

- 默认保存路径：`features/<工作项ID>-<slug>/README.md`。
- 作为单个 SR / AR / DTS / CHANGE 的入口索引，记录当前状态和关键工件。

## 元数据

- 工作项类型:                          # SR / AR / DTS / CHANGE
- 工作项 ID:                            # 例：SR1234 / AR12345 / DTS67890
- 标题:
- 所属组件:                            # AR / DTS / CHANGE 必填；SR 可空
- 所属子系统:                          # SR 必填；AR / DTS / CHANGE 可空
- 关联 IR:
- 关联 SR:
- 关联 AR:
- Owner / 经办人:
- 创建日期:

## 状态快照

- 当前阶段:
- 工作流 Profile:
- 执行模式:
- 待完成评审与门禁:
- 下一步动作或推荐 Skill:
- 收尾类型:                            # closeout 后写入：implementation / analysis / blocked
- 收尾结论:                            # 未 closeout 时留空：closed / blocked

## 过程工件

| 工件 | 路径 | 状态 |
|---|---|---|
| Requirement | `requirement.md` | pending / present / approved |
| Traceability | `traceability.md` | pending / present |
| Component Design Draft | `component-design-draft.md` | N/A / pending / present / approved |
| AR Design Draft | `ar-design-draft.md` | N/A / pending / present / approved |
| Tasks | `tasks.md` | N/A / pending / present / approved |
| 任务看板 | `task-board.md` | N/A / pending / present |
| Implementation Log | `implementation-log.md` | N/A / pending / present |
| Evidence | `evidence/` | N/A / pending / present |
| 完成门禁 | `completion.md` | N/A / pending / present |
| 收尾 | `closeout.md` | pending / present |

## 评审与门禁

| 节点 | 记录路径 | 结论 | 日期 | 适用工作项 |
|---|---|---|---|---|
| spec-review | `reviews/spec-review.md` |  |  | SR / AR / DTS / CHANGE |
| component-design-review | `reviews/component-design-review.md` |  |  | SR / AR(component-impact) |
| ar-design-review | `reviews/ar-design-review.md` |  |  | AR / DTS / CHANGE |
| tasks-review | `reviews/tasks-review.md` |  |  | AR / DTS / CHANGE |
| test-check | `reviews/test-check.md` |  |  | AR / DTS / CHANGE |
| code-review | `reviews/code-review.md` |  |  | AR / DTS / CHANGE |
| completion-gate | `completion.md` |  |  | AR / DTS / CHANGE |

## 关联长期资产

| 长期资产 | 路径 | 本工作项是否触发同步 | 备注 |
|---|---|---|---|
| Component Design | `docs/component-design.md` | yes / no / N/A |  |
| AR Design | `docs/ar-designs/AR<id>-<slug>.md` | yes / no / N/A |  |
| Interfaces | `docs/interfaces.md` | yes / no / N/A（项目未启用） |  |
| Dependencies | `docs/dependencies.md` | yes / no / N/A（项目未启用） |  |
| Runtime Behavior | `docs/runtime-behavior.md` | yes / no / N/A（项目未启用） |  |

## 备注

- 
