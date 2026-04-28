# Tasks Review Checklist

## 评审维度

| ID | 维度 | Pass Condition |
|---|---|---|
| `TR1` | 可执行性 | 关键任务可冷启动，无大任务 |
| `TR2` | 任务合同完整性 | 关键任务有 Acceptance/Files/Verify/完成条件 |
| `TR3` | 验证与测试种子 | 种子足够支持 fail-first |
| `TR4` | 依赖与顺序 | 依赖/关键路径可理，无循环 |
| `TR5` | 追溯覆盖 | 任务可回指到规格/设计 |
| `TR6` | Router 重选就绪度 | Current Active Task 选择规则唯一 |
