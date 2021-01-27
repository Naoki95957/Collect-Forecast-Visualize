from scrapers.el_salvador import ElSalvador
import pytest


@pytest.fixture(scope='module', autouse=True)
def get_driver():
    print("init el salvador testing")
    es = ElSalvador()
    yield es


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
    es = get_driver
    try:
        es.date(day=10, month=10, year=2020)
        es.date(day=8, month=10, year=2020)
        assert True
    except Exception as e:
        print(e)
        assert False


# T3
def test_output_list(get_driver):
    es = get_driver
    data = es.date(day=10, month=10, year=2020)
    assert isinstance(data, list)


# T4
def test_output_value(get_driver):
    es = get_driver
    data = es.date(day=10, month=10, year=2020)
    assert isinstance(data[0]['value'], float)


# T5
def test_output_dict_size(get_driver):
    es = get_driver
    data = es.date(day=10, month=10, year=2020)
    assert 4 == len(data[0])


# T6
def test_output_tz_aware(get_driver):
    es = get_driver
    data = es.date(day=10, month=10, year=2020)
    assert data[0]['ts'].tzinfo is not None


# T7
def test_error_future(get_driver):
    es = get_driver
    try:
        es.date(day=10, month=10, year=2080)
        assert False
    except Exception as e:
        print(e)
        assert True


# T8
def test_error_illegal_date(get_driver):
    es = get_driver
    try:
        es.date(day=40, month=10, year=2040)
        assert False
    except Exception as e:
        print(e)
        assert True


# T9
def test_error_backwards_dates(get_driver):
    es = get_driver
    try:
        es.date_range(
            start_day=10, start_month=10, start_year=2020,
            end_day=5, end_month=10, end_year=2020)
        assert False
    except Exception as e:
        print(e)
        assert True
