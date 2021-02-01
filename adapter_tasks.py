from adapters.scraper_adapter import ScraperAdapter
from queue import Queue
import threading

class AdapterThread(threading.Thread):
    '''
    Automatically handle tasks for simultanious scraping

    Make use of multi-threading
    '''

    def __init__(self, scraper: ScraperAdapter, upload_data: Queue):
        super(AdapterThread, self).__init__()
        self.scraper = ScraperAdapter

    def start(self):
        # TODO sort of init
        return super().start()

    def run(self):
        # TODO build out running task
        
        return super().run()

    # overrides join
    def join(self, timeout=30):
        # TODO things to kill running process
        super().join(timeout)

