from adapters.el_salvador_adaptor import ElSalvadorAdapter
from adapters.scraper_adapter import ScraperAdapter
import pytest
import pytz
import arrow
import datetime


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


def test_adapter_inheritance(get_adapter):
    esa = get_adapter
    esa.frequency()
    if isinstance(esa, ScraperAdapter):
        assert True
    else:
        assert False


def test_adapter_scrape_too_fast(get_adapter):
    esa = get_adapter
    esa.scrape_new_data()
    if esa.scrape_new_data():
        assert False
    else:
        assert True


def test_adapter_scrape_history(get_adapter):
    esa = get_adapter
    if esa.scrape_history(
        start_year=2021, start_month=1,
        start_day=21, end_year=2021,
        end_month=3, end_day=22):
        assert True
    else:
        assert False


def test_adapter_frequency(get_adapter):
    esa = get_adapter
    if (esa.frequency() == 60 * 60 * 24 * 7):
        assert True
    else:
        assert False


def test_adapter_set_date(get_adapter):
    passing = True
    esa = get_adapter
    if not esa.scrape_new_data():
        passing = False
    now_date = datetime.datetime.now(tz=pytz.timezone("America/Los_Angeles"))
    now_date.astimezone(tz=pytz.timezone('America/El_Salvador'))
    test_date = arrow.get(
        '00-' + now_date.strftime("%d/%m/%Y"),
        'HH-DD/MM/YYYY',
        locale='es',
        tzinfo='America/El_Salvador'
    ).datetime
    esa.set_last_scraped_date(test_date)
    if esa.scrape_new_data():
        assert passing
    else:
        assert False
