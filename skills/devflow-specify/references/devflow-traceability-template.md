# devflow 追溯矩阵模板

使用说明：

- 默认保存路径：`features/<工作项ID>-<slug>/traceability.md`。
- 列集按工作项类型有所不同：
  - SR（需求分析子街区）：IR -> SR -> Affected Components -> Component Design Section -> Candidate AR Breakdown
  - AR / DTS / CHANGE（实现子街区）：IR -> SR -> AR -> 组件设计 -> AR 设计 -> Task -> 代码 -> 测试 -> 验证

## 标识信息

- 工作项类型:                          # SR / AR / DTS / CHANGE
- 工作项 ID:
- 所属组件:                            # AR / DTS / CHANGE
- 所属子系统:                          # SR

## 追溯行 — 实现子街区（AR / DTS / CHANGE）

| IR | SR | AR | 组件设计章节 | AR 设计章节 | 任务 ID | 测试设计用例 | 代码文件 / 函数 | 测试代码文件 | 验证证据 |
|---|---|---|---|---|---|---|---|---|---|
|   |   |   |   |   |   |   |   |   |   |

## 追溯行 — 需求分析子街区（SR）

| IR | SR | 受影响组件 | 修改面 | 组件设计章节 | 候选 AR ID | 覆盖 SR 行 |
|---|---|---|---|---|---|---|
|   |   |   |   |   |   |   |

## 备注

- 若某行不存在对应链接，标记 `N/A` 并简述理由。
- 跨组件 AR 在每个受影响组件仓库内分别维护对应行，本文件只覆盖当前组件仓库视角。
- 测试设计用例必须能在 AR 实现设计的测试设计章节中找到对应条目，形成双向锚点。
