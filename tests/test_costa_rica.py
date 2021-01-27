from scrapers.costa_rica import CostaRica
import pytest


@pytest.fixture(scope='module', autouse=True)
def get_driver():
    print("Initalize Costa Rica testing")
    costa_rica = CostaRica()
    yield costa_rica


# T1
def test_driver_crash():
    try:
        get_driver
        assert True
    except Exception as e:
        print(e)
        assert False


# T2
def test_multiple_queries(get_driver):
    costa_rica = get_driver
    try:
        costa_rica.date(2020, 9, 30)
        costa_rica.date(2020, 9, 24)
        assert True
    except Exception as e:
        print(e)
        assert False


# T3
def test_date_range(get_driver):
    costa_rica = get_driver
    try:
        costa_rica.date_range(2020, 10, 30, 2020, 11, 1)
        assert True
    except Exception as e:
        print(e)
        assert False


# T4
def test_output_type_is_a_list(get_driver):
    costa_rica = get_driver
    data = costa_rica.date(2020, 10, 10)
    assert isinstance(data, list)


# T5
def test_output_value_is_a_float(get_driver):
    costa_rica = get_driver
    data = costa_rica.date(2020, 10, 10)
    assert isinstance(data[0]['value'], float)


# T6
def test_output_tz_aware(get_driver):
    costa_rica = get_driver
    data = costa_rica.date(2020, 10, 10)
    assert data[0]['ts'].tzinfo is not None
