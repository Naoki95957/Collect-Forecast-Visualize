from datetime import datetime
from adapters.el_salvador_adapter import ElSalvadorAdapter
from adapters.mexico_adapter import MexicoAdapter
from adapters.scraper_adapter import ScraperAdapter
import datetime
# import pytz
import arrow
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


db = client.get_database('El_Salvador')['Historic']


def es_adapter_demo():    
    el_salvador = ElSalvadorAdapter()
    start = datetime.date(2019, 1, 1)
    delta = datetime.timedelta(days=6)
    
    for week in range(105):
        end = start + delta
        #dd/mm/yyyy
        id = start.strftime("%d/%m/%Y")
        print("Current:")
        print("\t", id)
        data = el_salvador.scrape_history(start.year, start.month, start.day, end.year, end.month, end.day)
        data['_id'] = id
        db.insert_one(data)
        start = end + datetime.timedelta(days=1)
        
    print("Completed to:")
    print("\t", start.strftime("%d/%m/%Y"))
    
def mexico_adapter_demo():    
    ma = MexicoAdapter()
    start = datetime.date(2019, 12, 31)
    delta = datetime.timedelta(days=6)
    
    for week in range(53):
        end = start + delta
        #dd/mm/yyyy
        id = start.strftime("%d/%m/%Y")
        print("Current:")
        print("\t", id)
        data = ma.scrape_history(start.year, start.month, start.day, end.year, end.month, end.day)
        data['_id'] = id
        print_data(data)
        db.insert_one(data)
        start = end + datetime.timedelta(days=1)
        
    print("Completed to:")
    print("\t", start.strftime("%d/%m/%Y"))
    
def print_data(data):
    for k in data.keys():
        print(k)
        # for v in data[k]:
        #     print('\t', v)

if __name__ == "__main__":
    mexico_adapter_demo()
