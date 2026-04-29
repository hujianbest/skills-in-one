# 需求规格模板

使用说明：

- 本模板是 `devflow-specify` 生成 `features/<Work Item Id>-<slug>/requirement.md` 的默认模板。
- 若团队 `AGENTS.md` 声明了等价模板或路径，优先遵循团队约定。
- 本模板延续旧 `mdc-specify/references/spec-template.md` 的定位：作为规格 / requirement 的文档骨架；devflow 中默认落点为 `features/<id>/requirement.md`。
- 详细字段契约不在本模板重复维护：Requirement Rows、Interface Contract Candidates、SR-only 章节字段以 `requirement-rows-contract.md` 为准；NFR 的 QAS 写法以 `nfr-quality-attribute-scenarios.md` 为准。

## 1. 身份信息

| 字段 | 内容 |
|---|---|
| Work Item Type | SR / AR / DTS / CHANGE |
| Work Item ID |  |
| Title |  |
| Owner |  |
| Owning Component | AR / DTS / CHANGE 必填；SR 可空 |
| Owning Subsystem | SR 必填；AR / DTS / CHANGE 可空 |
| Related IR |  |
| Related SR | AR 必填 |
| Related AR | DTS 影响功能需求时填写 |
| Workflow Profile | requirement-analysis / standard / component-impact / hotfix / lightweight |

## 2. 背景与目标

- 背景:
- 目标:
- 用户 / 相关方:
- 当前问题或需求来源:

## 3. 范围 / 非范围

### 3.1 范围

- 

### 3.2 非范围

- 

## 4. 需求条目（Requirement Rows）

每条核心 row 至少满足 `references/requirement-rows-contract.md` 的字段契约。

| ID | Type | Statement | Acceptance | Source / Trace Anchor | Impact |
|---|---|---|---|---|---|
| FR-001 | FR |  |  |  |  |

## 5. 验收标准

| ID | 验收条件 | 覆盖 Requirement Rows | 验证方式 |
|---|---|---|---|
| AC-001 |  |  |  |

## 6. 嵌入式 NFR（如适用）

核心 NFR 应使用 QAS 五要素表达，详见 `references/nfr-quality-attribute-scenarios.md`。本节只保留记录落点，具体字段以该参考文件为准。

| NFR ID | QAS 摘要 | Acceptance / Response Measure | 备注 |
|---|---|---|---|
| NFR-001 |  |  |  |

## 7. 未决问题

### 7.1 阻塞问题

| ID | 问题 | Owner | 影响 | 截止 / 下一步 |
|---|---|---|---|---|
| OQ-001 |  |  |  |  |

### 7.2 非阻塞问题

| ID | 问题 | Owner | 处理方式 |
|---|---|---|---|
| OQ-002 |  |  |  |

## 8. 假设与依赖

| ID | 类型 | 内容 | 失效影响 | Owner |
|---|---|---|---|---|
| ASM-001 | Assumption / Dependency |  |  |  |

## 9. 按工作项类型划分的章节

### 9.1 SR：子系统范围评估

| 项 | 内容 |
|---|---|
| 影响子系统范围 |  |
| 跨组件影响 |  |
| 需求负责人 |  |

### 9.2 SR：受影响组件

字段契约见 `references/requirement-rows-contract.md#sr-only-章节字段`。

| Component | Modification Surface | Covers Rows | Component Design Impact |
|---|---|---|---|
|  |  |  |  |

### 9.3 SR：AR 拆分候选

字段契约见 `references/requirement-rows-contract.md#sr-only-章节字段`。

| Candidate ID | Scope | Owning Component | Covers SR Rows | Notes |
|---|---|---|---|---|
| CAR-001 |  |  |  |  |

### 9.4 SR：组件设计影响

- 是否需要修订组件实现设计:
- 影响章节:
- 模块架构师:
- 未决问题:

### 9.5 AR / DTS / CHANGE：组件影响评估

| 影响面 | 是否影响 | 说明 | 指向组件设计章节 |
|---|---|---|---|
| SOA 接口 | yes / no |  |  |
| 组件依赖 | yes / no |  |  |
| 状态机 | yes / no |  |  |
| 运行时行为 | yes / no |  |  |
| 内部实现 | yes / no |  |  |

### 9.6 AR / DTS / CHANGE：接口契约候选（Interface Contract Candidates，如适用）

当存在 `IFR` row，或 `Component Impact = interface` 时必填。字段契约见 `references/requirement-rows-contract.md#interface-contract-candidatesar--dts--change`。

| Candidate ID | Interface / Service Name | Provider / Consumer | Operation | Covers Requirement Rows | Open Questions |
|---|---|---|---|---|---|
| IFC-001 |  |  |  |  |  |
