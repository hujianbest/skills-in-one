---
name: mdc-bug-patterns
description: "基于 LLM 分析的 C++ 代码Bug模式检测，包含内存泄漏、空指针访问、资源泄漏、并发问题和逻辑错误等常见Bug模式。用于: 检查 C++ 代码Bug、检测内存问题、发现潜在崩溃、代码安全性审查、代码质量分析"
---

# C++ 代码 Bug 模板排查技能

## 分析流程

1. **代码解析** - 理解代码结构、函数、类及其关系
2. **应用模板** - 从 `references/templates.md` 加载检测模板，使用 LLM 进行推理分析
3. **生成报告** - 生成控制台输出或 Excel 格式报告（含上下文）

## 模板系统

查看 `references/templates.md` 获取所有内置模板的完整列表。

每个模板包含：
- 唯一的模板ID（用于引用）
- 人类可读的名称
- 类别（用于筛选）
- 严重程度（用于优先级排序）
- 检测模式（供 LLM 理解）
- 问题代码示例
- 修复代码示例
- 修复建议列表

## 模板格式

### 模板ID

**名称**: 人类可读的名称  
**类别**: memory|null|resource|concurrency|logic  
**严重程度**: critical|high|medium|low

**检测模式**:
描述要查找的内容（LLM 使用的清晰指令）

**问题代码**:
```cpp
// 有 bug 的代码
```

**修复代码**:
```cpp
// 修复后的代码
```

**修复建议**:
- 修复建议1
- 修复建议2

## 内置模板

| 类别 | 模板ID | 严重程度 | 模式 |
|------|--------|----------|------|
| 内存管理 | mem-new-no-delete | 严重 | new 未配对 delete |
| 内存管理 | mem-new-array-no-del-array | 严重 | new[] 未配对 delete[] |
| 内存管理 | mem-no-destructor | 高 | 缺少析构函数 |
| 空指针 | ptr-deref-no-check | 严重 | 指针解引用前未做空指针检查 |
| 空指针 | ptr-optional-value-no-check | 中 | optional 访问时未检查 |
| 资源管理 | res-file-no-close | 高 | 文件句柄未关闭 |
| 资源管理 | res-mutex-no-unlock | 高 | 互斥锁未解锁 |
| 并发 | con-unsynchronized-access | 严重 | 未同步的共享数据访问 |
| 并发 | con-lock-ordering | 中 | 锁顺序不一致导致死锁风险 |
| 逻辑 | int-add-overflow | 高 | 指数加法溢出 |
| 逻辑 | int-sub-overflow | 高 | 指数减法下溢 |
| 逻辑 | int-mul-overflow | 高 | 指数乘法溢出 |
| 逻辑 | int-shift-overflow | 中 | 位运算溢出 |
| 逻辑 | int-signed-unsigned-mix | 中 | 有符号无符号混用 |
| 逻辑 | int-narrowing-cast | 低 | 类型转换截断 |
| 逻辑 | div-by-zero | 高 | 除以零 |
| 逻辑 | empty-container-access | 高 | 空容器访问 |

## 创建新模板
在 `references/templates.md` 中添加新章节：
1. 选择唯一的 `模板ID`（如 `buffer-overflow-access`）
2. 在"检测模式"字段描述要检测的内容（给 LLM 的清晰指令）
3. 提供"问题代码"展示 bug
4. 提供"修复代码"展示修复方案
5. 添加"修复建议"用于修复问题

## 示例模板

### int-add-overflow

**名称**: 整数加法溢出  
**类别**: logic  
**严重程度**: high

**检测模式**:
查找可能溢出的有符号整数加法运算，但未进行边界检查的情况。
查找：a + b，其中两者都是有符号类型且运算前无溢出检查。

**问题代码**:
```cpp
int add(int a, int b) {
    return a + b;  // 可能溢出!
}
```

**修复代码**:
```cpp
int add(int a, int b) {
    int result;
    if (__builtin_add_overflow(a, b, &result)) {
        throw std::overflow_error("溢出");
    }
    return result;
}
```

**修复建议**:
- 使用 __builtin_add_overflow 进行安全加法
- 使用 std::numeric_limits 检查边界


## LLM 分析过程

### 步骤 1：加载模板
读取 `references/templates.md` 获取所有检测模板

### 步骤 2：分析代码

LLM 在模板指导下执行语义分析：

1. **理解模式**：从"检测模式"字段，LLM 学习要检测的 Bug 类型
2. **分析代码**：LLM 理解代码，不仅是模式匹配
3. **验证发现**：使用语义分析减少误报
4. **收集上下文**：提取每个发现前后各5行代码（含行号）
5. **应用严重程度**：按模板的严重程度，根据上下文调整

### 步骤 3：生成报告
格式化 findings 为控制台输出或 Excel 格式：
- 严重程度级别
- 匹配的模板
- 位置 (文件:行号)
- 上下文（前后各5行）
- 修复建议

## 输出格式

### 控制台输出
对每个发现的 Bug：

```
[严重] 模板名称 (id: mem-new-no-delete)
位置: file.cpp:行号:列号
模式: new 未配对 delete
上下文:
    5: class Buffer {
    6: public:
>>> 7:     void process() {
    8:         int* data = new int[100];
    9:         data[0] = 42;
```

### Excel 输出
生成 Excel 报告，包含列：
- 严重程度（颜色编码：严重=红色、高=橙色、中=黄色、低=绿色）
- 类别
- 模板ID
- 名称
- 位置
- 模式
- 上下文（前后各5行，问题行用 >>> 标记）
- 时间戳

## 辅助脚本

使用 `scripts/excel_helper.py` 从 JSON 格式的 findings 生成 Excel 报告。
