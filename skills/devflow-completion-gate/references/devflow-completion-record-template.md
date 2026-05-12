# devflow 完成门禁记录模板

使用说明：

- 默认保存路径：`features/<工作项ID>-<slug>/completion.md`。
- 用于记录 task-level 或 work-item-level 的完成判断、验证命令、新鲜度锚点和下一步。

## 元数据

- 工作项类型:                          # AR / DTS / CHANGE
- 工作项 ID:
- 所属组件:
- 工作流 Profile:                      # standard / component-impact / hotfix / lightweight
- 当前活跃任务:
- 任务计划路径:
- 任务看板路径:
- 日期:
- 记录路径:

## 上游证据包

| 工件 | 路径 | 状态 |
|---|---|---|
| 需求 / 规格 | `requirement.md` | present / approved |
| 规格评审 | `reviews/spec-review.md` | 通过 / 需修改 / 阻塞 |
| 组件设计 | `docs/component-design.md` | unchanged / updated / N/A |
| 组件设计评审 | `reviews/component-design-review.md` | 通过 / N/A |
| AR 设计 | `ar-design-draft.md` + `docs/ar-designs/AR<id>-<slug>.md` | approved |
| AR 设计评审 | `reviews/ar-design-review.md` | 通过 |
| 任务队列前置检查 | `tasks.md` / `task-board.md` | passed |
| 实现日志 | `implementation-log.md` | present |
| 测试证据 | `evidence/unit/`、`evidence/integration/` | present |
| 静态分析证据 | `evidence/static-analysis/` | present / N/A |
| 构建证据 | `evidence/build/` | present |
| 测试有效性评审 | `reviews/test-check.md` | 通过 |
| 代码检视 | `reviews/code-review.md` | 通过 |

## 完成声明

- 声明:                                   # 准备宣告什么完成了
- 范围:                                   # 本次完成覆盖的当前活跃任务 / AR 行为 / DTS 修复范围

## 任务队列结果

- 已完成任务:
- 门禁后任务状态:                         # done / blocked
- 下一 ready 任务:                        # <Task ID> / none / conflict
- 下一步动作判断:                         # devflow-tdd-implementation / devflow-finalize / devflow-router

## 本轮执行的验证命令

```text
<command 1>
```

- 退出码:
- 摘要:

```text
<command 2>
```

- 退出码:
- 摘要:

## 新鲜度锚点

- Commit / 构建 ID:
- 为什么这些证据属于当前最新代码状态:
- 大体量原始日志路径:

## 质量风险审计

- 嵌入式风险（内存 / 并发 / 实时性 / 资源生命周期 / 错误处理）:
- 已知 critical 静态分析 / 编译告警 / 编码规范违反:
- 未覆盖的 AR 行为或边界:
- SOA 边界 / 跨组件依赖风险:

## 结论

- 结论: `通过` | `需修改` | `阻塞`
- 结论理由:
- 下一步动作或推荐 Skill:                # canonical devflow-* 节点：devflow-tdd-implementation / devflow-finalize / devflow-router 等
- reroute_via_router: true / false

## 备注

- 限制 / 未关闭项:
