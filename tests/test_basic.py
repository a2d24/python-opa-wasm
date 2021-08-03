import pytest

from opa_wasm import OPAPolicy


def test_policy_execution():
    policy = OPAPolicy('./policy_simple.wasm')
    assert policy.evaluate({}) == [{'result': {"allow": False}}]
    assert policy.evaluate({"user": "alice"}) == [{'result': {"allow": True}}]

def test_invalid_path():
    with pytest.raises(ValueError):
        OPAPolicy('./foo.wasm')
