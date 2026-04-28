# C++ GoogleTest 说明

仅覆盖 **GoogleTest 语法与结构**层面的评审要点。断言是否“够强”、覆盖是否完整等通用判断见 `review-rubric.md`。

## 命名

推荐名称中体现：

- 被测函数或行为
- 输入场景或条件
- 预期结果

较好的例子：

- `OrderService_Submit_NullCart_Fails`
- `Cache_Get_ValidKey_ReturnsValue`

较弱的例子：

- `Test1`
- `BasicCase`
- `Works`

## ASSERT 与 EXPECT

- 后续语句依赖前置条件成立时，优先 `ASSERT_*`，避免在无效状态下继续执行产生误导性失败信息。
- 同一条用例内需收集多个独立断言时，用 `EXPECT_*`，便于一次看出多处回归。

## 典型弱模式（框架层面）

以下模式在 rubric 中也会从“行为”角度讨论，此处强调 **gtest 写法**上的识别：

- 对失败路径用例仍只写成功路径式断言。
- 用合并算术表达式一次性“扫过”多个字段，例如：

```cpp
EXPECT_GT(info.a + info.b + info.c, 0u);
```

更稳妥的写法是**分字段**断言，或在契约允许时使用精确期望值：

```cpp
EXPECT_GT(info.a, 0u);
EXPECT_GT(info.b, 0u);
EXPECT_GT(info.c, 0u);
```

## Fixture 与套件

- `SetUp`/`TearDown` 或共享 fixture 是否引入**跨用例可变状态**；若有，是否每次测试前重置。
- `TEST_F` 基类是否过大导致多数用例要“抵消”默认 setup；可考虑拆套件或局部 helper。
- 参数化测试（`TEST_P`）是否真正减少重复并提高矩阵覆盖；避免仅为形式而参数化。

## 评审顺序提醒

- 先用 `review-rubric.md` 判断行为与覆盖，再用本节检查 gtest 惯用法是否放大或掩盖了问题。
