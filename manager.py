from adapters.el_salvador_adaptor import ElSalvadorAdapter
import pymongo

# this would be the interface between the DB and python
# adapters would be the interface between THIS and the scrapers

# this class is like main that runs all the strategy or adaptor pattern

# connection to the mongodb here
# use other classes

client = pymongo.MongoClient(
    "mongodb+srv://BCWATT:WattTime2021" +
    "@cluster0.tbh2o.mongodb.net/" +
    "WattTime?retryWrites=true&w=majority")


db = client.get_database('WattTime')


def es_adapter_demo():
    esa = ElSalvadorAdapter()
    # expectation is that 1 might have data
    print(esa.scrape_new_data())
    # and that the rest will not due to not waiting
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
