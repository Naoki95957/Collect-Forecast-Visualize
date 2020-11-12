from scrapers.costa_rica import CostaRica
from scrapers.nicaragua import Nicaragua
from scrapers.el_salvador import ElSalvador
from scrapers.el_salvador_legacy import ElSalvador as ESL


def test_general_El_Salvador():
    try:
        es = ElSalvador()
        data = es.scrape_data()
        for datapoint in data:
            print(datapoint)
        assert True
    except Exception:
        assert False


def test_general_ESL():
    try:
        es = ESL()
        data = es.scrape_data()
        for datapoint in data:
            print(datapoint)
        assert True
    except Exception:
        assert False


def test_general_costa_rica():
    try:
        cr = CostaRica()
        data = cr.search_date()
        for datapoint in data:
            print(datapoint)
        assert True
    except Exception:
        assert False


def test_general_Nicaragua():
    try:
        nic = Nicaragua()
        data = nic.search_date()
        for datapoint in data:
            print(datapoint)
        assert True
    except Exception:
        assert False
