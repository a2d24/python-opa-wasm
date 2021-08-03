import pytest

from opa_wasm import OPAPolicy


def test_entrypoint_by_id():
    policy = OPAPolicy('./policy_simple.wasm')
    assert policy.evaluate({}, entrypoint=0) == [{'result': {"allow": False}}]
    assert policy.evaluate({}, entrypoint=1) == [{'result': False}]
    assert policy.evaluate({}, entrypoint=2) == []

def test_entrypoint_by_name():
    policy = OPAPolicy('./policy_simple.wasm')
    assert policy.evaluate({}, entrypoint='example/allow') == [{'result': False}]
    assert policy.evaluate({}, entrypoint='example/company_name') == []

def test_entrypoint_by_name_with_data():
    policy = OPAPolicy('./policy_simple.wasm')
    policy.set_data({"company_name": "ACME"})
    assert policy.evaluate({}, entrypoint='example/company_name') == [{'result': "ACME"}]

def test_invalid_entry_point():
    with pytest.raises(ValueError):
        policy = OPAPolicy('./policy_simple.wasm')
        policy.evaluate({}, entrypoint='foo.bar')
