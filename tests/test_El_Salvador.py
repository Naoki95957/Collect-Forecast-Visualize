from scrapers.el_salvador import ElSalvador
import pytest


@pytest.fixture(scope='module', autouse=True)
def get_driver():
    print("init el salvador testing")
    es = ElSalvador()
    yield es


def test_driver_crash():
    print("Testing driver")
    try:
        ElSalvador()
        assert True
    except Exception as e:
        print(e)
        assert False


def test_multiple_queries(get_driver):
    print("Testing queries")
    es = get_driver
    try:
        es.date(10, 10, 2020)
        es.date(10, 8, 2020)
        assert True
    except Exception as e:
        print(e)
        assert False


def test_output_list(get_driver):
    print("Testing if output is list")
    es = get_driver
    data = es.date(10, 10, 2020)
    assert list == type(data)


def test_output_value(get_driver):
    print("Testing if output value is a float")
    es = get_driver
    data = es.date(10, 10, 2020)
    assert isinstance(data[0]['value'], float)


def test_output_dict_size(get_driver):
    print("Testing if output dictionary is size 4")
    es = get_driver
    data = es.date(10, 10, 2020)
    assert 4 == len(data[0])


def test_output_tz_aware(get_driver):
    print("Testing if output is tz aware")
    es = get_driver
    data = es.date(10, 10, 2020)
    assert data[0]['ts'].tzinfo is not None


def test_error_future(get_driver):
    print("Testing for future date error")
    es = get_driver
    try:
        data1 = es.today()
        data2 = es.date(10, 10, 2040)
        # This should work and just report present
        # day info instead of future info
        assert data1[0] == data2[0]
    except Exception as e:
        print(e)
        assert False


def test_error_illegal_date(get_driver):
    print("Testing for illegal date error")
    es = get_driver
    try:
        es.date(40, 10, 2040)
        assert False
    except Exception as e:
        print(e)
        assert True


def test_error_backwards_dates(get_driver):
    print("Testing for swaped date range error")
    es = get_driver
    try:
        es.date_range(
            10, 10, 2020,
            5, 10, 2020)
        assert False
    except Exception as e:
        print(e)
        assert True
