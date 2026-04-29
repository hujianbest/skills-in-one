# 验证记录模板

> 配套 `devflow-completion-gate/SKILL.md`。用于保存验证命令、结果摘要、新鲜度锚点和门禁结论。

## 元数据

- 验证类型:                             # unit / integration / simulation / build / static-analysis / regression / completion
- 工作项类型:                           # AR / DTS / CHANGE
- 工作项 ID:
- 当前活跃任务:
- 范围:
- 日期:
- 记录路径:
- Worktree 路径 / 分支（如适用）:

## 已消费的上游证据

- 实现交接:
- 评审 / 门禁记录:
  - 规格评审:
  - 组件设计评审:
  - AR 设计评审:
  - 任务队列前置检查:
  - 测试有效性评审:
  - 代码检视:
- 任务 / 进度锚点:
  - 任务计划:
  - 任务看板:
  - 进度:
- 追溯矩阵:

## 被验证的声明

- 声明:
- 声明类型: task-level completion / work-item completion / regression / environment recovery

## 验证范围

- 覆盖范围:
- 未覆盖范围:
- 范围理由:

## 命令与结果

### 命令 1

```text
<command>
```

- 退出码:
- 摘要:
- 关键输出:
- 证据路径:

### 命令 2（如适用）

```text
<command>
```

- 退出码:
- 摘要:
- 关键输出:
- 证据路径:

## 新鲜度锚点

- Commit / 构建 ID:
- 工具链 / 目标平台:
- 配置:
- 为什么该证据对应最新相关代码状态:
- 输出日志 / 终端 / 工件:

## 嵌入式风险审计

| 维度 | 状态 | 证据 / 说明 |
|---|---|---|
| 内存（边界 / 池化 / 栈 / 生命周期） | clean / documented-debt / critical-open / N/A |  |
| 并发（中断 / 锁 / 临界区 / 竞态） | clean / documented-debt / critical-open / N/A |  |
| 实时性（latency / deadline / 调度） | clean / documented-debt / critical-open / N/A |  |
| 资源生命周期（句柄 / 文件 / 缓冲区） | clean / documented-debt / critical-open / N/A |  |
| 错误处理（输入校验 / 错误码 / 降级） | clean / documented-debt / critical-open / N/A |  |
| ABI / API 兼容 | clean / documented-debt / critical-open / N/A |  |
| SOA 边界 / 跨组件依赖 | clean / documented-debt / critical-open / N/A |  |

## 结论

- 结论: `通过` | `需修改` | `阻塞`
- 结论理由:
- 下一步动作或推荐 Skill:
- reroute_via_router: true / false

## 范围 / 剩余工作说明

- 剩余任务判断（如适用）:
- 如果存在唯一 next-ready task:
- 如果没有 ready / pending task:
- 如果 task-board 状态冲突:
- 备注:

## 关联工件

- 关联工件:
