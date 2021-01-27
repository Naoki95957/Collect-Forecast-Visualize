from adapters.costa_rica_adapter import CostaRicaAdapter
from adapters.scraper_adapter import ScraperAdapter
import pytest
import platform


rpi = pytest.mark.skipif((
    platform.architecture()[0] == "32bit"),
    reason="Raspberry pi can't run mexico for some reason"
)


@pytest.fixture(scope='module', autouse=True)
def get_adapter():
    print("testing costa rica")
    ca = CostaRicaAdapter()
    yield ca


def reset_adapter(adapter: CostaRicaAdapter):
    adapter.set_last_scraped_date(None)


# T1
def test_adapter_crash():
    try:
        get_adapter
        assert True
    except Exception as e:
        print(e)
        assert False


# T2
def test_adapter_conversion(get_adapter):
    reset_adapter(get_adapter)
    ca = get_adapter
    if isinstance(ca, ScraperAdapter):
        assert True
    else:
        assert False

# T3
@rpi
def test_adapter_scrape_too_fast(get_adapter):
    reset_adapter(get_adapter)
    ca = get_adapter
    ca.scrape_new_data()
    if ca.scrape_new_data():
        assert False
    else:
        assert True


# T4
def test_adapter_scrape_history(get_adapter):
    reset_adapter(get_adapter)
    ca = get_adapter
    if ca.scrape_history(
            start_year=2021, start_month=1,
            start_day=21, end_year=2021,
            end_month=1, end_day=22):
        assert True
    else:
        assert False


# T5
def test_adapter_frequency(get_adapter):
    reset_adapter(get_adapter)
    ca = get_adapter
    if (ca.frequency() == 60 * 60 * 24):
        assert True
    else:
        assert False
