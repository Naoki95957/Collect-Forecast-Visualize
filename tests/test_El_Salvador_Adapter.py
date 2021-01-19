from adapters.el_salvador_adaptor import ElSalvadorAdapter
import pytest

@pytest.fixture(scope='module', autouse=True)
def get_adapter():
    print("init el salvador adapter testing")
    esa = ElSalvadorAdapter()
    yield esa

def test_adapter_crash():
    try:
        get_adapter
        assert True
    except Exception as e:
        print(e)
        assert False