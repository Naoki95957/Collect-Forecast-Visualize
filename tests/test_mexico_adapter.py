from adapters.mexico_adapter import MexicoAdapter
from adapters.scraper_adapter import ScraperAdapter
import pytest
import pytz
import datetime
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


@rpi
def test_adapter_crash():
    try:
        get_adapter
        assert True
    except Exception as e:
        print(e)
        assert False


@rpi
def test_adapter_inheritance(get_adapter):
    ma = get_adapter
    if isinstance(ma, ScraperAdapter):
        assert True
    else:
        assert False


@rpi
def test_adapter_scrape_too_fast(get_adapter):
    ma = get_adapter
    ma.scrape_new_data()
    if ma.scrape_new_data():
        assert False
    else:
        assert True


@rpi
def test_adapter_scrape_history(get_adapter):
    ma = get_adapter
    if ma.scrape_history(2018, 1, 21, 2018, 3, 21):
        assert True
    else:
        assert False


@rpi
def test_adapter_frequency(get_adapter):
    ma = get_adapter
    if (ma.frequency() == 60 * 60 * 24 * 7):
        assert True
    else:
        assert False


@rpi
def test_adapter_set_date(get_adapter):
    passing = True
    ma = get_adapter
    if not ma.scrape_new_data():
        passing = False
    now_date = datetime.datetime.now(tz=pytz.timezone("America/Los_Angeles"))
    now_date.astimezone(tz=pytz.timezone('Mexico/General'))
    test_date = arrow.get(
        '00-' + now_date.strftime("%d/%m/%Y"),
        'HH-DD/MM/YYYY',
        locale='es',
        tzinfo='Mexico/General'
    ).datetime
    ma.set_last_scraped_date(test_date)
    if ma.scrape_new_data():
        assert passing
    else:
        assert False
