# Open Policy Agent WebAssembly SDK for Python

This is the source for the
[opa-wasm](https://pypi.org/project/opa-wasm/)
Python module which is an SDK for using WebAssembly (wasm) compiled 
[Open Policy Agent](https://www.openpolicyagent.org/) Rego policies using [wasmer-python](https://github.com/wasmerio/wasmer-python).

# Getting Started
## Install the module

You may choose to use either the `cranelift` or `llvm` compiler package as follows: 

```
pip install opa-wasm[cranelift]
```
or
```
pip install opa-wasm[llvm]
```

For builds that target AWS Lambda as an execution environment, it is recommended to use cranelift. This avoids 
the need to bundle additional binary dependencies as part of the lambda package.

See the [wasmer-python](https://github.com/wasmerio/wasmer-python) docs for more information

## Usage

There are only a couple of steps required to start evaluating the policy.


```python
# Import the module
from opa_wasm import OPAPolicy

# Load a policy by specifying its file path
policy = OPAPolicy('./policy.wasm')

# Optional: Set policy data
policy.set_data({"company_name": "ACME"})

# Evaluate the policy
input = {"user": "alice"}
result = policy.evaluate(input)
```

## Writing the policy

See [https://www.openpolicyagent.org/docs/latest/how-do-i-write-policies/](https://www.openpolicyagent.org/docs/latest/how-do-i-write-policies/)

## Compiling the policy

Either use the [Compile REST API](https://www.openpolicyagent.org/docs/latest/rest-api/#compile-api) or `opa build` CLI tool.

For example, with OPA v0.20.5+:

```bash
opa build -t wasm -e 'example/allow' example.rego
```
Which compiles the `example.rego` policy file with the result set to
`data.example.allow`. The result will be an OPA bundle with the `policy.wasm`
binary included. 

See `opa build --help` for more details.

## Credits

This project was inspired by the equivalent NPM Module [@open-policy-agent/opa-wasm](https://github.com/open-policy-agent/npm-opa-wasm)