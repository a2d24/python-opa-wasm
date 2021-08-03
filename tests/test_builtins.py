import pytest

from opa_wasm import OPAPolicy

def sprintf(string, values):
    return string.replace("%v", "{}").format(*values)

def test_throws_if_builtin_missing():
    with pytest.raises(LookupError):
        OPAPolicy('./policy_with_builtins.wasm')

def test_with_builtin_function():
    builtins = {'sprintf': sprintf}
    policy = OPAPolicy('./policy_with_builtins.wasm', builtins=builtins)
    policy.set_data({"company_name": "ACME"})

    assert policy.evaluate({"user":"alice"}) == [
        {
            'result': {
                'allow': True,
                'message': "Hello There alice! Welcome to ACME"
            }
        }
    ]
