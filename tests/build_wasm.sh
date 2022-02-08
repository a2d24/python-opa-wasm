opa build -t wasm -e example -e example/allow -e example/company_name policy.rego
tar -zxvf bundle.tar.gz /policy.wasm
mv policy.wasm policy_simple.wasm
rm bundle.tar.gz

opa build -t wasm -e example policy_with_builtins.rego
tar -zxvf bundle.tar.gz /policy.wasm
mv policy.wasm policy_with_builtins.wasm
rm bundle.tar.gz

opa build -t wasm -e memory/check policy_memory_check.rego
tar -zxvf bundle.tar.gz /policy.wasm
mv policy.wasm policy_memory_check.wasm
rm bundle.tar.gz
