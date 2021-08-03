from opa_wasm import OPAPolicy


def test_execution_with_data():
    policy = OPAPolicy('./policy_simple.wasm')
    policy.set_data({"company_name": "ACME"})
    assert policy.evaluate({"user": "bob"}) == [
        {
            'result': {
                "allow": False,
                "company_name": "ACME"
            }
        }
    ]
