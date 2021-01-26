from adapters.mexico_adapter import MexicoAdapter
from adapters.scraper_adapter import ScraperAdapter
import pytest
import platform

rpi = pytest.mark.skipif((
    platform.architecture()[0] == "32bit"),
    reason="Raspberry pi can't run mexico for some reason"
)


@pytest.fixture(scope='module', autouse=True)
def get_adapter():
    print("init el salvador adapter testing")
    ma = MexicoAdapter()
    yield ma


@rpi
def test_adapter_crash():
    try:
        get_adapter
        assert True
    except Exception as e:
        print(e)
        assert False


@rpi
def test_adapter_conversion():
    ma = MexicoAdapter(get_adapter)
    if isinstance(ma, ScraperAdapter):
        assert True
    else:
        assert False


@rpi
def test_adapter_scrape_too_fast():
    ma = MexicoAdapter(get_adapter)
    ma.scrape_new_data()
    if ma.scrape_new_data():
        assert False
    else:
        assert True
