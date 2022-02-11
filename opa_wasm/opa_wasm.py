import itertools
import json
from pathlib import Path
from typing import Union, Tuple

from wasmer import Memory, MemoryType
from wasmer import engine, Store, Module, Instance, ImportObject, Function

try:
    from wasmer_compiler_cranelift import Compiler
except ImportError:
    from wasmer_compiler_llvm import Compiler


class OPAPolicy:
    STORE = Store(engine.JIT(Compiler))

    def __init__(self, wasm_path, memory_pages=5, max_memory_pages=None, builtins=None):
        if not Path(wasm_path).is_file():
            raise ValueError(f"Path: {wasm_path} is not a valid file")

        self.memory = Memory(OPAPolicy.STORE, MemoryType(memory_pages, maximum=max_memory_pages, shared=False))

        import_object = ImportObject()
        import_object.register(
            "env",
            {
                "memory": self.memory,
                "opa_builtin0": Function(OPAPolicy.STORE, self._opa_builtin0),
                "opa_builtin1": Function(OPAPolicy.STORE, self._opa_builtin1),
                "opa_builtin2": Function(OPAPolicy.STORE, self._opa_builtin2),
                "opa_builtin3": Function(OPAPolicy.STORE, self._opa_builtin3),
                "opa_builtin4": Function(OPAPolicy.STORE, self._opa_builtin4),
                "opa_abort": Function(OPAPolicy.STORE, self._opa_abort),
                "opa_println": Function(OPAPolicy.STORE, self._opa_println)
            }
        )

        self.module = Module(OPAPolicy.STORE, open(wasm_path, 'rb').read())
        self.instance = Instance(self.module, import_object)

        abi_major_version = self.instance.exports.opa_wasm_abi_version
        if abi_major_version and abi_major_version.value != 1:
            raise RuntimeError(f"Unsupported ABI Version {abi_major_version.value}")

        abi_minor_version = self.instance.exports.opa_wasm_abi_minor_version
        if abi_minor_version and abi_minor_version.value >= 2:
            self.supports_fastpath = True
        else:
            self.supports_fastpath = False

        self.entrypoints = self._fetch_json(self.instance.exports.entrypoints())
        self.builtins_by_id = self._create_builtins_map(builtins if builtins else {})

        # Set the default value for data. This can be overwritten by set_data
        self.data_address = self._put_json({})

        self.base_heap_pointer = self.instance.exports.opa_heap_ptr_get()
        self.data_heap_pointer = self.base_heap_pointer
        self.heap_pointer = self.base_heap_pointer

    def evaluate(self, input, entrypoint=0):
        entrypoint = self._lookup_entrypoint(entrypoint)

        # Before each evaluation, reset the heap pointer to the data_heap_pointer
        self.heap_pointer = self.data_heap_pointer

        if not self.supports_fastpath:
            return self._evaluate_legacy(input, entrypoint)

        return self._evaluate_fastpath(input, entrypoint)

    def set_data(self, data):
        # Reset the heap to the base_heap_pointer when data is changed
        self.instance.exports.opa_heap_ptr_set(self.base_heap_pointer)

        #  Perform update of data and pointers
        self.data_address = self._put_json(data)
        self.data_heap_pointer = self.instance.exports.opa_heap_ptr_get()
        self.heap_pointer = self.data_heap_pointer

    def _evaluate_fastpath(self, input, entrypoint):
        input_address, input_length = self._put_json_in_memory(input)
        result = self.instance.exports.opa_eval(
            0,
            entrypoint,
            self.data_address,
            input_address,
            input_length,
            self.heap_pointer,
            0
        )
        return self._fetch_json_raw(result)

    def _evaluate_legacy(self, input, entrypoint):
        # Reset the heap pointer before each evaluation
        self.instance.exports.opa_heap_ptr_set(self.data_heap_pointer)
        input_address = self._put_json(input)

        context = self.instance.exports.opa_eval_ctx_new()

        self.instance.exports.opa_eval_ctx_set_input(context, input_address)
        self.instance.exports.opa_eval_ctx_set_data(context, self.data_address)
        self.instance.exports.opa_eval_ctx_set_entrypoint(context, entrypoint)

        self.instance.exports.eval(context)
        result_address = self.instance.exports.opa_eval_ctx_get_result(context)

        return self._fetch_json(result_address)

    def _fetch_json(self, address: int):
        json_address = self.instance.exports.opa_json_dump(address)
        return self._fetch_json_raw(json_address)

    def _fetch_json_raw(self, json_address: int):
        return json.loads(self._fetch_string_as_bytearray(json_address))

    def _put_json(self, value) -> int:
        json_string = json.dumps(value).encode('utf-8')
        size = len(json_string)

        dest_string_address = self.instance.exports.opa_malloc(size)
        buffer = self.memory.uint8_view(offset=dest_string_address)
        buffer[0:size] = bytearray(json_string)

        dest_json_address = self.instance.exports.opa_json_parse(dest_string_address, size)

        if dest_json_address == 0:
            raise RuntimeError("Failed to parse JSON Value")

        return dest_json_address

    def _put_json_in_memory(self, value) -> Tuple[int, int]:
        json_string = json.dumps(value).encode('utf-8')
        input_length = len(json_string)

        input_address = self.heap_pointer
        buffer = self.memory.uint8_view(offset=input_address)
        buffer[0:input_length] = bytearray(json_string)

        self.heap_pointer = input_address + input_length
        return input_address, input_length

    def _fetch_string_as_bytearray(self, address) -> bytearray:
        memory_buffer = bytearray(self.memory.buffer)
        start_of_json_string_iterator = itertools.islice(memory_buffer, address, None)
        json_string_iterator = itertools.takewhile(bool, start_of_json_string_iterator)  # Null terminated string
        return bytearray(json_string_iterator)

    def _dispatch(self, id: int, *args):
        return self._put_json(self.builtins_by_id[id](*args))

    def _create_builtins_map(self, builtins):
        builtins_by_id = {}
        builtin_functions_required = self._fetch_json(self.instance.exports.builtins())

        for function_name, id in builtin_functions_required.items():
            if function_name not in builtins:
                raise LookupError(f"A required builtin '{function_name}' function was not provided.")

            builtins_by_id[id] = builtins[function_name]

        return builtins_by_id

    def _opa_builtin0(self, builtin_id: int, ctx: int) -> int:
        return self._dispatch(builtin_id)

    def _opa_builtin1(self, builtin_id: int, ctx: int, _1: int) -> int:
        return self._dispatch(builtin_id, *self._make_args_for_builtin(_1))

    def _opa_builtin2(self, builtin_id: int, ctx: int, _1: int, _2: int) -> int:
        return self._dispatch(builtin_id, *self._make_args_for_builtin(_1, _2))

    def _opa_builtin3(self, builtin_id: int, ctx: int, _1: int, _2: int, _3: int) -> int:
        return self._dispatch(builtin_id, *self._make_args_for_builtin(_1, _2, _3))

    def _opa_builtin4(self, builtin_id: int, ctx: int, _1: int, _2: int, _3: int, _4: int) -> int:
        return self._dispatch(builtin_id, *self._make_args_for_builtin(_1, _2, _3, _4))

    def _opa_abort(self, address: int):
        raise RuntimeError(f"OPA Aborted with message: {self._fetch_string_as_bytearray(address).decode('utf-8')}")

    def _opa_println(self, address: int):
        print(self._fetch_string_as_bytearray(address).decode('utf-8'))

    def _make_args_for_builtin(self, *addresses):
        return [self._fetch_json(address) for address in addresses]

    def _lookup_entrypoint(self, entrypoint: Union[str, int]) -> int:
        if isinstance(entrypoint, int) and entrypoint < len(self.entrypoints):
            return entrypoint

        if isinstance(entrypoint, str) and entrypoint in self.entrypoints:
            return self.entrypoints[entrypoint]

        raise ValueError(f"The specified entrypoint '{entrypoint}' is not valid")
