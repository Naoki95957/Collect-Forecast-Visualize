from adapters.scraper_adapter import ScraperAdapter
from adapters.costa_rica_adapter import CostaRicaAdapter
from adapters.mexico_adapter import MexicoAdapter
from adapters.nicaragua_adapter import NicaraguaAdapter
from adapters.el_salvador_adapter import ElSalvadorAdapter
from queue import Queue
from datetime import datetime
from enum import Enum
import time
import threading

class adapter_types(Enum):
    '''
    Used to identify what type of adapter
    '''
    El_Salvador=1,
    Costa_Rica=2,
    Nicaragua=3,
    Mexico=4

class AdapterThread(threading.Thread):
    '''
    Automatically handle tasks for simultanious scraping

    Make use of multi-threading

    '''
    __kill = False
    __running = False
    bad_adapter = False
    __bypass = False
    __adapter_type = None
    __new_adapter_switcher = {
        adapter_types.Costa_Rica: CostaRicaAdapter,
        adapter_types.El_Salvador: ElSalvadorAdapter,
        adapter_types.Mexico: MexicoAdapter,
        adapter_types.Nicaragua: NicaraguaAdapter
    }

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
        if isinstance(adapter, MexicoAdapter):
            self.__adapter_type = adapter_types.Mexico
        elif isinstance(adapter, NicaraguaAdapter):
            self.__adapter_type = adapter_types.Nicaragua
        elif isinstance(adapter, ElSalvadorAdapter):
            self.__adapter_type = adapter_types.El_Salvador
        elif isinstance(adapter, CostaRicaAdapter):
            self.__adapter_type = adapter_types.Costa_Rica
    
    def __scrape_intermittent(self, startdate, enddate):
        try:
            self.upload_queue.put(
                (
                    self.__adapter_type,
                    self.__new_adapter_switcher[self.__adapter_type]().scrape_history(
                        start_day=startdate.day, start_month=startdate.month,
                        start_year=startdate.year, end_day=enddate.day,
                        end_month=enddate.month, end_year=enddate.year
                    )
                )
            )
        except Exception as e:
            print("FAILED", startdate)

    def get_intermittent_data(self, startdate: datetime, enddate: datetime):
        '''
        Gets historical data and throws it into queue

        This is a seperate task and will be threaded
        '''
        threading.Thread(
            target=self.__scrape_intermittent,
            kwargs={
                # 'self' : self,
                'startdate' : startdate,
                'enddate' : enddate
            }
        ).start()
        
    def get_adapter_failure(self) -> bool:
        '''
        Returns False if adapter is fine

        Returns True if adapter failed
        '''
        return self.bad_adapter

    def reset_adapter(self):
        '''
        Reset to a new adapter
        '''
        threading.Thread(target=self.__reset_adapter, kwargs={'self':self}).start()
        
    def __reset_adapter(self):
        '''
        Reset to a new adapter helper
        '''
        self.adapter = self.__new_adapter_switcher[self.__adapter_type]()
        self.bad_adapter = False

    def set_adapter(self, adapter: ScraperAdapter):
        '''
        Set adapter to new adapter
        '''
        self.adapter = adapter
        self.bad_adapter = False

    def set_todays_start_time(self, time: datetime):
        '''
        This will set the reference point for the adapter landing page
        '''
        if not time.tzinfo:
            raise TypeError("datetime object must be tz aware")
        self.adapter.set_last_scraped_date(time)

    def schedule_todays_data_now(self):
        '''
        This will let the running thread know to reattempt a scrape now
        '''
        self.__bypass = True


    def attempt_to_queue_todays_data(self):
        '''
        This will attempt to get todays data
        '''
        try:
            data = self.adapter.scrape_new_data()
            if data:
                self.upload_queue.put((self.__adapter_type, data))
        except Exception as e:
            print(e)
            self.bad_adapter = True

    def is_alive(self):
        return self.__running

    def start(self):
        self.__kill = False
        return super().start()

    def run(self):
        '''
        Runs the adapter for realtime data gathering

        Sleeps a majority of its time

        This also has a fake watchdog so that we can kill the process
        in a reasonable amount of time
        '''
        self.__running = True
        freq = self.adapter.frequency()
        # equals freq so it scrapes once before waiting
        total_sleep = freq
        while not self.__kill:
            if total_sleep < freq and not self.__bypass:
                total_sleep += self.__watchdog_time
                time.sleep(self.__watchdog_time)
            else:
                total_sleep = 0
                self.__bypass = False
                self.attempt_to_queue_todays_data()
        self.__running = False
        return super().run()

    def join(self, timeout=30):
        self.__kill = True
        super().join(timeout)

    def __del__(self):
        self.join()
