from scrapers.mexico import Mexico
import pytest
import platform
import sys

rpi = pytest.mark.skipif(
    (platform.system() == "Linux" and sys.version_info == (3, 6, 6)),
    reason="Raspberry pi can't run mexico for some reason"
)


@pytest.fixture(scope='module', autouse=True)
def get_driver():
    print("init Mexico testing")
    mexico = Mexico()
    yield mexico


@rpi
def test_driver_crash():
    try:
        Mexico()
        assert True
    except Exception as e:
        print(e)
        assert False


@rpi
def test_multiple_queries(get_driver):
    mexico = get_driver
    try:
        mexico.scrape_month(month=8, year=2020)
        mexico.scrape_month(month=7, year=2020)
        assert True
    except Exception as e:
        print(e)
        assert False


@rpi
def test_output_list(get_driver):
    mexico = get_driver
    data = mexico.scrape_month(month=3, year=2020)
    assert isinstance(data, list)


@rpi
def test_output_value(get_driver):
    mexico = get_driver
    data = mexico.scrape_month(month=6, year=2019)
    assert isinstance(data[0]['value'], float)


@rpi
def test_output_dict_size(get_driver):
    mexico = get_driver
    data = mexico.scrape_month(month=11, year=2019)
    assert 4 == len(data[0])


@rpi
def test_output_tz_aware(get_driver):
    mexico = get_driver
    data = mexico.scrape_month(month=5, year=2020)
    assert data[0]['ts'].tzinfo is not None


@rpi
def test_error_future(get_driver):
    mexico = get_driver
    try:
        mexico.scrape_month(month=10, year=2025)
        assert False
    except Exception as e:
        print(e)
        assert True


@rpi
def test_error_illegal_date(get_driver):
    mexico = get_driver
    try:
        mexico.scrape_month(month=15, year=2020)
        assert False
    except Exception as e:
        print(e)
        assert True


@rpi
def test_error_no_file(get_driver):
    mexico = get_driver
    try:
        mexico.scrape_month(month=12, year=2020)
        assert False
    except Exception as e:
        print(e)
        assert True


'''
We don't need this test at the moment because the
method will actually succeed independent of how the
dates are given. This is entirely dependent on the
behavior of the host's website and may be subject
to change in the future.

def test_error_backwards_dates(get_driver):
    mexico = get_driver
    try:
        mexico.scrape_month_range(
            initial_month=10, initial_year=2020,
            final_month=10, final_year=2020)
        assert False
    except Exception as e:
        print(e)
        assert True
'''
