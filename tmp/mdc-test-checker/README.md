# mdc-test-checker

`mdc-test-checker` 是一个用于审查单元测试质量的通用 Skill，适合在不同项目中复用。

## 这个 Skill 做什么

- 判断测试是否真正证明了行为，而不是只把代码跑通
- 识别弱断言、边界覆盖不足、错误路径缺失、隔离性问题
- 输出结构化评审结论，便于 reviewer 或作者直接跟进修改

## 适用场景

- 审查 gtest、pytest、JUnit 等测试代码
- 判断某批单测是否合理、是否符合规范
- 做测试质量 review、回归风险评估、弱断言检查

## 不适用场景

- 纯性能压测方案设计
- 集成测试或 E2E 环境排障
- 只要求写实现、不要求评审
- 纯格式化、命名或 lint 规则讨论

## 目录说明

- `SKILL.md`：Skill 主入口，定义触发条件、工作流、输出模板
- `references/review-rubric.md`：通用测试审查准则
- `references/gtest-cpp.md`：GoogleTest 相关补充
- `references/review-examples.md`：评审措辞与强弱对照
- `evals/evals.json`：正向评测样例
- `evals/trigger-eval.json`：触发/不触发校准样例
- `evals/acceptance-check.md`：最小验收清单

## 分发建议

如果要把这个 Skill 单独分发到其他仓库或环境，保留整个 `mdc-test-checker/` 目录即可，不要只复制 `SKILL.md`。
