from adapters.nicaragua_adapter import NicaraguaAdapter
from adapters.el_salvador_adapter import ElSalvadorAdapter
from adapters.mexico_adapter import MexicoAdapter
from adapters.costa_rica_adapter import CostaRicaAdapter
from adapters.scraper_adapter import ScraperAdapter
from adapters.adapter_tasks import adapter_types
from cron import cron
from queue import Queue
from arrow import Arrow
from threading import Thread
import datetime
import pytz
import arrow
import pymongo
import time

# this would be the interface between the DB and python
# adapters would be the interface between THIS and the scrapers

# this class is like main that runs all the strategy or adaptor pattern

# connection to the mongodb here
# use other classes

# hours between checking the DB
db_checking_frequency = 12

# the basis to check the db
doc_start_time = {
    'year': 2019,
    'month': 1, 
    'day': 1
}

# doc string format for mongodb
doc_format = "%d/%m/%Y"

# client
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

name_switcher = {
    adapter_types.El_Salvador: 'El_Salvador',
    adapter_types.Nicaragua: 'America/Managua',
    adapter_types.Costa_Rica: 'America/Costa_Rica',
    adapter_types.Mexico: 'Mexico/General'
}

tz_switcher = {
    adapter_types.El_Salvador: pytz.timezone('America/El_Salvador'),
    adapter_types.Nicaragua: pytz.timezone('America/Managua'),
    adapter_types.Costa_Rica: pytz.timezone('America/Costa_Rica'),
    adapter_types.Mexico: pytz.timezone('Mexico/General')
}

def main():
    # set up queue and cron jobs
    upload_queue = list()
    jobs = cron(upload_queue)
    # Start uploader job
    Thread(target=uploader, kwargs={"cron_obj":jobs, "upload_queue":upload_queue}).start()

    # check db until we crash
    while True:
        # look for missing entries and add them to queue
        # PROBLEM: Nicaragua still has broken data on
        # the 29th and the 30th of 8/2019 due to extra columns
        print("checking DB...")
        for adapter in adapter_types:
            db = db_switcher[adapter]
            now = datetime.datetime.now() - datetime.timedelta(days=1)
            start = datetime.datetime(2019, 1, 1)
            delta = datetime.timedelta(days=6)
            while start < now:
                end = start + delta
                # check doc
                # 169 entries per doc (includes ID)
                query = db.find_one({'_id': start.strftime(doc_format)})
                if (not query) or (len(query) != 169):
                    # This will get pushed into the queue
                    print("Requesting data from ", name_switcher[adapter], ":")
                    print("\tfor week:", start.strftime(doc_format))
                    jobs.request_historical(adapter, start, end)
                # iterate
                start = end + datetime.timedelta(days=1)
        print("Done checking db. Sleeping now...")
        time.sleep(60 * 60 * db_checking_frequency)

def uploader(cron_obj: cron, upload_queue: list):
    '''
    This will run in a loop and check the queue for data to load
    '''
    print("Uploader started")
    while cron_obj.cron_alive:
        if len(upload_queue) > 0:
            data = upload_queue.pop(0)
            print("Now sorting data from", name_switcher[data[0]])
            print(len(upload_queue), "uploads in queue")
            collection = db_switcher[data[0]]
            entries = data[1]
            marked_entries = [
                {
                    '_id': get_doc(str2datetime(entry, tz_switcher[data[0]])),
                    entry: entries[entry]
                }
                for entry in entries.keys()
            ]
            print("uploading data for", name_switcher[data[0]])
            upload_sorter(collection, marked_entries)
        time.sleep(1)
    print("cron died! Death on:", datetime.datetime.now())

def upload_sorter(db_collection, marked_entries, overwrite=False):
    '''
    Helper function that uploads data one at a time:

    It checks if entry exists, and if it does, it skips it

    Otherwise it appends it to the doc

    overwrite will set entries regardless if it exists
    '''
    i = 0
    for _id, entry in marked_entries:
        doc_id = marked_entries[i]['_id']
        db_filter = {'_id': doc_id}
        # check if doc exists
        if db_collection.find_one(db_filter):
            # update if overwrite, check for entry and add missing
            db_entry = db_collection.find({'_id': doc_id, entry:{'$exists':'true'}})
            print(db_entry)
            if db_entry.retrieved:
                # entry exists, only update if overwrite
                if overwrite:
                    db_collection.update_one(db_filter, {'$set': {entry: marked_entries[i][entry]}})
            else:
                db_collection.update_one(db_filter, {'$set': {entry: marked_entries[i][entry]}})
        else:
            db_collection.insert_one(marked_entries[i])
        i += 1

def str2datetime(string: str, tzinfo=None) -> datetime.datetime:
    '''
    This str to datetime is for the hourly format we're using
    '''
    return arrow.get(string, "HH-DD/MM/YYYY", tzinfo=tzinfo)

def get_doc(date: datetime.datetime) -> str:
    '''
    Helper function to get the doc for x/y/z date

    returns the str that should be the ID of the doc
    '''
    start = datetime.datetime(
        doc_start_time['year'],
        doc_start_time['month'],
        doc_start_time['day']
    )
    # yes this is a bit redundant, but I wanna have JUST days, not hours
    end = datetime.datetime(date.year, date.month, date.day)
    diff = (end - start).days % 7
    week = end - datetime.timedelta(days=diff)
    week_date = Arrow.strptime(str(week), "%Y-%m-%d %H:%M:%S").datetime
    return week_date.strftime("%d/%m/%Y")

# Everything w/ demo is an old example of
# how we pushed historical data to our DB

def es_adapter_demo():
    db = client.get_database('El_Salvador')['Historic']
    el_salvador = ElSalvadorAdapter()
    start = datetime.date(2019, 12, 24)
    delta = datetime.timedelta(days=6)
    
    for week in range(106 - 51):
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

def test():
    db = client.get_database('El_Salvador')['Historic']
    start = datetime.date(2019, 1, 1)
    print(len(db.find_one({'_id': start.strftime(doc_format)})))

def print_data(data):
    for k in data.keys():
        print(k)
        # for v in data[k]:
        #     print('\t', v)

if __name__ == "__main__":
    main()
