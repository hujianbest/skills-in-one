# devflow 收尾记录模板

使用说明：

- 默认保存路径：`features/<工作项ID>-<slug>/closeout.md`。
- 覆盖两类收尾：
  - 实现收尾：AR / DTS / CHANGE，基于 `devflow-completion-gate` 通过。
  - 分析收尾：SR，基于 `devflow-spec-review` 或 `devflow-component-design-review` 通过。

## 收尾摘要

- 工作项类型:                          # SR / AR / DTS / CHANGE
- 工作项 ID:
- 所属组件:                            # AR / DTS / CHANGE 必填
- 所属子系统:                          # SR 必填
- 工作流 Profile:                      # requirement-analysis / standard / component-impact / hotfix / lightweight
- 收尾类型: `implementation` | `analysis` | `blocked`
- 收尾结论: `closed` | `blocked`
- 基于的上游结论:                      # implementation: features/<id>/completion.md
                                           # analysis(SR 不修订组件设计): features/<id>/reviews/spec-review.md
                                           # analysis(SR 修订组件设计): features/<id>/reviews/component-design-review.md
- 日期:

## 证据矩阵

按收尾类型填写。`N/A`（不适用本类型）不算 blocked。

| 工件 | 路径 | 实现收尾 | 分析收尾 |
|---|---|---|---|
| 需求 | `requirement.md` | present | present |
| 规格评审 | `reviews/spec-review.md` | 通过 | 通过 |
| 组件设计评审 | `reviews/component-design-review.md` | 通过 / N/A | 通过 / N/A |
| AR 设计评审 | `reviews/ar-design-review.md` | 通过 | **N/A** |
| 任务队列前置检查 | `tasks.md` / `task-board.md` | passed | **N/A** |
| 任务看板 | `task-board.md` | all done / cancelled | **N/A** |
| 测试有效性评审 | `reviews/test-check.md` | 通过 | **N/A** |
| 代码检视 | `reviews/code-review.md` | 通过 | **N/A** |
| 完成门禁 | `completion.md` | 通过 | **N/A** |

## 长期资产同步

| 长期资产 | 路径 | 本次是否同步 | 备注 |
|---|---|---|---|
| 组件实现设计 | `docs/component-design.md` | yes / no / N/A |  |
| AR 实现设计 | `docs/ar-designs/AR<id>-<slug>.md` | yes / N/A | implementation closeout 的 AR 工作项必填；SR / DTS 不修改 AR 设计时写 N/A |
| Interfaces（可选） | `docs/interfaces.md` | yes / no / N/A（项目未启用） |  |
| Dependencies（可选） | `docs/dependencies.md` | yes / no / N/A（项目未启用） |  |
| Runtime Behavior（可选） | `docs/runtime-behavior.md` | yes / no / N/A（项目未启用） |  |

## AR 拆分候选（仅 Analysis closeout 必填；其他类型写 N/A）

| 字段 | 说明 |
|---|---|
| Candidate ID | 例 `CAR-001`（SR 内部编号） |
| 范围 | 1-2 句候选 AR 范围 |
| 所属组件 | 候选 AR 所属组件（必须唯一） |
| 覆盖 SR 行 | 引用本 SR 的若干 row ID |
| 优先级提示 | 团队约定的优先级提示 |
| 复杂度估计 | `S` / `M` / `L` |
| 交接 Owner | 候选 AR 应交给哪位开发负责人 / 团队 |
| 备注 | 依赖关系、与其他候选的拆分边界等 |

如本 SR 显式声明“无可拆分 AR”，写明理由并记录需求负责人确认。

## 状态同步

- 最终 `Current Stage`:                   # closed / completed
- 最终 `Next Action Or Recommended Skill（下一步动作或推荐 Skill）`: # null（已完成）
- 未关闭风险记录到:                       # 例：组件级 risk log / backlog 路径

## 交接

- 提交 / 合并状态:                         # branch / MR / PR 信息（implementation closeout）
                                           # 或候选 AR 交付清单（analysis closeout）
- 团队同步说明:
- 限制 / 未关闭项:
