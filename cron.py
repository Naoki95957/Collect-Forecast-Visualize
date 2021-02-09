from adapters.el_salvador_adapter import ElSalvadorAdapter
from adapters.mexico_adapter import MexicoAdapter
from adapters.nicaragua_adapter import NicaraguaAdapter
from adapters.costa_rica_adapter import CostaRicaAdapter
from adapters.scraper_adapter import ScraperAdapter
from adapters.adapter_tasks import AdapterThread, adapter_types
from queue import Queue
from threading import Thread
from datetime import datetime
import time

class cron:
    adapter_threads = list()
    manager_queue = None
    cron_alive = True
    __cron_thread = None
    __switcher = dict()

    def __init__(self, queue: list):
        self.manager_queue = queue

        esa = ElSalvadorAdapter()
        ma = MexicoAdapter()
        na = NicaraguaAdapter()
        cra = CostaRicaAdapter()

        esat = AdapterThread(esa, queue)
        mat = AdapterThread(ma, queue)
        nat = AdapterThread(na, queue)
        crat = AdapterThread(cra, queue)

        self.__switcher = {
            adapter_types.El_Salvador: esat,
            adapter_types.Costa_Rica: crat,
            adapter_types.Mexico: mat,
            adapter_types.Nicaragua: nat
        }
        self.adapter_threads.extend(
            [
                esat,
                crat,
                mat,
                nat
            ]
        )
        self.__set_up_health_check()

    def get_adapter_threads(self) -> list:
        return self.adapter_threads

    def set_last_scrape_date(
            self, 
            adapter_type: adapter_types,
            date: datetime):
        '''
        Set the last scraped date for the adapters
        '''
        thread = self.__switcher[adapter_type]
        ScraperAdapter(thread.adapter).set_last_scraped_date(date)

    def scrape_todays_data_now(self, adapter_type: adapter_types):
        '''
        This will let the adpter know that we want to attempt
        to scrape the landing page infomation right now
        '''
        self.__switcher[adapter_type].schedule_todays_data_now()

    def request_historical(
            self, 
            adapter_type: adapter_types,
            start_date: datetime,
            end_date: datetime):
        '''
        Will let the adpter know to queue historical data
        '''
        thread = self.__switcher[adapter_type]
        thread.get_intermittent_data(
            start_date, 
            end_date
        )

    def __set_up_health_check(self):
        '''
        New thread w/ loop to constantly check health of adapters
        '''
        self.cron_alive = True
        for t in self.adapter_threads:
            t.start()
        self.__cron_thread = Thread(target=self.__health_loop)
        self.__cron_thread.start()

    def __health_loop(self):
        while self.cron_alive:
            self.check_adapters()

    def check_adapters(self):
        if not self.adapter_threads:
            return
        for t in self.adapter_threads:
            if t.bad_adapter:
                t.reset_adapter()

    def __del__(self):
        self.cron_alive = False
        self.__cron_thread.join()
        for t in self.adapter_threads:
            t.join()
