# LLDB Eigen Tensor Pretty Printer

Provides pretty-printing and visualization support for `Eigen::Tensor` types in the LLDB debugger.

- For the Chinese version, see [README.zh-CN.md](README.zh-CN.md).

## Features

- **Pretty formatting**: Displays `Eigen::Tensor` type and dimension information in a clear, readable format within the debugger
- **Interactive exploration**: Expands tensors in LLDB's Variables view for step-by-step navigation through dimensions
- **Multi-dimensional support**: Handles tensors of any rank, from 0D scalars to N-dimensional tensors
- **TensorMap support**: Also supports `Eigen::TensorMap` objects in addition to `Eigen::Tensor`
- **Efficient caching**: Caches tensor elements intelligently to improve debugging performance

## Installation

### Requirements
- LLDB debugger
- Python 3.x
- Eigen library (used by the debugged code)

### Quick install

```bash
INSTALL_PATH=~/.lldb-eigen-tensor-pretty-printer
git clone https://github.com/azurity/lldb-eigen-viz.git $INSTALL_PATH
echo 'command script import "'$INSTALL_PATH'/lldb_eigen_tensor_pretty_printer.py"' >> ~/.lldbinit
```

### Manual install

1. **Get the script file**

   Copy `lldb_eigen_tensor_pretty_printer.py` into your working directory.

2. **Configure LLDB init script**

   Edit or create `~/.lldbinit` and add:

   ```
   command script import /path/to/lldb_eigen_tensor_pretty_printer.py
   ```

   Replace `/path/to/` with the actual path to the script.

3. **Verify installation**

   In LLDB, run:
   ```
   (lldb) type category list
   ```

   You should see the `Eigen` category enabled.

## Usage example

### Build example code

Create `test_tensor.cpp`:

```cpp
#include <Eigen/Dense>

int main() {
    // Create a 3x4x5 float tensor
    Eigen::Tensor<float, 3> tensor(3, 4, 5);

    // Fill tensor data
    for (int i = 0; i < 3; ++i) {
        for (int j = 0; j < 4; ++j) {
            for (int k = 0; k < 5; ++k) {
                tensor(i, j, k) = i * 20 + j * 5 + k;
            }
        }
    }

    return 0;  // Set breakpoint here
}
```

Build with debug symbols:

```bash
g++ -g -std=c++17 -I/path/to/eigen test_tensor.cpp -o test_tensor
```

### Debug in LLDB

```bash
lldb ./test_tensor
(lldb) br set -n main
(lldb) run
(lldb) next  # Run to the breakpoint

(lldb) frame variable tensor
# Example output:
# (Eigen::Tensor<float, 3, 0, long>) tensor = Eigen::Tensor<float, 3, 0, long>[3x4x5]

(lldb) frame variable tensor -d run  # Expand to inspect contents
# You should see:
# [0]
#   [0]
#     [0] = 0
#     [1] = 1
#     [2] = 2
#     ...
```

## Advanced features

### Nested element access

In LLDB's Variables view, you can:
- click the expand chevrons to inspect each tensor dimension
- navigate through nested tensor elements step by step
- view scalar element values directly

### Supported tensor configuration

This pretty printer supports the following tensor templates:

```cpp
Eigen::Tensor<ScalarType, NumDimensions, StorageOrder>
Eigen::TensorMap<Eigen::Tensor<ScalarType, NumDimensions, StorageOrder>>
```

- **ScalarType**: any scalar type such as `float`, `double`, `int`, etc.
- **NumDimensions**: any number of dimensions
- **StorageOrder**: `0` (`Eigen::ColMajor`) or `1` (`Eigen::RowMajor`)

## Implementation details

### Core components

1. **TensorDesc class**
   - parses tensor metadata, including dimensions, type, and storage layout
   - converts between multidimensional indices and linear offsets

2. **TensorSyntheticProvider class**
   - implements LLDB synthetic provider behavior
   - manages dynamic loading and caching of tensor elements

3. **TensorIterSyntheticProvider class**
   - handles recursive expansion of multi-dimensional tensors
   - supports navigation across arbitrary tensor ranks

### Performance optimizations

- **Element caching**: visited elements are cached to avoid repeated lookups
- **Lazy loading**: tensor data is accessed only when needed
- **Type management**: iterator types are created dynamically and reused

## License

MIT License

## Resources

- [LLDB Python API documentation](https://lldb.llvm.org/python_api.html)
- [Eigen Tensor documentation](https://eigen.tuxfamily.org/dox/unsupported/group__CXX11__Tensor__Module.html)
- [LLDB variable customization guide](https://lldb.llvm.org/use/variable.html)
