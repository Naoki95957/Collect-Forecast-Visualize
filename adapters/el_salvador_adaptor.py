from adapters.scraper_adapter import ScraperAdapter
from scrapers.el_salvador import ElSalvador
from datetime import timedelta
import copy
import datetime


class ElSalvadorAdapter(ScraperAdapter):

    def __init__(self, scraper=ElSalvador):
        self.scraper = ElSalvador()
        self.last_scrape_date = None
        self.last_scrape_list = []

    def scrape(self):
        '''
        Will attempt to scrape data by the hour

        If the last scrape was within an hour, it will return None

        Returns: dict with data entries for the hour.
        '''
        will_scrape = False
        delta = None
        if (not self.last_scrape_date):
            will_scrape = True
        else:
            delta = timedelta(
                datetime.datetime.today() - self.last_scrape_date)
            # 60 seconds * 60 minutes
            if (delta.seconds / (60 * 60) > 1):
                will_scrape = True

        if (will_scrape):
            # TODO scrape data
            self.last_scrape_date = datetime.datetime.now()
            data = self.scraper.scrape_data()
            print(data)
            dataCopy = copy.deepcopy(self.last_scrape_list)
            self.last_scrape_list = data
            # TODO make these into dictionaries to take a difference in sets
            return data - dataCopy
        else:
            return None

    def scrape_day(self) -> dict:
        # TODO
        return None

    def frequency(self):
        # TODO return something that indicates hourly
        return None
