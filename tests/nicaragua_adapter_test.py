from adapters.nicaragua_adapter import NicaraguaAdapter
from adapters.scraper_adapter import ScraperAdapter
import pytest


@pytest.fixture(scope='module', autouse=True)
def get_adapter():
    print("testing Nicaragua")
    na = NicaraguaAdapter()
    yield na


def reset_adapter(adapter: NicaraguaAdapter):
    adapter.set_last_scraped_date(None)


def test_adapter_crash():
    try:
        get_adapter
        assert True
    except Exception as e:
        print(e)
        assert False


def test_adapter_conversion(get_adapter):
    reset_adapter(get_adapter)
    na = get_adapter
    if isinstance(na, ScraperAdapter):
        assert True
    else:
        assert False


def test_adapter_scrape_too_fast(get_adapter):
    reset_adapter(get_adapter)
    na = get_adapter
    na.scrape_new_data()
    if na.scrape_new_data():
        assert False
    else:
        assert True


def test_adapter_scrape_history(get_adapter):
    reset_adapter(get_adapter)
    na = get_adapter
    if na.scrape_history(
        start_year=2021, start_month=1,
        start_day=21, end_year=2021,
        end_month=1, end_day=22):
        assert True
    else:
        assert False


def test_adapter_frequency(get_adapter):
    reset_adapter(get_adapter)
    na = get_adapter
    if (na.frequency() == 60 * 60 * 24):
        assert True
    else:
        assert False
