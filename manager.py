from operator import truediv
from adapters.nicaragua_adapter import NicaraguaAdapter
from adapters.el_salvador_adapter import ElSalvadorAdapter
from adapters.mexico_adapter import MexicoAdapter
from adapters.costa_rica_adapter import CostaRicaAdapter
from adapters.adapter_tasks import AdapterTypes
from forecast.forecast_tasks import ForecasterThread, ForecasterTypes
from cron import cron
from arrow import Arrow
from threading import Thread
from dotenv import load_dotenv
from forecast.forecast import str2datetime, get_doc
import os
import datetime
import pytz
import arrow
import pymongo
import time
import subprocess

load_dotenv()

# TO CHANGE START REF. go to forecast.forecast.py

# hours between checking the DB
db_checking_frequency = 8

# doc string format for mongodb
doc_format = "%d/%m/%Y"

# client
client = pymongo.MongoClient(os.getenv("MONGO_SRV"))

db_switcher = {
    AdapterTypes.El_Salvador: client.get_database('El_Salvador')['Historic'],
    AdapterTypes.Nicaragua: client.get_database('Nicaragua')['Historic'],
    AdapterTypes.Costa_Rica: client.get_database('Costa_Rica')['Historic'],
    AdapterTypes.Mexico: client.get_database('Mexico')['Historic'],
    ForecasterTypes.El_Salvador : client.get_database('El_Salvador')['Forecast'],
    ForecasterTypes.Nicaragua : client.get_database('Nicaragua')['Forecast'],
    ForecasterTypes.Costa_Rica : client.get_database('Costa_Rica')['Forecast'],
    ForecasterTypes.Mexico : client.get_database('Mexico')['Forecast']
}

tz_switcher = {
    AdapterTypes.El_Salvador: pytz.timezone('America/El_Salvador'),
    AdapterTypes.Nicaragua: pytz.timezone('America/Managua'),
    AdapterTypes.Costa_Rica: pytz.timezone('America/Costa_Rica'),
    AdapterTypes.Mexico: pytz.timezone('Mexico/General'),
    ForecasterTypes.El_Salvador : pytz.timezone('America/El_Salvador'),
    ForecasterTypes.Nicaragua : pytz.timezone('America/Managua'),
    ForecasterTypes.Costa_Rica : pytz.timezone('America/Costa_Rica'),
    ForecasterTypes.Mexico : pytz.timezone('Mexico/General')
}

main_jobs = []

def main():
    # set up queue and cron jobs
    upload_queue = list()
    jobs = cron(upload_queue, main_jobs)
    # Start uploader job
    Thread(target=uploader, kwargs={"cron_obj":jobs, "upload_queue":upload_queue}).start()
    Thread(target=check_db, kwargs={"cron_obj":jobs, "upload_queue":upload_queue}).start()

    # some jobs don't work unless on main thread???
    while True:
        if main_jobs:
            main_jobs.pop(0)()
        time.sleep(1)

def check_db(cron_obj: cron, upload_queue: list):
     while True:
        # look for missing entries and add them to queue
        # PROBLEM: Nicaragua still has broken data on
        # TODO manually sort out the week 27/8/2019
        # TODO Additionally out weeks of 30/05/2017,
        # 06/06/2017, 13/06/2017, 20/06/2017, 27/06/2017
        # 17/07/2018, 24/07/2018, 
        # for WHATEVER REASON, 29th and the 30th in 8/2019 have extra columns
        # this means Nic will continue to fail this week/days until we fix it
        print("checking DB...")
        for adapter in AdapterTypes:
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
                    print("Requesting data from ", adapter, ":")
                    print("\tfor week:", start.strftime(doc_format))
                    cron_obj.request_historical(adapter, start, end)
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
            print("Now sorting data from", data[0])
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
            print("uploading data for", data[0])
            # Forecasted data will constantly be updated, therefore needs to be overwritten
            upload_sorter(collection, marked_entries, overwrite=isinstance(data[0], ForecasterTypes))
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
    updated_entries = 0
    print("Checking", len(marked_entries), "entries for upload...")
    for _id, entry in marked_entries:
        doc_id = marked_entries[i]['_id']
        db_filter = {'_id': doc_id}
        # check if doc exists
        if db_collection.find_one(db_filter):
            # update if overwrite, check for entry and add missing
            db_entry = db_collection.find({'_id': doc_id, entry:{'$exists':'true'}})
            if db_entry.retrieved:
                # entry exists, only update if overwrite
                if overwrite:
                    db_collection.update_one(db_filter, {'$set': {entry: marked_entries[i][entry]}})
                    updated_entries += 1
            else:
                db_collection.update_one(db_filter, {'$set': {entry: marked_entries[i][entry]}})
                updated_entries += 1
        else:
            db_collection.insert_one(marked_entries[i])
            updated_entries += 1
        i += 1
    print("Updated", updated_entries, "entries")

# Everything w/ demo is an old example of
# how we pushed historical data to our DB

def es_adapter_demo():
    db = client.get_database('El_Salvador')['Historic']
    el_salvador = ElSalvadorAdapter()
    start = datetime.date(year=2016, month=12, day=27)
    delta = datetime.timedelta(days=6)

    for week in range(105):
        end = start + delta
        #dd/mm/yyyy
        doc_id = start.strftime("%d/%m/%Y")
        print("Current week", week, ":")
        print("\t", doc_id)
        data = el_salvador.scrape_history(start.year, start.month, start.day, end.year, end.month, end.day)
        data['_id'] = doc_id
        db.insert_one(data)
        start = end + datetime.timedelta(days=1)
        
    print("Completed to:")
    print("\t", start.strftime("%d/%m/%Y"))
    
def mexico_adapter_demo():
    db = client.get_database('Mexico')['Historic']
    ma = MexicoAdapter()
    start = datetime.date(year=2016, month=12, day=27)
    delta = datetime.timedelta(days=6)
    for week in range(105):
        end = start + delta
        #dd/mm/yyyy
        doc_id = start.strftime("%d/%m/%Y")
        print("Current week", week, ":")
        print("\t", doc_id)
        data = ma.scrape_history(start.year, start.month, start.day, end.year, end.month, end.day)
        data['_id'] = doc_id
        print_data(data)
        db.insert_one(data)
        start = end + datetime.timedelta(days=1)

    print("Completed to:")
    print("\t", start.strftime("%d/%m/%Y"))

def nic_adapter_demo():
    # TODO manually sort out the week 27/8/2019
    # TODO Additionally out weeks of 30/05/2017,
    # 06/06/2017, 13/06/2017, 20/06/2017, 27/06/2017
    # 17/07/2018, 24/07/2018, 
    # for WHATEVER REASON, 29th and the 30th in 8/2019 have extra columns
    db = client.get_database('Nicaragua')['Historic']
    na = NicaraguaAdapter()
    start = datetime.date(year=2018, month=12, day=18)
    delta = datetime.timedelta(days=6)
    for week in range(105):
        end = start + delta
        #dd/mm/yyyy
        doc_id = start.strftime("%d/%m/%Y")
        print("Current week", week, ":")
        print("\t", doc_id)
        data = na.scrape_history(start.year, start.month, start.day, end.year, end.month, end.day)
        data['_id'] = doc_id
        print_data(data)
        db.insert_one(data)
        start = end + datetime.timedelta(days=1)

    print("Completed to:")
    print("\t", start.strftime("%d/%m/%Y"))

def cr_adapter_demo():
    db = client.get_database('Costa_Rica')['Historic']
    cr = CostaRicaAdapter()
    start = datetime.date(year=2016, month=12, day=27)
    delta = datetime.timedelta(days=6)
    failed_weeks = []
    for week in range(105):
        end = start + delta
        #dd/mm/yyyy
        for i in range(0, 5):
            try:    
                doc_id = start.strftime("%d/%m/%Y")
                if i > 0 and doc_id not in failed_weeks:
                    failed_weeks.append(doc_id)
                print("Current week", week, ":")
                print("\t", doc_id)
                data = cr.scrape_history(start.year, start.month, start.day, end.year, end.month, end.day)
                data['_id'] = doc_id
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
    main()
