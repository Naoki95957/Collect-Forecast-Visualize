from scrapers.costa_rica import CostaRica
from scrapers.nicaragua import Nicaragua
from scrapers.el_salvador import ElSalvador


def test_general_El_Salvador():
    try:
        es = ElSalvador()
        data = es.today()
        for datapoint in data:
            print(datapoint)
        assert True
    except Exception:
        assert False

def test_general_costa_rica():
    try:
        cr = CostaRica()
        data = cr.today()
        for datapoint in data:
            print(datapoint)
        assert True
    except Exception:
        assert False

def test_general_Nicaragua():
    try:
        nic = Nicaragua()
        data = nic.yesterday()
        for datapoint in data:
            print(datapoint)
        assert True
    except Exception:
        assert False
