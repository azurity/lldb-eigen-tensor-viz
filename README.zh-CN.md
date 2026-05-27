# LLDB Eigen Tensor Pretty Printer

为 LLDB 调试器提供 Eigen::Tensor 类型的美化打印和可视化能力。

## 功能特性

- **美化显示**：在调试器中以友好的格式显示 `Eigen::Tensor` 的类型和维度信息
- **交互式探索**：在 LLDB 的Variables窗口中展开张量，逐层导航各个维度的元素
- **多维度支持**：支持任意维度的张量（0维标量到N维张量）
- **TensorMap 支持**：除 `Eigen::Tensor` 外，也支持 `Eigen::TensorMap` 对象
- **高效缓存**：智能缓存张量元素，提升调试性能

## 安装

### 前置要求
- LLDB 调试器
- Python 3.x
- Eigen 库（用于编译调试的代码）

### 快速安装

```bash
INSTALL_PATH=~/.lldb-eigen-tensor-pretty-printer
git clone https://github.com/azurity/lldb-eigen-viz.git $INSTALL_PATH
echo 'command script import "'$INSTALL_PATH'/lldb_eigen_tensor_pretty_printer.py"' >> ~/.lldbinit
```

### 手动安装

1. **获取脚本文件**

   将 `lldb_eigen_tensor_pretty_printer.py` 复制到你的工作目录。

2. **配置LLDB初始化脚本**

   编辑或创建 `~/.lldbinit`，添加以下内容：

   ```
   command script import /path/to/lldb_eigen_tensor_pretty_printer.py
   ```

   用实际的文件路径替换 `/path/to/`。

3. **验证安装**

   在LLDB中运行：
   ```
   (lldb) type category list
   ```
   
   应该能看到 `Eigen` 分类已启用。

## 使用示例

### 编译示例代码

创建文件 `test_tensor.cpp`：

```cpp
#include <Eigen/Dense>

int main() {
    // 创建一个 3x4x5 的float张量
    Eigen::Tensor<float, 3> tensor(3, 4, 5);
    
    // 填充数据
    for (int i = 0; i < 3; ++i) {
        for (int j = 0; j < 4; ++j) {
            for (int k = 0; k < 5; ++k) {
                tensor(i, j, k) = i * 20 + j * 5 + k;
            }
        }
    }
    
    return 0;  // 在这里设置断点
}
```

编译调试版本：

```bash
g++ -g -std=c++17 -I/path/to/eigen test_tensor.cpp -o test_tensor
```

### 在LLDB中调试

```bash
lldb ./test_tensor
(lldb) br set -n main
(lldb) run
(lldb) next  # 执行到断点处

(lldb) frame variable tensor
# 输出示例：
# (Eigen::Tensor<float, 3, 0, long>) tensor = Eigen::Tensor<float, 3, 0, long>[3x4x5]

(lldb) frame variable tensor -d run  # 展开查看内容
# 可以看到：
# [0]
#   [0]
#     [0] = 0
#     [1] = 1
#     [2] = 2
#     ...
```

## 高级特性

### 访问嵌套元素

在LLDB的Variables窗口中，你可以：
- 点击展开箭头查看各个维度
- 逐层导航到具体的元素值
- 查看标量元素的具体数值

### 支持的张量配置

本插件支持以下张量模板：

```cpp
Eigen::Tensor<ScalarType, NumDimensions, StorageOrder>
Eigen::TensorMap<Eigen::Tensor<ScalarType, NumDimensions, StorageOrder>>
```

- **ScalarType**：任何标量类型（float、double、int 等）
- **NumDimensions**：任意维度数
- **StorageOrder**：`0`（`Eigen::ColMajor`）或 `1`（`Eigen::RowMajor`）

## 技术细节

### 核心组件

1. **TensorDesc 类**
   - 解析张量的元数据（维度、类型、存储布局）
   - 处理索引与线性偏移的相互转换

2. **TensorSyntheticProvider 类**
   - 实现LLDB的合成类型提供者接口
   - 管理张量元素的动态加载和缓存

3. **TensorIterSyntheticProvider 类**
   - 处理多维张量的递归展开
   - 支持任意深度的维度导航

### 性能优化

- **元素缓存**：已访问的元素被缓存，避免重复查询
- **延迟加载**：仅在需要时才访问张量元素
- **类型管理**：动态生成迭代器类型，复用类型定义

## 许可证

MIT License

## 相关资源

- [LLDB Python API 文档](https://lldb.llvm.org/python_api.html)
- [Eigen Tensor 文档](https://eigen.tuxfamily.org/dox/unsupported/group__CXX11__Tensor__Module.html)
- [LLDB 类型定制指南](https://lldb.llvm.org/use/variable.html)
