---
name: mdc-test-driven-dev
description: 使用 HDT(based on GoogleTest) 进行 C 和 C++ 测试驱动开发。当用户要编写 C 和 C++ 代码、实现新功能、修复 Bug、重构 C 和 C++ 项目时，请务必使用此技能——即使用户没有明确提到 TDD 或测试。只要涉及 CC 和 C++ 实现代码的编写，就应先写测试再写实现。同样适用于用户提到 gtest、gmock、ctest、CMake 测试、C 和 C++ 单元测试、HDT用例等场景。
---

# 测试驱动开发（TDD）

## 概述

先写测试，看着它失败，再写最少的代码让它通过。

**核心原则：** 如果你没有亲眼看到测试失败，你就不知道它到底测的是什么。

## 何时使用

**始终使用：**
- 新功能实现
- Bug 修复
- 重构
- 行为变更

**例外（需要与用户确认）：**
- 一次性原型
- 自动生成的代码
- 纯配置文件

想着"就这一次不写测试"？停下来，那是在给自己找借口。

## 铁律

```
没有失败的测试，就不写产品代码
```

先写了实现代码？删掉它，从头来过。

**没有例外：**

## Workflow

### 1. 写一个失败的测试 (RED)

为要实现的编写测试用例，描述期望的行为。

**要求：**
- 测试名清楚说明要测试的行为
- 只测一件事
- 使用真实代码优先，只在必要时用 mock
- 避免依赖实现细节

### 2. 验证测试失败

运行测试确认它按预期失败。

**验证：**
- 测试必须失败（不能直接通过）
- 失败原因是因为功能缺失（不是编译错误）
- 失败原因是符合预期的

**如果测试直接通过**：修订测试，你在测已有行为

**如果编译报错**：先修编译错误

### 3. 写最少的实现代码 (GREEN)

写刚好能让测试通过的最简单代码。

**原则：**
- 不要添加测试未要求的功能
- 不要顺手重构其他代码
- 遵循 YAGNI（You Aren\'t Gonna Need It）

### 4. 验证测试通过

运行测试并确认所有测试通过。

**验证：**
- 当前测试通过
- 其他测试依然通过
- 编译输出干净（无 warning）

**如果测试失败**：修改实现代码，不要改测试

**如果其他测试失败**：立即修复回归

### 5. 重构（可选）

仅当所有测试通过后，可以进行重构：
- 消除重复代码
- 改善命名
- 提取辅助函数

保持测试全绿，不添加新行为。

### 6. 重复

继续下一个行为，返回步骤 1。

---

## MDC HDT 环境准备

MDC HDT 测试与普通HDT不同，需要预先配置测试桩(stubs)以隔离MDC环境依赖。

**首次使用HDT时必须完成环境准备，详细步骤移至：** @references/mdc-hdt-setup.md

**快速检查清单：**
- [ ] 创建标准目录结构 `test/hdt/{tests,conf,stubs}`
- [ ] 为每个依赖创建stub（消息类型、中间件、日志宏）
- [ ] 配置CMakeLists.txt使用`mdc_dt_binary`
- [ ] 验证构建成功

---

## 测试用例设计

**重要：** 编写HDT测试用例前，必须先查阅AR实现设计文档中的测试设计章节，按照文档中定义的测试用例进行实现。

**如何从AR设计文档获取测试用例，详见：** @references/test-case-design-from-AR.md

**核心原则：**
- 测试用例必须包含至少1个断言
- 命名格式：`函数名_测试场景中文描述`
- 使用辅助方法减少重复代码

---

## RED-GREEN实战示例

### RED — 写一个失败的测试

写一个最小的测试，描述期望的行为。

<Good>
```cpp
TEST(RetryTest, RetriesFailedOperations3Times) {
  int attempts = 0;
  auto operation = [&]() -> std::string {
    ++attempts;
    if (attempts < 3) throw std::runtime_error("fail");
    return "success";
  };

  auto result = retry_operation(operation);

  EXPECT_EQ(result, "success");
  EXPECT_EQ(attempts, 3);
}
```
名字清晰，测试真实行为，只测一件事
</Good>

<Bad>
```cpp
TEST(RetryTest, RetryWorks) {
  MockOperation mock;
  EXPECT_CALL(mock, execute())
      .WillOnce(testing::Throw(std::runtime_error("fail")))
      .WillOnce(testing::Throw(std::runtime_error("fail")))
      .WillOnce(testing::Return("success"));
  retry_operation([&]{ return mock.execute(); });
  // 只验证了 mock 调用次数，没测真实逻辑
}
```
名字含糊，测的是 mock 而非代码
</Bad>

**要求：**
- 只测一个行为
- 测试名说明行为（`RejectsEmptyInput`，不是 `Test1`）
- 用真实代码，mock 只在不得已时使用

### 验证 RED — 看着它失败

**必须执行，绝不跳过。** [MDC HDT构建命令见@references/mdc-hdt-commands.md]

确认：
- 测试**失败**（不是编译错误）
- 失败原因符合预期
- 失败是因为功能缺失（不是因为拼错了）

**测试直接通过了？** 你在测已有的行为，修改测试。

**编译报错？** 先修编译，再运行直到看见正确的失败。

### GREEN — 最少的实现代码

写最简单的代码让测试通过。

<Good>
```cpp
template <typename F>
auto retry_operation(F&& fn, int max_retries = 3) -> decltype(fn()) {
  for (int i = 0; i < max_retries; ++i) {
    try {
      return fn();
    } catch (...) {
      if (i == max_retries - 1) throw;
    }
  }
  throw std::logic_error("unreachable");
}
```
刚好够让测试通过
</Good>

<Bad>
```cpp
template <typename F>
auto retry_operation(
    F&& fn,
    int max_retries = 3,
    std::chrono::milliseconds backoff = std::chrono::milliseconds(100),
    BackoffStrategy strategy = BackoffStrategy::Exponential,
    std::function<void(int, const std::exception&)> on_retry = nullptr
) -> decltype(fn()) {
  // YAGNI — 没有测试要求这些参数
}
```
过度设计
</Bad>

不要加功能、不要顺手重构别的代码、不要"改进"超出测试要求的范围。

### 验证 GREEN — 看着它通过

**必须执行。** [MDC HDT构建命令见@references/mdc-hdt-commands.md]

确认：
- 当前测试通过
- 其他测试依然通过
- 编译输出干净（没有 warning）

**测试失败了？** 改实现代码，不改测试。

**其他测试挂了？** 立刻修。

### REFACTOR — 整理代码

只在全绿之后：
- 消除重复
- 改善命名
- 提取辅助函数

保持测试全绿。不添加新行为。

### 重复

为下一个行为写下一个失败的测试。

---

## GoogleTest模式与最佳实践

**详细的GoogleTest使用模式、Test Fixture、参数化测试、断言选择、依赖注入等，移至：** @references/googletest-patterns.md

**核心要点：**
- Test Fixture共享setup/teardown代码
- 辅助方法减少重复
- 回调方法设为public以便测试
- 正确使用EXPECT_*/ASSERT_*

---

## 修复Bug示例

**Bug：** 空字符串被接受为有效输入

**RED**
```cpp
TEST(InputValidatorTest, RejectsEmptyString) {
  InputValidator validator;
  auto result = validator.validate("");
  EXPECT_FALSE(result.ok);
  EXPECT_EQ(result.error, "input must not be empty");
}
```

**验证RED**
```bash
$ ctest --output-on-failure -R RejectsEmptyString
[  FAILED  ] InputValidatorTest.RejectsEmptyString
Expected equality of these values:
  result.error
    Which is: ""
  "input must not be empty"
```

**GREEN**
```cpp
ValidationResult InputValidator::validate(std::string_view input) {
  if (input.empty()) {
    return {.ok = false, .error = "input must not be empty"};
  }
  // ...existing logic...
}
```

**验证GREEN**
```bash
$ ctest --output-on-failure
[  PASSED  ] 42 tests.
```

**REFACTOR**
如果有多个字段需要非空校验，提取通用验证函数。

---

## 测试驱动发现的缺陷

TDD不仅能验证实现正确性，还能发现设计中的逻辑缺陷。

**经典案例：** 缺失订阅有效性检查

**测试前实现：**
```cpp
bool AiInferStatus::IsInferAllowed() const {
    std::lock_guard<std::mutex> ssLock(m_systemStatusMutex);
    const uint32_t state = m_systemStatus.state;
    // 直接检查状态，未验证订阅是否有效
    if (state != STATE_WORKING && state != STATE_LOWPOWER) {
        return false;
    }
    // ...
}
```

**测试用例：**
```cpp
TEST_F(AiInferStatusTest, IsInferAllowed_缺少车辆消息拒绝推理) {
    PublishSystemStatusWorkMsg();  // 仅发送系统消息
    
    EXPECT_FALSE(status->IsInferAllowed()) 
        << "缺少车辆消息应拒绝推理";
}
```

**测试失败结果：**
```
[  FAILED  ] IsInferAllowed_缺少车辆消息拒绝推理
Expected: false
  Actual: true    // 测试失败！IsInferAllowed返回true
缺少车辆消息应拒绝推理
```

**测试驱动发现缺陷：** `IsInferAllowed()` 未调用 `IsSubscriptionValid()` 检查

**修复后实现：**
```cpp
bool AiInferStatus::IsInferAllowed() const {
    // 新增：验证订阅有效性
    if (!IsSubscriptionValid()) {
        return false;
    }
    std::lock_guard<std::mutex> ssLock(m_systemStatusMutex);
    // ...
}
```

**经验总结：测试驱动的缺陷发现**
- 测试用例应覆盖边界情况（如缺失消息）
- 测试驱动开发能发现"逻辑层"的缺陷（如缺少前置检查）
- 缺陷修复后，回归测试自动验证所有场景

---

## MDC HDT构建与运行

**详细命令和问题排查，移至：** @references/mdc-hdt-commands.md

**快速命令：**
```bash
cd test/hdt
rm -rf build && cmake -S . -B build -DMDC_TOP_DIR=<MDC_ROOT> ...
make -j$(nproc) && ./ai2s_d_status_test --gtest_color=yes
```

---

## 遇到困难

| 问题 | 解决 |
|------|------|
| 不知道怎么测 | 先写你期望的 API，先写断言，问你的搭档 |
| 测试太复杂 | 设计太复杂，简化接口 |
| 必须 mock 一切 | 耦合太紧，使用依赖注入 |
| setup 代码太长 | 提取到 Test Fixture。仍然复杂？简化设计 |

## 调试集成

发现 bug？先写一个能重现它的失败测试，再走 TDD 循环。测试既证明了修复有效，又防止回归。

永远不要在没有测试的情况下修 bug。

## 测试反模式

添加 mock 或测试工具时，阅读 @testing-anti-patterns.md 避免常见陷阱：
- 测试的是 mock 行为而非真实行为
- 给产品类加只有测试才用的方法
- 不了解依赖关系就乱 mock

## 验证清单

完成工作前逐项检查：

- [ ] 每个新函数/方法都有对应测试
- [ ] 每个测试都亲眼看到失败
- [ ] 每个测试的失败原因是功能缺失（不是拼写错误）
- [ ] 每次只写了让测试通过的最少代码
- [ ] 所有测试通过
- [ ] 编译输出干净（无 warning、无 error）
- [ ] 测试使用真实代码（mock 只在不得已时使用）
- [ ] 边界和错误情况已覆盖

不能全部打勾？你跳过了 TDD，从头来过。

## TDD核心原则与禁止行为

**详细原则和借口分析，移至：** @references/tdd-principles.md

**核心原则：**
```
没有失败的测试，就不写产品代码
产品代码 → 必须先有一个失败的测试，否则 → 不是 TDD
```

---

## 最终规则

```
产品代码 → 必须先有一个失败的测试
否则 → 不是 TDD
```
没有用户许可，不得例外。

## Ready for test-checker

测试实现已产出，具备 `mdc-test-checker` 的前置条件：

- [ ] RED evidence 已记录（看到测试失败）
- [ ] GREEN evidence 已记录（测试通过）
- [ ] 测试使用真实行为（非纯 mock）
- [ ] 编译输出干净
- [ ] 边界和错误情况已覆盖

推荐下一步：派发 `mdc-test-checker` reviewer subagent。
