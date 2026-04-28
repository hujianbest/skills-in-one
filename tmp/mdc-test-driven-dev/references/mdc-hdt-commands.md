# MDC HDT 构建与运行命令参考

## 完整构建流程

```bash
cd test/hdt

# 1. 清理旧构建
rm -rf build

# 2. 配置CMake
cmake -S . -B build \
  -DCMAKE_BUILD_TYPE=Debug \
  -DMDC_CHIP=1951lite \
  -DMDC_NEW_PRODUCT=mdc620max \
  -DMDC_NEW_VERSION=common \
  -DMDC_NEW_MODE=inside \
  -DMDC_TOP_DIR=<MDC_ROOT>

# 3. 编译测试
cd build && make -j$(nproc)

# 4. 运行测试
./ai2s_d_status_test --gtest_color=yes
```

## 常用测试运行命令

```bash
# 运行所有测试
./ai2s_d_status_test --gtest_color=yes

# 运行特定测试（支持通配符）
./ai2s_d_status_test --gtest_filter=AiInferStatusTest.IsInferAllowed_*

# 运行特定Test Suite
./ai2s_d_status_test --gtest_filter=AiInferStatusTest.*

# 列出所有测试（不执行）
./ai2s_d_status_test --gtest_list_tests

# 调试特定测试（失败时中断）
./ai2s_d_status_test --gtest_filter=TestName --gtest_break_on_failure

# 重复运行测试（验证稳定性）
./ai2s_d_status_test --gtest_repeat=100 --gtest_filter=TestName

# 输出XML报告
./ai2s_d_status_test --gtest_output=xml:report.xml

# 输出JSON报告
./ai2s_d_status_test --gtest_output=json:report.json
```

## 常见构建问题排查

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `fatal error: xxx.h: No such file or directory` | stub缺失或include路径未配置 | 创建对应stub文件，确认stubs目录在include路径优先级第一 |
| `undefined reference to xxx` | 链接依赖缺失 | 补充stub完整实现或添加链接库 |
| `cannot find -lautosar_stub` | MDC构建系统依赖不存在 | 移除DEPS中的autosar_stub，改用stubs |
| `not found ... include/public` | 目录不存在 | 创建空目录或移除INCS中的对应路径 |
| `is private within this context` | 测试访问private方法 | 将回调方法改为public（框架接口） |
| `cannot convert ... to const ConstPtr&` | 消息类型不匹配 | 使用`std::make_shared`构造ConstPtr |

## CMAKE配置参数说明

| 参数 | 说明 | 常用值 |
|------|------|--------|
| `-DMDC_CHIP` | 芯片类型 | 1951lite, 1951, 7801 |
| `-DMDC_NEW_PRODUCT` | 产品型号 | mdc620max, mdc610 |
| `-DMDC_NEW_VERSION` | 版本 | common, release |
| `-DMDC_NEW_MODE` | 合作模式 | inside, platform |
| `-DMDC_TOP_DIR` | MDC项目根目录 | 绝对路径 |
| `-DMDC_TEST_TYPE` | 测试类型 | ut, it, fuzz |

## 获取MDC_ROOT路径

```bash
# 方法1：使用git-mm命令
git-mm --root-dir

# 方法2：从当前目录推断
# 如果工作目录是 .../mdc/core/soc/cass/cps/ai2s_d
# 则MDC_ROOT是 .../mdc
```
