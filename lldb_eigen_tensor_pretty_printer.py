import lldb


globalDebugger = None


def __lldb_init_module(debugger, internal_dict):
    try:
        global globalDebugger
        globalDebugger = debugger
        debugger.HandleCommand(
            "type summary add --expand -x \"^Eigen::Tensor<.*>$\" -F lldb_eigen_tensor_pretty_printer.tensor_pretty_printer -p -r -w Eigen")
        debugger.HandleCommand(
            "type summary add --expand -x \"^Eigen::TensorMap<.*>$\" -F lldb_eigen_tensor_pretty_printer.tensor_pretty_printer -p -r -w Eigen")
        debugger.HandleCommand(
            "type synthetic add -x \"^Eigen::Tensor<.*>$\" -l lldb_eigen_tensor_pretty_printer.TensorSyntheticProvider -p -r -w Eigen")
        debugger.HandleCommand(
            "type synthetic add -x \"^Eigen::TensorMap<.*>$\" -l lldb_eigen_tensor_pretty_printer.TensorSyntheticProvider -p -r -w Eigen")
        debugger.HandleCommand("type category enable Eigen")
    except Exception as err:
        print(err)


class TensorDesc():
    def __init__(self, val_obj):
        real_value = val_obj.GetNonSyntheticValue()
        real_type = val_obj.type.GetCanonicalType()
        self.type_name = real_type.name
        self.is_map = False
        if real_type.name.split('<')[0] == 'Eigen::TensorMap':
            self.is_map = True
            real_type = real_type.template_args[0]
        self.scalar = real_type.template_args[0]
        self.N = int(real_type.GetTemplateArgumentValue(
            val_obj.GetTarget(), 1).value)
        self.direct = int(real_type.GetTemplateArgumentValue(
            val_obj.GetTarget(), 2).value)
        dimension_data = real_value.GetValueForExpressionPath(
            '.m_dimensions' if self.is_map else '.m_storage.m_dimensions').children[0].children[0]
        self.dims = [int(item.value) for item in dimension_data.children]

    def fold_index(self, index):
        indices = []
        iter = index
        if self.direct == 0:
            for i in range(self.N):
                iter, item = divmod(iter, self.dims[i])
                indices.append(item)
        else:
            for i in range(self.N - 1, -1, -1):
                iter, item = divmod(iter, self.dims[i])
                indices.insert(0, item)
        return indices

    def unfold_indices(self, indices):
        index = 0
        factor = 1
        if self.direct == 0:
            for i in range(self.N):
                index += indices[i] * factor
                factor *= self.dims[i]
        else:
            for i in range(self.N - 1, -1, -1):
                index += indices[i] * factor
                factor *= self.dims[i]
        return index


def tensor_pretty_printer(val_obj, internal_dict):
    try:
        desc = TensorDesc(val_obj)
        if desc.N == 0:
            return ""
        return f'{desc.type_name} [{"x".join([str(item) for item in desc.dims])}]'
    except Exception as err:
        print(err)
    return ""


tensor_iter_type_dict = dict()
tensor_iter_type_reverse_dict = dict()


def get_tensor_iter_type(val_obj, desc: TensorDesc):
    global tensor_iter_type_dict
    if desc.type_name not in tensor_iter_type_dict:
        name = f'__debug_eigen_tensor_iter_type_{len(tensor_iter_type_dict)}'
        var_name = f'__debug_eigen_tensor_iter_type_{len(tensor_iter_type_dict)}_var'
        tensor_iter_type_dict[desc.type_name] = val_obj.EvaluateExpression(
            f'struct {name} {{ void *data; size_t offset; size_t n; }}; struct {name}* {var_name} = 0; {var_name}').GetType().GetPointeeType()
        tensor_iter_type_reverse_dict[name] = val_obj.type.GetCanonicalType()
        globalDebugger.HandleCommand(
            f"type synthetic add -x \"^{name}$\" -l lldb_eigen_tensor_pretty_printer.TensorIterSyntheticProvider -p -r -w Eigen")
    return tensor_iter_type_dict[desc.type_name]


def create_children_getter(val_obj, base_index: int, sub_n: int):
    desc = TensorDesc(val_obj)
    data_ptr = int(val_obj.GetNonSyntheticValue(
    ).GetValueForExpressionPath('.m_data' if desc.is_map else '.m_storage.m_data').value, 16)
    if desc.N == 0:
        return None, 0, val_obj.CreateValueFromAddress(f'scalar', data_ptr, desc.scalar)
    elif sub_n + 1 == desc.N:
        def getter(index):
            indices = desc.fold_index(base_index)
            indices[sub_n] = index
            offset = desc.unfold_indices(indices)
            return val_obj.CreateValueFromAddress(f'[{index}]', data_ptr + offset * desc.scalar.GetByteSize(), desc.scalar)
        return getter, desc.dims[sub_n], None
    else:
        iter_type = get_tensor_iter_type(val_obj, desc)

        def getter(index):
            indices = desc.fold_index(base_index)
            indices[sub_n] = index
            offset = desc.unfold_indices(indices)
            data = lldb.SBData.CreateDataFromUInt64Array(lldb.eByteOrderLittle, 8, [
                                                         val_obj.addr.GetLoadAddress(val_obj.GetTarget()), offset, sub_n])
            return val_obj.CreateValueFromData(f'[{index}]', data, iter_type)
        return getter, desc.dims[sub_n], None


class BaseSyntheticProvider():
    def num_children(self, max_children: int) -> int:
        return self.children_n

    def get_child_index(self, name: str) -> int:
        try:
            return int(name.lstrip('[').rstrip(']'))
        except:
            return -1

    def get_child_at_index(self, index: int) -> lldb.SBValue | None:
        try:
            if index < 0 or index >= self.children_n:
                return None
            if index not in self.children_cache:
                self.children_cache[index] = self.children_getter(index)
        except Exception as err:
            print(err)
        return self.children_cache[index]

    def update(self) -> bool:
        return False

    def has_children(self) -> bool:
        return self.value is None

    def get_value(self) -> lldb.SBValue | None:
        return self.value


class TensorSyntheticProvider(BaseSyntheticProvider):
    def __init__(self, val_obj, internal_dict):
        try:
            self.children_getter, self.children_n, self.value = create_children_getter(
                val_obj, 0, 0)
            self.children_cache = dict()
        except Exception as err:
            print(err)


class TensorIterSyntheticProvider(BaseSyntheticProvider):
    def __init__(self, val_obj, internal_dict):
        try:
            raw_value = val_obj.GetNonSyntheticValue()
            real_type = tensor_iter_type_reverse_dict[raw_value.type.name]
            data_ptr = int(
                raw_value.GetValueForExpressionPath('.data').value, 16)
            offset = int(raw_value.GetValueForExpressionPath('.offset').value)
            n = int(raw_value.GetValueForExpressionPath('.n').value)
            self.children_getter, self.children_n, self.value = create_children_getter(
                val_obj.CreateValueFromAddress('base', data_ptr, real_type), offset, n + 1)
            self.children_cache = dict()
        except Exception as err:
            print(err)
