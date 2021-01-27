from adapters.nicaragua_adapter import NicaraguaAdapter
from adapters.scraper_adapter import ScraperAdapter
import pytest


@pytest.fixture(scope='module', autouse=True)
def get_adapter():
    print("testing Nicaragua")
    na = NicaraguaAdapter()
    yield na


# T1
def test_adapter_crash():
    try:
        get_adapter
        assert True
    except Exception as e:
        print(e)
        assert False


# T2
def test_adapter_conversion():
    na = NicaraguaAdapter()
    if isinstance(na, ScraperAdapter):
        assert True
    else:
        assert False


# T3
def test_adapter_scrape_too_fast():
    na = NicaraguaAdapter()
    na.scrape_new_data()
    if na.scrape_new_data():
        assert False
    else:
        assert True


# T4
def test_adapter_scrape_history(get_adapter):
    na = get_adapter
    if na.scrape_history(
        start_year=2021, start_month=1,
        start_day=21, end_year=2021,
        end_month=3, end_day=22):
        assert True
    else:
        assert False


# T5
def test_adapter_frequency(get_adapter):
    na = get_adapter
    if (na.frequency() == str(60 * 60 * 24)):
        assert True
    else:
        assert False
