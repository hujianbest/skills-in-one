# MDC HDT 环境准备指南

在MDC项目中使用HDT测试前，需要先配置测试环境，包括创建目录结构、测试桩(stubs)和构建系统。

## 标准目录结构

组件目录下创建HDT标准结构：

```bash
cd <component_dir>
mkdir -p test/hdt/{tests,conf,stubs}
```

最终目录结构：
```
test/hdt/
├── CMakeLists.txt           # MDC HDT构建配置
├── conf/
│   ├── comp.cmake          # 组件CMake配置（GTest依赖）
│   └── config.yaml         # HDT配置
├── stubs/                  # 测试桩（隔离MDC依赖）
│   ├── aps_logger.h
│   ├── common_msgs/
│   │   └── VehicleBasicInfo.h
│   ├── sensor_utils/
│   │   └── common/
│   │       └── common_unicom_io.h
│   └── ss_msgs/
│       ├── SsSystemStatus.h
│       └── SystemStatus.h
└── tests/                  # 测试源文件
    └── test_*.cpp
```

## 测试桩(stubs)创建

### 原则

- 桩模拟依赖的核心行为，不追求完整实现
- 支持测试需要的操作（如SubscribeMsg、消息发布）
- 桩放在`stubs/`目录并通过include优先加载（覆盖真实依赖）

### 消息类型桩示例

```cpp
// stubs/ss_msgs/SsSystemStatus.h
#ifndef SS_MSGS_SSSYSTEMSTATUS_H
#define SS_MSGS_SSSYSTEMSTATUS_H

#include <cstdint>
#include <memory>

namespace ss_msgs {
struct SystemStatus_ {
    uint32_t state = 0;
    uint32_t subState = 0;
};
using SystemStatus = SystemStatus_;

template <class ContainerAllocator>
struct SsSystemStatus_ {
    using ConstPtr = std::shared_ptr<const SsSystemStatus_<ContainerAllocator>>;
    SystemStatus_ sysStatus{};
    SystemStatus_ curStatus{};
    SystemStatus_ destStatus{};
    int32_t mode = 0;
    int32_t operation = 0;
    uint32_t state = 0;
};
using SsSystemStatus = SsSystemStatus_<std::allocator<void>>;
}
#endif
```

### 中间件桩示例

```cpp
// stubs/sensor_utils/common/common_unicom_io.h
namespace Sensor { namespace Common {
template<typename RosMsgType>
class CommonUnicomIo final {
    using SubCallback = std::function<void(const RosMsgType&)>;
public:
    bool SubscribeMsg(const std::string& topic, 
                     const SubCallback& func, 
                     const std::uint32_t queueSize = 3U) {
        if (!func || m_forceFailure) return false;
        if (!m_callback) {
            m_callback = func;
            m_topic = topic;
            return true;
        }
        return true;  // 允许重复订阅（幂等性）
    }
    
    void SetForceFailure(bool fail) { m_forceFailure = fail; }
    
private:
    SubCallback m_callback;
    std::string m_topic;
    bool m_forceFailure = false;
};
}}
```

### 日志宏桩示例

```cpp
// stubs/aps_logger.h
#ifndef APS_LOGGER_H
#define APS_LOGGER_H

#include <iostream>
#include <string>

#define INFO_LOG(tag, msg) std::cout << "[INFO] " << tag << ": " << msg << std::endl
#define ERROR_LOG(tag, msg) std::cerr << "[ERROR] " << tag << ": " << msg << std::endl
#define WARN_LOG(tag, msg) std::cout << "[WARN] " << tag << ": " << msg << std::endl

#endif
```

## CMakeLists.txt配置

使用MDC的 `mdc_dt_binary` 和 `mdc_dt_select` 函数：

```cmake
cmake_minimum_required(VERSION 3.16)
project(ai2s_d_hdt_test VERSION 1.0 LANGUAGES C CXX)

# 包含MDC测试依赖
include("${CMAKE_CURRENT_SOURCE_DIR}/conf/comp.cmake")
include(${MDC_TOP_DIR}/core/ci/cmake/mmake/cc/mdc_cc_test.cmake)

get_filename_component(COMP_DIR ../.. ABSOLUTE)

# 添加桩的include路径（必须优先，覆盖真实依赖）
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/stubs)

# 生成测试目标
mdc_dt_binary(ai2s_d_status_test
  INCS
    ${COMP_DIR}/include/private
    ${COMP_DIR}/include/public
    ${COMP_DIR}/test/hdt/tests
  SRCS
    ${COMP_DIR}/src/ai_infer_status.cpp
)

mdc_dt_select(ai2s_d_status_test TEST_TYPE "ut"
  SRCS
    ${COMP_DIR}/test/hdt/tests/test_ai_infer_status.cpp
)

# 链接gtest/gmock
target_link_libraries(ai2s_d_status_test PRIVATE gtest gmock gtest_main pthread)
```

## comp.cmake配置

```cmake
# GTest配置
find_package(GTest REQUIRED)
find_package(GMock REQUIRED)
```

## config.yaml配置

```yaml
---
version: 1.0.0

project:
  name: "ai2s_d_test"
  desc: "AI inference service component HDT tests"

pipeline:
  build:
    - task: "cmake_test"
  run:
    - task: "run_test"
      args: -a"--gtest_output=json:report.json"
  report:
    - task: "gcovr_report"
      args: -a"-f ../../include -f ../../src -e '\\.+\\.h' --json coverage.json"

components:
  - type: "hdt_cmc_c_cpp"
    manifest:
      gtest: null
      mockcpp-kirin: null
      gcov: null
      asan: null
```

## Stubs创建检查清单

- [ ] 每个include依赖都有对应的stub文件
- [ ] 消息stub包含主要字段定义和ConstPtr
- [ ] 中间件stub包含核心方法（SubscribeMsg/PublishMsg）
- [ ] 日志stub提供INFO_LOG/ERROR_LOG/WARN_LOG宏
- [ ] stub目录在include路径优先级第一
- [ ] 编译无"找不到头文件"错误
- [ ] 链接无"undefined reference"错误

## 环境验证

构建并运行空测试确保环境正常：

```bash
cd test/hdt
rm -rf build
cmake -S . -B build \
  -DCMAKE_BUILD_TYPE=Debug \
  -DMDC_CHIP=1951lite \
  -DMDC_NEW_PRODUCT=mdc620max \
  -DMDC_NEW_VERSION=common \
  -DMDC_NEW_MODE=inside \
  -DMDC_TOP_DIR=<MDC_ROOT>
cd build && make -j$(nproc)
./ai2s_d_status_test --gtest_color=yes
```
