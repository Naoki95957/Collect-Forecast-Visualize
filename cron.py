from scrapers.nicaragua import Nicaragua
from adapters.el_salvador_adapter import ElSalvadorAdapter
from adapters.mexico_adapter import MexicoAdapter
from adapters.nicaragua_adapter import NicaraguaAdapter
from adapters.costa_rica_adapter import CostaRicaAdapter
from adapters.scraper_adapter import ScraperAdapter
from adapters.adapter_tasks import AdapterThread, AdapterTypes
from forecast.forecast_tasks import ForecasterTypes, ForecasterThread, ForecastFactory
from threading import Thread
from datetime import datetime

class cron:
    '''
    Sort of a scheduler. This is meant to handle all things threads and adapters
    '''
    created_threads = list()
    manager_queue = None
    main_job_queue = None
    cron_alive = True
    __cron_thread = None
    __switcher = dict()

    def __init__(self, queue: list, main_job_queue: list):
        self.manager_queue = queue
        self.main_job_queue = main_job_queue
        esa = ElSalvadorAdapter()
        ma = MexicoAdapter()
        na = NicaraguaAdapter()
        cra = CostaRicaAdapter()
        esf = ForecastFactory.el_salvador_forecaster()
        nf = ForecastFactory.nicaragua_forecaster()
        crf = ForecastFactory.costa_rica_forecaster()
        # mf = ForecastFactory.mexico_forecaster()

        esat = AdapterThread(esa, queue)
        mat = AdapterThread(ma, queue)
        nat = AdapterThread(na, queue)
        crat = AdapterThread(cra, queue)
        esft = ForecasterThread(esf, queue)
        crft = ForecasterThread(crf, queue)
        nft = ForecasterThread(nf, queue)
        # mft = ForecasterThread(mf, queue)

        self.__switcher = {
            AdapterTypes.El_Salvador: esat,
            AdapterTypes.Costa_Rica: crat,
            AdapterTypes.Mexico: mat,
            AdapterTypes.Nicaragua: nat,
            ForecasterTypes.El_Salvador: esft,
            ForecasterTypes.Nicaragua: nft,
            ForecasterTypes.Costa_Rica: crft,
            # ForecasterTypes.Mexico: mft
        }

        self.created_threads.extend(
            [
                # esat,
                # crat,
                # mat,
                # nat,
                esft,
                crft,
                nft,
                # mft
            ]
        )
        self.__set_up_health_check()

    def get_adapter_threads(self) -> list:
        return self.created_threads

    def set_last_scrape_date(
            self, 
            adapter_type: AdapterTypes,
            date: datetime):
        '''
        Set the last scraped date for the adapters
        '''
        thread = self.__switcher[adapter_type]
        ScraperAdapter(thread.adapter).set_last_scraped_date(date)

    def scrape_todays_data_now(self, adapter_type: AdapterTypes):
        '''
        This will let the adpter know that we want to attempt
        to scrape the landing page infomation right now
        '''
        self.__switcher[adapter_type].schedule_todays_data_now()

    def request_historical(
            self, 
            adapter_type: AdapterTypes,
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
        for t in self.created_threads:
            if isinstance(t, AdapterThread):
                t.start()
            elif isinstance(t, ForecasterThread):
                t.start()
        self.__cron_thread = Thread(target=self.__health_loop)
        self.__cron_thread.start()

    def __health_loop(self):
        while self.cron_alive:
            self.check_threads()

    def check_threads(self):
        if not self.created_threads:
            return
        for t in self.created_threads:
            if isinstance(t, AdapterThread) and t.bad_adapter:
                t.reset_adapter()
            elif isinstance(t, ForecasterThread) and t.bad_forecaster:
                t.reset_forecaster()

    def __del__(self):
        self.cron_alive = False
        self.__cron_thread.join()
        # TODO join forecaster threads
        for t in self.created_threads:
            if isinstance(t, AdapterThread):
                t.join()
            elif isinstance(t, ForecasterThread):
                t.join()
