from scrapers.nicaragua import Nicaragua
import pytest


@pytest.fixture(scope='module', autouse=True)
def get_driver():
    print("Initalize Nicaragua testting")
    nicaragua = Nicaragua()
    yield nicaragua


# T1
def test_nicaragua_driver_crash():
    try:
        get_driver
        assert True
    except Exception as e:
        print(e)
        assert False


# T2
def test_nicaragua_multiple_queries(get_driver):
    nicaragua = get_driver
    try:
        nicaragua.date(2020, 9, 30)
        nicaragua.date(2020, 9, 24)
        assert True
    except Exception as e:
        print(e)
        assert False


# T3
def test_nicaragua_date_range(get_driver):
    nicaragua = get_driver
    try:
        nicaragua.date_range(2020, 10, 30, 2020, 11, 1)
        assert True
    except Exception as e:
        print(e)
        assert False


# T4
def test_nicaragua_output_type_is_a_list(get_driver):
    nicaragua = get_driver
    data = nicaragua.date(2020, 10, 10)
    assert isinstance(data, list)


# T5
def test_nicaragua_output_value_is_a_float(get_driver):
    nicaragua = get_driver
    data = nicaragua.date(2020, 10, 10)
    assert isinstance(data[0]['value'], float)


# T6
def test_nicaragua_output_tz_aware(get_driver):
    nicaragua = get_driver
    data = nicaragua.date(2020, 10, 10)
    assert data[0]['ts'].tzinfo is not None


# T7
def test_nicaragua_output_dict_size(get_driver):
    nicaragua = get_driver
    data = nicaragua.date(day=10, month=10, year=2020)
    assert 4 == len(data[0])


# T8
def test_nicaragua_error_illegal_date(get_driver):
    nicaragua = get_driver
    try:
        nicaragua.date(day=40, month=10, year=2040)
        assert False
    except Exception as e:
        print(e)
        assert True


# T9
def test_nicaragua_error_backwards_dates(get_driver):
    nicaragua = get_driver
    try:
        nicaragua.date_range(
            start_day=10, start_month=10, start_year=2020,
            end_day=5, end_month=10, end_year=2020)
        assert False
    except Exception as e:
        print(e)
        assert True
