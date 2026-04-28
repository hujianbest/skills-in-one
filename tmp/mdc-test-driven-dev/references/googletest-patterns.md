# GoogleTest实用模式与最佳实践

## Test Fixture（共享 setup/teardown）

当多个测试需要相同的准备工作时，使用 fixture：

```cpp
class CalculatorTest : public ::testing::Test {
protected:
  void SetUp() override {
    calc = std::make_unique<Calculator>();
  }
  
  void TearDown() override {
    calc.reset();
  }

  std::unique_ptr<Calculator> calc;
};

TEST_F(CalculatorTest, AddsPositiveNumbers) {
  EXPECT_EQ(calc->add(2, 3), 5);
}

TEST_F(CalculatorTest, ReturnsZeroForEmptyInput) {
  EXPECT_EQ(calc->sum({}), 0);
}
```

**MDC HDT测试常用模式：** 添加辅助方法减少重复

```cpp
class AiInferStatusTest : public ::testing::Test {
protected:
  std::unique_ptr<AiInferStatus> status;

  // 辅助方法：发布系统状态消息
  void PublishSystemStatusWorkMsg() {
    auto msg = std::make_shared<ss_msgs::SsSystemStatus>();
    msg->sysStatus.state = 1;  // WORKING
    status->OnSystemStatusCallback(msg);
  }

  // 辅助方法：发布车辆基本信息
  void PublishVehicleBasicInfoHumanDriveMsg() {
    auto msg = std::make_shared<common_msgs::VehicleBasicInfo>();
    msg->adsWorkStatus = 1;  // 人驾
    msg->actualGear.value = 2;
    status->OnVehicleBasicInfoCallback(msg);
  }
};
```

## 参数化测试

同一个逻辑、不同输入时，避免复制粘贴：

```cpp
struct EmailCase {
  std::string input;
  bool expected_valid;
};

class EmailValidationTest : public ::testing::TestWithParam<EmailCase> {};

TEST_P(EmailValidationTest, ValidatesCorrectly) {
  auto [input, expected] = GetParam();
  EXPECT_EQ(is_valid_email(input), expected);
}

INSTANTIATE_TEST_SUITE_P(Emails, EmailValidationTest, ::testing::Values(
    EmailCase{"user@example.com", true},
    EmailCase{"missing-at.com", false},
    EmailCase{"", false},
    EmailCase{"a@b.c", true}
));
```

## 断言选择指南

| 场景 | 推荐断言 | 说明 |
|------|----------|------|
| 继续执行后续断言 | `EXPECT_*` | 失败后继续运行 |
| 失败则无法继续 | `ASSERT_*` | 失败后立即终止当前测试 |
| 布尔结果 | `EXPECT_TRUE` / `EXPECT_FALSE` | 布尔验证 |
| 数值相等 | `EXPECT_EQ` / `EXPECT_NE` | 数值比较 |
| 数值大小 | `EXPECT_GT` / `EXPECT_GE` / `EXPECT_LT` / `EXPECT_LE` | 数值边界 |
| 浮点比较 | `EXPECT_NEAR(a, b, tol)` | 避免浮点精度问题 |
| 字符串包含 | `EXPECT_THAT(s, HasSubstr("x"))` | 需要 `#include <gmock/gmock-matchers.h>` |
| 异常 | `EXPECT_THROW(expr, ExType)` | 验证抛出指定类型异常 |
| 不抛异常 | `EXPECT_NO_THROW(expr)` | 验证无异常 |

## 依赖注入与接口

C++ 中通过抽象基类（接口）注入依赖，方便隔离测试：

```cpp
class ILogger {
public:
  virtual ~ILogger() = default;
  virtual void log(std::string_view message) = 0;
};

class Service {
public:
  explicit Service(std::shared_ptr<ILogger> logger) : logger_(std::move(logger)) {}
  void process(int value) {
    if (value < 0) {
      logger_->log("negative input");
      return;
    }
    // ...
  }
private:
  std::shared_ptr<ILogger> logger_;
};
```

测试时用 GoogleMock 提供假实现：

```cpp
class MockLogger : public ILogger {
public:
  MOCK_METHOD(void, log, (std::string_view message), (override));
};

TEST(ServiceTest, LogsWarningOnNegativeInput) {
  auto logger = std::make_shared<MockLogger>();
  Service service(logger);

  EXPECT_CALL(*logger, log(HasSubstr("negative")));
  service.process(-1);
}
```

**注意：** mock 是为了隔离外部依赖（网络、文件系统、数据库），不是为了省事。
如果一个类可以直接构造，就直接用真实对象。

## 好测试的标准

| 品质 | 好 | 坏 |
|------|----|----|
| **最小** | 只测一件事。名字里有"并且"？拆开。 | `TEST(Validator, ValidatesEmailAndDomainAndWhitespace)` |
| **清晰** | 名字描述行为 | `TEST(Foo, Test1)` |
| **表达意图** | 展示理想的 API | 隐藏了代码该做什么 |

## 回调方法测试技术

**问题：** 回调函数通常是private的，测试无法直接调用

**解决方案：** 在生产代码中将回调设为public（因为被框架调用且测试需要）

```cpp
class AiInferStatus {
public:
    // 回调函数设为public（框架回调接口，测试也需要）
    void OnSystemStatusCallback(const ss_msgs::SsSystemStatus::ConstPtr& msg);
    void OnVehicleBasicInfoCallback(const common_msgs::VehicleBasicInfo::ConstPtr& msg);
    
    // 其他业务接口...
};
```

## 测试辅助方法最佳实践

**原则：**
- 将重复的消息构造提取到测试Fixture辅助方法
- 辅助方法名称以动词开头（如`Publish`, `Create`, `Setup`）
- 辅助方法简化测试代码，提高可读性

**示例：**
```cpp
// 繁复的测试代码（差）
TEST_F(Test, Case1) {
    auto msg = std::make_shared<ss_msgs::SsSystemStatus>();
    msg->sysStatus.state = 1;
    msg->sysStatus.subState = 0;
    status->OnSystemStatusCallback(msg);
    EXPECT_TRUE(...);
}

TEST_F(Test, Case2) {
    auto msg = std::make_shared<ss_msgs::SsSystemStatus>();
    msg->sysStatus.state = 1;
    msg->sysStatus.subState = 0;
    status->OnSystemStatusCallback(msg);
    EXPECT_FALSE(...);
}

// 使用辅助方法（好）
class Test : public ::testing::Test {
protected:
    void PublishSystemStatusWorkMsg() {
        auto msg = std::make_shared<ss_msgs::SsSystemStatus>();
        msg->sysStatus.state = 1;
        msg->sysStatus.subState = 0;
        status->OnSystemStatusCallback(msg);
    }
};

TEST_F(Test, Case1) {
    PublishSystemStatusWorkMsg();
    EXPECT_TRUE(...);
}

TEST_F(Test, Case2) {
    PublishSystemStatusWorkMsg();
    EXPECT_FALSE(...);
}
```
