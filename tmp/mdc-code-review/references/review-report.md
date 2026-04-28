# Code Review Report

MDC项目代码检视报告模板。

## 检视报告要求

### 1 必须包含的内容

对于每个问题，必须包含：
1. **位置**：file_path:line_number
2. **问题描述**：What's wrong
3. **重要性**：Why it matters
4. **修复建议**：How to fix（附带代码示例）

### 2 报告结构

```markdown
# 检视报告

## 基本信息
- Commit SHA
- 变更文件
- 变更统计

## 变更详细分析
- 逐个文件/函数分析

## 代码质量评估
### Strengths (优点)
### Issues (问题)
#### Critical
#### Important
#### Minor

## 测试覆盖分析
## 综合评估
## 改进建议清单
```

### 3 评估结论

必须给出明确的评估结论：
- **Ready to merge**: 可以合并
- **Ready to merge with fixes**: 修复指定问题后可合并
- **Not ready**: 不建议合并

必须说明理由（1-2句话）。
