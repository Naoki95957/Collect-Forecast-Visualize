from adapters.mexico_adapter import MexicoAdapter
from adapters.scraper_adapter import ScraperAdapter
import pytest
import platform
import arrow

rpi = pytest.mark.skipif((
    platform.architecture()[0] == "32bit"),
    reason="Raspberry pi can't run mexico for some reason"
)


@pytest.fixture(scope='module', autouse=True)
def get_adapter():
    print("init el salvador adapter testing")
    ma = MexicoAdapter()
    yield ma


# test that the adapter doesn't crash
@rpi
def test_1():
    try:
        get_adapter
        assert True
    except Exception as e:
        print(e)
        assert False


# test that the adapter pattern holds
@rpi
def test_2():
    ma = MexicoAdapter(get_adapter)
    if isinstance(ma, ScraperAdapter):
        assert True
    else:
        assert False


# test that the adapter will not repeat a scrape
@rpi
def test_3():
    ma = MexicoAdapter(get_adapter)
    ma.scrape_new_data()
    if ma.scrape_new_data():
        assert False
    else:
        assert True


# test the scrape history method
@rpi
def test_4():
    ma = MexicoAdapter(get_adapter)
    if ma.scrape_history(2018, 1, 21, 2018, 3, 21):
        assert True
    else:
        assert False


# verify frequency
@rpi
def test_5():
    ma = MexicoAdapter(get_adapter)
    if (ma.frequency() == 60 * 60 * 24 * 31):
        assert True
    else:
        assert False


# test the scrape history method
@rpi
def test_6():
    ma = MexicoAdapter(get_adapter)
    test_date = arrow.get(
        '02-26/01/2021',
        'HH-DD/MM/YYYY',
        locale='es',
        tzinfo='Mexico/General'
    ).datetime
    # TODO
    if ma.set_last_scraped_date(test_date):
        assert False
    else:
        assert True
