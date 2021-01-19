from scrapers.el_salvador import ElSalvador
import pytest


@pytest.fixture(scope='module', autouse=True)
def get_driver():
    print("init el salvador testing")
    es = ElSalvador()
    yield es


def test_driver_crash():
    try:
        get_driver
        assert True
    except Exception as e:
        print(e)
        assert False


def test_multiple_queries(get_driver):
    es = get_driver
    try:
        es.date(day=10, month=10, year=2020)
        es.date(day=8, month=10, year=2020)
        assert True
    except Exception as e:
        print(e)
        assert False


def test_output_list(get_driver):
    es = get_driver
    data = es.date(day=10, month=10, year=2020)
    assert isinstance(data, list)


def test_output_value(get_driver):
    es = get_driver
    data = es.date(day=10, month=10, year=2020)
    assert isinstance(data[0]['value'], float)


def test_output_dict_size(get_driver):
    es = get_driver
    data = es.date(day=10, month=10, year=2020)
    assert 4 == len(data[0])


def test_output_tz_aware(get_driver):
    es = get_driver
    data = es.date(day=10, month=10, year=2020)
    assert data[0]['ts'].tzinfo is not None


def test_error_future(get_driver):
    es = get_driver
    try:
        es.date(day=10, month=10, year=2080)
        assert False
    except Exception as e:
        print(e)
        assert True


def test_error_illegal_date(get_driver):
    es = get_driver
    try:
        es.date(day=40, month=10, year=2040)
        assert False
    except Exception as e:
        print(e)
        assert True


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
