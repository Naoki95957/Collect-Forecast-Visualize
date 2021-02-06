from adapters.nicaragua_adapter import NicaraguaAdapter
from adapters.el_salvador_adapter import ElSalvadorAdapter
from adapters.mexico_adapter import MexicoAdapter
from adapters.costa_rica_adapter import CostaRicaAdapter
from adapters.scraper_adapter import ScraperAdapter
from adapters.adapter_tasks import adapter_types
from cron import cron
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

db_switcher = {
    adapter_types.El_Salvador: client.get_database('El_Salvador')['Historic'],
    adapter_types.Nicaragua: client.get_database('Nicaragua')['Historic'],
    adapter_types.Costa_Rica: client.get_database('Costa_Rica')['Historic'],
    adapter_types.Mexico: client.get_database('Mexico')['Historic']
}

def main():
    # TODO set up cron
    # TODO check each db for missing data in x intervals
    # TODO check queue for data to upload


# Everything w/ demo is an old example of
# how we pushed historical data to our DB

def es_adapter_demo():
    db = client.get_database('El_Salvador')['Historic']
    el_salvador = ElSalvadorAdapter()
    start = datetime.date(2019, 1, 1)
    delta = datetime.timedelta(days=6)
    
    for week in range(106):
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
    db = client.get_database('Mexico')['Historic']
    ma = MexicoAdapter()
    start = datetime.date(2019, 1, 1)
    delta = datetime.timedelta(days=6)
    for week in range(106):
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

def nic_adapter_demo():
    # TODO manually sort out the week 27/8/2019
    # for WHATEVER REASON, 29th and the 30th in 8/2019 have extra columns
    db = client.get_database('Nicaragua')['Historic']
    na = NicaraguaAdapter()
    start = datetime.date(2019, 1, 1)
    delta = datetime.timedelta(days=6)
    for week in range(106):
        end = start + delta
        #dd/mm/yyyy
        id = start.strftime("%d/%m/%Y")
        print("Current:")
        print("\t", id)
        data = na.scrape_history(start.year, start.month, start.day, end.year, end.month, end.day)
        data['_id'] = id
        print_data(data)
        db.insert_one(data)
        start = end + datetime.timedelta(days=1)

    print("Completed to:")
    print("\t", start.strftime("%d/%m/%Y"))

def cr_adapter_demo():
    db = client.get_database('Costa_Rica')['Historic']
    cr = CostaRicaAdapter()
    start = datetime.date(2019, 1, 1)
    delta = datetime.timedelta(days=6)
    failed_weeks = []
    for week in range(106):
        end = start + delta
        #dd/mm/yyyy
        for i in range(0, 5):
            try:
                id = start.strftime("%d/%m/%Y")
                if i > 0 and id not in failed_weeks:
                    failed_weeks.append(id)
                print("Current:")
                print("\t", id)
                data = cr.scrape_history(start.year, start.month, start.day, end.year, end.month, end.day)
                data['_id'] = id
                print_data(data)
                db.insert_one(data)
                break
            except Exception as e:
                print(e)
        start = end + datetime.timedelta(days=1)

    print("Completed to:")
    print("\t", start.strftime("%d/%m/%Y"))
    print("Double check these weeks:")
    for entry in failed_weeks:
        print('\t', entry)

def print_data(data):
    for k in data.keys():
        print(k)
        # for v in data[k]:
        #     print('\t', v)

if __name__ == "__main__":
    cr_adapter_demo()
