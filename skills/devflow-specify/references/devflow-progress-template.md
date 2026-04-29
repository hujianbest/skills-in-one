# devflow 工作项进度模板

使用说明：

- 默认保存路径：`features/<工作项ID>-<slug>/progress.md`。
- `Next Action Or Recommended Skill（下一步动作或推荐 Skill）` 只能写 canonical `devflow-*` 节点名，不允许自由文本，不允许写 `using-devflow`。
- 若项目在 `AGENTS.md` 中声明等价模板或路径，优先遵循项目约定。

## 标识信息

- 工作项类型:                          # SR / AR / DTS / CHANGE
- 工作项 ID:
- 所属组件:                            # AR / DTS / CHANGE 必填；SR 可空
- 所属子系统:                          # SR 必填；AR / DTS / CHANGE 可空
- 关联 IR:
- 关联 SR:                             # AR 必填
- 关联 AR:                             # DTS 影响功能需求时填写
- AR 拆分候选:                         # 仅 SR 适用；spec-review 后定稿，analysis closeout 时写入 closeout.md

## 工作流状态

- 当前阶段:                            # canonical devflow-* 节点
- 工作流 Profile:                      # requirement-analysis / standard / component-impact / hotfix / lightweight
- 执行模式:                            # interactive / auto
- 当前活跃任务:                        # task queue preflight 通过后填写唯一 active task；无则留空
- 任务计划路径:                        # features/<id>/tasks.md
- 任务看板路径:                        # features/<id>/task-board.md
- 最后更新:

## 待完成评审与门禁

- 待完成评审与门禁:
- 阻塞项:

## 进度说明

- 本轮变化:
- 证据路径:                            # 例：features/<id>/evidence/...
- 未关闭风险:

## 追溯锚点

- IR / SR / AR 引用:
- 组件设计引用:
- AR 设计引用:
- 测试设计引用:

## 下一步

- 下一步动作或推荐 Skill:              # canonical devflow-* 节点
- 备注:
