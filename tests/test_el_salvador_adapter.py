from adapters.el_salvador_adaptor import ElSalvadorAdapter
from adapters.scraper_adapter import ScraperAdapter
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


def test_adapter_conversion():
    esa = ElSalvadorAdapter(get_adapter)
    if isinstance(esa, ScraperAdapter):
        assert True
    else:
        assert False


def test_adapter_scrape_too_fast():
    esa = ElSalvadorAdapter(get_adapter)
    esa.scrape_new_data()
    if esa.scrape_new_data():
        assert False
    else:
        assert True
