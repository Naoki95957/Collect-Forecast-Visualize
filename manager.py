from adapters.el_salvador_adaptor import ElSalvadorAdapter
from adapters.scraper_adapter import ScraperAdapter
# import datetime
# import pytz
# import arrow
# import pymongo

# this would be the interface between the DB and python
# adapters would be the interface between THIS and the scrapers

# this class is like main that runs all the strategy or adaptor pattern

# connection to the mongodb here
# use other classes

# client = pymongo.MongoClient(
#     "mongodb+srv://BCWATT:WattTime2021" +
#     "@cluster0.tbh2o.mongodb.net/" +
#     "WattTime?retryWrites=true&w=majority")


# db = client.get_database('WattTime')


def es_adapter_demo():
    esa = ElSalvadorAdapter()
    print(isinstance(esa, ScraperAdapter))
    # expectation is that 1 might have data
    print(esa.scrape_new_data())
    # and that the rest will not due to not waiting
    print(esa.scrape_new_data())
    # test_date = arrow.get(
    #     '02-26/01/2021',
    #     'HH-DD/MM/YYYY',
    #     locale='es',
    #     tzinfo=pytz.timezone('America/El_Salvador')).datetime
    # esa.set_last_scraped_date(test_date)
    print(esa.scrape_new_data())
    print(esa.scrape_new_data())
    print("flush")
    data = esa.scrape_history(2021, 1, 18, 2021, 1, 19)
    for i in data:
        print(i)
        for j in data[i]:
            print('\t', j)


if __name__ == "__main__":
    es_adapter_demo()
