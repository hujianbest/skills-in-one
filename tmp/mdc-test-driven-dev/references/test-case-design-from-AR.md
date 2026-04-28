# MDC HDT 测试用例设计参考指南

本文档基于AR设计文档section 6.2测试用例规范，提供标准的测试用例设计指导。

## 测试用例设计流程

### 步骤1：读取AR设计文档section 6.2

AR设计文档（例如 `features/AR20260421964780-state-subscription/ar-design.md`）的section 6.2提供测试用例清单：

| 功能点                          | 测试用例                                           | 预期结果                                                           |
| ------------------------------- | -------------------------------------------------- | ------------------------------------------------------------------ |
| Init-订阅成功                   | SubscribeMsg两个topic都返回true                    | Init返回true，m_ssSubscribed=true, m_vehicleSubscribed=true        |
| IsInferAllowed-人驾允许         | state=WORKING, adsWorkStatus=1                     | 返回true                                                           |

### 步骤2：从AR用例表转换到HDT测试代码

按照以下规则转换：

| AR表格列        | HDT代码位置        |
|----------------|-------------------|
| "功能点"        | 测试用例命名（前缀）  |
| "测试用例"       | 测试实现和断言期望     |
| "预期结果"       | 断言校验和失败信息    |

### 步骤3：应用命名规范

**格式：** `功能点_测试场景_预期中文结果`

**示例：**
- AR：Init-订阅成功 → HDT：`Init_订阅成功_两个Topic都返回true`
- AR：IsInferAllowed-人驾允许 → HDT：`IsInferAllowed_WORKING状态且人驾允许返回true`

## 完整示例：AR设计文档到HDT测试转换

**AR设计文档section 6.2内容：**

```
| 功能点                          | 测试用例                                           | 预期结果                                                           |
| ------------------------------- | -------------------------------------------------- | ------------------------------------------------------------------ |
| Init-订阅成功                   | SubscribeMsg两个topic都返回true                    | Init返回true，m_ssSubscribed=true, m_vehicleSubscribed=true        |
| Init-订阅部分失败               | 一个订阅返回false                                  | Init返回false，记录ERROR日志                                       |
| OnSystemStatusCallback-正常     | 收到有效SystemStatus消息                           | m_systemStatus.state/subState更新，m_ssReceived=true               |
| OnVehicleBasicInfoCallback-正常 | 收到有效VehicleBasicInfo消息                       | m_vehicleInfo.adsWorkStatus/actualGear更新，m_vehicleReceived=true |
| OnSystemStatusCallback-空指针   | msg==nullptr                                       | 记录ERROR日志，不更新缓存                                          |
| IsInferAllowed-人驾允许         | state=WORKING, adsWorkStatus=1                     | 返回true                                                           |
| IsInferAllowed-驻车允许         | state=WORKING, adsWorkStatus=11, actualGear=1      | 返回true                                                           |
| IsInferAllowed-MDC状态拒绝      | state=SUSPEND                                      | 返回false                                                          |
| IsInferAllowed-智驾拒绝         | state=WORKING, adsWorkStatus=11, actualGear=4(D档) | 返回false                                                          |
| IsSubscriptionValid-都收到      | m_ssReceived=true, m_vehicleReceived=true          | 返回true                                                           |
| IsSubscriptionValid-部分未收到  | m_ssReceived=true, m_vehicleReceived=false         | 返回false                                                          |
```

**转换后的HDT测试代码：**

```cpp
// ========== Init功能测试 ==========

TEST_F(AiInferStatusTest, Init_订阅成功_两个Topic都返回true) {
    // 测试因子：订阅成功
    // 预期结果：Init返回true，m_ssSubscribed=true, m_vehicleSubscribed=true
    
    bool result = status->Init();
    
    EXPECT_TRUE(result) << "Init应返回true当两个订阅都成功";
}

TEST_F(AiInferStatusTest, Init_订阅部分失败_一个订阅返回false) {
    // 测试因子：部分订阅失败
    // 预期结果：Init返回false，记录ERROR日志
    
    WARN_LOG("AI2S_D_TEST", "模拟部分订阅失败场景");
    
    bool result = status->Init();
    
    EXPECT_FALSE(result) << "Init应返回false当任何一个订阅失败";
}

// ========== 回调功能测试 ==========

TEST_F(AiInferStatusTest, OnSystemStatusCallback_正常_收到消息更新缓存) {
    // 测试因子：有效SystemStatus消息
    // 预期结果：m_systemStatus.state/subState更新，m_ssReceived=true
    
    auto msg = std::make_shared<ss_msgs::SsSystemStatus>();
    msg->sysStatus.state = 1;  // WORKING
    msg->sysStatus.subState = 0;
    
    status->OnSystemStatusCallback(msg);
    
    EXPECT_TRUE(status->IsSubscriptionValid()) 
        << "收到消息后订阅应有效";
}

TEST_F(AiInferStatusTest, OnSystemStatusCallback_空指针_记录错误日志不更新缓存) {
    // 测试因子：msg==nullptr
    // 预期结果：记录ERROR日志，不更新缓存
    
    bool validityBefore = status->IsSubscriptionValid();
    status->OnSystemStatusCallback(nullptr);
    bool validityAfter = status->IsSubscriptionValid();
    
    EXPECT_EQ(validityBefore, validityAfter) 
        << "空指针不应改变订阅有效性";
}

TEST_F(AiInferStatusTest, OnVehicleBasicInfoCallback_正常_收到消息更新缓存) {
    // 测试因子：有效VehicleBasicInfo消息
    // 预期结果：m_vehicleInfo.adsWorkStatus/actualGear更新，m_vehicleReceived=true
    
    auto msg = std::make_shared<common_msgs::VehicleBasicInfo>();
    msg->adsWorkStatus = 11;  // NCA（自动驾驶）
    msg->actualGear.value = 1;      // P档（驻车）
    
    status->OnVehicleBasicInfoCallback(msg);
    
    EXPECT_TRUE(status->IsSubscriptionValid()) 
        << "收到消息后订阅应有效";
}

// ========== 推理准入判断测试 ==========

TEST_F(AiInferStatusTest, IsInferAllowed_WORKING状态且人驾允许返回true) {
    // 测试因子：state=WORKING, adsWorkStatus=1（人驾）
    // 预期结果：返回true
    
    PublishSystemStatusWorkMsg();
    PublishVehicleBasicInfoHumanDriveMsg();
    
    EXPECT_TRUE(status->IsInferAllowed()) 
        << "WORKING+人驾应允许推理";
}

TEST_F(AiInferStatusTest, IsInferAllowed_自动驾驶但驻车允许返回true) {
    // 测试因子：state=WORKING, adsWorkStatus=11, actualGear=1（P档驻车）
    // 预期结果：返回true
    
    PublishSystemStatusWorkMsg();
    
    auto msg = std::make_shared<common_msgs::VehicleBasicInfo>();
    msg->adsWorkStatus = 11;      // NCA（自动驾驶）
    msg->actualGear.value = 1;      // P档
    status->OnVehicleBasicInfoCallback(msg);
    
    EXPECT_TRUE(status->IsInferAllowed()) 
        << "自动驾驶+驻车应允许推理";
}

TEST_F(AiInferStatusTest, IsInferAllowed_SUSPEND状态拒绝返回false) {
    // 测试因子：state=SUSPEND
    // 预期结果：返回false
    
    auto msg = std::make_shared<ss_msgs::SsSystemStatus>();
    msg->sysStatus.state = 2;  // SUSPEND
    status->OnSystemStatusCallback(msg);
    PublishVehicleBasicInfoHumanDriveMsg();
    
    EXPECT_FALSE(status->IsInferAllowed()) 
        << "SUSPEND状态应拒绝推理";
}

TEST_F(AiInferStatusTest, IsInferAllowed_自动驾驶且非驻车拒绝返回false) {
    // 测试因子：adsWorkStatus>10且actualGear≠1
    // 预期结果：返回false
    
    PublishSystemStatusWorkMsg();
    
    auto msg = std::make_shared<common_msgs::VehicleBasicInfo>();
    msg->adsWorkStatus = 11;      // NCA（自动驾驶）
    msg->actualGear.value = 4;      // D档
    status->OnVehicleBasicInfoCallback(msg);
    
    EXPECT_FALSE(status->IsInferAllowed()) 
        << "自动驾驶+非驻车应拒绝推理";
}

// ========== IsSubscriptionValid测试 ==========

TEST_F(AiInferStatusTest, IsSubscriptionValid_都收到消息返回true) {
    // 测试因子：m_ssReceived=true, m_vehicleReceived=true
    // 预期结果：返回true
    
    PublishSystemStatusWorkMsg();
    PublishVehicleBasicInfoHumanDriveMsg();
    
    EXPECT_TRUE(status->IsSubscriptionValid()) 
        << "都收到消息时应返回true";
}

TEST_F(AiInferStatusTest, IsSubscriptionValid_部分未收到返回false) {
    // 测试因子：m_ssReceived=true, m_vehicleReceived=false
    // 预期结果：返回false
    
    PublishSystemStatusWorkMsg();
    
    EXPECT_FALSE(status->IsSubscriptionValid()) 
        << "部分未收到消息时应返回false";
}
```

## 测试用例添加说明

1. **使用辅助方法**：将重复的消息构造提取到Test Fixture的辅助方法中（如 `PublishSystemStatusWorkMsg()`, `PublishVehicleBasicInfoHumanDriveMsg()`）

2. **包含中文错误信息**：`<< "中文描述"` 墄强失败时可读性

3. **遵守断言要求**：每个测试用例至少1个断言

4. **基于AR设计**：测试用例直接对应AR设计文档section 6.2的测试用例表

5. **命名对应功能点**：测试命名首段对应AR文档"功能点"列

## 测试覆盖检查清单

从AR设计section 6.2生成测试后，逐项验证：

- [ ] AR文档section 6.2的每个功能点都有对应测试
- [ ] AR文档section 6.2的每个测试用例都有对应测试代码
- [ ] 测试命名清晰描述场景（中文结尾）
- [ ] 每个测试包含测试因子注释
- [ ] 每个测试包含预期结果注释
- [ ] 每个测试至少1个断言
- [ ] 断言失败信息包含中文说明
- [ ] 重复代码提取到辅助方法

## 常见问题

**Q：测试名称太长**  
A：保持清晰，长度不是问题。键信息：功能点 + 测试场景 + 预期结果

**Q：AR文档测试用例表为空**  
A：联系相关人员补充测试用例，或基于业务逻辑自行补充测试场景

**Q：应该测试私有方法吗**  
A：通过public接口测试。如果必须测private，使用friend class或#define private public

**Q：如何测试无返回值函数**  
A：验证内部状态或副作用，如 `EXPECT_TRUE(status->IsSubscriptionValid())`

## 参考资料

- MDC HDT构建环境：@see @mdc-test-driven-dev SKILL.md "MDC HDT 环境准备"
- GoogleTest文档：https://google.github.io/googletest/
- AR设计文档格式：参考 `features/*-*/ar-design.md` section 6.2
