import os

os.system('opa build -t wasm -e sample policy.rego')
os.system('tar -zxvf bundle.tar.gz /policy.wasm')
os.system('rm bundle.tar.gz')

from opa_wasm import OPAPolicy

data = {"test_1": "123456789"}


policy = OPAPolicy('./policy.wasm', memory_pages=3)
policy.set_data(data)

result = policy.evaluate({"test_2": "Hello, World"})

assert result[0]['result']['test']['test_1'] == "123456789"
assert result[0]['result']['test']['test_2'] == "Hello, World"