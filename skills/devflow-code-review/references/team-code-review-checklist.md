# Team Code Review Checklist

> 配套 `devflow-code-review/SKILL.md`。本文件完整继承旧 MDC 项目通用代码检视检查清单，用于补充 `code-review-rubric.md` 的 CR1-CR8 评分维度。

## 一、代码质量检查点

### 1.1 Clean Code

- [ ] 命名是否清晰且符合项目规范
  - 类名：PascalCase（如 `VdecImpl`, `ProcessUserSpecifiedSizeTest`）
  - 函数名：camelCase（如 `validateParams`, `setupEnvironment`）
  - 成员变量：snake_case with trailing underscore（如 `isInit_`, `bufferSize_`）
  - 常量：ALL_CAPS 或 constexpr（如 `IMG_MAX_WIDTH`, `BUFFER_SIZE`）
- [ ] 函数长度是否合理（建议 < 50 行）
- [ ] 是否有重复代码（DRY 原则）
- [ ] 是否有深层嵌套（建议 < 3 层）
- [ ] 注释是否必要且准确

### 1.2 错误处理

- [ ] 所有可能失败的操作是否有错误处理
- [ ] 错误码使用是否正确（如 `HI_SUCCESS` / `HI_FAILURE`，或项目 `AGENTS.md` 声明的等价错误码）
- [ ] 错误日志是否完整（包含上下文信息）
- [ ] 异常安全是否考虑（资源泄漏风险）

### 1.3 类型安全

- [ ] 是否使用项目特定类型（如 `hi_u8`, `hi_s32`, `hi_u32` 等，或项目 `AGENTS.md` 声明的等价类型）
- [ ] 类型转换是否安全（避免隐式转换）
- [ ] 指针使用是否安全（空指针检查、生命周期清晰）
- [ ] 是否使用无符号类型后缀（`U`, `ULL`）

### 1.4 边界情况

- [ ] 是否处理了空指针 / `nullptr`
- [ ] 是否处理了零值
- [ ] 是否处理了边界值（最大 / 最小）
- [ ] 是否处理了异常输入

### 1.5 资源管理

- [ ] 动态内存是否使用 RAII（智能指针）
- [ ] 文件句柄是否正确关闭
- [ ] 锁是否正确释放
- [ ] 是否有资源泄漏风险

## 二、架构设计检查点

### 2.1 设计决策

- [ ] 类设计是否合理（单一职责）
- [ ] 接口设计是否清晰
- [ ] 依赖关系是否合理
- [ ] 是否遵循开闭原则

### 2.2 可扩展性

- [ ] 是否易于扩展
- [ ] 配置是否灵活
- [ ] 是否有硬编码限制

### 2.3 性能考虑

- [ ] 是否有不必要的拷贝
- [ ] 是否有性能瓶颈
- [ ] 是否合理使用 SIMD 优化
- [ ] 是否合理使用 `noexcept`

### 2.4 安全性

- [ ] 输入验证是否充分
- [ ] 是否有缓冲区溢出风险
- [ ] 是否有竞态条件
- [ ] 敏感信息是否保护

## 三、测试代码检查点

### 3.1 测试有效性

- [ ] 测试是否真正测试了业务逻辑（而非只测试 Mock）
- [ ] 断言是否充分（验证了关键结果）
- [ ] 边界值是否覆盖
- [ ] 异常分支是否测试

### 3.2 测试规范

- [ ] 测试类命名是否符合规范（`<ComponentName>Test`）
- [ ] 测试用例命名是否清晰（`<methodName><Scenario>Test`）
- [ ] `TearDown` 是否调用 `GlobalMockObject::verify()`（若项目测试框架要求）
- [ ] Mock 设置是否合理

### 3.3 测试覆盖

- [ ] 正常场景是否覆盖
- [ ] 边界场景是否覆盖
- [ ] 异常场景是否覆盖
- [ ] 未覆盖场景是否有说明

## 四、项目规范检查点

### 4.1 命名规范

- [ ] 是否符合 PascalCase / camelCase / snake_case 等项目规范
- [ ] 是否有版权信息（若项目要求）

## 五、问题分级标准

### Critical（必须修复）

**定义：** 影响系统稳定性、安全性的严重问题。

**示例：**

1. **安全漏洞**
   - 缓冲区溢出风险
   - 未验证的用户输入
   - 敏感信息泄露
2. **数据丢失风险**
   - 未持久化的关键数据
   - 可能覆盖数据的操作
3. **严重功能缺陷**
   - 导致系统崩溃的 bug
   - 核心功能无法工作
   - 内存泄漏（严重）
4. **违反关键规范**
   - 违反安全编码规范
   - 破坏关键接口契约

**处理要求：** 必须在合并前修复。

### Important（应该修复）

**定义：** 影响代码质量、可维护性的重要问题。

**示例：**

1. **架构问题**
   - 违反单一职责原则
   - 过度耦合
   - 不合理的设计模式
2. **资源管理问题**
   - 内存管理风险（异常不安全）
   - 资源泄漏隐患
   - 未使用 RAII
3. **测试问题**
   - 测试断言不充分
   - 测试覆盖不足
   - Mock 使用不当
4. **性能问题**
   - 明显的性能瓶颈
   - 不必要的拷贝
   - 低效算法
5. **错误处理缺陷**
   - 缺少错误处理
   - 错误信息不清晰
   - 异常处理不当

**处理要求：** 建议在合并前修复，或创建技术债务跟踪。

### Minor（建议改进）

**定义：** 代码风格、可读性方面的改进建议。

**示例：**

1. **代码风格**
   - 命名不一致
   - 格式不规范
   - 缺少必要注释
2. **优化机会**
   - 代码可简化
   - 重复代码
   - 可提取公共逻辑
3. **文档改进**
   - 注释不完整
   - 缺少示例
   - 文档过时

**处理要求：** 可在后续迭代中改进。

## 六、常见问题模式

### 6.1 内存管理

**问题模式：** 使用裸指针 `new` / `delete`。

```cpp
// Bad: 异常不安全
uint8_t* buffer = new uint8_t[1024];
process(buffer);  // 如果这里抛异常，buffer 泄漏
delete[] buffer;

// Good: 使用智能指针
auto buffer = std::make_unique<uint8_t[]>(1024);
process(buffer.get());  // 异常安全，自动释放
```

**检查要点：**

- 是否有 `new` / `delete` 配对
- 是否在可能抛异常的代码路径上
- 是否考虑使用智能指针

### 6.2 测试断言

**问题模式：** 只验证返回值，未验证副作用。

```cpp
// Bad: 只验证返回值
EXPECT_EQ(func(), HI_SUCCESS);

// Good: 验证副作用
EXPECT_EQ(func(), HI_SUCCESS);
EXPECT_EQ(state.counter, expected_count);
EXPECT_TRUE(state.is_modified);
```

**检查要点：**

- 是否验证了函数的实际效果
- 是否验证了状态变化
- 是否验证了关键输出

### 6.3 魔法数字

**问题模式：** 硬编码数字缺乏语义。

```cpp
// Bad: 魔法数字
uint8_t* buffer = new uint8_t[1024];
mockResult.width = 1920;
mockResult.height = 1079;

// Good: 使用 constexpr 常量
namespace {
constexpr uint32_t BUFFER_SIZE {1024U};
constexpr uint32_t ALIGNED_WIDTH {1920U};
constexpr uint32_t UNALIGNED_HEIGHT {1079U};
}

uint8_t* buffer = new uint8_t[BUFFER_SIZE];
mockResult.width = ALIGNED_WIDTH;
mockResult.height = UNALIGNED_HEIGHT;
```

**检查要点：**

- 数字是否有语义说明
- 是否应提取为常量
- 是否使用了适当的类型后缀

### 6.4 代码重复

**问题模式：** 多个测试代码高度相似。

```cpp
// Bad: 重复代码
TEST_F(Test, Scenario1) {
    // ... 20 行重复代码 ...
    obj.width = 0;  // 唯一不同点
    // ... 3 行重复代码 ...
}

TEST_F(Test, Scenario2) {
    // ... 20 行重复代码 ...
    obj.height = 0;  // 唯一不同点
    // ... 3 行重复代码 ...
}

// Good: 参数化测试
INSTANTIATE_TEST_SUITE_P(Params, Test, testing::Values(
    TestData{0, 1080},
    TestData{1920, 0}
));

TEST_P(Test, Scenario) {
    auto param = GetParam();
    // ... 统一的测试逻辑 ...
}
```

**检查要点：**

- 相似度是否超过 80%
- 是否违反 DRY 原则
- 是否可提取公共逻辑或参数化

### 6.5 测试覆盖

**问题模式：** 缺少边界值测试。

```cpp
// Bad: 只测试正常值
TEST_F(Test, NormalCase) {
    testFunc(100);  // 只测试一个值
}

// Good: 测试边界值
TEST_F(Test, ZeroValue) { testFunc(0); }
TEST_F(Test, MinValue) { testFunc(1); }
TEST_F(Test, MaxValue) { testFunc(INT_MAX); }
TEST_F(Test, NormalValue) { testFunc(100); }
```

**检查要点：**

- 是否测试了零值
- 是否测试了边界值
- 是否测试了异常输入
- 是否测试了组合场景
