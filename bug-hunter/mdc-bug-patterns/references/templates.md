# C++ 代码Bug排查模板

## 1. mem-new-no-delete

**名称**: new 未配对 delete  
**类别**: 内存管理 (memory)  
**严重程度**: 严重 (critical)

**检测模式**:
查找 new 分配的内存但在所有退出路径中未调用 delete 的情况

**问题代码**:
```cpp
void process() {
    int* data = new int[100];
    data[0] = 42;
    // 缺少 delete[] data - 内存泄漏!
}
```

**修复代码**:
```cpp
void process() {
    std::vector<int> data(100);
    data[0] = 42;
}  // 自动清理
```

**修复建议**:
- 使用 std::vector 或 std::unique_ptr 实现自动清理
- 确保在析构函数或 RAII 包装器中调用 delete

---

## 2. mem-new-array-no-del-array

**名称**: new[] 未配对 delete[]  
**类别**: 内存管理 (memory)  
**严重程度**: 严重 (critical)

**检测模式**:
查找 new[] 分配的数组但未调用匹配的 delete[] 的情况

**问题代码**:
```cpp
void func() {
    int* arr = new int[50];
    // 缺少 delete[] arr
}
```

**修复代码**:
```cpp
void func() {
    std::vector<int> arr(50);
}  // 自动清理
```

**修复建议**:
- 使用 std::vector 进行数组管理
- 如果使用 new[]，确保在所有路径中调用 delete[]

---

## 3. mem-no-destructor

**名称**: 缺少析构函数  
**类别**: 内存管理 (memory)  
**严重程度**: 高 (high)

**检测模式**:
查找类中有原始指针成员但缺少析构函数的情况

**问题代码**:
```cpp
class Buffer {
public:
    Buffer(size_t size) : m_data(new char[size]) {}
    // 缺少析构函数 - 内存泄漏!
private:
    char* m_data;
    size_t m_size;
};
```

**修复代码**:
```cpp
class Buffer {
public:
    Buffer(size_t size) : m_data(new char[size]), m_size(size) {}
    ~Buffer() { delete[] m_data; }  // 添加析构函数
private:
    char* m_data;
    size_t m_size;
};
```

**修复建议**:
- 声明析构函数并执行 delete/delete[]
- 使用智能指针 (unique_ptr) 代替原始指针
- 遵循 Rule of Five

---

## 4. ptr-deref-no-check

**名称**: 指针解引用前未做空指针检查  
**类别**: 空指针 (null)  
**严重程度**: 严重 (critical)

**检测模式**:
查找指针在使用前未做空指针检查的解引用操作

**问题代码**:
```cpp
void usePointer(int* ptr) {
    int value = *ptr;  // 如果 ptr 为 null 会崩溃!
    process(value);
}
```

**修复代码**:
```cpp
void usePointer(int* ptr) {
    if (ptr == nullptr) return;
    int value = *ptr;
    process(value);
}
```

**修复建议**:
- 解引用前检查指针是否为 null
- 如果不允许为 null，使用引用 (&)

---

## 5. ptr-optional-value-no-check

**名称**: optional 访问时未检查  
**类别**: 空指针 (null)  
**严重程度**: 中 (medium)

**检测模式**:
查找调用 optional.value() 前未检查 has_value() 的情况

**问题代码**:
```cpp
void process() {
    int v = getValue().value();  // 如果没有值会抛出异常!
}
```

**修复代码**:
```cpp
void process() {
    auto opt = getValue();
    if (opt.has_value()) {
        int v = opt.value();
        process(v);
    }
}
```

**修复建议**:
- 调用 value() 前检查 has_value()
- 使用 value_or() 提供默认值

---

## 6. res-file-no-close

**名称**: 文件句柄未关闭  
**类别**: 资源管理 (resource)  
**严重程度**: 高 (high)

**检测模式**:
查找调用 fopen 但在所有退出路径中未调用 fclose 的情况

**问题代码**:
```cpp
void processFile(const char* path) {
    FILE* f = fopen(path, "r");
    if (!f) return;
    // 异常可能导致文件未关闭!
}
```

**修复代码**:
```cpp
void processFile(const std::string& path) {
    std::ifstream f(path);
    if (!f) return;
}  // 自动清理
```

**修复建议**:
- 使用 std::ifstream/ofstream 实现自动资源管理
- 确保在所有退出路径中调用 fclose

---

## 7. res-mutex-no-unlock

**名称**: 互斥锁未解锁  
**类别**: 资源管理 (resource)  
**严重程度**: 高 (high)

**检测模式**:
查找调用 mutex.lock() 但在所有路径中未匹配 unlock() 的情况

**问题代码**:
```cpp
void safeAccess() {
    mutex.lock();
    if (condition) {
        mutex.unlock();
        return;
    }
    // ... 执行工作
    mutex.unlock();
}
```

**修复代码**:
```cpp
void safeAccess() {
    std::lock_guard<std::mutex> lock(mutex);
    if (condition) return;
    // ... 执行工作
}  // 自动解锁
```

**修复建议**:
- 使用 std::lock_guard 或 std::unique_lock 实现自动解锁
- 确保在所有 return/throw 路径中调用 unlock

---

## 8. con-unsynchronized-access

**名称**: 未同步的共享数据访问  
**类别**: 并发 (concurrency)  
**严重程度**: 严重 (critical)

**检测模式**:
查找访问非 const 全局/静态变量但无互斥锁保护的情况

**问题代码**:
```cpp
int globalCounter = 0;
void increment() {
    globalCounter++;  // 非线程安全!
}
```

**修复代码**:
```cpp
std::atomic<int> globalCounter{0};
void increment() {
    globalCounter.fetch_add(1);
}
```

**修复建议**:
- 使用 std::atomic 处理简单计数器
- 使用 std::mutex 保护复杂操作

---

## 9. con-lock-ordering

**名称**: 潬换顺序不一致导致的死锁风险  
**类别**: 并发 (concurrency)  
**严重程度**: 中 (medium)

**检测模式**:
查找嵌套锁但锁获取顺序不一致的情况

**问题代码**:
```cpp
void thread1() {
    lockA.lock();
    lockB.lock();
}
void thread2() {
    lockB.lock();  // 可能死锁!
    lockA.lock();
}
```

**修复代码**:
```cpp
void thread1() {
    lockA.lock();
    lockB.lock();
}
void thread2() {
    lockA.lock();  // 一致的顺序
    lockB.lock();
}
```

**修复建议**:
- 始终按一致的顺序获取锁
- 使用 std::scoped_lock 处理多个锁

---

## 10. int-add-overflow

**名称**: 整数加法溢出  
**类别**: 逻辑 (logic)  
**严重程度**: 高 (high)

**检测模式**:
查找有符号整数加法运算但未进行溢出检查的情况

**问题代码**:
```cpp
int addNumbers(int a, int b) {
    return a + b;  // 可能溢出!
}
```

**修复代码**:
```cpp
int addNumbers(int a, int b) {
    int result;
    if (__builtin_add_overflow(a, b, &result)) {
        throw std::overflow_error("Integer overflow");
    }
    return result;
}
```

**修复建议**:
- 使用 __builtin_add_overflow 进行安全加法
- 使用 std::numeric_limits 进行边界检查

---

## 11. int-sub-overflow

**名称**: 整数减法下溢  
**类别**: 逻辑 (logic)  
**严重程度**: 高 (high)

**检测模式**:
查找减法运算可能下溢 INT_MIN 的情况

**问题代码**:
```cpp
int subtract(int a, int b) {
    return a - b;  // 可能下溢!
}
```

**修复代码**:
```cpp
int subtract(int a, int b) {
    int result;
    if (__builtin_sub_overflow(a, b, &result)) {
        throw std::overflow_error("Integer underflow");
    }
    return result;
}
```

**修复建议**:
- 使用 __builtin_sub_overflow 进行安全减法
- 运算前检查边界

---

## 12. int-mul-overflow

**名称**: 整数乘法溢出  
**类别**: 逻辑 (logic)  
**严重程度**: 高 (high)

**检测模式**:
查找乘法运算可能溢出的情况

**问题代码**:
```cpp
void allocate(size_t count) {
    int total = count * sizeof(int);  // count 很大时会溢出!
    int* buffer = new int[count];
}
```

**修复代码**:
```cpp
void allocate(size_t count) {
    if (count > SIZE_MAX / sizeof(int)) {
        throw std::bad_alloc();
    }
    size_t total = count * sizeof(int);
    int* buffer = new int[count];
}
```

**修复建议**:
- 使用 __builtin_mul_overflow 进行安全乘法
- 乘法前测试边界

---

## 13. int-shift-overflow

**名称**: 位运算溢出  
**类别**: 逻辑 (logic)  
**严重程度**: 中 (medium)

**检测模式**:
查找位移操作中的位移量 >= 类型宽度的情况

**问题代码**:
```cpp
int shiftLeft(int value, int amount) {
    return value << amount;  // 如果 amount >= 32 会未定义行为!
}
```

**修复代码**:
```cpp
int shiftLeft(int value, int amount) {
    if (amount < 0 || amount >= 32) {
        throw std::invalid_argument("Invalid shift amount");
    }
    return value << amount;
}
```

**修复建议**:
- 验证位移量非负且 < 类型宽度
- 使用 __builtin_clz 检查位移操作

---

## 14. int-signed-unsigned-mix

**名称**: 有符号无符号混用比较  
**类别**: 逻辑 (logic)  
**严重程度**: 中 (medium)

**检测模式**:
查找混用有符号和无符号类型的比较或运算

**问题代码**:
```cpp
void processVector(const std::vector<int>& vec) {
    for (int i = 0; i < vec.size(); i++) {  // 警告!
        std::cout << vec[i] << "\n";
    }
}
```

**修复代码**:
```cpp
void processVector(const std::vector<int>& vec) {
    for (size_t i = 0; i < vec.size(); i++) {
        std::cout << vec[i] << "\n";
    }
}
```

**修复建议**:
- 与 .size() 一致使用 size_t
- 显式转换为匹配的符号性

---

## 15. int-narrowing-cast

**名称**: 类型转换截断  
**类别**: 逻辑 (logic)  
**严重程度**: 低 (low)

**检测模式**:
查找无边界检查的窄化转换

**问题代码**:
```cpp
int fromLong(int64_t value) {
    int result = value;  // 如果 value > INT_MAX 会截断!
    return result;
}
```

**修复代码**:
```cpp
int fromLong(int64_t value) {
    if (value > INT_MAX || value < INT_MIN) {
        throw std::overflow_error("Value out of range");
    }
    return static_cast<int>(value);
}
```

**修复建议**:
- 窄化转换前检查边界
- 使用 static_cast 并进行显式验证

---

## 16. div-by-zero

**名称**: 除以零  
**类别**: 逻辑 (logic)  
**严重程度**: 高 (high)

**检测模式**:
查找除法/取模运算未检查分母为零的情况

**问题代码**:
```cpp
double divide(int a, int b) {
    return a / b;  // 如果 b 为 0 会崩溃!
}
```

**修复代码**:
```cpp
double divide(int a, int b) {
    if (b == 0) throw std::invalid_argument("Division by zero");
    return static_cast<double>(a) / b;
}
```

**修复建议**:
- 除法前检查分母不为零
- 对分母值进行边界检查

---

## 17. empty-container-access

**名称**: 空容器访问  
**类别**: 逻辑 (logic)  
**严重程度**: 高 (high)

**检测模式**:
查找调用 .front() 或 .back() 但未检查容器为空的情况

**问题代码**:
```cpp
void processFirst(const std::vector<int>& items) {
    int first = items.front();  // 如果为空会出现未定义行为!
}
```

**修复代码**:
```cpp
void processFirst(const std::vector<int>& items) {
    if (items.empty()) return;
    int first = items.front();
}
```

**修复建议**:
- 访问 .front() 或 .back() 前检查 .empty()
- 使用 .at() 进行边界检查访问

---