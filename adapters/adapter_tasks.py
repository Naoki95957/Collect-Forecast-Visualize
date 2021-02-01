from adapters.scraper_adapter import ScraperAdapter
from queue import Queue
from datetime import datetime
import time
import threading


class AdapterThread(threading.Thread):
    '''
    Automatically handle tasks for simultanious scraping

    Make use of multi-threading

    '''
    __kill = False
    __running = False

    # in seconds
    __watchdog_time = 5

    def __init__(self, adapter: ScraperAdapter, upload_data: Queue):
        super(AdapterThread, self).__init__()
        if not isinstance(adapter, ScraperAdapter):
            raise TypeError(
                "Expected a Scraper Adapter. Recieved a %s",
                type(adapter))
        self.adapter = adapter
        self.upload_queue = upload_data

    def get_intermittent_data(self, startdate: datetime, enddate: datetime):
        return self.adapter.scrape_history(
            start_day=startdate.day, start_month=startdate.month,
            start_year=startdate.year, end_day=enddate.day,
            end_month=enddate.month, end_year=enddate.year)

    def set_todays_start_time(self, time: datetime):
        '''
        This will set the reference point for the adapter landing page
        '''
        if not time.tzinfo:
            raise TypeError("datetime object must be tz aware")
        self.adapter.set_last_scraped_date(time)

    def attempt_to_queue_todays_data(self):
        '''
        This will attempt to get todays data
        '''
        data = self.adapter.scrape_new_data()
        if data:
            self.upload_queue.put(data)

    def is_alive(self):
        return self.__running

    def start(self):
        return super().start()

    def run(self):
        '''
        Runs the adapter for realtime data gathering

        Sleeps a majority of its time

        This also has a fake watchdog so that we can kill the process
        in a reasonable amount of time
        '''
        try:
            self.__running = True
            freq = self.adapter.frequency()
            # equals freq so it scrapes once before waiting
            total_sleep = freq
            while not self.__kill:
                if total_sleep < freq:
                    total_sleep += self.__watchdog_time
                    time.sleep(self.__watchdog_time)
                else:
                    total_sleep = 0
                    self.attempt_to_queue_todays_data()
        except Exception as e:
            print(e)
        self.__running = False
        return super().run()

    def join(self, timeout=30):
        self.__kill = True
        super().join(timeout)

    def __del__(self):
        self.join()
