from scrapers.costa_rica import CostaRica


def general_test_costa_rica():
    try:
        cr = CostaRica()
        data = cr.search_date()
        for datapoint in data:
            print(datapoint)
        assert True
    except Exception:
        assert False